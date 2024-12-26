[![Image](./docs/frontpage.png "GitIngest main page")](https://gitingest.com)

<!-- License -->
<a href="https://github.com/cyclotruc/gitingest/blob/main/LICENSE">
  <img alt="License" src="https://img.shields.io/badge/license-MIT-blue.svg" />
</a>
<!-- PyPI version -->
<a href="https://badge.fury.io/py/gitingest">
  <img src="https://badge.fury.io/py/gitingest.svg" alt="PyPI version" />
</a>
<!-- Downloads -->
<a href="https://pepy.tech/project/gitingest">
  <img src="https://pepy.tech/badge/gitingest" alt="Downloads" />
</a>
<!-- GitHub issues -->
<a href="https://github.com/cyclotruc/gitingest/issues">
  <img src="https://img.shields.io/github/issues/cyclotruc/gitingest" alt="GitHub issues" />
</a>
<!-- Black code style -->
<a href="https://github.com/psf/black">
  <img alt="Code style: black" src="https://img.shields.io/badge/code%20style-black-000000.svg" />
</a>

<!-- Discord -->
<a href="https://discord.com/invite/zerRaGK9EC">
  <img src="https://dcbadge.limes.pink/api/server/https://discord.com/invite/zerRaGK9EC" alt="Discord" />
</a>

# GitIngest

Turn any Git repository into a prompt-friendly text ingest for LLMs.

You can also replace `hub` with `ingest` in any github url to access the coresponding digest

[gitingest.com](https://gitingest.com)

## 🚀 Features

- **Easy code context**: Get a text digest from a git repository URL or a directory
- **Smart Formatting**: Optimized output format for LLM prompts
- **Statistics about**:
  - File and directory structure
  - Size of the extract
  - Token count
- **CLI tool**: Run it as a command (Currently on Linux only)
- **Python package**: Import it in your code

## 📦 Installation

``` bash
pip install gitingest
```

## 💡 Command Line usage

The `gitingest` command line tool allows you to analyze codebases and create a text dump of their contents.

```bash
# Basic usage
gitingest /path/to/directory

# From url
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

## 🛠️ Using

- Tailwind CSS - Frontend
- [FastAPI](https://github.com/fastapi/fastapi) - Backend framework
- [tiktoken](https://github.com/openai/tiktoken) - Token estimation
- [apianalytics.dev](https://www.apianalytics.dev/) - Simple Analytics

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
Ensure environment variables are set before running the application or deploying it via Docker.

## ✔️ Contributing

Contributions are welcome!

Gitingest aims to be friendly for first time contributors, with a simple python and html codebase. If you need any help while working with the code, reach out to us on [discord](https://discord.com/invite/zerRaGK9EC)

### Ways to contribute

1. Provide your feedback and ideas on discord
2. Open an Issue on github to report a bug
3. Create a Pull request
   - Fork the repository
   - Make your changes and test them locally
   - Open a pull request for review and feedback

### 🔧 Local dev

#### Environment Configuration

- **`ALLOWED_HOSTS`**: Specify allowed hostnames for the application. Default: `"gitingest.com,*.gitingest.com,gitdigest.dev,localhost"`.
You can configure the application using the following environment variables:

```bash
ALLOWED_HOSTS="gitingest.local,localhost"
```

#### Run locally

1. Clone the repository

```bash
git clone https://github.com/cyclotruc/gitingest.git
cd gitingest
```

2. Install dependencies

```bash
pip install -r requirements.txt
```

3. Run the application:

```bash
cd src
uvicorn main:app --reload
```

The frontend will be available at `localhost:8000`
