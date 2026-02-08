// =======================================================
// Web B - b.js
//
// Responsabilidades:
// - Manejo de autenticación (SSO y login normal)
// - Almacenamiento de token de Web B (sessionStorage)
// - Comunicación con:
//      AUTH  -> http://HOST:8000
//      B API -> http://HOST:8002
// - WebSocket para eventos en tiempo real
// - Inicialización del Dashboard
// =======================================================


// ---------------------------------------------------------------------
// BASES DINÁMICAS SEGÚN HOST ACTUAL
// ---------------------------------------------------------------------
const HOST = window.location.hostname;

// Servicio AUTH (login / SSO)
const AUTH_BASE_DEFAULT = `http://${HOST}:8000`;

// Servicio Web B (reportes, WS, accesos)
const API_B_DEFAULT = `http://${HOST}:8002`;


// =====================================================================
// TOKEN STORAGE (WEB B)
// =====================================================================
// Decisión de seguridad:
// - Se usa sessionStorage (NO localStorage)
// - El token se borra al cerrar pestaña/navegador
// - Reduce riesgo ante XSS persistente

function getTokenB() {
  const t = sessionStorage.getItem("token_b") || "";
  // Protección ante valores inválidos serializados
  if (t === "undefined" || t === "null") return "";
  return t;
}

function setTokenB(token) {
  if (!token || token === "undefined" || token === "null") return;
  sessionStorage.setItem("token_b", token);
}

function clearTokenB() {
  sessionStorage.removeItem("token_b");
}

// Logout centralizado de Web B
function logoutB() {
  clearTokenB();
  // Redirige siempre a login normal
  window.location.href = "/login.html";
}


// =====================================================================
// UTILIDADES GENERALES
// =====================================================================

// Obtener query string param (?token=...)
function qs(name) {
  const u = new URL(window.location.href);
  return u.searchParams.get(name) || "";
}

// Parseo tolerante de body (JSON o texto)
function parseBody(text) {
  let data = null;
  try {
    data = text ? JSON.parse(text) : null;
  } catch {
    data = text;
  }
  return data;
}

// Normaliza errores devueltos por FastAPI
function normalizeError(res, data) {
  if (data && typeof data === "object" && data.detail !== undefined) {
    // Caso FastAPI: detail puede ser string o array
    if (Array.isArray(data.detail)) {
      return `${res.status} - ${data.detail
        .map((x) => x.msg || JSON.stringify(x))
        .join(" | ")}`;
    }
    return `${res.status} - ${
      typeof data.detail === "string"
        ? data.detail
        : JSON.stringify(data.detail)
    }`;
  }
  if (typeof data === "string") return `${res.status} - ${data}`;
  return `${res.status} - ${JSON.stringify(data)}`;
}


// =====================================================================
// HELPERS HTTP
// =====================================================================

// POST genérico (sin token, usado para AUTH / SSO)
async function apiPost(base, path, body) {
  const res = await fetch(base + path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });

  const txt = await res.text();
  const data = parseBody(txt);

  if (!res.ok) throw new Error(normalizeError(res, data));
  return data;
}

// Fetch autenticado contra Web B
async function apiFetchB(path, opts = {}, apiBase = API_B_DEFAULT) {
  const headers = opts.headers ? { ...opts.headers } : {};
  headers["Content-Type"] = "application/json";

  // Si hay token, se envía como Bearer
  const t = getTokenB();
  if (t) headers["Authorization"] = "Bearer " + t;

  const res = await fetch(apiBase + path, { ...opts, headers });

  const txt = await res.text();
  const data = parseBody(txt);

  if (!res.ok) throw new Error(normalizeError(res, data));
  return data;
}


// =====================================================================
// WEB B: REGISTRO DE ACCESOS (Mongo B)
// =====================================================================
// Se llama cada vez que:
// - Login normal
// - Login por SSO
async function logAccessB(access_type, apiBase = API_B_DEFAULT) {
  return apiFetchB(
    "/b/log-access",
    {
      method: "POST",
      body: JSON.stringify({ access_type }),
    },
    apiBase
  );
}


