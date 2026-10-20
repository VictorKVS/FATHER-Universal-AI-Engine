# PD-001 · IDEA CARD

**Project ID:** FATHER-ACADEMY-OSINT-001  
**Title:** ALINA OSINT ACADEMY  
**Document ID:** PD-001  
**Status:** DRAFT / REGISTERED  
**Source version:** 0.1  
**Development mode:** Prototype First / Evidence Driven / Human Approval

## 1. One-sentence idea

Create inside FATHER a reusable professional-training mechanism in which ALINA teaches, exercises and evaluates another agent until its professional skills are demonstrated by evidence, starting with an OSINT specialist.

## 2. Problem hypothesis

Agent capabilities are often assembled as prompts/tools without a structured professional curriculum, source-grounded knowledge, repeatable practice, explicit exams, skill history and evidence of mastery.

As a result, a system may look capable without being able to demonstrate professional competence.

## 3. Value hypothesis

FATHER can convert professional knowledge into:

```text
PROFESSION
 → COMPETENCIES
 → KNOWLEDGE
 → SKILLS
 → EXERCISES
 → EVIDENCE
 → EVALUATION
 → CORRECTION
 → VERIFIED SKILL PROFILE
```

and reuse the same training mechanism later for InfoSec analysts, lawyers, engineers and other FATHER specialists.

## 4. First proof

First profession: `OSINT Specialist`.

First student: `ALINA_OSINT_STUDENT`.

First proving ground: `OSINT-TG-001`.

## 5. Core product objects from source brief

- Profession
- Competency
- Skill
- KnowledgeNode
- KnowledgeEdge
- SourceDocument
- SourceFragment
- Curriculum
- Lesson
- Assignment
- TrainingRun
- Evidence
- Evaluation
- SkillProfile
- AgentProfile
- Procedure

All objects require stable identity/version/provenance/change history at later analysis/design stages.

## 6. Candidate learning cycle

```text
ASSIGNMENT
 → PLAN
 → ACTION
 → RESULT
 → CHECK
 → SCORE
 → ERROR REVIEW
 → CORRECTION
 → RETRY
```

Weight-changing SFT/DPO/RL is not part of the first prototype. First stage trains behavior/procedure with evidence and evaluation.

## 7. Non-goals for current intake

- no independent Academy platform outside FATHER;
- no claim that a UI proves competence;
- no claim that RAG presence proves competence;
- no automatic reinforcement of unverified conclusions;
- no unrestricted OSINT tool authority;
- no silent replacement of existing OSINT collectors;
- no architecture approval at idea stage.

## 8. Existing assets to inspect

Candidate donor/reuse targets named in source:

- FATHER Analytical Core;
- ALINA;
- Model Zoo;
- RAG / Knowledge systems;
- existing evaluation/testing;
- VictorKVS/OSINT_deepseek;
- TelethonTransport;
- TelegramCollector;
- MaterialStore;
- DeterministicEvidenceAnalyst;
- DeterministicSocrates.

Reuse must be proven by inventory and tests, not assumed.

## 9. Security placeholders

```text
SECURITY_STATUS: TBD_BY_SECURITY
DEVSECOPS_SECURITY_STATUS: TBD
LEGAL_APPLICABILITY: TBD_BY_SECURITY_AND_COMPLIANCE
MANDATORY_CONTROLS: TBD_BY_SECURITY
MANDATORY_LICENSES: TBD_BY_SECURITY
SECURITY_COST: TBD_BY_SECURITY
DEVSECOPS_COST: TBD_BY_SECURITY_AND_DEVSECOPS
```

## 10. Gate

`GATE-PD00-IDEA = REGISTERED_FOR_PRODUCT_DISCOVERY`

This does NOT mean READY_FOR_ARCHITECTURE.
