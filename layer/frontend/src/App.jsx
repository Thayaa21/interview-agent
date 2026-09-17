import React, { useEffect, useMemo, useRef, useState } from "react";
import { listSessions, getEvents, startMock, openEventStream } from "./api.js";
import Transcript from "./components/Transcript.jsx";
import CriteriaPanel from "./components/CriteriaPanel.jsx";
import GuardrailFeed from "./components/GuardrailFeed.jsx";
import SessionList from "./components/SessionList.jsx";
import LiveCall from "./components/LiveCall.jsx";

export default function App() {
  const [sessions, setSessions] = useState([]);
  const [activeId, setActiveId] = useState(null);
  // eventsBySession: { [sessionId]: Event[] }
  const [eventsBySession, setEventsBySession] = useState({});
  const [candidate, setCandidate] = useState("Candidate");
  const [role, setRole] = useState("oncology_rn");
  const wsRef = useRef(null);

  // Live event stream.
  useEffect(() => {
    refreshSessions();
    const ws = openEventStream((ev) => {
      setEventsBySession((prev) => {
        const list = prev[ev.session_id] ? [...prev[ev.session_id], ev] : [ev];
        return { ...prev, [ev.session_id]: list };
      });
      if (ev.type === "session_start") {
        refreshSessions();
        setActiveId((cur) => cur || ev.session_id);
      }
      if (ev.type === "session_end") refreshSessions();
    });
    wsRef.current = ws;
    return () => ws && ws.close();
  }, []);

  async function refreshSessions() {
    setSessions(await listSessions());
  }

  async function selectSession(id) {
    setActiveId(id);
    if (!eventsBySession[id]) {
      const evs = await getEvents(id);
      setEventsBySession((prev) => ({ ...prev, [id]: evs }));
    }
  }

  async function onStartMock() {
    const { session_id } = await startMock(candidate, role);
    setActiveId(session_id);
    setEventsBySession((prev) => ({ ...prev, [session_id]: [] }));
  }

  // Events coming from the REAL LiveKit agent (data messages), merged into the
  // same per-session event list the panels render.
  function pushLiveEvent(ev) {
    const sid = ev.session_id;
    if (!sid) return;
    ev.id = ev.id || `live_${Date.now()}_${Math.random().toString(36).slice(2, 7)}`;
    setEventsBySession((prev) => {
      const list = prev[sid] ? [...prev[sid], ev] : [ev];
      return { ...prev, [sid]: list };
    });
    setActiveId((cur) => cur || sid);
  }

  const activeEvents = eventsBySession[activeId] || [];
  const active = sessions.find((s) => s.session_id === activeId);

  const analyses = useMemo(
    () => activeEvents.filter((e) => e.type === "analysis").map((e) => e.payload),
    [activeEvents]
  );
  const guardrails = useMemo(
    () => activeEvents.filter((e) => e.type === "guardrail").map((e) => e.payload),
    [activeEvents]
  );
  const overall = useMemo(() => {
    if (!analyses.length) return null;
    return analyses.reduce((a, x) => a + (x.score || 0), 0) / analyses.length;
  }, [analyses]);

  return (
    <div className="app">
      <header className="topbar">
        <div className="brand">
          <span className="dot" /> Soliant Interview Agent · Live
        </div>
        <div className="controls">
          <input value={candidate} onChange={(e) => setCandidate(e.target.value)} />
          <select value={role} onChange={(e) => setRole(e.target.value)}>
            <option value="oncology_rn">Oncology RN</option>
            <option value="staff_pharmacist">Staff Pharmacist</option>
          </select>
          <LiveCall
            role={role}
            onEvent={pushLiveEvent}
            onSessionId={(id) => {
              setActiveId(id);
              setEventsBySession((prev) => ({ ...prev, [id]: prev[id] || [] }));
            }}
          />
          <button className="mock-btn" onClick={onStartMock}>▶ Mock call</button>
        </div>
      </header>

      <div className="layout">
        <aside className="sidebar">
          <SessionList sessions={sessions} activeId={activeId} onSelect={selectSession} />
        </aside>

        <main className="main">
          {!activeId ? (
            <div className="empty">Click "📞 Talk to agent" to start a live voice interview, or "▶ Mock call" to replay a scripted one.</div>
          ) : (
            <>
              <div className="session-head">
                <div>
                  <h2>{active?.candidate || "…"}</h2>
                  <div className="muted">
                    {active?.role} · {active?.status || "active"}
                  </div>
                </div>
                {overall != null && (
                  <div className={`score-badge ${scoreClass(overall)}`}>
                    {Math.round(overall * 100)}%
                    <span>overall</span>
                  </div>
                )}
              </div>

              <div className="panels">
                <section className="panel transcript-panel">
                  <h3>Transcript</h3>
                  <Transcript events={activeEvents} />
                </section>

                <section className="panel">
                  <h3>Answer → JD criteria</h3>
                  <CriteriaPanel analyses={analyses} />
                </section>

                <section className="panel">
                  <h3>Guardrails</h3>
                  <GuardrailFeed guardrails={guardrails} />
                </section>
              </div>
            </>
          )}
        </main>
      </div>
    </div>
  );
}

function scoreClass(s) {
  if (s >= 0.7) return "good";
  if (s >= 0.4) return "mid";
  return "low";
}
