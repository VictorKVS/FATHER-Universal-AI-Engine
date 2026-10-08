# Security Policy

## Scope and status
Pre-implementation design repository. No claim of security certification or production readiness. Do not report real secrets in public issues.

## Reporting
For vulnerabilities use GitHub private vulnerability reporting if enabled; otherwise contact repository maintainer through a private channel. Never publish exploit details, real credentials, personal data or restricted logs.

## Defaults
Deny by default; least privilege; no keys, tokens, .env, raw runs or model weight binaries in Git. Review adapter dependencies and licenses. Provider data disclosure requires approved project policy. Do not grant tools based on model output.

## Required future CI gates
Secret scanning, SAST, dependency vulnerability scan, lockfiles/SBOM, license checks, artifact scanning, adversarial tests, authentication/authorization integration tests and release sign-off.

## Disclosure
Coordinate security fixes before public disclosure. Scope compliance checks to each deployment and record evidence and accepted residual risks.
