import React from "react";

// Shows, per answered question, how the candidate's answer mapped to the JD
// behavioral criteria: status chip + confidence + evidence.
const STATUS_LABEL = {
  met: "Met",
  partial: "Partial",
  not_met: "Not met",
  not_addressed: "Not addressed",
};

export default function CriteriaPanel({ analyses }) {
  if (!analyses.length) {
    return <div className="muted">No answers analyzed yet.</div>;
  }
  return (
    <div className="criteria">
      {analyses.map((a, i) => (
        <div key={`${a.question_id}-${i}`} className="crit-card">
          <div className="crit-head">
            <span className="crit-q">{a.question_text}</span>
            <span className={`score-pill ${band(a.score)}`}>
              {Math.round((a.score || 0) * 100)}%
            </span>
          </div>
          <div className="crit-summary">{a.summary}</div>
          <ul className="crit-list">
            {a.criteria.map((c) => (
              <li key={c.criterion_id}>
                <span className={`chip ${c.status}`}>{STATUS_LABEL[c.status]}</span>
                <span className="crit-label">{c.label}</span>
                <span className="crit-conf">{Math.round((c.confidence || 0) * 100)}%</span>
                {c.evidence ? <div className="crit-ev">“{c.evidence}”</div> : null}
              </li>
            ))}
          </ul>
        </div>
      ))}
    </div>
  );
}

function band(s) {
  if (s >= 0.7) return "good";
  if (s >= 0.4) return "mid";
  return "low";
}
