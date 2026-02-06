"""
Extract Agent for OBMMS.

Responsible for extracting travel-related information from user input,
including destination, distance, score requirements, and season preferences.
"""

from typing import Any, Dict, Optional

from ..common import extract_json_from_response
from ..common.config import get_config
from ..common.logger import get_logger
from ..llm import TongyiLLM, TongyiLLMConfig
from ..prompt import extract_info_prompt
from .agent import Agent

logger = get_logger(__name__)


class ExtractAgent(Agent):
    """
    Agent for extracting travel information from user input.

    This agent analyzes user messages to extract structured information
    about travel preferences such as destination, travel range, score
    requirements, and preferred seasons.
    """

    def __init__(
        self,
        is_async: bool = False,
        model_name: str | None = None,
    ) -> None:
        """
        Initialize the Extract Agent.

        Args:
            is_async: Whether to enable async operations.
            model_name: The LLM model to use. If None, uses config default.
        """
        if model_name is None:
            model_name = get_config().default_llm_model
        config = TongyiLLMConfig(model_name=model_name)
        llm = TongyiLLM(config=config)
        super().__init__(llm=llm, is_async=is_async)

    def _parse_response(self, response: Any) -> Dict[str, Any]:
        """
        Parse the LLM response and extract JSON data.

        Args:
            response: The raw LLM response.

        Returns:
            Extracted information as a dictionary.

        Raises:
            ValueError: If response parsing fails.
        """
        if response.status_code != 200:
            raise ValueError(
                f"LLM request failed with status {response.status_code}: "
                f"{getattr(response, 'message', 'Unknown error')}"
            )

        response_text = str(response.output.text)
        logger.debug(f"Extract agent raw response: {response_text}")

        return extract_json_from_response(response_text)

    def chat(self, user_content: str, **kwargs) -> Dict[str, Any]:
        """
        Extract travel information from user content.

        Args:
            user_content: The user's input message.
            **kwargs: Additional arguments (unused).

        Returns:
            A dictionary containing extracted information:
            - departure: Travel destination (city/province)
            - distance: Travel range
            - score: Minimum attraction score requirement
            - season: Preferred travel season

        Raises:
            ValueError: If extraction fails after retries.
        """
        logger.info(f"[ExtractAgent] Starting extraction for user input: {user_content[:100]}...")
        prompted_message = extract_info_prompt.format(user_info=user_content)
        logger.debug(f"[ExtractAgent] Generated prompt length: {len(prompted_message)} chars")

        last_exception: Optional[Exception] = None
        
        for attempt in range(self.DEFAULT_RETRY_COUNT):
            logger.info(f"[ExtractAgent] Attempt {attempt + 1}/{self.DEFAULT_RETRY_COUNT}")
            try:
                response = self._llm.chat(prompt=prompted_message)
                result = self._parse_response(response)
                logger.info(f"[ExtractAgent] Successfully extracted: {result}")
                return result
            except Exception as e:
                last_exception = e
                logger.warning(f"[ExtractAgent] Attempt {attempt + 1} failed: {e}")

        logger.error(f"[ExtractAgent] All attempts failed. Last error: {last_exception}")
        raise ValueError(
            f"Failed to extract information after {self.DEFAULT_RETRY_COUNT} attempts: "
            f"{last_exception}"
        )

    async def achat(self, user_content: str, **kwargs) -> Dict[str, Any]:
        """
        Async version of extract chat.

        Args:
            user_content: The user's input message.
            **kwargs: Additional arguments (unused).

        Returns:
            A dictionary containing extracted information.

        Raises:
            ValueError: If extraction fails.
        """
        if self._executor is None:
            raise ValueError("Thread pool executor is not initialized")

        logger.info(f"[ExtractAgent] Async extraction for: {user_content[:100]}...")
        prompted_message = extract_info_prompt.format(user_info=user_content)

        last_exception: Optional[Exception] = None

        for attempt in range(self.DEFAULT_RETRY_COUNT):
            logger.info(f"[ExtractAgent] Async attempt {attempt + 1}/{self.DEFAULT_RETRY_COUNT}")
            try:
                response = await self.run_in_executor(
                    self._llm.chat,
                    prompted_message,
                )
                result = self._parse_response(response)
                logger.info(f"[ExtractAgent] Async extracted: {result}")
                return result
            except Exception as e:
                last_exception = e
                logger.warning(f"[ExtractAgent] Async attempt {attempt + 1} failed: {e}")

        logger.error(f"[ExtractAgent] All async attempts failed. Last error: {last_exception}")
        raise ValueError(
            f"Failed to extract information after {self.DEFAULT_RETRY_COUNT} attempts: "
            f"{last_exception}"
        )
