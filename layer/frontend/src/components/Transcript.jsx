import React, { useEffect, useRef } from "react";

// Renders the running transcript: agent + candidate turns, plus inline
// guardrail markers, in event order. Auto-scrolls as new turns arrive.
export default function Transcript({ events }) {
  const endRef = useRef(null);
  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [events.length]);

  const rows = events.filter(
    (e) => e.type === "turn" || e.type === "guardrail"
  );

  return (
    <div className="transcript">
      {rows.map((e) => {
        if (e.type === "guardrail") {
          return (
            <div key={e.id} className={`t-guard ${e.payload.verdict}`}>
              guardrail · {e.payload.stage} · {e.payload.verdict} ({e.payload.reason})
            </div>
          );
        }
        const { speaker, kind, text } = e.payload;
        return (
          <div key={e.id} className={`bubble ${speaker}`}>
            <div className="bubble-meta">
              {speaker}
              {kind ? ` · ${kind}` : ""}
            </div>
            <div className="bubble-text">{text}</div>
          </div>
        );
      })}
      <div ref={endRef} />
    </div>
  );
}
