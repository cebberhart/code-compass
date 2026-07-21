import anthropic
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

load_dotenv()
client = anthropic.Anthropic()
MODEL = 'claude-sonnet-4-5'

def summarize_file(file):
    """Returns a one-line description of what a file does."""
    name = file['name']
    content = file['content']
    prompt = f"""You are a code documentation assistant.
In one sentence (max 20 words), describe what this file does.

File: {name}
Content:
{content[:3000]}
"""
    for attempt in range(3):
        try:
            response = client.messages.create(
                model=MODEL,
                max_tokens=100,
                messages=[{'role': 'user', 'content': prompt}]
            )
            return response.content[0].text.strip()
        except Exception as e:
            if '429' in str(e) and attempt < 2:
                time.sleep(2 ** attempt)
                continue
            return f"Could not summarize: {str(e)}"

def summarize_all_files(files):
    """Summarizes all files in parallel using a thread pool."""
    summaries = [None] * len(files)

    with ThreadPoolExecutor(max_workers=5) as executor:
        future_to_index = {
            executor.submit(summarize_file, f): i
            for i, f in enumerate(files)
        }
        for future in as_completed(future_to_index):
            i = future_to_index[future]
            try:
                summaries[i] = future.result()
            except Exception as e:
                summaries[i] = f"Error: {str(e)}"

    return summaries

def answer_question(question, files, history=None):
    """Given a question, file list, and optional history, return an AI answer."""
    # Build codebase context
    context = ''
    for f in files:
        context += f"\n\n### {f['path']}\n{f['content'][:2000]}"

    # Build conversation messages
    messages = []

    # Add previous conversation history if it exists
    if history:
        for entry in history[-10:]: # only last 10 exchanges for history
            messages.append({'role': 'user', 'content': entry['question']})
            messages.append({'role': 'assistant', 'content': entry['answer']})

    # Add the current question with codebase context
    prompt = f"""You are a developer onboarding assistant.
Answer the following question about this codebase.
Cite specific file names when relevant.
Keep your answer clear and concise.

CODEBASE:
{context}

QUESTION: {question}
"""
    messages.append({'role': 'user', 'content': prompt})

    response = client.messages.create(
        model=MODEL,
        max_tokens=1024,
        messages=messages
    )
    return response.content[0].text.strip()