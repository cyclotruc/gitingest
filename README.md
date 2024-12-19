![License](https://img.shields.io/badge/license-MIT-blue.svg)
# GitIngest 🔍


[![Image](./docs/frontpage.png)](https://gitingest.com/)

[gitingest.com](https://gitingest.com/) - Turn any Git repository into a prompt-friendly text ingest for LLMs.
You can also replace `hub` with `ingest` in any github url to access the coresponding digest

## 🚀 Features

- **One-Click Analysis**: Simply paste a Git repository URL and get instant pastable context
- **Smart Formatting**: Optimized output format for LLM prompts
- **Statistics about**: :
  - File and directory structure
  - Size of the extract
  - (soon) Token count  
- **Web Interface**: Lightweight responsive UI

## 🛠️ Tech Stack
- Tailwind CSS
- FastAPI - Backend framework
- [apianalytics.dev](https://www.apianalytics.dev/) - Usage tracking

## 📦 Running Tests

To run the tests, first install the test dependencies:
```bash
pip install -r requirements.txt
```

Then run the tests with coverage:
```bash
cd src
pytest --cov
```

To generate a coverage HTML report:
```bash
pytest --cov --cov-report=html
```
The report will be available in `htmlcov/index.html`

## 📦 Installation

1. Clone the repository:
```bash
git clone https://github.com/cyclotruc/gitingest.git
cd gitingest
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the application:
```bash
cd src
uvicorn main:app --reload
```


The application will be available at `http://localhost:8000`

### Docker

1. Build the image:
```
docker build -t gitingest .
```

2. Run the container:
```
docker run -d --name gitingest -p 8000:8000 gitingest
```
The application will be available at `http://localhost:8000`

### 🌐 Environment Configuration

You can configure the application using the following environment variables:

- **`ALLOWED_HOSTS`**: Specify allowed hostnames for the application. Default: `"gitingest.com,*.gitingest.com,gitdigest.dev,localhost"`.

Example:

```bash
ALLOWED_HOSTS="gitingest.local,localhost"
```

Ensure these variables are set before running the application or deploying it via Docker.

## ✔️ Contributions are welcome!
Create a pull request or open an Issue about anything you'd like to see in gitingest

## 🔒 WIP
- Feedback/suggestions: Please open a github Issue or mail me: romain@coderamp.io
- Repository cloning is limited to public GitHub repositories only
- Too big repos will probably timeout (if longer than 20 secondes to clone)


## Command Line Global Installation

```bash
pip install -e .
```

## Command Line Usage

The `gitingest` command line tool allows you to analyze any directory and create a text dump of its contents.

### Basic Usage

```bash
gitingest /path/to/directory
```

This will create a text file named after your directory (e.g., `directory.txt`) in your current working directory.

### Specifying Output Location

```bash
gitingest /path/to/directory -o /path/to/output.txt
```

### Options

- `-o, --output`: Specify the output file path (default: `<directory_name>.txt` in current directory)
- `-s, --max-size`: Maximum file size to process in bytes (default: 10MB)
- `-i, --ignore-pattern`: Additional patterns to ignore (can be used multiple times)

### Examples

```bash
# Basic usage
gitingest ~/projects/myproject

# Custom output location
gitingest ~/projects/myproject -o ~/Desktop/analysis.txt

# Ignore specific file patterns
gitingest ~/projects/myproject -i "*.csv" -i "*.json"

# Set maximum file size (e.g., 5MB)
gitingest ~/projects/myproject -s 5000000
```

### Output Format

The generated text file contains:
1. Summary statistics (file count, directory count, content size)
2. Directory tree structure
3. Contents of all text files

Files and directories that are commonly ignored (like `.git`, `node_modules`, cache directories, etc.) are automatically excluded. You can add additional patterns to ignore using the `-i` flag.

