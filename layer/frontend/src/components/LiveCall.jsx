import React from "react";
import { useLiveCall } from "../useLiveCall.js";

// "Talk to agent" control — connects the browser to the REAL LiveKit agent
// (Deepgram STT + GPT-4o + Cartesia TTS). Events from the agent (turns,
// guardrails, analysis) flow through onEvent into the dashboard panels.
const STATUS_TEXT = {
  idle: "Ready",
  connecting: "Connecting…",
  connected: "🎙️ Live — talk to the agent",
  ended: "Call ended",
  error: "Error",
};

export default function LiveCall({ role, onEvent, onSessionId }) {
  const { status, error, sessionId, connect, disconnect, audioElRef } = useLiveCall({ onEvent });
  const live = status === "connected" || status === "connecting";

  React.useEffect(() => {
    if (sessionId) onSessionId && onSessionId(sessionId);
  }, [sessionId, onSessionId]);

  return (
    <div className="call-panel">
      <div className="call-row">
        {!live ? (
          <button className="call-btn" onClick={() => connect(role)}>
            📞 Talk to agent
          </button>
        ) : (
          <button className="call-btn end" onClick={disconnect}>
            ■ End call
          </button>
        )}
        <span className={`call-status ${status}`}>{STATUS_TEXT[status] || status}</span>
      </div>
      {error ? <div className="call-error">{error}</div> : null}
      <div ref={audioElRef} style={{ display: "none" }} />
    </div>
  );
}
