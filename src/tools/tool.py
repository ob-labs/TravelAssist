"""
Tool base class for OBMMS.

Provides the abstract interface for tools that agents can use
to perform specific actions like database queries.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict


class Tool(ABC):
    """
    Abstract base class for agent tools.

    Tools provide specific capabilities that agents can use to
    perform actions such as database queries, API calls, etc.
    """

    @abstractmethod
    def call(self, **kwargs) -> Any:
        """
        Execute the tool's main functionality.

        Args:
            **kwargs: Tool-specific arguments.

        Returns:
            Tool-specific result.
        """
        pass

    def __repr__(self) -> str:
        """Return string representation of the tool."""
        return f"<{self.__class__.__name__}>"
