// Base URL del backend (FastAPI): usa el mismo host donde se abrió el frontend
const API = `http://${window.location.hostname}:8000`;

const el = (id) => document.getElementById(id);

// Containers
const authCard = el("authCard");
const appCard = el("appCard");

// Auth
const tabLogin = el("tabLogin");
const tabRegister = el("tabRegister");
const tabLoginTop = el("tabLoginTop");
const tabRegisterTop = el("tabRegisterTop");

const authForm = el("authForm");
const authSubmit = el("authSubmit");
const authMsg = el("authMsg");

const emailInput = el("email");
const passInput = el("password");
const showPass = el("showPass");

const signinLabel = el("signinLabel");
const signupLabel = el("signupLabel");
const authUnderline = el("authUnderline");

// Theme
const themeToggle = el("themeToggle");

// Topbar
const logoutBtn = el("logoutBtn");
const whoami = el("whoami");

// App actions
const refreshBtn = el("refreshBtn");
const reportBtn = el("reportBtn");
const printReportBtn = el("printReportBtn");
const goSSOBtn = el("goSSOBtn");

// Create + lists
const createForm = el("createForm");
const createBtn = el("createBtn");
const newTitle = el("newTitle");
const newDesc = el("newDesc");
const newStatus = el("newStatus");
const appMsg = el("appMsg");
const tasksList = el("tasksList");
const reportBox = el("reportBox");

// Toast + Modal
const toastHost = el("toastHost");

const modalOverlay = el("modalOverlay");
const modalTitle = el("modalTitle");
const modalBody = el("modalBody");
const modalClose = el("modalClose");
const modalCancel = el("modalCancel");
const modalOk = el("modalOk");

let mode = "login";

// -------------------- Theme --------------------
function applyTheme(theme) {
  const root = document.documentElement;
  const isDark = theme === "dark";

  if (isDark) root.setAttribute("data-theme", "dark");
  else root.removeAttribute("data-theme");

  // aria pressed
  if (themeToggle) themeToggle.setAttribute("aria-pressed", isDark ? "true" : "false");

  // ✅ NUEVO: cambiar ícono luna/sol
  const label = document.querySelector(".theme-label");
  if (label) label.textContent = isDark ? "☀️" : "🌙";
}


function getSavedTheme() {
  return localStorage.getItem("theme") || "light";
}

function toggleTheme() {
  const cur = getSavedTheme();
  const next = cur === "dark" ? "light" : "dark";
  localStorage.setItem("theme", next);
  applyTheme(next);
  // recalcular underline si cambia el layout
  requestAnimationFrame(positionUnderline);
}

// -------------------- UI helpers --------------------
function setMsg(target, text, kind = "") {
  target.className = "msg " + (kind || "");
  target.textContent = text || "";
}

function setLoading(button, loading, textLoading = "Cargando...") {
  if (!button) return;
  button.disabled = loading;
  button.classList.toggle("loading", !!loading);

  const t = button.querySelector(".btn-text");
  if (!t) return;

  if (!button.dataset._txt) button.dataset._txt = t.textContent;
  t.textContent = loading ? textLoading : button.dataset._txt;
}

function markInvalid(inputEl, isInvalid) {
  if (!inputEl) return;
  inputEl.classList.toggle("input-err", !!isInvalid);
}

function clearAuthFields() {
  emailInput.value = "";
  passInput.value = "";
  if (showPass) showPass.checked = false;
  passInput.type = "password";
  markInvalid(emailInput, false);
  markInvalid(passInput, false);
  setMsg(authMsg, "");
}

function clearAppMessages() {
  setMsg(appMsg, "");
}

function clearToasts() {
  if (toastHost) toastHost.innerHTML = "";
}

