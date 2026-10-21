# 18 — FATHER GIT WORKSPACE

**Status:** platform architecture / DevSecOps control surface  
**Purpose:** make repositories, branches, commits, pull requests, checks and merge gates visible inside FATHER as part of each project's production state.

---

# 1. Core principle

Git is not an external developer detail.

For FATHER it is part of the manufacturing process:

\`\`\`text
PROJECT
  ↓
REPOSITORY
  ↓
BRANCH
  ↓
COMMITS
  ↓
PR / REVIEW
  ↓
CI + SECURITY CHECKS
  ↓
EVIDENCE
  ↓
MERGE GATE
  ↓
APPROVED STATE
\`\`\`

A project stage must be traceable to the exact branch/commit where its evidence was produced.

---

# 2. Git Workspace in FATHER

Top-level navigation:

\`\`\`text
FATHER
├── PROJECTS
├── GIT WORKSPACE
├── AGENTS
├── COMPONENTS
├── KNOWLEDGE
├── MANUFACTURING KB
├── TEST LAB
└── OPERATIONS
\`\`\`

The same Git Workspace is also embedded inside each Project.

---

# 3. Repository view

Each repository card shows:

- repository;
- default branch;
- linked FATHER projects;
- active feature branches;
- open PRs;
- branches without PR;
- branches behind default;
- branches diverged from default;
- latest known evidence status;
- release/protected branch status;
- DevSecOps alerts.

Example:

\`\`\`text
FATHER-Universal-AI-Engine

DEFAULT: main

ACTIVE BRANCHES
├── feature/alina-osint-academy-v01
│   ├── PROJECT: FATHER-ACADEMY-OSINT-001
│   ├── RELATION TO MAIN: DIVERGED
│   ├── AHEAD: 16
│   ├── BEHIND: 3
│   └── PR: NONE
│
└── feature/father-project-registry-v01
    ├── PROJECT: FATHER PLATFORM / REGISTRY
    ├── RELATION TO MAIN: AHEAD
    ├── AHEAD: 17
    ├── BEHIND: 0
    └── PR: NONE
\`\`\`

Counts are live/snapshot data and must be refreshed rather than treated as permanent documentation.

---

# 4. Branch graph

The UI should visualize branches as a graph/timeline:

\`\`\`text
main ─────●────────●────────●──────────────▶
           \                    \
            \                    └─ feature/father-project-registry-v01
             \
              └─ feature/alina-osint-academy-v01
                    ↘ branch is currently behind main
\`\`\`

Branch node information:

- branch name;
- base/default branch;
- linked project;
- linked stage;
- latest commit;
- ahead/behind;
- divergence state;
- PR;
- review state;
- CI state;
- Security state;
- DevSecOps gate;
- merge readiness;
- age/last activity;
- owner.

---

# 5. Branch states

\`\`\`text
SYNCED
AHEAD
BEHIND
DIVERGED
STALE
BLOCKED
READY_FOR_REVIEW
READY_FOR_MERGE
MERGED
CLOSED
\`\`\`

A branch can be green for tests but still not be merge-ready if review/security evidence is missing.

---

# 6. Color semantics

Suggested UI semantics:

\`\`\`text
GRAY    = inactive / not evaluated
BLUE    = active development
YELLOW  = review or evidence incomplete
ORANGE  = behind/diverged / revalidation required
GREEN   = required checks passed and gate satisfied
RED     = failed/blocking condition
PURPLE  = explicit waiver/decision required
\`\`\`

Color is derived from evidence/status, never manually assigned as proof.

---

# 7. Project ↔ branch binding

A project may have:

- one primary development branch;
- supporting branches;
- external repository branches;
- release branch/tag/ref;
- archived historical branches.

Contract:

\`\`\`text
Project
  ├── primary_repository
  ├── primary_branch
  ├── supporting_branches[]
  ├── external_repo_refs[]
  ├── approved_commit
  └── release_ref
\`\`\`

Each StageRun may additionally pin its own commit SHA.

---

# 8. Commit panel

Clicking a branch opens a commit timeline.

For each commit show:

- short SHA;
- human commit subject;
- author;
- time;
- linked project/stage;
- changed logical artifact;
- tests/checks;
- Security/DevSecOps evidence;
- gate impact;
- related DecisionRecord;
- related RiskFinding.

A commit is not automatically "good" because it exists.

---

# 9. Pull Request lane

PR card should show:

- base → head;
- linked project/stage;
- draft/open/closed/merged;
- files changed;
- reviewers;
- unresolved threads;
- checks;
- security checks;
- required evidence;
- merge blockers;
- approval state.

Merge button in FATHER must remain gated by project policy and explicit authorization.

---

# 10. DevSecOps control surface

For each active branch:

\`\`\`text
BUILD
UNIT TEST
INTEGRATION TEST
SAST
SCA
SECRET SCAN
LICENSE SCAN
SBOM
CONTAINER SCAN
IaC / K8S SCAN
ARTIFACT PROVENANCE
REVIEW
SECURITY REVIEW
RELEASE / MERGE GATE
\`\`\`

Each item uses:

\`\`\`text
NOT_APPLICABLE
NOT_RUN
RUNNING
PASS
FAIL
BLOCKED
WAIVED_WITH_APPROVAL
\`\`\`

No missing check is rendered as PASS.

---

# 11. Branch risk indicators

FATHER should flag:

## Divergence risk
Branch is both ahead and behind default.

## Staleness risk
No activity for configured period while project remains active.

## Orphan branch
Branch has no linked Project/Stage/owner.

## No-review risk
Material branch has no PR/review route.

## Evidence drift
Stage documents refer to an older commit than current branch head.

## Security drift
Security evidence was generated before material code/config changes.

## Dependency drift
Lockfile/SBOM/dependency state changed after security checks.

---

# 12. Merge readiness

Calculated:

\`\`\`text
BRANCH READY?
  ├── linked project/stage
  ├── required docs complete
  ├── tests valid
  ├── Security checks valid
  ├── DevSecOps checks valid
  ├── no unresolved blocker
  ├── required review complete
  ├── evidence current for HEAD
  └── explicit authorization where required
\`\`\`

Only then:

\`READY_FOR_MERGE\`

This is still not an automatic merge instruction.

---

# 13. Snapshot vs live data

FATHER distinguishes:

\`\`\`text
LIVE GIT STATE
= fetched from GitHub/connectors

EVIDENCE SNAPSHOT
= recorded state used by a gate/release
\`\`\`

A release must pin an immutable snapshot:

- repo;
- branch;
- commit SHA;
- checks;
- evidence;
- gate decision.

The live branch may later move.

---

# 14. Current verified FATHER snapshot

At the time this specification was created, GitHub reported:

\`\`\`text
Repository:
VictorKVS/FATHER-Universal-AI-Engine

Default branch:
main

feature/alina-osint-academy-v01
  status vs main: DIVERGED
  ahead: 16
  behind: 3
  open PR: none found

feature/father-project-registry-v01
  status vs main: AHEAD
  ahead: 17
  behind: 0
  open PR: none found
\`\`\`

This is a point-in-time evidence snapshot, not a permanent assertion.

---

# 15. FATHER UI views

## Repository Map
Repositories and active branches.

## Branch Graph
Visual ancestry/divergence.

## Project Git View
Only refs belonging to one project.

## PR / Review View
Review and merge work.

## DevSecOps View
Checks/evidence per branch/commit.

## Release Lineage
Approved release → exact commit → exact evidence.

---

# 16. Manufacturing Knowledge Base integration

Git events become production events:

\`\`\`text
BRANCH_CREATED
COMMIT_ADDED
PR_OPENED
REVIEW_REQUESTED
CHECK_PASSED
CHECK_FAILED
BRANCH_DIVERGED
GATE_BLOCKED
MERGE_APPROVED
MERGED
RELEASE_PINNED
\`\`\`

This allows FATHER to learn, for example:

- which branches repeatedly diverge;
- where rework occurs;
- which check catches most defects;
- how long reviews take;
- which stage causes the most merge blockers.

---

# 17. Canonical rules

\`\`\`text
EVERY ACTIVE BRANCH SHOULD HAVE PURPOSE + OWNER + PROJECT LINK.

EVERY APPROVED STATE MUST PIN AN EXACT COMMIT.

DEVSECOPS/SECURITY EVIDENCE MUST MATCH THE COMMIT IT CLAIMS TO VERIFY.

DIVERGED/BEHIND DOES NOT MEAN FAIL,
BUT IT MUST BE VISIBLE.

NO AUTOMATIC MERGE FROM A GREEN COLOR ALONE.
\`\`\`
