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
    parts = repo_url.rstrip('/').split('/')
    owner, repo = parts[-2], parts[-1]

    # Step 1: Get the file tree
    tree_url = f'https://api.github.com/repos/{owner}/{repo}/git/trees/HEAD?recursive=1'
    tree_resp = requests.get(tree_url, headers=get_headers(), timeout=10)
    tree_resp.raise_for_status()
    tree = tree_resp.json().get('tree', [])

    # Step 2: Filter to supported file types, cap at MAX_FILES
    file_paths = [
        item['path'] for item in tree
        if item['type'] == 'blob'
        and any(item['path'].endswith(ext) for ext in SUPPORTED_EXTENSIONS)
    ][:MAX_FILES]

    # Step 3: Fetch each file's content
    files = []
    for path in file_paths:
        content_url = f'https://api.github.com/repos/{owner}/{repo}/contents/{path}'
        resp = requests.get(content_url, headers=get_headers(), timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            content = base64.b64decode(data['content']).decode('utf-8', errors='ignore')
            files.append({'name': path.split('/')[-1], 'path': path, 'content': content})
    return files