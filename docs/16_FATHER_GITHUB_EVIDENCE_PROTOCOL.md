# 16 — FATHER GITHUB EVIDENCE / PRODUCTION PROTOCOL

**Status:** mandatory prototype protocol  
**Purpose:** use GitHub as the production protocol and evidence index for every FATHER project stage, while keeping secrets, sensitive data and oversized artifacts out of the repository.

---

# 1. Core rule

Every material production action must leave a traceable GitHub record.

This does NOT mean that every raw byte must be committed.

\`\`\`text
MATERIAL ACTION / DECISION / TEST / GATE
        ↓
GITHUB RECORD REQUIRED
        ↓
DIRECT ARTIFACT
or
MANIFEST + HASH + LOCATION + ACCESS POLICY
\`\`\`

GitHub is the protocol-of-record for:

- stage status;
- documents;
- specialist analyses;
- decisions and rationale;
- risks;
- budget changes;
- DevSecOps checks;
- security checks;
- tests;
- evidence;
- gate results;
- defects/fixes;
- release approvals;
- project memory.

---

# 2. Storage decision

Before adding an artifact, evaluate:

\`\`\`text
SIZE
SENSITIVITY
REPRODUCIBILITY VALUE
AUDIT VALUE
CHANGE FREQUENCY
LICENSE / DISTRIBUTION RIGHTS
\`\`\`

Then choose one mode.

## MODE A — COMMIT DIRECTLY

Use for small, non-sensitive, reviewable artifacts:

- Markdown;
- YAML;
- JSON;
- schemas;
- source code;
- test code;
- small logs;
- summaries;
- SBOM manifests;
- scan reports without secrets;
- decision records;
- gate reports;
- hashes/manifests.

## MODE B — COMMIT POINTER / MANIFEST

Use when raw material is:

- large;
- sensitive;
- binary-heavy;
- frequently regenerated;
- restricted by license;
- unsuitable for repository history.

GitHub stores:

- artifact_id;
- filename/type;
- size;
- sha256;
- storage_location;
- source;
- classification;
- owner;
- access rule;
- produced_by;
- stage;
- related test/gate;
- retention;
- version;
- verification status.

## MODE C — DO NOT STORE CONTENT

Never commit:

- passwords;
- API keys;
- access tokens;
- private keys;
- Telegram session files;
- .env with secrets;
- raw credentials;
- prohibited personal/sensitive data;
- restricted material without authorization.

GitHub stores only a safe metadata/evidence record where appropriate.

---

# 3. Internal size policy

The thresholds are FATHER policy, not GitHub platform limits, and may be changed centrally.

Default prototype policy:

\`\`\`text
SMALL      <= 1 MiB     → normally commit directly
MEDIUM     >1 to 10 MiB → commit only when review/audit value justifies it
LARGE      >10 MiB      → prefer manifest/pointer or managed artifact storage
VERY LARGE / DATASET    → manifest + hash + controlled external storage
\`\`\`

Sensitivity overrides size.

A 2 KiB secret is never committed.

A 50 MiB public evidence package may still be stored externally if repository history would not benefit from the raw payload.

---

# 4. Project protocol layout

Recommended project structure:

\`\`\`text
projects/<project_id>/
├── project.yaml
├── pre_design/
├── stages/
│   ├── 00_idea/
│   ├── 01_product/
│   ├── 02_security/
│   ├── 03_compliance/
│   ├── 04_ba/
│   ├── 05_sa/
│   ├── 06_requirements/
│   ├── 07_architecture/
│   ├── 08_development/
│   ├── 09_test_eval/
│   └── 10_operations/
├── decisions/
├── risks/
├── costs/
├── devsecops/
├── security/
├── evidence/
│   ├── manifests/
│   ├── reports/
│   └── indexes/
├── gates/
├── defects/
├── releases/
└── memory/
\`\`\`

The exact physical layout may evolve, but the logical object types remain stable.

---

# 5. Stage protocol

Each stage must expose a protocol summary:

\`\`\`text
STAGE_ID
STATUS
OWNER
INPUT_ARTIFACTS
OUTPUT_ARTIFACTS
SPECIALIST_ANALYSIS
OPEN_RISKS
COST_IMPACT
DEVSECOPS_STATUS
SECURITY_STATUS
TEST_STATUS
EVIDENCE_REFS
GATE_STATUS
BLOCKERS
NEXT_OWNER
\`\`\`

The FATHER UI should render its stage pictogram from this state.

---

# 6. DevSecOps evidence

Every applicable stage/release must be able to link to evidence for:

- branch/ref;
- commit SHA;
- pull request/review;
- build result;
- unit tests;
- integration tests;
- SAST;
- SCA;
- secret scan;
- license scan;
- SBOM;
- artifact provenance;
- dependency lock/pin state;
- container scan when applicable;
- IaC/Kubernetes scan when applicable;
- image digest when applicable;
- deployment evidence;
- rollback evidence;
- release gate.

Statuses must be explicit:

\`\`\`text
NOT_APPLICABLE
NOT_RUN
RUNNING
PASS
FAIL
BLOCKED
WAIVED_WITH_APPROVAL
\`\`\`

Missing evidence must never render as PASS.

---

# 7. Security evidence

Information Security / DevSecOps Security should be able to link:

- Security Context;
- Data Classification;
- Authority/Action Matrix;
- Risk Register;
- Security Constraints;
- Budget Envelope;
- threat/security analysis;
- exceptions;
- residual-risk decisions;
- security test results;
- approved waivers;
- security release decision.

Every waiver must identify:

- owner;
- rationale;
- scope;
- expiry/review date;
- compensating control if any;
- evidence;
- revisit trigger.

---

# 8. Evidence manifest

When raw evidence is not committed, create an Evidence Manifest.

Required fields:

\`\`\`text
evidence_id
project_id
stage_id
artifact_type
name
version
size_bytes
sha256
classification
storage_mode
storage_location
owner
created_at
producer
source_ref
commit_ref
test_ref
gate_ref
access_policy
retention
verification_status
notes
\`\`\`

---

# 9. Gate rule

A gate may only consume explicit evidence states.

\`\`\`text
REQUIRED CONTROL
  ↓
EVIDENCE PRESENT?
  ├─ NO  → NOT_READY / BLOCKED
  └─ YES
       ↓
VALID?
  ├─ NO  → FAIL
  └─ YES → PASS
\`\`\`

No evidence → no PASS.

---

# 10. Branch and change protocol

For active development:

- work on a dedicated feature branch;
- do not merge without authorized review;
- do not rewrite unrelated history;
- no blanket clean/reset/stash of user work;
- material changes receive human-readable commit messages;
- stage/gate transitions are committed;
- release state is pinned by immutable commit/tag/reference.

---

# 11. Production protocol event

Every important GitHub change should map to Manufacturing KB:

\`\`\`text
GITHUB COMMIT / PR / REPORT
        ↓
ArtifactVersion / DecisionRecord / GateResult / Evidence
        ↓
Manufacturing KB event
        ↓
Project current state
        ↓
Project Memory after approval
\`\`\`

GitHub is therefore not just source storage. It is one of the evidence sources for FATHER production memory.

---

# 12. UI indicators

Project/stage UI should show:

\`\`\`text
GIT PROTOCOL
  commits: N
  latest commit: <sha>
  evidence manifests: N
  security reports: N
  devsecops reports: N
  missing required evidence: N
  latest gate: PASS/FAIL/BLOCKED
\`\`\`

For DevSecOps/Security a user can click and inspect the exact report/evidence that produced the status.

---

# 13. Retention rule

During development:
retain detailed protocol history.

After approval/release:
retain full Manufacturing KB history + compact Project Memory.

Do not delete rejected alternatives, failed tests or superseded decisions merely to make history look clean.

---

# 14. Canonical rules

\`\`\`text
NO MATERIAL CHANGE WITHOUT TRACE.

NO PASS WITHOUT EVIDENCE.

NO SECURITY/DEVSECOPS GREEN STATUS WITHOUT A CHECK OR APPROVED WAIVER.

NO SECRET IN GIT.

LARGE/SENSITIVE ARTIFACTS MAY LIVE OUTSIDE GIT,
BUT THEIR VERIFIED MANIFEST MUST LIVE IN THE PROJECT PROTOCOL.
\`\`\`
