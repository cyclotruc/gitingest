"""Helper utilities for mapping file extensions to Tree-sitter parsers."""

from pathlib import Path

from tree_sitter_languages import get_language, get_parser

LANGUAGE_QUERIES = {
    "python": "languages/python.scm",
    "javascript": "languages/javascript.scm",
    "go": "languages/go.scm",  # <-- ADDED
}

EXT_TO_LANG = {
    ".py": "python",
    ".js": "javascript",
    ".ts": "javascript",
    ".go": "go",  # <-- ADDED
}


def get_lang_from_path(path: Path) -> str | None:
    """Return the registered language for a given file path.

    Parameters
    ----------
    path : Path
        File path to inspect.

    Returns
    -------
    str | None
        The detected language name, or ``None`` if the extension is unknown.
    """

    return EXT_TO_LANG.get(path.suffix.lower())


def build_parser(language_name: str):
    """Build and return a Tree-sitter parser and query for a language.

    Parameters
    ----------
    language_name : str
        The language key as defined in :data:`LANGUAGE_QUERIES`.

    Returns
    -------
    tuple
        The initialized ``Parser`` instance and compiled ``Query``.
    """

    lang = get_language(language_name)
    parser = get_parser(language_name)
    query_path = Path(__file__).resolve().parent / LANGUAGE_QUERIES[language_name]
    query = lang.query(query_path.read_text())
    return parser, query