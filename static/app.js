function setStatus(text, state = 'ready') {
  document.getElementById('status-text').textContent = text;
  const dot = document.getElementById('status-dot');
  dot.className = 'status-dot' + (state !== 'ready' ? ' ' + state : '');
}

function getTime() {
  return new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

function addMessage(sender, text, type) {
  const history = document.getElementById('chat-history');
  const welcome = history.querySelector('.chat-welcome');
  if (welcome) welcome.remove();

  const msg = document.createElement('div');
  msg.className = 'msg ' + type;
  msg.innerHTML = `
    <div class="msg-sender">${sender}</div>
    <div class="msg-bubble">${text}</div>
    <div class="msg-time">${getTime()}</div>
  `;
  history.appendChild(msg);
  history.scrollTop = history.scrollHeight;
}

function renderFileCard(file) {
  const ext = file.path.split('.').pop();
  const name = file.path.split('/').pop();
  return `
    <div class="file-card">
      <div class="file-card-header">
        <span class="file-ext">${ext}</span>
        <span class="file-name">${name}</span>
      </div>
      <div class="file-summary">${file.summary}</div>
    </div>
  `;
}

async function loadRepo() {
  const url = document.getElementById('repo-url').value.trim();
  if (!url) { setStatus('Enter a GitHub URL first', 'error'); return; }

  setStatus('Fetching repo…', 'loading');
  document.getElementById('file-list').innerHTML =
    "<div class='file-list-empty'>Loading files — this may take up to 90 seconds…</div>";

  try {
    const res = await fetch('/load', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ url })
    });
    const data = await res.json();
    if (data.error) throw new Error(data.error);

    const count = data.file_count;
    document.getElementById('file-count').textContent =
      count + (count === 30 ? ' (capped)' : '') + ' files';
    document.getElementById('file-list').innerHTML =
      data.summaries.map(renderFileCard).join('');

    setStatus('Loaded ' + count + ' files');
    addMessage('Code Compass', 'Repository loaded. Ask me anything about the codebase.', 'ai');
  } catch (err) {
    setStatus('Error: ' + err.message, 'error');
    document.getElementById('file-list').innerHTML =
      "<div class='file-list-empty'>Failed to load. Check the URL and try again.</div>";
  }
}

async function askQuestion() {
  const input = document.getElementById('question');
  const question = input.value.trim();
  if (!question) return;

  input.value = '';
  input.disabled = true;
  addMessage('You', question, 'user');
  setStatus('Thinking…', 'loading');

  try {
    const res = await fetch('/ask', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question })
    });
    const data = await res.json();
    if (data.error) throw new Error(data.error);
    addMessage('Code Compass', data.answer, 'ai');
    setStatus('Ready');
  } catch (err) {
    addMessage('Code Compass', 'Error: ' + err.message, 'ai');
    setStatus('Error', 'error');
  } finally {
    input.disabled = false;
    input.focus();
  }
}

async function resetSession() {
  await fetch('/reset', { method: 'POST' });
  document.getElementById('file-list').innerHTML =
    "<div class='file-list-empty'>No repository loaded yet.</div>";
  document.getElementById('file-count').textContent = '';
  document.getElementById('repo-url').value = '';
  document.getElementById('chat-history').innerHTML =
    "<div class='chat-welcome'><p>Load a repository from the sidebar, then ask anything about the codebase.</p></div>";
  setStatus('Session cleared');
}