"""
Tongyi (通义千问) LLM implementation.

Provides integration with Alibaba Cloud's Tongyi Qianwen model
through the DashScope API.
"""

from typing import Generator, List, Union

import dashscope

from ..common.config import get_config
from ..common.logger import get_logger
from .llm import ChatResult, LLM, LLMConfig

logger = get_logger(__name__)


class TongyiLLMConfig(LLMConfig):
    """
    Configuration specific to Tongyi LLM.

    Inherits all settings from LLMConfig with Tongyi-specific defaults.
    """

    pass


class TongyiLLM(LLM):
    """
    Tongyi Qianwen LLM implementation using DashScope API.

    This class provides integration with Alibaba Cloud's Tongyi Qianwen
    model for both single-turn and multi-turn conversations.
    """

    SYSTEM_PROMPT = "You are a helpful assistant."

    def __init__(self, config: TongyiLLMConfig) -> None:
        """
        Initialize the Tongyi LLM.

        Args:
            config: Tongyi LLM configuration.
        """
        super().__init__(config)
        self._api_key = get_config().dashscope_api_key

    @property
    def api_key(self) -> str:
        """Get the DashScope API key."""
        return self._api_key

    def chat(self, prompt: str) -> Union[dashscope.Generation, Generator]:
        """
        Send a single prompt to Tongyi Qianwen.

        Args:
            prompt: The input prompt string.

        Returns:
            If streaming: A generator yielding response chunks.
            Otherwise: The DashScope Generation response object.
        """
        logger.info(f"[TongyiLLM] Calling model {self._config.model_name}")
        logger.debug(f"[TongyiLLM] Prompt length: {len(prompt)} chars")
        
        response = dashscope.Generation.call(
            model=self._config.model_name,
            prompt=prompt,
            history=None,
            api_key=self._api_key,
            stream=self._config.stream,
            incremental_output=self._config.incremental_output,
            top_p=self._config.top_p,
            temperature=self._config.temperature,
        )
        
        # Return generator for streaming mode
        if self._config.stream:
            logger.info("[TongyiLLM] Returning streaming response")
            return response
        
        # Process non-streaming response
        logger.info(f"[TongyiLLM] Response status: {response.status_code}")
        logger.debug(f"[TongyiLLM] Response: {str(response)[:200]}...")
        return response

    def multi_chat(
        self,
        messages: List[dict],
        user_content: str,
        pure_user_content: str,
        use_for_history: bool = True,
    ) -> Union[ChatResult, Generator]:
        """
        Send a multi-turn chat to Tongyi Qianwen.

        Args:
            messages: Previous chat messages in the conversation.
            user_content: The formatted user content (may include prompts).
            pure_user_content: The original user input.
            use_for_history: Whether to append this exchange to history.

        Returns:
            If streaming: A generator yielding response chunks.
            Otherwise: A tuple of (status_code, response_text, updated_messages).
        """
        logger.info(f"[TongyiLLM] Multi-chat with {len(messages)} messages in history")
        logger.debug(f"[TongyiLLM] Stream mode: {self._config.stream}")
        
        # Build message list with system prompt
        new_messages = [{"role": "system", "content": self.SYSTEM_PROMPT}]
        new_messages.extend(messages)
        new_messages.append({"role": "user", "content": user_content})

        logger.debug(f"[TongyiLLM] Total messages: {len(new_messages)}")

        response = dashscope.Generation.call(
            model=self._config.model_name,
            messages=new_messages,
            api_key=self._api_key,
            stream=self._config.stream,
            incremental_output=self._config.incremental_output,
            top_p=self._config.top_p,
            temperature=self._config.temperature,
            result_format="message",
        )

        # Return generator for streaming mode
        if self._config.stream:
            logger.info("[TongyiLLM] Returning streaming response")
            return response

        # Process non-streaming response
        logger.info(f"[TongyiLLM] Response status: {response.status_code}")
        
        if response.status_code == 200:
            assistant_message = response.output.choices[0]["message"]
            logger.debug(f"[TongyiLLM] Response content: {assistant_message['content'][:100]}...")
            
            if use_for_history:
                messages.append({"role": "user", "content": pure_user_content})
                messages.append({
                    "role": assistant_message["role"],
                    "content": assistant_message["content"],
                })
                logger.debug(f"[TongyiLLM] Updated history, now {len(messages)} messages")

            return response.status_code, assistant_message["content"], messages

        logger.warning(f"[TongyiLLM] Chat failed with status {response.status_code}")
        return response.status_code, "", messages
