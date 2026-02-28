/* Agent BIM Romania — Dashboard Logic */

// ── Auth / CSRF ───────────────────────────────────────────────────────────────
function getCSRFToken() {
  return sessionStorage.getItem('csrf_token') || '';
}

async function logout() {
  try {
    await fetch('/logout', { method: 'POST', headers: { 'X-CSRF-Token': getCSRFToken() } });
  } catch { /* ignore */ }
  sessionStorage.clear();
  window.location.href = '/login';
}

// ── Section navigation ────────────────────────────────────────────────────────
const SECTION_TITLES = {
  dashboard: 'Dashboard',
  documents: 'Adaugă Documente',
  generator: 'Generator BIM',
  chat:      'Chat Expert BIM',
  downloads: 'Documente Generate',
};

// Exclude year-only folders (2024, 2025 etc.) — these are document libraries, not real projects
function filterProjects(list) {
  return list.filter(p => !/^\d{4}$/.test(p.trim()));
}

function showSection(name) {
  document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
  document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));

  const page = document.getElementById(`page-${name}`);
  const nav  = document.querySelector(`.nav-item[data-section="${name}"]`);
  if (page) page.classList.add('active');
  if (nav)  nav.classList.add('active');

  document.getElementById('topbarTitle').textContent = SECTION_TITLES[name] || name;

  if (name === 'documents')  loadDocuments();
  if (name === 'downloads')  loadGenerated();
  if (name === 'dashboard')  loadDashboard();
  if (name === 'generator')  loadProjects('genProject');

  // Mobile: close sidebar
  document.getElementById('sidebar').classList.remove('open');
}

document.querySelectorAll('.nav-item').forEach(item => {
  item.addEventListener('click', e => {
    e.preventDefault();
    showSection(item.dataset.section);
  });
});

document.getElementById('menuToggle').addEventListener('click', () => {
  document.getElementById('sidebar').classList.toggle('open');
});

// ── RAG Status ────────────────────────────────────────────────────────────────
async function checkRagStatus() {
  setRagIndicator('checking', 'Verificare RAG...');
  try {
    const data = await apiFetch('/status');
    if (data.rag_ready) {
      setEl('statChunks', fmt(data.chunk_count));
    } else {
      setEl('statChunks', '0');
    }
  } catch {
    setRagIndicator('inactive', 'Server offline');
  }
}

function setRagIndicator(cls, label) {
  const dot   = document.getElementById('ragDot');
  const lbl   = document.getElementById('ragPillLabel');
  if (dot) { dot.className = `rag-dot ${cls}`; }
  if (lbl) lbl.textContent = label;
}

// ── Dashboard ─────────────────────────────────────────────────────────────────
async function loadDashboard() {
  checkRagStatus();

  // Projects (filtered — exclude year-only folders)
  try {
    const all = await apiFetch('/api/projects');
    const projects = filterProjects(all);
    const list = document.getElementById('projectsList');
    if (projects.length === 0) {
      list.innerHTML = '<div class="empty-state">Niciun proiect găsit. Adaugă documente pentru a crea primul proiect.</div>';
    } else {
      list.innerHTML = projects.map(p => `
        <div class="project-tag" onclick="goGenerateProject('${esc(p)}')">
          <span class="project-tag-name">📁 ${esc(p)}</span>
          <span class="project-tag-arrow">→ Generator</span>
        </div>`).join('');
    }
    document.getElementById('statProjects').textContent = projects.length;
  } catch { }

  // Docs count
  try {
    const docs = await apiFetch('/api/documents');
    document.getElementById('statDocs').textContent = docs.length;
  } catch { }

  // Generated
  loadRecentGenerated();
}

async function loadRecentGenerated() {
  try {
    const files = await apiFetch('/api/generated');
    const el = document.getElementById('recentGenerated');
    document.getElementById('statGenerated').textContent = files.length;

    // Badge
    const badge = document.getElementById('dlBadge');
    if (files.length > 0) {
      badge.textContent = files.length;
      badge.style.display = 'inline';
    }

    if (files.length === 0) {
      el.innerHTML = '<div class="empty-state">Nu există fișiere generate încă.</div>';
      return;
    }
    el.innerHTML = files.slice(0, 5).map(f => `
      <div class="recent-item">
        <span class="recent-icon">📄</span>
        <span class="recent-name" title="${esc(f.name)}">${docLabel(f.name)}</span>
        <span class="recent-meta">${f.modified.split(' ')[0]}</span>
        <a class="recent-dl" href="/download/${encodeURIComponent(f.name)}" download>⬇</a>
      </div>`).join('');
  } catch {
    document.getElementById('recentGenerated').innerHTML = '<div class="empty-state">—</div>';
  }
}

