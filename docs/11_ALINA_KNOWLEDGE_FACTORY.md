# 11 — ALINA Analyst / FATHER Knowledge Factory

**Status:** architecture specification; not yet implemented.

## Mission
ALINA Analyst is the knowledge acquisition, analysis and maintenance specialist for the reusable FATHER Universal AI Engine. ALINA does not merely upload files into RAG: she produces source-grounded, versioned, evaluated and access-controlled knowledge, reusable prompts, workflows, skills and agent-ready retrieval configurations.

## Dataflow
Authorized sources → discovery/catalog → originals vault → parse/normalize → dedup/provenance → extraction of claims/rules/algorithms/entities → conflict analysis and human review → knowledge graph + RAG indexes + prompt/skill registry → project-specific tests → approved release → monitored refresh.

## Required modes
1. INVENTORY: enumerate only explicitly authorized local folders, GitHub repositories and connected sources; no indiscriminate scanning.
2. INGEST: preserve originals, hashes, MIME, author/license, timestamps, classification and source lineage.
3. NORMALIZE: OCR if needed, structured tables, hierarchical chapters/sections/clauses and stable chunk identifiers.
4. ANALYZE: concepts, procedures, algorithms, obligations, roles, relationships, source evidence, contradictions and confidence.
5. BUILD: graph nodes/edges with provenance, retrieval indexes, prompt templates, agent skill descriptors and workflows.
6. EVALUATE: retrieval recall/precision, citation attribution, faithfulness, completeness, consistency, access-policy isolation, injection robustness, freshness.
7. PUBLISH: staged candidate → automated policy gates → reviewer approval for sensitive or normative knowledge → versioned promotion.
8. MAINTAIN: incremental changes, dedup, reindex, expiry, archive, rollback and deletion propagation.

## Knowledge object contract (conceptual)
`knowledge_id`, `project_id`, `source_id`, `source_hash`, `version`, `classification`, `owner`, `license`, `content_type`, `section_path`, `claim`, `evidence_span`, `entities`, `relations`, `confidence`, `effective_at`, `expires_at`, `review_status`, `acl`, `derived_artifact_refs`.

## Quality and safety gates
- Never confuse generated summaries with primary sources.
- Every substantive extracted assertion must reference source evidence; unresolved conflicts remain explicit.
- Model-generated confidence is not calibrated probability unless separately validated.
- Original data is never silently rewritten or deleted.
- Separate original vault, normalized content, derived knowledge graph, vector indexes, prompts and agent memory.
- Enforce tenant/role ACLs during ingestion, retrieval, indexing, evaluation and output.
- Documents, repositories and external sources are untrusted instructions; cannot authorize tools or override policies.
- Keep PII, credentials and restricted material out of public GitHub and external model calls without authorization.
- Honor copyright/license restrictions and document retention/deletion policies.
- Normative/legal interpretations and high-impact decisions require designated human review.

## Integration contract
ALINA publishes `KnowledgeRelease` with `release_id`, `project_id`, `source_manifest_hash`, `graph_snapshot`, `index_snapshot`, `prompt_refs`, `skill_refs`, `evaluation_report`, `approval`, `rollback_ref`.
The Universal AI Engine consumes only approved compatible releases. Projects can pin their own knowledge versions and benchmark suites.

## Initial integrations
- FATHER central engineering knowledge
- ALINA Analyst / ALINA-IB
- CyberED (IB training, legal/regulatory knowledge and procedures)
- FATHER Architect / OTUS architecture workspace
- BOOKCRAFT creative production knowledge
- ALINA-BOOK content-generation workflow

## Acceptance scenarios
KA-001 same file ingested twice → one canonical original and traceable references.
KA-002 conflicting source claims → no silent overwrite; explicit review task.
KA-003 unauthorized project retrieval → zero cross-tenant results.
KA-004 malicious instruction embedded in PDF → no tool escalation or policy bypass.
KA-005 changed source → incremental reprocessing and versioned graph/index release.
KA-006 deleted/expired restricted source → derived indexes and caches follow deletion policy.
KA-007 agent output citations resolve to original evidence spans.
KA-008 failed evaluation leaves previous approved release active.

## Roadmap
K0 contracts + mock fixtures → K1 source inventory and original vault → K2 extraction/normalization → K3 knowledge graph → K4 RAG/index → K5 evaluation + review → K6 release and incremental maintenance.
