from pathlib import Path

from gitingest import ingestion
from gitingest.query_parsing import IngestionQuery


def test_recursion_early_exit(monkeypatch, tmp_path):
    for i in range(5):
        (tmp_path / f"f{i}.txt").write_text("hi")

    query = IngestionQuery(
        user_name=None,
        repo_name=None,
        local_path=tmp_path,
        url=None,
        slug="slug",
        id="id",
    )

    monkeypatch.setattr(ingestion, "MAX_FILES", 2)
    summary, _, _ = ingestion.ingest_query(query)
    assert "Files analyzed: 2" in summary