// -------------------- Toasts (notificaciones dentro de la página) --------------------
function toast(type, title, text, timeoutMs = 3200) {
  if (!toastHost) return;

  const node = document.createElement("div");
  node.className = `toast ${type || "info"}`;

  const ico = document.createElement("div");
  ico.className = "toast-ico";
  ico.textContent = type === "ok" ? "✓" : type === "err" ? "!" : "i";

  const body = document.createElement("div");
  body.className = "toast-body";

  const t = document.createElement("div");
  t.className = "toast-title";
  t.textContent = title || "Aviso";

  const p = document.createElement("p");
  p.className = "toast-text";
  p.textContent = text || "";

  const close = document.createElement("button");
  close.className = "toast-close";
  close.type = "button";
  close.textContent = "✕";
  close.onclick = () => node.remove();

  body.appendChild(t);
  body.appendChild(p);

  node.appendChild(ico);
  node.appendChild(body);
  node.appendChild(close);

  toastHost.appendChild(node);

  if (timeoutMs > 0) {
    setTimeout(() => {
      if (node && node.parentNode) node.remove();
    }, timeoutMs);
  }
}

// -------------------- Modal (reemplaza confirm()) --------------------
function openModal({ title = "Confirmar", message = "¿Seguro?", okText = "Aceptar", cancelText = "Cancelar", danger = false }) {
  return new Promise((resolve) => {
    modalTitle.textContent = title;
    modalBody.textContent = message;

    modalOk.textContent = okText;
    modalCancel.textContent = cancelText;

    modalOk.classList.toggle("danger", !!danger);

    modalOverlay.classList.remove("hidden");
    modalOverlay.setAttribute("aria-hidden", "false");

    const cleanup = () => {
      modalOverlay.classList.add("hidden");
      modalOverlay.setAttribute("aria-hidden", "true");
      modalClose.onclick = null;
      modalCancel.onclick = null;
      modalOk.onclick = null;
      modalOverlay.onclick = null;
      document.removeEventListener("keydown", escHandler);
    };

    const escHandler = (e) => {
      if (e.key === "Escape") {
        cleanup();
        resolve(false);
      }
    };

    modalClose.onclick = () => { cleanup(); resolve(false); };
    modalCancel.onclick = () => { cleanup(); resolve(false); };
    modalOk.onclick = () => { cleanup(); resolve(true); };

    modalOverlay.onclick = (e) => {
      if (e.target === modalOverlay) {
        cleanup();
        resolve(false);
      }
    };

    document.addEventListener("keydown", escHandler);
  });
}

// -------------------- Validations --------------------
function isUceEmail(email) {
  return email.trim().toLowerCase().endsWith("@uce.edu.ec");
}

function isStrongPassword(p) {
  if (!p || p.length < 8) return false;
  const hasUpper = /[A-Z]/.test(p);
  const hasNum = /[0-9]/.test(p);
  return hasUpper && hasNum;
}

function statusClass(status) {
  if (status === "PENDING") return "status-pending";
  if (status === "IN_PROGRESS") return "status-progress";
  if (status === "DONE") return "status-done";
  return "";
}

// -------------------- Token helpers --------------------
function getToken() {
  const t = localStorage.getItem("token") || "";
  if (t === "undefined" || t === "null") return "";
  return t;
}
function setToken(t) {
  if (!t || t === "undefined" || t === "null") return;
  localStorage.setItem("token", t);
}
function clearToken() {
  localStorage.removeItem("token");
}

// -------------------- View helpers --------------------
function showApp(email = "") {
  authCard.classList.add("hidden");
  appCard.classList.remove("hidden");
  logoutBtn.classList.remove("hidden");
  whoami.textContent = email ? `Sesión: ${email}` : "Sesión activa";
}

function showAuth() {
  authCard.classList.remove("hidden");
  appCard.classList.add("hidden");
  logoutBtn.classList.add("hidden");
  whoami.textContent = "";
}

function syncTopPills() {
  tabLoginTop.classList.toggle("active", mode === "login");
  tabRegisterTop.classList.toggle("active", mode === "register");

  signinLabel.className = mode === "login" ? "auth-head-strong" : "auth-head-muted";
  signupLabel.className = mode === "register" ? "auth-head-strong" : "auth-head-muted";

  authSubmit.querySelector(".btn-text").textContent = mode === "login" ? "Entrar" : "Registrar";
}

