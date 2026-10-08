# 09 — Integration and ALINA Migration

## Public contracts
Preferred transport: REST/JSON (OpenAPI), CLI and JS/TS/Python SDKs. Project has its own configuration, policies, model requirements, prompt versions, test datasets and artifact scope.

## ALINA-BOOK extraction plan
Source (do not modify in-place without tests):
`G:\1\Vibe coding\Vibe-coding-router\DZ_18. Integration with external services\ALINA_LLM_FACTORY` and `server/providers`.

Candidate components:
- runner/executor lifecycle with timeouts and final-product fallback
- provider adapters: Ollama/GigaChat/OpenAI
- prompt/input hashing, stage manifests and artifact contracts
- missing-credential skip
- watchdog and mock fixtures

Known concerns from earlier test logs:
- skipped worker exit code 0 previously led to manifest status mistakenly counted as success
- a local provider assembled additional system instructions; not strict prompt parity
- response previews and untrusted provider errors need privacy review
- real GigaChat model path had JSON-parse failure; OpenAI credentials should not be assumed

## Safe migration criteria
1. Inventory files and licenses; check git status, ignore rules and data classification.
2. Never copy .env, backups, outputs, RUNS, FINAL, API keys or actual source documents.
3. Extract small units and preserve behavior with tests; no monolithic copy.
4. Test real runner with mock worker isolated from live RUNS/FINAL.
5. Establish feature flag and rollback plan for ALINA integration.
6. Benchmark exact prompt/version/seed/configuration and maintain provenance.

## Compatibility tests
Existing ALINA generator stays operational. New engine adapter implements `generate`, status, artifacts and evaluation contracts; switched on only after comparison runs and explicit acceptance.
