import requests
import base64
import os
from dotenv import load_dotenv

load_dotenv()

SUPPORTED_EXTENSIONS = ('.py', '.js', '.ts', '.md')
MAX_FILES = 30

def get_headers():
    token = os.getenv('GITHUB_TOKEN')
    if token:
        return {'Authorization': f'token {token}'}
    return {}

def get_repo_files(repo_url):
    """
    Given a GitHub URL like https://github.com/owner/repo,
    returns a list of dicts: [{name, path, content}, ...]
    """
    # Validate URL format
    if not repo_url.startswith('https://github.com/'):
        raise ValueError("Please enter a valid GitHub URL (e.g. https://github.com/owner/repo)")

    parts = repo_url.rstrip('/').split('/')
    if len(parts) < 5:
        raise ValueError("URL must include both owner and repo name (e.g. https://github.com/owner/repo)")

    owner, repo = parts[-2], parts[-1]

    # Get the file tree
    tree_url = f'https://api.github.com/repos/{owner}/{repo}/git/trees/HEAD?recursive=1'
    try:
        tree_resp = requests.get(tree_url, headers=get_headers(), timeout=10)
    except requests.exceptions.Timeout:
        raise TimeoutError("GitHub API timed out. Check your internet connection and try again.")
    except requests.exceptions.ConnectionError:
        raise ConnectionError("Could not connect to GitHub. Check your internet connection.")

    if tree_resp.status_code == 404:
        raise ValueError(f"Repository '{owner}/{repo}' not found. Make sure the URL is correct and the repo is public.")
    elif tree_resp.status_code == 403:
        raise PermissionError("GitHub API rate limit reached. Wait a few minutes and try again.")
    elif tree_resp.status_code == 401:
        raise PermissionError("GitHub authentication failed. Check your GITHUB_TOKEN in .env.")
    elif tree_resp.status_code != 200:
        raise Exception(f"GitHub API error: {tree_resp.status_code}")

    tree = tree_resp.json().get('tree', [])

    if not tree:
        raise ValueError("This repository appears to be empty.")

    # Filter to supported file types, cap at MAX_FILES
    all_supported = [
        item['path'] for item in tree
        if item['type'] == 'blob'
        and any(item['path'].endswith(ext) for ext in SUPPORTED_EXTENSIONS)
    ]

    was_capped = len(all_supported) > MAX_FILES
    file_paths = all_supported[:MAX_FILES]

    if not file_paths:
        raise ValueError("No supported files found (.py, .js, .ts, .md). Try a different repository.")

    # Fetch each file's content
    files = []
    for path in file_paths:
        content_url = f'https://api.github.com/repos/{owner}/{repo}/contents/{path}'
        try:
            resp = requests.get(content_url, headers=get_headers(), timeout=10)
        except requests.exceptions.Timeout:
            continue  # skip files that time out, don't crash
        if resp.status_code == 200:
            data = resp.json()
            content = base64.b64decode(data['content']).decode('utf-8', errors='ignore')
            files.append({
                'name': path.split('/')[-1],
                'path': path,
                'content': content,
            })

    if not files:
        raise ValueError("Could not retrieve any file contents from this repository.")

    return files, was_capped