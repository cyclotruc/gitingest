![License](https://img.shields.io/badge/license-MIT-blue.svg)
# GitDigest 🔍

Turn any GitHub repository into a prompt-friendly text digest for LLMs. 

[Live demo](https://gitdigest.dev/)

## 🚀 Features

- **One-Click Analysis**: Simply paste a GitHub repository URL and get instant results
- **Smart Formatting**: Optimized output format for LLM prompts
- **Statistics about**: :
  - File and directory structure
  - Token counts and statistics
  - Repository summary
- **Web Interface**: Clean, responsive UI built with Tailwind CSS

## 🛠️ Tech Stack

- FastAPI - Backend framework
- [apianalytics.dev](https://www.apianalytics.dev/) - Usage tracking

## 📦 Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/gitdigest.git
cd gitdigest
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
# Create .env file
touch .env

# Add your API analytics key
echo "API_ANALYTICS_KEY=your_key_here" >> .env
```

4. Run the application:
```bash
cd src
uvicorn main:app --reload
```

The application will be available at `http://localhost:8000`


## 🔒 WIP
- Feedback/suggestions: Please open a GitHub Issue or mail me: romain@coderamp.io
- Repository cloning is limited to GitHub repositories only
- Processing timeouts are implemented (10s for cloning, 15s for processing)
- Request size limits are in place to prevent abuse

