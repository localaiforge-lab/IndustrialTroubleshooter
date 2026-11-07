(() => {
  const el = {
    banner: document.getElementById("banner"),
    answerMode: document.getElementById("answerMode"),
    statDocs: document.getElementById("statDocs"),
    statParts: document.getElementById("statParts"),
    statCodes: document.getElementById("statCodes"),
    tabWork: document.getElementById("tabWork"),
    tabOverview: document.getElementById("tabOverview"),
    work: document.getElementById("work"),
    overview: document.getElementById("overview"),
    library: document.getElementById("library"),
    uploadCard: document.getElementById("uploadCard"),
    askCard: document.getElementById("askCard"),
    uploadStep: document.getElementById("uploadStep"),
    askStep: document.getElementById("askStep"),
    area: document.getElementById("area"),
    drop: document.getElementById("drop"),
    browse: document.getElementById("browse"),
    file: document.getElementById("file"),
    uploadOut: document.getElementById("uploadOut"),
    askForm: document.getElementById("askForm"),
    question: document.getElementById("question"),
    askBtn: document.getElementById("askBtn"),
    answer: document.getElementById("answer"),
  };

  let libraryCount = 0;
  let busy = false;

  function showBanner(text, kind) {
    if (!text) {
      el.banner.hidden = true;
      el.banner.textContent = "";
      el.banner.className = "banner";
      return;
    }
    el.banner.hidden = false;
    el.banner.className = `banner ${kind || ""}`.trim();
    el.banner.textContent = text;
  }

  async function api(path, options = {}) {
    let response;
    try {
      response = await fetch(path, options);
    } catch {
      throw new Error("Nem érem el a szervert. Nyissa meg az oldal a hibakereső címéről.");
    }
    const text = await response.text();
    let body = null;
    try {
      body = text ? JSON.parse(text) : null;
    } catch {
      body = null;
    }
    if (!response.ok) {
      const detail = body && body.detail;
      throw new Error(typeof detail === "string" ? detail : "A művelet nem sikerült.");
    }
    return body;
  }

  function paintStats(summary) {
    libraryCount = summary.documents || 0;
    el.statDocs.textContent = String(libraryCount);
    el.statParts.textContent = String(summary.passages || 0);
    el.statCodes.textContent = String(summary.faultCodes || 0);
    const hasDocs = libraryCount > 0;
    el.uploadCard.style.order = hasDocs ? "2" : "1";
    el.askCard.style.order = hasDocs ? "1" : "2";
    el.uploadStep.textContent = hasDocs ? "2" : "1";
    el.askStep.textContent = hasDocs ? "1" : "2";
    el.askBtn.disabled = busy || !hasDocs;
    if (!busy) {
      el.askBtn.textContent = hasDocs
        ? "Válasz a dokumentumokból"
        : "Először töltsön fel dokumentumot";
    }
    if (summary.answerMode === "model") {
      el.answerMode.textContent = "A választ a dokumentumok alapján fogalmazzuk";
    } else if (summary.answerMode) {
      el.answerMode.textContent = "A választ a dokumentumrészlet mutatja";
    }
  }

  function showWork() {
    el.tabWork.setAttribute("aria-selected", "true");
    el.tabOverview.setAttribute("aria-selected", "false");
    el.work.hidden = false;
    el.overview.hidden = true;
  }

  function showOverview() {
    el.tabWork.setAttribute("aria-selected", "false");
    el.tabOverview.setAttribute("aria-selected", "true");
    el.work.hidden = true;
    el.overview.hidden = false;
    loadLibrary();
  }

  function renderUpload(results) {
    el.uploadOut.replaceChildren();
    let added = 0;
    let rejected = 0;
    for (const item of results || []) {
      if (item.status === "added") added += 1;
      if (item.status === "rejected") rejected += 1;
      const box = document.createElement("article");
      box.className = `result ${item.status || ""}`;
      const title = document.createElement("strong");
      title.textContent = item.filename || "Fájl";
      const line = document.createElement("p");
      const bits = [item.message || ""];
      if (item.kindLabel) bits.push(item.kindLabel);
      if (item.sizeLabel) bits.push(item.sizeLabel);
      if (item.faultCodeCount) bits.push(`${item.faultCodeCount} hibakód`);
      line.textContent = bits.filter(Boolean).join(" · ");
      box.append(title, line);
      for (const warning of item.warnings || []) {
        const note = document.createElement("p");
        note.textContent = warning;
        box.append(note);
      }
      el.uploadOut.append(box);
    }
    if (added && !rejected) {
      showBanner(`${added} dokumentum bekerült a tudástárba. Lent már lehet kérdezni.`, "ok");
    } else if (added && rejected) {
      showBanner(`${added} dokumentum bekerült, ${rejected} kimaradt. A piros soroknál ott a teendő.`, "");
    } else if (rejected) {
      showBanner("Egyik fájl sem került be. A piros sor mondja, mit kell máshogy menteni.", "bad");
    }
  }

  function renderAnswer(data) {
    el.answer.hidden = false;
    el.answer.replaceChildren();
    const text = document.createElement("pre");
    text.textContent = data.answer || "";
    el.answer.append(text);
    const sources = data.sources || [];
    if (!sources.length) return;
    const list = document.createElement("div");
    list.className = "sources";
    const heading = document.createElement("p");
    heading.className = "hint";
    heading.textContent = "Forrás a tudástárban";
    list.append(heading);
    sources.forEach((source, index) => {
      const details = document.createElement("details");
      details.open = data.mode === "model" && index === 0;
      const summary = document.createElement("summary");
      summary.textContent = source.location || source.filename || "Dokumentum";
      const excerpt = document.createElement("p");
      excerpt.textContent = source.excerpt || "";
      details.append(summary, excerpt);
      list.append(details);
    });
    el.answer.append(list);
  }

  function renderLibrary(documents) {
    el.library.replaceChildren();
    if (!documents.length) {
      const empty = document.createElement("p");
      empty.className = "empty";
      empty.textContent = "Még nincs dokumentum. A Hibakeresés lapon lehet feltölteni.";
      el.library.append(empty);
      return;
    }
    const list = document.createElement("div");
    list.className = "docs";
    for (const doc of documents) {
      const row = document.createElement("article");
      row.className = "doc";
      const info = document.createElement("div");
      const title = document.createElement("h3");
      title.textContent = doc.filename || doc.title || "Dokumentum";
      const meta = document.createElement("p");
      const when = doc.uploadedAt ? new Date(doc.uploadedAt).toLocaleString("hu-HU") : "";
      const codes = doc.faultCodeCount ? `${doc.faultCodeCount} hibakód` : "szöveges leírás";
      meta.textContent = [doc.kindLabel, doc.sizeLabel, doc.area, codes, when].filter(Boolean).join(" · ");
      info.append(title, meta);
      if ((doc.warnings || []).length) {
        const warn = document.createElement("p");
        warn.textContent = doc.warnings.join(" ");
        info.append(warn);
      }
      const remove = document.createElement("button");
      remove.type = "button";
      remove.className = "ghost";
      remove.textContent = "Törlés";
      remove.addEventListener("click", () => removeDoc(doc));
      row.append(info, remove);
      list.append(row);
    }
    el.library.append(list);
  }

  async function refresh() {
    const summary = await api("/v1/plant/status");
    paintStats(summary);
  }

  async function loadLibrary() {
    const data = await api("/v1/plant/documents");
    renderLibrary(data.documents || []);
  }

  async function removeDoc(doc) {
    const name = doc.filename || "ezt a dokumentumot";
    if (!window.confirm(`Törli a tudástárból: ${name}? Utána a hibakeresés már nem használja.`)) {
      return;
    }
    try {
      const data = await api(`/v1/plant/documents/${doc.id}`, { method: "DELETE" });
      paintStats({ ...data.library, answerMode: el.answerMode.textContent.includes("fogalmaz") ? "model" : "documents" });
      await loadLibrary();
      showBanner("A dokumentum kikerült a tudástárból.", "ok");
    } catch (error) {
      showBanner(error.message, "bad");
    }
  }

  async function filesFromEntry(entry) {
    if (entry.isFile) {
      const file = await new Promise((resolve, reject) => entry.file(resolve, reject));
      return [file];
    }
    if (!entry.isDirectory) return [];
    const reader = entry.createReader();
    const nested = [];
    const readBatch = () =>
      new Promise((resolve, reject) => reader.readEntries(resolve, reject));
    let batch = await readBatch();
    while (batch.length) {
      for (const child of batch) nested.push(...(await filesFromEntry(child)));
      batch = await readBatch();
    }
    return nested;
  }

  async function filesFromList(fileList, dataTransfer) {
    if (dataTransfer && dataTransfer.items) {
      const collected = [];
      const entries = [];
      for (const item of dataTransfer.items) {
        if (item.kind !== "file") continue;
        const entry = item.webkitGetAsEntry ? item.webkitGetAsEntry() : null;
        if (entry) entries.push(entry);
      }
      if (entries.length) {
        for (const entry of entries) collected.push(...(await filesFromEntry(entry)));
        if (collected.length) return collected;
      }
    }
    return Array.from(fileList || []);
  }

  async function upload(files) {
    const list = Array.from(files || []).filter((file) => file && file.name);
    if (!list.length || busy) return;
    busy = true;
    el.drop.classList.add("busy");
    el.askBtn.disabled = true;
    showBanner(`${list.length} fájl feldolgozása. Nagy kézikönyvnél ez eltart egy percig.`, "");
    el.uploadOut.replaceChildren();
    try {
      const form = new FormData();
      for (const file of list) form.append("files", file, file.name);
      form.append("area", el.area.value.trim());
      const data = await api("/v1/plant/documents", { method: "POST", body: form });
      renderUpload(data.results || []);
      paintStats({ ...(data.library || {}), answerMode: (await api("/v1/plant/status")).answerMode });
      const added = (data.results || []).some((item) => item.status === "added");
      if (added) el.question.focus();
    } catch (error) {
      showBanner(error.message, "bad");
    } finally {
      busy = false;
      el.drop.classList.remove("busy");
      el.file.value = "";
      el.askBtn.disabled = libraryCount === 0;
      el.askBtn.textContent = libraryCount
        ? "Válasz a dokumentumokból"
        : "Először töltsön fel dokumentumot";
    }
  }

  async function ask(event) {
    event.preventDefault();
    const question = el.question.value.trim();
    if (!question || busy) return;
    if (!libraryCount) {
      showBanner("Először töltsön fel legalább egy dokumentumot. Enélkül nincs miből válaszolni.", "");
      return;
    }
    busy = true;
    el.askBtn.disabled = true;
    el.askBtn.textContent = "Keresés a dokumentumokban…";
    showBanner("", "");
    try {
      const data = await api("/v1/plant/ask", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question }),
      });
      renderAnswer(data);
    } catch (error) {
      showBanner(error.message, "bad");
    } finally {
      busy = false;
      el.askBtn.disabled = libraryCount === 0;
      el.askBtn.textContent = "Válasz a dokumentumokból";
    }
  }

  el.tabWork.addEventListener("click", showWork);
  el.tabOverview.addEventListener("click", showOverview);
  el.browse.addEventListener("click", () => el.file.click());
  el.file.addEventListener("change", () => upload(el.file.files));
  el.askForm.addEventListener("submit", ask);

  ["dragenter", "dragover"].forEach((name) => {
    el.drop.addEventListener(name, (event) => {
      event.preventDefault();
      el.drop.classList.add("over");
    });
  });
  el.drop.addEventListener("dragleave", () => el.drop.classList.remove("over"));
  el.drop.addEventListener("drop", async (event) => {
    event.preventDefault();
    el.drop.classList.remove("over");
    const files = await filesFromList(event.dataTransfer.files, event.dataTransfer);
    upload(files);
  });

  refresh().catch((error) => showBanner(error.message, "bad"));
})();
