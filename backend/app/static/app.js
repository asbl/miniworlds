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
    return fetch(path, opts);
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
      const status = el("workspace-status") || el("dashboard-status");
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
        el("err").textContent = (res.data && res.data.detail) || "Login fehlgeschlagen";
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
    async function loadInvites() {
      const res = await apiJson("/api/admin/invites");
      const tb = el("invites-table").querySelector("tbody");
      tb.innerHTML = "";
      (res.data.invites || []).forEach(function (inv) {
        const tr = document.createElement("tr");
        tr.innerHTML = "<td>" + esc(inv.school) + "</td><td>" + esc(inv.email || "—") + "</td><td>" + fmtTs(inv.created_at) +
          "</td><td>" + (inv.expires_at ? fmtTs(inv.expires_at) : "nie") + "</td><td>" + (inv.claimed_at ? fmtTs(inv.claimed_at) : "nein") + "</td>";
        const td = document.createElement("td");
        if (!inv.claimed_at) {
          const b = document.createElement("button");
          b.className = "danger"; b.textContent = "Löschen";
          b.addEventListener("click", async function () {
            await api("/api/admin/invites/" + inv.id, { method: "DELETE" });
            loadInvites();
          });
          td.appendChild(b);
        }
        tr.appendChild(td);
        tb.appendChild(tr);
      });
    }
    el("invite-form").addEventListener("submit", async function (ev) {
      ev.preventDefault();
      const f = ev.target;
      const res = await apiJson("/api/admin/invites", {
        method: "POST",
        body: JSON.stringify({ school: f.school.value, email: f.email.value || null }),
      });
      if (res.status === 200) {
        const box = el("new-code");
        box.classList.remove("hidden");
        box.textContent = "Neuer Lehrercode (nur einmalig sichtbar):\n" + res.data.code + "\nSchule: " + res.data.school;
        f.reset();
        loadInvites();
      }
    });
    async function loadSettings() {
      const res = await apiJson("/api/admin/settings");
      el("settings-form").teacher_quota_cap.value = res.data.teacher_quota_cap;
      el("settings-form").student_default_quota.value = res.data.student_default_quota;
    }
    el("settings-form").addEventListener("submit", async function (ev) {
      ev.preventDefault();
      await apiJson("/api/admin/settings", {
        method: "PATCH",
        body: JSON.stringify({
          teacher_quota_cap: parseInt(ev.target.teacher_quota_cap.value, 10),
          student_default_quota: parseInt(ev.target.student_default_quota.value, 10),
        }),
      });
      loadSettings();
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
        b.addEventListener("click", async function () {
          await api("/api/admin/teachers/" + t.id + "/disable", { method: "POST", body: JSON.stringify({ disabled: !t.disabled }) });
          loadTeachers();
        });
        td.appendChild(b);
        tr.appendChild(td);
        tb.appendChild(tr);
      });
    }
    async function loadPublicTasks() {
      const res = await apiJson("/api/admin/public-tasks");
      const box = el("public-tasks-list");
      if (!box) return;
      box.innerHTML = "";
      (res.data.public_tasks || []).forEach(function (t) {
        const li = document.createElement("li");
        li.textContent = "#" + t.id + " „" + t.title + "“ v" + t.version + " (" + t.status + ", " + esc(t.school || t.author_alias || "anonym") + ", Lizenz: " + esc(t.license) + ") ";
        const b = document.createElement("button");
        b.className = "danger";
        b.textContent = t.status === "hidden" ? "einblenden" : "verbergen";
        b.addEventListener("click", async function () {
          await api("/api/admin/public-tasks/" + t.id + "/hide", { method: "POST", body: JSON.stringify({ hidden: t.status !== "hidden" }) });
          loadPublicTasks();
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
        li.textContent = fmtTs(e.ts) + "  [" + e.actor_type + " " + e.actor_ref + "] " + e.action + " " + e.target + (e.meta ? "  " + JSON.stringify(e.meta) : "");
        ul.appendChild(li);
      });
    }
    loadInvites(); loadSettings(); loadTeachers(); loadPublicTasks(); loadAudit();
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
