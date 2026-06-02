// ── state ──
let docs = [];         // { name, chunks, filename }
let messages = [];     // { role, content, sources }
let isLoading = false;
let currentDocFilename = null;

const API = 'http://localhost:5000';

// ── elements ──
const fileInput     = document.getElementById('fileInput');
const uploadZone    = document.getElementById('uploadZone');
const uploadProgress= document.getElementById('uploadProgress');
const progressFill  = document.getElementById('progressFill');
const progressLabel = document.getElementById('progressLabel');
const docList       = document.getElementById('docList');
const docEmpty      = document.getElementById('docEmpty');
const chatEmpty     = document.getElementById('chatEmpty');
const messageList   = document.getElementById('messageList');
const questionInput = document.getElementById('questionInput');
const sendBtn       = document.getElementById('sendBtn');
const statusLabel   = document.getElementById('statusLabel');
const inputHint     = document.getElementById('inputHint');

// ── drag and drop ──
uploadZone.addEventListener('dragover', e => {
e.preventDefault();
uploadZone.classList.add('drag-over');
});
uploadZone.addEventListener('dragleave', () => uploadZone.classList.remove('drag-over'));
uploadZone.addEventListener('drop', e => {
e.preventDefault();
uploadZone.classList.remove('drag-over');
const files = Array.from(e.dataTransfer.files).filter(f => f.type === 'application/pdf');
if (files.length) handleFiles(files);
});

fileInput.addEventListener('change', () => {
if (fileInput.files.length) handleFiles(Array.from(fileInput.files));
});

// ── upload ──
async function handleFiles(files) {
for (const file of files) {
    await uploadFile(file);
}
}

async function uploadFile(file) {
uploadProgress.classList.add('visible');
progressFill.style.width = '0%';
progressLabel.textContent = `uploading ${file.name}…`;

// Animate progress bar while waiting
let pct = 0;
const tick = setInterval(() => {
    pct = Math.min(pct + Math.random() * 8, 85);
    progressFill.style.width = pct + '%';
}, 120);

try {
    const formData = new FormData();
    formData.append('file', file);

    const res = await fetch(`${API}/upload`, { method: 'POST', body: formData });
    const data = await res.json();

    clearInterval(tick);

    if (!res.ok) throw new Error(data.error || 'Upload failed');

    progressFill.style.width = '100%';
    progressLabel.textContent = `✓ ${data.chunks} chunks indexed`;

    setTimeout(() => {
    uploadProgress.classList.remove('visible');
    progressFill.style.width = '0%';
    }, 1800);

    // Add to doc list
    docs.push({ name: file.name, chunks: data.chunks, filename: data.filename });
    currentDocFilename = data.filename;
    renderDocList();
    enableChat();

} catch (err) {
    clearInterval(tick);
    progressFill.style.width = '0%';
    progressLabel.textContent = `✗ ${err.message}`;
    setTimeout(() => uploadProgress.classList.remove('visible'), 2500);
}

// Reset file input
fileInput.value = '';
}

// ── doc list ──
function renderDocList() {
    // clear everything first
    docList.innerHTML = '';

    if (docs.length === 0) {
        docList.innerHTML = `
            <div class="doc-list__empty" id="docEmpty">
                No documents loaded.<br />
                Upload a PDF to begin.
            </div>`;
        return;
    }

    docs.forEach((doc, idx) => {
        const el = document.createElement('div');
        el.className = 'doc-item' + (doc.filename === currentDocFilename ? ' active' : '');
        el.innerHTML = `
            <div class="doc-item__icon">PDF</div>
            <div class="doc-item__body">
                <div class="doc-item__name" title="${doc.name}">${doc.name}</div>
                <div class="doc-item__meta">${doc.chunks} chunks indexed</div>
            </div>
            <button class="doc-item__remove" title="Remove" onclick="removeDoc(${idx}, event)">✕</button>
        `;
        el.addEventListener('click', () => selectDoc(idx));
        docList.appendChild(el);
    });
}

function selectDoc(idx) {
    currentDocFilename = docs[idx].filename;
    document.getElementById('activeDocLabel').textContent = currentDocFilename;
    renderDocList();
}

async function removeDoc(idx, e) {
    e.stopPropagation();
    const doc = docs[idx];

    try {
        await fetch(`${API}/remove`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ filename: doc.filename })
        });
    } catch (_) {}

    docs.splice(idx, 1);
    if (docs.length === 0) {
        currentDocFilename = null;
        disableChat();
    } else {
        currentDocFilename = docs[0].filename;
    }
    renderDocList();
}

