const API = `http://${window.location.hostname}:8000`;

function getTokenB() {
  return localStorage.getItem("token_b") || "";
}

function setTokenB(token) {
  localStorage.setItem("token_b", token);
}

async function apiFetchB(path, opts = {}) {
  const headers = opts.headers ? { ...opts.headers } : {};
  headers["Content-Type"] = "application/json";

  const t = getTokenB();
  if (t) headers["Authorization"] = "Bearer " + t;

  const res = await fetch(API + path, { ...opts, headers });
  const txt = await res.text();

  let data = null;
  try { data = txt ? JSON.parse(txt) : null; }
  catch { data = txt; }

  if (!res.ok) {
    const msg = typeof data === "string" ? data : JSON.stringify(data);
    throw new Error(msg);
  }
  return data;
}

function connectWS(eventsBox) {
  const host = window.location.hostname;
  const ws = new WebSocket(`ws://${host}:8000/ws/reports`);

  ws.onopen = () => {
    eventsBox.textContent = "WS conectado\n" + eventsBox.textContent;
    ws.send("ping");
  };

  ws.onmessage = (ev) => {
    eventsBox.textContent = ev.data + "\n" + eventsBox.textContent;
  };

  ws.onclose = () => setTimeout(() => connectWS(eventsBox), 1500);
}

// ✅ SSO consume: si viene ?token=... lo canjea por access_token y guarda token_b
async function tryConsumeSsoToken(statsBox) {
  const url = new URL(window.location.href);
  const ssoToken = url.searchParams.get("token");
  if (!ssoToken) return false;

  try {
    const res = await fetch(API + "/sso/consume", {
      method: "POST",
      headers: { "Content-Type": "application/json" },

      // ✅ CLAVE: esto debe llamarse sso_token
      body: JSON.stringify({ sso_token: ssoToken }),
    });

    const txt = await res.text();
    let data = null;
    try { data = txt ? JSON.parse(txt) : null; }
    catch { data = txt; }

    if (!res.ok) throw new Error(typeof data === "string" ? data : JSON.stringify(data));

    if (!data?.access_token) throw new Error("Respuesta de /sso/consume no trae access_token");

    setTokenB(data.access_token);
    statsBox.textContent = "✅ SSO consumido. token_b guardado.\n" + statsBox.textContent;

    // limpia el token de la URL
    url.searchParams.delete("token");
    window.history.replaceState({}, "", url.toString());

    return true;
  } catch (e) {
    statsBox.textContent = "❌ Error consumiendo SSO: " + e.message + "\n" + statsBox.textContent;
    return false;
  }
}

document.addEventListener("DOMContentLoaded", async () => {
  const eventsBox = document.getElementById("events");
  const statsBox  = document.getElementById("stats");
  const reportBox = document.getElementById("report");

  const btnStats  = document.getElementById("loadStats");
  const btnReport = document.getElementById("loadReport");
  const btnLogin  = document.getElementById("loginNormal");

  if (!eventsBox || !statsBox || !reportBox) {
    console.error("Faltan contenedores: events/stats/report. Revisa los IDs en el HTML.");
    return;
  }

  // 1) consume SSO si vino por URL
  await tryConsumeSsoToken(statsBox);

  // 2) WS
  connectWS(eventsBox);

  // 3) Stats
  if (btnStats) {
    btnStats.addEventListener("click", async () => {
      try {
        const data = await apiFetchB("/reports/access-stats", { method: "GET" });
        statsBox.textContent = JSON.stringify(data, null, 2);
      } catch (e) {
        statsBox.textContent =
          "ERROR: " + e.message + "\n\n" +
          "Tip: Revisa que exista token_b en localStorage (DevTools > Application > Local Storage).";
      }
    });
  }

  // 4) Reporte
  if (btnReport) {
    btnReport.addEventListener("click", async () => {
      try {
        const data = await apiFetchB("/reports/tasks-with-last-change", { method: "GET" });
        reportBox.textContent = JSON.stringify(data, null, 2);
      } catch (e) {
        reportBox.textContent =
          "ERROR: " + e.message + "\n\n" +
          "Esto suele ser 403 si NO hay token_b o el token expiró.";
      }
    });
  }

  // 5) Marca normal
  if (btnLogin) {
    btnLogin.addEventListener("click", async () => {
      try {
        const data = await apiFetchB("/sso/mark-normal", { method: "POST" });
        statsBox.textContent = "Marcado NORMAL_LOGIN: " + JSON.stringify(data);
      } catch (e) {
        statsBox.textContent = "ERROR: " + e.message;
      }
    });
  }
});
