# Gitingest — Docker‑ready Fork 🐳

[![Image](./docs/frontpage.png "Gitingest main page")](https://gitingest.com)

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](https://github.com/cyclotruc/gitingest/blob/main/LICENSE)
[![PyPI version](https://badge.fury.io/py/gitingest.svg)](https://badge.fury.io/py/gitingest)
[![GitHub stars](https://img.shields.io/github/stars/cyclotruc/gitingest?style=social.svg)](https://github.com/cyclotruc/gitingest)
[![Downloads](https://pepy.tech/badge/gitingest)](https://pepy.tech/project/gitingest)
[![CI](https://github.com/Leonai-do/gitingest/actions/workflows/ci.yml/badge.svg)](https://github.com/Leonai-do/gitingest/actions/workflows/ci.yml)
[![Coverage](https://codecov.io/gh/cyclotruc/gitingest/branch/main/graph/badge.svg)](https://codecov.io/gh/cyclotruc/gitingest)
[![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/cyclotruc/gitingest/badge)](https://scorecard.dev/viewer/?uri=github.com/cyclotruc/gitingest)

[![Discord](https://dcbadge.limes.pink/api/server/https://discord.com/invite/zerRaGK9EC)](https://discord.com/invite/zerRaGK9EC)

> **Heads‑up** This repository is an **independent fork** of the fantastic
> [cyclotruc/gitingest](https://github.com/cyclotruc/gitingest).
> We aim for *zero‑surprise Docker usage* on WSL 2 / Linux while tracking
> upstream features.
> Huge thanks 🙏 to the original authors for making the project MIT‑licensed and
> hack‑friendly!
>
> *If you want the pristine upstream package, just run `pip install gitingest` –
> see the [Installation](#-installation) section below.*

Turn any Git repository into a prompt‑friendly text digest you can feed to an
LLM – plus a one‑command container workflow.

You can also **replace `hub` with `ingest`** in any GitHub URL to access the
corresponding digest (This uses the orginal app for now):
`https://github.com/cyclotruc/gitingest`

[https://gitingest.com](https://gitingest.com) ·
[Chrome Extension](https://chrome.google.com/webstore/detail/gitingest/abc123) ·
[Firefox Add‑on](https://addons.mozilla.org/firefox/addon/gitingest)
---

## ✨ What’s new in this fork (June 2025)

| Change                                           | Why it matters                                                           |
| ------------------------------------------------ | ------------------------------------------------------------------------ |
| **Docker‑first workflow** (`docker-compose.yml`) | `docker compose up -d` → [http://localhost:9090](http://localhost:9090). |
| **`.env` template**                              | Central place for hosts, debug flag, size limit, PAT token.              |
| **Ext4‑friendly docs**                           | No more drvfs `chown` errors on WSL 2.                                   |
| **LF enforcement** (`.gitattributes`)            | Prevents `bash\r` shebang crashes.                                       |
| **Developer option:** `uv`                       | Conflict‑free, deterministic Python installs.                            |
| **Semantic Chunking**                            | Splits Python/JS into functions/classes using Tree-sitter.               |
| **Performance Flags**                            | `--parallel`, `--incremental`, `--compress`, and `--stream` are enabled. |
| **Security Enhancements**                        | Auto-redaction of secrets and path traversal protection.                 |

---

## 🚀 Features *(upstream + fork)*

* **CLI & Python API** – generate a `digest.txt` with one command or one import.
* **Web UI** – paste any repo URL, tweak include/exclude patterns.
* **Chrome / Firefox add‑ons** – swap *hub → ingest* automatically.
* **Self‑host** – single `docker compose up -d` (this fork).
* **Smart Formatting**: Optimized output format for LLM prompts
* **Statistics about**: File and directory structure, size of the extract, token count
* **Private Repo Support**: Use a GitHub Personal Access Token (PAT) for private repos.

## 📚 Requirements

| Tool             | Version                        | Notes                                      |
| ---------------- | ------------------------------ | ------------------------------------------ |
| Python           | ≥ 3.8                          | Required for CLI and local development.    |
| Git              | any                            | Required for repository cloning.           |
| Docker + Compose | ≥ v20                          | **Recommended for this fork's workflow.**  |
| GitHub PAT       | (optional)                     | For private repositories.                  |

---

### 📦 Installation

#### This fork via Docker (Recommended Workflow)

```bash
# clone inside WSL 2 ext4 (or native Linux)
$ git clone https://github.com/<your‑org>/gitingest.git ~/dev/gitingest
$ cd ~/dev/gitingest

# prepare runtime bits
$ cp .env.example .env     # Tweak GITHUB_TOKEN for private repos
$ mkdir -p cache

# build & run
$ docker compose build --pull
$ docker compose up -d

→ http://localhost:9090
```

#### Upstream CLI via pipx (Original Method)

This installs the original `cyclotruc/gitingest` package, not this fork.

```bash
# Install pipx via your package manager (e.g., brew, apt)
brew install pipx
pipx ensurepath

# Install gitingest
pipx install gitingest
```
---

## 🧩 Browser Extension Usage

<!-- markdownlint-disable MD033 -->
<a href="https://chromewebstore.google.com/detail/adfjahbijlkjfoicpjkhjicpjpjfaood" target="_blank" title="Get Gitingest Extension from Chrome Web Store"><img height="48" src="https://github.com/user-attachments/assets/20a6e44b-fd46-4e6c-8ea6-aad436035753" alt="Available in the Chrome Web Store" /></a>
<a href="https://addons.mozilla.org/firefox/addon/gitingest" target="_blank" title="Get Gitingest Extension from Firefox Add-ons"><img height="48" src="https://github.com/user-attachments/assets/c0e99e6b-97cf-4af2-9737-099db7d3538b" alt="Get The Add-on for Firefox" /></a>
<a href="https://microsoftedge.microsoft.com/addons/detail/nfobhllgcekbmpifkjlopfdfdmljmipf" target="_blank" title="Get Gitingest Extension from Microsoft Edge Add-ons"><img height="48" src="https://github.com/user-attachments/assets/204157eb-4cae-4c0e-b2cb-db514419fd9e" alt="Get from the Edge Add-ons" /></a>
<!-- markdownlint-enable MD033 -->

The extension is open source at [lcandy2/gitingest-extension](https://github.com/lcandy2/gitingest-extension).

## 💡 Command line usage

The `gitingest` command line tool allows you to analyze codebases and create a text dump of their contents.

```bash
# Basic usage (writes to digest.txt by default)
gitingest /path/to/directory

# From URL
gitingest https://github.com/cyclotruc/gitingest

# From a specific subdirectory
gitingest https://github.com/cyclotruc/gitingest/tree/main/src/gitingest/utils

# For private repositories, use a token
export GITHUB_TOKEN=github_pat_...
gitingest https://github.com/username/private-repo --token $GITHUB_TOKEN

# Customize output file or pipe to stdout
gitingest . -o my_digest.md
gitingest . -o - | wc -l

# See more options
gitingest --help
```

## 🐍 Python package usage

```python
# Synchronous usage
from gitingest import ingest

# From local path, URL, or subdirectory
summary, tree, content = ingest("https://github.com/cyclotruc/gitingest")

# For private repos, pass a token or set env var
import os
os.environ["GITHUB_TOKEN"] = "github_pat_..."
summary, tree, content = ingest("https://github.com/username/private-repo")
```

By default, this won't write a file but can be enabled with the `output` argument.

```python
# Asynchronous usage
from gitingest import ingest_async
import asyncio

result = asyncio.run(ingest_async("path/to/directory"))
```

### Jupyter notebook usage

```python
from gitingest import ingest_async

# Use await directly in Jupyter
summary, tree, content = await ingest_async("path/to/directory")
```

## 🐳 Self‑host (Docker - This Fork)

This fork adds a **single-file stack**:

```bash
# build image & start
$ docker compose up -d --build

# env vars live in .env
ALLOWED_HOSTS=localhost,127.0.0.1
GITINGEST_DEBUG=false
```

* Container user: `appuser` (UID 1000).
* Cache path: `./cache` → `/tmp/gitingest`.
* Health check: `GET /health`.

WSL 2 users **must clone on ext4** (e.g. `~/dev/...`).

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](./CONTRIBUTING.md) for detailed instructions on how to submit a pull request.

* **Non-technical**: Create an Issue, spread the word, or share feedback on Discord.
* **Technical**: Run `pre‑commit install` to get started. PR title prefix: `feat(docker): …`, `fix(ci): …`, etc.

## 🛠️ Stack

* [Tailwind CSS](https://tailwindcss.com) - Frontend
* [FastAPI](https://github.com/fastapi/fastapi) - Backend framework
* [Jinja2](https://jinja.palletsprojects.com) - HTML templating
* [tiktoken](https://github.com/openai/tiktoken) - Token estimation
* [posthog](https://github.com/PostHog/posthog) - Amazing analytics

### 📦 Looking for a JavaScript/FileSystemNode package?

Check out the NPM alternative 📦 **Repomix**:
[https://github.com/yamadashy/repomix](https://github.com/yamadashy/repomix)

---

## 🚀 Project growth

[![Stargazers over time](https://starchart.cc/Leonai-do/gitingest.svg?variant=adaptive)](https://starchart.cc/Leonai-do/gitingest)

---

## 📄 License & credits

This fork remains under the **MIT License**.
Credit to [@cyclotruc](https://github.com/cyclotruc) and contributors for the
original implementation.