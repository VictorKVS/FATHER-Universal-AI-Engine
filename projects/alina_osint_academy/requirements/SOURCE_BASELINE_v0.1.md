# SOURCE BASELINE REGISTER · ALINA OSINT ACADEMY v0.1

This file preserves the development intent of the user-supplied source brief without treating proposed implementation choices as approved architecture.

## Source authority

Primary development source:
**FATHER DEVELOPMENT PACK — ALINA OSINT ACADEMY**, version 0.1.

## Requirements preserved from source

### Goal
Create a professional-agent training system inside FATHER. ALINA acts as knowledge architect/teacher/methodologist/mentor/examiner; an OSINT agent is the first student.

### Universalization
The same mechanism should later train InfoSec analysts, lawyers, engineers and other FATHER agents.

### Core data concepts
Profession, Competency, Skill, KnowledgeNode/Edge, SourceDocument/Fragment, Curriculum, Lesson, Assignment, TrainingRun, Evidence, Evaluation, SkillProfile, AgentProfile, Procedure.

### Knowledge graph
Must separate:
- importance_weight
- dependency_weight
- confidence_weight
- mastery_score
- risk_weight

Knowledge confidence must not be confused with student mastery.

### Source traceability
Every factual knowledge item should link to an addressable primary-source fragment.

### ALINA teaching roles
Candidate logical roles/services:
- Curriculum Designer
- Knowledge Curator
- Training Orchestrator
- Skills Evaluator
- Professional Registry

The source explicitly allows these to be roles/services rather than separate LLMs.

### OSINT student
Candidate capabilities:
receive task; plan collection; choose allowed tools; search/collect; preserve source IDs; extract entities/relations; verify; build graph; report; submit to examiner.

### Curriculum
Ten modules OSINT-01..OSINT-10, each with objectives, prerequisites, primary sources, theory, practice, checks, success criteria and retraining rules.

### Learning
Behavior-level training first; model-weight training only after a verified dataset exists.

### Proving ground
OSINT-TG-001 using existing OSINT_deepseek infrastructure. Existing transport/collector/storage/reasoning components are reuse candidates.

### Prototype acceptance intent
A complete vertical loop must be demonstrated:
teacher creates plan/task → student executes → evidence is stored → evaluator checks → skill profile changes → retry/retraining uses detected errors → state survives restart.

## Proposed implementation choices — NOT APPROVED YET

- Python/FastAPI
- PostgreSQL + pgvector or existing FATHER RAG
- SQLite for isolated MVP
- NetworkX
- React
- pytest
- JSON Schema / Pydantic

These remain architecture candidates until PRE-DESIGN is passed.

## Runtime claim requiring revalidation

The source brief says Telegram connectivity was previously verified and lists Telethon/Psiphon/session details. Current operator evidence shows timeout on connection attempts, therefore development status is:

`TELEGRAM_RUNTIME = REVALIDATION_REQUIRED`

No contradiction is deleted; both historical source claim and current evidence remain traceable.
