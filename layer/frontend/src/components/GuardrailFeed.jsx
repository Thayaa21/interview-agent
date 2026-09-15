import React from "react";

// Live feed of guardrail decisions (input redirects/blocks, output blocks,
// budget hits). This is the visible proof the agent stays in scope.
const VERDICT_LABEL = {
  allow: "Allowed",
  redirect: "Redirected",
  block: "Blocked",
  end: "Ended",
};

export default function GuardrailFeed({ guardrails }) {
  const flagged = guardrails.filter((g) => g.verdict && g.verdict !== "allow");
  if (!flagged.length) {
    return <div className="muted">No guardrail interventions. Agent stayed in scope. ✓</div>;
  }
  return (
    <ul className="guard-feed">
      {flagged.map((g, i) => (
        <li key={i} className={`guard-item ${g.verdict}`}>
          <span className={`guard-badge ${g.verdict}`}>{VERDICT_LABEL[g.verdict]}</span>
          <div className="guard-body">
            <div className="guard-reason">
              {g.stage} · {g.reason}
            </div>
            {g.attempted ? <div className="guard-attempt">blocked: “{g.attempted}”</div> : null}
            {g.replacement ? <div className="guard-repl">said: “{g.replacement}”</div> : null}
          </div>
        </li>
      ))}
    </ul>
  );
}
