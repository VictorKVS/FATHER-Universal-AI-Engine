# FATHER PRE-DESIGN PROCESS v0.1

**Purpose:** mandatory pre-architecture process for every new FATHER project/agent/product.

> Architecture is forbidden until the PRE-DESIGN GATE is passed.

## State machine

```text
IDEA_REGISTERED
      ↓
PRODUCT_DISCOVERY
      ↓
SECURITY_INTAKE
      ↓
LEGAL_COMPLIANCE_APPLICABILITY
      ↓
BUSINESS_ANALYSIS
      ↓
SYSTEM_ANALYSIS
      ↓
REQUIREMENTS_BASELINE
      ↓
PRE_DESIGN_REVIEW
      ↓
READY_FOR_ARCHITECTURE
```

Any failed gate returns the project to the responsible previous stage.

---

## PD-00 · Idea Intake

### Input
- free-form idea
- initiator
- initial context

### Mandatory actions
1. assign Project/Agent ID;
2. register owner/initiator;
3. write one-sentence idea;
4. record problem hypothesis;
5. record initial value hypothesis;
6. record explicit non-goals;
7. register open questions.

### Outputs
- PD-001 IDEA_CARD
- registry entry

### Gate
`GATE-PD00-IDEA`

PASS only if:
- ID exists;
- problem is expressed without implementation;
- target human/business context is named;
- non-goals are present;
- unknowns are explicitly marked.

---

## PD-01 · Product Manager Discovery

### Inputs
- PD-001 IDEA_CARD

### Mandatory actions
1. identify user, customer, owner, stakeholders;
2. define AS-IS problem at product level;
3. formulate desired outcome;
4. identify first narrow use case;
5. define value hypothesis;
6. define scope / out-of-scope;
7. identify assumptions and dependencies;
8. define measurable success criteria;
9. identify expected lifecycle;
10. record unresolved questions for Security Intake.

### Outputs
- PD-002 PRODUCT_BRIEF
- PD-003 STAKEHOLDER_MAP
- PD-004 VALUE_AND_SUCCESS_METRICS
- PD-005 SCOPE_AND_NON_GOALS
- PD-006 ASSUMPTION_REGISTER

### Gate
`GATE-PD01-PRODUCT`

PASS only if:
- first user/use case is identifiable;
- success can be measured;
- scope is bounded;
- assumptions are visible;
- no implementation architecture has been smuggled into the product brief.

---

## PD-02 · Information Security Intake

**This stage is mandatory before Business/System Analysis.**

### Inputs
- PD-002..PD-006

### Mandatory actions
1. identify information categories;
2. identify personal/sensitive/confidential data;
3. identify trust boundaries;
4. identify actors and preliminary authority levels;
5. define allowed actions;
6. define prohibited actions;
7. define actions requiring human approval;
8. define audit/evidence expectations;
9. define retention/deletion constraints;
10. identify credential/secrets risks;
11. identify third-party/integration risks;
12. identify preliminary threat/risk hypotheses;
13. identify security questions that BA/SA must respect.

### Outputs
- PD-007 SECURITY_CONTEXT
- PD-008 DATA_CLASSIFICATION_DRAFT
- PD-009 AUTHORITY_AND_ACTION_MATRIX
- PD-010 INITIAL_RISK_REGISTER
- PD-011 SECURITY_CONSTRAINTS

### Gate
`GATE-PD02-SECURITY`

PASS only if:
- data classes are not unknown without explicit TBD reason;
- prohibited/high-impact actions are identified;
- human gates are identified;
- audit/evidence needs are known;
- security constraints are handed forward.

---

## PD-03 · Legal / Compliance Applicability

### Inputs
- Product Brief
- Security Intake Pack

### Mandatory actions
1. identify jurisdictions;
2. identify applicable information categories and regulated activities;
3. classify candidate laws/regulations/standards;
4. mark each item APPLICABLE / NOT_APPLICABLE / TBD / REVIEW_REQUIRED;
5. record temporal/version scope;
6. identify obligations affecting process, data, authority, retention, evidence or deployment;
7. identify questions requiring legal specialist review.

