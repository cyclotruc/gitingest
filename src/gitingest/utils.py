
## Async Timeout decorator
import asyncio
import functools
from typing import TypeVar, Callable

T = TypeVar("T")

class AsyncTimeoutError(Exception):
    """Raised when an async operation exceeds its timeout limit."""
    pass

def async_timeout(seconds: int = 10):
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            try:
                return await asyncio.wait_for(func(*args, **kwargs), timeout=seconds)
            except asyncio.TimeoutError:
                raise AsyncTimeoutError(f"Clone timed out after {seconds} seconds")
        return wrapper
    return decorator