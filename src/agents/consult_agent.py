"""
Consult Agent for OBMMS.

Responsible for guiding users to provide missing travel information
through friendly conversation.
"""

from typing import Any, Generator, List, Optional, Union

from ..common import format_numbered_list
from ..common.config import get_config
from ..common.logger import get_logger
from ..llm import TongyiLLM, TongyiLLMConfig
from ..prompt import consult_prompt
from .agent import Agent

logger = get_logger(__name__)


class ConsultAgent(Agent):
    """
    Agent for consulting users about missing travel information.

    This agent guides users through a friendly conversation to gather
    necessary information about their travel preferences that wasn't
    provided in their initial input.
    """

    def __init__(
        self,
        enable_stream: bool = False,
        is_async: bool = False,
        model_name: str | None = None,
    ) -> None:
        """
        Initialize the Consult Agent.

        Args:
            enable_stream: Whether to enable streaming output.
            is_async: Whether to enable async operations.
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
        super().__init__(llm=llm, is_async=is_async)
        self._enable_stream = enable_stream

    @property
    def enable_stream(self) -> bool:
        """Check if streaming is enabled."""
        return self._enable_stream

    def _format_necessary_info(self, necessary_list: List[str]) -> str:
        """
        Format the list of required information as a numbered list.

        Args:
            necessary_list: List of missing required information.

        Returns:
            Formatted numbered list string.
        """
        return format_numbered_list(necessary_list)

    def chat(
        self,
        necessary_list: List[str],
        chat_history: List[dict],
        user_content: str,
        **kwargs,
    ) -> Union[str, Generator]:
        """
        Guide user to provide missing information.

        Args:
            necessary_list: List of information items still needed.
            chat_history: Previous conversation history.
            user_content: The user's latest message.
            **kwargs: Additional arguments (unused).

        Returns:
            If streaming: A generator yielding response chunks.
            Otherwise: The assistant's response string.

        Raises:
            ValueError: If the LLM request fails.
        """
        logger.info(f"[ConsultAgent] Starting consultation, missing fields: {necessary_list}")
        logger.debug(f"[ConsultAgent] Chat history length: {len(chat_history)}")
        
        necessary_str = self._format_necessary_info(necessary_list)

        prompted_message = consult_prompt.format(
            attraction_info=necessary_str,
            user_content=user_content,
        )

        logger.debug(f"[ConsultAgent] Generated prompt length: {len(prompted_message)} chars")

        # Handle streaming mode
        if self._enable_stream:
            logger.info("[ConsultAgent] Using streaming mode")
            return self._llm.multi_chat(
                messages=chat_history,
                user_content=prompted_message,
                pure_user_content=user_content,
            )

        # Non-streaming mode with retry
        for attempt in range(self.DEFAULT_RETRY_COUNT):
            logger.info(f"[ConsultAgent] Attempt {attempt + 1}/{self.DEFAULT_RETRY_COUNT}")
            status_code, response, _ = self._llm.multi_chat(
                messages=chat_history,
                user_content=prompted_message,
                pure_user_content=user_content,
            )
            if status_code == 200:
                logger.info(f"[ConsultAgent] Response generated: {response[:100]}...")
                return response

            logger.warning(
                f"[ConsultAgent] Attempt {attempt + 1} failed with status {status_code}"
            )

        logger.error("[ConsultAgent] All attempts failed")
        raise ValueError(f"Failed to consult user after {self.DEFAULT_RETRY_COUNT} attempts")

    async def achat(
        self,
        necessary_list: List[str],
        chat_history: List[dict],
        user_content: str,
        **kwargs,
    ) -> Union[str, Generator]:
        """
        Async version of consult chat.

        Args:
            necessary_list: List of information items still needed.
            chat_history: Previous conversation history.
            user_content: The user's latest message.
            **kwargs: Additional arguments (unused).

        Returns:
            If streaming: A generator yielding response chunks.
            Otherwise: The assistant's response string.

        Raises:
            ValueError: If executor not initialized or LLM request fails.
        """
        if self._executor is None:
            raise ValueError("Thread pool executor is not initialized")

        logger.info(f"[ConsultAgent] Async consultation, missing fields: {necessary_list}")
        
        necessary_str = self._format_necessary_info(necessary_list)

        prompted_message = consult_prompt.format(
            attraction_info=necessary_str,
            user_content=user_content,
        )

        # Handle streaming mode
        if self._enable_stream:
            logger.info("[ConsultAgent] Async streaming mode")
            return await self.run_in_executor(
                self._llm.multi_chat,
                chat_history,
                prompted_message,
                user_content,
            )

        # Non-streaming mode with retry
        for attempt in range(self.DEFAULT_RETRY_COUNT):
            logger.info(f"[ConsultAgent] Async attempt {attempt + 1}/{self.DEFAULT_RETRY_COUNT}")
            status_code, response, _ = await self.run_in_executor(
                self._llm.multi_chat,
                chat_history,
                prompted_message,
                user_content,
            )
            if status_code == 200:
                logger.info(f"[ConsultAgent] Async response: {response[:100]}...")
                return response

            logger.warning(
                f"[ConsultAgent] Async attempt {attempt + 1} failed with status {status_code}"
            )

        logger.error("[ConsultAgent] All async attempts failed")
        raise ValueError(f"Failed to consult user after {self.DEFAULT_RETRY_COUNT} attempts")
