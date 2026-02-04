// Cambia esto si tu backend está en otro host/puerto
const API = "http://localhost:8000"; // URL base del backend (FastAPI)

// Helper para obtener elementos del DOM por id
const el = (id) => document.getElementById(id);

// Referencias a contenedores principales (pantalla auth vs pantalla app)
const authCard = el("authCard"); // Card/section de autenticación (login/registro)
const appCard = el("appCard");   // Card/section principal de la app (tareas/reporte)

// Elementos de tabs/form de autenticación
const tabLogin = el("tabLogin");       // Tab para modo login
const tabRegister = el("tabRegister"); // Tab para modo registro
const authForm = el("authForm");       // Formulario de autenticación
const authSubmit = el("authSubmit");   // Botón submit del formulario
const authMsg = el("authMsg");         // Caja/label para mensajes de auth (errores/ok)

// Inputs del formulario de autenticación
const emailInput = el("email");      // Input email
const passInput = el("password");    // Input password

// Barra superior / sesión
const logoutBtn = el("logoutBtn"); // Botón de cerrar sesión
const whoami = el("whoami");       // Etiqueta para mostrar quién está logueado

// Botones de acciones en la app
const refreshBtn = el("refreshBtn");           // Botón para recargar tareas
const reportBtn = el("reportBtn");             // Botón para cargar reporte combinado
const printReportBtn = el("printReportBtn");   // 👈 NUEVO (requiere botón en HTML) imprimir reporte

// Elementos para crear tarea y mostrar resultados
const createForm = el("createForm"); // Formulario para crear tarea
const newTitle = el("newTitle");     // Input título de nueva tarea
const newDesc = el("newDesc");       // Input descripción de nueva tarea
const newStatus = el("newStatus");   // Select/estado de nueva tarea
const appMsg = el("appMsg");         // Mensajes generales de la app (errores/ok)
const tasksList = el("tasksList");   // Contenedor donde se renderiza el listado de tareas
const reportBox = el("reportBox");   // Contenedor donde se renderiza el reporte

let mode = "login"; // or "register"  // Modo actual del formulario de auth

function setMsg(target, text, kind = "") {
  // Setea un mensaje (texto + clase CSS) en un elemento target
  // kind puede ser "ok", "err" u otros estilos definidos en CSS
  target.className = "msg " + (kind || "");
  target.textContent = text || "";
}

function isUceEmail(email) {
  // Validador simple en frontend: exige correo institucional UCE
  return email.trim().toLowerCase().endsWith("@uce.edu.ec");
}

function getToken() {
  // Obtiene el token JWT guardado en localStorage (si existe)
  return localStorage.getItem("token") || "";
}

function setToken(t) {
  // Guarda el token JWT en localStorage para mantener sesión
  localStorage.setItem("token", t);
}

function clearToken() {
  // Elimina el token de localStorage (logout real)
  localStorage.removeItem("token");
}

function showApp(email = "") {
  // Cambia la UI a "modo app" (oculta auth, muestra app y logout)
  authCard.classList.add("hidden");
  appCard.classList.remove("hidden");
  logoutBtn.classList.remove("hidden");
  whoami.textContent = email ? `Sesión: ${email}` : "Sesión activa";
}

function showAuth() {
  // Cambia la UI a "modo auth" (muestra login/registro, oculta app y logout)
  authCard.classList.remove("hidden");
  appCard.classList.add("hidden");
  logoutBtn.classList.add("hidden");
  whoami.textContent = "";
}

function setMode(next) {
  // Cambia el modo del formulario (login vs register) y actualiza UI del tab/botón
  mode = next;
  tabLogin.classList.toggle("active", mode === "login");
  tabRegister.classList.toggle("active", mode === "register");
  authSubmit.textContent = mode === "login" ? "Entrar" : "Crear cuenta";
  setMsg(authMsg, "");
}

// Cambia de modo con clicks en tabs
tabLogin.addEventListener("click", () => setMode("login"));
tabRegister.addEventListener("click", () => setMode("register"));

