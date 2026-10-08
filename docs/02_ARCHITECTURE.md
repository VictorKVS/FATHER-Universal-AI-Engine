# 02 — Architecture

## Context
Consumer App/CLI/SDK → AuthN/AuthZ + Project API → Project Registry → Workflow Scheduler → Model Router / Model Zoo → Provider Adapters.
Workflow nodes may reference Prompt Registry, Knowledge Hub, RAG Factory, Memory, Agent Zoo and approved Tool Gateway.
Every execution emits sanitized traces, artifact lineage, metrics and immutable run manifests.

## Bounded contexts
| Module | Responsibility | Interface |
|---|---|---|
| core | IDs, typed contracts, errors, policy context | internal package |
| project-registry | tenants, config, classification, quotas, scorecards | CRUD + audit |
| model-zoo | capability probes, model descriptors, version locks, adapters | ModelAdapter |
| workflow | DAG, parallel/condition/loop, checkpoint, retry/failover | WorkflowGraph |
| prompt-registry | versioned immutable prompts, template rendering | PromptVersion |
| knowledge | ingest/provenance/dedup/access scopes | SourceDocument |
| rag | chunk/embed/index/retrieve/rerank/evaluate | RetrievalPlan |
| memory | scoped episodic/semantic memory, TTL, consent | MemoryPolicy |
| agent-zoo | agent roles, budgets, tool permissions | AgentProfile |
| tool-gateway | tool/MCP allowlist, confirmation, sandbox | ToolInvocation |
| evaluation | datasets, metrics, benchmarks, regressions | EvaluationRun |
| observability | OpenTelemetry spans, safe logging, cost/usage | RunTrace |
| artifact-store | validated outputs, signatures/hashes, lineage | ArtifactRef |
| security | authorization, PII, policy checks, audit | PolicyDecision |

## Minimal node contract
Input: `run_id`, `project_id`, `node_id`, `prompt_ref`, `model_ref`, `input_artifact_refs`, `policy_context`, `limits`.
Output: `status`, `artifact_refs`, `validation`, `metrics`, `trace_ref`, `error_code`.

Allowed terminal statuses: SUCCESS, FAILED, TIMED_OUT, SKIPPED_NOT_CONFIGURED, SKIPPED_BY_POLICY, CANCELLED.
A zero process exit alone does not imply SUCCESS. Only schema-valid accepted artifacts may advance the chain.

## Model adapter interface
`describeCapabilities()`, `health()`, `generate(request)`, `embed(request)`, `rerank(request)`, `estimateUsage(request)`, `cancel(runId)` — methods optional only if missing capability is explicitly declared. No implicit behavioral additions in strict-comparison mode.

## Execution
Workflow graph compilation → validate node capabilities, security constraints, budgets and graph bounds → run in isolated executor → validate products → publish accepted artifacts → evaluate against project benchmark → approval gate → optional deployment.

## Storage
PostgreSQL (metadata & graph relations), S3-compatible object store or local equivalent (originals & products), configurable vector backend (RAG), secrets manager, OpenTelemetry collector. Local development must support lighter fixtures without requiring production components.

## Diagram policy
Canonical machine-readable graph and ADR precede any rendered visualization. Avoid crossing edges in visual diagrams via automatic routing/grouping.
