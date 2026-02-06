"""
LangGraph-based Agent Workflow for Travel Assistant.

Provides a declarative graph-based workflow using LangGraph's StateGraph
for the travel planning process.
"""

from typing import Annotated, Any, Dict, Generator, List, Optional, Tuple, TypedDict, Union
from operator import add

from langgraph.graph import END, StateGraph
from pydantic import BaseModel, Field

from ..agents import ConsultAgent, ExtractAgent, PlanAgent, SummaryAgent
from ..common import (
    FIELD_DEPARTURE,
    FIELD_DISTANCE,
    FIELD_NAME_MAP,
    FIELD_SCORE,
    FIELD_SEASON,
    geocode,
    replace_folded_vectors,
)
from ..common.config import get_config
from ..common.logger import get_logger
from ..tools import QueryTool

logger = get_logger(__name__)


# =============================================================================
# Graph State Definition
# =============================================================================


class TravelGraphState(TypedDict, total=False):
    """
    State schema for the travel planning workflow graph.

    This TypedDict defines all data that flows through the graph nodes.
    """

    # Input fields
    user_content: str
    chat_history: List[dict]

    # User travel preferences (persisted across turns)
    departure: Optional[str]
    distance: Optional[str]
    score: Optional[int]
    season: Optional[str]

    # Intermediate results
    extracted_info: Optional[Dict[str, Any]]
    summary_text: Optional[str]

    # Output fields
    response: Optional[Any]  # Can be string or streaming generator
    geo_coords: Optional[List[Tuple[float, float]]]
    sql_statements: Optional[List[str]]
    column_names: Optional[List[str]]
    result_rows: Optional[List[Tuple]]

    # Control flow flags
    is_complete: bool
    need_reset: bool
    success: bool
    error_message: Optional[str]
    
    # Status messages for UI display (using add operator to append messages)
    status_messages: Annotated[List[str], add]


class WorkflowResponse(BaseModel):
    """
    Response model for workflow execution.

    Contains all information needed by the frontend to update its state
    and display the conversation.
    """

    success: bool = Field(default=True, description="Whether the interaction succeeded")
    reply: str = Field(default="", description="LLM output for this turn")
    need_reset: bool = Field(default=False, description="Whether frontend should reset history")
    sql: Optional[str] = Field(default=None, description="SQL statement if used")
    datas: Optional[List[dict]] = Field(default=None, description="Query results if SQL was used")
    lats: Optional[List[float]] = Field(default=None, description="Latitude coordinates for map")
    longs: Optional[List[float]] = Field(default=None, description="Longitude coordinates for map")
    departure: Optional[str] = Field(default=None, description="Saved departure location")
    distance: Optional[str] = Field(default=None, description="Saved travel distance")
    score: Optional[int] = Field(default=None, description="Saved score requirement")
    season: Optional[str] = Field(default=None, description="Saved season preference")
    status_messages: List[str] = Field(default_factory=list, description="Status messages from workflow execution")


# =============================================================================
# State Update Helpers
# =============================================================================


