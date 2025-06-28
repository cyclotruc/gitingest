"""Compatibility utilities wrapping asyncio features that are missing on older Python versions (e.g. 3.8)."""

from __future__ import annotations

import asyncio
import contextvars
import functools
import sys
from typing import Callable, TypeVar

from gitingest.utils.compat_typing import ParamSpec

P = ParamSpec("P")
R = TypeVar("R")


if sys.version_info >= (3, 9):
    from asyncio import to_thread
else:

    async def to_thread(func: Callable[P, R], /, *args: P.args, **kwargs: P.kwargs) -> R:
        """Back-port :func:`asyncio.to_thread` for Python < 3.9.

        Run ``func`` in the default thread-pool executor and return the result.
        """
        loop = asyncio.get_running_loop()
        ctx = contextvars.copy_context()
        func_call = functools.partial(ctx.run, func, *args, **kwargs)
        return await loop.run_in_executor(None, func_call)

    # Patch stdlib so that *existing* imports of asyncio see the shim.
    if not hasattr(asyncio, "to_thread"):
        asyncio.to_thread = to_thread

__all__ = ["to_thread"]
