"""
Tests for LangGraph-based workflow.

This module contains unit tests for the TravelWorkflow class
and related functions in travel_assist_flow.py.
"""

import unittest
from unittest.mock import MagicMock, patch

from src.agents.travel_assist_flow import (
    TravelGraphState,
    TravelWorkflow,
    WorkflowResponse,
    build_async_graph,
    build_sync_graph,
    get_missing_fields,
    get_user_info_dict,
    is_info_complete,
    route_after_extract,
    update_user_state,
)
from src.common import (
    FIELD_DEPARTURE,
    FIELD_DEPARTURE_CN,
    FIELD_DISTANCE,
    FIELD_DISTANCE_CN,
    FIELD_SCORE,
    FIELD_SCORE_CN,
    FIELD_SEASON,
    FIELD_SEASON_CN,
)


class TestStateHelpers(unittest.TestCase):
    """Tests for state helper functions."""

    def test_update_user_state_new_values(self):
        """Test updating state with all new values."""
        state: TravelGraphState = {
            "user_content": "test",
            "chat_history": [],
            "departure": None,
            "distance": None,
            "score": None,
            "season": None,
            "is_complete": False,
            "need_reset": False,
            "success": True,
        }

        extracted = {
            FIELD_DEPARTURE: "杭州",
            FIELD_DISTANCE: "100公里",
            FIELD_SCORE: 90,
            FIELD_SEASON: "春季",
        }

        updates = update_user_state(state, extracted)

        self.assertEqual(updates["departure"], "杭州")
        self.assertEqual(updates["distance"], "100公里")
        self.assertEqual(updates["score"], 90)
        self.assertEqual(updates["season"], "春季")

    def test_update_user_state_score_max(self):
        """Test score update uses max strategy."""
        state: TravelGraphState = {
            "user_content": "test",
            "chat_history": [],
            "departure": None,
            "distance": None,
            "score": 85,
            "season": None,
            "is_complete": False,
            "need_reset": False,
            "success": True,
        }

        # New score is higher
        updates = update_user_state(state, {FIELD_SCORE: 90})
        self.assertEqual(updates["score"], 90)

        # New score is lower
        updates = update_user_state(state, {FIELD_SCORE: 80})
        self.assertEqual(updates["score"], 85)

    def test_update_user_state_season_concat(self):
        """Test season update uses concat strategy."""
        state: TravelGraphState = {
            "user_content": "test",
            "chat_history": [],
            "departure": None,
            "distance": None,
            "score": None,
            "season": "春季",
            "is_complete": False,
            "need_reset": False,
            "success": True,
        }

        updates = update_user_state(state, {FIELD_SEASON: "秋季"})
        self.assertEqual(updates["season"], "春季秋季")

    def test_get_missing_fields(self):
        """Test getting missing field display names."""
        state: TravelGraphState = {
            "user_content": "test",
            "chat_history": [],
            "departure": "杭州",
            "distance": None,
            "score": 90,
            "season": None,
            "is_complete": False,
            "need_reset": False,
            "success": True,
        }

        missing = get_missing_fields(state)
        self.assertIn(FIELD_DISTANCE_CN, missing)
        self.assertIn(FIELD_SEASON_CN, missing)
        self.assertNotIn(FIELD_DEPARTURE_CN, missing)
        self.assertNotIn(FIELD_SCORE_CN, missing)

    def test_is_info_complete_true(self):
        """Test info completeness check when all fields are filled."""
        state: TravelGraphState = {
            "user_content": "test",
            "chat_history": [],
            "departure": "杭州",
            "distance": "100公里",
            "score": 90,
            "season": "春季",
            "is_complete": False,
            "need_reset": False,
            "success": True,
        }

        self.assertTrue(is_info_complete(state))

    def test_is_info_complete_false(self):
        """Test info completeness check when some fields are missing."""
        state: TravelGraphState = {
            "user_content": "test",
            "chat_history": [],
            "departure": "杭州",
            "distance": None,
            "score": 90,
            "season": None,
            "is_complete": False,
            "need_reset": False,
            "success": True,
        }

        self.assertFalse(is_info_complete(state))

    def test_get_user_info_dict(self):
        """Test extracting user info as dictionary."""
        state: TravelGraphState = {
            "user_content": "test",
            "chat_history": [],
            "departure": "杭州",
            "distance": "100公里",
            "score": 90,
            "season": "春季",
            "is_complete": True,
            "need_reset": False,
            "success": True,
        }

        info = get_user_info_dict(state)
        self.assertEqual(info[FIELD_DEPARTURE], "杭州")
        self.assertEqual(info[FIELD_DISTANCE], "100公里")
        self.assertEqual(info[FIELD_SCORE], 90)
        self.assertEqual(info[FIELD_SEASON], "春季")