function setMode(next) {
  mode = next;

  // legacy tabs (compat)
  tabLogin.classList.toggle("active", mode === "login");
  tabRegister.classList.toggle("active", mode === "register");

  // limpiar inputs + mensajes al cambiar
  clearAuthFields();
  clearToasts();

  syncTopPills();
  requestAnimationFrame(positionUnderline);
}

// underline dinámico según label activo
function positionUnderline() {
  const activeEl = mode === "login" ? signinLabel : signupLabel;
  const wrap = activeEl?.parentElement;
  if (!activeEl || !wrap || !authUnderline) return;

  const wrapRect = wrap.getBoundingClientRect();
  const rect = activeEl.getBoundingClientRect();

  const left = rect.left - wrapRect.left;
  const width = rect.width;

  authUnderline.style.transform = `translateX(${Math.max(0, left)}px)`;
  authUnderline.style.width = `${Math.max(42, width)}px`;
}

// -------------------- API wrapper --------------------
async function apiFetch(path, opts = {}) {
  const headers = opts.headers || {};
  headers["Content-Type"] = "application/json";

  const token = getToken();
  if (token) headers["Authorization"] = "Bearer " + token;

  const res = await fetch(API + path, { ...opts, headers });

  const text = await res.text();
  let data = null;
  try { data = text ? JSON.parse(text) : null; }
  catch { data = text; }

  if (!res.ok) {
    let detail = "Error";
    if (data && data.detail !== undefined) {
      if (Array.isArray(data.detail)) detail = data.detail.map((x) => x.msg).join(" | ");
      else if (typeof data.detail === "object") detail = JSON.stringify(data.detail);
      else detail = String(data.detail);
    } else if (typeof data === "string") detail = data;
    else if (data) detail = JSON.stringify(data);

    throw new Error(`${res.status} - ${detail}`);
  }

  return data;
}

// -------------------- “shake” visual when invalid --------------------
function shake(elm) {
  if (!elm) return;
  elm.animate(
    [
      { transform: "translateX(0)" },
      { transform: "translateX(-6px)" },
      { transform: "translateX(6px)" },
      { transform: "translateX(-4px)" },
      { transform: "translateX(4px)" },
      { transform: "translateX(0)" },
    ],
    { duration: 260, easing: "ease-out" }
  );
}

// -------------------- Events --------------------
tabLogin.addEventListener("click", () => setMode("login"));
tabRegister.addEventListener("click", () => setMode("register"));

tabLoginTop.addEventListener("click", () => setMode("login"));
tabRegisterTop.addEventListener("click", () => setMode("register"));

if (themeToggle) themeToggle.addEventListener("click", toggleTheme);

if (showPass) {
  showPass.addEventListener("change", () => {
    passInput.type = showPass.checked ? "text" : "password";
  });
}

