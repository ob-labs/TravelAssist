"""
LLM module for OBMMS.

Provides LLM interfaces and implementations.
"""

from .llm import LLM, LLMConfig, ChatResult
from .tongyi import TongyiLLM, TongyiLLMConfig

__all__ = [
    "LLM",
    "LLMConfig",
    "ChatResult",
    "TongyiLLM",
    "TongyiLLMConfig",
]
