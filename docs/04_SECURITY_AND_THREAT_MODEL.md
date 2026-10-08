# 04 — Security Architecture & Threat Model

**Status:** initial threat-model baseline. Full analysis, tests and compliance evidence pending.

## Trust boundaries
Untrusted: end-user input, documents from KB/RAG, web results, provider outputs, MCP/tool responses, uploaded model artifacts, community adapters.
Trusted only after validation: authenticated project identity, policy engine, approved tool grants, locked release manifests and artifact provenance.

## Threats / controls / verification
| Threat | Required control | Verification |
|---|---|---|
| Prompt injection / instruction hierarchy bypass | role separation, data isolation, no model-origin permissions | adversarial fixtures |
| Sensitive data exfiltration | PII/data classification, outbound policy, redaction, no default raw logs | canary/egress tests |
| Cross-project data leakage | tenancy-aware authorization and retrieval filters | negative access tests |
| Malicious tool calls and MCP abuse | allowlist, typed schemas, least privilege, approval for side effects | tool-policy tests |
| Insecure deserialization or artifact poisoning | signed/versioned artifacts, parser validation, sandbox | malicious fixture tests |
| Provider compromise or response spoofing | TLS validation, provenance checks, bounded parsing | network failure tests |
| Dependency / CI compromise | lockfiles, SBOM, SCA, SAST, secret scanning, provenance | pipeline gates |
| Denial of wallet/resource exhaustion | request quotas, hard token/time/cost ceilings, circuit breakers | load/chaos tests |
| Agent infinite loops | DAG validation and finite iteration ceilings | termination tests |
| Model or evaluation manipulation | dataset isolation, holdouts, version pins, judge calibration | replay and leakage tests |

## Standards mapping (applicability to be assessed)
OWASP Top 10 for LLM Applications and Agentic applications; OWASP ASVS/API Security Top 10; NIST AI RMF and Generative AI Profile; NIST SSDF; ISO/IEC 27001, 27002, 42001; SLSA; SBOM; applicable 152-FZ/FSTEK requirements for particular deployments.

## Secure-by-default rules
- No cloud transmission for restricted data without explicit project policy.
- Never persist API tokens in model prompts, artifacts, crash dumps or Git.
- Separate admin/control, run execution and tool permissions.
- Treat model output as content, not an executable command.
- Hash artifacts; restrict MIME types and max sizes.
- Store only necessary traces; access controlled with retention and deletion.
- Enforce approved provider/model/region configuration on every request.
- Review adapter source and license before plugin activation.

## Operational process
Record assets → data flows → trust boundaries → misuse cases → severity and mitigations → test evidence → residual risk acceptance → periodic review. Security findings block production approval according to severity policy.
