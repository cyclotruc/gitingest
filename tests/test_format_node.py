from pathlib import Path
from gitingest.output_formatters import format_node
from gitingest.schemas import FileSystemNode, FileSystemNodeType
from gitingest.query_parsing import IngestionQuery


def test_tree_called_once(monkeypatch, tmp_path):
    node = FileSystemNode(
        name="file.txt",
        type=FileSystemNodeType.FILE,
        path_str="file.txt",
        path=tmp_path / "file.txt",
        size=4,
        file_count=1,
    )
    node.path.write_text("text")
    query = IngestionQuery(
        user_name=None,
        repo_name=None,
        local_path=tmp_path,
        url=None,
        slug="slug",
        id="id",
    )
    calls = []

    def fake_create(q, node, prefix="", is_last=True):
        calls.append(1)
        return "tree"

    monkeypatch.setattr("gitingest.output_formatters._create_tree_structure", fake_create)
    format_node(node, query)
    assert len(calls) == 1