def update_user_state(
    state: TravelGraphState,
    extracted: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Update user travel state with newly extracted information.

    Implements smart merging:
    - departure and distance: direct replacement
    - score: keep maximum value
    - season: concatenate strings

    Args:
        state: Current graph state.
        extracted: Newly extracted information.

    Returns:
        Dictionary with updated state fields.
    """
    updates: Dict[str, Any] = {}

    if extracted.get(FIELD_DEPARTURE) is not None:
        updates["departure"] = extracted[FIELD_DEPARTURE]

    if extracted.get(FIELD_DISTANCE) is not None:
        updates["distance"] = extracted[FIELD_DISTANCE]

    if extracted.get(FIELD_SCORE) is not None:
        current_score = state.get("score")
        new_score = extracted[FIELD_SCORE]
        if current_score is None:
            updates["score"] = new_score
        else:
            updates["score"] = max(current_score, new_score)

    if extracted.get(FIELD_SEASON) is not None:
        current_season = state.get("season")
        new_season = extracted[FIELD_SEASON]
        if current_season is None:
            updates["season"] = new_season
        else:
            updates["season"] = current_season + new_season

    return updates


def get_missing_fields(state: TravelGraphState) -> List[str]:
    """
    Get list of missing required field display names.

    Args:
        state: Current graph state.

    Returns:
        List of display names for missing fields.
    """
    field_keys = [FIELD_DEPARTURE, FIELD_DISTANCE, FIELD_SCORE, FIELD_SEASON]
    return [
        FIELD_NAME_MAP[key]
        for key in field_keys
        if state.get(key) is None
    ]


def is_info_complete(state: TravelGraphState) -> bool:
    """
    Check if all required travel information is filled.

    Args:
        state: Current graph state.

    Returns:
        True if all required fields have values.
    """
    return all([
        state.get("departure") is not None,
        state.get("distance") is not None,
        state.get("score") is not None,
        state.get("season") is not None,
    ])


def get_user_info_dict(state: TravelGraphState) -> Dict[str, Any]:
    """
    Extract user travel info as a dictionary.

    Args:
        state: Current graph state.

    Returns:
        Dictionary with departure, distance, score, season.
    """
    return {
        FIELD_DEPARTURE: state.get("departure"),
        FIELD_DISTANCE: state.get("distance"),
        FIELD_SCORE: state.get("score"),
        FIELD_SEASON: state.get("season"),
    }


# =============================================================================
# Graph Node Functions
# =============================================================================


def extract_node(state: TravelGraphState) -> Dict[str, Any]:
    """
    Extract travel information from user input.

    This node uses ExtractAgent to parse the user's message and
    extract structured travel preferences.

    Args:
        state: Current graph state.

    Returns:
        State updates with extracted info and completion status.
    """
    status_messages = ["📝 正在提取旅行信息..."]
    logger.info("=== EXTRACT NODE ===")
    user_content = state["user_content"]

    try:
        extract_agent = ExtractAgent()
        extracted_info = extract_agent.chat(user_content=user_content)
        logger.info(f"Extracted: {extracted_info}")
        status_messages.append(f"✓ 提取完成: {extracted_info}")

        # Calculate state updates
        updates = update_user_state(state, extracted_info)

        # Merge with current state to check completeness
        merged_state = {**state, **updates}
        complete = is_info_complete(merged_state)

        logger.info(f"Info complete: {complete}")
        if complete:
            status_messages.append("✓ 旅行信息已完整")
        else:
            status_messages.append("⚠ 旅行信息不完整，需要补充")

        return {
            "extracted_info": extracted_info,
            "is_complete": complete,
            "success": True,
            "status_messages": status_messages,
            **updates,
        }

    except Exception as e:
        logger.error(f"Extract failed: {e}", exc_info=True)
        status_messages.append(f"✗ 提取失败: {str(e)}")
        return {
            "success": False,
            "error_message": str(e),
            "is_complete": False,
            "status_messages": status_messages,
        }


def consult_node(state: TravelGraphState) -> Dict[str, Any]:
    """
    Consult user for missing travel information.

    This node uses ConsultAgent to generate a friendly response
    asking the user for missing required information.

    Args:
        state: Current graph state.

    Returns:
        State updates with response and geo coordinates.
    """
    status_messages = ["💬 正在生成咨询回复..."]
    logger.info("=== CONSULT NODE ===")
    missing_fields = get_missing_fields(state)
    logger.info(f"Missing fields: {missing_fields}")
    status_messages.append(f"⚠ 缺少字段: {', '.join(missing_fields)}")

    try:
        consult_agent = ConsultAgent(enable_stream=True)
        response = consult_agent.chat(
            necessary_list=missing_fields,
            chat_history=state.get("chat_history", []),
            user_content=state["user_content"],
        )

        # Get departure coordinates if available
        geo_coords = None
        departure = state.get("departure")
        if departure is not None:
            try:
                logger.info(f"Geocoding: {departure}")
                status_messages.append(f"🌍 正在定位出发地: {departure}")
                lat, lng = geocode(departure)
                geo_coords = [(lat, lng)]
                status_messages.append(f"✓ 定位成功: ({lat:.4f}, {lng:.4f})")
            except Exception as e:
                logger.warning(f"Geocoding failed: {e}")
                status_messages.append(f"⚠ 定位失败: {e}")

        logger.info("Consult completed")
        status_messages.append("✓ 咨询回复生成完成")
        return {
            "response": response,
            "geo_coords": geo_coords,
            "need_reset": False,
            "success": True,
            "status_messages": status_messages,
        }

    except Exception as e:
        logger.error(f"Consult failed: {e}", exc_info=True)
        status_messages.append(f"✗ 咨询失败: {str(e)}")
        return {
            "success": False,
            "error_message": str(e),
            "status_messages": status_messages,
        }


def summary_node(state: TravelGraphState) -> Dict[str, Any]:
    """
    Summarize user's travel requirements.

    This node uses SummaryAgent to create a concise summary
    of the user's travel preferences from the conversation.

    Args:
        state: Current graph state.

    Returns:
        State updates with summary text.
    """
    status_messages = ["📋 正在总结旅行需求..."]
    logger.info("=== SUMMARY NODE ===")

    try:
        summary_agent = SummaryAgent()
        summary_text = summary_agent.chat(
            chat_history=state.get("chat_history", []),
            user_content=state["user_content"],
        )
        logger.info(f"Summary: {summary_text[:100]}...")
        status_messages.append(f"✓ 需求总结完成: {summary_text[:50]}...")

        return {
            "summary_text": summary_text,
            "success": True,
            "status_messages": status_messages,
        }

    except Exception as e:
        logger.error(f"Summary failed: {e}", exc_info=True)
        status_messages.append(f"✗ 总结失败: {str(e)}")
        return {
            "success": False,
            "error_message": str(e),
            "status_messages": status_messages,
        }


def plan_node(state: TravelGraphState) -> Dict[str, Any]:
    """
    Generate travel plan based on user requirements.

    This node uses PlanAgent to search for attractions and
    generate a detailed travel plan.

    Args:
        state: Current graph state.

    Returns:
        State updates with plan, coordinates, and query results.
    """
    status_messages = ["🔍 正在规划旅行方案..."]
    logger.info("=== PLAN NODE ===")

    cfg = get_config()
    sql_statements: List[str] = []
    column_names: List[str] = []
    result_rows: List[Tuple] = []

    try:
        status_messages.append("🔧 初始化查询工具...")
        query_tool = QueryTool(
            table_name=cfg.default_table_name,
            topk=cfg.default_topk,
        )
        plan_agent = PlanAgent(
            query_tool=query_tool,
            enable_stream=True,
            search_only=True,
        )

        status_messages.append("🔎 开始搜索景点...")
        user_info = get_user_info_dict(state)
        _, geo_coords, search_duration = plan_agent.chat(
            necessary_info=user_info,
            chat_history=state.get("chat_history", []),
            summary=state.get("summary_text", ""),
            user_content=state["user_content"],
            str_list=sql_statements,
            result_column_names=column_names,
            result_rows=result_rows,
        )
        logger.info(f"Search completed in {search_duration:.2f}s")
        logger.info(f"Found {len(geo_coords) if geo_coords else 0} attractions")
        
        num_attractions = len(geo_coords) if geo_coords else 0
        status_messages.append(f"✓ 搜索完成: 用时 {search_duration:.2f}秒")
        status_messages.append(f"✓ 找到 {num_attractions} 个景点")

        return {
            "geo_coords": geo_coords,
            "sql_statements": sql_statements,
            "column_names": column_names,
            "result_rows": result_rows,
            "need_reset": True,
            "success": True,
            "status_messages": status_messages,
        }

    except Exception as e:
        logger.error(f"Plan failed: {e}", exc_info=True)
        status_messages.append(f"✗ 规划失败: {str(e)}")
        return {
            "success": False,
            "error_message": str(e),
            "status_messages": status_messages,
        }


# =============================================================================
# Async Node Functions
# =============================================================================


async def extract_node_async(state: TravelGraphState) -> Dict[str, Any]:
    """Async version of extract_node."""
    status_messages = ["📝 正在提取旅行信息..."]
    logger.info("=== ASYNC EXTRACT NODE ===")
    user_content = state["user_content"]

    try:
        extract_agent = ExtractAgent(is_async=True)
        extracted_info = await extract_agent.achat(user_content=user_content)
        logger.info(f"Extracted: {extracted_info}")
        status_messages.append(f"✓ 提取完成: {extracted_info}")

        updates = update_user_state(state, extracted_info)
        merged_state = {**state, **updates}
        complete = is_info_complete(merged_state)

        logger.info(f"Info complete: {complete}")
        if complete:
            status_messages.append("✓ 旅行信息已完整")
        else:
            status_messages.append("⚠ 旅行信息不完整，需要补充")

        return {
            "extracted_info": extracted_info,
            "is_complete": complete,
            "success": True,
            "status_messages": status_messages,
            **updates,
        }

    except Exception as e:
        logger.error(f"Async extract failed: {e}", exc_info=True)
        status_messages.append(f"✗ 提取失败: {str(e)}")
        return {
            "success": False,
            "error_message": str(e),
            "is_complete": False,
            "status_messages": status_messages,
        }


async def consult_node_async(state: TravelGraphState) -> Dict[str, Any]:
    """Async version of consult_node."""
    status_messages = ["💬 正在生成咨询回复..."]
    logger.info("=== ASYNC CONSULT NODE ===")
    missing_fields = get_missing_fields(state)
    logger.info(f"Missing fields: {missing_fields}")
    status_messages.append(f"⚠ 缺少字段: {', '.join(missing_fields)}")

    try:
        consult_agent = ConsultAgent(enable_stream=True, is_async=True)
        response = await consult_agent.achat(
            necessary_list=missing_fields,
            chat_history=state.get("chat_history", []),
            user_content=state["user_content"],
        )

        geo_coords = None
        departure = state.get("departure")
        if departure is not None:
            try:
                logger.info(f"Geocoding: {departure}")
                status_messages.append(f"🌍 正在定位出发地: {departure}")
                lat, lng = geocode(departure)
                geo_coords = [(lat, lng)]
                status_messages.append(f"✓ 定位成功: ({lat:.4f}, {lng:.4f})")
            except Exception as e:
                logger.warning(f"Geocoding failed: {e}")
                status_messages.append(f"⚠ 定位失败: {e}")

        logger.info("Async consult completed")
        status_messages.append("✓ 咨询回复生成完成")
        return {
            "response": response,
            "geo_coords": geo_coords,
            "need_reset": False,
            "success": True,
            "status_messages": status_messages,
        }

    except Exception as e:
        logger.error(f"Async consult failed: {e}", exc_info=True)
        status_messages.append(f"✗ 咨询失败: {str(e)}")
        return {
            "success": False,
            "error_message": str(e),
            "status_messages": status_messages,
        }


async def summary_node_async(state: TravelGraphState) -> Dict[str, Any]:
    """Async version of summary_node."""
    status_messages = ["📋 正在总结旅行需求..."]
    logger.info("=== ASYNC SUMMARY NODE ===")

    try:
        summary_agent = SummaryAgent(is_async=True)
        summary_text = await summary_agent.achat(
            chat_history=state.get("chat_history", []),
            user_content=state["user_content"],
        )
        logger.info(f"Summary: {summary_text[:100]}...")
        status_messages.append(f"✓ 需求总结完成: {summary_text[:50]}...")

        return {
            "summary_text": summary_text,
            "success": True,
            "status_messages": status_messages,
        }

    except Exception as e:
        logger.error(f"Async summary failed: {e}", exc_info=True)
        status_messages.append(f"✗ 总结失败: {str(e)}")
        return {
            "success": False,
            "error_message": str(e),
            "status_messages": status_messages,
        }


async def plan_node_async(state: TravelGraphState) -> Dict[str, Any]:
    """Async version of plan_node."""
    status_messages = ["🔍 正在规划旅行方案..."]
    logger.info("=== ASYNC PLAN NODE ===")

    cfg = get_config()
    sql_statements: List[str] = []
    column_names: List[str] = []
    result_rows: List[Tuple] = []

    try:
        status_messages.append("🔧 初始化查询工具...")
        query_tool = QueryTool(
            table_name=cfg.default_table_name,
            topk=cfg.default_topk,
        )
        plan_agent = PlanAgent(
            query_tool=query_tool,
            enable_stream=True,
            is_async=True,
            search_only=True,
        )

        status_messages.append("🔎 开始搜索景点...")
        user_info = get_user_info_dict(state)
        _, geo_coords, search_duration = await plan_agent.achat(
            necessary_info=user_info,
            chat_history=state.get("chat_history", []),
            summary=state.get("summary_text", ""),
            user_content=state["user_content"],
            str_list=sql_statements,
            result_column_names=column_names,
            result_rows=result_rows,
        )
        logger.info(f"Async search completed in {search_duration:.2f}s")
        logger.info(f"Found {len(geo_coords) if geo_coords else 0} attractions")
        
        num_attractions = len(geo_coords) if geo_coords else 0
        status_messages.append(f"✓ 搜索完成: 用时 {search_duration:.2f}秒")
        status_messages.append(f"✓ 找到 {num_attractions} 个景点")

        return {
            "geo_coords": geo_coords,
            "sql_statements": sql_statements,
            "column_names": column_names,
            "result_rows": result_rows,
            "need_reset": True,
            "success": True,
            "status_messages": status_messages,
        }

    except Exception as e:
        logger.error(f"Async plan failed: {e}", exc_info=True)
        status_messages.append(f"✗ 规划失败: {str(e)}")
        return {
            "success": False,
            "error_message": str(e),
            "status_messages": status_messages,
        }


# =============================================================================
# Routing Functions
# =============================================================================


def route_after_extract(state: TravelGraphState) -> str:
    """
    Determine the next node after extraction.

    Args:
        state: Current graph state.

    Returns:
        "summary" if info is complete, "consult" otherwise.
    """
    if not state.get("success", True):
        logger.info("Routing to END due to error")
        return END

    if state.get("is_complete", False):
        logger.info("Routing to SUMMARY (info complete)")
        return "summary"

    logger.info("Routing to CONSULT (info incomplete)")
    return "consult"


# =============================================================================
# Graph Builder
# =============================================================================


def build_sync_graph() -> StateGraph:
    """
    Build the synchronous travel workflow graph.

    Returns:
        Compiled StateGraph for synchronous execution.
    """
    graph = StateGraph(TravelGraphState)

    # Add nodes
    graph.add_node("extract", extract_node)
    graph.add_node("consult", consult_node)
    graph.add_node("summary", summary_node)
    graph.add_node("plan", plan_node)

    # Set entry point
    graph.set_entry_point("extract")

    # Add conditional edge after extract
    graph.add_conditional_edges(
        "extract",
        route_after_extract,
        {
            "consult": "consult",
            "summary": "summary",
            END: END,
        },
    )

    # Add edges
    graph.add_edge("consult", END)
    graph.add_edge("summary", "plan")
    graph.add_edge("plan", END)

    return graph.compile()


def build_async_graph() -> StateGraph:
    """
    Build the asynchronous travel workflow graph.

    Returns:
        Compiled StateGraph for asynchronous execution.
    """
    graph = StateGraph(TravelGraphState)

    # Add async nodes
    graph.add_node("extract", extract_node_async)
    graph.add_node("consult", consult_node_async)
    graph.add_node("summary", summary_node_async)
    graph.add_node("plan", plan_node_async)

    # Set entry point
    graph.set_entry_point("extract")

    # Add conditional edge after extract
    graph.add_conditional_edges(
        "extract",
        route_after_extract,
        {
            "consult": "consult",
            "summary": "summary",
            END: END,
        },
    )

    # Add edges
    graph.add_edge("consult", END)
    graph.add_edge("summary", "plan")
    graph.add_edge("plan", END)

    return graph.compile()


# =============================================================================
# TravelWorkflow Class
# =============================================================================


class TravelWorkflow:
    """
    LangGraph-based travel planning workflow.

    This class provides a clean interface for executing the travel
    planning workflow using LangGraph's StateGraph.
    """

    def __init__(
        self,
        chat_history: Optional[List[dict]] = None,
        departure: Optional[str] = None,
        distance: Optional[str] = None,
        score: Optional[int] = None,
        season: Optional[str] = None,
    ) -> None:
        """
        Initialize the workflow.

        Args:
            chat_history: Previous conversation messages.
            departure: Saved departure location.
            distance: Saved travel distance.
            score: Saved score requirement.
            season: Saved season preference.
        """
        logger.info(f"[TravelWorkflow] Initializing with history_len={len(chat_history or [])}")
        logger.debug(
            f"[TravelWorkflow] State: departure={departure}, "
            f"distance={distance}, score={score}, season={season}"
        )

        self._chat_history = chat_history or []
        self._departure = departure
        self._distance = distance
        self._score = score
        self._season = season

        # Build graphs
        self._sync_graph = build_sync_graph()
        self._async_graph = build_async_graph()

        logger.info("[TravelWorkflow] Initialization complete")

    def _create_initial_state(self, user_content: str) -> TravelGraphState:
        """
        Create initial state for graph execution.

        Args:
            user_content: The user's input message.

        Returns:
            Initial TravelGraphState.
        """
        return TravelGraphState(
            user_content=user_content,
            chat_history=self._chat_history,
            departure=self._departure,
            distance=self._distance,
            score=self._score,
            season=self._season,
            is_complete=False,
            need_reset=False,
            success=True,
            status_messages=[],
        )

    def _build_response(
        self,
        final_state: Dict[str, Any],
    ) -> Tuple[Optional[Any], WorkflowResponse]:
        """
        Build workflow response from final state.

        Args:
            final_state: The final state after graph execution.

        Returns:
            Tuple of (streamer_or_none, WorkflowResponse).
        """
        response = WorkflowResponse()

        # Check for errors
        if not final_state.get("success", True):
            response.success = False
            response.reply = final_state.get("error_message", "Unknown error")
            response.status_messages = final_state.get("status_messages", [])
            logger.info(f"[TravelWorkflow] Error response with {len(response.status_messages)} status messages")
            return None, response

        # Populate user state
        response.departure = final_state.get("departure")
        response.distance = final_state.get("distance")
        response.score = final_state.get("score")
        response.season = final_state.get("season")
        response.need_reset = final_state.get("need_reset", False)
        
        # Populate status messages
        response.status_messages = final_state.get("status_messages", [])
        logger.info(f"[TravelWorkflow] Built response with {len(response.status_messages)} status messages")
        if response.status_messages:
            logger.info(f"[TravelWorkflow] Status messages: {response.status_messages}")

        # Populate geo coordinates
        geo_coords = final_state.get("geo_coords")
        if geo_coords:
            response.lats = [coord[0] for coord in geo_coords]
            response.longs = [coord[1] for coord in geo_coords]
        else:
            response.lats = []
            response.longs = []

        # Populate SQL and results (for plan node)
        sql_statements = final_state.get("sql_statements")
        column_names = final_state.get("column_names")
        result_rows = final_state.get("result_rows")

        if sql_statements:
            response.sql = replace_folded_vectors(sql_statements[0])
            if column_names and result_rows:
                response.datas = [
                    dict(zip(column_names, row))
                    for row in result_rows
                ]

        # Get streamer (for consult node)
        streamer = final_state.get("response")

        return streamer, response

    def run(self, user_content: str) -> Tuple[Optional[Any], WorkflowResponse]:
        """
        Execute the workflow synchronously.

        Args:
            user_content: The user's input message.

        Returns:
            Tuple of (streamer_or_none, WorkflowResponse).
        """
        logger.info(f"[TravelWorkflow] Running sync: {user_content[:100]}...")

        initial_state = self._create_initial_state(user_content)
        final_state = self._sync_graph.invoke(initial_state)

        return self._build_response(final_state)

    async def arun(self, user_content: str) -> Tuple[Optional[Any], WorkflowResponse]:
        """
        Execute the workflow asynchronously.

        Args:
            user_content: The user's input message.

        Returns:
            Tuple of (streamer_or_none, WorkflowResponse).
        """
        logger.info(f"[TravelWorkflow] Running async: {user_content[:100]}...")

        initial_state = self._create_initial_state(user_content)
        final_state = await self._async_graph.ainvoke(initial_state)

        return self._build_response(final_state)
