function setStatus(text, state = 'ready') {
  document.getElementById('status-text').textContent = text;
  const dot = document.getElementById('status-dot');
  dot.className = 'status-dot' + (state !== 'ready' ? ' ' + state : '');
}

function getTime() {
  return new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

function updateProgress(current, total) {
  const wrap = document.getElementById('progress-wrap');
  const bar = document.getElementById('progress-bar');
  if (!wrap || !bar) return;
  wrap.style.display = 'block';
  bar.style.width = Math.round((current / total) * 100) + '%';
}

function hideProgress() {
  const wrap = document.getElementById('progress-wrap');
  const bar = document.getElementById('progress-bar');
  if (!wrap || !bar) return;
  wrap.style.display = 'none';
  bar.style.width = '0%';
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
  document.getElementById('file-count').textContent = '';
  document.getElementById('file-list').innerHTML =
    "<div class='file-list-empty'>Connecting to GitHub…</div>";

  try {
    const response = await fetch('/load-stream', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ url })
    });

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';
    let fileCards = [];

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop();

      for (const line of lines) {
        if (!line.startsWith('data: ')) continue;
        const data = JSON.parse(line.slice(6));

        if (data.error) {
          setStatus('Error: ' + data.error, 'error');
          hideProgress();
          document.getElementById('file-list').innerHTML =
            "<div class='file-list-empty'>Failed to load. Check the URL.</div>";
          return;
        }

        if (data.progress) {
          setStatus(`Summarizing file ${data.progress} of ${data.total}…`, 'loading');
          updateProgress(data.progress, data.total);
          document.getElementById('file-count').textContent =
            `${data.progress} of ${data.total}`;
          fileCards.push({ path: data.file, summary: data.summary });
          document.getElementById('file-list').innerHTML =
            fileCards.map(renderFileCard).join('');
        }

        if (data.done) {
          hideProgress();
          const capMsg = data.was_capped ? ' (capped at 30)' : '';
          setStatus('Loaded ' + data.file_count + ' files');
          document.getElementById('file-count').textContent =
            data.file_count + ' files';
          addMessage('Code Compass',
            'Repository loaded' + (data.was_capped ? ' — showing first 30 files out of more available.' : '.') +
            'Ask me anything about the codebase.', 'ai');
        }
      }
    }
  } catch (err) {
    hideProgress();
    setStatus('Error: ' + err.message, 'error');
    document.getElementById('file-list').innerHTML =
      "<div class='file-list-empty'>Failed to load. Check the URL.</div>";
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
  hideProgress();
  document.getElementById('file-list').innerHTML =
    "<div class='file-list-empty'>No repository loaded yet.</div>";
  document.getElementById('file-count').textContent = '';
  document.getElementById('repo-url').value = '';
  document.getElementById('chat-history').innerHTML =
    "<div class='chat-welcome'><p>Load a repository from the sidebar, then ask anything about the codebase.</p></div>";
  setStatus('Session cleared');
}

async function uploadFiles(input) {
  const file = input.files[0];
  if (!file) return;

  setStatus('Uploading ' + file.name + '…', 'loading');
  document.getElementById('file-count').textContent = '';
  document.getElementById('file-list').innerHTML =
    "<div class='file-list-empty'>Processing zip file…</div>";

  const formData = new FormData();
  formData.append('file', file);

  try {
    const response = await fetch('/upload', {
      method: 'POST',
      body: formData
    });

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';
    let fileCards = [];

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop();

      for (const line of lines) {
        if (!line.startsWith('data: ')) continue;
        const data = JSON.parse(line.slice(6));

        if (data.error) {
          setStatus('Error: ' + data.error, 'error');
          hideProgress();
          document.getElementById('file-list').innerHTML =
            "<div class='file-list-empty'>Failed to process zip.</div>";
          return;
        }

        if (data.progress) {
          setStatus(`Summarizing file ${data.progress} of ${data.total}…`, 'loading');
          updateProgress(data.progress, data.total);
          document.getElementById('file-count').textContent =
            `${data.progress} of ${data.total}`;
          fileCards.push({ path: data.file, summary: data.summary });
          document.getElementById('file-list').innerHTML =
            fileCards.map(renderFileCard).join('');
        }

        if (data.done) {
          hideProgress();
          setStatus('Loaded ' + data.file_count + ' files');
          document.getElementById('file-count').textContent =
            data.file_count + ' files';
          addMessage('Code Compass',
            'Zip file loaded. Ask me anything about the codebase.', 'ai');
        }
      }
    }
  } catch (err) {
    hideProgress();
    setStatus('Error: ' + err.message, 'error');
    document.getElementById('file-list').innerHTML =
      "<div class='file-list-empty'>Failed to process zip.</div>";
  }
}