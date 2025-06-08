from pathlib import Path
from tree_sitter_languages import get_language, get_parser

LANGUAGE_QUERIES = {
    "python": "languages/python.scm",
    "javascript": "languages/javascript.scm",
}

EXT_TO_LANG = {
    ".py": "python",
    ".js": "javascript",
    ".ts": "javascript",
}

def get_lang_from_path(path: Path):
    return EXT_TO_LANG.get(path.suffix.lower())


def build_parser(language_name: str):
    lang = get_language(language_name)
    parser = get_parser(language_name)
    query_path = Path(__file__).resolve().parent / LANGUAGE_QUERIES[language_name]
    query = lang.query(query_path.read_text())
    return parser, query
