from flask import Flask, render_template, request, jsonify, Response, stream_with_context
from dotenv import load_dotenv
from github_loader import get_repo_files
from ai_engine import summarize_file, summarize_all_files, answer_question
import os
import json
import zipfile
import io

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
        files = get_repo_files(url)
        if not files:
            return jsonify({'error': 'No supported files found in this repository'}), 400
        summary_texts = summarize_all_files(files)
        summaries = []
        for i, f in enumerate(files):
            summaries.append({'path': f['path'], 'summary': summary_texts[i]})
        store['files'] = files
        store['summaries'] = summaries
        store['history'] = []
        return jsonify({'summaries': summaries, 'file_count': len(files)})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/load-stream', methods=['POST'])
def load_stream():
    url = request.json.get('url', '')
    if not url:
        return jsonify({'error': 'No URL provided'}), 400

    def generate():
        try:
            files = get_repo_files(url)
            if not files:
                yield f"data: {json.dumps({'error': 'No supported files found'})}\n\n"
                return
            total = len(files)
            summaries = []
            for i, f in enumerate(files):
                summary = summarize_file(f)
                summaries.append({'path': f['path'], 'summary': summary})
                yield f"data: {json.dumps({'progress': i + 1, 'total': total, 'file': f['path'], 'summary': summary})}\n\n"
            store['files'] = files
            store['summaries'] = summaries
            store['history'] = []
            yield f"data: {json.dumps({'done': True, 'file_count': total})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return Response(
        stream_with_context(generate()),
        mimetype='text/event-stream',
        headers={'Cache-Control': 'no-cache', 'X-Accel-Buffering': 'no'}
    )

@app.route('/upload', methods=['POST'])
def upload_files():
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    uploaded_file = request.files['file']
    if not uploaded_file.filename.endswith('.zip'):
        return jsonify({'error': 'Only zip files are supported'}), 400

    def generate():
        try:
            zip_bytes = uploaded_file.read()
            zf = zipfile.ZipFile(io.BytesIO(zip_bytes))
            SUPPORTED = ('.py', '.js', '.ts', '.md')
            names = [
                n for n in zf.namelist()
                if any(n.endswith(ext) for ext in SUPPORTED)
                and not n.startswith('__MACOSX')
            ][:30]
            if not names:
                yield f"data: {json.dumps({'error': 'No supported files found in zip'})}\n\n"
                return
            total = len(names)
            files = []
            summaries = []
            for i, name in enumerate(names):
                content = zf.read(name).decode('utf-8', errors='ignore')
                file_obj = {'name': name.split('/')[-1], 'path': name, 'content': content}
                summary = summarize_file(file_obj)
                files.append(file_obj)
                summaries.append({'path': name, 'summary': summary})
                yield f"data: {json.dumps({'progress': i + 1, 'total': total, 'file': name, 'summary': summary})}\n\n"
            store['files'] = files
            store['summaries'] = summaries
            store['history'] = []
            yield f"data: {json.dumps({'done': True, 'file_count': total})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return Response(
        stream_with_context(generate()),
        mimetype='text/event-stream',
        headers={'Cache-Control': 'no-cache', 'X-Accel-Buffering': 'no'}
    )

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
        store['history'].append({'question': question, 'answer': answer})
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