async function apiFetch(path, opts = {}) {
  // Wrapper de fetch:
  // - Agrega headers JSON
  // - Agrega Authorization Bearer si hay token
  // - Parsea respuesta (intenta JSON; si no, usa texto)
  // - Si status no es OK, construye un error "bonito" con detail
  const headers = opts.headers || {};
  headers["Content-Type"] = "application/json";

  const token = getToken();
  if (token) headers["Authorization"] = "Bearer " + token;

  const res = await fetch(API + path, { ...opts, headers });

  // intenta leer json si existe
  const text = await res.text();
  let data = null;
  try {
    data = text ? JSON.parse(text) : null;
  } catch {
    data = text;
  }

  if (!res.ok) {
    // ✅ Manejo bonito de errores (evita [object Object])
    let detail = "Error";
    if (data && data.detail !== undefined) {
      if (Array.isArray(data.detail)) {
        // Caso típico de validación FastAPI/Pydantic: detail es lista de errores
        detail = data.detail.map((x) => x.msg).join(" | ");
      } else if (typeof data.detail === "object") {
        // Si detail es objeto, lo stringify para que sea legible
        detail = JSON.stringify(data.detail);
      } else {
        // Si detail es string u otro primitivo, lo convierte a string
        detail = String(data.detail);
      }
    } else if (typeof data === "string") {
      detail = data;
    } else if (data) {
      detail = JSON.stringify(data);
    }
    // Lanza error con status + detalle para mostrarlo en UI
    throw new Error(`${res.status} - ${detail}`);
  }

  return data;
}

// Submit del formulario de auth (login o register dependiendo del modo)
authForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  setMsg(authMsg, "");

  const email = emailInput.value.trim();
  const password = passInput.value;

  // ✅ Validación local: evita 422 del backend
  if (!isUceEmail(email)) {
    setMsg(authMsg, "Usa un correo institucional que termine en @uce.edu.ec", "err");
    return;
  }

  try {
    // Define endpoint según modo actual
    const endpoint = mode === "login" ? "/auth/login" : "/auth/register";

    // Llama API para obtener token
    const data = await apiFetch(endpoint, {
      method: "POST",
      headers: {}, // apiFetch setea headers
      body: JSON.stringify({ email, password })
    });

    // Guarda token y cambia a vista de app
    setToken(data.access_token);
    setMsg(authMsg, "Listo ✅ Token guardado.", "ok");
    showApp(email);
    await loadTasks();
  } catch (err) {
    // Muestra error en el card de auth
    setMsg(authMsg, err.message, "err");
  }
});

// Logout: limpia token + UI
logoutBtn.addEventListener("click", () => {
  clearToken();
  tasksList.innerHTML = "";
  reportBox.innerHTML = "";
  setMsg(appMsg, "");
  showAuth();
});

// Botón recargar tareas
refreshBtn.addEventListener("click", loadTasks);

// Botón cargar reporte combinado (Postgres + Mongo)
reportBtn.addEventListener("click", async () => {
  setMsg(appMsg, "");
  try {
    const rep = await apiFetch("/reports/tasks-with-last-change", { method: "GET" });
    renderReport(rep);
  } catch (err) {
    reportBox.innerHTML = "";
    setMsg(appMsg, "No se pudo cargar reporte: " + err.message, "err");
  }
});

