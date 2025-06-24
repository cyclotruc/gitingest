import pytest
from pydantic import ValidationError

from gitingest.ingestion import apply_gitingest_file
from gitingest.query_parsing import IngestionQuery


def test_gitingest_config_unknown_key(tmp_path):
    cfg = tmp_path / ".gitingest"
    cfg.write_text("""
[config]
ignore_patterns = ["*.py"]
foo = "bar"
""")
    query = IngestionQuery(
        user_name=None,
        repo_name=None,
        local_path=tmp_path,
        url=None,
        slug="slug",
        id="id",
    )
    with pytest.raises(ValidationError):
        apply_gitingest_file(tmp_path, query)

