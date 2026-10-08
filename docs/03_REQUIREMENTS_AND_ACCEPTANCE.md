# 03 — Requirements & Acceptance

## Functional requirements
FR-001 register/update/remove adapters without changing workflow core.
FR-002 validate capability compatibility before automatic substitution.
FR-003 pin model revision and parameters for reproducible experiments.
FR-004 configure and execute serial/parallel/conditional workflows; loops have finite hard bounds.
FR-005 prompt registry: immutable versions, safe templating, hash comparisons and rollback.
FR-006 source registry: originals, dedup, provenance, ownership, classification, access and retention.
FR-007 RAG variants: ingestion, chunking, embedding, retrieval, reranking, citation provenance.
FR-008 project-scoped memory with consent/retention/erase controls.
FR-009 experiment matrix and batched benchmark schedules, with budgets and stop conditions.
FR-010 configurable metric plugin interface, baselines, confidence intervals and scorecards.
FR-011 skipped/failed model must not erase previously accepted product.
FR-012 final product must reference last policy-approved successful stage and its manifest.
FR-013 integrated API/CLI/SDK plus ALINA-BOOK consumer adapter.
FR-014 full run provenance, audit events, sanitized logs and artifact integrity.
FR-015 human approval before side-effecting/high-risk tool calls or promotions.
FR-016 multi-project isolation and access-control policies.
FR-017 visual Workflow Designer serializes the same schema as code-defined workflow.

## Non-functional and security requirements
NFR-001 fail closed if authorization/policy cannot be evaluated.
NFR-002 provider credentials only through secret references; never write to Git/logs.
NFR-003 per-project tenant isolation in DB, indexes, cache, memory, prompts and artifacts.
NFR-004 explicit egress allowlist and data residency controls.
NFR-005 cancellation, timeouts, bounded retries, circuit breakers and backpressure.
NFR-006 reproducible builds, dependency pinning, SBOM and CI security gates.
NFR-007 metrics/traces without raw private prompts or sensitive outputs by default.
NFR-008 project-specific service SLOs, with p50/p95/p99 and error budgets.

## Acceptance test scenarios
AT-001 SUCCESS → SKIPPED_NOT_CONFIGURED → FAILED → SUCCESS: FINAL equals last accepted artifact; accurate statuses and counts.
AT-002 SUCCESS without META or with invalid schema must not advance chain.
AT-003 prompt injection in retrieved document cannot grant tools, reveal secrets or override policies.
AT-004 one project cannot read another project's prompts, memory, embeddings or artifacts.
AT-005 missing credential yields explicit skip; no real provider call.
AT-006 model switch fails safely if capabilities, classification or residency mismatch.
AT-007 deterministic fixtures reproduce dataset/prompt/config hashes and score calculation.
AT-008 CI detects seeded secrets, vulnerable dependencies, malicious tool args and unauthorized outbound calls.
AT-009 side-effecting tools require authorization and applicable approval.
AT-010 rollback restores approved model/prompt/RAG/workflow configuration with traceability.

Acceptance is evidence-based; passing syntax checks or mocked unit tests alone is not production certification.