// ✅ Imprimir reporte (requiere botón printReportBtn en HTML)
if (printReportBtn) {
  printReportBtn.addEventListener("click", () => {
    // Toma el HTML del reporte si ya está renderizado, o arma un <pre> con texto plano
    const content = reportBox.innerHTML
      ? reportBox.innerHTML
      : `<pre>${escapeHtml(reportBox.textContent || "")}</pre>`;

    // Abre una ventana nueva para imprimir el contenido de forma limpia
    const w = window.open("", "_blank");

    // Estilos inline mínimos para impresión (tabla/badges)
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

    // Escribe el documento HTML a imprimir y dispara window.print()
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

// Submit para crear tarea
createForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  setMsg(appMsg, "");
  try {
    // Construye payload para el backend
    const payload = {
      title: newTitle.value.trim(),
      description: newDesc.value.trim() || null,
      status: newStatus.value
    };

    // Crea tarea en backend
    const created = await apiFetch("/tasks", { method: "POST", body: JSON.stringify(payload) });

    // Feedback al usuario
    setMsg(appMsg, `Tarea creada ✅ (${created.id})`, "ok");

    // Limpia formulario
    newTitle.value = "";
    newDesc.value = "";
    newStatus.value = "PENDING";

    // Recarga listado
    await loadTasks();
  } catch (err) {
    setMsg(appMsg, err.message, "err");
  }
});

async function loadTasks() {
  // Carga tareas del backend y renderiza el listado
  setMsg(appMsg, "");
  reportBox.innerHTML = "";
  tasksList.innerHTML = `<div class="muted small">Cargando...</div>`;

  try {
    const tasks = await apiFetch("/tasks", { method: "GET" });
    renderTasks(tasks);
  } catch (err) {
    tasksList.innerHTML = "";
    setMsg(appMsg, "No se pudo cargar tareas: " + err.message, "err");

    // Si el token ya no es válido/expiró => vuelve a auth
    if (String(err.message).includes("401")) {
      clearToken();
      showAuth();
    }
  }
}

function renderTasks(tasks) {
  // Renderiza el listado de tareas en el DOM
  if (!tasks || tasks.length === 0) {
    tasksList.innerHTML = `<div class="muted small">No tienes tareas aún. Crea una arriba 👆</div>`;
    return;
  }

  tasksList.innerHTML = "";
  for (const t of tasks) {
    // Crea un bloque por tarea
    const div = document.createElement("div");
    div.className = "item";

    // Inserta HTML de la tarea (escapando texto para evitar XSS)
    div.innerHTML = `
      <div class="item-top">
        <div>
          <div class="item-title">${escapeHtml(t.title)}</div>
          <div class="item-meta">${escapeHtml(t.description || "")}</div>
        </div>
        <div class="badge">${escapeHtml(t.status)}</div>
      </div>
      <div class="item-actions">
        <button class="btn" data-action="status" data-id="${t.id}" data-status="PENDING">PENDING</button>
        <button class="btn" data-action="status" data-id="${t.id}" data-status="IN_PROGRESS">IN_PROGRESS</button>
        <button class="btn" data-action="status" data-id="${t.id}" data-status="DONE">DONE</button>
        <button class="btn danger" data-action="delete" data-id="${t.id}">Eliminar</button>
      </div>
      <div class="muted small">id: ${t.id}</div>
    `;
    tasksList.appendChild(div);
  }

  // Agrega listeners a botones dentro del listado (cambiar estado / eliminar)
  tasksList.querySelectorAll("button").forEach((btn) => {
    btn.addEventListener("click", async () => {
      const action = btn.dataset.action;
      const id = btn.dataset.id;

      if (action === "delete") {
        await deleteTask(id);
      } else if (action === "status") {
        await updateTaskStatus(id, btn.dataset.status);
      }
    });
  });
}

async function updateTaskStatus(taskId, status) {
  // Actualiza el estado de una tarea mediante PUT /tasks/{id}
  setMsg(appMsg, "");
  try {
    const updated = await apiFetch(`/tasks/${taskId}`, {
      method: "PUT",
      body: JSON.stringify({ status })
    });
    setMsg(appMsg, `Estado actualizado ✅ (${updated.status})`, "ok");
    await loadTasks();
  } catch (err) {
    setMsg(appMsg, err.message, "err");
  }
}

async function deleteTask(taskId) {
  // Elimina una tarea mediante DELETE /tasks/{id}
  setMsg(appMsg, "");
  if (!confirm("¿Eliminar esta tarea?")) return;

  try {
    await apiFetch(`/tasks/${taskId}`, { method: "DELETE" });
    setMsg(appMsg, "Tarea eliminada ✅", "ok");
    await loadTasks();
  } catch (err) {
    setMsg(appMsg, err.message, "err");
  }
}

function escapeHtml(s) {
  // Escapa caracteres especiales para prevenir inyección de HTML (XSS) al renderizar strings
  return String(s)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function renderReport(rows) {
  // Renderiza el reporte "tareas + último cambio" como tabla HTML
  if (!rows || rows.length === 0) {
    reportBox.innerHTML = `<div class="muted small">No hay datos para el reporte todavía.</div>`;
    return;
  }

  // Formatea fecha/tiempo para presentación
  const fmt = (d) => {
    if (!d) return "-";
    const dt = new Date(d);
    if (Number.isNaN(dt.getTime())) return String(d);
    return dt.toLocaleString();
  };

  // Construye tabla HTML del reporte
  const html = `
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
            <td><span class="badge">${escapeHtml(r.status || "")}</span></td>
            <td>${escapeHtml(r.last_action || "-")}</td>
            <td>${escapeHtml(fmt(r.last_action_at))}</td>
          </tr>
        `).join("")}
      </tbody>
    </table>
  `;
  reportBox.innerHTML = html;
}

// Auto-login si ya hay token
(function boot() {
  // Inicializa la UI al cargar la página:
  // - por defecto setea modo login
  // - si hay token guardado, muestra la app y carga tareas
  // - si no hay token, muestra pantalla de auth
  setMode("login");
  const token = getToken();
  if (token) {
    showApp("");
    loadTasks();
  } else {
    showAuth();
  }
})();
