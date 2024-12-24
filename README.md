[![Image](./docs/frontpage.png "GitIngest main page")](https://gitingest.com/)

![License](https://img.shields.io/badge/license-MIT-blue.svg)

# GitIngest 🔍
Turn any Git repository into a prompt-friendly text ingest for LLMs.

You can also replace `hub` with `ingest` in any github url to access the coresponding digest

[gitingest.com](https://gitingest.com/) 


## 🚀 Features

- **Easy code context**: Get a text digest from a git repository URL or a directory
- **Smart Formatting**: Optimized output format for LLM prompts
- **Statistics about**: :
  - File and directory structure
  - Size of the extract
  - Token count  
- **CLI tool**: Run it as a command (Currently on Linux only)
- **Python package**: Import it in your code


## 📦 Installation

```
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

#or from URL
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
```
docker build -t gitingest .
```

2. Run the container:
```
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
2. Create a Pull request
   - Fork the repository
   - Make your changes and test them locally
   - Open a pull request for review and feedback

### 🔧 Local dev

####  Environment Configuration
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

## 🗂️ Using Local Directories

In addition to GitHub Public repo URLs, you can now use local directories with the CLI and Python package.

### CLI usage with local directories

```bash
# Basic usage with local directory
gitingest /path/to/local/directory

# See more options
gitingest --help
```

### Python package usage with local directories

```python
from gitingest import ingest

# Ingest from a local directory
summary, tree, content = ingest("/path/to/local/directory")
```

By default, this won't write a file but can be enabled with the `output` argument.
