// =======================================================
// Web A - app.js
//
// Arquitectura (microservicios):
//   AUTH (JWT/SSO)  -> http://HOST:8000   (login/register + emitir token SSO)
//   A (tasks CRUD)  -> http://HOST:8001   (crear/listar/editar/eliminar tareas)
//   B (reports/ws)  -> http://HOST:8002   (reportes + websocket de eventos)
//
// Nota:
// - Este archivo NO hace render con frameworks.
// - Usa IDs del DOM (index.html) como "contract" de UI.
// =======================================================


// ---------------------------------------------------------------------
// BASE URLS (dinámicas según el host donde se abre el frontend)
// ---------------------------------------------------------------------
const HOST = window.location.hostname;
const AUTH_API = `http://${HOST}:8000`; // login/register/sso token
const A_API    = `http://${HOST}:8001`; // tasks
const B_API    = `http://${HOST}:8002`; // reports + ws (si tu reporte está en B)

// Helper corto para obtener elementos por id
const el = (id) => document.getElementById(id);


// =====================================================================
// REFERENCIAS DOM (contrato con index.html)
// =====================================================================

// Containers principales: vista auth vs vista app
const authCard = el("authCard");
const appCard = el("appCard");

// Auth: tabs y elementos del formulario
const tabLogin = el("tabLogin");                 // tabs legacy (ocultos en HTML)
const tabRegister = el("tabRegister");
const tabLoginTop = el("tabLoginTop");           // tabs UI visibles (píldoras)
const tabRegisterTop = el("tabRegisterTop");

const authForm = el("authForm");
const authSubmit = el("authSubmit");
const authMsg = el("authMsg");

const emailInput = el("email");
const passInput = el("password");
const showPass = el("showPass");

// Labels y underline dinámico del header de auth
const signinLabel = el("signinLabel");
const signupLabel = el("signupLabel");
const authUnderline = el("authUnderline");

// Theme
const themeToggle = el("themeToggle");

// Topbar
const logoutBtn = el("logoutBtn"); // botón salir (solo cuando hay sesión)
const whoami = el("whoami");       // indicador de sesión/usuario

// Acciones de la app
const refreshBtn = el("refreshBtn");
const reportBtn = el("reportBtn");
const printReportBtn = el("printReportBtn");
const goSSOBtn = el("goSSOBtn");

// Create + listas
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

// SSO panel (URL editable/copiable)
const ssoUrl = el("ssoUrl");
const copySsoUrlBtn = el("copySsoUrlBtn");
const openSsoUrlBtn = el("openSsoUrlBtn");

// Estado de modo auth: "login" o "register"
let mode = "login";


// =====================================================================
// THEME (LIGHT/DARK) - persistencia localStorage
// =====================================================================
function applyTheme(theme) {
  const root = document.documentElement;
  const isDark = theme === "dark";

  // CSS dark activado por data-theme
  if (isDark) root.setAttribute("data-theme", "dark");
  else root.removeAttribute("data-theme");

  // Accesibilidad del switch
  if (themeToggle) themeToggle.setAttribute("aria-pressed", isDark ? "true" : "false");

  // Cambia icono en el header
  const label = document.querySelector(".theme-label");
  if (label) label.textContent = isDark ? "☀️" : "🌙";
}

function getSavedTheme() {
  return localStorage.getItem("theme") || "light";
}

function toggleTheme() {
  // Alterna tema y reposiciona underline (por cambios de layout)
  const cur = getSavedTheme();
  const next = cur === "dark" ? "light" : "dark";
  localStorage.setItem("theme", next);
  applyTheme(next);
  requestAnimationFrame(positionUnderline);
}


// =====================================================================
// UI HELPERS (mensajes, loading, validación visual)
// =====================================================================

// Setea mensaje en un contenedor y clase de estado (ok/err)
function setMsg(target, text, kind = "") {
  target.className = "msg " + (kind || "");
  target.textContent = text || "";
}

