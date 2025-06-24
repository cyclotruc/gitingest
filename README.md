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

[gitingest.com](https://gitingest.com) · [Chrome Extension](https://chromewebstore.google.com/detail/adfjahbijlkjfoicpjkhjicpjpjfaood) · [Firefox Add-on](https://addons.mozilla.org/firefox/addon/gitingest)

## ✨ What’s new in this fork (June 2025)

| Change                                           | Why it matters                                                           |
| ------------------------------------------------ | ------------------------------------------------------------------------ |
| **Docker‑first workflow** (`docker-compose.yml`) | `docker compose up -d` → [http://localhost:9090](http://localhost:9090). |
| **`entrypoint.sh`**                              | Auto‑chowns cache dir so non‑root container user can write.              |
| **`.env` template**                              | Central place for hosts, debug flag, size limit, PAT token.              |
| **Ext4‑friendly docs**                           | No more drvfs `chown` errors on WSL 2.                                   |
| **LF enforcement** (`.gitattributes`)            | Prevents `bash\r` shebang crashes.                                       |
| **Developer option:** `uv`                       | Conflict‑free, deterministic Python installs.                            |

---

## 🚀 Features *(upstream + fork)*

* **CLI & Python API** – generate a `digest.txt` with one command or one import.
* **Web UI** – paste any repo URL, tweak include/exclude patterns.
* **Chrome / Firefox add‑ons** – swap *hub → ingest* automatically.
* **Self‑host** – single `docker compose up -d` (this fork).
* **Easy code context**: Get a text digest from a Git repository URL or a directory
* **Smart Formatting**: Optimized output format for LLM prompts
* **Statistics about**:
  * File and directory structure
  * Size of the extract
  * Token count
* **CLI tool**: Run it as a shell command
* **Python package**: Import it in your code

## 📚 Requirements

| Tool             | Version                        |
| ---------------- | ------------------------------ |
| Python           | ≥ 3.8                          |
| Git              | any                            |
| Docker + Compose | ≥ v20 (for container workflow) |
| Linux (Optional)  | optional but recommended       |
| WSL 2 (Windows -  Optional)  | optional but recommended       |

---

### 📦 Installation

Gitingest is available on [PyPI](https://pypi.org/project/gitingest/).
You can install it using `pip`:

```bash
pip install gitingest # installs cyclotruc/gitingest from PyPI
```

However, it might be a good idea to use `pipx` or `uv` to install it.
You can install `pipx` using your preferred package manager.

```bash
brew install pipx
apt install pipx
scoop install pipx
...
```

If you are using pipx for the first time, run:

```bash
pipx ensurepath
```

```bash
# install gitingest
pipx install gitingest
```

### This fork via Docker (recommended)

```bash
# clone inside WSL 2 ext4 (or native Linux)
$ git clone https://github.com/<your‑org>/gitingest.git ~/dev/gitingest
$ cd ~/dev/gitingest

# prepare runtime bits
$ cp .env.example .env     # tweak if needed
$ mkdir -p cache

# build & run
$ docker compose build --pull
$ docker compose up -d

→ http://localhost:9090
```

### ⚡ Optional: dev install with **uv**

```bash
pip install -U uv          # Rust‑powered installer
uv pip compile --all-extras -o requirements.txt pyproject.toml
uv venv .venv && source .venv/bin/activate
uv pip install -r requirements.txt
```

---

## 🧩 Browser Extension Usage

<!-- markdownlint-disable MD033 -->
<a href="https://chromewebstore.google.com/detail/adfjahbijlkjfoicpjkhjicpjpjfaood" target="_blank" title="Get Gitingest Extension from Chrome Web Store"><img height="48" src="https://github.com/user-attachments/assets/20a6e44b-fd46-4e6c-8ea6-aad436035753" alt="Available in the Chrome Web Store" /></a>
<a href="https://addons.mozilla.org/firefox/addon/gitingest" target="_blank" title="Get Gitingest Extension from Firefox Add-ons"><img height="48" src="https://github.com/user-attachments/assets/c0e99e6b-97cf-4af2-9737-099db7d3538b" alt="Get The Add-on for Firefox" /></a>
<a href="https://microsoftedge.microsoft.com/addons/detail/nfobhllgcekbmpifkjlopfdfdmljmipf" target="_blank" title="Get Gitingest Extension from Microsoft Edge Add-ons"><img height="48" src="https://github.com/user-attachments/assets/204157eb-4cae-4c0e-b2cb-db514419fd9e" alt="Get from the Edge Add-ons" /></a>
<!-- markdownlint-enable MD033 -->

The extension is open source at [lcandy2/gitingest-extension](https://github.com/lcandy2/gitingest-extension).

Issues and feature requests are welcome to the repo.

## 💡 Command line usage

The `gitingest` command line tool allows you to analyze codebases and create a text dump of their contents.

```bash
# Basic usage
gitingest /path/to/directory

# From URL
gitingest https://github.com/cyclotruc/gitingest

# See more options
gitingest --help
```

This will write the digest in a text file (default `digest.txt`) in your current working directory.

## 🐍 Python package usage

```python
# Synchronous usage
from gitingest import ingest

summary, tree, content = ingest("path/to/directory")

# or from URL
summary, tree, content = ingest("https://github.com/cyclotruc/gitingest")
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

This is because Jupyter notebooks are asynchronous by default.

## 🐳 Self‑host (Docker)

This fork adds a **single‑file stack**:

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

### Semantic chunking

By default Gitingest now splits Python/JS files into functions & classes using
Tree-sitter (like Repomix). Unknown filetypes fall back to whole-file.

---

### 🚀 Performance flags

* `--parallel` (default ON): scan files with 8 threads.
* `--incremental`: skip unchanged files using SHA cache in `~/.gitingestcache`.
* `--compress`: write `digest.txt.gz` (≈ 10× smaller on monorepos).
* `--stream`: fetch files directly from GitHub without creating a `.git` directory.

### Security flags
* Secrets are auto-redacted using [`detect-secrets`](https://github.com/Yelp/detect-secrets).
* Path traversal protection blocks `../` and unsafe symlinks.
* Rate limit: set `RATE_LIMIT_PER_MIN=60` in `.env` (0 disables).

Original method:

1. Build the image:

   ``` bash
   docker build -t gitingest .
   ```

2. Run the container:

   ``` bash
   docker run -d --name gitingest -p 8000:8000 gitingest
   ```

The application will be available at `http://localhost:8000`.

If you are hosting it on a domain, you can specify the allowed hostnames via env variable `ALLOWED_HOSTS`.

   ```bash
   # Default: "gitingest.com, *.gitingest.com, localhost, 127.0.0.1".
   ALLOWED_HOSTS="example.com, localhost, 127.0.0.1"
   ```

## 🤝 Contributing

### Non-technical ways to contribute

* **Create an Issue**: If you find a bug or have an idea for a new feature, please [create an issue](https://github.com/cyclotruc/gitingest/issues/new) on GitHub. This will help us track and prioritize your request.
* **Spread the Word**: If you like Gitingest, please share it with your friends, colleagues, and on social media. This will help us grow the community and make Gitingest even better.
* **Use Gitingest**: The best feedback comes from real-world usage! If you encounter any issues or have ideas for improvement, please let us know by [creating an issue](https://github.com/cyclotruc/gitingest/issues/new) on GitHub or by reaching out to us on [Discord](https://discord.com/invite/zerRaGK9EC).

### Technical ways to contribute

Gitingest aims to be friendly for first time contributors, with a simple Python and HTML codebase. If you need any help while working with the code, reach out to us on [Discord](https://discord.com/invite/zerRaGK9EC). For detailed instructions on how to make a pull request, see [CONTRIBUTING.md](./CONTRIBUTING.md).

* Run `pre‑commit install` – hooks enforce LF & ruff/black.
* Commit new shell scripts with `chmod +x`.
* PR title prefix: `feat(docker): …`, `fix(ci): …`, etc.

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

(Star history chart courtesy of [https://starchart.cc](https://starchart.cc).)

---

## 📄 License & credits

This fork remains under the **MIT License**.
Credit to [@cyclotruc](https://github.com/cyclotruc) and contributors for the
original implementation.
