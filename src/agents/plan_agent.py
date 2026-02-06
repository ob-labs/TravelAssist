"""
Plan Agent for OBMMS.

Responsible for generating travel plans based on user requirements
and available attractions from the database.
"""

import time
from typing import Any, Dict, Generator, List, Optional, Tuple, Union

from ..common import parse_point_coordinates
from ..common.config import get_config
from ..common.logger import get_logger
from ..llm import TongyiLLM, TongyiLLMConfig
from ..prompt import plan_prompt
from ..tools import QueryTool
from .agent import Agent

logger = get_logger(__name__)

# Type aliases
Coordinates = Tuple[float, float]
PlanResult = Tuple[Optional[str], Optional[List[Coordinates]], float]


class PlanAgent(Agent):
    """
    Agent for generating travel plans.

    This agent uses the OBMMS tool to search for attractions based
    on user requirements and generates detailed travel plans with
    the help of the LLM.
    """

    def __init__(
        self,
        query_tool: QueryTool,
        enable_stream: bool = False,
        is_async: bool = False,
        search_only: bool = False,
        model_name: str | None = None,
    ) -> None:
        """
        Initialize the Plan Agent.

        Args:
            query_tool: The Query tool for searching attractions.
            enable_stream: Whether to enable streaming output.
            is_async: Whether to enable async operations.
            search_only: If True, only search without generating plan.
            model_name: The LLM model to use. If None, uses config default.
        """
        if model_name is None:
            model_name = get_config().default_llm_model
        config = TongyiLLMConfig(
            model_name=model_name,
            stream=enable_stream,
            incremental_output=enable_stream,
        )
        llm = TongyiLLM(config=config)
        super().__init__(llm=llm, tool=query_tool, is_async=is_async)
        self._enable_stream = enable_stream
        self._search_only = search_only

    @property
    def enable_stream(self) -> bool:
        """Check if streaming is enabled."""
        return self._enable_stream

    @property
    def search_only(self) -> bool:
        """Check if search-only mode is enabled."""
        return self._search_only

    def _format_attraction_info(
        self,
        row: tuple,
        index: int,
    ) -> str:
        """
        Format a single attraction row into readable string.

        Args:
            row: Database row tuple.
            index: Attraction index number.

        Returns:
            Formatted attraction information string.
        """
        # Join all columns except the last (geometry)
        info = "".join(str(col) for col in list(row)[:-1])
        return f"景点{index}: {info}\n\n"

    def _process_search_results(
        self,
        results: Any,
        result_column_names: Optional[List[str]] = None,
        result_rows: Optional[List[Tuple]] = None,
    ) -> Tuple[str, Optional[List[Coordinates]]]:
        """
        Process database search results.

        Args:
            results: Database query results.
            result_column_names: Optional list to store column names.
            result_rows: Optional list to store result rows.

        Returns:
            Tuple of (formatted_info_string, geo_coordinates_list).
        """
        if result_column_names is not None:
            result_column_names.extend(results.keys())

        attraction_infos = ""
        geo_coordinates: Optional[List[Coordinates]] = None
        index = 1

        for row in results.fetchall():
            if result_rows is not None:
                result_rows.append(row)

            if geo_coordinates is None:
                geo_coordinates = []

            # Extract geometry from last column
            geometry_str = str(list(row)[-1])
            geo_coordinates.append(parse_point_coordinates(geometry_str))

            if not self._search_only:
                attraction_infos += self._format_attraction_info(row, index)

            index += 1

        if not attraction_infos and not self._search_only:
            attraction_infos = "不存在可选旅行景点"

        return attraction_infos, geo_coordinates

    def chat(
        self,
        necessary_info: Dict[str, Any],
        chat_history: List[dict],
        summary: str,
        user_content: str,
        str_list: Optional[List[str]] = None,
        result_column_names: Optional[List[str]] = None,
        result_rows: Optional[List[Tuple]] = None,
        **kwargs,
    ) -> PlanResult:
        """
        Generate a travel plan based on user requirements.

        Args:
            necessary_info: Dictionary of required travel information.
            chat_history: Previous conversation history.
            summary: Summary of user's requirements.
            user_content: The user's latest message.
            str_list: Optional list to store SQL statements.
            result_column_names: Optional list to store column names.
            result_rows: Optional list to store result rows.
            **kwargs: Additional arguments (unused).

        Returns:
            Tuple of (plan_response, geo_coordinates, search_duration).

        Raises:
            ValueError: If plan generation fails after retries.
        """
        logger.info(f"[PlanAgent] Starting plan generation with info: {necessary_info}")
        logger.debug(f"[PlanAgent] Summary: {summary[:100]}...")

        # Search for attractions
        logger.info("[PlanAgent] Searching for attractions in database...")
        start_time = time.time()
        results = self._tool.call(
            necessary_info=necessary_info,
            summary=summary,
            str_list=str_list,
        )
        search_duration = time.time() - start_time
        logger.info(f"[PlanAgent] Database search completed in {search_duration:.2f}s")

        # Process results
        attraction_infos, geo_coordinates = self._process_search_results(
            results,
            result_column_names,
            result_rows,
        )

        num_attractions = len(geo_coordinates) if geo_coordinates else 0
        logger.info(f"[PlanAgent] Found {num_attractions} attractions")

        # Return early if search-only mode
        if self._search_only:
            logger.info("[PlanAgent] Search-only mode, returning results")
            return None, geo_coordinates, search_duration

        # Generate plan
        logger.info("[PlanAgent] Generating travel plan with LLM...")
        prompted_message = plan_prompt.format(
            option_attractions=attraction_infos,
            user_content=user_content,
        )

        # Handle streaming mode
        if self._enable_stream:
            logger.info("[PlanAgent] Using streaming mode for plan generation")
            response = self._llm.multi_chat(
                messages=chat_history,
                user_content=prompted_message,
                pure_user_content=user_content,
            )
            return response, geo_coordinates, search_duration

        # Non-streaming mode with retry
        for attempt in range(self.DEFAULT_RETRY_COUNT):
            logger.info(f"[PlanAgent] Plan generation attempt {attempt + 1}/{self.DEFAULT_RETRY_COUNT}")
            status_code, response, _ = self._llm.multi_chat(
                messages=chat_history,
                user_content=prompted_message,
                pure_user_content=user_content,
            )
            if status_code == 200:
                logger.info(f"[PlanAgent] Plan generated successfully: {response[:100]}...")
                return response, geo_coordinates, search_duration

            logger.warning(
                f"[PlanAgent] Attempt {attempt + 1} failed with status {status_code}"
            )

        logger.error("[PlanAgent] All plan generation attempts failed")
        raise ValueError(
            f"Failed to generate plan after {self.DEFAULT_RETRY_COUNT} attempts"
        )

    async def achat(
        self,
        necessary_info: Dict[str, Any],
        chat_history: List[dict],
        summary: str,
        user_content: str,
        str_list: Optional[List[str]] = None,
        result_column_names: Optional[List[str]] = None,
        result_rows: Optional[List[Tuple]] = None,
        **kwargs,
    ) -> PlanResult:
        """
        Async version of plan generation.

        Args:
            necessary_info: Dictionary of required travel information.
            chat_history: Previous conversation history.
            summary: Summary of user's requirements.
            user_content: The user's latest message.
            str_list: Optional list to store SQL statements.
            result_column_names: Optional list to store column names.
            result_rows: Optional list to store result rows.
            **kwargs: Additional arguments (unused).

        Returns:
            Tuple of (plan_response, geo_coordinates, search_duration).

        Raises:
            ValueError: If executor not initialized or generation fails.
        """
        if self._executor is None:
            raise ValueError("Thread pool executor is not initialized")

        logger.info(f"[PlanAgent] Async plan generation with info: {necessary_info}")

        # Search for attractions
        logger.info("[PlanAgent] Async searching for attractions...")
        start_time = time.time()
        results = await self.run_in_executor(
            self._tool.call,
            necessary_info,
            summary,
            str_list,
        )
        search_duration = time.time() - start_time
        logger.info(f"[PlanAgent] Async search completed in {search_duration:.2f}s")

        # Process results
        attraction_infos, geo_coordinates = self._process_search_results(
            results,
            result_column_names,
            result_rows,
        )

        num_attractions = len(geo_coordinates) if geo_coordinates else 0
        logger.info(f"[PlanAgent] Found {num_attractions} attractions")

        # Return early if search-only mode
        if self._search_only:
            logger.info("[PlanAgent] Async search-only mode, returning results")
            return None, geo_coordinates, search_duration

        # Generate plan
        logger.info("[PlanAgent] Async generating travel plan...")
        prompted_message = plan_prompt.format(
            option_attractions=attraction_infos,
            user_content=user_content,
        )

        # Handle streaming mode
        if self._enable_stream:
            logger.info("[PlanAgent] Async streaming mode for plan")
            response = await self.run_in_executor(
                self._llm.multi_chat,
                chat_history,
                prompted_message,
                user_content,
            )
            return response, geo_coordinates, search_duration

        # Non-streaming mode with retry
        for attempt in range(self.DEFAULT_RETRY_COUNT):
            logger.info(f"[PlanAgent] Async attempt {attempt + 1}/{self.DEFAULT_RETRY_COUNT}")
            status_code, response, _ = await self.run_in_executor(
                self._llm.multi_chat,
                chat_history,
                prompted_message,
                user_content,
            )
            if status_code == 200:
                logger.info(f"[PlanAgent] Async plan generated: {response[:100]}...")
                return response, geo_coordinates, search_duration

            logger.warning(
                f"[PlanAgent] Async attempt {attempt + 1} failed with status {status_code}"
            )

        logger.error("[PlanAgent] All async attempts failed")
        raise ValueError(
            f"Failed to generate plan after {self.DEFAULT_RETRY_COUNT} attempts"
        )
