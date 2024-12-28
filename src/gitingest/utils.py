## Async Timeout decorator
import asyncio
import functools
from collections.abc import Awaitable, Callable
from typing import ParamSpec, TypeVar

T = TypeVar("T")
P = ParamSpec("P")


class AsyncTimeoutError(Exception):
    """Raised when an async operation exceeds its timeout limit."""


def async_timeout(seconds: int = 10) -> Callable[[Callable[P, Awaitable[T]]], Callable[P, Awaitable[T]]]:
    def decorator(func: Callable[P, Awaitable[T]]) -> Callable[P, Awaitable[T]]:
        @functools.wraps(func)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            try:
                return await asyncio.wait_for(func(*args, **kwargs), timeout=seconds)
            except asyncio.TimeoutError:
                raise AsyncTimeoutError(f"Operation timed out after {seconds} seconds")

        return wrapper

    return decorator
