from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
from github_loader import get_repo_files
from ai_engine import summarize_all_files, answer_question
import os

load_dotenv()
app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY')

# Simple in-memory store
store = {
    'files': [],
    'summaries': [],
    'history': []
}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/load', methods=['POST'])
def load_repo():
    url = request.json.get('url', '')
    if not url:
        return jsonify({'error': 'No URL provided'}), 400
    try:
        # Fetch files from GitHub
        files = get_repo_files(url)
        if not files:
            return jsonify({'error': 'No supported files found in this repository'}), 400

        # Summarize all files in parallel
        summary_texts = summarize_all_files(files)

        # Build summary list
        summaries = []
        for i, f in enumerate(files):
            summaries.append({
                'path': f['path'],
                'summary': summary_texts[i]
            })

        # Store everything and reset history
        store['files'] = files
        store['summaries'] = summaries
        store['history'] = []

        return jsonify({'summaries': summaries, 'file_count': len(files)})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/ask', methods=['POST'])
def ask():
    question = request.json.get('question', '')
    files = store.get('files', [])
    history = store.get('history', [])

    if not files:
        return jsonify({'error': 'No repository loaded'}), 400
    if not question:
        return jsonify({'error': 'No question provided'}), 400

    try:
        answer = answer_question(question, files, history)

        # Save to conversation history
        store['history'].append({
            'question': question,
            'answer': answer
        })

        return jsonify({'answer': answer})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/reset', methods=['POST'])
def reset():
    store['files'] = []
    store['summaries'] = []
    store['history'] = []
    return jsonify({'status': 'ok'})

if __name__ == '__main__':
    app.run(debug=True) 