// Estado loading para botones (disable + spinner + cambio de texto)
function setLoading(button, loading, textLoading = "Cargando...") {
  if (!button) return;
  button.disabled = loading;
  button.classList.toggle("loading", !!loading);

  const t = button.querySelector(".btn-text");
  if (!t) return;

  // Guarda texto original para restaurarlo
  if (!button.dataset._txt) button.dataset._txt = t.textContent;
  t.textContent = loading ? textLoading : button.dataset._txt;
}

// Marca inputs con estilo de error
function markInvalid(inputEl, isInvalid) {
  if (!inputEl) return;
  inputEl.classList.toggle("input-err", !!isInvalid);
}

// Limpia campos y estado del login/registro
function clearAuthFields() {
  emailInput.value = "";
  passInput.value = "";
  if (showPass) showPass.checked = false;
  passInput.type = "password";
  markInvalid(emailInput, false);
  markInvalid(passInput, false);
  setMsg(authMsg, "");
}

// Limpia mensajes de la app
function clearAppMessages() {
  setMsg(appMsg, "");
}

// Limpia toasts (si quieres “resetear” feedback)
function clearToasts() {
  if (toastHost) toastHost.innerHTML = "";
}


// =====================================================================
// TOASTS (notificaciones flotantes)
// =====================================================================
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

  // Auto-cierre
  if (timeoutMs > 0) {
    setTimeout(() => {
      if (node && node.parentNode) node.remove();
    }, timeoutMs);
  }
}


// =====================================================================
// MODAL (confirmación custom para eliminar tareas)
// =====================================================================
// Reemplaza confirm() del navegador por:
// - Mejor UI
// - Mejor control
// - Accesibilidad básica (escape + click afuera)
function openModal({
  title = "Confirmar",
  message = "¿Seguro?",
  okText = "Aceptar",
  cancelText = "Cancelar",
  danger = false
}) {
  return new Promise((resolve) => {
    // Setear textos
    modalTitle.textContent = title;
    modalBody.textContent = message;

    modalOk.textContent = okText;
    modalCancel.textContent = cancelText;

    // Danger (estilo rojo) para acciones destructivas
    modalOk.classList.toggle("danger", !!danger);

    // Mostrar modal
    modalOverlay.classList.remove("hidden");
    modalOverlay.setAttribute("aria-hidden", "false");

    // Cleanup para evitar leaks de handlers
    const cleanup = () => {
      modalOverlay.classList.add("hidden");
      modalOverlay.setAttribute("aria-hidden", "true");
      modalClose.onclick = null;
      modalCancel.onclick = null;
      modalOk.onclick = null;
      modalOverlay.onclick = null;
      document.removeEventListener("keydown", escHandler);
    };

    // Cerrar con Escape
    const escHandler = (e) => {
      if (e.key === "Escape") {
        cleanup();
        resolve(false);
      }
    };

    // Botones
    modalClose.onclick = () => { cleanup(); resolve(false); };
    modalCancel.onclick = () => { cleanup(); resolve(false); };
    modalOk.onclick = () => { cleanup(); resolve(true); };

    // Click fuera del modal también cancela
    modalOverlay.onclick = (e) => {
      if (e.target === modalOverlay) {
        cleanup();
        resolve(false);
      }
    };

    document.addEventListener("keydown", escHandler);
  });
}


// =====================================================================
// VALIDACIONES (frontend)
// =====================================================================

// Verifica correo institucional
function isUceEmail(email) {
  return email.trim().toLowerCase().endsWith("@uce.edu.ec");
}

// Contraseña fuerte: 8 chars, 1 mayúscula, 1 número
function isStrongPassword(p) {
  if (!p || p.length < 8) return false;
  const hasUpper = /[A-Z]/.test(p);
  const hasNum = /[0-9]/.test(p);
  return hasUpper && hasNum;
}

// Clase CSS según estado de tarea (badges)
function statusClass(status) {
  if (status === "PENDING") return "status-pending";
  if (status === "IN_PROGRESS") return "status-progress";
  if (status === "DONE") return "status-done";
  return "";
}


