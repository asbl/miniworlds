(() => {
  "use strict";
  const $ = id => document.getElementById(id);
  const esc = value => String(value ?? "").replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
  const status = text => { $("dashboard-status").textContent = text; };
  const guarded = fn => async event => {
    event?.preventDefault();
    try { await fn(event); } catch (error) { status(error.message); $("dashboard-status").classList.add("error"); }
  };
  let courses = [], projects = [], tasks = [], shares = [];
  let codeDefaultsLoaded = false;
  const nameMap = new Map(), workspaceNames = new Map();
  const fmtDate = value => value ? new Date(value).toLocaleString("de-DE") : "Noch nicht gespeichert";
  const courseName = id => courses.find(c => c.id === id)?.title || "Ohne Klasse";
  const personName = p => nameMap.get(p.code) || workspaceNames.get(p.workspace_id) || "";
  async function api(path, options = {}) {
    const response = await fetch(path, {...options, headers:{"Content-Type":"application/json", "X-CSRF-Token":sessionStorage.getItem("csrf") || "", ...(options.headers || {})}});
    const body = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(typeof body.detail === "string" ? body.detail : "Die Aktion ist fehlgeschlagen (" + response.status + ").");
    return body;
  }
  const write = (path, method, body) => api(path, {method, body:JSON.stringify(body)});
  function button(text, callback, className = "secondary") {
    const b = document.createElement("button"); b.type = "button"; b.textContent = text; b.className = className;
    b.addEventListener("click", guarded(callback)); return b;
  }
  function link(text, url) { const a = document.createElement("a"); a.textContent = text; a.href = url; a.target = "_blank"; a.rel = "noopener"; return a; }
  function populateCourses() {
    document.querySelectorAll(".course-picker").forEach(select => {
      const value = select.value;
      select.replaceChildren(new Option(select.dataset.all ? "Alle Klassen" : "Ohne Klasse", ""));
      courses.forEach(c => select.add(new Option(c.title + (c.school_year ? " · " + c.school_year : "") + (c.archived ? " (archiviert)" : ""), c.id)));
      if ([...select.options].some(o => o.value === value)) select.value = value;
    });
    $("courses-list").replaceChildren();
    for (const c of courses) {
      const row = document.createElement("p"); row.append(document.createTextNode(c.title + " · " + c.school_year + " · " + c.projects + " Projekte "));
      row.append(button(c.archived ? "Reaktivieren" : "Archivieren", async () => {
        if (!c.archived && !confirm("Klasse archivieren? Projekte bleiben lesbar und herunterladbar, Änderungen werden gesperrt.")) return;
        await write("/api/teacher/courses/" + c.id, "PATCH", {archived:!c.archived}); await refresh();
      })); $("courses-list").append(row);
    }
  }
  async function refresh() {
    const result = await Promise.all([api("/api/teacher/courses"), api("/api/teacher/projects" + (nameMap.size ? "?with_code=true" : "")), api("/api/teacher/tasks"), api("/api/teacher/share-requests")]);
    courses = result[0].courses; projects = result[1].projects; tasks = result[2].tasks; shares = result[3].requests;
    if (!codeDefaultsLoaded && result[1].code_defaults) {
      $("project-create-form").code_readonly_days.value=result[1].code_defaults.readonly_days;
      codeDefaultsLoaded=true;
    }
    const policy = result[1].storage_policy;
    $("archive-policy").textContent = policy ? `Archivspeicher pro Projekt: ${(policy.submission_max_bytes/1048576).toFixed(0)} MB, bis zu ${policy.submission_max_versions} eingereichte Fassungen je Aufgabe. Bei vollem Speicher werden ältere Fassungen entfernt; die letzte Abgabe jeder Aufgabe bleibt erhalten.` : "";
    const starter = $("starter-project"), selectedStarter = starter.value;
    starter.replaceChildren(new Option("Leeres Projekt", ""), ...projects.map(p => new Option(p.title + " #" + p.id, p.id)));
    if ([...starter.options].some(o => o.value === selectedStarter)) starter.value = selectedStarter;
    for (const p of projects) if (p.code && nameMap.has(p.code)) workspaceNames.set(p.workspace_id, nameMap.get(p.code));
    populateCourses(); renderProjects(); renderTasks(); renderShares();
  }
  function renderProjects() {
    const filter = $("project-filter-course").value, state = $("project-filter-state").value, query = $("project-search").value.trim().toLowerCase();
    const rows = projects.filter(p => (!filter || p.course_id === Number(filter)) && (!state || p.read_only === (state === "readonly")) && (!query || [p.id,p.title,personName(p)].join(" ").toLowerCase().includes(query)));
    const tbody = $("projects-table").querySelector("tbody"); tbody.replaceChildren();
    $("select-all-projects").checked = false;
    for (const p of rows) {
      const row = document.createElement("tr");
      row.innerHTML = `<td><input type="checkbox" class="project-select" value="${p.id}" aria-label="Projekt ${p.id} auswählen"></td><td>${esc(p.title)} <small>#${p.id}</small></td><td class="local-name">${esc(personName(p))}</td><td class="code-cell"></td><td>${esc(courseName(p.course_id))}</td><td>${(p.used_bytes/1048576).toFixed(1)} / ${(p.quota_bytes/1048576).toFixed(1)} MB</td><td>${p.read_only ? "Nur lesen" : "Bearbeitbar"}</td><td>${esc(fmtDate(p.last_save_at))}</td><td class="project-actions"></td>`;
      row.querySelector(".code-cell").append(button("Code anzeigen", async () => {
        const data = await api(`/api/teacher/projects/${p.id}/code`); p.code = data.code;
        row.querySelector(".code-cell").textContent = data.code;
        if (nameMap.has(data.code)) workspaceNames.set(p.workspace_id, nameMap.get(data.code));
        row.querySelector(".local-name").textContent = personName(p);
      }));
      const actions = row.querySelector(".project-actions");
      actions.append(button("Zugang einstellen", async () => editAccess(p)));
      if (p.password_protected) actions.append(button("Passwort zurücksetzen", async () => {
        if (!confirm("Schülerpasswort entfernen? Bestehende Sitzungen werden abgemeldet. Der Projektcode bleibt erhalten.")) return;
        await api(`/api/teacher/projects/${p.id}/password`, {method:"DELETE"}); await refresh();
      }));
      actions.append(link("Ansehen / Starten", "/player?teacher=" + p.id), document.createTextNode(" "), link("ZIP", `/api/teacher/projects/${p.id}/download`));
      const approved = shares.find(s => s.project_id === p.id && s.status === "approved");
      if (approved?.slug) actions.append(document.createTextNode(" "), link("Öffentlich", "/p/" + approved.slug));
      actions.append(button("Umbenennen", async () => {
        const title = prompt("Projekttitel (keine Personennamen):", p.title); if (!title?.trim()) return;
        await write(`/api/teacher/projects/${p.id}`, "PATCH", {title:title.trim()}); await refresh();
      }), button("Speicher ändern", async () => {
        const value = prompt("Speicherplatz in MB:", String(p.quota_bytes/1048576)); if (value === null) return;
        const amount = Number(value); if (!Number.isFinite(amount) || amount <= 0) throw new Error("Bitte eine positive Zahl eingeben.");
        await write(`/api/teacher/projects/${p.id}`, "PATCH", {quota_bytes:Math.round(amount*1048576)}); await refresh();
      }), button("Kopie starten", async () => {
        const copy = await write(`/api/teacher/projects/${p.id}/fork`, "POST", {});
        status("Kopie erstellt. Projekt-Code: " + copy.code); await refresh();
      }), button("Code erneuern", async () => {
        if (!confirm("Code erneuern? Der alte Code und zugehörige Zugangstokens werden ungültig.")) return;
        const result = await write(`/api/teacher/projects/${p.id}/regenerate-code`, "POST", {});
        status("Neuer Code: " + result.code); await refresh();
      }), button("Löschen", async () => {
        if (!confirm("Projekt samt Medien und Abgaben endgültig löschen?")) return;
        await api(`/api/teacher/projects/${p.id}`, {method:"DELETE"}); await refresh();
      }, "danger"));
      tbody.append(row);
    }
  }
  async function bulk(change) {
    const project_ids = [...document.querySelectorAll(".project-select:checked")].map(c => Number(c.value));
    if (!project_ids.length) throw new Error("Bitte zuerst Projekte auswählen.");
    await write("/api/teacher/projects/bulk", "PATCH", {project_ids, ...change}); await refresh();
  }
  function localDate(value) {
    if (!value) return "";
    const date = new Date(value); date.setMinutes(date.getMinutes()-date.getTimezoneOffset());
    return date.toISOString().slice(0,16);
  }
  async function editAccess(p) {
    const dialog = document.createElement("dialog"); dialog.className="panel";
    dialog.innerHTML=`<form><h3>Zugang einstellen · ${esc(p.title)}</h3>
      <label><input name="read_only" type="checkbox" ${p.manual_read_only ? "checked" : ""}> Jetzt schreibgeschützt</label>
      <label>Bearbeitbar bis (optional) <input name="writable_until" type="datetime-local" value="${localDate(p.writable_until)}"></label>
      <label>Code gültig nach Schreibschutz (Tage; leer = unbegrenzt) <input name="days" type="number" min="1" max="36500" value="${p.code_readonly_days ?? ""}"></label>
      <label>Festes Ablaufdatum (optional) <input name="expires" type="datetime-local" value="${localDate(p.code_expires_at)}"></label>
      <p>Das frühere Ablaufdatum gilt. Aktuell: ${esc(p.effective_code_expires_at ? fmtDate(p.effective_code_expires_at) : "kein festes Ablaufdatum")}.</p>
      <p>Archivierte Klassen sind ebenfalls schreibgeschützt. Nach der jährlichen Umstellung gilt dieselbe Zugangsfrist.</p>
      <p role="alert"></p><button>Speichern</button> <button type="button" data-cancel>Abbrechen</button></form>`;
    const close=()=>{dialog.close();dialog.remove();};
    dialog.querySelector("[data-cancel]").onclick=close;dialog.addEventListener("cancel",()=>dialog.remove());
    dialog.querySelector("form").addEventListener("submit",async event=>{
      event.preventDefault(); const f=event.target;
      try {
        await write(`/api/teacher/projects/${p.id}`,"PATCH",{read_only:f.read_only.checked,writable_until:f.writable_until.value ? new Date(f.writable_until.value).toISOString() : null,code_readonly_days:f.days.value ? Number(f.days.value) : null,code_expires_at:f.expires.value ? new Date(f.expires.value).toISOString() : null});
        close();await refresh();
      } catch(error) {dialog.querySelector('[role="alert"]').textContent=error.message;}
    });
    document.body.append(dialog);dialog.showModal();
  }
  async function renderTemplateCodes() {
    const {codes}=await api("/api/teacher/template-codes"), box=$("template-codes");box.replaceChildren();
    for(const code of codes) {
      const line=document.createElement("p");
      line.textContent=`${code.code} · Projekt #${code.project_id} · ${code.used_at ? "Eingelöst" : code.expires_at && new Date(code.expires_at)<new Date() ? "Abgelaufen" : "Noch verfügbar"}${code.expires_at ? " · gültig bis "+fmtDate(code.expires_at) : ""} `;
      line.append(button("Entfernen",async()=>{await api(`/api/teacher/template-codes/${code.id}`,{method:"DELETE"});await renderTemplateCodes();}));box.append(line);
    }
  }
  function renderTasks() {
    $("tasks-list").replaceChildren();
    const filter = $("task-filter-course").value;
    for (const task of tasks.filter(t => !filter || t.course_id === Number(filter))) {
      const card = document.createElement("article"); card.className = "task-card";
      card.innerHTML = `<h4>${esc(task.title)}</h4><p>${esc(courseName(task.course_id))} · ${task.assignments_count} Zuweisungen${task.is_template_for_new_projects ? " · automatisch für neue Projekte" : ""}</p><p class="task-description">${esc(task.description)}</p>`;
      const edit = document.createElement("details");
      edit.innerHTML = `<summary>Aufgabe bearbeiten</summary><form><label>Titel <input name="title" maxlength="255" required value="${esc(task.title)}"></label><label>Beschreibung <textarea name="description">${esc(task.description)}</textarea></label><label><input type="checkbox" name="template" ${task.is_template_for_new_projects ? "checked" : ""}> Künftigen Projekten automatisch zuweisen</label><button>Änderungen speichern</button></form>`;
      edit.querySelector("form").addEventListener("submit", guarded(async event => {
        const f = event.target;
        await write(`/api/teacher/tasks/${task.id}`, "PATCH", {title:f.elements.namedItem("title").value, description:f.description.value, is_template_for_new_projects:f.template.checked}); await refresh();
      })); card.append(edit);
      const list = document.createElement("ol");
      task.items.forEach((item, index) => {
        const li = document.createElement("li"); li.append(document.createTextNode(item.prompt + " (" + item.kind + ") "));
        li.append(button("Bearbeiten", async () => {
          const promptText = prompt("Aufgabentext:", item.prompt); if (promptText === null) return;
          await write(`/api/teacher/tasks/${task.id}/items/${item.id}`, "PATCH", {prompt:promptText}); await refresh();
        }));
        if (index > 0) li.append(button("Nach oben", async () => {
          // Rewrite every position to repair any gaps left by older clients.
          const order = [...task.items]; [order[index-1], order[index]] = [order[index], order[index-1]];
          for (let n=0;n<order.length;n++) await write(`/api/teacher/tasks/${task.id}/items/${order[n].id}`, "PATCH", {position:n});
          await refresh();
        }));
        li.append(button("Entfernen", async () => { if (!confirm("Aufgabenteil entfernen? Vorhandene Abgaben behalten ihre Aufgabenfassung.")) return; await api(`/api/teacher/tasks/${task.id}/items/${item.id}`,{method:"DELETE"}); await refresh(); }, "danger"));
        list.append(li);
      }); card.append(list);
      const add = document.createElement("form");
      add.innerHTML = '<label>Aufgabentyp <select name="kind"><option value="text">Information</option><option value="checkbox">Checkbox</option></select></label><label>Text <input name="prompt" required></label><button>Aufgabenteil hinzufügen</button>';
      add.addEventListener("submit", guarded(async event => {
        await write(`/api/teacher/tasks/${task.id}/items`, "POST", {kind:event.target.kind.value, prompt:event.target.prompt.value}); await refresh();
      })); card.append(add);
      const controls = document.createElement("div"); controls.className = "task-controls";
      controls.append(button(task.course_id ? "Klasse inkl. künftiger Projekte zuweisen" : "Allen inkl. künftiger Projekte zuweisen", async () => {
        await write(`/api/teacher/tasks/${task.id}/assign`, "POST", {all:true}); await refresh();
      }), button("Ausgewählten Projekten zuweisen", async () => {
        const ids = [...document.querySelectorAll(".project-select:checked")].map(c=>Number(c.value));
        if (!ids.length) throw new Error("Bitte im Bereich Projekte zuerst eine Auswahl treffen.");
        await write(`/api/teacher/tasks/${task.id}/assign`, "POST", {project_ids:ids}); await refresh();
      }), button("Abgaben ansehen", async () => { await showSubmissions(task, card); }), button("In Galerie veröffentlichen", async () => {
        if (!confirm("Die Aufgabenstellung in der öffentlichen Galerie veröffentlichen?")) return;
        await write(`/api/teacher/tasks/${task.id}/publish`, "POST", {}); status("Aufgabe veröffentlicht.");
      }), button("Aufgabe löschen", async () => {
        if (!confirm("Aufgabe und sämtliche zugehörigen Abgaben endgültig löschen?")) return;
        await api(`/api/teacher/tasks/${task.id}`,{method:"DELETE"}); await refresh();
      }, "danger")); card.append(controls);
      const subBox = document.createElement("div"); subBox.className="submissions";card.append(subBox);
      $("tasks-list").append(card);
    }
  }
  async function showSubmissions(task, card) {
    const {submissions} = await api(`/api/teacher/tasks/${task.id}/submissions`), box = card.querySelector(".submissions");
    box.replaceChildren();
    const label = document.createElement("label");label.textContent="Abgaben filtern ";
    const filter = document.createElement("select"); filter.add(new Option("Alle", "")); filter.add(new Option("Noch nicht abgegeben", "missing")); filter.add(new Option("Abgegeben, offen", "submitted")); filter.add(new Option("Erledigt", "done")); label.append(filter);box.append(label);
    const table = document.createElement("table"); box.append(table);
    function draw() {
      table.innerHTML = "<thead><tr><th>Projekt / Code</th><th>Name (lokal)</th><th>Status</th><th>Erledigt</th><th>Projektstand und Antworten</th><th>Aktion</th></tr></thead><tbody></tbody>";
      for (const s of submissions.filter(s => !filter.value || (filter.value === "missing" ? s.status !== "submitted" : filter.value === "done" ? s.done : s.status === "submitted" && !s.done))) {
        const row = document.createElement("tr");
        row.innerHTML = `<td>${esc(s.project_title)} #${s.project_id}<br><code>${esc(s.code)}</code></td><td>${esc(nameMap.get(s.code) || "")}</td><td>${s.status === "submitted" ? "Abgegeben am " + esc(fmtDate(s.submitted_at)) : s.submitted_at ? "Wieder geöffnet" : "Noch nicht abgegeben"}</td><td class="done-cell"></td><td class="answers-cell"></td><td class="action-cell"></td>`;
        const done = document.createElement("input"); done.type="checkbox";done.checked=s.done;done.setAttribute("aria-label","Abgabe als erledigt markieren");
        done.addEventListener("change",guarded(async()=>{await write(`/api/teacher/submissions/${s.submission_id}`,"PATCH",{done:done.checked});s.done=done.checked;})); row.querySelector(".done-cell").append(done);
        const detail = document.createElement("details"); detail.innerHTML="<summary>Abgegebene Versionen und Antworten</summary>";
        detail.addEventListener("toggle",guarded(async()=>{
          if (!detail.open || detail.dataset.loaded) return;
          const {versions} = await api(`/api/teacher/submissions/${s.submission_id}/versions`);
          if (!versions.length) detail.append(document.createTextNode("Noch keine Abgabe vorhanden."));
          for (const v of versions) {
            const entry = document.createElement("div");entry.className="panel";
            entry.append(document.createTextNode("Version " + v.version + " · " + fmtDate(v.created_at) + " "));
            if (v.snapshot_available) {
              entry.append(link("Ansehen / Starten", `/player?submission=${s.submission_id}&version=${v.version}`),document.createTextNode(" "),link("ZIP", `/api/teacher/submissions/${s.submission_id}/versions/${v.version}/download`));
              const snapshot = await api(`/api/teacher/submissions/${s.submission_id}/versions/${v.version}`);
              for (const item of snapshot.snapshot.task.items) {
                const answer = snapshot.answers[item.id]; if (item.kind !== "checkbox" || typeof answer?.checked !== "boolean") continue;
                const text = document.createElement("p");text.className="answers-view";
                text.textContent = item.prompt + ": " + (answer.checked ? "Ja" : "Nein");entry.append(text);
              }
            } else entry.append(document.createTextNode("Altbestand: kein eingefrorener Programmstand vorhanden."));
            detail.append(entry);
          }
          detail.dataset.loaded="true";
        })); row.querySelector(".answers-cell").append(detail);
        if (s.status === "submitted") row.querySelector(".action-cell").append(button("Wieder öffnen",async()=>{await write(`/api/teacher/submissions/${s.submission_id}/reopen`,"POST",{});await showSubmissions(task,card);}));
        table.querySelector("tbody").append(row);
      }
    }
    filter.addEventListener("change",draw);draw();
  }
  function renderShares() {
    $("share-list").replaceChildren();
    if (!shares.length) $("share-list").textContent="Keine Freigabe-Anträge.";
    for(const s of shares) {
      const card=document.createElement("article");card.className="task-card";
      const p=projects.find(p=>p.id===s.project_id);
      card.innerHTML=`<h4>Projekt #${s.project_id} · ${esc(s.status)}</h4><p>${esc(p?.title || "")} · beantragt ${esc(fmtDate(s.declared_at))}</p>`;
      card.append(link("Programm prüfen", "/player?teacher="+s.project_id));
      for (const m of s.media) {const text=document.createElement("p");text.textContent=m.orig_name+" · "+m.license+" · "+m.source;card.append(text);}
      if(s.status==="pending") card.append(button("Freigeben",async()=>{await write(`/api/teacher/share-requests/${s.id}/approve`,"POST",{});await refresh();}),button("Ablehnen",async()=>{await write(`/api/teacher/share-requests/${s.id}/reject`,"POST",{});await refresh();}));
      if(s.status==="approved") card.append(link("Öffentlich ansehen","/p/"+s.slug),button("Widerrufen",async()=>{await write(`/api/teacher/share-requests/${s.id}/revoke`,"POST",{});await refresh();},"danger"));
      $("share-list").append(card);
    }
  }
  async function loadGallery() {
    const result=await api("/api/teacher/gallery?q="+encodeURIComponent($("gallery-q").value));$("gallery").replaceChildren();
    for(const t of result.tasks) {const card=document.createElement("article");card.className="task-card";card.innerHTML=`<h4>${esc(t.title)}</h4><p>${esc(t.description)}</p>`;card.append(button("Für mich kopieren",async()=>{await write(`/api/teacher/gallery/${t.id}/copy`,"POST",{});await refresh();}));$("gallery").append(card);}
  }
  document.querySelectorAll(".tab").forEach(b=>b.addEventListener("click",guarded(async()=>{
    document.querySelectorAll(".tab").forEach(x=>x.classList.toggle("active",x===b));
    document.querySelectorAll(".tab-panel").forEach(p=>p.classList.toggle("hidden",p.id!=="tab-"+b.dataset.tab));
    if(b.dataset.tab==="audit") {const result=await api("/api/teacher/audit?limit=100");$("audit-list").replaceChildren(...result.entries.map(e=>{const li=document.createElement("li");li.textContent=fmtDate(e.ts)+" · "+e.action+" · "+e.target;return li;}));}
    if(b.dataset.tab==="tasks") await loadGallery();
  })));
  $("course-create-form").addEventListener("submit",guarded(async e=>{await write("/api/teacher/courses","POST",{title:e.target.elements.namedItem("title").value,school_year:e.target.school_year.value});e.target.reset();await refresh();}));
  $("project-create-form").addEventListener("submit",guarded(async e=>{
    const f=e.target;
    const result=await write("/api/teacher/projects","POST",{count:Number(f.count.value),course_id:Number(f.course_id.value)||null,template_project_id:Number(f.template_project_id.value)||null,access_mode:f.access_mode.value,code_readonly_days:Number(f.code_readonly_days.value),writable_until:f.writable_until.value ? new Date(f.writable_until.value).toISOString() : null,code_expires_at:f.code_expires_at.value ? new Date(f.code_expires_at.value).toISOString() : null});
    $("new-codes").textContent="Öffnen auf editor.opencoding.de → Projekt mit Code öffnen\n"+result.projects.map(p=>p.code).join("\n");$("new-codes").classList.remove("hidden");await refresh();await renderTemplateCodes();
  }));
  $("task-create-form").addEventListener("submit",guarded(async e=>{
    const f=e.target;await write("/api/teacher/tasks","POST",{title:f.elements.namedItem("title").value,description:f.description.value,course_id:Number(f.course_id.value)||null,is_template_for_new_projects:f.is_template_for_new_projects.checked});f.reset();await refresh();
  }));
  for (const id of ["project-filter-course","project-filter-state"]) $(id).addEventListener("change",renderProjects);
  $("project-search").addEventListener("input",renderProjects);$("task-filter-course").addEventListener("change",renderTasks);
  $("refresh-projects").addEventListener("click",guarded(refresh));
  $("select-all-projects").addEventListener("change",e=>document.querySelectorAll(".project-select").forEach(c=>c.checked=e.target.checked));
  $("bulk-lock").addEventListener("click",guarded(()=>bulk({read_only:true})));$("bulk-unlock").addEventListener("click",guarded(()=>bulk({read_only:false})));
  $("bulk-move").addEventListener("click",guarded(()=>bulk({course_id:Number($("bulk-course").value)||null})));
  $("gallery-search").addEventListener("click",guarded(loadGallery));
  $("namejoin-file").addEventListener("change",guarded(async event=>{
    const file=event.target.files[0];if(!file)return;const workbook=XLSX.read(await file.arrayBuffer(),{type:"array"});
    const rows=XLSX.utils.sheet_to_json(workbook.Sheets[workbook.SheetNames[0]],{header:1});
    const header=(rows.shift()||[]).map(s=>String(s).trim().toLowerCase()),codeIndex=header.indexOf("code"),nameIndex=header.indexOf("name");
    if(codeIndex<0||nameIndex<0)throw new Error("Die Datei benötigt die Spalten Code und Name.");
    nameMap.clear();workspaceNames.clear();for(const row of rows){const code=String(row[codeIndex]||"").trim().toUpperCase(),name=String(row[nameIndex]||"").trim();if(code&&name)nameMap.set(code,name);}
    $("namejoin-status").textContent=nameMap.size+" Zuordnungen lokal geladen.";await refresh();
  }));
  guarded(async()=>{const session=await api("/api/auth/session");sessionStorage.setItem("csrf",session.csrf);await refresh();await renderTemplateCodes();})();
})();
