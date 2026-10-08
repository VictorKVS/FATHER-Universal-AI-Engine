# 07 — Roadmap and Release Gates

## R0 — Repository & design baseline
Deliver: charter, architecture, requirements, security model, documentation registry, exclusions, initial CI, branch policy.
Gate: no secrets/real data in repo; accepted architecture and migration boundaries.

## R1 — Minimal reusable engine
Deliver: TypeScript/Node ESM core, typed ModelAdapter/Run/Artifact, registry, scheduler, JSON schema validation, unit/integration tests; local mock providers.
Gate: passing acceptance tests AT-001–AT-006 and no uncontrolled side effects.

## R2 — Evaluation & automatic experiments
Deliver: benchmark/dataset registry, metric plugins, reproducible experiment matrix, evaluator/judge calibration, scorecards, candidate auto-selection.
Gate: thresholds, baseline comparisons and holdout protections verified.

## R3 — Knowledge, RAG and memory
Deliver: source registry, provenance/dedup/retention, configurable embeddings/indexes/retrieval/reranking, scoped memory.
Gate: retrieval ACL/isolation and injection tests pass.

## R4 — Agent zoo, tools and visual graph designer
Deliver: graph editor, tools/MCP gateway, approvals, SDK, API, workflows from config.
Gate: least-privilege and workflow bounds verified.

## R5 — Production hardening
Deliver: SAST/SCA/secret scan/SBOM/container scans, stress/fault/load tests, SLOs, backup/restore, docs and release checklist.
Gate: all required tests pass, residual risks approved, compliance assessment scoped, no critical unresolved vulnerabilities.

## Release rules
No direct code copy from ALINA until secret/license checks and an isolated mock integration fixture. No assertion that runtime or security is production-ready without evidence.
