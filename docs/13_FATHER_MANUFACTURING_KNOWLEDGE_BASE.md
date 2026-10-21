# 13 — FATHER MANUFACTURING KNOWLEDGE BASE

**Status:** platform architecture / knowledge contract  
**Purpose:** accumulate reusable production experience from every FATHER project, agent, component, stage, gate, defect, decision and verified outcome.

---

# 1. Why this exists

FATHER must not only produce objects. It must learn how objects are produced.

A completed project should leave two results:

\`\`\`text
1. PRODUCT / AGENT / COMPONENT / DOCUMENT
2. VERIFIED MANUFACTURING EXPERIENCE
\`\`\`

The second result becomes reusable factory knowledge.

---

# 2. Relationship with ALINA Knowledge Factory

\`\`\`text
ALINA KNOWLEDGE FACTORY
  = source-grounded domain/professional knowledge

FATHER MANUFACTURING KNOWLEDGE BASE
  = source-grounded production/process experience
\`\`\`

Both use provenance, versioning, review and evidence.

ALINA may normalize and structure production experience, but project specialists remain owners of their decisions.

---

# 3. What is a manufacturing object

FATHER may manufacture or modify:

- Product
- Agent
- Component
- Assembly
- Block
- Mechanism
- Workflow
- Prompt/Policy
- Knowledge Release
- Document
- Requirement
- Architecture Decision
- Integration
- Test
- Evidence Package
- UI Module
- Deployment Unit
- Dataset
- Evaluation Pack
- Procedure

Every manufactured object receives a stable identity and production lineage.

---

# 4. Core manufacturing entities

## ManufacturingCase
One concrete production effort/project.

## ManufacturedObject
The object being produced.

## StageRun
One execution of IDEA / PM / SECURITY / BA / SA / ARCH / DEV / TEST / OPS stage.

## ArtifactVersion
A concrete version of a document/code/schema/config/evidence artifact.

## SpecialistAnalysis
Professional analysis of an artifact or stage.

## DecisionRecord
A decision with rationale, owner and evidence.

## GateResult
PASS / FAIL / RETURN / HOLD / BLOCKED with supporting evidence.

## RiskFinding
A discovered risk, severity, owner and treatment.

## CostRecord
Estimated/actual CAPEX/OPEX/license/integration/operations impact.

## DefectRecord
A defect/error/problem found during production.

## FixRecord
How the defect was corrected and how the correction was verified.

## PatternRecord
A reusable production pattern proven across cases.

## AntiPatternRecord
A recurring approach that caused failures/cost/risk.

## ReuseCandidate
A component/process/decision pattern suitable for reuse.

## LessonLearned
A concise experience statement linked to evidence.

## MetricSnapshot
Measured time/cost/quality/security/evaluation values.

---

# 5. Minimum object contract

Every production record should support:

\`\`\`text
record_id
record_type
project_id
object_id
object_type
stage_id
artifact_id
version
status
owner_role
reviewer_role
created_at
updated_at
inputs
outputs
decision
rationale
risks
cost_impact
time_impact
security_impact
dependencies
reused_from
derived_from
evidence_refs
source_refs
test_refs
gate_ref
metrics
result
confidence
lessons
next_action
\`\`\`

Fields may be optional by record type, but provenance/evidence must not be silently lost.

---

# 6. Event model

FATHER writes production experience as events.

Candidate events:

\`\`\`text
CASE_CREATED
STAGE_OPENED
ARTIFACT_CREATED
ARTIFACT_UPDATED
SPECIALIST_ANALYSIS_ADDED
DECISION_MADE
RISK_FOUND
COST_ESTIMATE_UPDATED
GATE_RECALCULATED
GATE_PASSED
GATE_FAILED
RETURNED_TO_PREVIOUS_STAGE
DEFECT_FOUND
FIX_APPLIED
FIX_VERIFIED
COMPONENT_REUSED
REUSE_FAILED
TEST_EXECUTED
EVIDENCE_ATTACHED
RELEASED
PRODUCTION_FEEDBACK_RECEIVED
DEPRECATED
\`\`\`

The UI stage color/state should be derived from current records/events, not manually painted.

---

# 7. Experience extraction pipeline

\`\`\`text
PROJECT ACTIVITY
      ↓
RAW PRODUCTION EVENTS
      ↓
ARTIFACTS + ANALYSIS + DECISIONS + EVIDENCE
      ↓
ALINA NORMALIZATION
      ↓
LESSON CANDIDATE
      ↓
CROSS-CASE COMPARISON
      ↓
PATTERN / ANTIPATTERN CANDIDATE
      ↓
HUMAN REVIEW
      ↓
FATHER MANUFACTURING CANON
\`\`\`

One successful case is not enough to declare a universal pattern.

Statuses:

\`\`\`text
OBSERVED
CANDIDATE
CROSS_VERIFIED
PROJECT_PROVEN
CANONICAL
DEPRECATED
\`\`\`

---

# 8. What FATHER should learn

Examples:

## Product
- which PM questions reduced rework later;
- which scope decisions prevented architecture explosion;
- which features were dropped after security-cost review.

## Security
- which product functions caused high security/compliance cost;
- which cheaper redesign preserved most value;
- which controls repeatedly appeared.

## BA / SA
- which missing business rules caused downstream defects;
- which information-flow gaps caused implementation rework.

## Architecture
- which decisions improved/reduced reliability, cost, latency or complexity;
- which dependencies caused lock-in or repeated failures.

## Development
- which component was reusable;
- what adaptation cost was required;
- which implementation pattern caused defects.

## QA / Evaluation
- which tests found real failures;
- what escaped to later stages;
- which acceptance criteria were weak.

## Operations
- actual incident causes;
- recovery effectiveness;
- actual OPEX vs estimated OPEX;
- recurring maintenance burden.

---

# 9. Cost learning

FATHER must retain both estimate and actual:

\`\`\`text
ESTIMATED_COST
        ↓
APPROVED_BUDGET
        ↓
ACTUAL_COST
        ↓
DELTA
        ↓
CAUSE OF DELTA
        ↓
LESSON FOR NEXT PROJECT
\`\`\`

Cost categories:

- development;
- security;
- licenses;
- compliance;
- infrastructure;
- integration;
- operations;
- external services;
- support;
- audit/certification;
- human expert review;
- model/token/GPU usage where applicable.

This enables future projects to start from observed ranges rather than invented estimates.

---

# 10. Stage integration

Every FATHER production stage must write experience.

Example:

\`\`\`text
PRODUCT MANAGER NODE
  ├─ PD-002..PD-006
  ├─ SpecialistAnalysis
  ├─ decisions
  ├─ assumptions
  ├─ metrics
  ├─ GATE-PD01
  └─ ExperienceRecords

INFOSEC NODE
  ├─ PD-007..PD-011A
  ├─ risks
  ├─ controls
  ├─ budget
  ├─ decisions
  ├─ GATE-PD02
  └─ ExperienceRecords
\`\`\`

The same pattern applies to BA, SA, Architecture, Development, QA and Operations.

---

# 11. UI behavior

The FATHER stage pictogram is a projection of Manufacturing KB state.

On click, the stage panel should show:

- Overview
- Documents
- Specialist Analysis
- Decisions
- Risks
- Cost
- Metrics
- Gate
- Traceability
- History
- Lessons Learned

Button:

\`RECALCULATE STAGE\`

re-evaluates current artifact/gate state and writes a new immutable recalculation event.

---

# 12. Learning rules

1. Never rewrite historical evidence silently.
2. Corrections create new versions/events.
3. Generated lesson != verified lesson.
4. One project observation != universal rule.
5. Every Pattern/AntiPattern must link to supporting cases.
6. Estimated cost and actual cost must remain separate.
7. Specialist decision ownership must remain visible.
8. ALINA structures experience but does not rewrite specialist authority.
9. Failed projects are valuable knowledge and must not disappear.
10. NO EVIDENCE → NO FACTORY CANON.

---

# 13. First live cases

Initial experience sources:

- LIFE-001
- FATHER-ACADEMY-OSINT-001
- future Golden Reference teardown/rebuild cases
- future donor intake/certification cases

The Academy project should become the first complete StageRun example because it already has IDEA, Product Pack and Security Intake records.

---

# 14. Initial implementation target

For v0.1 it is enough to support:

1. ManufacturingCase
2. StageRun
3. ArtifactVersion
4. SpecialistAnalysis
5. DecisionRecord
6. GateResult
7. RiskFinding
8. CostRecord
9. DefectRecord
10. FixRecord
11. LessonLearned
12. PatternRecord
13. Evidence links
14. immutable history

No vector search or complex ML is required to begin accumulating experience.

---

# 15. Canonical principle

\`\`\`text
FATHER DOES NOT ONLY BUILD OBJECTS.

FATHER REMEMBERS
HOW THEY WERE BUILT,
WHY DECISIONS WERE MADE,
WHAT FAILED,
WHAT IT COST,
WHAT WAS PROVEN,
AND WHAT SHOULD BE REUSED NEXT TIME.
\`\`\`
