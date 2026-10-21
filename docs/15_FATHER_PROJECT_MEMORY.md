# 15 — FATHER PROJECT MEMORY / DECISION HISTORY

**Status:** platform architecture / mandatory production-memory contract  
**Purpose:** preserve the full development process while a project is active and publish a compact, human-readable memory after approval/release.

---

# 1. Core principle

During development FATHER records the process in detail.

After approval FATHER does NOT delete that history.

Instead it creates two layers:

\`\`\`text
LAYER 1 — FULL MANUFACTURING HISTORY
  immutable events, versions, analyses, decisions, risks, costs,
  defects, tests, evidence, rejected alternatives

LAYER 2 — PROJECT MEMORY
  concise explanation of what was implemented,
  why it was chosen,
  what alternatives were rejected,
  what constraints mattered,
  what should trigger reconsideration
\`\`\`

The first layer is for audit, reconstruction and learning.

The second layer is for humans who return to the project months or years later.

---

# 2. Development-time capture

While a project is active, FATHER should automatically preserve:

- stage opened/closed;
- artifact created/updated;
- specialist analysis;
- decision and rationale;
- alternative considered;
- rejected alternative and reason;
- risk discovered;
- security/compliance impact;
- cost estimate changes;
- blockers;
- gate calculation;
- return to previous stage;
- architecture/implementation decisions;
- defect/failure;
- fix;
- test/evaluation;
- evidence;
- release decision;
- production feedback.

No important production decision should exist only in chat.

---

# 3. Decision record

Every material decision should answer:

\`\`\`text
WHAT WAS DECIDED?
WHY?
WHO DECIDED?
WHICH INPUTS/EVIDENCE?
WHICH ALTERNATIVES?
WHY WERE THEY REJECTED?
WHAT TRADE-OFF WAS ACCEPTED?
WHAT DOES THIS AFFECT?
WHEN SHOULD THIS BE REVISITED?
\`\`\`

Minimum fields:

- decision_id;
- project_id;
- stage_id;
- title;
- context;
- decision;
- rationale;
- alternatives;
- rejected_reasons;
- constraints;
- evidence_refs;
- owner;
- reviewers;
- cost_impact;
- security_impact;
- operational_impact;
- status;
- effective_from;
- revisit_triggers.

---

# 4. Project Memory Release

When a project reaches an approved/released state, FATHER generates a compact:

\`PROJECT_MEMORY.md\`

and machine-readable:

\`project_memory.json\`

This is NOT a replacement for the full Manufacturing KB history.

It is a stable summary pinned to the approved release/version.

---

# 5. Project Memory content

## 5.1 What was built
Short description of the final implemented object.

## 5.2 Why it was needed
Original problem/value.

## 5.3 Final solution
What was actually implemented, not what was originally proposed.

## 5.4 Why this solution
Key reasons for choosing it.

## 5.5 Rejected alternatives
Short list of serious alternatives and why they were not chosen.

## 5.6 Key constraints
Security, legal, cost, schedule, infrastructure, compatibility, team, data.

## 5.7 Important trade-offs
What we gained and what we intentionally sacrificed.

## 5.8 Security / compliance result
What materially changed the design.

## 5.9 Cost result
Estimated vs actual major cost drivers.

## 5.10 Known limitations
What the solution still does not solve.

## 5.11 Lessons learned
Reusable conclusions.

## 5.12 Revisit triggers
Conditions under which the old decision should be reviewed again.

Examples:
- vendor price changed;
- regulation changed;
- load grew x10;
- security model changed;
- component became unsupported;
- new certified alternative appeared;
- project scope changed;
- repeated production incident occurred.

## 5.13 Key evidence
Links to decisive tests, documents, gates and production evidence.

---

# 6. Lifecycle

\`\`\`text
PROJECT CREATED
  ↓
FULL EVENT CAPTURE
  ↓
STAGE DECISIONS
  ↓
GATES / REWORK / TESTS
  ↓
APPROVED RELEASE
  ↓
PROJECT MEMORY DRAFT
  ↓
OWNER + RELEVANT SPECIALISTS REVIEW
  ↓
PROJECT MEMORY RELEASE
  ↓
PIN TO RELEASE
  ↓
FUTURE MAINTENANCE / NEW DECISIONS
  ↓
NEW MEMORY VERSION WHEN MATERIAL CHANGE OCCURS
\`\`\`

---

# 7. Statuses

Project Memory statuses:

\`\`\`text
NOT_READY
DRAFT
IN_REVIEW
APPROVED
SUPERSEDED
ARCHIVED
\`\`\`

An active pre-design project normally has no APPROVED Project Memory yet.

---

# 8. UI

For an active project:

\`\`\`text
PROJECT
  [Current State]
  [Stages]
  [Documents]
  [Decisions]
  [History]
  [Manufacturing Experience]
\`\`\`

For an approved/released project add a prominent:

\`\`\`text
[ WHY WE BUILT IT THIS WAY ]
\`\`\`

Opening it shows:

- What was built
- Why
- Main decisions
- Rejected alternatives
- Constraints
- Trade-offs
- Lessons
- Revisit triggers
- Key evidence

A second button:

\`[ FULL HISTORY ]\`

opens Manufacturing KB history.

---

# 9. Project list after completion

Completed projects remain visible in FATHER.

Their card should show:

\`\`\`text
PROJECT NAME
STATUS: RELEASED / OPERATIONS / ARCHIVED
LAST APPROVED VERSION
WHAT IT DOES
WHY THIS WAY
KEY LIMITATION
LAST REVIEW DATE
REVISIT TRIGGER STATUS
\`\`\`

The user should not need to open dozens of old documents just to understand the project.

---

# 10. Rejected decisions are valuable knowledge

FATHER must keep rejected alternatives because future conditions can change.

Example:

\`\`\`text
2026:
Option B rejected because license cost was too high.

2028:
Vendor changed licensing.

→ FATHER can surface:
"Previously rejected option may now be worth reconsidering."
\`\`\`

Therefore:
\`REJECTED != DELETED\`

---

# 11. Relationship with Manufacturing KB

\`\`\`text
MANUFACTURING KB
  = complete production memory

PROJECT MEMORY
  = approved human-readable digest of that memory

PROJECT REGISTRY
  = current/latest project identity and state
\`\`\`

---

# 12. Canonical rule

\`\`\`text
NO MATERIAL DECISION WITHOUT RATIONALE.

NO APPROVED PROJECT WITHOUT PROJECT MEMORY.

NO PROJECT MEMORY WITHOUT LINKS TO ORIGINAL EVIDENCE.
\`\`\`

---

# 13. Initial adoption

Use the mechanism for:

- FATHER-ACADEMY-OSINT-001
- LIFE-001

During development both projects accumulate full history.

Their concise Project Memory becomes APPROVED only after an approved/released implementation exists.
