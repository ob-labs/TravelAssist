"""
Summary Agent for OBMMS.

Responsible for summarizing user's travel requirements from
the conversation history.
"""

from typing import Any, List, Optional

from ..common.config import get_config
from ..common.logger import get_logger
from ..llm import TongyiLLM, TongyiLLMConfig
from ..prompt import summary_prompt
from .agent import Agent

logger = get_logger(__name__)


class SummaryAgent(Agent):
    """
    Agent for summarizing user travel requirements.

    This agent analyzes the conversation history to extract and
    summarize the key characteristics of the user's desired
    travel destination.
    """

    def __init__(
        self,
        is_async: bool = False,
        model_name: str | None = None,
    ) -> None:
        """
        Initialize the Summary Agent.

        Args:
            is_async: Whether to enable async operations.
            model_name: The LLM model to use. If None, uses config default.
        """
        if model_name is None:
            model_name = get_config().default_llm_model
        config = TongyiLLMConfig(model_name=model_name)
        llm = TongyiLLM(config=config)
        super().__init__(llm=llm, is_async=is_async)

    def chat(
        self,
        chat_history: List[dict],
        user_content: str,
        **kwargs,
    ) -> str:
        """
        Summarize user's travel requirements.

        Args:
            chat_history: Previous conversation history.
            user_content: The user's latest message.
            **kwargs: Additional arguments (unused).

        Returns:
            A summary of user's travel requirements.

        Raises:
            ValueError: If summarization fails after retries.
        """
        logger.info(f"[SummaryAgent] Starting summarization, history length: {len(chat_history)}")
        prompted_message = summary_prompt.format(user_content=user_content)
        logger.debug(f"[SummaryAgent] Generated prompt length: {len(prompted_message)} chars")

        for attempt in range(self.DEFAULT_RETRY_COUNT):
            logger.info(f"[SummaryAgent] Attempt {attempt + 1}/{self.DEFAULT_RETRY_COUNT}")
            status_code, response, _ = self._llm.multi_chat(
                messages=chat_history,
                user_content=prompted_message,
                pure_user_content=user_content,
                use_for_history=False,
            )

            if status_code == 200:
                logger.info(f"[SummaryAgent] Generated summary: {response[:150]}...")
                return response

            logger.warning(
                f"[SummaryAgent] Attempt {attempt + 1} failed with status {status_code}"
            )

        logger.error("[SummaryAgent] All attempts failed")
        raise ValueError(
            f"Failed to generate summary after {self.DEFAULT_RETRY_COUNT} attempts"
        )

    async def achat(
        self,
        chat_history: List[dict],
        user_content: str,
        **kwargs,
    ) -> str:
        """
        Async version of summary chat.

        Args:
            chat_history: Previous conversation history.
            user_content: The user's latest message.
            **kwargs: Additional arguments (unused).

        Returns:
            A summary of user's travel requirements.

        Raises:
            ValueError: If executor not initialized or summarization fails.
        """
        if self._executor is None:
            raise ValueError("Thread pool executor is not initialized")

        logger.info(f"[SummaryAgent] Async summarization, history length: {len(chat_history)}")
        prompted_message = summary_prompt.format(user_content=user_content)

        for attempt in range(self.DEFAULT_RETRY_COUNT):
            logger.info(f"[SummaryAgent] Async attempt {attempt + 1}/{self.DEFAULT_RETRY_COUNT}")
            status_code, response, _ = await self.run_in_executor(
                self._llm.multi_chat,
                chat_history,
                prompted_message,
                user_content,
                False,  # use_for_history
            )

            if status_code == 200:
                logger.info(f"[SummaryAgent] Async summary: {response[:150]}...")
                return response

            logger.warning(
                f"[SummaryAgent] Async attempt {attempt + 1} failed with status {status_code}"
            )

        logger.error("[SummaryAgent] All async attempts failed")
        raise ValueError(
            f"Failed to generate summary after {self.DEFAULT_RETRY_COUNT} attempts"
        )
