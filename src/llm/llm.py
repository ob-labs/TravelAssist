"""
LLM base classes and interfaces.

Provides abstract base class for LLM implementations and
configuration dataclass.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Generator, List, Optional, Tuple, Union


@dataclass
class LLMConfig:
    """
    Configuration for LLM instances.

    Attributes:
        model_name: The name of the LLM model to use.
        top_p: Nucleus sampling parameter (0-1).
        temperature: Sampling temperature (0-2).
        stream: Whether to enable streaming output.
        incremental_output: Whether to output incrementally in streaming mode.
        max_chat_rounds: Maximum rounds for multi-turn chat history.
    """

    model_name: str = "qwen-plus"
    top_p: float = 0.1
    temperature: float = 0.3
    stream: bool = False
    incremental_output: bool = False
    max_chat_rounds: int = 3


# Type alias for LLM response
LLMResponse = Union[Any, Generator]
ChatResult = Tuple[int, str, List[dict]]


class LLM(ABC):
    """
    Abstract base class for Large Language Model implementations.

    Subclasses must implement the `chat` and `multi_chat` methods
    to provide model-specific functionality.
    """

    def __init__(self, config: LLMConfig) -> None:
        """
        Initialize the LLM with the given configuration.

        Args:
            config: LLM configuration settings.
        """
        self._config = config

    @property
    def config(self) -> LLMConfig:
        """Get the LLM configuration."""
        return self._config

    @property
    def model_name(self) -> str:
        """Get the model name."""
        return self._config.model_name

    @property
    def is_streaming(self) -> bool:
        """Check if streaming is enabled."""
        return self._config.stream

    @abstractmethod
    def chat(self, prompt: str) -> LLMResponse:
        """
        Send a single prompt to the LLM.

        Args:
            prompt: The input prompt string.

        Returns:
            The LLM response object.
        """
        pass

    @abstractmethod
    def multi_chat(
        self,
        messages: List[dict],
        user_content: str,
        pure_user_content: str,
        use_for_history: bool = True,
    ) -> Union[ChatResult, Generator]:
        """
        Send a multi-turn chat to the LLM.

        Args:
            messages: Previous chat messages in the conversation.
            user_content: The formatted user content (may include prompts).
            pure_user_content: The original user input.
            use_for_history: Whether to append this exchange to history.

        Returns:
            If streaming: A generator yielding response chunks.
            Otherwise: A tuple of (status_code, response_text, updated_messages).
        """
        pass