// =====================================================================
// TOKEN HELPERS (Web A) - sessionStorage por seguridad
// =====================================================================
// Decisión:
/// - sessionStorage reduce persistencia del token (tipo banca)
function getToken() {
  const t = sessionStorage.getItem("token") || "";
  if (t === "undefined" || t === "null") return "";
  return t;
}
function setToken(t) {
  if (!t || t === "undefined" || t === "null") return;
  sessionStorage.setItem("token", t);
}
function clearToken() {
  sessionStorage.removeItem("token");
}


// =====================================================================
// VIEW HELPERS: cambiar entre auth y app
// =====================================================================
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

// Sincroniza UI de tabs “píldora” con el modo
function syncTopPills() {
  tabLoginTop.classList.toggle("active", mode === "login");
  tabRegisterTop.classList.toggle("active", mode === "register");

  signinLabel.className = mode === "login" ? "auth-head-strong" : "auth-head-muted";
  signupLabel.className = mode === "register" ? "auth-head-strong" : "auth-head-muted";

  // Cambia texto del botón submit según modo
  authSubmit.querySelector(".btn-text").textContent =
    mode === "login" ? "Entrar" : "Registrar";
}

// Cambia modo y resetea UI
function setMode(next) {
  mode = next;

  tabLogin.classList.toggle("active", mode === "login");
  tabRegister.classList.toggle("active", mode === "register");

  clearAuthFields();
  clearToasts();

  syncTopPills();
  requestAnimationFrame(positionUnderline);
}

// Reposiciona underline bajo el label activo (login/register)
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


// =====================================================================
// API WRAPPER (fetch + JSON + errores FastAPI)
// =====================================================================
function parseBody(text) {
  let data = null;
  try { data = text ? JSON.parse(text) : null; }
  catch { data = text; }
  return data;
}

function normalizeError(res, data) {
  if (data && typeof data === "object" && data.detail !== undefined) {
    if (Array.isArray(data.detail)) {
      return `${res.status} - ${data.detail.map((x) => x.msg || JSON.stringify(x)).join(" | ")}`;
    }
    return `${res.status} - ${typeof data.detail === "string" ? data.detail : JSON.stringify(data.detail)}`;
  }
  if (typeof data === "string") return `${res.status} - ${data}`;
  return `${res.status} - ${JSON.stringify(data)}`;
}

// apiFetch(base, path, opts): wrapper con Authorization Bearer automático
async function apiFetch(base, path, opts = {}) {
  const headers = opts.headers ? { ...opts.headers } : {};
  headers["Content-Type"] = "application/json";

  // Adjunta token si existe
  const token = getToken();
  if (token) headers["Authorization"] = "Bearer " + token;

  const res = await fetch(base + path, { ...opts, headers });

  const text = await res.text();
  const data = parseBody(text);

  if (!res.ok) throw new Error(normalizeError(res, data));
  return data;
}


// =====================================================================
// SHAKE: animación para invalidaciones (UX)
// =====================================================================
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


// =====================================================================
// EVENTOS UI (tabs, theme, show password)
// =====================================================================
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