// AUTH submit
authForm.addEventListener("submit", async (e) => {
  e.preventDefault();

  clearToasts();
  setMsg(authMsg, "");

  const email = emailInput.value.trim().toLowerCase();

  const password = passInput.value || "";

  // validaciones completas
  let ok = true;

  markInvalid(emailInput, false);
  markInvalid(passInput, false);

  if (!email) {
    ok = false;
    markInvalid(emailInput, true);
    toast("err", "Falta el correo", "Escribe tu correo institucional @uce.edu.ec.");
  } else if (!isUceEmail(email)) {
    ok = false;
    markInvalid(emailInput, true);
    toast("err", "Revisa tu correo", "Usa un correo que termine en @uce.edu.ec.");
  }

  if (!password) {
    ok = false;
    markInvalid(passInput, true);
    toast("err", "Falta la contraseña", "Escribe tu contraseña.");
  } else if (!isStrongPassword(password)) {
    ok = false;
    markInvalid(passInput, true);
    toast("err", "Contraseña inválida", "Mínimo 8 caracteres, 1 mayúscula y 1 número.");
  }

  if (!ok) {
    shake(authCard);
    return;
  }

  if (mode === "login") {
    // LOGIN
    setLoading(authSubmit, true, "Entrando...");
    try {
      const data = await apiFetch("/auth/login", {
        method: "POST",
        body: JSON.stringify({ email, password })
      });

      const access =
        data?.access_token ||
        data?.token ||
        data?.jwt ||
        data?.data?.access_token ||
        "";

      if (!access) throw new Error("No se recibió access_token del backend. Revisa /auth/login.");

      setToken(access);

      setMsg(authMsg, "Listo ✅ Sesión iniciada.", "ok");
      toast("ok", "Sesión iniciada", "Bienvenido. Cargando tus tareas…", 2200);

      showApp(email);
      await loadTasks();
    } catch (err) {
      setMsg(authMsg, "No se pudo iniciar sesión.", "err");
      toast("err", "Error al iniciar sesión", err.message, 4200);
    } finally {
      setLoading(authSubmit, false);
    }
  } else {
    // REGISTER (NO LOGIN AUTOMÁTICO)
    setLoading(authSubmit, true, "Registrando...");
    try {
      await apiFetch("/auth/register", {
        method: "POST",
        body: JSON.stringify({ email, password })
      });

      toast("ok", "Registro exitoso", "Ahora puedes iniciar sesión con tu cuenta.", 3800);
      setMsg(authMsg, "Registro exitoso ✅", "ok");

      // limpiar campos y volver a login
      clearAuthFields();
      setMode("login");
    } catch (err) {
      setMsg(authMsg, "No se pudo registrar.", "err");
      toast("err", "Error al registrar", err.message, 4200);
    } finally {
      setLoading(authSubmit, false);
    }
  }
});

// Logout
logoutBtn.addEventListener("click", () => {
  clearToken();
  tasksList.innerHTML = "";
  reportBox.innerHTML = "";
  clearAppMessages();
  clearToasts();
  whoami.textContent = "";
  showAuth();
  setMode("login");
});

// Refresh tasks
refreshBtn.addEventListener("click", loadTasks);

// Report
reportBtn.addEventListener("click", async () => {
  clearToasts();
  setMsg(appMsg, "");
  setLoading(reportBtn, true, "Cargando...");
  try {
    const rep = await apiFetch("/reports/tasks-with-last-change", { method: "GET" });
    renderReport(rep);
  } catch (err) {
    reportBox.innerHTML = "";
    setMsg(appMsg, "No se pudo cargar el reporte.", "err");
    toast("err", "No se pudo cargar el reporte", err.message, 4200);
  } finally {
    setLoading(reportBtn, false);
  }
});

// Print report
if (printReportBtn) {
  printReportBtn.addEventListener("click", () => {
    const content = reportBox.innerHTML
      ? reportBox.innerHTML
      : `<pre>${escapeHtml(reportBox.textContent || "")}</pre>`;

    const w = window.open("", "_blank");
    const styles = `
      <style>
        body{font-family:Arial, sans-serif; padding:18px;}
        h2{margin:0 0 10px;}
        .muted{color:#555; font-size:12px;}
        table{width:100%; border-collapse:collapse; margin-top:10px;}
        th,td{border:1px solid #ccc; padding:8px; text-align:left;}
        th{background:#f2f2f2;}
        .badge{display:inline-block; padding:2px 8px; border-radius:999px; border:1px solid #ccc; font-size:12px;}
      </style>
    `;

    w.document.write(`
      <html>
        <head>
          <title>Reporte combinado</title>
          ${styles}
        </head>
        <body>
          <h2>Reporte combinado</h2>
          <div class="muted">Tareas (Postgres) + último cambio (Mongo)</div>
          ${content}
          <script>window.print();</script>
        </body>
      </html>
    `);
    w.document.close();
  });
}

