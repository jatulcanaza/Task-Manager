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

document.addEventListener("DOMContentLoaded", async () => {
  const eventsBox = document.getElementById("events");
  const statsBox  = document.getElementById("stats");
  const reportBox = document.getElementById("report");

  const btnStats  = document.getElementById("loadStats");
  const btnReport = document.getElementById("loadReport");

  if (!eventsBox || !statsBox || !reportBox) {
    console.error("Faltan contenedores: events/stats/report. Revisa los IDs en el HTML.");
    return;
  }

  connectWS(eventsBox);

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
});