// =====================================================================
// AUTH SUBMIT (login o registro)
// =====================================================================
authForm.addEventListener("submit", async (e) => {
  e.preventDefault();

  clearToasts();
  setMsg(authMsg, "");

  // Normalización inputs
  const email = emailInput.value.trim().toLowerCase();
  const password = passInput.value || "";

  // Validación UI
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

  // Si hay errores → shake y salir
  if (!ok) {
    shake(authCard);
    return;
  }

  // ------------------- LOGIN -------------------
  if (mode === "login") {
    setLoading(authSubmit, true, "Entrando...");
    try {
      // Llama al microservicio AUTH: /auth/login
      const data = await apiFetch(AUTH_API, "/auth/login", {
        method: "POST",
        body: JSON.stringify({ email, password }),
      });

      // Soporta varias posibles formas de respuesta (robustez)
      const access =
        data?.access_token ||
        data?.token ||
        data?.jwt ||
        data?.data?.access_token ||
        "";

      if (!access) throw new Error("No se recibió access_token del backend. Revisa /auth/login.");

      // Guardar token en sessionStorage
      setToken(access);

      // Feedback + transición a app
      setMsg(authMsg, "Listo ✅ Sesión iniciada.", "ok");
      toast("ok", "Sesión iniciada", "Bienvenido. Cargando tus tareas…", 2200);

      showApp(email);

      // Cargar tareas al iniciar sesión
      await loadTasks();
    } catch (err) {
      setMsg(authMsg, "No se pudo iniciar sesión.", "err");
      toast("err", "Error al iniciar sesión", err.message, 4200);
    } finally {
      setLoading(authSubmit, false);
    }

  // ------------------- REGISTER -------------------
  } else {
    setLoading(authSubmit, true, "Registrando...");
    try {
      // Registro en AUTH: /auth/register
      // Importante: NO inicia sesión automático (decisión de UX/seguridad)
      await apiFetch(AUTH_API, "/auth/register", {
        method: "POST",
        body: JSON.stringify({ email, password }),
      });

      toast("ok", "Registro exitoso", "Ahora puedes iniciar sesión con tu cuenta.", 3800);
      setMsg(authMsg, "Registro exitoso ✅", "ok");

      // Limpia y vuelve a modo login
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


// =====================================================================
// LOGOUT (Web A)
// =====================================================================
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


// =====================================================================
// REFRESH TASKS (botón)
// =====================================================================
refreshBtn.addEventListener("click", loadTasks);


// =====================================================================
// REPORT (reporte combinado vive en B:8002)
// =====================================================================
reportBtn.addEventListener("click", async () => {
  clearToasts();
  setMsg(appMsg, "");
  setLoading(reportBtn, true, "Cargando...");
  try {
    // Llama al microservicio B: /reports/tasks-with-last-change
    const rep = await apiFetch(B_API, "/reports/tasks-with-last-change", { method: "GET" });
    renderReport(rep);
  } catch (err) {
    reportBox.innerHTML = "";
    setMsg(appMsg, "No se pudo cargar el reporte.", "err");
    toast("err", "No se pudo cargar el reporte", err.message, 4200);
  } finally {
    setLoading(reportBtn, false);
  }
});


// =====================================================================
// PRINT REPORT (abre ventana e imprime)
// =====================================================================
if (printReportBtn) {
  printReportBtn.addEventListener("click", () => {
    // Usa HTML renderizado o texto del reporte
    const content = reportBox.innerHTML
      ? reportBox.innerHTML
      : `<pre>${escapeHtml(reportBox.textContent || "")}</pre>`;

    const w = window.open("", "_blank");

    // CSS mínimo para impresión
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


// =====================================================================
// CREATE TASK (POST /tasks en A:8001)
// =====================================================================
createForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  clearToasts();
  setMsg(appMsg, "");

  const title = (newTitle.value || "").trim();

  // Validación de título
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
    // Payload de creación
    const payload = {
      title,
      description: (newDesc.value || "").trim() || null,
      status: newStatus.value,
    };

    // Llama a A:8001 /tasks
    const created = await apiFetch(A_API, "/tasks", {
      method: "POST",
      body: JSON.stringify(payload),
    });

    toast("ok", "Tarea creada", `Se creó la tarea: ${created.title || created.id}`, 2600);
    setMsg(appMsg, "Tarea creada ✅", "ok");

    // Reset form
    newTitle.value = "";
    newDesc.value = "";
    newStatus.value = "PENDING";

    // Refresh lista
    await loadTasks();

  } catch (err) {
    setMsg(appMsg, "No se pudo crear la tarea.", "err");
    toast("err", "Error al crear tarea", err.message, 4200);
  } finally {
    setLoading(createBtn, false);
  }
});


// =====================================================================
// TASKS: load + render + actions
// =====================================================================
async function loadTasks() {
  clearToasts();
  setMsg(appMsg, "");
  tasksList.innerHTML = `<div class="muted small">Cargando…</div>`;
  setLoading(refreshBtn, true, "Actualizando...");

  try {
    // GET tasks desde A:8001
    const tasks = await apiFetch(A_API, "/tasks", { method: "GET" });
    renderTasks(tasks);

  } catch (err) {
    tasksList.innerHTML = "";
    setMsg(appMsg, "No se pudo cargar tareas.", "err");
    toast("err", "No se pudo cargar tareas", err.message, 4200);

    // Si el token expira o es inválido → volver a login
    if (String(err.message).includes("401") || String(err.message).includes("403")) {
      clearToken();
      showAuth();
      setMode("login");
    }
  } finally {
    setLoading(refreshBtn, false);
  }
}

function renderTasks(tasks) {
  // Estado vacío
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

  // Render listado
  tasksList.innerHTML = "";

  for (const t of tasks) {
    const div = document.createElement("div");
    div.className = "item";

    // Render seguro (escapeHtml) para evitar inyección HTML
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

  // Bind handlers a todos los botones generados
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


// ---------------------------------------------------------------------
// UPDATE STATUS (PUT /tasks/{id} en A:8001)
// ---------------------------------------------------------------------
async function updateTaskStatus(taskId, status, btn) {
  clearToasts();
  setMsg(appMsg, "");
  setLoading(btn, true, "...");

  try {
    const updated = await apiFetch(A_API, `/tasks/${taskId}`, {
      method: "PUT",
      body: JSON.stringify({ status }),
    });

    toast("ok", "Estado actualizado", `Nuevo estado: ${updated.status}`, 2200);
    setMsg(appMsg, `Estado actualizado ✅ (${updated.status})`, "ok");
    await loadTasks();

  } catch (err) {
    setMsg(appMsg, "No se pudo actualizar el estado.", "err");
    toast("err", "Error al actualizar", err.message, 4200);
  } finally {
    // Restaurar texto original del botón
    setLoading(btn, false, btn.dataset._txt || "");
  }
}


// ---------------------------------------------------------------------
// DELETE TASK (DELETE /tasks/{id} en A:8001)
// ---------------------------------------------------------------------
async function deleteTask(taskId, title) {
  clearToasts();
  setMsg(appMsg, "");

  const label = title ? `"${title}"` : taskId;

  // Modal de confirmación antes de eliminar
  const ok = await openModal({
    title: "Eliminar tarea",
    message: `¿Seguro que deseas eliminar la tarea ${label}?`,
    okText: "Eliminar",
    cancelText: "Cancelar",
    danger: true,
  });

  if (!ok) return;

  try {
    await apiFetch(A_API, `/tasks/${taskId}`, { method: "DELETE" });
    toast("ok", "Tarea eliminada", "Se eliminó correctamente.", 2200);
    setMsg(appMsg, "Tarea eliminada ✅", "ok");
    await loadTasks();
  } catch (err) {
    setMsg(appMsg, "No se pudo eliminar la tarea.", "err");
    toast("err", "Error al eliminar", err.message, 4200);
  }
}


// =====================================================================
// REPORT RENDER (tabla HTML a partir de DTO del backend B)
// =====================================================================
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

  // Formatea fecha ISO a hora local del navegador
  const fmt = (d) => {
    if (!d) return "-";
    const dt = new Date(d);
    if (Number.isNaN(dt.getTime())) return String(d);
    return dt.toLocaleString();
  };

  // Render como tabla
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


// =====================================================================
// WEBSOCKET (event-driven refresh)
// =====================================================================
// Conecta a B:8002/ws/reports
// Cuando llegan eventos (task.created/updated/deleted), recarga tareas
function connectWS() {
  const host = window.location.hostname;
  const ws = new WebSocket(`ws://${host}:8002/ws/reports`);

  ws.onopen = () => console.log("WS conectado");

  ws.onmessage = (ev) => {
    try {
      // Si llega JSON válido, asumimos evento
      JSON.parse(ev.data);
      loadTasks(); // recarga la lista automáticamente
    } catch {}
  };

  ws.onclose = () => {
    console.log("WS desconectado, reintentando...");
    setTimeout(connectWS, 2000);
  };
}


// =====================================================================
// SSO: GENERAR URL PARA WEB B (sin login normal allá)
// =====================================================================
async function goToWebBSSO() {
  // Decide dónde mostrar el mensaje (depende si estás en app o auth)
  const msgBox = appCard.classList.contains("hidden") ? authMsg : appMsg;
  setMsg(msgBox, "");
  clearToasts();

  try {
    const t = getToken();
    if (!t) {
      toast("err", "SSO", "Primero inicia sesión para usar SSO.");
      return;
    }

    // 1) Pedir SSO token al AUTH (válido 2 min)
    // Este endpoint requiere Bearer token (se adjunta en apiFetch automáticamente)
    const data = await apiFetch(AUTH_API, "/sso/token", { method: "POST" });
    const ssoToken = data?.sso_token || "";
    if (!ssoToken) throw new Error("El backend no devolvió sso_token.");

    // 2) Construir URL a Web B (puerto 8081) con el token en query param
    const url = `http://${HOST}:8081/sso.html?token=${encodeURIComponent(ssoToken)}`;

    // 3) Mostrarla en el input editable
    if (ssoUrl) ssoUrl.value = url;

    toast("ok", "SSO listo", "URL generada. Puedes editar el token y abrir Web B.", 3200);
  } catch (err) {
    toast("err", "SSO falló", err.message, 4200);
  }
}
if (goSSOBtn) goSSOBtn.addEventListener("click", goToWebBSSO);


// =====================================================================
// COPIAR URL (Clipboard API + fallback)
// =====================================================================
async function copyTextSafe(text) {
  // 1) Clipboard API moderna
  if (navigator.clipboard && typeof navigator.clipboard.writeText === "function") {
    await navigator.clipboard.writeText(text);
    return true;
  }

  // 2) Fallback clásico (textarea + execCommand)
  const ta = document.createElement("textarea");
  ta.value = text;
  ta.setAttribute("readonly", "");
  ta.style.position = "fixed";
  ta.style.left = "-9999px";
  document.body.appendChild(ta);
  ta.select();
  const ok = document.execCommand("copy");
  document.body.removeChild(ta);
  return ok;
}

if (copySsoUrlBtn) {
  copySsoUrlBtn.addEventListener("click", async () => {
    const url = ssoUrl?.value || "";
    if (!url) return toast("err", "Copiar", "No hay URL todavía. Genera una primero.");

    try {
      const ok = await copyTextSafe(url);
      if (!ok) throw new Error("No se pudo copiar automáticamente. Copia manualmente con Ctrl+C.");
      toast("ok", "Copiado", "URL copiada al portapapeles.", 2000);
    } catch (e) {
      toast("err", "Copiar", e.message, 3500);
    }
  });
}


// =====================================================================
// ABRIR URL (en nueva pestaña)
// =====================================================================
if (openSsoUrlBtn) {
  openSsoUrlBtn.addEventListener("click", () => {
    const url = ssoUrl?.value || "";
    if (!url) return toast("err", "Abrir", "No hay URL todavía. Genera una primero.");
    // noopener,noreferrer: mejora seguridad (evita window.opener)
    window.open(url, "_blank", "noopener,noreferrer");
  });
}


// =====================================================================
// ESCAPE HTML (evita inyección XSS en renderTasks/report)
// =====================================================================
function escapeHtml(s) {
  return String(s)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}


// =====================================================================
// BOOT (inicio de la app)
// =====================================================================
(function boot() {
  // Aplica tema guardado
  applyTheme(getSavedTheme());

  // Sincroniza tabs y underline visual
  syncTopPills();
  requestAnimationFrame(positionUnderline);

  // Mantener underline correcto ante resize
  window.addEventListener("resize", () => requestAnimationFrame(positionUnderline));

  // Si ya existe token en sesión → entrar directo a app
  const token = getToken();
  if (token) {
    showApp("");
    loadTasks();
  } else {
    showAuth();
    setMode("login");
  }

  // Conectar WS para actualizaciones automáticas
  connectWS();
})();
