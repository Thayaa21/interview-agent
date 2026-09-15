import React from "react";

export default function SessionList({ sessions, activeId, onSelect }) {
  return (
    <div className="session-list">
      <div className="sidebar-title">Sessions</div>
      {sessions.length === 0 && <div className="muted small">No sessions yet.</div>}
      {sessions.map((s) => (
        <button
          key={s.session_id}
          className={`session-item ${s.session_id === activeId ? "active" : ""}`}
          onClick={() => onSelect(s.session_id)}
        >
          <div className="si-name">{s.candidate}</div>
          <div className="si-meta">
            <span>{s.role}</span>
            <span className={`si-status ${s.status}`}>{s.status}</span>
          </div>
          {s.score != null && (
            <div className="si-score">{Math.round(s.score * 100)}%</div>
          )}
        </button>
      ))}
    </div>
  );
}