// ── Documents ─────────────────────────────────────────────────────────────────
let _allDocs = [];

async function loadDocuments() {
  loadProjects('uploadProject');
  try {
    _allDocs = await apiFetch('/api/documents');
    renderDocsTable(_allDocs);
    document.getElementById('docCount').textContent = _allDocs.length;
  } catch {
    document.getElementById('docsBody').innerHTML = '<tr><td colspan="4" class="empty-cell">Eroare la încărcare.</td></tr>';
  }
}

function renderDocsTable(docs) {
  const body = document.getElementById('docsBody');
  if (docs.length === 0) {
    body.innerHTML = '<tr><td colspan="4" class="empty-cell">Niciun document găsit.</td></tr>';
    return;
  }
  body.innerHTML = docs.map(d => `
    <tr>
      <td style="max-width:280px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap" title="${esc(d.path)}">
        ${d.ext === 'PDF' ? '🔴' : '🔵'} ${esc(d.name)}
      </td>
      <td>${esc(d.project)}</td>
      <td><span class="badge badge-${d.ext.toLowerCase()}">${d.ext}</span></td>
      <td>${d.size_kb} KB</td>
    </tr>`).join('');
}

document.getElementById('docSearch').addEventListener('input', function() {
  const q = this.value.toLowerCase();
  renderDocsTable(q ? _allDocs.filter(d =>
    d.name.toLowerCase().includes(q) || d.project.toLowerCase().includes(q)
  ) : _allDocs);
});

// ── Upload ────────────────────────────────────────────────────────────────────
const uploadZone  = document.getElementById('uploadZone');
const fileInput   = document.getElementById('fileInput');
const uploadBtn   = document.getElementById('uploadBtn');
let _selectedFiles = [];

uploadZone.addEventListener('click', () => fileInput.click());

uploadZone.addEventListener('dragover', e => { e.preventDefault(); uploadZone.classList.add('drag-over'); });
uploadZone.addEventListener('dragleave', () => uploadZone.classList.remove('drag-over'));
uploadZone.addEventListener('drop', e => {
  e.preventDefault();
  uploadZone.classList.remove('drag-over');
  handleFiles(e.dataTransfer.files);
});

fileInput.addEventListener('change', () => handleFiles(fileInput.files));

function handleFiles(files) {
  _selectedFiles = Array.from(files).filter(f =>
    f.name.endsWith('.pdf') || f.name.endsWith('.docx')
  );
  if (_selectedFiles.length > 0) {
    uploadZone.querySelector('.upload-text').textContent =
      `${_selectedFiles.length} fișier(e) selectate: ${_selectedFiles.map(f=>f.name).join(', ')}`;
    uploadBtn.disabled = false;
  }
}

uploadBtn.addEventListener('click', async () => {
  if (!_selectedFiles.length) return;
  const project = document.getElementById('uploadProjectNew').value.trim()
    || document.getElementById('uploadProject').value
    || 'Uploads';

  const bar    = document.getElementById('uploadProgress');
  const fill   = document.getElementById('uploadFill');
  const label  = document.getElementById('uploadLabel');
  const result = document.getElementById('uploadResult');

  bar.style.display = 'block'; result.style.display = 'none';
  uploadBtn.disabled = true;

  let done = 0;
  for (const file of _selectedFiles) {
    label.textContent = `Se încarcă ${file.name}...`;
    const fd = new FormData();
    fd.append('file', file);
    fd.append('project', project);
    try {
      await fetch('/api/upload', { method: 'POST', body: fd, headers: { 'X-CSRF-Token': getCSRFToken() } });
    } catch { }
    done++;
    fill.style.width = Math.round(done / _selectedFiles.length * 100) + '%';
  }

  bar.style.display = 'none';
  result.style.display = 'block';
  result.innerHTML = `<div class="alert" style="background:#F0FDF4;border-color:#86EFAC;color:#166534">
    ✅ ${done} fișier(e) încărcate în proiectul <strong>${esc(project)}</strong>.
    <button class="btn btn-sm btn-primary" style="margin-left:8px" onclick="triggerReindex()">Re-indexează acum</button>
  </div>`;
  showToast(`${done} fișier(e) încărcate în "${project}". Re-indexează pentru a le folosi în chat.`, 'success', 5000);

  _selectedFiles = [];
  uploadBtn.disabled = true;
  uploadZone.querySelector('.upload-text').textContent = 'Trage fișierele PDF sau DOCX aici';
  document.getElementById('reindexBanner').style.display = 'flex';
  loadDocuments();
});

