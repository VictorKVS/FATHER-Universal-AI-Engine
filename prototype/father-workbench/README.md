# FATHER Project Workbench — UI Prototype v0.1

Dependency-free prototype of the FATHER project production workspace.

Run from repository root:

python -m http.server 8094

Open:

http://localhost:8094/prototype/father-workbench/

The prototype reads projects/registry.json and docs/git/current_workspace.snapshot.json when available.

It demonstrates Portfolio, production conveyor, Stage Inspector, specialist analysis, scorecards, Git state and DevSecOps evidence semantics.

No npm packages are required. Missing checks intentionally remain NOT_RUN.

World-practice review: docs/research/19_WORLD_PRACTICE_IDP_DEVSECOPS.md


## Control-plane prototype server

Preferred run mode:

```powershell
python prototype/father-workbench/server.py --port 8094
```

Open:

```text
http://127.0.0.1:8094/
```

Available prototype APIs:

- `GET /api/health`
- `GET /api/projects`
- `GET /api/providers`
- `GET /api/git-snapshot`
- `GET /api/projects/<project_id>`
- `POST /api/actions/plan`

The server performs policy planning only. It does **not** mutate GitHub, GitLab, GitVerse, SourceCraft or any other provider.

Security properties in v0.1:

- binds to localhost by default;
- no provider credentials;
- no external network calls;
- CSP and basic browser security headers;
- static path containment;
- JSON body size limit;
- action allowlist;
- high-impact actions remain blocked without explicit evidence/approval.


## Optional GitHub write credential

Read-only GitHub access works for public repositories without a token.

To enable the first audited write operation (`SCM.CREATE_BRANCH`), set a server-side environment variable before starting FATHER:

```powershell
$env:FATHER_GITHUB_TOKEN = "<fine-grained token from your secure credential store>"
python prototype/father-workbench/server.py --port 8094
```

Do **not** put the token in source files, `.env` committed to Git, browser JavaScript, screenshots or evidence files.

For this prototype use the minimum GitHub repository permission needed to create refs. Higher-impact operations remain disabled even if the token itself has broader rights.


## Evidence and manufacturing history

The control plane stores runtime evidence outside Git:

- `prototype/father-workbench/runtime/evidence-index.jsonl`
- `prototype/father-workbench/runtime/evidence/<project>/<evidence_id>.json`
- `prototype/father-workbench/runtime/manufacturing-events.jsonl`
- `prototype/father-workbench/runtime/scm-actions.jsonl`

Runtime files are ignored by Git and may contain operational metadata. Evidence files are create-once and indexed by SHA-256.

APIs:

- `GET /api/projects/<project_id>/evidence`
- `GET /api/projects/<project_id>/manufacturing-events`

A live provider read captures/deduplicates a provider-state snapshot. Successful SCM mutations produce both audit/manufacturing events and an action-result evidence record.


## Optional GitLab connection

GitLab.com is the default GitLab API base URL. For self-managed GitLab set both variables server-side:

```powershell
$env:FATHER_GITLAB_URL = "https://gitlab.example.com"
$env:FATHER_GITLAB_TOKEN = "<minimum-scope token from your secure credential store>"
```

The current GitLab adapter supports live read plus the same limited audited write contract as GitHub:

- `SCM.CREATE_BRANCH`
- `SCM.OPEN_CHANGE_REQUEST`

Merge, delete, release publish and permission/secret changes remain disabled.
