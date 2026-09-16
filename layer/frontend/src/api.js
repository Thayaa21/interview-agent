// Tiny API client for the dashboard backend.

export async function listSessions() {
  const r = await fetch("/api/sessions");
  return r.json();
}

export async function getEvents(sessionId) {
  const r = await fetch(`/api/sessions/${sessionId}/events`);
  return r.json();
}

export async function startMock(candidate, role, speed = 4.0) {
  const r = await fetch("/api/mock/start", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ candidate, role, speed }),
  });
  return r.json();
}

export async function getRulebook() {
  const r = await fetch("/api/rulebook");
  return r.json();
}

export async function getRoles() {
  const r = await fetch("/api/roles");
  return r.json();
}

// Live browser call ("Call me").
export async function startCall(candidate, role) {
  const r = await fetch("/api/call/start", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ candidate, role }),
  });
  return r.json();
}

export async function sendAnswer(sessionId, text) {
  const r = await fetch("/api/call/answer", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ session_id: sessionId, text }),
  });
  return r.json();
}

// Open a WebSocket to the live event stream. onEvent(event) per message.
export function openEventStream(onEvent) {
  const proto = location.protocol === "https:" ? "wss" : "ws";
  const ws = new WebSocket(`${proto}://${location.host}/ws`);
  ws.onmessage = (m) => {
    try {
      onEvent(JSON.parse(m.data));
    } catch (_) {}
  };
  return ws;
}
