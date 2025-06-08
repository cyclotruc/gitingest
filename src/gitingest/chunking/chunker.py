from dataclasses import dataclass
from pathlib import Path

from .language_registry import build_parser, get_lang_from_path


@dataclass
class Chunk:
    path: str
    index: int
    kind: str
    text: str


def _split_long(text: str, max_lines: int):
    lines = text.splitlines()
    for i in range(0, len(lines), max_lines):
        yield "\n".join(lines[i : i + max_lines])


def chunk_file(path: Path, max_lines: int = 400) -> list[Chunk]:
    lang_name = get_lang_from_path(path)
    if not lang_name:
        try:
            text = path.read_text()
        except UnicodeDecodeError:
            text = "[Non-text file]"
        return [Chunk(str(path), 0, "file", text)]

    parser, query = build_parser(lang_name)
    source = path.read_bytes()
    tree = parser.parse(source)
    root = tree.root_node
    chunks: list[Chunk] = []
    idx = 0

    for node, cap_name in query.captures(root):
        start, end = node.start_byte, node.end_byte
        text = source[start:end].decode()
        if text.count("\n") > max_lines:
            for sub in _split_long(text, max_lines):
                chunks.append(Chunk(str(path), idx, cap_name.split(".")[0], sub))
                idx += 1
        else:
            chunks.append(Chunk(str(path), idx, cap_name.split(".")[0], text))
            idx += 1

    if not chunks:
        try:
            text = source.decode()
        except UnicodeDecodeError:
            text = "[Non-text file]"
        chunks.append(Chunk(str(path), 0, "file", text))
    return chunks


