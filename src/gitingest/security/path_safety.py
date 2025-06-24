from pathlib import Path


def is_safe_path(base: Path, target: Path) -> bool:
    """Return True if the resolved target is within base and not a symlink outside."""
    try:
        return base in target.resolve(strict=False).parents
    except RuntimeError:
        # Cyclic symlink
        return False