// ── Re-indexare ───────────────────────────────────────────────────────────────
async function triggerReindex() {
  const btn  = document.getElementById('reindexBtn');
  const stat = document.getElementById('reindexStatus');
  if (btn) btn.disabled = true;

  stat.style.display = 'block';
  stat.textContent   = '⏳ Indexare în curs... (poate dura câteva minute)';

  try {
    await apiFetch('/api/reindex', { method: 'POST', headers: { 'X-CSRF-Token': getCSRFToken() } });
    // Poll status
    const poll = setInterval(async () => {
      try {
        const s = await apiFetch('/api/reindex/status');
        if (!s.running) {
          clearInterval(poll);
          if (s.last_result === 'ok') {
            stat.textContent = '✅ Indexare finalizată!';
            showToast('Indexare finalizată cu succes! Baza de cunoștințe a fost actualizată.', 'success', 5000);
          } else {
            stat.textContent = `⚠ ${s.last_result || 'Finalizat'}`;
            showToast('Indexare finalizată cu avertismente. Verifică consola.', 'warn');
          }
          if (btn) btn.disabled = false;
          checkRagStatus();
          loadDashboard();
        }
      } catch { clearInterval(poll); if (btn) btn.disabled = false; }
    }, 3000);
  } catch (e) {
    stat.textContent = '⚠ Eroare: ' + e.message;
    if (btn) btn.disabled = false;
  }
}

// ── Projects loader ───────────────────────────────────────────────────────────
async function loadProjects(selectId) {
  try {
    const all = await apiFetch('/api/projects');
    const projects = filterProjects(all);   // exclude year folders
    const sel = document.getElementById(selectId);
    if (!sel) return;
    const current = sel.value;
    while (sel.options.length > 1) sel.remove(1);
    projects.forEach(p => {
      const opt = new Option(p, p);
      sel.add(opt);
    });
    if (current) sel.value = current;
  } catch { }
}

// ── Generator ─────────────────────────────────────────────────────────────────
let _activeJobId = null;
let _pollTimer   = null;

document.querySelectorAll('.gen-btn').forEach(btn => {
  btn.addEventListener('click', () => startGenerate(btn.dataset.type));
});

function goGenerateType(type) {
  showSection('generator');
  if (type === 'bep') {
    setTimeout(() => openBepModal(), 300);
  } else {
    setTimeout(() => startGenerate(type), 300);
  }
}

function goGenerateProject(project) {
  showSection('generator');
  setTimeout(() => {
    const sel = document.getElementById('genProject');
    if (sel) sel.value = project;
  }, 300);
}

async function startGenerate(docType) {
  const project = document.getElementById('genProject').value.trim();
  const alert   = document.getElementById('genAlert');
  const panel   = document.getElementById('genProgressPanel');
  const result  = document.getElementById('genResult');

  alert.style.display  = 'none';
  result.style.display = 'none';

  if (!project) {
    alert.style.display = 'block';
    alert.textContent   = '⚠ Te rugăm să selectezi un proiect din lista de mai sus.';
    return;
  }

  // Find label
  const card  = document.querySelector(`.gen-card[data-type="${docType}"]`);
  const title = card ? card.querySelector('.gen-card-title').textContent : docType;

  panel.style.display = 'block';
  setEl('genProgressTitle', `Se generează: ${title}`);
  setEl('genProgressSub', `Proiect: ${project} · Durează 30–90 secunde…`);

  // Disable all gen buttons
  document.querySelectorAll('.gen-btn').forEach(b => b.disabled = true);

  try {
    const data = await apiFetch('/api/generate', {
      method:  'POST',
      headers: {'Content-Type': 'application/json', 'X-CSRF-Token': getCSRFToken()},
      body:    JSON.stringify({ type: docType, project }),
    });
    _activeJobId = data.job_id;
    pollGenJob();
  } catch (e) {
    panel.style.display = 'none';
    alert.style.display = 'block';
    alert.textContent   = '⚠ Eroare la pornirea generării: ' + e.message;
    document.querySelectorAll('.gen-btn').forEach(b => b.disabled = false);
  }
}