// ── chat enable/disable ──
function enableChat() {
    questionInput.disabled = false;
    sendBtn.disabled = false;
    inputHint.textContent = 'enter ↵ to send · shift+enter for new line';
    statusLabel.textContent = 'ready';
    statusLabel.className = 'topbar__status ready';
    document.getElementById('activeDocLabel').textContent = currentDocFilename || 'none';
}

function disableChat() {
questionInput.disabled = true;
sendBtn.disabled = true;
inputHint.textContent = 'upload a document to begin';
statusLabel.textContent = 'awaiting document';
statusLabel.className = 'topbar__status';
}

// ── textarea auto-resize ──
questionInput.addEventListener('input', () => {
questionInput.style.height = 'auto';
questionInput.style.height = Math.min(questionInput.scrollHeight, 180) + 'px';
});

questionInput.addEventListener('keydown', e => {
if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    sendQuestion();
}
});

// ── hints ──
function useHint(btn) {
if (docs.length === 0) return;
questionInput.value = btn.textContent;
questionInput.focus();
}

// ── send ──
async function sendQuestion() {
const q = questionInput.value.trim();
if (!q || isLoading || docs.length === 0) return;

isLoading = true;
questionInput.value = '';
questionInput.style.height = 'auto';
sendBtn.disabled = true;

// Show message list, hide empty state
chatEmpty.style.display = 'none';
messageList.style.display = 'flex';

// User message
appendMessage('user', q, []);

// Thinking indicator
const thinkingEl = appendThinking();

statusLabel.textContent = 'thinking…';
statusLabel.className = 'topbar__status';

try {
    const res = await fetch(`${API}/ask`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question: q, filename: currentDocFilename })
    });
    const data = await res.json();

    thinkingEl.remove();

    if (!res.ok) throw new Error(data.error || 'Request failed');

    appendMessage('assistant', data.answer, data.sources || []);
    statusLabel.textContent = 'ready';
    statusLabel.className = 'topbar__status ready';

} catch (err) {
    thinkingEl.remove();
    appendMessage('assistant', `Error: ${err.message}`, []);
    statusLabel.textContent = 'error';
    statusLabel.className = 'topbar__status';
}

isLoading = false;
sendBtn.disabled = false;
questionInput.focus();
}

// ── message rendering ──
function appendMessage(role, content, sources) {
const now = new Date().toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', hour12: false });

const el = document.createElement('div');
el.className = `message message--${role}`;

let sourcesHTML = '';
if (sources && sources.length > 0) {
    sourcesHTML = `<div class="message__sources">` +
    sources.map(s => `
        <div class="source-chip">
        <span class="source-chip__label">page ${s.page}</span>
        <span class="source-chip__text">${escapeHTML(s.excerpt)}</span>
        </div>
    `).join('') +
    `</div>`;
}

el.innerHTML = `
    <div class="message__header">
    <span class="message__role">${role === 'user' ? 'you' : 'scholarmind'}</span>
    <span class="message__time">${now}</span>
    </div>
    <div class="message__body">${renderMarkdown(content)}</div>
    ${sourcesHTML}
`;

messageList.appendChild(el);
messageList.scrollTop = messageList.scrollHeight;

messages.push({ role, content, sources });
return el;
}

function appendThinking() {
const el = document.createElement('div');
el.className = 'thinking';
el.innerHTML = `
    <div class="thinking__dots">
    <div class="thinking__dot"></div>
    <div class="thinking__dot"></div>
    <div class="thinking__dot"></div>
    </div>
    <span class="thinking__label">reading document…</span>
`;
messageList.appendChild(el);
messageList.scrollTop = messageList.scrollHeight;
return el;
}

function escapeHTML(str) {
return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

function renderMarkdown(str) {
return escapeHTML(str)
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.+?)\*/g, '<em>$1</em>')
    .replace(/^#{1,3} (.+)$/gm, '<strong>$1</strong>')
    .replace(/^\d+\. (.+)$/gm, '<div style="margin:0.25rem 0 0.25rem 1rem;">$1</div>')
    .replace(/^[-•] (.+)$/gm, '<div style="margin:0.25rem 0 0.25rem 1rem;">· $1</div>')
    .replace(/\n\n/g, '</p><p style="margin-top:0.75rem">')
    .replace(/\n/g, '<br>');
}

// ── reset ──
async function resetSession() {
try {
    await fetch(`${API}/reset`, { method: 'POST' });
} catch (_) {}

docs = [];
messages = [];
currentDocFilename = null;

messageList.innerHTML = '';
messageList.style.display = 'none';
chatEmpty.style.display = 'flex';
docEmpty.style.display = 'block';
docList.querySelectorAll('.doc-item').forEach(i => i.remove());

disableChat();
}