// Create task submit
createForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  clearToasts();
  setMsg(appMsg, "");

  const title = (newTitle.value || "").trim();
  if (!title) {
    markInvalid(newTitle, true);
    toast("err", "Falta el título", "Escribe un título para la tarea.");
    return;
  }
  if (title.length < 3) {
    markInvalid(newTitle, true);
    toast("err", "Título muy corto", "El título debe tener al menos 3 caracteres.");
    return;
  }
  markInvalid(newTitle, false);

  setLoading(createBtn, true, "Creando...");
  try {
    const payload = {
      title,
      description: (newDesc.value || "").trim() || null,
      status: newStatus.value
    };

    const created = await apiFetch("/tasks", { method: "POST", body: JSON.stringify(payload) });

    // micro “success”
    toast("ok", "Tarea creada", `Se creó la tarea: ${created.title || created.id}`, 2600);
    setMsg(appMsg, "Tarea creada ✅", "ok");

    // limpiar
    newTitle.value = "";
    newDesc.value = "";
    newStatus.value = "PENDING";

    await loadTasks();
  } catch (err) {
    setMsg(appMsg, "No se pudo crear la tarea.", "err");
    toast("err", "Error al crear tarea", err.message, 4200);
  } finally {
    setLoading(createBtn, false);
  }
});

// -------------------- Tasks --------------------
async function loadTasks() {
  clearToasts();
  setMsg(appMsg, "");
  tasksList.innerHTML = `<div class="muted small">Cargando…</div>`;
  setLoading(refreshBtn, true, "Actualizando...");

  try {
    const tasks = await apiFetch("/tasks", { method: "GET" });
    renderTasks(tasks);
  } catch (err) {
    tasksList.innerHTML = "";
    setMsg(appMsg, "No se pudo cargar tareas.", "err");
    toast("err", "No se pudo cargar tareas", err.message, 4200);

    if (String(err.message).includes("401")) {
      clearToken();
      showAuth();
      setMode("login");
    }
  } finally {
    setLoading(refreshBtn, false);
  }
}

function renderTasks(tasks) {
  if (!tasks || tasks.length === 0) {
    tasksList.innerHTML = `
      <div class="empty">
        <div class="empty-ico">✅</div>
        <div>
          <div class="empty-title">Sin tareas todavía</div>
          <div class="empty-sub">Crea una tarea arriba para empezar.</div>
        </div>
      </div>`;
    return;
  }

  tasksList.innerHTML = "";
  for (const t of tasks) {
    const div = document.createElement("div");
    div.className = "item";

    div.innerHTML = `
      <div class="item-top">
        <div>
          <div class="item-title">${escapeHtml(t.title)}</div>
          <div class="item-meta">${escapeHtml(t.description || "")}</div>
        </div>
        <div class="badge ${statusClass(t.status)}">${escapeHtml(t.status)}</div>
      </div>

      <div class="item-actions">
        <button class="btn status pending" data-action="status" data-id="${t.id}" data-status="PENDING" type="button">PENDING</button>
        <button class="btn status progress" data-action="status" data-id="${t.id}" data-status="IN_PROGRESS" type="button">IN_PROGRESS</button>
        <button class="btn status done" data-action="status" data-id="${t.id}" data-status="DONE" type="button">DONE</button>
        <button class="btn danger" data-action="delete" data-id="${t.id}" data-title="${escapeHtml(t.title)}" type="button">Eliminar</button>
      </div>

      <div class="muted small">id: ${t.id}</div>
    `;
    tasksList.appendChild(div);
  }

  tasksList.querySelectorAll("button").forEach((btn) => {
    btn.addEventListener("click", async () => {
      const action = btn.dataset.action;
      const id = btn.dataset.id;

      if (action === "delete") {
        await deleteTask(id, btn.dataset.title || "");
      } else if (action === "status") {
        await updateTaskStatus(id, btn.dataset.status, btn);
      }
    });
  });
}

async function updateTaskStatus(taskId, status, btn) {
  clearToasts();
  setMsg(appMsg, "");
  setLoading(btn, true, "...");
  try {
    const updated = await apiFetch(`/tasks/${taskId}`, {
      method: "PUT",
      body: JSON.stringify({ status })
    });

    toast("ok", "Estado actualizado", `Nuevo estado: ${updated.status}`, 2200);
    setMsg(appMsg, `Estado actualizado ✅ (${updated.status})`, "ok");
    await loadTasks();
  } catch (err) {
    setMsg(appMsg, "No se pudo actualizar el estado.", "err");
    toast("err", "Error al actualizar", err.message, 4200);
  } finally {
    setLoading(btn, false, btn.dataset._txt || "");
  }
}

