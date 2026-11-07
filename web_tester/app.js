(() => {
  const STORAGE_KEY = 'lumeei.webTester.apiUrl';

  const el = {
    apiUrl: document.getElementById('apiUrl'),
    btnPing: document.getElementById('btnPing'),
    btnSend: document.getElementById('btnSend'),
    chatForm: document.getElementById('chatForm'),
    question: document.getElementById('question'),
    messages: document.getElementById('messages'),
    debug: document.getElementById('debug'),
    debugPanel: document.getElementById('debugPanel'),
    showDebug: document.getElementById('showDebug'),
    healthPills: document.getElementById('healthPills'),
  };

  function baseUrl() {
    return (el.apiUrl.value || '').trim().replace(/\/+$/, '');
  }

  function saveUrl() {
    localStorage.setItem(STORAGE_KEY, baseUrl());
  }

  function setDebug(obj) {
    el.debug.textContent =
      typeof obj === 'string' ? obj : JSON.stringify(obj, null, 2);
  }

  function addMessage(role, text) {
    const div = document.createElement('div');
    div.className = `msg ${role}`;
    div.textContent = text;
    el.messages.appendChild(div);
    el.messages.scrollTop = el.messages.scrollHeight;
  }

  function renderHealth(data, error) {
    el.healthPills.innerHTML = '';
    const add = (text, cls) => {
      const s = document.createElement('span');
      s.className = `pill ${cls || ''}`.trim();
      s.textContent = text;
      el.healthPills.appendChild(s);
    };

    if (error) {
      add('offline / hiba', 'bad');
      add(String(error).slice(0, 80), 'bad');
      return;
    }

    add(data.ok ? 'ok' : 'not ok', data.ok ? 'ok' : 'bad');
    add(`rag ${data.ragReady ? '✓' : '✗'}`, data.ragReady ? 'ok' : 'bad');
    add(`llm ${data.llmReady ? '✓' : '✗'}`, data.llmReady ? 'ok' : 'bad');
    if (typeof data.uptimeSec === 'number') {
      add(`up ${data.uptimeSec}s`);
    }
    const books = Array.isArray(data.books) ? data.books.length : 0;
    add(`${books} könyv`);
  }

  async function api(path, options = {}) {
    const url = `${baseUrl()}${path}`;
    const ctrl = new AbortController();
    const timer = setTimeout(() => ctrl.abort(), options.timeoutMs || 120000);
    try {
      const res = await fetch(url, {
        ...options,
        signal: ctrl.signal,
        headers: {
          Accept: 'application/json',
          ...(options.body ? { 'Content-Type': 'application/json' } : {}),
          ...(options.headers || {}),
        },
      });
      const text = await res.text();
      let json = null;
      try {
        json = text ? JSON.parse(text) : null;
      } catch {
        json = { raw: text };
      }
      if (!res.ok) {
        const detail =
          (json && (json.detail || json.message)) || text || res.statusText;
        throw new Error(`${res.status}: ${detail}`);
      }
      return json;
    } finally {
      clearTimeout(timer);
    }
  }

  async function ping() {
    saveUrl();
    el.btnPing.disabled = true;
    try {
      const data = await api('/health', { method: 'GET', timeoutMs: 20000 });
      renderHealth(data);
      setDebug({ health: data, apiUrl: baseUrl() });
      return data;
    } catch (err) {
      renderHealth(null, err.message || err);
      setDebug({ error: String(err), apiUrl: baseUrl() });
      throw err;
    } finally {
      el.btnPing.disabled = false;
    }
  }

  async function translate(text, source, target) {
    const data = await api('/v1/translate', {
      method: 'POST',
      timeoutMs: 20000,
      body: JSON.stringify({ text, source, target }),
    });
    return data.text;
  }

  async function ask(hungarianQuestion) {
    let englishQuestion = hungarianQuestion;
    let translateOk = true;
    try {
      englishQuestion = await translate(hungarianQuestion, 'hu', 'en');
    } catch (err) {
      translateOk = false;
      // Régi Cloud Run image fordítás nélkül: magyarul küldjük (gyengébb minőség).
      console.warn('translate Hu→En failed, fallback raw HU', err);
    }

    const chat = await api('/v1/chat', {
      method: 'POST',
      timeoutMs: 180000,
      body: JSON.stringify({
        question: englishQuestion,
        hungarianQuestion,
      }),
    });
    const englishAnswer = chat.answer || '';
    let hungarianAnswer = englishAnswer;
    try {
      hungarianAnswer = await translate(englishAnswer, 'en', 'hu');
    } catch (err) {
      translateOk = false;
      console.warn('translate En→Hu failed, show English answer', err);
    }
    return {
      hungarianQuestion,
      englishQuestion,
      englishAnswer,
      hungarianAnswer,
      translateOk,
      debug: chat.debug || null,
    };
  }

  el.chatForm.addEventListener('submit', async (ev) => {
    ev.preventDefault();
    const q = el.question.value.trim();
    if (!q) return;

    saveUrl();
    el.question.value = '';
    el.btnSend.disabled = true;
    el.question.disabled = true;
    addMessage('user', q);
    addMessage('meta', 'Fordítás + Cloud Run…');

    try {
      const result = await ask(q);
      // Remove trailing meta spinner line
      const last = el.messages.lastElementChild;
      if (last && last.classList.contains('meta')) last.remove();

      if (!result.translateOk) {
        addMessage(
          'meta',
          'Megjegyzés: /v1/translate nem elérhető – redeploy-old a Cloud Run image-t a teljes Hu↔En pipeline-hoz.',
        );
      }
      addMessage('bot', result.hungarianAnswer);
      setDebug({
        hungarianQuestion: result.hungarianQuestion,
        englishQuestion: result.englishQuestion,
        englishAnswer: result.englishAnswer,
        hungarianAnswer: result.hungarianAnswer,
        translateOk: result.translateOk,
        serverDebug: result.debug,
      });
    } catch (err) {
      const last = el.messages.lastElementChild;
      if (last && last.classList.contains('meta')) last.remove();
      addMessage('bot', `Hiba: ${err.message || err}`);
      setDebug({ error: String(err) });
    } finally {
      el.btnSend.disabled = false;
      el.question.disabled = false;
      el.question.focus();
    }
  });

  el.btnPing.addEventListener('click', () => {
    ping().catch(() => {});
  });

  el.showDebug.addEventListener('change', () => {
    el.debugPanel.style.display = el.showDebug.checked ? '' : 'none';
  });

  el.question.addEventListener('keydown', (ev) => {
    if (ev.key === 'Enter' && !ev.shiftKey) {
      ev.preventDefault();
      el.chatForm.requestSubmit();
    }
  });

  // Boot
  const saved = localStorage.getItem(STORAGE_KEY);
  el.apiUrl.value =
    saved || window.LUMEEI_DEFAULT_API || 'https://example.invalid';
  addMessage(
    'meta',
    'Böngészős tesztelő. A kérdés magyarul megy → szerver fordítás → RAG/Qwen → magyar válasz.',
  );
  ping().catch(() => {});
})();