function pollGenJob() {
  clearInterval(_pollTimer);
  _pollTimer = setInterval(async () => {
    try {
      const s = await apiFetch(`/api/generate/status/${_activeJobId}`);
      if (s.status === 'done') {
        clearInterval(_pollTimer);
        showGenResult(s.file);
      } else if (s.status === 'error') {
        clearInterval(_pollTimer);
        document.getElementById('genProgressPanel').style.display = 'none';
        const al = document.getElementById('genAlert');
        al.style.display = 'block';
        al.textContent   = '⚠ Eroare generare: ' + (s.error || 'necunoscut');
        document.querySelectorAll('.gen-btn').forEach(b => b.disabled = false);
      }
    } catch { }
  }, 2000);
}

function showGenResult(filename) {
  document.getElementById('genProgressPanel').style.display = 'none';
  document.querySelectorAll('.gen-btn').forEach(b => b.disabled = false);

  const result = document.getElementById('genResult');
  result.style.display = 'flex';
  setEl('genResultTitle', '✅ Document generat cu succes!');
  setEl('genResultFile', filename);
  const dl = document.getElementById('genResultDownload');
  dl.href = `/download/${encodeURIComponent(filename)}`;
  dl.setAttribute('download', filename);

  showToast(`Document generat: ${filename}`, 'success');
  loadRecentGenerated();
}

function generateAnother() {
  document.getElementById('genResult').style.display = 'none';
}

// ── Downloads ─────────────────────────────────────────────────────────────────
async function loadGenerated() {
  const body = document.getElementById('generatedBody');
  body.innerHTML = '<tr><td colspan="6" class="empty-cell">Se încarcă...</td></tr>';
  try {
    const files = await apiFetch('/api/generated');
    const badge = document.getElementById('dlBadge');
    badge.textContent = files.length;
    badge.style.display = files.length > 0 ? 'inline' : 'none';
    document.getElementById('statGenerated').textContent = files.length;

    if (files.length === 0) {
      body.innerHTML = '<tr><td colspan="6" class="empty-cell">Nu există fișiere generate încă.<br>Folosește secțiunea Generator BIM.</td></tr>';
      return;
    }
    body.innerHTML = files.map(f => {
      const type    = docType(f.name);
      const proj    = docProject(f.name);
      return `<tr>
        <td style="max-width:200px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap" title="${esc(f.name)}">
          📄 ${esc(f.name)}
        </td>
        <td>${type}</td>
        <td>${proj}</td>
        <td>${f.modified}</td>
        <td>${f.size_kb} KB</td>
        <td>
          <a href="/download/${encodeURIComponent(f.name)}" download class="btn btn-sm btn-primary">⬇ Descarcă</a>
        </td>
      </tr>`;
    }).join('');
  } catch {
    body.innerHTML = '<tr><td colspan="6" class="empty-cell">Eroare la încărcare.</td></tr>';
  }
}

// ── Chat ──────────────────────────────────────────────────────────────────────
const messagesContainer = document.getElementById('messagesContainer');
const userInput         = document.getElementById('userInput');
const sendBtn           = document.getElementById('sendBtn');

userInput.addEventListener('input', () => {
  userInput.style.height = 'auto';
  userInput.style.height = Math.min(userInput.scrollHeight, 160) + 'px';
});

userInput.addEventListener('keydown', e => {
  if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage(); }
});

sendBtn.addEventListener('click', sendMessage);

document.getElementById('newChatBtn').addEventListener('click', async () => {
  await fetch('/reset', { method: 'POST', headers: { 'X-CSRF-Token': getCSRFToken() } });
  messagesContainer.innerHTML = '';
  messagesContainer.appendChild(buildWelcome());
});

document.querySelectorAll('.chip').forEach(chip => {
  chip.addEventListener('click', () => sendMessageText(chip.dataset.msg));
});

function sendMessage() {
  const text = userInput.value.trim();
  if (text) sendMessageText(text);
}

