# Project Architecture

Gitingest is organized around a core ingestion library, a CLI, and an optional FastAPI server.

- **`src/gitingest`** contains the ingestion logic. The `ingestion.py` module
  walks the filesystem and returns summary information. Helper utilities live in
  the `utils` subpackage.
- **`src/gitingest/cli.py`** exposes the command line interface built with
  `click` and calls into the ingestion functions.
- **`src/server`** implements a lightweight web front‑end using FastAPI and
  Jinja2 templates. It reuses the same ingestion code and exposes a simple HTTP
  API.

The typical flow is:
1. A path or repository URL is parsed by `query_parsing.py`.
2. If needed, the repository is cloned by `cloning.py`.
3. `ingestion.py` traverses the files and directories, applying ignore rules and
   collecting statistics.
4. `output_formatters.py` builds the textual summary, directory tree and file
   contents that are returned to the caller or written to disk.

This one‑pager should help newcomers quickly locate the main components.

