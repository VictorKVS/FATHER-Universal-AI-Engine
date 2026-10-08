# 05 — Evaluation Lab & Metric Registry

## Golden principle
Measurements are project-specific, reproducible, calibrated against meaningful references and accompanied by uncertainty. Do not optimize solely for one LLM-judge score.

## Metric families
- Response quality: factual correctness, answer relevance, completeness, concision, instruction following, JSON/schema validity, hallucination rate, consistency, task success.
- Retrieval: recall@k, precision@k, hit@k, MRR, nDCG, context precision/recall, reranker lift, evidence and citation accuracy.
- Grounding: faithfulness, attributable claim rate, unsupported-claim rate, groundedness.
- Prompts: sensitivity, repeatability, robustness to formatting, role-boundary compliance, success delta by version.
- Agent/workflow: end-to-end task completion, tool-call correctness, approval compliance, loop termination, retry/recovery, failure propagation.
- Security: injection success rate, data leakage rate, privilege escalation attempts blocked, unauthorized tool execution, cross-tenant access violations.
- Runtime: TTFT, end-to-end latency p50/p95/p99, throughput, tokens/sec, timeout/errors, queue time, SLA/SLO.
- Resources/cost: tokens in/out, API cost per successful task, GPU time/VRAM, RAM/CPU, energy where measured, cost regression.
- Data/KB: ingest completeness, duplicates, freshness, source traceability, parser quality, ACL coverage, embedding drift.
- Reliability/drift: availability, stability across seeds, model drift, benchmark regression, crash/cancel/rollback rates.

## Experimental protocol
1. Define project task set, representative sample and private holdout; assign owners.
2. Declare candidate model versions and capabilities; pin model adapter and parameters.
3. Declare prompt version, KB snapshot/index, retrieval settings and workflow graph.
4. Define baseline, budget, safety exclusions, metric set, thresholds and aggregation.
5. Execute combinations under fair resource controls; track every failure/skip.
6. Evaluate deterministic rules first, expert judgments and judges with calibration.
7. Report mean/median/quantiles, uncertainty, slice metrics and cost-quality trade-offs.
8. Gate promotion using mandatory safety tests + project-defined quality thresholds.
9. Retain experiment manifest and rollback point.

## Core metric record schema (conceptual)
`metric_id`, `version`, `unit`, `direction` (higher/lower), `range`, `aggregator`, `sample_count`, `measurement_method`, `reference_dataset`, `confidence`, `evaluator_version`, `project_id`.

## Auto-switch rules
Only validated, authorized, capability-compatible and data-residency-compatible candidates may be selected. Production promotions require explicit approval policy; experimentation must not change production routing by default.

## Explicit cautions
Temperature=0 does not guarantee identical outputs across all runtimes. LLM-as-a-Judge needs bias calibration and human spot checks. RAG faithfulness does not establish factual truth independently of source quality.