async function sendMessageText(text) {
  if (sendBtn.disabled) return;
  const welcome = document.getElementById('welcomeMsg');
  if (welcome) welcome.remove();

  appendMsg('user', text);
  userInput.value = '';
  userInput.style.height = 'auto';
  setLoading(true);
  const loadEl = appendLoading();

  try {
    const res  = await fetch('/chat', {
      method:  'POST',
      headers: {'Content-Type': 'application/json', 'X-CSRF-Token': getCSRFToken()},
      body:    JSON.stringify({message: text}),
    });
    if (res.status === 401 || res.status === 403) {
      sessionStorage.clear();
      window.location.href = '/login';
      return;
    }
    const data = await res.json();
    loadEl.remove();
    if (res.ok) {
      appendMsg('assistant', data.response);
      // Sources hidden per product requirements
    } else {
      appendMsg('assistant', `Eroare: ${data.error || 'Ceva nu a mers.'}`);
    }
  } catch {
    loadEl.remove();
    appendMsg('assistant', 'Nu am putut contacta serverul. Verifică că app.py rulează.');
  }
  setLoading(false);
  messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

function appendMsg(role, text) {
  const wrap = document.createElement('div');
  wrap.className = `message ${role}`;
  const row = document.createElement('div');
  row.className = 'message-row';
  const av = document.createElement('div');
  av.className  = 'message-avatar';
  av.textContent = role === 'user' ? 'Tu' : 'BIM';
  const bbl = document.createElement('div');
  bbl.className = 'message-bubble';
  bbl.innerHTML = formatText(text);
  row.appendChild(av); row.appendChild(bbl);
  wrap.appendChild(row);

  if (role === 'assistant') {
    const actions = document.createElement('div');
    actions.className = 'message-actions';
    const btn = document.createElement('button');
    btn.className = 'copy-btn';
    btn.innerHTML = '📋 Copiază';
    btn.addEventListener('click', () => {
      navigator.clipboard.writeText(text).then(() => {
        btn.innerHTML = '✅ Copiat';
        btn.classList.add('copied');
        setTimeout(() => { btn.innerHTML = '📋 Copiază'; btn.classList.remove('copied'); }, 2200);
      }).catch(() => showToast('Nu s-a putut copia textul.', 'error'));
    });
    actions.appendChild(btn);
    wrap.appendChild(actions);
  }

  messagesContainer.appendChild(wrap);
  messagesContainer.scrollTop = messagesContainer.scrollHeight;
  return wrap;
}

function appendLoading() {
  const wrap = document.createElement('div');
  wrap.className = 'message assistant';
  const row = document.createElement('div');
  row.className = 'message-row';
  const av = document.createElement('div');
  av.className = 'message-avatar'; av.textContent = 'BIM';
  const lb = document.createElement('div');
  lb.className = 'loading-bubble';
  lb.innerHTML = '<div class="dot"></div><div class="dot"></div><div class="dot"></div>';
  row.appendChild(av); row.appendChild(lb);
  wrap.appendChild(row);
  messagesContainer.appendChild(wrap);
  messagesContainer.scrollTop = messagesContainer.scrollHeight;
  return wrap;
}

function appendSources(sources, msgEl) {
  const panel = document.createElement('div');
  panel.className = 'sources-panel';
  const title = document.createElement('div');
  title.className = 'sources-title';
  title.textContent = `Surse (${sources.length})`;
  panel.appendChild(title);
  sources.forEach(s => {
    const card = document.createElement('div');
    card.className = 'source-card';
    const rel = s.relevance >= .75 ? 'badge-high' : s.relevance >= .5 ? 'badge-med' : 'badge-low';
    const rlbl = s.relevance >= .75 ? 'Relevant' : s.relevance >= .5 ? 'Parțial' : 'Slab';
    card.innerHTML = `
      <span class="source-icon">📄</span>
      <div class="source-info">
        <div class="source-title" title="${esc(s.source)}">${esc(s.title)}</div>
        <div class="source-meta">${esc(s.category)} · Pag. ${s.page}</div>
      </div>
      <span class="source-badge ${rel}">${rlbl}</span>`;
    panel.appendChild(card);
  });
  msgEl.appendChild(panel);
}

function buildWelcome() {
  const d = document.createElement('div');
  d.id = 'welcomeMsg';
  d.className = 'welcome-message';
  d.innerHTML = `
    <div class="welcome-icon"><svg width="52" height="52" viewBox="0 0 48 48" fill="none">
      <rect width="48" height="48" rx="12" fill="#EFF6FF"/>
      <path d="M12 33L24 15L36 33H12Z" fill="#1D4ED8" opacity=".8"/>
      <rect x="18" y="24" width="12" height="9" fill="#1D4ED8" opacity=".6"/>
    </svg></div>
    <h2>Expert BIM România</h2>
    <p>Pune orice întrebare despre BIM, ISO 19650, CDE sau proiectele tale.</p>
    <div class="welcome-chips">
      <button class="chip" data-msg="Ce este BIM și de ce este important pentru România?">Ce este BIM?</button>
      <button class="chip" data-msg="Care este termenul limită 2026 pentru digitalizarea construcțiilor?">Termenul 2026</button>
      <button class="chip" data-msg="Ce prevede ISO 19650-2 pentru EIR și BEP?">ISO 19650</button>
      <button class="chip" data-msg="Cum funcționează clash detection?">Clash detection</button>
    </div>`;
  d.querySelectorAll('.chip').forEach(c => c.addEventListener('click', () => sendMessageText(c.dataset.msg)));
  return d;
}

function setLoading(on) {
  sendBtn.disabled   = on;
  userInput.disabled = on;
}

function formatText(text) {
  let h = text.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
  h = h.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
  h = h.replace(/\*([^*\n]+?)\*/g, '<em>$1</em>');
  h = h.replace(/`([^`]+)`/g, '<code>$1</code>');

  const lines = h.split('\n');
  const out   = [];
  let inUL = false, inOL = false;

  const closeList = () => {
    if (inUL) { out.push('</ul>'); inUL = false; }
    if (inOL) { out.push('</ol>'); inOL = false; }
  };

  for (const line of lines) {
    const t = line.trim();
    if (!t) { closeList(); continue; }
    if (t.startsWith('### ')) { closeList(); out.push(`<h4>${t.slice(4)}</h4>`); continue; }
    if (t.startsWith('## '))  { closeList(); out.push(`<h3>${t.slice(3)}</h3>`); continue; }
    if (t.startsWith('# '))   { closeList(); out.push(`<h2>${t.slice(2)}</h2>`); continue; }
    if (t === '---' || t === '___') { closeList(); out.push('<hr>'); continue; }
    if (t.startsWith('&gt; ')) { closeList(); out.push(`<blockquote>${t.slice(5)}</blockquote>`); continue; }
    const ulm = t.match(/^[-*•]\s+(.+)/);
    if (ulm) {
      if (inOL) { out.push('</ol>'); inOL = false; }
      if (!inUL) { out.push('<ul>'); inUL = true; }
      out.push(`<li>${ulm[1]}</li>`); continue;
    }
    const olm = t.match(/^\d+[.)]\s+(.+)/);
    if (olm) {
      if (inUL) { out.push('</ul>'); inUL = false; }
      if (!inOL) { out.push('<ol>'); inOL = true; }
      out.push(`<li>${olm[1]}</li>`); continue;
    }
    closeList();
    out.push(`<p>${line}</p>`);
  }
  closeList();
  return out.join('');
}

// ── Helpers ───────────────────────────────────────────────────────────────────
function esc(s) { return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;'); }
function setEl(id, txt) { const e = document.getElementById(id); if (e) e.textContent = txt; }
function fmt(n) { return Number(n).toLocaleString('ro-RO'); }

// ── Toast notifications ────────────────────────────────────────────────────────
function showToast(msg, type = 'info', duration = 3800) {
  let container = document.getElementById('toastContainer');
  if (!container) {
    container = document.createElement('div');
    container.id = 'toastContainer';
    container.className = 'toast-container';
    document.body.appendChild(container);
  }
  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;
  const icons = { info: 'ℹ️', success: '✅', error: '❌', warn: '⚠️' };
  toast.innerHTML = `<span>${icons[type] || 'ℹ️'}</span><span>${esc(msg)}</span>`;
  container.appendChild(toast);
  setTimeout(() => {
    toast.style.animation = 'toastOut .25s ease forwards';
    setTimeout(() => toast.remove(), 260);
  }, duration);
}

async function apiFetch(url, opts) {
  const r = await fetch(url, opts);
  if (r.status === 401 || r.status === 403) {
    sessionStorage.clear();
    window.location.href = '/login';
    throw new Error(`HTTP ${r.status}`);
  }
  if (!r.ok) throw new Error(`HTTP ${r.status}`);
  return r.json();
}

function docLabel(name) {
  if (name.startsWith('BEP_'))        return '📋 ' + name;
  if (name.startsWith('LOD_'))        return '📊 ' + name;
  if (name.startsWith('EIR_'))        return '📄 ' + name;
  if (name.startsWith('CERINTE_'))    return '🔍 ' + name;
  if (name.startsWith('CHECKLIST_'))  return '✅ ' + name;
  if (name.startsWith('MINUTA_'))     return '📝 ' + name;
  if (name.startsWith('ISO19650_'))   return '🏛️ ' + name;
  return '📄 ' + name;
}

function docType(name) {
  if (name.startsWith('BEP_'))       return 'BEP';
  if (name.startsWith('LOD_'))       return 'LOD Matrix';
  if (name.startsWith('EIR_'))       return 'EIR';
  if (name.startsWith('CERINTE_'))   return 'Cerințe BIM';
  if (name.startsWith('CHECKLIST_')) return 'Checklist';
  if (name.startsWith('MINUTA_'))    return 'Minută';
  if (name.startsWith('ISO19650_'))  return 'ISO 19650';
  return '—';
}

function docProject(name) {
  const m = name.match(/^[A-Z0-9]+_(.+?)_\d{8}/);
  return m ? m[1].replace(/_/g, ' ') : '—';
}

// ── BEP Parametric Modal ──────────────────────────────────────────────────────
function openBepModal() {
  const modal = document.getElementById('bepModal');
  modal.classList.add('active');
  // Pre-fill project name from dropdown if selected
  const genProj = document.getElementById('genProject');
  if (genProj && genProj.value) {
    document.getElementById('bepProject').value = genProj.value;
  }
}

function closeBepModal() {
  document.getElementById('bepModal').classList.remove('active');
}

// Close modal on overlay click
document.getElementById('bepModal').addEventListener('click', function(e) {
  if (e.target === this) closeBepModal();
});

// Close modal on Escape key
document.addEventListener('keydown', function(e) {
  if (e.key === 'Escape') closeBepModal();
});

async function submitBepParametric() {
  const project   = document.getElementById('bepProject').value.trim();
  const client    = document.getElementById('bepClient').value.trim();
  const workType  = document.getElementById('bepWorkType').value;
  const phase     = document.getElementById('bepPhase').value;
  const contractor = document.getElementById('bepContractor').value.trim() || 'De desemnat';
  const cde       = document.getElementById('bepCDE').value;
  const standards = document.getElementById('bepStandards').value.trim();
  const revitData = document.getElementById('bepRevitData').value.trim();

  // Collect checked disciplines
  const disciplines = [];
  document.querySelectorAll('#bepModal .checkbox-grid input[type="checkbox"]:checked').forEach(cb => {
    disciplines.push(cb.value);
  });

  // Validation
  if (!project) { showToast('Te rugăm să completezi numele proiectului.', 'warn'); return; }
  if (!client)  { showToast('Te rugăm să completezi clientul/beneficiarul.', 'warn'); return; }
  if (disciplines.length === 0) { showToast('Selectează cel puțin o disciplină BIM.', 'warn'); return; }

  // Close modal
  closeBepModal();

  // Show progress
  const panel  = document.getElementById('genProgressPanel');
  const result = document.getElementById('genResult');
  const alert  = document.getElementById('genAlert');
  alert.style.display  = 'none';
  result.style.display = 'none';
  panel.style.display  = 'block';
  setEl('genProgressTitle', 'Se generează: BEP Parametric (13 capitole)');
  setEl('genProgressSub', `Proiect: ${project} · 4 apeluri AI · Durează 60–120 secunde…`);

  // Disable gen buttons
  document.querySelectorAll('.gen-btn').forEach(b => b.disabled = true);

  try {
    const data = await apiFetch('/api/generate', {
      method: 'POST',
      headers: {'Content-Type': 'application/json', 'X-CSRF-Token': getCSRFToken()},
      body: JSON.stringify({
        type: 'bep_parametric',
        project,
        client,
        work_type: workType,
        phase,
        disciplines,
        contractor,
        cde_platform: cde,
        standards,
        revit_data: revitData,
      }),
    });
    _activeJobId = data.job_id;
    pollGenJob();
  } catch (e) {
    panel.style.display = 'none';
    alert.style.display = 'block';
    alert.textContent   = '⚠ Eroare la pornirea generării BEP: ' + e.message;
    document.querySelectorAll('.gen-btn').forEach(b => b.disabled = false);
  }
}

// ── Init ──────────────────────────────────────────────────────────────────────
showSection('dashboard');
