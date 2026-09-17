# Soliant AI Voice Interview Agent
### Automated first-round screening that talks, listens, and evaluates — in real time

---

## Page 1 — The Opportunity

**The problem**
Recruiters spend hours on repetitive first-round phone screens. Candidates wait
days for a callback. Screening quality varies from recruiter to recruiter.

**Our solution**
An AI voice agent that conducts the first-round interview automatically:
- Calls or connects with the candidate and holds a **natural spoken conversation**
- Asks the **right questions for the role** and adapts with follow-ups
- **Scores each answer** against the job's criteria, live
- Keeps a full transcript and evaluation for the recruiter

**The result:** faster screening, consistent quality, recruiters focused on the
best candidates — at a fraction of the time and cost.

---

## Page 2 — How It Works (Pipeline)

A candidate speaks; the agent hears, thinks, and responds in real time.

```
  Candidate (browser or phone)
        │  voice
        ▼
  Speech-to-Text  →  AI Interviewer (GPT-4o)  →  Text-to-Speech
     (Deepgram)        decides what to ask         (Cartesia, natural voice)
        │
        ▼
  Live Dashboard:  transcript  •  guardrail checks  •  answer scoring
```

- **Hears** the candidate accurately (streaming speech recognition)
- **Thinks** like an interviewer — greets, asks, reacts, follows up
- **Speaks** in a warm, human-sounding voice
- **Shows everything live** on a recruiter dashboard

Built on **LiveKit** — the same pipeline works over a **web browser today** and a
**phone call** when needed, with no rebuild.

---

## Page 3 — Architecture (at a glance)

```
   ┌─────────────┐     ┌──────────────────────┐     ┌────────────────┐
   │  Candidate  │────▶│   Real-time Voice     │────▶│   Recruiter    │
   │  (mic)      │◀────│   Interview Engine    │◀────│   Dashboard    │
   └─────────────┘     └──────────────────────┘     └────────────────┘
                                │
                    ┌───────────┴───────────┐
                    ▼                       ▼
          ┌──────────────────┐    ┌────────────────────┐
          │  Guardrail Layer  │    │  Scoring Layer      │
          │  (stays on-topic) │    │  (answer → JD fit)  │
          └──────────────────┘    └────────────────────┘
```

- **Voice engine** — real-time conversation (speech in, AI, voice out).
- **Guardrail layer** — keeps the agent strictly on the interview.
- **Scoring layer** — maps every answer to the role's required competencies.
- **Dashboard** — recruiters watch the transcript, guardrails, and scores live.

Everything is **role-aware** and **configurable** — new roles and questions are
added by editing simple config, not code.

---

## Page 4 — What Makes Us Different: The Guardrails

Most AI agents drift off-topic or can be tricked. Ours don't.

**The problem with others**
- Keyword filters wrongly block real answers (a nurse says "diagnosis" → flagged).
- "Please stay on topic" in the prompt fades as the conversation grows.

**Our approach — intelligent, rule-based guardrails**
- A single **rulebook** defines what's allowed vs. not — one source of truth.
- The AI judges every candidate turn by **intent, not keywords** — it knows
  clinical talk is fine, but "give me a recipe" is not.
- It tells apart **off-topic** (gently redirect) from a **hijack attempt**
  ("act as a different assistant" → hard block).
- Every decision is **visible on the dashboard** — you can *see* it stay in scope.

**Why it matters:** in regulated fields like healthcare, "trust me, it stays on
topic" isn't enough. We *show* it, every turn.

---

## Page 5 — Value & Roadmap

**Value today**
- ⏱️ **Faster screening** — automated first round, available 24/7
- 🎯 **Consistent & fair** — every candidate gets the same structured interview
- 📊 **Instant evaluation** — answers scored against the role, live
- 🔒 **On-topic & safe** — intent-based guardrails, fully observable
- 💬 **Human-feeling** — natural voice and conversation, not a rigid bot

**Where we are**
- Working live: browser voice interview, guardrail detection, criteria scoring,
  recruiter dashboard — on real infrastructure.

**Roadmap**
- Phone (inbound & outbound) calling at scale
- Guardrail enforcement (from live monitoring to hard control)
- Post-call candidate reports & recruiter summaries
- Expanded role library and analytics

---

*Soliant — healthcare & education staffing. Built to screen more candidates,
faster, without losing the human touch.*
