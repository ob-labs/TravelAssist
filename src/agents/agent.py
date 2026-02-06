"""
Agent base class for OBMMS.

Provides the abstract base class for all agents with common
functionality like async execution and retry logic.
"""

import asyncio
from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor
from functools import wraps
from typing import Any, Callable, Optional, TypeVar, Union

from ..common.config import get_config
from ..common.logger import get_logger
from ..llm import LLM
from ..tools import Tool

logger = get_logger(__name__)


def with_logging(func: Callable) -> Callable:
    """
    Decorator to add logging to agent methods.

    Logs method entry, exit, and any exceptions.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        func_name = func.__name__
        class_name = args[0].__class__.__name__ if args else "Unknown"
        logger.debug(f"[{class_name}] Entering {func_name}")
        try:
            result = func(*args, **kwargs)
            logger.debug(f"[{class_name}] Exiting {func_name} successfully")
            return result
        except Exception as e:
            logger.error(f"[{class_name}] {func_name} failed with error: {e}")
            raise

    @wraps(func)
    async def async_wrapper(*args, **kwargs):
        func_name = func.__name__
        class_name = args[0].__class__.__name__ if args else "Unknown"
        logger.debug(f"[{class_name}] Entering async {func_name}")
        try:
            result = await func(*args, **kwargs)
            logger.debug(f"[{class_name}] Exiting async {func_name} successfully")
            return result
        except Exception as e:
            logger.error(f"[{class_name}] Async {func_name} failed with error: {e}")
            raise

    if asyncio.iscoroutinefunction(func):
        return async_wrapper
    return wrapper

T = TypeVar("T")


def with_retry(max_retries: int | None = None):
    """
    Decorator to add retry logic to agent methods.

    Args:
        max_retries: Maximum number of retry attempts. If None, uses config default.

    Returns:
        Decorated function with retry logic.
    """
    if max_retries is None:
        max_retries = get_config().default_retry_count

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            last_exception = None
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    logger.warning(
                        f"Attempt {attempt + 1}/{max_retries} failed: {e}"
                    )
            raise last_exception

        @wraps(func)
        async def async_wrapper(*args, **kwargs) -> T:
            last_exception = None
            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    logger.warning(
                        f"Attempt {attempt + 1}/{max_retries} failed: {e}"
                    )
            raise last_exception

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return wrapper

    return decorator


class Agent(ABC):
    """
    Abstract base class for agents.

    Agents are responsible for specific tasks in the travel planning
    workflow, such as extracting information, consulting users,
    summarizing requirements, and generating plans.

    Attributes:
        llm: The language model instance.
        tool: Optional tool for the agent to use.
        executor: Thread pool executor for async operations.
    """

    def __init__(
        self,
        llm: LLM,
        tool: Optional[Tool] = None,
        is_async: bool = False,
        max_workers: int | None = None,
    ) -> None:
        """
        Initialize the agent.

        Args:
            llm: The language model to use.
            tool: Optional tool for the agent.
            is_async: Whether to enable async operations.
            max_workers: Maximum worker threads for async executor. If None, uses config default.
        """
        cfg = get_config()
        self.DEFAULT_RETRY_COUNT = cfg.default_retry_count
        if max_workers is None:
            max_workers = cfg.max_workers
        self._llm = llm
        self._tool = tool
        self._is_async = is_async
        self._executor: Optional[ThreadPoolExecutor] = None

        if is_async:
            self._executor = ThreadPoolExecutor(max_workers=max_workers)

        logger.info(
            f"[{self.__class__.__name__}] Initialized with LLM={llm.model_name}, "
            f"async={is_async}, tool={tool}"
        )

    @property
    def llm(self) -> LLM:
        """Get the LLM instance."""
        return self._llm

    @property
    def tool(self) -> Optional[Tool]:
        """Get the tool instance."""
        return self._tool

    @property
    def executor(self) -> Optional[ThreadPoolExecutor]:
        """Get the thread pool executor."""
        return self._executor

    @property
    def is_async(self) -> bool:
        """Check if async mode is enabled."""
        return self._is_async

    async def run_in_executor(
        self,
        func: Callable[..., T],
        *args: Any,
        **kwargs: Any,
    ) -> T:
        """
        Run a blocking function in the thread pool executor.

        Args:
            func: The blocking function to run.
            *args: Positional arguments for the function.
            **kwargs: Keyword arguments for the function.

        Returns:
            The result of the function call.

        Raises:
            ValueError: If executor is not initialized or func is async.
        """
        if self._executor is None:
            raise ValueError("Thread pool executor is not initialized")

        if asyncio.iscoroutinefunction(func):
            raise ValueError(
                f"Function {func.__name__} is async, not a blocking function"
            )

        logger.debug(
            f"[{self.__class__.__name__}] Running {func.__name__} in executor"
        )

        loop = asyncio.get_event_loop()

        if kwargs:
            def wrapper():
                return func(*args, **kwargs)
            return await loop.run_in_executor(self._executor, wrapper)

        return await loop.run_in_executor(self._executor, func, *args)

    @abstractmethod
    def chat(self, **kwargs) -> Any:
        """
        Execute the agent's main chat functionality.

        This method must be implemented by subclasses to define
        the agent's specific behavior.

        Args:
            **kwargs: Agent-specific arguments.

        Returns:
            Agent-specific response.
        """
        pass

    async def achat(self, **kwargs) -> Any:
        """
        Async version of the chat method.

        Default implementation runs the sync chat in executor.
        Subclasses can override for truly async implementations.

        Args:
            **kwargs: Agent-specific arguments.

        Returns:
            Agent-specific response.
        """
        return await self.run_in_executor(self.chat, **kwargs)

    def __del__(self):
        """Clean up resources."""
        if self._executor:
            self._executor.shutdown(wait=False)
