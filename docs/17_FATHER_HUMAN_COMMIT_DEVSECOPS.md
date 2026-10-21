# 17 — FATHER HUMAN COMMIT & DEVSECOPS WORKFLOW

**Status:** mandatory engineering protocol  
**Purpose:** keep Git history readable for humans and make every material change traceable through DevSecOps/Security evidence.

---

# 1. Human commit rule

A commit message must explain the engineering change to a person who opens the history months later.

Bad:

\`\`\`text
update
fix
changes
docs
final
try again
stuff
\`\`\`

Good:

\`\`\`text
docs(projects): add project memory rationale
sec(academy): define security context for OSINT training
feat(registry): add project portfolio records
test(gate): cover missing-evidence failure path
fix(runtime): preserve state after restart
\`\`\`

---

# 2. Commit format

Preferred subject:

\`\`\`text
<type>(<scope>): <human-readable result>
\`\`\`

Recommended types:

- feat
- fix
- docs
- sec
- test
- refactor
- chore
- perf
- build
- ci
- ops
- revert

Rules:

- subject is concise;
- subject describes result, not activity;
- one logical change per commit;
- no fake words such as "final" when the work is not truly final;
- do not include secrets, personal data or sensitive runtime values;
- avoid machine-generated noise;
- use a body only when rationale or risk is not obvious from the subject.

Recommended body when needed:

\`\`\`text
Why:
- ...

Impact:
- ...

Evidence:
- ...
\`\`\`

The body should remain short and useful.

---

# 3. Commit size principle

\`\`\`text
TOO SMALL:
format-only noise split into many meaningless commits

TOO LARGE:
multiple unrelated decisions hidden in one commit

RIGHT:
one coherent engineering change with one understandable reason
\`\`\`

Commit boundaries should follow logical production units:
document, schema, gate, test, fix, integration, protocol, release evidence.

---

# 4. DevSecOps workflow

\`\`\`text
ISSUE / STAGE TASK
        ↓
FEATURE BRANCH
        ↓
CHANGE
        ↓
LOCAL VALIDATION
        ↓
SECURITY / QUALITY CHECKS
        ↓
COMMIT
        ↓
PUSH
        ↓
PR / REVIEW WHEN REQUIRED
        ↓
CI EVIDENCE
        ↓
GATE
        ↓
MERGE ONLY AFTER AUTHORIZED APPROVAL
\`\`\`

---

# 5. Mandatory checks by change type

## Documentation / schemas
- syntax/parse check where applicable;
- broken-reference check where available;
- schema validation;
- no secrets;
- traceability references.

## Python/backend
- formatting/lint where configured;
- unit tests;
- integration tests where relevant;
- SAST;
- SCA;
- secret scan;
- dependency/lock verification.

## Frontend
- build;
- lint;
- tests;
- dependency scan;
- secret scan;
- generated bundle sanity.

## Containers / IaC / Kubernetes
- syntax/validate;
- image/IaC scan;
- dependency/base-image review;
- secrets check;
- SBOM/provenance where applicable.

## Release
- test summary;
- security summary;
- known risks;
- rollback path;
- evidence refs;
- explicit release gate.

---

# 6. Security rules

Never:

- commit .env with secrets;
- commit API tokens;
- commit Telegram sessions;
- commit private keys;
- bypass a failed gate by changing status manually;
- mark NOT_RUN as PASS;
- delete failed evidence to make history clean;
- merge because "it probably works";
- use blanket reset/clean/stash on unrelated user work.

---

# 7. Evidence rule

Every important commit should be connectable to one or more of:

- StageRun
- ArtifactVersion
- DecisionRecord
- RiskFinding
- GateResult
- TestReport
- SecurityReport
- EvidenceManifest

For major changes:

\`\`\`text
COMMIT
  ↓
CHECKS
  ↓
EVIDENCE
  ↓
GATE
\`\`\`

No evidence means no green gate.

---

# 8. Review discipline

Review should ask:

1. Does the change match the approved stage requirement?
2. Does it introduce an undocumented decision?
3. Is security impact understood?
4. Is rollback possible?
5. Are tests/evidence sufficient?
6. Does it change scope?
7. Does it introduce a new dependency/license?
8. Does Manufacturing KB need a lesson/decision record?

---

# 9. Branch discipline

- active work uses a dedicated branch;
- main/default branch is not changed casually;
- branch names describe the work;
- unrelated user changes are not reset, cleaned or rewritten;
- merge requires explicit authorization when required by project policy;
- release/approved state must point to an immutable commit/tag/ref.

Examples:

\`\`\`text
feature/alina-osint-academy-v01
feature/father-project-registry-v01
fix/osint-runtime-restart
sec/academy-tool-permissions
\`\`\`

---

# 10. Commit message examples for FATHER

\`\`\`text
docs(factory): define manufacturing knowledge base

feat(projects): add portfolio registry with active projects

docs(memory): add approved project rationale template

sec(academy): define trust boundaries and protected assets

ci(security): require secret scan before release gate

test(academy): prove mastery cannot change without evaluation

fix(state): restore training run after process restart

ops(evidence): record release rollback proof
\`\`\`

---

# 11. Canonical rules

\`\`\`text
HUMAN-READABLE HISTORY
ONE LOGICAL CHANGE PER COMMIT
NO SECRET IN GIT
NO PASS WITHOUT EVIDENCE
NO MERGE WITHOUT REQUIRED REVIEW
NO SILENT SCOPE CHANGE
NO DEVSECOPS GREEN WITHOUT CHECKS
\`\`\`
