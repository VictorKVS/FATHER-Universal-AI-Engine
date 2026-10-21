# 21 — FATHER DEV PLATFORM ENVIRONMENT

**Status:** prototype environment contract  
**Purpose:** embed interchangeable Git/DevOps platforms into the FATHER working environment.

## Environment

```text
FATHER
├── PROJECTS
├── DEV PLATFORM
│   ├── Overview
│   ├── Providers
│   ├── Repositories
│   ├── Branches
│   ├── PR / MR / Changes
│   ├── Issues / Work Items
│   ├── CI / CD
│   ├── Packages / Artifacts
│   ├── Security / DevSecOps
│   ├── Mirrors / Migration
│   └── Audit / Evidence
├── AGENTS
├── COMPONENTS
├── KNOWLEDGE
├── MANUFACTURING KB
├── TEST LAB
└── OPERATIONS
```

## Provider model

FATHER project identity is independent of provider.

Supported target families:

- GitHub / GitHub Enterprise;
- GitLab / GitLab Self-Managed;
- GitVerse / SberTech;
- SourceCraft / Yandex;
- GitFlic;
- Azure DevOps;
- Bitbucket;
- Forgejo;
- Gitea.

A provider may be:

```text
CONNECTED
PRIMARY
MIRROR
AVAILABLE
MIGRATION_TARGET
HISTORICAL
DISCONNECTED
```

## Project binding

Each project can have one primary provider and zero or more mirrors/historical providers.

```text
PROJECT
  ├── primary_provider
  ├── primary_repository
  ├── primary_branch
  ├── mirrors[]
  ├── migration_targets[]
  ├── historical_providers[]
  └── provider_evidence[]
```

## UI behavior

The Project Workbench shows:

- primary provider;
- repository/branch;
- provider health;
- ahead/behind when applicable;
- PR/MR status;
- pipeline/check status;
- evidence freshness;
- available mirrors;
- migration target choices;
- blocked high-impact actions with reasons.

The global **Dev Platform** page provides a cross-project view of all providers and repositories.

## Provider switch

```text
INVENTORY
→ MIRROR / EXPORT
→ TARGET IMPORT
→ REF / HASH VERIFY
→ ISSUE / CHANGE / PIPELINE MAPPING
→ SECURITY / ACCESS VERIFY
→ MIGRATION EVIDENCE
→ SWITCH PRIMARY
→ OLD PROVIDER → MIRROR / HISTORICAL / DECOMMISSION
```

Project ID, Manufacturing KB history and Project Memory do not change.

## Security

- tokens remain server-side;
- least privilege;
- no provider credentials in browser;
- every mutation is audited;
- merge/publish/delete/permission/secret operations are gated;
- provider mutation is reconciled by re-reading actual provider state;
- migration cannot PASS without verification evidence.

## Prototype boundary

The current browser prototype visualizes the control plane and creates action drafts only.

Real provider writes require trusted backend adapters.

Current connected provider in the prototype: GitHub.

GitLab, GitVerse, SourceCraft, GitFlic, Azure DevOps, Bitbucket, Forgejo and Gitea are represented as provider targets until their adapters/connections are implemented and verified.
