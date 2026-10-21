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
