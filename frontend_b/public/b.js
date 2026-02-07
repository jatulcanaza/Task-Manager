// =======================================================
// Web B - b.js (SSO + Dashboard reports + Access logging)
//   AUTH (JWT/SSO)  -> http://HOST:8000
//   B (reports/ws) -> http://HOST:8002
// =======================================================

const HOST = window.location.hostname;

const AUTH_BASE_DEFAULT = `http://${HOST}:8000`;
const API_B_DEFAULT = `http://${HOST}:8002`;

// ===== Token storage (B) =====
function getTokenB() {
  const t = localStorage.getItem("token_b") || "";
  if (t === "undefined" || t === "null") return "";
  return t;
}
function setTokenB(token) {
  if (!token || token === "undefined" || token === "null") return;
  localStorage.setItem("token_b", token);
}
function clearTokenB() {
  localStorage.removeItem("token_b");
}

// ===== Utils =====
function qs(name) {
  const u = new URL(window.location.href);
  return u.searchParams.get(name) || "";
}

function parseBody(text) {
  let data = null;
  try {
    data = text ? JSON.parse(text) : null;
  } catch {
    data = text;
  }
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

async function apiFetchB(path, opts = {}, apiBase = API_B_DEFAULT) {
  const headers = opts.headers ? { ...opts.headers } : {};
  headers["Content-Type"] = "application/json";

  const t = getTokenB();
  if (t) headers["Authorization"] = "Bearer " + t;

  const res = await fetch(apiBase + path, { ...opts, headers });

  const txt = await res.text();
  const data = parseBody(txt);

  if (!res.ok) throw new Error(normalizeError(res, data));
  return data;
}

// ===== Web B: registrar accesos =====
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

// ===== SSO page (token-gated) =====
async function handleSSOPage({
  authBase = AUTH_BASE_DEFAULT,
  apiBaseB = API_B_DEFAULT,
  onStatus = null,
} = {}) {
  const sso = qs("token");

  if (!sso) {
    window.location.href = "/login.html";
    return;
  }

  try {
    onStatus && onStatus("Validando SSO token…", "");

    const data = await apiPost(authBase, "/sso/consume", { sso_token: sso });
    const access = data?.access_token || "";
    if (!access) throw new Error("Respuesta de /sso/consume sin access_token");

    setTokenB(access);

    // ✅ registrar en Mongo B
    await logAccessB("SSO_TOKEN", apiBaseB);

    // limpiar token de URL
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

// ===== WebSocket =====
function connectWS(eventsBox, wsBase = null, onEvent = null) {
  const host = window.location.hostname;
  const wsUrl = wsBase || `ws://${host}:8002/ws/reports`;
  const ws = new WebSocket(wsUrl);

  ws.onopen = () => {
    if (eventsBox) eventsBox.textContent = "WS conectado\n" + (eventsBox.textContent || "");

    // keep-alive cada 25s
    ws._ka = setInterval(() => {
      try { ws.send("ping"); } catch {}
    }, 25000);
  };

  ws.onmessage = (ev) => {
    if (eventsBox) eventsBox.textContent = ev.data + "\n" + (eventsBox.textContent || "");
    if (onEvent) onEvent(ev.data);
  };

  ws.onclose = () => {
    try { clearInterval(ws._ka); } catch {}
    setTimeout(() => connectWS(eventsBox, wsBase, onEvent), 1500);
  };
}

// ===== Dashboard init =====
function initDashboard({ apiBase = API_B_DEFAULT, wsBase = null } = {}) {
  document.addEventListener("DOMContentLoaded", () => {
    if (!getTokenB()) {
      window.location.href = "/login.html";
      return;
    }

    const eventsBox = document.getElementById("events");
    const statsBox = document.getElementById("stats");
    const reportBox = document.getElementById("report");

    const btnStats = document.getElementById("loadStats");
    const btnReport = document.getElementById("loadReport");

    async function refreshStats() {
      const stats = await apiFetchB("/reports/access-stats", { method: "GET" }, apiBase);
      if (statsBox) statsBox.textContent = JSON.stringify(stats, null, 2);
    }

    async function refreshReport() {
      const rpt = await apiFetchB("/reports/tasks-with-last-change", { method: "GET" }, apiBase);
      if (reportBox) reportBox.textContent = JSON.stringify(rpt, null, 2);
    }

    // ✅ WS: cada evento refresca TODO (reporte automático)
    connectWS(eventsBox, wsBase, async () => {
      try { await refreshStats(); } catch {}
      try { await refreshReport(); } catch {}
    });

    if (btnStats) {
      btnStats.addEventListener("click", async () => {
        try {
          await refreshStats();
        } catch (e) {
          statsBox.textContent = "ERROR: " + e.message;
          if (String(e.message).includes("401") || String(e.message).includes("403")) {
            clearTokenB();
            window.location.href = "/login.html";
          }
        }
      });
    }

    if (btnReport) {
      btnReport.addEventListener("click", async () => {
        try {
          await refreshReport();
        } catch (e) {
          reportBox.textContent = "ERROR: " + e.message;
          if (String(e.message).includes("401") || String(e.message).includes("403")) {
            clearTokenB();
            window.location.href = "/login.html";
          }
        }
      });
    }
  });
}

// Exponer
window.handleSSOPage = handleSSOPage;
window.initDashboard = initDashboard;
window.logAccessB = logAccessB;
window.apiFetchB = apiFetchB;
