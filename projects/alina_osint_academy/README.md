# ALINA OSINT ACADEMY v0.1

**Project ID:** FATHER-ACADEMY-OSINT-001  
**Status:** PRE_DESIGN / IN DEVELOPMENT  
**Branch:** `feature/alina-osint-academy-v01`  
**Source:** user-supplied "FATHER DEVELOPMENT PACK — ALINA OSINT ACADEMY" v0.1  
**Architecture:** NOT APPROVED  
**Security:** TBD_BY_SECURITY  
**DevSecOps Security:** TBD  
**Legal/Compliance:** TBD_BY_SECURITY_AND_COMPLIANCE

## Mission

Build the first vertical slice of the FATHER professional-agent training mechanism using OSINT as the first profession.

The system is not a separate educational platform. It is a development track inside FATHER Analytical Core.

## Training relationship

```text
ALINA ANALYST / TEACHER
        ↓
CURRICULUM / SOURCES / TASKS
        ↓
ALINA_OSINT_STUDENT
        ↓
ACTION / EVIDENCE
        ↓
EVALUATION
        ↓
ERROR ANALYSIS
        ↓
CORRECTION / RETRAINING
        ↓
VERIFIED SKILL PROFILE
```

## Source-preserved candidate subsystems

The source brief proposes use of existing FATHER capabilities:

- Agent Zoo
- Model Zoo
- Knowledge Base / RAG
- Knowledge Graph
- Memory
- MCP / Tools
- Workflow Engine
- Evaluation
- Observability
- Guardrails
- Artifact Store

These are **candidate reuse targets**, not proof that every integration already exists or works.

## First profession

`OSINT Specialist`

Candidate curriculum:
OSINT-01..OSINT-10 from foundations, law/ethics/OPSEC through independent complex investigation.

## First student

`ALINA_OSINT_STUDENT`

## First proving ground

`OSINT-TG-001`

Goal: use the existing OSINT project as a practical training environment, collect evidence, evaluate work, update skill profile and prove repeatable learning.

### Current Telegram note

The source brief states that Telegram connectivity had been verified previously. Current live status is **REVALIDATION_REQUIRED** because the latest operator evidence showed connection timeouts. No PASS is claimed here.

## Development route

```text
SOURCE INTAKE
 → PD-001 IDEA CARD
 → PRODUCT PACK
 → SECURITY + DEVSECOPS SECURITY
 → COMPLIANCE
 → BA
 → SA
 → REQUIREMENTS BASELINE
 → PRE-DESIGN GATE
 → ARCHITECTURE
 → VERTICAL PROTOTYPE
 → UI
 → TEST / EVIDENCE
```

All implementation suggestions from the source brief are preserved as `PROPOSED_NOT_APPROVED` until the relevant gate.
