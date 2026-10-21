# 20 — FATHER SCM / DEV PLATFORM CONTROL PLANE

**Status:** platform architecture / bidirectional integration contract  
**Purpose:** make GitHub-like systems manageable from FATHER, not merely visible.

---

# 1. Core principle

FATHER integrates with source-control / DevOps platforms through provider adapters.

```text
GitHub
GitLab
GitVerse / SberTech
SourceCraft / Yandex
GitFlic
Azure DevOps
Bitbucket
Forgejo / Gitea
        ⇅
FATHER SCM CONTROL PLANE
        ⇅
Project / Stage / Security / DevSecOps / Evidence / Gate
```

FATHER must not hard-code its production model to one provider.

The provider is a replaceable infrastructure choice.

A project may move from one provider to another without changing its FATHER project identity, stage history, gates, Manufacturing KB history or Project Memory.

---

# 2. Read and write

## Read
- repositories;
- branches;
- commits;
- pull/merge requests;
- issues/work items;
- reviews;
- checks/pipelines;
- releases/tags;
- labels;
- artifacts;
- deployment/status metadata.

## Provider lifecycle
FATHER must support:

- connect provider;
- disconnect provider;
- set primary provider;
- add secondary/mirror provider;
- mirror repository;
- migrate repository;
- migrate or remap issues/work items where supported;
- migrate or remap pull/merge requests where supported;
- migrate or regenerate CI/CD definitions where feasible;
- verify migration completeness;
- switch primary provider;
- preserve old provider as read-only historical source.

## Write
Depending on permissions and policy:

- create branch;
- create/update issue or work item;
- create/update pull/merge request;
- assign reviewers;
- add labels;
- add comments;
- request changes / approve review where allowed;
- trigger approved workflow/pipeline;
- retry approved failed jobs;
- create tag/release draft;
- update release metadata;
- record deployment/release evidence;
- synchronize project metadata;
- close/archive approved work items.

High-impact operations are gated separately.

---

# 3. High-impact operations

These require explicit policy + evidence + human authorization where configured:

- merge PR/MR;
- delete branch;
- force-update branch;
- alter protected-branch rules;
- change required checks;
- modify secrets;
- modify repository permissions;
- publish release;
- deploy to production;
- rollback production;
- delete repository/artifacts;
- approve residual security risk.

A green UI state alone never authorizes these actions.

---

# 4. Action contract

Every write action becomes a FATHER action record:

```text
action_id
provider
repository
project_id
stage_id
action_type
target
requested_by
requested_at
required_permissions
required_gates
required_evidence
approval_policy
status
provider_request_ref
provider_result_ref
before_state
after_state
evidence_refs
audit_event
rollback_or_recovery
```

Statuses:

```text
DRAFT
READY
AWAITING_APPROVAL
APPROVED
EXECUTING
SUCCEEDED
FAILED
BLOCKED
CANCELLED
ROLLED_BACK
```

---

# 5. Provider abstraction

FATHER uses canonical commands:

```text
SCM.CREATE_BRANCH
SCM.OPEN_CHANGE_REQUEST
SCM.UPDATE_CHANGE_REQUEST
SCM.REQUEST_REVIEW
SCM.ADD_LABEL
SCM.ADD_COMMENT
SCM.CREATE_WORK_ITEM
SCM.UPDATE_WORK_ITEM
SCM.TRIGGER_PIPELINE
SCM.RETRY_JOB
SCM.CREATE_RELEASE_DRAFT
SCM.PUBLISH_RELEASE
SCM.MERGE_CHANGE_REQUEST
SCM.DELETE_BRANCH
```

Provider adapters translate them:

```text
FATHER command
      ↓
GitHub adapter       → Pull Request / Actions / Issues
GitLab adapter       → Merge Request / Pipelines / Issues
GitVerse adapter     → repository / review / tracker / CI/CD
SourceCraft adapter  → Pull Request / Issues / CI/CD / packages
GitFlic adapter      → merge/code review / issues / pipelines
Azure DevOps adapter → Pull Request / Pipelines / Work Items
Bitbucket adapter    → Pull Request / Pipelines / Issues
Forgejo adapter      → Pull Request / Actions / Issues
```

