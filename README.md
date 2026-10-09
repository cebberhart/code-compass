# Code Compass

An AI-powered tool for asking questions about a GitHub repository in plain English. Paste a public repo URL, and Code Compass loads the code and answers questions with context from the actual files.

**Demo video:** https://youtu.be/j3l-e6EcRTA

## Features
- Loads public GitHub repositories (.py, .js, .ts, .md files, up to 30 files)
- Summarizes each file and answers natural-language questions using the Anthropic Claude API
- Answers rendered as formatted Markdown (headings, lists, code blocks), sanitized with DOMPurify
- Streaming progress bar while a repository loads
- Friendly error handling for invalid URLs and API issues
- Optional GitHub token support for higher rate limits

## Tech Stack
Python, Flask, Anthropic Claude API, GitHub REST API, HTML/CSS/JavaScript, Docker

## Planning and Testing
Built with full SRS and SPMP documentation, COCOMO effort estimation, and UML use case and sequence diagrams. All test cases (TC-01 through TC-07) pass.

## Run Locally
1. Clone the repo and create a virtual environment
2. `pip install -r requirements.txt`
3. Create a `.env` file:
```
   ANTHROPIC_API_KEY=your_key_here
   GITHUB_TOKEN=optional
```
4. `python app.py` and open http://127.0.0.1:5000

## Run with Docker
1. Create the `.env` file from step 3 above
2. Build and run:
```
   docker build -t code-compass .
   docker run -p 5000:5000 --env-file .env code-compass
```
3. Open http://localhost:5000

Your API key is passed in at runtime and never copied into the image (`.env` is listed in `.dockerignore`).
