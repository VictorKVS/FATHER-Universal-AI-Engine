# PD-007 · SECURITY CONTEXT

**Project ID:** FATHER-ACADEMY-OSINT-001  
**Product:** ALINA OSINT ACADEMY v0.1  
**Stage:** INFORMATION SECURITY INTAKE  
**Status:** DRAFT  
**Owner:** Information Security Specialist  
**Co-owner:** DevSecOps Security  
**Architecture:** BLOCKED  
**Legal/Compliance:** TBD_BY_SECURITY_AND_COMPLIANCE  
**Cost:** TBD_BY_SECURITY_AND_DEVSECOPS  

---

# 1. Security purpose

Определить контекст безопасности для первого вертикального прототипа профессионального обучения OSINT-агента внутри FATHER.

Документ не утверждает конкретную архитектуру, СЗИ, лицензии или нормативную применимость.

---

# 2. Protected value

Защищаем не только исходные данные, но и достоверность самого процесса обучения.

Критические ценности:

- профессиональная база знаний;
- первоисточники и SourceFragment;
- учебные программы;
- задания;
- процедуры;
- результаты TrainingRun;
- Evidence;
- Evaluation;
- SkillProfile;
- AgentProfile;
- история ошибок и коррекции;
- политики доступа к инструментам;
- секреты/учётные данные внешних сервисов;
- журналы действий;
- доказательства того, почему навык был признан подтверждённым.

Главный принцип:

