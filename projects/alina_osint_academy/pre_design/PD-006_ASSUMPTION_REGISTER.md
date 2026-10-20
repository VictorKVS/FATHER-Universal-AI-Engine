# PD-006 · ASSUMPTION REGISTER

**Project ID:** FATHER-ACADEMY-OSINT-001  
**Status:** DRAFT

| ID | Assumption | Risk if false | Validation |
|---|---|---|---|
| A-001 | Professional competence can be decomposed into measurable competencies/skills | model becomes decorative | OSINT expert review |
| A-002 | Evidence-based evaluation is feasible for at least one OSINT task | mastery cannot be proven | controlled OSINT-TG-001 test |
| A-003 | Existing FATHER components can support part of the training loop | large implementation delta | inventory |
| A-004 | Existing OSINT_deepseek assets can be reused safely | duplicate/rewrite work | component validation |
| A-005 | ALINA can structure curriculum without being final authority | source/teaching errors | human domain review |
| A-006 | Behavior/procedure retraining can improve task performance without model fine-tuning | no measurable learning | correction-loop experiment |
| A-007 | SkillProfile can remain distinct from knowledge confidence | metrics collapse | schema/test |
| A-008 | SourceFragment-level provenance is practical | evidence overhead too high | prototype measurement |
| A-009 | A single profession pilot can expose reusable abstractions | core becomes OSINT-specific | second-case dry run |
| A-010 | Evaluation can detect deliberately planted errors | evaluator too weak | controlled fault set |
| A-011 | Training state can survive restart/recovery | non-repeatable system | restart test |
| A-012 | Telegram is a useful first practical source class | external dependency blocks MVP | runtime revalidation / fixture fallback for non-live tests |
| A-013 | Human review cost is acceptable for prototype | evaluation too expensive | measure reviewer time |
| A-014 | Tool permissions can be tied to skill/security policy | unsafe autonomy | Security/DevSecOps analysis |
| A-015 | Existing proposed stack is not mandatory | premature architecture lock-in | Architecture stage |

## High-priority assumptions

Must be tested earliest:

\`\`\`text
A-001 competence decomposition
A-002 evidence evaluation
A-004 reuse of OSINT assets
A-006 measurable correction loop
A-010 error detection
A-011 restart recovery
\`\`\`

## Security-dependent assumptions

A-014 and any tool/autonomy assumptions remain:

\`TBD_BY_SECURITY + TBD_BY_DEVSECOPS_SECURITY\`