Project logic remains provider-independent.

---

# 6. UI

Each Project Git Workspace should have:

## State
Repository / branch / PR / checks / evidence.

## Actions
Context-aware actions allowed for current user and stage.

Example:

```text
[ Create branch ]
[ Open PR ]
[ Request review ]
[ Add issue ]
[ Run checks ]
[ Create release draft ]

[ Merge ]             BLOCKED
Reason:
- Security review incomplete
- SAST NOT_RUN
- required approval missing
```

Buttons must show WHY an action is blocked.

---

# 7. Permission model

Three layers are evaluated:

```text
PROVIDER PERMISSION
AND
FATHER ROLE / AUTHORITY
AND
PROJECT GATE POLICY
```

Example:

User may technically have GitHub merge permission, but FATHER still blocks merge when project policy requires Security Gate PASS.

Conversely, FATHER never escalates beyond provider permissions.

---

# 8. Security

Mandatory rules:

- provider tokens/credentials are server-side only;
- no SCM secrets in browser JavaScript;
- least privilege;
- short-lived credentials where supported;
- auditable identity;
- secret rotation;
- action allowlist;
- protected high-impact actions;
- CSRF/replay protection for web actions;
- immutable audit events;
- result reconciliation after provider mutation;
- no success state until provider result is verified.

---

# 9. Reconciliation

After every write:

```text
REQUEST
  ↓
PROVIDER MUTATION
  ↓
FETCH CURRENT PROVIDER STATE
  ↓
COMPARE EXPECTED / ACTUAL
  ↓
WRITE EVIDENCE
  ↓
UPDATE FATHER
```

A provider API 200 alone is not sufficient proof of desired final state.

---

# 10. DevSecOps integration

Examples:

## Open PR
FATHER may automatically attach:
- project ID;
- stage;
- decision refs;
- risk refs;
- required checks;
- evidence expectations.

## Run checks
FATHER can trigger configured CI, then collect:
- test result;
- SAST;
- SCA;
- secret scan;
- SBOM;
- license scan;
- image/IaC checks.

## Merge
Allowed only when:
- change request current;
- required reviews complete;
- security checks current for HEAD;
- no blocking risk;
- gate policy satisfied;
- explicit approval obtained when required.

---

# 11. Supported Dev Platform families

FATHER should support the concept, not only GitHub:

- GitHub / GitHub Enterprise;
- GitLab.com / GitLab Self-Managed;
- GitVerse / SberTech;
- SourceCraft / Yandex;
- GitFlic;
- Azure DevOps Services / Server;
- Bitbucket Cloud / Data Center;
- Forgejo;
- Gitea;
- future corporate/internal SCM and DevOps platforms.

Provider-specific extras may appear as extensions, but canonical project/gate logic stays inside FATHER.

## 11.1 Provider switching

Canonical flow:

```text
CURRENT PROVIDER
      ↓
INVENTORY
      ↓
MIRROR / EXPORT
      ↓
TARGET PROVIDER IMPORT
      ↓
REPOSITORY HASH / REF CHECK
      ↓
BRANCH / TAG CHECK
      ↓
ISSUE / PR / PIPELINE MAPPING
      ↓
SECURITY + ACCESS CHECK
      ↓
MIGRATION EVIDENCE
      ↓
SWITCH PRIMARY PROVIDER
      ↓
OLD PROVIDER = HISTORICAL / MIRROR / DECOMMISSION
```

The FATHER Project ID does not change during provider migration.

Provider-specific extras may appear as extensions, but canonical project/gate logic stays inside FATHER.

---

# 12. Prototype rule

The current static prototype may show action controls, but it must NOT contain provider credentials or call privileged provider APIs directly from the browser.

Real write operations require a trusted backend/connector layer.

---

# 13. Canonical rules

```text
READ + WRITE, NOT READ-ONLY.

PROVIDER-INDEPENDENT PROJECT MODEL.

NO TOKEN IN BROWSER.

NO HIGH-IMPACT ACTION WITHOUT POLICY/GATE.

NO SUCCESS WITHOUT RECONCILIATION.

EVERY MUTATION → AUDIT + EVIDENCE.
```
