import anthropic
from dotenv import load_dotenv

load_dotenv()
client = anthropic.Anthropic()
MODEL = 'claude-sonnet-4-5'

def summarize_file(name, content):
    """Returns a one-line description of what a file does."""
    prompt = f"""You are a code documentation assistant.
In one sentence (max 20 words), describe what this file does.

File: {name}
Content:
{content[:3000]}
"""
    response = client.messages.create(
        model=MODEL,
        max_tokens=100,
        messages=[{'role': 'user', 'content': prompt}]
    )
    return response.content[0].text.strip()

def answer_question(question, files):
    """Given a question and a list of file dicts, return an AI answer."""
    # Build context from all files
    context = ''
    for f in files:
        context += f"\n\n### {f['path']}\n{f['content'][:2000]}"

    prompt = f"""You are a developer onboarding assistant.
Answer the following question about this codebase.
Cite specific file names when relevant.

CODEBASE:
{context}

QUESTION: {question}
"""
    response = client.messages.create(
        model=MODEL,
        max_tokens=1024,
        messages=[{'role': 'user', 'content': prompt}]
    )
    return response.content[0].text.strip()