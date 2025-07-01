"""Compatibility layer for typing."""

try:
    from typing import ParamSpec, TypeAlias  # Py ≥ 3.10
except ImportError:
    from typing_extensions import ParamSpec, TypeAlias  # Py 3.8 / 3.9

try:
    from typing import Annotated  # Py ≥ 3.9
except ImportError:
    from typing_extensions import Annotated  # Py 3.8

__all__ = ["Annotated", "ParamSpec", "TypeAlias"]