async function deleteTask(taskId, title) {
  clearToasts();
  setMsg(appMsg, "");

  const label = title ? `"${title}"` : taskId;

  const ok = await openModal({
    title: "Eliminar tarea",
    message: `¿Seguro que deseas eliminar la tarea ${label}?`,
    okText: "Eliminar",
    cancelText: "Cancelar",
    danger: true
  });

  if (!ok) return;

  try {
    await apiFetch(`/tasks/${taskId}`, { method: "DELETE" });
    toast("ok", "Tarea eliminada", "Se eliminó correctamente.", 2200);
    setMsg(appMsg, "Tarea eliminada ✅", "ok");
    await loadTasks();
  } catch (err) {
    setMsg(appMsg, "No se pudo eliminar la tarea.", "err");
    toast("err", "Error al eliminar", err.message, 4200);
  }
}

// -------------------- Report --------------------
function renderReport(rows) {
  if (!rows || rows.length === 0) {
    reportBox.innerHTML = `
      <div class="empty">
        <div class="empty-ico">📊</div>
        <div>
          <div class="empty-title">Sin datos para el reporte</div>
          <div class="empty-sub">Crea tareas o espera eventos para ver cambios.</div>
        </div>
      </div>`;
    return;
  }

  const fmt = (d) => {
    if (!d) return "-";
    const dt = new Date(d);
    if (Number.isNaN(dt.getTime())) return String(d);
    return dt.toLocaleString();
  };

  reportBox.innerHTML = `
    <table class="rtable">
      <thead>
        <tr>
          <th>Tarea</th>
          <th>Estado</th>
          <th>Última acción</th>
          <th>Fecha</th>
        </tr>
      </thead>
      <tbody>
        ${rows.map(r => `
          <tr>
            <td>${escapeHtml(r.title || "")}</td>
            <td><span class="badge ${statusClass(r.status)}">${escapeHtml(r.status || "")}</span></td>
            <td>${escapeHtml(r.last_action || "-")}</td>
            <td>${escapeHtml(fmt(r.last_action_at))}</td>
          </tr>
        `).join("")}
      </tbody>
    </table>
  `;
}

// -------------------- WS --------------------
function connectWS() {
  const host = window.location.hostname;
  const ws = new WebSocket(`ws://${host}:8000/ws/reports`);

  ws.onopen = () => console.log("WS conectado");
  ws.onmessage = (ev) => {
    try {
      JSON.parse(ev.data);
      loadTasks();
    } catch {}
  };
  ws.onclose = () => {
    console.log("WS desconectado, reintentando...");
    setTimeout(connectWS, 2000);
  };
}

// -------------------- SSO redirect --------------------
async function goToWebBSSO() {
  const msgBox = appCard.classList.contains("hidden") ? authMsg : appMsg;
  setMsg(msgBox, "");
  clearToasts();

  try {
    const t = getToken();
    if (!t) {
      toast("err", "SSO", "Primero inicia sesión para usar SSO.");
      return;
    }

    const data = await apiFetch("/sso/token", { method: "POST" });
    const ssoToken = data?.sso_token || "";
    if (!ssoToken) throw new Error("El backend no devolvió sso_token.");

    const host = window.location.hostname;
    window.location.href = `http://${host}:8081/sso.html?token=${encodeURIComponent(ssoToken)}`;
  } catch (err) {
    toast("err", "SSO falló", err.message, 4200);
  }
}
if (goSSOBtn) goSSOBtn.addEventListener("click", goToWebBSSO);

// -------------------- Utils --------------------
function escapeHtml(s) {
  return String(s)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

// -------------------- Boot --------------------
(function boot() {
  applyTheme(getSavedTheme());

  // default mode
  syncTopPills();
  requestAnimationFrame(positionUnderline);

  // on resize, keep underline aligned
  window.addEventListener("resize", () => requestAnimationFrame(positionUnderline));

  const token = getToken();
  if (token) {
    showApp("");
    loadTasks();
  } else {
    showAuth();
    setMode("login");
  }

  connectWS();
})();