class TestRouting(unittest.TestCase):
    """Tests for routing functions."""

    def test_route_after_extract_to_summary(self):
        """Test routing to summary when info is complete."""
        state: TravelGraphState = {
            "user_content": "test",
            "chat_history": [],
            "is_complete": True,
            "success": True,
        }

        result = route_after_extract(state)
        self.assertEqual(result, "summary")

    def test_route_after_extract_to_consult(self):
        """Test routing to consult when info is incomplete."""
        state: TravelGraphState = {
            "user_content": "test",
            "chat_history": [],
            "is_complete": False,
            "success": True,
        }

        result = route_after_extract(state)
        self.assertEqual(result, "consult")

    def test_route_after_extract_on_error(self):
        """Test routing to END on error."""
        from langgraph.graph import END

        state: TravelGraphState = {
            "user_content": "test",
            "chat_history": [],
            "is_complete": False,
            "success": False,
        }

        result = route_after_extract(state)
        self.assertEqual(result, END)


class TestGraphBuilder(unittest.TestCase):
    """Tests for graph building functions."""

    def test_build_sync_graph(self):
        """Test synchronous graph is built correctly."""
        graph = build_sync_graph()
        # Graph should be compiled (has invoke method)
        self.assertTrue(hasattr(graph, "invoke"))

    def test_build_async_graph(self):
        """Test asynchronous graph is built correctly."""
        graph = build_async_graph()
        # Graph should be compiled (has ainvoke method)
        self.assertTrue(hasattr(graph, "ainvoke"))


class TestWorkflowResponse(unittest.TestCase):
    """Tests for WorkflowResponse model."""

    def test_default_values(self):
        """Test default values are set correctly."""
        response = WorkflowResponse()
        self.assertTrue(response.success)
        self.assertEqual(response.reply, "")
        self.assertFalse(response.need_reset)
        self.assertIsNone(response.sql)
        self.assertIsNone(response.datas)

    def test_custom_values(self):
        """Test custom values are set correctly."""
        response = WorkflowResponse(
            success=False,
            reply="Error occurred",
            need_reset=True,
            departure="杭州",
        )
        self.assertFalse(response.success)
        self.assertEqual(response.reply, "Error occurred")
        self.assertTrue(response.need_reset)
        self.assertEqual(response.departure, "杭州")


class TestTravelWorkflow(unittest.TestCase):
    """Tests for TravelWorkflow class."""

    def test_init_default(self):
        """Test initialization with default values."""
        workflow = TravelWorkflow()
        self.assertEqual(workflow._chat_history, [])
        self.assertIsNone(workflow._departure)
        self.assertIsNone(workflow._distance)
        self.assertIsNone(workflow._score)
        self.assertIsNone(workflow._season)

    def test_init_with_values(self):
        """Test initialization with provided values."""
        history = [{"role": "user", "content": "hello"}]
        workflow = TravelWorkflow(
            chat_history=history,
            departure="杭州",
            distance="100公里",
            score=90,
            season="春季",
        )
        self.assertEqual(workflow._chat_history, history)
        self.assertEqual(workflow._departure, "杭州")
        self.assertEqual(workflow._distance, "100公里")
        self.assertEqual(workflow._score, 90)
        self.assertEqual(workflow._season, "春季")

    def test_create_initial_state(self):
        """Test initial state creation."""
        workflow = TravelWorkflow(
            departure="杭州",
            score=90,
        )
        state = workflow._create_initial_state("test content")

        self.assertEqual(state["user_content"], "test content")
        self.assertEqual(state["departure"], "杭州")
        self.assertEqual(state["score"], 90)
        self.assertIsNone(state["distance"])
        self.assertIsNone(state["season"])
        self.assertFalse(state["is_complete"])
        self.assertFalse(state["need_reset"])
        self.assertTrue(state["success"])


class TestTravelWorkflowIntegration(unittest.TestCase):
    """Integration tests for TravelWorkflow (requires mocking)."""

    @patch("src.agents.travel_assist_flow.ExtractAgent")
    @patch("src.agents.travel_assist_flow.ConsultAgent")
    def test_run_incomplete_info(self, mock_consult_cls, mock_extract_cls):
        """Test workflow run when info is incomplete (goes to consult)."""
        # Mock extract agent
        mock_extract = MagicMock()
        mock_extract.chat.return_value = {
            FIELD_DEPARTURE: "杭州",
            FIELD_DISTANCE: None,
            FIELD_SCORE: None,
            FIELD_SEASON: None,
        }
        mock_extract_cls.return_value = mock_extract

        # Mock consult agent
        mock_consult = MagicMock()
        mock_consult.chat.return_value = "请告诉我行程范围、景点评分要求和出行季节"
        mock_consult_cls.return_value = mock_consult

        # Mock geocode to avoid network call
        with patch("src.agents.travel_assist_flow.geocode") as mock_geocode:
            mock_geocode.return_value = (30.25, 120.16)

            workflow = TravelWorkflow()
            streamer, response = workflow.run("我想去杭州旅游")

            # Should return consult response
            self.assertTrue(response.success)
            self.assertFalse(response.need_reset)
            self.assertEqual(response.departure, "杭州")
            # Streamer should be the consult response
            self.assertIsNotNone(streamer)


if __name__ == "__main__":
    unittest.main()
