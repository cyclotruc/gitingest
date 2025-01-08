# Gitingest

[![Image](./docs/frontpage.png "Gitingest main page")](https://gitingest.com)

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](https://github.com/cyclotruc/gitingest/blob/main/LICENSE)
[![PyPI version](https://badge.fury.io/py/gitingest.svg)](https://badge.fury.io/py/gitingest)
[![GitHub stars](https://img.shields.io/github/stars/cyclotruc/gitingest?style=social.svg)](https://github.com/cyclotruc/gitingest)
[![Downloads](https://pepy.tech/badge/gitingest)](https://pepy.tech/project/gitingest)

[![Discord](https://dcbadge.limes.pink/api/server/https://discord.com/invite/zerRaGK9EC)](https://discord.com/invite/zerRaGK9EC)

Turn any Git repository into a prompt-friendly text ingest for LLMs.

You can also replace `hub` with `ingest` in any GitHub URL to access the coresponding digest

[gitingest.com](https://gitingest.com/) · [Chrome Extension](https://chromewebstore.google.com/detail/adfjahbijlkjfoicpjkhjicpjpjfaood) · [Firefox Add-on](https://addons.mozilla.org/firefox/addon/gitingest/)

## 🚀 Features

- **Easy code context**: Get a text digest from a git repository URL or a directory
- **Smart Formatting**: Optimized output format for LLM prompts
- **Statistics about**:
  - File and directory structure
  - Size of the extract
  - Token count
- **CLI tool**: Run it as a shell command (currently on Linux only)
- **Python package**: Import it in your code

## 📦 Installation

``` bash
pip install gitingest
```

## 🧩 Browser Extension Usage

<!-- markdownlint-disable MD033 -->
<a href="https://chromewebstore.google.com/detail/adfjahbijlkjfoicpjkhjicpjpjfaood" target="_blank" title="Get Gitingest Extension from Chrome Web Store"><img height="48" src="https://github.com/user-attachments/assets/20a6e44b-fd46-4e6c-8ea6-aad436035753" alt="Available in the Chrome Web Store" /></a>
<a href="https://addons.mozilla.org/firefox/addon/gitingest/" target="_blank" title="Get Gitingest Extension from Firefox Add-ons"><img height="48" src="https://github.com/user-attachments/assets/c0e99e6b-97cf-4af2-9737-099db7d3538b" alt="Get The Add-on for Firefox" /></a>
<a href="https://microsoftedge.microsoft.com/addons/detail/nfobhllgcekbmpifkjlopfdfdmljmipf" target="_blank" title="Get Gitingest Extension from Firefox Add-ons"><img height="48" src="https://github.com/user-attachments/assets/204157eb-4cae-4c0e-b2cb-db514419fd9e" alt="Get from the Edge Add-ons" /></a>
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

## 🐛 Python package usage

```python
from gitingest import ingest

summary, tree, content = ingest("path/to/directory")

# or from URL
summary, tree, content = ingest("https://github.com/cyclotruc/gitingest")
```

By default, this won't write a file but can be enabled with the `output` argument

## 🌐 Self-host

1. Build the image:

   ``` bash
   docker build -t gitingest .
   ```

2. Run the container:

   ``` bash
   docker run -d --name gitingest -p 8000:8000 gitingest
   ```

The application will be available at `http://localhost:8000`

If you are hosting it on a domain, you can specify the allowed hostnames via env variable `ALLOWED_HOSTS`.

   ```bash
   #Default: "gitingest.com,*.gitingest.com,localhost, 127.0.0.1".
   ALLOWED_HOSTS="example.com, localhost, 127.0.0.1"
   ```

## 🛠️ Stack

- [Tailwind CSS](https://tailwindcss.com/) - Frontend
- [FastAPI](https://github.com/fastapi/fastapi) - Backend framework
- [Jinja2](https://jinja.palletsprojects.com/) - HTML templating
- [tiktoken](https://github.com/openai/tiktoken) - Token estimation
- [apianalytics.dev](https://www.apianalytics.dev/) - Simple Analytics

### Looking for a javascript/node package?

Check out the NPM alternative 📦 Repomix: <https://github.com/yamadashy/repomix>

## ✔️ Contributing to Gitingest

Gitingest aims to be friendly for first time contributors, with a simple python and html codebase.
 If you need any help while working with the code, reach out to us on [discord](https://discord.com/invite/zerRaGK9EC)

### Ways to help (non-technical)

- Provide your feedback and ideas on Discord
- Open an issue on GitHub to report a bug / submit a feature request
- Talk about Gitingest on social media

### How to submit a PR

1. Fork the repository & clone it locally
2. Setup the dev environment (see Development section bellow)
3. Run unit tests with `pytest`
4. Commit your changes and run `pre-commit`
5. Open a pull request on Github for review and feedback
6. (Optionnal) Invite project maintainer to your branch for easier collaboration

## 🔧 Development

### Run web UI locally

1. Clone the repository:

   ```bash
   git clone https://github.com/cyclotruc/gitingest.git
   cd gitingest
   ```

2. Install dependencies:

   ```bash
   pip install -r requirements-dev.txt
   python -m venv .venv
   source .venv/bin/activate
   pre-commit install
   ```

3. Run the application:

   ```bash
   cd src
   uvicorn main:app --reload
   ```

4. Run unit tests:

   ```bash
   pytest
   ```

The application should be available at `http://localhost:8000`

### Working on the CLI

1. Install the package in dev mode:

   ```bash
   pip install -e .
   ```

2. Run the CLI:

   ```bash
   gitingest --help
   ```