\`\`\`text
КОМПЕТЕНТНОСТЬ АГЕНТА
НЕ ДОЛЖНА МОЧЬ БЫТЬ ПОВЫШЕНА
БЕЗ ПРОВЕРЯЕМОГО EVIDENCE + EVALUATION
\`\`\`

---

# 3. Security objectives

## SEC-OBJ-001 · Integrity of training state
Нельзя незаметно изменить mastery_score, evaluation, evidence или историю обучения.

## SEC-OBJ-002 · Provenance
Критические знания и оценки должны сохранять происхождение.

## SEC-OBJ-003 · Least privilege
Обучаемый агент получает только разрешённые инструменты и действия.

## SEC-OBJ-004 · Human authority
Высокорисковые действия не выполняются автоматически без установленного human approval.

## SEC-OBJ-005 · Secret isolation
API keys, Telegram sessions, credentials и другие секреты не должны попадать в репозиторий, RAG, training evidence или UI.

## SEC-OBJ-006 · Separation of duties
Ученик не может сам себе подтвердить компетенцию.

## SEC-OBJ-007 · Reproducibility
Критические проверки должны быть воспроизводимыми.

## SEC-OBJ-008 · Evidence preservation
Должна сохраняться доказательная база, позволяющая проверить, почему был поставлен PASS/FAIL.

## SEC-OBJ-009 · Safe failure
Недоступность внешнего источника не должна автоматически превращаться в успешный результат.

## SEC-OBJ-010 · No fake PASS
Отсутствие доказательств не может быть интерпретировано как успешное прохождение.

---

# 4. Security-relevant actors

| Actor | Security role |
|---|---|
| FATHER Owner | final platform authority |
| Product Manager | scope/value owner |
| Information Security Specialist | security decision owner |
| DevSecOps Security | security engineering owner |
| ALINA | teacher/methodologist/evidence curator |
| OSINT Student | restricted learner |
| OSINT Domain Expert | professional validation |
| Evaluator / QA | independent verification |
| SRE/Operations | runtime/incident/recovery |
| External Source/Tool Provider | untrusted/partially trusted dependency |

---

# 5. Preliminary trust boundaries

## TB-001 · Human ↔ FATHER
Human approvals and administrative actions.

## TB-002 · ALINA ↔ Student Agent
Teacher-to-learner task/feedback boundary.

## TB-003 · Student Agent ↔ Tools
Highest-risk operational boundary.

## TB-004 · FATHER ↔ External Sources
Internet/Telegram/other external source boundary.

## TB-005 · FATHER ↔ External Models/Services
LLM/API/provider boundary where applicable.

## TB-006 · Runtime ↔ Repository
Secrets and runtime artifacts must not leak into source control.

## TB-007 · Training State ↔ Evaluation
Skill state must not be mutated without authorized evaluation.

## TB-008 · Evidence Store ↔ Knowledge/Skill Promotion
Raw material cannot directly become trusted knowledge or mastered skill.

---

# 6. Data / artifact classes — preliminary

This is a context-level draft. Formal classification is PD-008.

### CLASS-A · Public/Open Source Material
Public webpages, public Telegram posts, public documents.

Risk:
public source does not mean trustworthy source.

### CLASS-B · Internal Training Data
Curricula, assignments, procedures, synthetic tests, scoring rules.

### CLASS-C · Security-Sensitive Configuration
Tool permissions, policies, guardrails, evaluation thresholds.

### CLASS-D · Credentials / Secrets
API keys, session files, tokens, passwords, cryptographic material.

Default handling:
**DO NOT STORE IN REPOSITORY / RAG / TRAINING DATA.**

### CLASS-E · Operational Evidence
Logs, source IDs, timestamps, hashes, evaluations, error history.

### CLASS-F · Potential Personal/Sensitive Data
May appear in OSINT material or external sources.

Status:
**TBD_BY_SECURITY_AND_COMPLIANCE**

---

# 7. Allowed actions — preliminary

Student may only perform actions explicitly granted by policy and task scope.

Candidate allowed actions for prototype:

- receive assignment;
- create research plan;
- query approved public sources;
- use approved read-only tools;
- collect permitted material;
- preserve source identifiers;
- extract entities/relations;
- generate hypotheses;
- mark uncertainty;
- prepare report;
- submit work for evaluation.

Exact tool permissions:
**TBD_BY_SECURITY + DEVSECOPS_SECURITY**

---

# 8. Prohibited actions — preliminary

Without separate approval the prototype must not:

- perform destructive actions;
- alter external systems;
- bypass authentication;
- evade access controls;
- exploit vulnerabilities;
- perform unauthorized active scanning;
- access private accounts without authorization;
- publish or redistribute sensitive findings automatically;
- use secrets outside approved runtime boundaries;
- modify its own mastery score;
- modify evaluator results;
- self-certify;
- promote unverified claims into trusted knowledge;
- silently change curriculum/evaluation rules;
- execute arbitrary code from collected material;
- commit sessions/tokens/keys to Git.

---

# 9. Human approval candidates

Human approval is expected for:

- enabling a new external tool;
- increasing tool privileges;
- active interaction with third-party infrastructure;
- use of credentials/sessions;
- publication/export of sensitive results;
- promotion of knowledge into trusted/canonical state;
- change of evaluation thresholds;
- exception to a security policy;
- acceptance of residual risk;
- certification/promotion of agent autonomy level.

Final matrix is PD-009.

---

# 10. External dependencies

Candidate dependencies:

- Telegram;
- OSINT_deepseek;
- external websites/search services;
- LLM providers where used;
- package repositories;
- container registries;
- GitHub;
- future MCP/tools.

Security rule:

\`\`\`text
EXTERNAL DEPENDENCY
≠
TRUSTED DEPENDENCY
\`\`\`

Each dependency must be inventoried and validated before production use.

---

# 11. Security risks — initial hypotheses

These are hypotheses only; formal register is PD-010.

### RISK-H-001
Student receives excessive tool permissions.

### RISK-H-002
Untrusted source content manipulates agent behavior.

### RISK-H-003
Prompt injection / instruction injection from collected material.

### RISK-H-004
Unverified claims are promoted into knowledge.

### RISK-H-005
Student manipulates evaluation or SkillProfile.

### RISK-H-006
Teacher/evaluator roles are insufficiently separated.

### RISK-H-007
Secrets leak into logs/evidence/repository.

### RISK-H-008
Malicious or malformed files are ingested.

### RISK-H-009
External dependency compromise affects training result.

### RISK-H-010
A runtime/network failure is misreported as successful training.

### RISK-H-011
Evaluation dataset leaks to the student and allows gaming.

### RISK-H-012
Agent gains autonomy faster than verified competence.

### RISK-H-013
OSINT collection unintentionally captures personal/sensitive information.

### RISK-H-014
Historical evidence is altered or becomes unverifiable.

### RISK-H-015
Supply-chain dependency introduces vulnerable/malicious code.

---

# 12. DevSecOps Security handoff

DevSecOps Security must later define executable gates for:

- secret scanning;
- SAST;
- SCA;
- license scanning;
- SBOM;
- dependency pinning;
- artifact integrity;
- container scanning if containers are used;
- IaC/Kubernetes scanning if applicable;
- CI/CD protections;
- branch/review policies;
- environment separation;
- secrets management;
- runtime telemetry;
- security logging;
- vulnerability remediation;
- rollback/recovery;
- release evidence.

No tool/vendor is selected here.

---

# 13. Logging / evidence expectations

Security-relevant events should be traceable:

\`\`\`text
WHO
WHAT
WHEN
ON WHICH ARTIFACT
USING WHICH TOOL
UNDER WHICH POLICY
WITH WHICH INPUT
WITH WHICH RESULT
WITH WHICH EVIDENCE
\`\`\`

Minimum candidate events:

- assignment issued;
- tool permission granted;
- external source accessed;
- evidence stored;
- evaluation created;
- mastery changed;
- policy changed;
- exception approved;
- training rerun;
- runtime/recovery event.

---

# 14. Retention / deletion

Exact periods are not defined at this stage.

Must support later policies for:

- evidence retention;
- source material retention;
- secret/session non-retention;
- correction of wrong data;
- deletion where required;
- historical audit preservation where required.

Status:
**TBD_BY_SECURITY_AND_COMPLIANCE**

---

# 15. Security budget context

Current status:

\`\`\`text
SECURITY_COST: TBD_BY_SECURITY
DEVSECOPS_COST: TBD_BY_SECURITY_AND_DEVSECOPS
LICENSE_COST: TBD
MANDATORY_SECURITY_PRODUCTS: TBD
MANDATORY_DOMAIN_SYSTEMS: TBD
\`\`\`

Cost will be estimated after PD-008..PD-011 establish what controls are actually required.

---

# 16. Security decisions at PD-007

### SEC-DEC-001
The Student Agent is not a trusted principal by default.

### SEC-DEC-002
Tool access is policy-controlled and least-privilege.

### SEC-DEC-003
Student cannot self-certify or directly alter mastery.

### SEC-DEC-004
External content is treated as untrusted input.

### SEC-DEC-005
Secrets are excluded from repository, RAG and training corpus.

### SEC-DEC-006
Evidence and evaluation integrity are security-critical.

### SEC-DEC-007
No network/runtime failure may silently become PASS.

### SEC-DEC-008
High-risk actions require explicit human approval until a later approved authority model says otherwise.

---

# 17. Open security questions

1. Which exact OSINT actions are permitted in the first prototype?
2. What data classes may be persisted?
3. What personal/sensitive data can appear in evidence?
4. Which actions require human approval?
5. How is evaluator independence enforced?
6. Who may change SkillProfile?
7. How are evaluation datasets protected from leakage?
8. Which external LLMs/tools may receive source material?
9. How are secrets injected into runtime?
10. Which logs/evidence require integrity protection?
11. What retention policy applies?
12. Which legal/compliance regimes become applicable?
13. Which DevSecOps controls are mandatory for prototype vs production?
14. What is the acceptable security/OPEX envelope?
15. What conditions permit increasing agent autonomy?

---

# 18. Handoff

\`\`\`text
PD-007 SECURITY_CONTEXT
        ↓
PD-008 DATA_CLASSIFICATION_DRAFT
PD-009 AUTHORITY_AND_ACTION_MATRIX
PD-010 INITIAL_RISK_REGISTER
PD-011 SECURITY_CONSTRAINTS
PD-011A SECURITY_COMPLIANCE_BUDGET_ENVELOPE
        ↓
GATE-PD02-SECURITY
\`\`\`

Architecture remains blocked.