### Outputs
- PD-012 COMPLIANCE_APPLICABILITY_MATRIX
- PD-013 LEGAL_CONSTRAINTS
- PD-014 REGULATORY_SOURCE_REGISTER

### Gate
`GATE-PD03-COMPLIANCE`

PASS only if:
- jurisdiction is explicit;
- applicability is reasoned, not merely a document list;
- TBD items are visible;
- no unsupported compliance claim is marked as confirmed.

---

## PD-04 · Business Analysis

### Inputs
- Product Pack
- Security Pack
- Compliance Pack

### Mandatory actions
1. model AS-IS process;
2. model TO-BE process;
3. identify actors/roles;
4. identify business events;
5. identify activities;
6. identify decisions and business rules;
7. identify information objects consumed/produced;
8. identify manual/human control points;
9. identify exception paths;
10. identify ownership and handoffs.

### Outputs
- PD-015 AS_IS_PROCESS
- PD-016 TO_BE_PROCESS
- PD-017 ACTOR_ROLE_MODEL
- PD-018 BUSINESS_RULE_REGISTER
- PD-019 BUSINESS_INFORMATION_OBJECTS
- PD-020 USE_CASE_CATALOG

### Gate
`GATE-PD04-BA`

PASS only if:
- TO-BE solves the stated problem;
- each step has actor + input + action + output;
- security/legal constraints are represented;
- exception paths and human gates exist where required;
- process is implementation-neutral.

---

## PD-05 · System Analysis

### Inputs
- approved business model
- security/compliance constraints

### Mandatory actions
1. convert business information objects into system information flows;
2. define canonical entities and ownership;
3. define system states and transitions;
4. define inputs/outputs per system step;
5. define preconditions/postconditions;
6. define commands/events/queries/documents;
7. define error/exception behavior;
8. define external systems/interfaces conceptually;
9. define traceability/provenance requirements;
10. define algorithms/decision rules at logical level;
11. identify deterministic vs probabilistic processing;
12. identify human/system responsibility boundaries.

### Outputs
- PD-021 INFORMATION_FLOW_MODEL
- PD-022 DATA_ENTITY_MODEL
- PD-023 STATE_TRANSITION_MODEL
- PD-024 LOGICAL_PROCESS_ALGORITHMS
- PD-025 INTERFACE_CONTEXT
- PD-026 ERROR_EXCEPTION_MODEL
- PD-027 TRACEABILITY_MODEL

### Gate
`GATE-PD05-SA`

PASS only if:
- every TO-BE step has system realization or explicit human-only status;
- inputs/outputs are defined;
- state transitions are defined;
- data ownership/source-of-truth is known or marked TBD;
- errors/exceptions are modeled;
- algorithms remain implementation-neutral.

---

## PD-06 · Requirements Baseline

### Inputs
- all previous approved artifacts

### Mandatory actions
1. derive business requirements;
2. derive functional requirements;
3. derive non-functional requirements;
4. derive security requirements;
5. derive compliance requirements;
6. derive data/privacy requirements;
7. derive observability/audit requirements;
8. derive lifecycle/operational requirements;
9. define acceptance criteria;
10. map each requirement to source and verification method;
11. identify conflicts and unresolved decisions.

### Outputs
- PD-028 REQUIREMENTS_REGISTER
- PD-029 NFR_REGISTER
- PD-030 SECURITY_REQUIREMENTS
- PD-031 COMPLIANCE_REQUIREMENTS
- PD-032 ACCEPTANCE_CRITERIA
- PD-033 TRACEABILITY_MATRIX
- PD-034 OPEN_DECISIONS_AND_CONFLICTS

### Gate
`GATE-PD06-REQ`

