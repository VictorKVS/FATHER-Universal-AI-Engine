# FATHER Core Factory — growth stages

Status: IMPLEMENTATION BASELINE  
Branch: `feature/father-core-cell-v01`

## Purpose

Build FATHER from the smallest provable manufacturing cell upward.

The infrastructure/UI/Git/DevSecOps layer remains an operating contour around the
factory. The factory core itself starts from canonical objects and one universal
information-processing path.

## Growth ladder

```text
STAGE 0  CANONICAL OBJECTS + ZOO INDEXES
         Agent / Model / Tool / Message / Artifact / Run / Evidence

STAGE 1  UNIVERSAL PROCESSOR
         INPUT
           → NORMALIZE
           → POLICY / CONTEXT
           → MODEL REQUEST
           → MODEL
           → MODEL RESPONSE
           → TRANSFORM
           → OUTPUT ARTIFACT
           → EVIDENCE

STAGE 2  CELL-001
         1 AGENT + 1 LLM
         one deterministic processing path
         one input / one output / one evidence record

STAGE 3  CELL-002
         1 AGENT + 2 LLM
         modes:
         - primary + fallback
         - selector
         - fan-out + compare
         - judge/verification

STAGE 4  AGENT ZOO
         N AGENTS + N MODELS
         role contracts / model eligibility / policies

STAGE 5  TOOL ZOO + PIPELINE
         Agent → Tool → Agent
         state / retry / branching / human gate

STAGE 6  GRAPH / ORCHESTRATION
         multi-agent workflows
         typed edges
         state transitions
         event/evidence stream

STAGE 7  FACTORY CERTIFICATION
         test → security → parity → evidence → certification → catalog

STAGE 8  FULL FATHER ENVIRONMENT
         Projects / Git / DevSecOps / Manufacturing KB / Operations
```

## Canonical runtime objects

### AgentSpec

An agent is not a model.

```text
AgentSpec
├── agent_id
├── name / role
├── instructions
├── capabilities
├── allowed_models
├── policies
├── input_contract
└── output_contract
```

Existing `agents/*/agent.yaml` files remain source artifacts. The Agent Zoo is an
index over those agents, not a second competing agent system.

### ModelSpec

```text
ModelSpec
├── model_id
├── provider_type
├── provider_model
├── base_url_env
├── api_key_env
├── capabilities
├── limits
└── status
```

Credentials are environment references only. Secret values are never stored in
the Zoo.

### MessageEnvelope

Every input and output travels through the same envelope.

```text
MessageEnvelope
├── schema_version
├── message_id
├── run_id
├── direction
├── content_type
├── payload
├── metadata
├── provenance
└── constraints
```

Raw strings, JSON and later files/documents are normalized into this contract
before the agent sees them.

### RunRecord

```text
RunRecord
├── run_id
├── cell_id
├── agent_id
├── model_id
├── started_at / finished_at
├── status
├── input_sha256
├── output_sha256
├── model_request
├── model_response metadata
├── transformations
└── evidence
```

FATHER does not persist hidden chain-of-thought. Evidence stores observable
inputs, outputs, configuration, hashes, timings, decisions/gates and explicit
rationales only.

## Universal Processor contract

```text
RAW INPUT
    │
    ▼
[Input Normalizer]
    │ canonical MessageEnvelope
    ▼
[Agent Context Builder]
    │ AgentSpec + constraints
    ▼
[Model Request Builder]
    │ provider-neutral ModelRequest
    ▼
[Model Adapter]
    │
    ▼
[Response Normalizer]
    │ canonical ModelResponse
    ▼
[Output Transformer]
    │ canonical MessageEnvelope / Artifact
    ▼
[Evidence Builder]
    │
    ▼
RUN RESULT
```

The same processor must work when the model changes. Model-specific code belongs
only in adapters.

## CELL-001 acceptance

CELL-001 is the first real factory cell:

```text
FATHER-MINIMAL-AGENT-001
        +
FATHER-LLM-OPENAI-COMPAT-001
        ↓
UniversalProcessor
        ↓
RunResult + Evidence
```

For CI there is also a deterministic test adapter. It proves the processing
contract without external credentials, but is **not** promoted as an LLM.

CELL-001 passes only when:

- one canonical input becomes one canonical output;
- the selected agent and model are explicit;
- input/output hashes are recorded;
- model adapter is replaceable;
- provider credentials are never present in artifacts/logs;
- errors fail closed;
- no hidden reasoning is requested or stored;
- unit tests reproduce the run contract.

## Next cell

CELL-002 must reuse the same contracts unchanged.

```text
                 ┌→ LLM-A ─┐
1 AGENT → ROUTER │         ├→ SELECT / COMPARE → OUTPUT
                 └→ LLM-B ─┘
```

If CELL-002 requires rewriting MessageEnvelope or AgentSpec, CELL-001 was not
universal enough and must be corrected rather than patched around.
