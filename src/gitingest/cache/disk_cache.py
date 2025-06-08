import json
import tempfile
from pathlib import Path
from typing import Any


class ChunkCache:
    """Very small disk-backed cache used for tests."""

    def __init__(self, path: Path | None = None) -> None:
        self.path = path or Path(tempfile.gettempdir()) / "gitingest_cache.json"
        if self.path.exists():
            try:
                self._data = json.loads(self.path.read_text())
            except Exception:
                self._data = {}
        else:
            self._data = {}

    def get(self, file: Path) -> Any:
        return self._data.get(str(file))

    def set(self, file: Path, value: Any) -> None:
        self._data[str(file)] = value

    def flush(self) -> None:
        self.path.write_text(json.dumps(self._data))
