# 19 — WORLD PRACTICE REVIEW: PROJECT / IDP / DEVSECOPS WORKSPACES

**Date:** 2026-10-21  
**Purpose:** identify proven UI/data patterns for the FATHER Project Workbench prototype.

## Recommendation

Do not clone one external platform.

Build FATHER as a specialized **engineering production portal** combining:

- software/entity catalog;
- project/value-stream state;
- Git/PR/check evidence;
- security/DevSecOps scorecards;
- health/status graph;
- documents and specialist analysis;
- immutable manufacturing history;
- approved project memory.

FATHER's differentiator is the evidence-backed **Pre-Design → Gate → Architecture → Build → Eval → Operations** chain and its memory of why decisions were made.

---

## 1. Backstage — take the catalog/entity model

Official documentation describes the Software Catalog as a centralized inventory of software ownership and metadata, with YAML metadata stored with code and harvested into the UI. Its system model uses Components, APIs, Resources and extensible entity kinds.

**Take into FATHER:**
- first-class typed entities;
- ownership;
- relations between entities;
- metadata-as-code;
- docs attached to entities;
- extensible object types.

**Do not copy blindly:**
- FATHER project stages and evidence gates are richer than a normal service catalog.

Sources:
- https://backstage.io/docs/features/software-catalog/
- https://backstage.io/docs/getting-started/viewing-catalog/
- https://backstage.io/docs/features/techdocs/getting-started/

---

## 2. GitHub — take commit-bound status evidence

GitHub status checks are tied to repository/commit conditions and can be required before merge.

**Take into FATHER:**
- every green DevSecOps/Security state points to exact evidence;
- evidence freshness is checked against the current commit;
- merge readiness is calculated, not decorative;
- required checks may block promotion.

**Additional FATHER rule:**
- NOT_RUN is never PASS;
- an approved waiver is a separate explicit state.

Source:
- https://docs.github.com/en/pull-requests/reference/status-checks

---

## 3. GitLab — take value-stream stage analytics

GitLab Value Stream Analytics models a value stream as stages with start/end events and calculates time spent through the development lifecycle. Its dashboards combine lifecycle, DORA and security signals.

**Take into FATHER:**
- stage start/end events;
- time-in-stage;
- bottleneck detection;
- portfolio comparison across projects;
- DORA/operations metrics later;
- security exposure visible next to delivery state.

**FATHER extension:**
- stages begin before code: Idea, PM, Security, Compliance, BA, SA, Requirements, Pre-Design.

Sources:
- https://docs.gitlab.com/user/group/value_stream_analytics/
- https://docs.gitlab.com/user/analytics/value_streams_dashboard/
- https://docs.gitlab.com/user/application_security/security_dashboard/

---

## 4. Argo CD — take health/status tree + drill-down

Argo CD exposes health states and resource trees where nodes show status and can be opened for detail. Health is derived from explicit resource state rather than a decorative color.

**Take into FATHER:**
- stage/project graph with compact status icons;
- click node → detailed condition panel;
- explicit conditions and timestamps;
- separate local node status from overall project status.

**Important design lesson:**
- do not infer a parent is healthy merely because most children look healthy;
- hard blockers must remain visible.

Sources:
- https://argo-cd.readthedocs.io/en/latest/operator-manual/health/
- https://argo-cd.readthedocs.io/en/latest/user-guide/application-set-ui/

---

## 5. Port / OpsLevel — take scorecards and maturity checks

Port and OpsLevel use scorecards/rubrics/checks to evaluate catalog entities against defined engineering standards and maturity levels.

**Take into FATHER:**
- scorecards for Security, DevSecOps, Evidence, Documentation, Reliability;
- rule-based levels;
- exact failed checks visible;
- portfolio view of maturity;
- checks can evolve separately from source objects.

**FATHER rule:**
- scorecards help prioritize work but never hide a hard gate blocker.

Sources:
- https://docs.port.io/governance/standards-and-compliance/concepts-and-structure/
- https://docs.port.io/governance/standards-and-compliance/overview/
- https://docs.opslevel.com/docs/getting-started-with-rubrics
- https://docs.opslevel.com/docs/maturity-report

---

## 6. Harness — take plugin/card/tab extensibility

Harness IDP supports software catalog pages extended with cards, tabs and plugins showing CI/CD, alerts, incidents and project state.

**Take into FATHER:**
- project workspace as extensible tabs;
- Git, Security, Cost, Test, Operations can be independent modules;
- source metadata remains tied to catalog entity;
- later self-service workflows can trigger approved factory actions.

**Do not take yet:**
- heavy plugin platform for the first prototype.

Sources:
- https://developer.harness.io/docs/internal-developer-portal/plugins/enable-a-new-plugin/
- https://developer.harness.io/docs/internal-developer-portal/flows/workflows-tutorials/create-a-new-service-using-idp-stage/

---

## 7. Azure DevOps — take unified lifecycle navigation

Azure DevOps unifies work planning, repositories, pipelines, artifacts and test plans with customizable dashboards.

**Take into FATHER:**
- one project workspace rather than separate disconnected tools;
- fast switching between work, Git, tests and deployment/evidence;
- dashboard as operational summary, not source of truth.

Source:
- https://learn.microsoft.com/azure/devops

---

# Prototype UX selected for FATHER

## Level 1 — Portfolio

Project cards:
- current stage;
- Product/Security/Architecture gates;
- branch condition;
- evidence completeness;
- risk/blocker summary.

## Level 2 — Project Workbench

Three primary visual surfaces:

1. **Production Conveyor**
   - stages as clickable nodes;
   - explicit state and owner;
   - documents/gate/blockers on node.

2. **Stage Inspector**
   - Overview
   - Documents
   - Specialist Analysis
   - Security/DevSecOps
   - Cost
   - History
   - Lessons

3. **Engineering Rail**
   - Git branch state;
   - checks;
   - scorecards;
   - evidence freshness;
   - merge readiness.

## Level 3 — Cross-project views

Later:
- Git Workspace;
- Manufacturing KB;
- cost/risk heatmaps;
- value-stream timing;
- maturity reports;
- reusable patterns.

---

# What not to do

- Do not create a giant dashboard with one misleading percentage.
- Do not show green without evidence.
- Do not hide blockers inside aggregate maturity scores.
- Do not copy GitHub/GitLab UI wholesale.
- Do not require Kubernetes to use the project model.
- Do not add a heavy frontend dependency before the UX/data model is proven.

---

# Prototype implementation choice

For the first visual prototype use plain HTML/CSS/JavaScript with no external runtime dependency.

Why:
- the repository currently has no established frontend;
- zero new npm supply-chain surface;
- instant local preview;
- enough to validate the information architecture;
- can later migrate to React/React Flow after the UX model is proven.

The prototype reads FATHER registry/snapshot JSON and uses a small stage-state snapshot for the two existing projects.
