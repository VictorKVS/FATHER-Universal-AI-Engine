# PD-003 · STAKEHOLDER MAP

**Project ID:** LIFE-001  
**Agent ID:** FATHER-LIFE-COMPANION-001  
**Document ID:** PD-003  
**Stage:** PRODUCT MANAGER DISCOVERY  
**Status:** DRAFT  
**Version:** 0.1  
**Owner:** Product Manager  
**Architecture:** NOT STARTED  
**Security status:** TBD_BY_SECURITY  
**Legal applicability:** TBD_BY_SECURITY_AND_COMPLIANCE

---

# 1. Purpose

Определить, кто влияет на продукт LIFE-001, кто получает ценность, кто несёт ответственность, кто предоставляет данные/сервисы и кто может ограничить или заблокировать внедрение.

Этот документ не определяет техническую архитектуру и не назначает меры ИБ.

---

# 2. Stakeholder groups

## STK-001 · Primary User

**Role:** самостоятельный совершеннолетний пользователь.

### Wants
- не терять важный жизненный контекст;
- быстро находить документы и историю;
- видеть обязательства и сроки;
- понимать, откуда появилась информация;
- сохранять контроль над данными;
- иметь возможность экспортировать контекст.

### Risks / concerns
- потеря приватности;
- неверные выводы;
- сложность использования;
- слишком много ручной работы;
- vendor lock-in;
- потеря данных;
- скрытые действия системы.

### Influence
**VERY HIGH**

### Product relationship
**PRIMARY VALUE RECIPIENT**

---

## STK-002 · Product Owner / Customer

Для первой версии:

