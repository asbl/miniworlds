/* miniworlds backend — Dashboard-/Player-Logik (Vanilla JS, CSP: nur externe Dateien) */
(function () {
  "use strict";

  // Clear old free-text answer drafts on every page, preserving checkbox choices only.
  Object.keys(sessionStorage).filter(key => key.startsWith("miniworlds-answers:")).forEach(key => {
    try {
      const old = JSON.parse(sessionStorage.getItem(key)), cleaned = {};
      if (old && typeof old === "object" && !Array.isArray(old)) {
        Object.entries(old).forEach(([id, answer]) => {
          if (/^[0-9]+$/.test(id) && typeof answer?.checked === "boolean") cleaned[id] = {checked:answer.checked};
        });
      }
      if (Object.keys(cleaned).length) sessionStorage.setItem(key, JSON.stringify(cleaned));
      else sessionStorage.removeItem(key);
    } catch (_) { sessionStorage.removeItem(key); }
  });


  function csrf() { return sessionStorage.getItem("csrf") || ""; }
  function stoken() { return sessionStorage.getItem("stoken") || ""; }

  async function api(path, opts) {
    opts = opts || {};
    opts.headers = Object.assign({ "Content-Type": "application/json" }, opts.headers || {});
    if (csrf()) opts.headers["X-CSRF-Token"] = csrf();
    if (stoken() && (path.indexOf("/api/play") === 0 || path === "/api/claim")) {
      opts.headers["Authorization"] = "Bearer " + stoken();
    }
    const response = await fetch(path, opts);
    if (path.startsWith("/api/admin/") && !response.ok) {
      const body=await response.json().catch(()=>({}));
      throw new Error(typeof body.detail === "string" ? body.detail : "Aktion fehlgeschlagen ("+response.status+").");
    }
    return response;
  }

  async function apiJson(path, opts) {
    const r = await api(path, opts);
    let data = null;
    try { data = await r.json(); } catch (e) { /* ignore */ }
    return { status: r.status, data: data };
  }

  function el(id) { return document.getElementById(id); }
  function esc(s) {
    return String(s == null ? "" : s).replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
  }
  function fmtBytes(n) {
    if (n >= 1048576) return (n / 1048576).toFixed(1) + " MB";
    if (n >= 1024) return (n / 1024).toFixed(1) + " KB";
    return n + " B";
  }
  function fmtTs(ts) { return ts ? new Date(ts).toLocaleString("de-DE") : "—"; }

  const auditLabels = {
    login:"Angemeldet", claim:"Lehrerzugang angelegt", invite_created:"Lehrercode erstellt", invite_deleted:"Lehrercode gelöscht",
    settings_changed:"Einstellungen geändert", teacher_disabled:"Lehrerzugang gesperrt", teacher_enabled:"Lehrerzugang entsperrt", teacher_deleted:"Lehrerzugang gelöscht",
    projects_created:"Projekte erstellt", project_updated:"Projekt geändert", projects_bulk_updated:"Projekte geändert", project_deleted:"Projekt gelöscht", project_forked:"Projekt kopiert",
    course_created:"Klasse angelegt", course_archived:"Klasse archiviert", course_reactivated:"Klasse reaktiviert", code_regenerated:"Code erneuert", student_password_reset:"Schülerpasswort entfernt",
    task_created:"Aufgabe erstellt", task_updated:"Aufgabe geändert", task_deleted:"Aufgabe gelöscht", task_assigned:"Aufgabe zugewiesen", task_submitted:"Projekt abgegeben",
    task_published:"Aufgabe veröffentlicht", task_unpublished:"Aufgabe zurückgezogen", public_task_copied:"Aufgabe kopiert", public_task_hidden:"Aufgabe verborgen", public_task_unhidden:"Aufgabe eingeblendet",
    submission_reopened:"Abgabe wieder geöffnet", submission_reviewed:"Abgabestatus geändert", share_requested:"Freigabe beantragt", share_approved:"Veröffentlichung freigegeben", share_rejected:"Freigabe abgelehnt", share_revoked:"Freigabe widerrufen",
    git_remote_set:"Git-Verbindung gespeichert", git_remote_removed:"Git-Verbindung entfernt", git_push:"Git-Änderungen übertragen", git_pull:"Git-Änderungen geladen", git_restore:"Version wiederhergestellt", git_history_deleted:"Versionsverlauf gelöscht", git_commit_failed:"Version konnte nicht gespeichert werden",
    retention_deleted:"Projekt nach Aufbewahrungsfrist gelöscht", retention_read_only:"Projekt nach Aufbewahrungsfrist gesperrt"
  };
  window.miniworldsAuditLabel = action => auditLabels[action] || action.replaceAll("_", " ");

  async function logout() {
    const button = el("logout-btn");
    button.disabled = true;
    try {
      if (window.miniworldsBeforeLogout) await window.miniworldsBeforeLogout();
      const session = await apiJson("/api/auth/session");
      if (session.status === 200) sessionStorage.setItem("csrf", session.data.csrf);
      const result = await apiJson("/api/auth/logout", { method: "POST", body: "{}" });
      if (result.status !== 200 && result.status !== 401) throw new Error("Abmelden ist fehlgeschlagen. Bitte erneut versuchen.");
      window.dispatchEvent(new Event("miniworlds:logout"));
      sessionStorage.clear();
      location.href = "/";
    } catch (error) {
      const status = el("workspace-status") || el("dashboard-status") || el("app-status");
      if (status) { status.textContent = error.message; status.classList.add("error"); }
      else alert(error.message);
      button.disabled = false;
    }
  }
  const lb = el("logout-btn");
  if (lb) lb.addEventListener("click", logout);

  const page = document.body.dataset.page;

  /* ---------- Login ---------- */
  if (page === "login") {
    el("login-form").addEventListener("submit", async function (ev) {
      ev.preventDefault();
      const f = ev.target;
      el("err").textContent = "";
      const res = await apiJson("/api/auth/login", {
        method: "POST",
        body: JSON.stringify({ email: f.email.value, password: f.password.value, role: f.dataset.role }),
      });
      if (res.status === 200) {
        sessionStorage.setItem("csrf", res.data.csrf);
        location.href = res.data.role === "admin" ? "/admin" : "/teacher";
      } else {
        el("err").textContent = (res.data && res.data.detail) || "Anmeldung fehlgeschlagen";
      }
    });
  }

  /* ---------- Claim ---------- */
  if (page === "claim") {
    const f = el("claim-form");
    f.invite_code.addEventListener("change", async function () {
      const res = await apiJson("/api/auth/invite-code-check", {
        method: "POST",
        body: JSON.stringify({ invite_code: f.invite_code.value, email: "", password: "" }),
      });
      if (res.status === 200) el("school-field").value = res.data.school || "";
    });
    f.addEventListener("submit", async function (ev) {
      ev.preventDefault();
      el("err").textContent = "";
      const res = await apiJson("/api/auth/claim", {
        method: "POST",
        body: JSON.stringify({ invite_code: f.invite_code.value, email: f.email.value, password: f.password.value }),
      });
      if (res.status === 200) {
        sessionStorage.setItem("csrf", res.data.csrf);
        location.href = "/teacher";
      } else {
        el("err").textContent = (res.data && res.data.detail) || "Fehler";
      }
    });
  }

  /* ---------- Admin ---------- */
  if (page === "admin") {
    function adminError(error) {
      el("app-status").textContent=error.message || "Keine Verbindung.";
      el("app-status").classList.add("error");
    }
    function adminOn(element, type, callback) {
      element.addEventListener(type, async event=>{
        try { await callback(event); } catch(error) { adminError(error); }
      });
    }
    async function loadInvites() {
      const res = await apiJson("/api/admin/invites");
      const tb = el("invites-table").querySelector("tbody");
      tb.innerHTML = "";
      (res.data.invites || []).forEach(function (inv) {
        const tr = document.createElement("tr");
        tr.innerHTML = "<td>" + esc(inv.school) + "</td><td>" + esc(inv.email || "—") + "</td><td>" + fmtTs(inv.created_at) +
          "</td><td>" + (inv.expires_at ? fmtTs(inv.expires_at) : "Unbegrenzt") + "</td><td>" + (inv.claimed_at ? fmtTs(inv.claimed_at) : "—") + "</td>";
        const td = document.createElement("td");
        if (!inv.claimed_at) {
          const b = document.createElement("button");
          b.className = "danger"; b.textContent = "Löschen";
          adminOn(b, "click", async function () {
            await api("/api/admin/invites/" + inv.id, { method: "DELETE" });
            await loadInvites();
          });
          td.appendChild(b);
        }
        tr.appendChild(td);
        tb.appendChild(tr);
      });
      if (!(res.data.invites || []).length) tb.innerHTML='<tr><td colspan="6" class="empty-row">Keine Lehrercodes.</td></tr>';
    }
    adminOn(el("invite-form"), "submit", async function (ev) {
      ev.preventDefault();
      const f = ev.target;
      const res = await apiJson("/api/admin/invites", {
        method: "POST",
        body: JSON.stringify({ school: f.school.value, email: f.email.value || null }),
      });
      if (res.status === 200) {
        const box = el("new-code");
        box.classList.remove("hidden");
        box.textContent = res.data.code + "\nNur einmal sichtbar.";
        f.reset();
        await loadInvites();
      }
    });
    async function loadSettings() {
      const res = await apiJson("/api/admin/settings");
      el("settings-form").teacher_quota_cap.value = res.data.teacher_quota_cap / 1048576;
      el("settings-form").student_default_quota.value = res.data.student_default_quota / 1048576;
    }
    adminOn(el("settings-form"), "submit", async function (ev) {
      ev.preventDefault();
      await apiJson("/api/admin/settings", {
        method: "PATCH",
        body: JSON.stringify({
          teacher_quota_cap: Math.round(Number(ev.target.teacher_quota_cap.value)*1048576),
          student_default_quota: Math.round(Number(ev.target.student_default_quota.value)*1048576),
        }),
      });
      await loadSettings();
      el("app-status").classList.remove("error");el("app-status").textContent="Gespeichert.";
    });
    async function loadTeachers() {
      const res = await apiJson("/api/admin/teachers");
      const tb = el("teachers-table").querySelector("tbody");
      tb.innerHTML = "";
      (res.data.teachers || []).forEach(function (t) {
        const tr = document.createElement("tr");
        tr.innerHTML = "<td>" + esc(t.email) + "</td><td>" + esc(t.school || "—") + "</td><td>" + t.projects + "</td><td>" + (t.disabled ? "gesperrt" : "aktiv") + "</td>";
        const td = document.createElement("td");
        const b = document.createElement("button");
        b.className = t.disabled ? "secondary" : "danger";
        b.textContent = t.disabled ? "Entsperren" : "Sperren";
        adminOn(b, "click", async function () {
          await api("/api/admin/teachers/" + t.id + "/disable", { method: "POST", body: JSON.stringify({ disabled: !t.disabled }) });
          await loadTeachers();
        });
        td.appendChild(b);
        tr.appendChild(td);
        tb.appendChild(tr);
      });
      if (!(res.data.teachers || []).length) tb.innerHTML='<tr><td colspan="5" class="empty-row">Keine Lehrerzugänge.</td></tr>';
    }
    async function loadPublicTasks() {
      const res = await apiJson("/api/admin/public-tasks");
      const box = el("public-tasks-list");
      if (!box) return;
      box.innerHTML = "";
      if (!(res.data.public_tasks || []).length) box.textContent="Keine öffentlichen Aufgaben.";
      (res.data.public_tasks || []).forEach(function (t) {
        const li = document.createElement("li");
        li.textContent = [t.title, "Version " + t.version, t.status === "hidden" ? "Verborgen" : "Öffentlich", t.school || t.author_alias, t.license].filter(Boolean).join(" · ") + " ";
        const b = document.createElement("button");
        b.className = "danger";
        b.textContent = t.status === "hidden" ? "Einblenden" : "Verbergen";
        adminOn(b, "click", async function () {
          await api("/api/admin/public-tasks/" + t.id + "/hide", { method: "POST", body: JSON.stringify({ hidden: t.status !== "hidden" }) });
          await loadPublicTasks();
        });
        li.appendChild(b);
        box.appendChild(li);
      });
    }
    async function loadAudit() {
      const res = await apiJson("/api/admin/audit?limit=100");
      const ul = el("audit-list");
      ul.innerHTML = "";
      (res.data.entries || []).forEach(function (e) {
        const li = document.createElement("li");
        li.textContent = [fmtTs(e.ts), window.miniworldsAuditLabel(e.action), e.target].filter(Boolean).join(" · ");
        const details=document.createElement("details"), summary=document.createElement("summary"), data=document.createElement("pre");
        summary.textContent="Details";data.textContent=JSON.stringify({actor_type:e.actor_type,actor_ref:e.actor_ref,meta:e.meta},null,2);
        details.append(summary,data);li.append(details);
        ul.appendChild(li);
      });
    }
    Promise.all([loadInvites(),loadSettings(),loadTeachers(),loadPublicTasks(),loadAudit()]).catch(adminError);
  }

  /* ---------- Öffentliche Seite: Melden ---------- */
  if (page === "public") {
    const f = el("report-form");
    if (f) f.addEventListener("submit", async function (ev) {
      ev.preventDefault();
      const slug = location.pathname.split("/").pop();
      const res = await apiJson("/api/public/" + encodeURIComponent(slug) + "/report", {
        method: "POST",
        body: JSON.stringify({ reason: f.reason.value }),
      });
      el("report-msg").textContent = res.status === 200 ? res.data.message : ((res.data && res.data.detail) || "Fehler");
    });
  }
})();
