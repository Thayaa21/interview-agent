import React from "react";
import { useVoiceCall, isVoiceSupported } from "../useVoiceCall.js";

// "Call me" voice panel: click to start talking to the agent in the browser.
// Uses the browser mic (speech-to-text) and speaker (text-to-speech).
const STATUS_TEXT = {
  idle: "Ready",
  speaking: "🔊 Agent speaking…",
  listening: "🎤 Listening — go ahead",
  thinking: "… thinking",
  done: "Call ended",
  error: "Error",
};

export default function CallPanel({ candidate, role, onSessionId }) {
  const { status, partial, error, start, stop, supported } = useVoiceCall({ onSessionId });
  const active = status !== "idle" && status !== "done" && status !== "error";

  return (
    <div className="call-panel">
      {!supported && (
        <div className="call-warn">
          Voice needs Chrome or Edge (Web Speech API). You can still use "Start
          mock call" to see the pipeline.
        </div>
      )}
      <div className="call-row">
        {!active ? (
          <button className="call-btn" disabled={!supported} onClick={() => start(candidate, role)}>
            📞 Call me
          </button>
        ) : (
          <button className="call-btn end" onClick={stop}>
            ■ End call
          </button>
        )}
        <span className={`call-status ${status}`}>{STATUS_TEXT[status] || status}</span>
      </div>
      {partial ? <div className="call-partial">“{partial}”</div> : null}
      {error ? <div className="call-error">{error}</div> : null}
    </div>
  );
}