PASS only if:
- critical requirements have source + owner;
- critical requirements have verification method;
- NFRs are measurable;
- unresolved conflicts are visible;
- acceptance criteria exist.

---

## PD-07 · Pre-Design Review

### Inputs
All PD-001..PD-034 artifacts.

### Review questions
- Is the problem worth solving?
- Is the first scope bounded?
- Is the user/customer clear?
- Are security constraints present before design?
- Is legal applicability understood enough to proceed?
- Are AS-IS and TO-BE coherent?
- Are information flows and states understood?
- Are requirements testable?
- Are major unknowns explicit?
- Is architecture actually needed now?

### Outputs
- PD-035 PRE_DESIGN_REVIEW_REPORT
- PD-036 PRE_DESIGN_DECISION

### Decision
One of:

```text
READY_FOR_ARCHITECTURE
RETURN_TO_PRODUCT
RETURN_TO_SECURITY
RETURN_TO_COMPLIANCE
RETURN_TO_BA
RETURN_TO_SA
RETURN_TO_REQUIREMENTS
HOLD
CANCEL
```

Only `READY_FOR_ARCHITECTURE` opens the Architecture stage.

---

# Mandatory Pre-Design Pack

```text
PD-001 IDEA_CARD
PD-002 PRODUCT_BRIEF
PD-003 STAKEHOLDER_MAP
PD-004 VALUE_AND_SUCCESS_METRICS
PD-005 SCOPE_AND_NON_GOALS
PD-006 ASSUMPTION_REGISTER

PD-007 SECURITY_CONTEXT
PD-008 DATA_CLASSIFICATION_DRAFT
PD-009 AUTHORITY_AND_ACTION_MATRIX
PD-010 INITIAL_RISK_REGISTER
PD-011 SECURITY_CONSTRAINTS

PD-012 COMPLIANCE_APPLICABILITY_MATRIX
PD-013 LEGAL_CONSTRAINTS
PD-014 REGULATORY_SOURCE_REGISTER

PD-015 AS_IS_PROCESS
PD-016 TO_BE_PROCESS
PD-017 ACTOR_ROLE_MODEL
PD-018 BUSINESS_RULE_REGISTER
PD-019 BUSINESS_INFORMATION_OBJECTS
PD-020 USE_CASE_CATALOG

PD-021 INFORMATION_FLOW_MODEL
PD-022 DATA_ENTITY_MODEL
PD-023 STATE_TRANSITION_MODEL
PD-024 LOGICAL_PROCESS_ALGORITHMS
PD-025 INTERFACE_CONTEXT
PD-026 ERROR_EXCEPTION_MODEL
PD-027 TRACEABILITY_MODEL

PD-028 REQUIREMENTS_REGISTER
PD-029 NFR_REGISTER
PD-030 SECURITY_REQUIREMENTS
PD-031 COMPLIANCE_REQUIREMENTS
PD-032 ACCEPTANCE_CRITERIA
PD-033 TRACEABILITY_MATRIX
PD-034 OPEN_DECISIONS_AND_CONFLICTS

PD-035 PRE_DESIGN_REVIEW_REPORT
PD-036 PRE_DESIGN_DECISION
```

---

# Core handoff contract

Every stage must state:

```text
INPUT
PROCESS
QUESTIONS
RULES
DECISIONS
OUTPUT
EXCEPTIONS
RISKS
EVIDENCE
NEXT OWNER
GATE
```

No stage may silently invent missing upstream facts.

---

# Traceability spine

```text
IDEA
 → VALUE
 → STAKEHOLDER
 → SECURITY CONSTRAINT
 → LEGAL/COMPLIANCE OBLIGATION
 → BUSINESS PROCESS
 → INFORMATION FLOW
 → LOGICAL ALGORITHM
 → REQUIREMENT
 → ACCEPTANCE CRITERION
 → ARCHITECTURE DECISION
 → COMPONENT
 → TEST
 → EVIDENCE
```

Architecture starts only after the left side of this chain is materially complete.
