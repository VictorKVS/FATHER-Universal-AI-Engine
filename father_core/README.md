# FATHER Core

This directory is the provider-neutral manufacturing core.

## First executable cell

```text
CELL-001
= FATHER-MINIMAL-AGENT-001
+ FATHER-LLM-OPENAI-COMPAT-001
+ FATHER_UNIVERSAL_PROCESSOR_V0_1
```

### Contract-only run

No network and no credentials:

```powershell
python scripts/run_father_cell.py --cell CELL-001 --test --input "hello FATHER"
```

JSON input:

```powershell
python scripts/run_father_cell.py --cell CELL-001 --test --json-input '{"task":"normalize","value":"demo"}'
```

### Real LLM run

CELL-001 uses an OpenAI-compatible `/chat/completions` transport. This is
deliberately provider-neutral and can point at a compatible local or remote
runtime.

```powershell
$env:FATHER_LLM_BASE_URL = "http://127.0.0.1:11434/v1"
$env:FATHER_LLM_MODEL = "<model-name>"
# Optional for local endpoints; required when the provider requires auth:
$env:FATHER_LLM_API_KEY = "<secret>"

python scripts/run_father_cell.py --cell CELL-001 --input "Explain this input briefly"
```

Secret values are read only from process environment and are not placed in Zoo
records, RunResult, evidence hashes or output artifacts.

## Output

Every successful run returns:

```text
RunResult
├── canonical input MessageEnvelope
├── canonical output MessageEnvelope
├── ModelResponse metadata
└── RunEvidence
    ├── cell / agent / model
    ├── input SHA-256
    ├── output SHA-256
    ├── transformation path
    └── adapter type
```

Hidden chain-of-thought is neither requested nor persisted.
