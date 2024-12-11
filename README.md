![License](https://img.shields.io/badge/license-MIT-blue.svg)
# GitIngest 🔍


[![Image](./docs/frontpage.png)](https://gitingest.com/)

[gitingest.com](https://gitingest.com/) - Turn any GitHub repository into a prompt-friendly text ingest for LLMs.
You can also replace `hub` with `ingest` in any github url to access the coresponding digest

## 🚀 Features

- **One-Click Analysis**: Simply paste a GitHub repository URL and get instant pastable context
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

## 📦 Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/gitingest.git
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

## ✔️ Contributions are welcome!
Create a pull request or open an Issue about anything you'd like to see in gitingest

## 🔒 WIP
- Feedback/suggestions: Please open a github Issue or mail me: romain@coderamp.io
- Repository cloning is limited to public GitHub repositories only
- Too big repos will probably timeout (if longer than 20 secondes to clone)

