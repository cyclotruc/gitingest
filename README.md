# Gitingest — Docker‑ready Fork 🐳

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
corresponding digest:
`https://github.com/tiangolo/fastapi` →
`https://gitingest.com/tiangolo/fastapi`

[https://gitingest.com](https://gitingest.com) ·
[Chrome Extension](https://chrome.google.com/webstore/detail/gitingest/abc123) ·
[Firefox Add‑on](https://addons.mozilla.org/firefox/addon/gitingest)

---

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
* **Smart formatting** – directory tree, file bodies & token counts.
* **Web UI** – paste any repo URL, tweak include/exclude patterns.
* **Chrome / Firefox add‑ons** – swap *hub → ingest* automatically.
* **Self‑host** – single `docker compose up -d` (this fork).

---

## 📚 Requirements

| Tool             | Version                        |
| ---------------- | ------------------------------ |
| Python           | ≥ 3.8                          |
| Git              | any                            |
| Docker + Compose | ≥ v20 (for container workflow) |
| WSL 2 (Windows)  | optional but recommended       |

---

## 📦 Installation

### Official upstream package (no Docker)

```bash
pip install gitingest               # installs cyclotruc/gitingest from PyPI
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

> **Port clash?** Change the left side of `"9090:8000"` in `docker-compose.yml`.

### ⚡ Optional: dev install with **uv**

```bash
pip install -U uv          # Rust‑powered installer
uv pip compile --all-extras -o requirements.txt pyproject.toml
uv venv .venv && source .venv/bin/activate
uv pip install -r requirements.txt
```

---

## 💡 Command‑line usage (upstream & fork)

```bash
# generate digest for local path or GitHub repo
$ gitingest .                       # current repo
$ gitingest https://github.com/lm-sys/FastChat > digest.txt
```

---

## 🐍 Python package usage

```python
from gitingest import ingest_async

digest = await ingest_async("https://github.com/psf/requests")
print(digest[:500])
```

---

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

---

## 🛠️ Stack

* **FastAPI** + Jinja2 + Tailwind CSS
* **Click** CLI
* **tiktoken** for token estimates
* **SlowAPI** for rate‑limiting
* **Docker** multi‑stage build (`python:3.12‑slim`)

---

## 🚀 Project growth

![Stars over time](https://starchart.cc/cyclotruc/gitingest.svg)

(Star history chart courtesy of [https://starchart.cc](https://starchart.cc).)

---

## 📦 Looking for a JavaScript/FileSystemNode package?

Check out the NPM alternative 📦 **Repomix**:
[https://github.com/yamadashy/repomix](https://github.com/yamadashy/repomix)

---

## 📝 Contributing to this fork

* Run `pre‑commit install` – hooks enforce LF & ruff/black.
* Commit new shell scripts with `chmod +x`.
* PR title prefix: `feat(docker): …`, `fix(ci): …`, etc.

---

## 📄 License & credits

This fork remains under the **MIT License**.
Credit to [@cyclotruc](https://github.com/cyclotruc) and contributors for the
original implementation.