// =====================================================================
// SSO PAGE HANDLER
// =====================================================================
// Se ejecuta SOLO en la página sso.html
//
// Flujo:
// 1) Lee token SSO desde URL
// 2) Llama a AUTH /sso/consume
// 3) Guarda access_token en sesión
// 4) Registra acceso SSO en Mongo B
// 5) Limpia URL
// 6) Redirige al dashboard
async function handleSSOPage({
  authBase = AUTH_BASE_DEFAULT,
  apiBaseB = API_B_DEFAULT,
  onStatus = null,
} = {}) {
  const sso = qs("token");

  // Si no hay token SSO → login normal
  if (!sso) {
    window.location.href = "/login.html";
    return;
  }

  try {
    onStatus && onStatus("Validando SSO token…", "");

    // Consumir token SSO en AUTH
    const data = await apiPost(authBase, "/sso/consume", { sso_token: sso });
    const access = data?.access_token || "";
    if (!access) throw new Error("Respuesta sin access_token");

    // Guardar token SOLO en sesión
    setTokenB(access);

    // Registrar acceso tipo SSO_TOKEN en Mongo B
    await logAccessB("SSO_TOKEN", apiBaseB);

    // Limpiar token de la URL (seguridad)
    const u = new URL(window.location.href);
    u.searchParams.delete("token");
    window.history.replaceState({}, "", u.toString());

    onStatus && onStatus("SSO OK ✅ Redirigiendo al dashboard…", "ok");
    setTimeout(() => (window.location.href = "/dashboard.html"), 500);

  } catch (e) {
    clearTokenB();
    onStatus && onStatus("SSO inválido/expirado. Redirigiendo a login…", "err");
    setTimeout(() => (window.location.href = "/login.html"), 900);
  }
}


// =====================================================================
// WEBSOCKET (EVENTOS EN TIEMPO REAL)
// =====================================================================
// - Se conecta a /ws/reports
// - Reintenta automáticamente si se cae
// - Mantiene keep-alive
function connectWS(eventsBox, wsBase = null, onEvent = null) {
  const host = window.location.hostname;
  const wsUrl = wsBase || `ws://${host}:8002/ws/reports`;
  const ws = new WebSocket(wsUrl);

  ws.onopen = () => {
    if (eventsBox)
      eventsBox.textContent =
        "WS conectado\n" + (eventsBox.textContent || "");

    // keep-alive cada 25s
    ws._ka = setInterval(() => {
      try { ws.send("ping"); } catch {}
    }, 25000);
  };

  ws.onmessage = (ev) => {
    if (eventsBox)
      eventsBox.textContent =
        ev.data + "\n" + (eventsBox.textContent || "");
    if (onEvent) onEvent(ev.data);
  };

  ws.onclose = () => {
    try { clearInterval(ws._ka); } catch {}
    // Reintento automático
    setTimeout(() => connectWS(eventsBox, wsBase, onEvent), 1500);
  };
}


// =====================================================================
// DASHBOARD INITIALIZATION
// =====================================================================
// Se ejecuta SOLO en dashboard.html
//
// Responsabilidades:
// - Verificar sesión
// - Conectar WS
// - Cargar reportes y stats
// - Manejar logout
function initDashboard({ apiBase = API_B_DEFAULT, wsBase = null } = {}) {
  document.addEventListener("DOMContentLoaded", () => {

    // Seguridad: si no hay token → login
    if (!getTokenB()) {
      window.location.href = "/login.html";
      return;
    }

    // Referencias DOM
    const eventsBox = document.getElementById("events");
    const statsBox = document.getElementById("stats");
    const reportBox = document.getElementById("report");

    const btnStats = document.getElementById("loadStats");
    const btnReport = document.getElementById("loadReport");
    const btnLogout = document.getElementById("logoutB");

    // Cargar estadísticas de accesos
    async function refreshStats() {
      const stats = await apiFetchB(
        "/reports/access-stats",
        { method: "GET" },
        apiBase
      );
      if (statsBox) statsBox.textContent = JSON.stringify(stats, null, 2);
    }

    // Cargar reporte combinado
    async function refreshReport() {
      const rpt = await apiFetchB(
        "/reports/tasks-with-last-change",
        { method: "GET" },
        apiBase
      );
      if (reportBox) reportBox.textContent = JSON.stringify(rpt, null, 2);
    }

    // Logout
    if (btnLogout) {
      btnLogout.addEventListener("click", () => logoutB());
    }

    // WS: cada evento refresca stats + reporte
    connectWS(eventsBox, wsBase, async () => {
      try { await refreshStats(); } catch {}
      try { await refreshReport(); } catch {}
    });

    // Botón stats manual
    if (btnStats) {
      btnStats.addEventListener("click", async () => {
        try {
          await refreshStats();
        } catch (e) {
          if (statsBox) statsBox.textContent = "ERROR: " + e.message;
          if (String(e.message).includes("401") || String(e.message).includes("403")) {
            logoutB();
          }
        }
      });
    }

    // Botón reporte manual
    if (btnReport) {
      btnReport.addEventListener("click", async () => {
        try {
          await refreshReport();
        } catch (e) {
          if (reportBox) reportBox.textContent = "ERROR: " + e.message;
          if (String(e.message).includes("401") || String(e.message).includes("403")) {
            logoutB();
          }
        }
      });
    }
  });
}


// =====================================================================
// EXPORTS GLOBALES
// =====================================================================
window.handleSSOPage = handleSSOPage;
window.initDashboard = initDashboard;
window.logAccessB = logAccessB;
window.apiFetchB = apiFetchB;
window.logoutB = logoutB;