\`\`\`text
USER = CUSTOMER = CONTEXT OWNER
\`\`\`

В дальнейшем модель может измениться, но это отдельная гипотеза.

### Influence
**VERY HIGH**

---

## STK-003 · Trusted Person / Family Member

Человек, которому пользователь может делегировать ограниченный доступ или передачу части контекста.

Examples:
- супруг/супруга;
- взрослые дети;
- родители;
- доверенное лицо.

### Needs
- понимать границы своих полномочий;
- получать только разрешённую информацию;
- видеть актуальность переданных данных;
- иметь подтверждаемую историю делегирования.

### Status
**NOT IN MVP AUTOMATION**  
Potential future stakeholder.

### Security
**TBD_BY_SECURITY**

---

## STK-004 · Parent / Guardian

Актуален для долгосрочного "birth-to-death" vision.

### Product issue
Для несовершеннолетнего основной пользователь, владелец данных и лицо, принимающее решения, могут быть разными субъектами.

### Key question
Когда и как полномочия должны переходить от родителя/опекуна самому человеку?

### Status
**OUT OF MVP / FUTURE LIFECYCLE**

### Security / legal
**TBD_BY_SECURITY_AND_COMPLIANCE**

---

## STK-005 · Professional Specialist

Человек, которому пользователь передаёт подготовленный context package.

Examples:
- врач;
- юрист;
- бухгалтер;
- финансовый консультант;
- преподаватель;
- карьерный консультант;
- страховой специалист;
- социальный работник.

### Needs
- краткий, понятный и проверяемый контекст;
- ссылки на источники;
- разделение фактов и интерпретаций;
- отсутствие ложного впечатления, что агент заменяет специалиста.

### Influence
**MEDIUM / HIGH depending on use case**

---

## STK-006 · Information Security Specialist

Обязательный участник Pre-Design.

### Accountable for
- Security Intake;
- data/information classification;
- risks;
- authority/trust boundaries;
- allowed/prohibited actions;
- mandatory controls;
- mandatory security products/licenses candidates;
- security budget impact;
- security recommendation to Product.

### Current state
\`\`\`text
SECURITY_STATUS: TBD_BY_SECURITY
\`\`\`

### Influence
**VERY HIGH**

### Gate authority
Can return project/feature for REDESIGN / DEFER / DROP.

---

## STK-007 · DevSecOps Security

Обязательный участник Security Engineering contour.

### Accountable for
- secure SDLC feasibility;
- CI/CD security gates;
- supply-chain controls;
- secrets/key-management implementation;
- runtime/infrastructure security;
- observability/security telemetry;
- operational security burden;
- release security gates.

### Current state
\`\`\`text
DEVSECOPS_SECURITY_STATUS: TBD
\`\`\`

### Influence
**VERY HIGH**

---

## STK-008 · ALINA Analyst

Knowledge/evidence support role.

### Provides
- source discovery;
- normative documents;
- versions/dates;
- source fragments;
- conflicts;
- requirement/control traceability;
- evidence-backed product/license/price inputs where available.

### Does NOT approve
- legal applicability;
- residual risk;
- security architecture;
- mandatory SZI;
- final cost;
- READY_FOR_ARCHITECTURE.

### Influence
**HIGH as evidence provider / LOW as approval authority**

---

## STK-009 · Legal / Compliance Specialist

### Accountable for
- jurisdiction;
- legal applicability;
- regulatory obligations;
- data/use restrictions;
- consent/delegation/legal authority issues;
- contract/licensing implications;
- compliance-related cost and timing.

### Current state
\`\`\`text
LEGAL_APPLICABILITY: TBD_BY_SECURITY_AND_COMPLIANCE
\`\`\`

### Influence
**VERY HIGH**

---

## STK-010 · Product Manager

### Accountable for
- product problem;
- value hypothesis;
- scope;
- priorities;
- user/customer;
- product economics;
- decision KEEP / REDESIGN / DEFER / DROP based on value and mandatory burden.

### Influence
**VERY HIGH**

---

## STK-011 · Business Analyst

### Accountable later for
- AS-IS;
- TO-BE;
- actors;
- business rules;
- business events;
- process ownership;
- use cases.

### Constraint
Must consume Security/Compliance Pack; cannot bypass it.

### Influence
**HIGH after Security Intake**

---

## STK-012 · System Analyst

### Accountable later for
- information flows;
- entities;
- states;
- system inputs/outputs;
- logical algorithms;
- exceptions;
- traceability.

### Constraint
Cannot invent missing business/security/legal requirements.

### Influence
**HIGH after BA**

---

## STK-013 · Architect

### Accountable later for
- architecture decisions;
- quality attributes;
- trade-offs;
- component/system boundaries;
- integration design;
- deployment concept.

### Constraint
Architecture is blocked until PRE-DESIGN gate.

### Influence
**VERY HIGH after READY_FOR_ARCHITECTURE**

---

## STK-014 · Development Team

### Needs
- unambiguous requirements;
- API/data contracts;
- security requirements;
- acceptance criteria;
- testable scope.

### Influence
**MEDIUM during pre-design / HIGH during implementation**

---

## STK-015 · QA / Evaluation

### Accountable later for
- functional verification;
- regression;
- AI/LLM evaluation where applicable;
- safety/evidence checks;
- acceptance evidence.

### Influence
**HIGH at release gates**

---

## STK-016 · SRE / Operations

### Accountable later for
- reliability;
- availability;
- backup/recovery;
- observability;
- incidents;
- operating cost.

### Influence
**HIGH for production viability**

---

## STK-017 · External Service Provider

Possible future providers:

- cloud;
- AI/model provider;
- identity provider;
- messaging/email;
- calendar;
- storage;
- payment provider;
- health/finance/government integrations;
- backup/archive.

### Risk
Provider availability, pricing, terms, data handling, jurisdiction and lock-in may materially affect the product.

### Status
**TBD / NOT SELECTED**

---

## STK-018 · Data Source Owner

A person or organization that controls a source of information used by the user.

Examples:
- employer;
- bank;
- medical organization;
- school/university;
- government service;
- insurer;
- service provider.

### Product issue
Access does not automatically imply permission to retain, reprocess or redistribute data.

### Security/legal
**TBD_BY_SECURITY_AND_COMPLIANCE**

---

## STK-019 · Regulator / Supervisory Authority

Potential stakeholder depending on scope/jurisdiction/domain.

### Influence
**VERY HIGH where applicable**

### Current state
\`\`\`text
APPLICABILITY: TBD
\`\`\`

Do not assume a regulator without applicability analysis.

---

## STK-020 · Auditor / Assessor / Certification Body

Potential future stakeholder if required by law, contract, sector or customer.

### Needs
- traceability;
- controls;
- evidence;
- test results;
- configuration/version information;
- audit trail.

### Status
**TBD_BY_SECURITY_AND_COMPLIANCE**

---

# 3. Influence / Interest matrix

| Stakeholder | Interest | Influence | Pre-Design role |
|---|---:|---:|---|
| Primary User | VERY HIGH | VERY HIGH | core |
| Product Manager | VERY HIGH | VERY HIGH | core |
| Information Security | HIGH | VERY HIGH | mandatory gate |
| DevSecOps Security | HIGH | VERY HIGH | mandatory gate |
| Legal / Compliance | HIGH | VERY HIGH | mandatory gate where applicable |
| ALINA Analyst | HIGH | MEDIUM | evidence support |
| Business Analyst | HIGH | HIGH | downstream |
| System Analyst | HIGH | HIGH | downstream |
| Architect | HIGH | VERY HIGH | blocked until gate |
| Professional Specialist | HIGH | MEDIUM | external consumer |
| Trusted Person / Family | MEDIUM | MEDIUM | future |
| Parent / Guardian | HIGH | VERY HIGH | future lifecycle |
| External Provider | MEDIUM | HIGH | dependency |
| Regulator | LOW direct / HIGH indirect | VERY HIGH | if applicable |
| Auditor / Assessor | MEDIUM | HIGH | if applicable |

---

# 4. Authority model — product-level draft

\`\`\`text
HUMAN USER
  └── primary decision owner

PRODUCT MANAGER
  └── product scope/value owner

INFORMATION SECURITY
  └── security decision owner

DEVSECOPS SECURITY
  └── security engineering owner

LEGAL / COMPLIANCE
  └── applicability/obligation owner

ALINA
  └── evidence/source enrichment

BA / SA
  └── analysis

ARCHITECT
  └── architecture after gate
\`\`\`

---

# 5. Stakeholder conflicts to expect

## Conflict C-001
**User convenience vs security/privacy**

Example:
"Connect everything automatically" vs least privilege/data minimization.

Status:
\`TBD_BY_SECURITY\`

## Conflict C-002
**Product value vs compliance/security cost**

A useful feature may trigger expensive controls, licenses, assessments or external systems.

Decision path:
\`KEEP / REDESIGN / DEFER / DROP\`

## Conflict C-003
**User ownership vs third-party source restrictions**

User may possess data but not necessarily have unrestricted rights to redistribute/reprocess it.

Status:
\`TBD_BY_SECURITY_AND_COMPLIANCE\`

## Conflict C-004
**Family convenience vs individual autonomy**

Especially minors, guardianship, incapacity and end-of-life.

Status:
\`FUTURE / TBD\`

## Conflict C-005
**Long-term memory vs right/need to delete or correct**

History must not mean "never forget anything".

Status:
\`TBD_BY_SECURITY_AND_COMPLIANCE\`

---

# 6. MVP stakeholder boundary

For first MVP:

\`\`\`text
IN
- Primary User
- Product Manager
- Information Security
- DevSecOps Security
- Legal/Compliance
- ALINA Analyst
- BA
- SA
- Architect
- Development
- QA
- Operations

LIMITED EXTERNAL
- Professional Specialist as recipient of user-prepared context package

OUT / FUTURE
- Parent/Guardian mode
- Incapacity delegation
- Digital legacy transfer
- Family shared control
- Institutional ownership
\`\`\`

---

# 7. Decisions from PD-003

### DEC-PD003-001
The Primary User remains the central stakeholder and primary context owner for MVP.

### DEC-PD003-002
Information Security and DevSecOps Security are mandatory gate owners, not advisory-only roles.

### DEC-PD003-003
ALINA is evidence/source support and cannot approve security/legal decisions.

### DEC-PD003-004
Trusted person, guardian and inheritance stakeholders remain outside MVP but must be preserved in long-term lifecycle design.

### DEC-PD003-005
External providers and regulators are dependencies/applicability stakeholders, not product owners.

---

# 8. Open questions

1. Who is the first real user cohort?
2. Which professional handoff scenario is most valuable?
3. Is Legal/Compliance mandatory for every deployment or conditional by scope?
4. Which stakeholders require contractual relationships in MVP?
5. Does the product require a dedicated support/operator role in MVP?
6. How should user corrections override imported/source-derived information?
7. Which stakeholder may challenge or revoke a delegation?
8. Who owns incident communication if personal context is compromised?
9. Which domain specialist must join when a regulated feature is added?
10. Which stakeholders must sign the Pre-Design decision?

---

# 9. Handoff

\`\`\`text
PD-002 PRODUCT_BRIEF
        +
PD-003 STAKEHOLDER_MAP
        ↓
PD-004 VALUE_AND_SUCCESS_METRICS
PD-005 SCOPE_AND_NON_GOALS
PD-006 ASSUMPTION_REGISTER
        ↓
GATE-PD01-PRODUCT
\`\`\`
