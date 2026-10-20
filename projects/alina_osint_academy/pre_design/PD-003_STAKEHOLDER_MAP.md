# PD-003 · STAKEHOLDER MAP

**Project ID:** FATHER-ACADEMY-OSINT-001  
**Status:** DRAFT

## Core stakeholders

| ID | Stakeholder | Role | Interest | Influence |
|---|---|---|---|---|
| STK-001 | FATHER Owner | product/customer owner | VERY HIGH | VERY HIGH |
| STK-002 | Product Manager | product scope/value | VERY HIGH | VERY HIGH |
| STK-003 | ALINA Analyst | teacher/methodologist/evidence support | VERY HIGH | HIGH |
| STK-004 | OSINT Student Agent | learner | VERY HIGH | MEDIUM |
| STK-005 | OSINT Domain Expert | profession/skill validity | HIGH | HIGH |
| STK-006 | Information Security Specialist | security gate owner | HIGH | VERY HIGH |
| STK-007 | DevSecOps Security | secure implementation gate owner | HIGH | VERY HIGH |
| STK-008 | Legal/Compliance | applicability and restrictions | MEDIUM/HIGH | VERY HIGH if applicable |
| STK-009 | Business Analyst | process analysis | HIGH | HIGH |
| STK-010 | System Analyst | information/system analysis | HIGH | HIGH |
| STK-011 | Architect | post-gate architecture | HIGH | VERY HIGH |
| STK-012 | Developer | implementation | HIGH | MEDIUM |
| STK-013 | QA/Evaluator | verification | VERY HIGH | HIGH |
| STK-014 | SRE/Operations | runtime/observability/recovery | MEDIUM | HIGH |
| STK-015 | Source/Tool Provider | external dependency | MEDIUM | MEDIUM/HIGH |

## Authority boundaries

\`\`\`text
PRODUCT MANAGER
  owns value/scope/priorities

OSINT DOMAIN EXPERT
  validates profession/competency meaning

INFORMATION SECURITY
  owns security applicability/risk/controls

DEVSECOPS SECURITY
  owns executable security engineering gates

ALINA
  prepares curriculum/evidence/source structure
  DOES NOT self-certify competence or approve security

QA / EVALUATION
  independently verifies outcomes
\`\`\`

## Key conflicts

- скорость обучения vs качество проверки;
- autonomy vs human approval;
- универсальность модели vs качество конкретной профессии;
- количество знаний vs подтверждённый навык;
- дешёвая evaluation vs достоверная evaluation;
- повторное использование existing components vs необходимость переработки.

## MVP boundary

В MVP обязательны:
FATHER Owner, PM, ALINA, OSINT Student, OSINT Expert, InfoSec, DevSecOps Security, QA/Evaluation.

BA/SA/Architect подключаются после Product/Security gates по общему FATHER process.
