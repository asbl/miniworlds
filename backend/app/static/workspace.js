/* Shared student workspace. The execution frame never receives credentials or API capabilities. */
(() => {
  "use strict";
  const $ = id => document.getElementById(id);
  const params = new URLSearchParams(location.search);
  const publicSlug = params.get("public"), teacherProject = params.get("teacher");
  const submissionId = params.get("submission"), submissionVersion = params.get("version");
  const preview = !!(publicSlug || teacherProject || submissionId);
  let project = null, token = sessionStorage.getItem("stoken"), dbData = null;
  let dirty = false, saving = null, saveTimer = null, conflict = false, recovering = false;
  let comparison = null;
  let loggingOut = false;
  let frame = null, channel = null, generation = 0, running = false;
  let runtimeFiles = null, runtimeSource = null, runtimeEpoch = 0;
  const taskTimers = new Map(), pendingAnswers = new Map(), taskEditors = new Map();
  const esc = s => String(s ?? "").replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
  const message = (s, error = false) => { $("workspace-status").textContent = s; $("workspace-status").classList.toggle("error", error); };
  const bytes = n => (n / 1048576).toFixed(1) + " MB";
  const draftKey = () => "miniworlds-draft:" + project.project_id;
  const answersKey = id => "miniworlds-answers:" + project.project_id + ":" + id;
  const guarded = fn => async event => { if (event) event.preventDefault(); try { await fn(event); } catch (error) { message(error.message, true); } };

  async function api(path, options = {}) {
    const headers = { ...(options.body instanceof FormData ? {} : {"Content-Type":"application/json"}), ...(options.headers || {}) };
    if (token && path.startsWith("/api/play")) headers.Authorization = "Bearer " + token;
    if (sessionStorage.getItem("csrf")) headers["X-CSRF-Token"] = sessionStorage.getItem("csrf");
    let response;
    try { response = await fetch(path, {...options, headers}); }
    catch (_) { throw new Error("Keine Verbindung. Dein Entwurf bleibt in diesem Tab erhalten."); }
    if (!response.ok) {
      const body = await response.json().catch(() => ({}));
      const error = new Error(typeof body.detail === "string" ? body.detail : "Die Aktion konnte nicht ausgeführt werden (" + response.status + ").");
      error.status = response.status;
      throw error;
    }
    return response;
  }
  const json = async (path, options) => (await api(path, options)).json();
  const write = (path, method, body) => json(path, {method, body: JSON.stringify(body)});

  function persistDraft() {
    if (!project || preview || !dirty) return;
    try { sessionStorage.setItem(draftKey(), JSON.stringify({source: $("source").value, db: dbData, revision: project.revision})); }
    catch (_) { message("Der lokale Entwurf konnte nicht gesichert werden. Bitte den Code herunterladen.", true); }
  }
  function highlight() {
    const code = $("source").value;
    const pattern = /#[^\n]*|(?:"(?:\\.|[^"\\])*"|'(?:\\.|[^'\\])*')|\b(?:False|None|True|and|as|assert|async|await|break|class|continue|def|del|elif|else|except|finally|for|from|global|if|import|in|is|lambda|nonlocal|not|or|pass|raise|return|try|while|with|yield)\b|\b\d+(?:\.\d+)?\b/g;
    let html = "", end = 0;
    for (const match of code.matchAll(pattern)) {
      const text = match[0], kind = text.startsWith("#") ? "comment" : /^["']/.test(text) ? "string" : /^\d/.test(text) ? "number" : "keyword";
      html += esc(code.slice(end, match.index)) + '<span class="py-' + kind + '">' + esc(text) + '</span>';
      end = match.index + text.length;
    }
    $("source-highlight").querySelector("code").innerHTML = html + esc(code.slice(end)) + "\n";
    $("source-highlight").scrollTop = $("source").scrollTop;
    $("source-highlight").scrollLeft = $("source").scrollLeft;
  }
  function changed() {
    highlight();
    if (preview || project?.read_only) return;
    dirty = true; generation++; persistDraft();
    $("save-state").textContent = "Ungespeicherte Änderungen · lokal gesichert";
    clearTimeout(saveTimer);
    saveTimer = setTimeout(() => save().catch(error => message(error.message, true)), 1500);
  }
  async function save() {
    if (saving) { await saving; return save(); }
    if (!project || preview || project.read_only) return !dirty;
    if (conflict || recovering) return false;
    if (!dirty) return true;
    const sentGeneration = generation;
    const payload = {source: $("source").value, db: dbData, base_revision: project.revision, message: $("commit-msg").value || null};
    $("save-state").textContent = "Speichert…";
    saving = (async () => {
      try {
        const result = await write("/api/play/save", "PUT", payload);
        project.revision = result.revision;
        project.save = {source: payload.source, db: payload.db};
        $("storage").textContent = bytes(result.used_bytes) + " von " + bytes(result.quota_bytes);
        if (result.warning) message(result.warning, true);
        if (generation === sentGeneration) {
          dirty = false; sessionStorage.removeItem(draftKey());
          $("save-state").textContent = "Gespeichert · " + new Date().toLocaleTimeString("de-DE");
          $("commit-msg").value = "";
        } else { persistDraft(); $("save-state").textContent = "Weitere Änderungen lokal gesichert"; }
        return true;
      } catch (error) {
        persistDraft(); $("save-state").textContent = "Noch nicht gespeichert · Entwurf lokal erhalten";
        if (error.status === 409) { conflict = true; $("conflict").classList.remove("hidden"); }
        message(error.message, true);
        return false;
      }
    })();
    try { return await saving; } finally { saving = null; }
  }
  async function compareConflict() {
    persistDraft();
    const latest = await json("/api/play/project");
    comparison = {revision:latest.revision, db:latest.save?.db ?? null, read_only:latest.read_only};
    $("comparison-local").value = $("source").value;
    $("comparison-server").value = latest.save?.source ?? "";
    $("comparison-database").classList.toggle("hidden", dbData === comparison.db);
    document.querySelector('input[name="comparison-db"][value="local"]').checked = true;
    $("comparison-status").textContent = latest.read_only ? latest.read_only_reason : "Serverstand geladen. Änderungen in anderen Tabs werden beim Speichern erneut geprüft.";
    $("comparison-save").disabled = latest.read_only;
    if (!$("conflict-comparison").open) $("conflict-comparison").showModal();
  }
  async function saveComparison() {
    if (!comparison || comparison.read_only) return;
    $("comparison-save").disabled = true;
    try {
      $("source").value = $("comparison-local").value;
      if (document.querySelector('input[name="comparison-db"]:checked').value === "server") dbData = comparison.db;
      project.revision = comparison.revision;
      conflict = false; recovering = false; dirty = true; generation++;
      highlight(); persistDraft();
      if (await save()) {
        $("conflict-comparison").close(); $("conflict").classList.add("hidden"); $("recovery").classList.add("hidden");
        message("Dein bearbeiteter Entwurf wurde gespeichert.");
      } else {
        const reason = $("workspace-status").textContent;
        conflict = true;
        $("conflict").classList.remove("hidden");
        await compareConflict();
        $("comparison-status").textContent = reason + " Dein Entwurf bleibt erhalten; der Serverstand wurde erneut geladen. Bitte nochmals vergleichen.";
      }
    } finally { $("comparison-save").disabled = !!comparison?.read_only; }
  }
  function stop() {
    runtimeEpoch++;
    channel?.port1.close(); channel?.port2.close(); channel = null;
    frame?.remove(); frame = null;
    running = false;
    $("run-btn").disabled = false; $("stop-btn").disabled = true;
    $("player-status").textContent = "Gestoppt. Beim nächsten Start wird die Laufzeit neu geladen.";
  }
  async function mediaFiles() {
    if (runtimeFiles) return runtimeFiles;
    const files = [];
    for (const asset of project.media || []) {
      let buffer;
      if (asset.content != null) buffer = Uint8Array.from(atob(asset.content), c => c.charCodeAt(0)).buffer;
      else {
        const url = publicSlug ? "/api/public/" + encodeURIComponent(publicSlug) + "/media/" + asset.asset_id : "/api/play/media/" + asset.id + "/file";
        // Teacher previews obtain a complete snapshot from their own authenticated API.
        buffer = await (await api(url)).arrayBuffer();
      }
      files.push({name: asset.filename || (asset.orig_name || "file").replace(/[^\w.\-]/g, "_"), content: buffer});
    }
    runtimeFiles = files;
    return files;
  }
  async function run() {
    if (running) return;
    const epoch = runtimeEpoch;
    running = true; $("run-btn").disabled = true; $("stop-btn").disabled = false;
    $("output").textContent = ""; $("player-status").textContent = "Laufzeit wird geladen…";
    try {
      const cfg = await json("/api/player/config");
      if (!cfg.wheel_available) throw new Error("Die Laufzeit ist auf dem Server noch nicht eingerichtet.");
      const [wheel, files, worker, audioCode] = await Promise.all([
        (await api(cfg.wheel_url)).arrayBuffer(), mediaFiles(),
        runtimeSource ? Promise.resolve(runtimeSource) : (await api("/static/runner-worker.js")).text(),
        (await api("/static/runner-audio.py")).text()
      ]);
      runtimeSource = worker;
      if (!running || epoch !== runtimeEpoch) return;
      const source = $("source").value;
      frame = document.createElement("iframe"); frame.title = "Programmausgabe";
      frame.setAttribute("sandbox", "allow-scripts"); frame.setAttribute("allow", "autoplay"); frame.src = "/runner";
      const activeFrame = frame;
      channel = new MessageChannel();
      channel.port1.onmessage = event => {
        if (activeFrame !== frame || !event.data || typeof event.data !== "object") return;
        const data = event.data;
        if (data.type === "output" && typeof data.text === "string") {
          $("output").textContent = ($("output").textContent + data.text.slice(0, 10000) + "\n").slice(-64000);
        } else if (data.type === "status" && typeof data.text === "string") {
          $("player-status").textContent = data.text.slice(0, 500);
        } else if (data.type === "done" || data.type === "error") {
          running = false; $("run-btn").disabled = false; $("stop-btn").disabled = false;
          if (data.type === "error") {
            $("output").textContent = String(data.text || "Unbekannter Fehler").slice(0, 64000);
            $("player-status").textContent = "Fehler im Programm. Die letzte Zeile der Ausgabe beschreibt die Ursache.";
            const line = String(data.text).match(/File ["'](?:\/project\/)?main.py["'], line (\d+)/);
            if (line) $("player-status").textContent += " Prüfe Zeile " + line[1] + ".";
          }
        } else if (data.type === "database" && !preview && typeof data.content === "string" && data.content.length <= project.quota_bytes * 2) {
          if (data.content !== dbData) { dbData = data.content || null; changed(); }
        }
      };
      frame.addEventListener("load", () => {
        if (activeFrame !== frame) return;
        activeFrame.contentWindow.postMessage({type:"init", worker, config:cfg, source, db:dbData, files, wheel, audioCode}, "*", [channel.port2]);
      }, {once:true});
      $("runner-host").replaceChildren(frame);
    } catch (error) { stop(); throw error; }
  }
  async function startFresh() { stop(); await run(); }

  function downloadBlob(blob, filename) {
    const url = URL.createObjectURL(blob), link = document.createElement("a");
    link.href = url; link.download = filename; link.click(); setTimeout(() => URL.revokeObjectURL(url), 1000);
  }
  async function downloadProject() {
    if (dirty && !await save()) throw new Error("Bitte zuerst den Speicherkonflikt lösen. Den lokalen Code kannst du gesondert herunterladen.");
    const url = submissionId ? `/api/teacher/submissions/${encodeURIComponent(submissionId)}/versions/${encodeURIComponent(submissionVersion)}/download` : teacherProject ? `/api/teacher/projects/${encodeURIComponent(teacherProject)}/download` : "/api/play/download";
    if (publicSlug) { downloadBlob(new Blob([$("source").value], {type:"text/x-python"}), "main.py"); return; }
    downloadBlob(await (await api(url)).blob(), submissionId ? "abgabe.zip" : "miniworlds-projekt.zip");
  }
  function taskStatus(task) { return task.status === "submitted" ? "Abgegeben" : task.submitted_at ? "Zur Überarbeitung geöffnet" : "In Bearbeitung"; }
  function renderTasks() {
    taskEditors.clear();
    $("tasks").replaceChildren();
    if (!project.tasks?.length) $("tasks").textContent = "Keine Aufgaben zugewiesen.";
    for (const task of project.tasks || []) {
      const card = document.createElement("article"); card.className = "task-card";
      card.innerHTML = `<h4>${esc(task.title)}</h4><p class="task-description">${esc(task.description)}</p><p class="task-status">${esc(taskStatus(task))}</p>`;
      const answerCache = sessionStorage.getItem(answersKey(task.assignment_id));
      let answers = task.answers || {};
      if (answerCache && task.status !== "submitted" && !project.read_only) {
        try { answers = JSON.parse(answerCache); } catch (_) { /* malformed local data */ }
      }
      for (const item of task.items) {
        const label = document.createElement(item.kind === "checkbox" ? "label" : "p");
        if (item.kind !== "checkbox") label.textContent = item.prompt;
        else {
          const input = document.createElement("input");
          input.type = "checkbox"; input.checked = answers[item.id]?.checked === true;
          input.dataset.item = item.id;
          input.disabled = project.read_only || task.status === "submitted";
          label.append(document.createTextNode(item.prompt + " "), input);
          input.addEventListener("input", () => {
            sessionStorage.setItem(answersKey(task.assignment_id), JSON.stringify(collectAnswers(card)));
            clearTimeout(taskTimers.get(task.assignment_id));
            taskTimers.set(task.assignment_id, setTimeout(() => { taskTimers.delete(task.assignment_id); saveAnswers(task, card).catch(e => message(e.message, true)); }, 1200));
          });
        }
        card.append(label);
      }
      if (!preview && !project.read_only && task.status !== "submitted") {
        const submit = document.createElement("button"); submit.textContent = "Projekt und Antworten abgeben";
        submit.addEventListener("click", guarded(async () => {
          submit.disabled = true;
          try {
            clearTimeout(taskTimers.get(task.assignment_id)); taskTimers.delete(task.assignment_id);
            if (!await save()) throw new Error("Der Programmstand konnte noch nicht gespeichert werden.");
            await saveAnswers(task, card);
            const result = await write(`/api/play/tasks/${task.assignment_id}/submit?base_revision=${project.revision}`, "POST", {});
            sessionStorage.removeItem(answersKey(task.assignment_id));
            task.status = result.status; task.submitted_at = result.submitted_at;
            renderTasks(); message("Abgegeben. Programm, Medien und Aufgaben wurden als fester Stand gesichert.");
          } finally { submit.disabled = false; }
        }));
        card.append(submit);
      }
      $("tasks").append(card);
      taskEditors.set(task.assignment_id, {task, card});
    }
  }
  function collectAnswers(card) {
    const answers = {};
    card.querySelectorAll("input[type=checkbox][data-item]").forEach(input => { answers[input.dataset.item] = {checked:input.checked}; });
    return answers;
  }
  async function saveAnswers(task, card) {
    const id = task.assignment_id;
    if (pendingAnswers.has(id)) await pendingAnswers.get(id);
    const answers = collectAnswers(card);
    const promise = write(`/api/play/tasks/${id}/answers`, "PUT", {answers, base_version: task.version || 0});
    pendingAnswers.set(id, promise);
    try {
      const result = await promise; task.version = result.version;
      if (JSON.stringify(collectAnswers(card)) === JSON.stringify(answers)) sessionStorage.removeItem(answersKey(id));
    } finally { pendingAnswers.delete(id); }
  }
  function renderMedia() {
    $("media-list").replaceChildren();
    for (const asset of project.media || []) {
      const row = document.createElement("p");
      const open = document.createElement("button"); open.className = "secondary";
      open.textContent = asset.filename || asset.orig_name;
      open.addEventListener("click", guarded(async () => {
        const files = await mediaFiles(), file = files.find(f => f.name === (asset.filename || asset.orig_name.replace(/[^\w.\-]/g, "_")));
        downloadBlob(new Blob([file.content], {type:asset.mime}), asset.filename || asset.orig_name);
      }));
      row.append(open, document.createTextNode(" · " + asset.license + (asset.source ? " · " + asset.source : "")));
      if (!preview && !project.read_only) {
        const edit = document.createElement("details");
        edit.innerHTML = '<summary>Lizenz/Quelle bearbeiten</summary><form><label>Lizenz <select name="license"></select></label><label>Lizenzangabe <input name="license_text" maxlength="2000"></label><label>Quelle <input name="source" maxlength="2000"></label><button>Angaben speichern</button></form>';
        const form = edit.querySelector("form");
        form.elements.license.replaceChildren(...(project.license_choices || []).map(value => new Option(value, value)));
        form.elements.license.value = asset.license;
        form.elements.license_text.value = asset.license_text || "";
        form.elements.source.value = asset.source || "";
        form.addEventListener("submit", guarded(async () => {
          await write("/api/play/media/" + asset.id, "PATCH", {license:form.elements.license.value, license_text:form.elements.license_text.value, source:form.elements.source.value});
          await refreshMedia(); message("Lizenzangaben gespeichert.");
        })); row.append(edit);
        const del = document.createElement("button"); del.className = "danger"; del.textContent = "Entfernen";
        del.addEventListener("click", guarded(async () => {
          if (!confirm("Datei entfernen? Ältere Abgaben behalten ihre Kopie.")) return;
          await api("/api/play/media/" + asset.id, {method:"DELETE"}); await refreshMedia();
        })); row.append(del);
      }
      $("media-list").append(row);
    }
  }
  async function refreshMedia() {
    // Never reload the editor when media change.
    const result = await json("/api/play/media"); project.media = result.media; runtimeFiles = null; renderMedia();
  }
  async function load() {
    stop(); clearTimeout(saveTimer); conflict = false; dirty = false; recovering = false;
    taskTimers.forEach(clearTimeout); taskTimers.clear();
    $("conflict").classList.add("hidden"); $("recovery").classList.add("hidden");
    if (submissionId) {
      const result = await json(`/api/teacher/submissions/${encodeURIComponent(submissionId)}/versions/${encodeURIComponent(submissionVersion)}`);
      project = {...result.snapshot, project_id:result.snapshot.project_id, tasks:[{...result.snapshot.task, answers:result.answers, status:"submitted", assignment_id:0}]};
    } else if (teacherProject) {
      const result = await json(`/api/teacher/projects/${encodeURIComponent(teacherProject)}/snapshot`); project = {...result.snapshot, project_id:result.snapshot.project_id};
    } else if (publicSlug) project = await json("/api/public/" + encodeURIComponent(publicSlug));
    else project = await json("/api/play/project");
    project.read_only = preview || project.read_only;
    runtimeFiles = null; dbData = project.save?.db || null;
    $("source").value = project.save?.source ?? (preview ? "" : "from miniworlds import *\n\nworld = World()\nworld.run()\n");
    $("source").readOnly = !!project.read_only;
    $("project-title").textContent = project.title || "miniworlds Projekt";
    $("storage").textContent = preview ? "Vorschau" : bytes(project.used_bytes) + " von " + bytes(project.quota_bytes);
    $("submission-policy").textContent = project.storage_policy ? `Es bleiben bis zu ${project.storage_policy.submission_max_versions} eingereichte Fassungen je Aufgabe erhalten. Bei vollem Archivspeicher werden ältere Fassungen entfernt; die letzte Abgabe jeder Aufgabe bleibt erhalten.` : "";
    $("save-state").textContent = "Geladen";
    $("entry").classList.add("hidden"); $("workspace").classList.remove("hidden");
    $("read-only-notice").classList.toggle("hidden", !project.read_only);
    $("read-only-notice").textContent = preview ? "Vorschau: Änderungen werden nicht gespeichert." : project.read_only_reason;
    for (const id of ["save-btn", "new-project", "share-btn", "clear-history"]) $(id).disabled = project.read_only;
    $("media-form").classList.toggle("hidden", project.read_only);
    $("advanced").classList.toggle("hidden", preview); $("sharing").classList.toggle("hidden", preview);
    $("refresh-tasks").classList.toggle("hidden", preview);
    $("project-picker-label").classList.toggle("hidden", preview); $("new-project").classList.toggle("hidden", preview);
    for (const id of ["remote-url", "remote-token", "remote-pull"]) $(id).disabled = project.read_only;
    $("remote-form").querySelector("button[type=submit]").disabled = project.read_only;
    $("license-select").replaceChildren(...(project.license_choices || []).map(value => new Option(value, value)));
    highlight(); renderTasks(); renderMedia();
    if (!preview) {
      const choices = await json("/api/play/projects");
      $("project-picker").replaceChildren(...choices.projects.map(p => new Option(p.title + (p.read_only ? " (nur lesen)" : ""), p.id)));
      $("project-picker").value = project.project_id;
      const draft = sessionStorage.getItem(draftKey());
      if (draft) {
        try {
          const data = JSON.parse(draft);
          if (data.source !== $("source").value || data.db !== dbData) { recovering = true; $("recovery").classList.remove("hidden"); }
          else sessionStorage.removeItem(draftKey());
        } catch (_) { sessionStorage.removeItem(draftKey()); }
      }
      if (!project.save && !recovering && !project.read_only) changed();
      $("share-status").textContent = project.share ? "Status: " + project.share.status + (project.share.slug ? " · /p/" + project.share.slug : "") : "Noch nicht veröffentlicht.";
    }
  }
  async function flush() {
    for (const {task, card} of taskEditors.values()) {
      if (sessionStorage.getItem(answersKey(task.assignment_id)) && !project.read_only && task.status !== "submitted") {
        clearTimeout(taskTimers.get(task.assignment_id)); taskTimers.delete(task.assignment_id);
        await saveAnswers(task, card);
      }
    }
    if (dirty && !await save()) throw new Error("Bitte den Entwurf zuerst speichern oder herunterladen.");
    if (recovering) throw new Error("Bitte den lokalen Entwurf zuerst wiederherstellen oder verwerfen.");
  }
  window.miniworldsBeforeLogout = async () => {
    if (!project || preview) return;
    try { await flush(); }
    catch (error) {
      if (!confirm(error.message + " Trotzdem abmelden und ungespeicherte Entwürfe auf diesem Gerät verwerfen?")) throw error;
    }
  };
  window.addEventListener("miniworlds:logout", () => { loggingOut = true; clearTimeout(saveTimer); taskTimers.forEach(clearTimeout); });
  $("claim-form").addEventListener("submit", guarded(async ev => {
    const result = await write("/api/claim", "POST", {code:ev.target.code.value});
    token = result.token; sessionStorage.setItem("stoken", token); message(""); await load();
  }));
  $("source").addEventListener("input", changed);
  $("source").addEventListener("scroll", highlight);
  $("source").addEventListener("keydown", event => {
    if (event.key !== "Tab" || $("source").readOnly) return;
    event.preventDefault(); const input = event.target; input.setRangeText("    ", input.selectionStart, input.selectionEnd, "end"); changed();
  });
  $("refresh-tasks").addEventListener("click", guarded(async () => {
    const result = await json("/api/play/project");
    for (const task of result.tasks) {
      const local = taskEditors.get(task.assignment_id);
      if (local && sessionStorage.getItem(answersKey(task.assignment_id))) task.version = local.task.version;
    }
    project.tasks = result.tasks;
    renderTasks(); message("Aufgaben aktualisiert. Dein Programm bleibt erhalten.");
  }));
  $("download-source").addEventListener("click", () => downloadBlob(new Blob([$("source").value], {type:"text/x-python"}), "main.py"));
  $("save-btn").addEventListener("click", guarded(save));
  $("run-btn").addEventListener("click", guarded(startFresh)); $("stop-btn").addEventListener("click", stop);
  $("download-project").addEventListener("click", guarded(downloadProject));
  $("download-draft").addEventListener("click", () => downloadBlob(new Blob([$("source").value], {type:"text/x-python"}), "mein-entwurf.py"));
  $("compare-conflict").addEventListener("click", guarded(compareConflict));
  $("comparison-save").addEventListener("click", guarded(saveComparison));
  $("comparison-cancel").addEventListener("click", () => $("conflict-comparison").close());
  $("comparison-use-server").addEventListener("click", guarded(async () => {
    await load();
    sessionStorage.removeItem(draftKey()); recovering = false;
    $("recovery").classList.add("hidden"); $("conflict-comparison").close();
    message("Serverstand übernommen.");
  }));
  $("reload-project").addEventListener("click", guarded(async () => {
    if (!confirm("Serverstand laden? Der lokale Entwurf bleibt für die Wiederherstellung erhalten.")) return; await load();
  }));
  $("restore-draft").addEventListener("click", guarded(async () => {
    const draft = JSON.parse(sessionStorage.getItem(draftKey()));
    $("source").value = draft.source; dbData = draft.db; recovering = false;
    $("recovery").classList.add("hidden");
    if (draft.revision !== project.revision) {
      conflict = true; $("conflict").classList.remove("hidden");
      message("Der Entwurf basiert auf einem älteren Stand. Über „Stände vergleichen“ kannst du ihn mit dem Serverstand zusammenführen.", true);
    }
    changed();
  }));
  $("discard-draft").addEventListener("click", () => { sessionStorage.removeItem(draftKey()); recovering = false; $("recovery").classList.add("hidden"); });
  $("project-picker").addEventListener("change", guarded(async event => {
    const id = event.target.value;
    try { await flush(); } catch (error) { event.target.value = project.project_id; throw error; }
    const result = await write(`/api/play/projects/${id}/open`, "POST", {});
    token = result.token; sessionStorage.setItem("stoken", token); await load();
  }));
  $("new-project").addEventListener("click", guarded(async () => {
    await flush(); const title = prompt("Projekttitel (bitte keine Personennamen):", "Neues Projekt"); if (!title?.trim()) return;
    const result = await write("/api/play/projects", "POST", {title:title.trim()});
    token = result.token; sessionStorage.setItem("stoken", token); await load();
  }));
  $("media-form").addEventListener("submit", guarded(async event => {
    await api("/api/play/media", {method:"POST", body:new FormData(event.target)});
    event.target.reset(); await refreshMedia(); message("Medium hochgeladen. Dein Code bleibt erhalten.");
  }));
  $("share-btn").addEventListener("click", guarded(async () => {
    await flush(); await write("/api/play/share-request", "POST", {declaration_accepted:$("share-declaration").checked});
    $("share-status").textContent = "Freigabe beantragt.";
  }));
  $("history-btn").addEventListener("click", guarded(async () => {
    const result = await json("/api/play/history"); $("history-list").replaceChildren();
    if (!result.available) { message("Der Versionsverlauf ist auf dem Server nicht verfügbar."); return; }
    $("history-storage").textContent = bytes(result.used_bytes) + " von " + bytes(result.max_bytes) + (result.paused ? " · Verlauf pausiert. Dein aktuelles Projekt bleibt gespeichert." : "");
    for (const commit of result.commits) {
      const li = document.createElement("li"), diff = document.createElement("button"), restore = document.createElement("button");
      li.append(document.createTextNode(commit.date.slice(0,16).replace("T"," ") + " · " + commit.message + " "));
      diff.textContent = "Änderungen"; restore.textContent = "Wiederherstellen"; restore.disabled = project.read_only;
      diff.addEventListener("click", guarded(async () => { $("diff-view").textContent = (await json("/api/play/history/" + commit.hash)).show; }));
      restore.addEventListener("click", guarded(async () => {
        await flush(); if (!confirm("Diese Version wiederherstellen?")) return;
        await write(`/api/play/restore/${commit.hash}?base_revision=${project.revision}`, "POST", {}); await load();
      })); li.append(diff, restore); $("history-list").append(li);
    }
  }));
  $("download-history").addEventListener("click", guarded(async () => {
    downloadBlob(await (await api("/api/play/history/download")).blob(), "miniworlds-verlauf.bundle");
  }));
  $("clear-history").addEventListener("click", guarded(async () => {
    await flush();
    if (!confirm("Alle gespeicherten Git-Versionen endgültig löschen? Lade den Verlauf vorher herunter. Der aktuelle Programmstand, Medien und Abgaben bleiben erhalten.")) return;
    const result = await json(`/api/play/history?base_revision=${project.revision}`, {method:"DELETE"});
    project.revision = result.revision; $("history-list").replaceChildren(); $("history-storage").textContent = "Verlauf gelöscht. Neue Änderungen werden wieder versioniert.";
    message("Der Versionsverlauf wurde gelöscht. Dein aktuelles Projekt bleibt erhalten.");
  }));
  $("remote-form").addEventListener("submit", guarded(async () => {
    await write("/api/play/remote", "PUT", {url:$("remote-url").value, token:$("remote-token").value || null});
    $("remote-token").value = ""; message("Remote gesetzt.");
  }));
  $("remote-push").addEventListener("click", guarded(async () => { await flush(); await write("/api/play/push", "POST", {}); message("Gespeicherter Stand übertragen."); }));
  $("remote-pull").addEventListener("click", guarded(async () => {
    await flush(); if (!confirm("Stand vom Remote laden?")) return;
    await write(`/api/play/pull?base_revision=${project.revision}`, "POST", {}); await load();
  }));
  window.addEventListener("beforeunload", event => { if (loggingOut) return; persistDraft(); if (dirty || pendingAnswers.size || taskTimers.size || Object.keys(sessionStorage).some(key => key.startsWith("miniworlds-answers:"))) { event.preventDefault(); event.returnValue = ""; } });
  setInterval(() => { if (dirty && !conflict && !recovering) save(); }, 10000);
  if (token || preview) load().catch(error => message(error.message, true));
})();
