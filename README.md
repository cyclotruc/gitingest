# Gitingest

[![Image](./docs/frontpage.png "Gitingest main page")](https://gitingest.com)

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](https://github.com/cyclotruc/gitingest/blob/main/LICENSE)
[![PyPI version](https://badge.fury.io/py/gitingest.svg)](https://badge.fury.io/py/gitingest)
[![GitHub stars](https://img.shields.io/github/stars/cyclotruc/gitingest?style=social.svg)](https://github.com/cyclotruc/gitingest)
[![Downloads](https://pepy.tech/badge/gitingest)](https://pepy.tech/project/gitingest)

[![Discord](https://dcbadge.limes.pink/api/server/https://discord.com/invite/zerRaGK9EC)](https://discord.com/invite/zerRaGK9EC)

Turn any Git repository into a prompt-friendly text ingest for LLMs.

You can also replace `hub` with `ingest` in any GitHub URL to access the corresponding digest.

[gitingest.com](https://gitingest.com) · [Chrome Extension](https://chromewebstore.google.com/detail/adfjahbijlkjfoicpjkhjicpjpjfaood) · [Firefox Add-on](https://addons.mozilla.org/firefox/addon/gitingest)

## 🚀 Features

- **Easy code context**: Get a text digest from a Git repository URL or a directory
- **Smart Formatting**: Optimized output format for LLM prompts
- **Statistics about**:
  - File and directory structure
  - Size of the extract
  - Token count
- **CLI tool**: Run it as a shell command
- **Python package**: Import it in your code

## 📚 Requirements

- Python 3.7+

## 📦 Installation

``` bash
pip install gitingest
```

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

### Accessing Private Repositories with Tokens

You can provide a Personal Access Token (PAT) to clone private repositories from supported platforms (GitHub, GitLab, Codeberg, Bitbucket).
**Important:** This token is used **only** for the clone operation and is **never stored or logged** by Gitingest.

1.  **Generate a Token:** Go to your Git provider's settings (e.g., GitHub Developer settings) and generate a Personal Access Token. Grant it the minimum required scope, which is typically read access to repositories (e.g., `repo` scope on GitHub, `read_repository` on GitLab).
2.  **Use the Token (CLI):** Pass the token using the `--access-token` option:
    ```bash
    gitingest https://github.com/your-user/your-private-repo --access-token YOUR_TOKEN
    gitingest https://gitlab.com/your-group/your-private-repo --access-token YOUR_TOKEN
    ```
    *Security Note:* Be mindful of your shell history when passing tokens directly on the command line.
3.  **Use the Token (Web UI):** Paste the token into the "Access Token (Optional, for private repos)" field on [gitingest.com](https://gitingest.com) or your self-hosted instance.

*Note: If using a token with an unsupported Git host, the token will be ignored.* 

## 🐍 Python package usage

```python
# Synchronous usage
from gitingest import ingest

# Public repo or local path
summary, tree, content = ingest(\"path/to/directory\")
summary, tree, content = ingest(\"https://github.com/cyclotruc/gitingest\")

# Private repo with token
summary, tree, content = ingest(
    \"https://github.com/your-user/your-private-repo\", 
    access_token=\"YOUR_TOKEN\"
)
```

By default, this won't write a file but can be enabled with the `output` argument.

```python
# Asynchronous usage
from gitingest import ingest_async
import asyncio

# Public repo or local path
result = asyncio.run(ingest_async(\"path/to/directory\"))

# Private repo with token
summary, tree, content = asyncio.run(
    ingest_async(\"https://gitlab.com/your-group/your-private-repo\", access_token=\"YOUR_TOKEN\")
)
```

### Jupyter notebook usage

```python
from gitingest import ingest_async

# Public repo or local path
summary, tree, content = await ingest_async(\"path/to/directory\")

# Private repo with token (use await directly in Jupyter)
summary, tree, content = await ingest_async(
    \"https://github.com/your-user/your-private-repo\", 
    access_token=\"YOUR_TOKEN\"
)
```

This is because Jupyter notebooks are asynchronous by default.

## 🐳 Self-host

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

- **Create an Issue**: If you find a bug or have an idea for a new feature, please [create an issue](https://github.com/cyclotruc/gitingest/issues/new) on GitHub. This will help us track and prioritize your request.
- **Spread the Word**: If you like Gitingest, please share it with your friends, colleagues, and on social media. This will help us grow the community and make Gitingest even better.
- **Use Gitingest**: The best feedback comes from real-world usage! If you encounter any issues or have ideas for improvement, please let us know by [creating an issue](https://github.com/cyclotruc/gitingest/issues/new) on GitHub or by reaching out to us on [Discord](https://discord.com/invite/zerRaGK9EC).

### Technical ways to contribute

Gitingest aims to be friendly for first time contributors, with a simple Python and HTML codebase. If you need any help while working with the code, reach out to us on [Discord](https://discord.com/invite/zerRaGK9EC). For detailed instructions on how to make a pull request, see [CONTRIBUTING.md](./CONTRIBUTING.md).

## 🛠️ Stack

- [Tailwind CSS](https://tailwindcss.com) - Frontend
- [FastAPI](https://github.com/fastapi/fastapi) - Backend framework
- [Jinja2](https://jinja.palletsprojects.com) - HTML templating
- [tiktoken](https://github.com/openai/tiktoken) - Token estimation
- [posthog](https://github.com/PostHog/posthog) - Amazing analytics

### Looking for a JavaScript/FileSystemNode package?

Check out the NPM alternative 📦 Repomix: <https://github.com/yamadashy/repomix>

## 🚀 Project Growth

[![Star History Chart](https://api.star-history.com/svg?repos=cyclotruc/gitingest&type=Date)](https://star-history.com/#cyclotruc/gitingest&Date)
