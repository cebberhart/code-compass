from flask import Flask, render_template, request, session, jsonify
from dotenv import load_dotenv
from github_loader import get_repo_files
from ai_engine import summarize_file, answer_question
import os

load_dotenv()
app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY')

# Simple in-memory store
store = {}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/load', methods=['POST'])
def load_repo():
    url = request.json.get('url', '')
    if not url:
        return jsonify({'error': 'No URL provided'}), 400
    try:
        files = get_repo_files(url)
        summaries = []
        for f in files:
            summary = summarize_file(f['name'], f['content'])
            summaries.append({'path': f['path'], 'summary': summary})
        store['files'] = files
        store['summaries'] = summaries
        return jsonify({'summaries': summaries, 'file_count': len(files)})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/ask', methods=['POST'])
def ask():
    question = request.json.get('question', '')
    files = store.get('files', [])
    if not files:
        return jsonify({'error': 'No repository loaded'}), 400
    try:
        answer = answer_question(question, files)
        return jsonify({'answer': answer})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/reset', methods=['POST'])
def reset():
    store.clear()
    return jsonify({'status': 'ok'})

if __name__ == '__main__':
    app.run(debug=True)