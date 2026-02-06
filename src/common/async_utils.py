"""
Async utilities for OBMMS.

Provides async helpers for running blocking functions.
"""

import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Callable, TypeVar

T = TypeVar("T")


async def run_blocking_in_executor(
    executor: ThreadPoolExecutor,
    func: Callable[..., T],
    *args: Any,
    **kwargs: Any,
) -> T:
    """
    Run a blocking function in a thread pool executor.

    Args:
        executor: The ThreadPoolExecutor to use.
        func: The blocking function to run.
        *args: Positional arguments to pass to the function.
        **kwargs: Keyword arguments to pass to the function.

    Returns:
        The result of the function call.

    Raises:
        ValueError: If the function is a coroutine function.
    """
    if asyncio.iscoroutinefunction(func):
        raise ValueError(f"The function {func.__name__} is a coroutine function, not a blocking function")

    loop = asyncio.get_event_loop()

    # If kwargs are provided, wrap the call
    if kwargs:
        def wrapper():
            return func(*args, **kwargs)
        return await loop.run_in_executor(executor, wrapper)

    return await loop.run_in_executor(executor, func, *args)


def create_executor(max_workers: int = 8) -> ThreadPoolExecutor:
    """
    Create a ThreadPoolExecutor with the specified number of workers.

    Args:
        max_workers: Maximum number of worker threads.

    Returns:
        A new ThreadPoolExecutor instance.
    """
    return ThreadPoolExecutor(max_workers=max_workers)
