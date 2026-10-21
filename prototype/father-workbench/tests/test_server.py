from __future__ import annotations

import importlib.util
import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

APP_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = APP_DIR.parents[1]
SERVER_FILE = APP_DIR / "server.py"
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

spec = importlib.util.spec_from_file_location("father_workbench_server", SERVER_FILE)
server = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(server)


class ActionPolicyTests(unittest.TestCase):
    def test_safe_branch_plan_is_ready_without_provider_mutation(self) -> None:
        plan = server.plan_action("FATHER-ACADEMY-OSINT-001", "SCM.CREATE_BRANCH")
        self.assertTrue(plan["allowed"])
        self.assertEqual(plan["status"], "READY")
        self.assertFalse(plan["provider_mutation"])

    def test_academy_merge_is_blocked(self) -> None:
        plan = server.plan_action(
            "FATHER-ACADEMY-OSINT-001",
            "SCM.MERGE_CHANGE_REQUEST",
        )
        self.assertFalse(plan["allowed"])
        self.assertEqual(plan["status"], "BLOCKED")
        self.assertIn("SECURITY_GATE_NOT_PASS", plan["reasons"])
        self.assertIn("EXPLICIT_MERGE_APPROVAL_REQUIRED", plan["reasons"])

    def test_provider_switch_requires_migration_evidence(self) -> None:
        plan = server.plan_action(
            "FATHER-ACADEMY-OSINT-001",
            "PROVIDER.SWITCH_PRIMARY",
        )
        self.assertFalse(plan["allowed"])
        self.assertIn(
            "MIGRATION_VERIFICATION_EVIDENCE_REQUIRED",
            plan["reasons"],
        )

    def test_unknown_action_is_blocked(self) -> None:
        plan = server.plan_action(
            "FATHER-ACADEMY-OSINT-001",
            "SCM.FORCE_PUSH_EVERYTHING",
        )
        self.assertFalse(plan["allowed"])
        self.assertEqual(plan["reasons"], ["ACTION_NOT_ALLOWLISTED"])

    def test_unknown_project_is_blocked(self) -> None:
        plan = server.plan_action("DOES-NOT-EXIST", "SCM.CREATE_BRANCH")
        self.assertFalse(plan["allowed"])
        self.assertEqual(plan["reasons"], ["PROJECT_NOT_FOUND"])


class FakeEvidenceStore:
    def __init__(self, fail_store: bool = False) -> None:
        self.fail_store = fail_store
        self.events = []
        self.evidence = []

    def append_manufacturing_event(
        self,
        *,
        project_id,
        event_type,
        source_ref,
        payload,
    ):
        event = {
            "event_id": f"MFG-{len(self.events) + 1}",
            "project_id": project_id,
            "event_type": event_type,
            "source_ref": source_ref,
            "payload": payload,
        }
        self.events.append(event)
        return event

    def store_evidence(self, **kwargs):
        if self.fail_store:
            raise OSError("simulated evidence failure")
        evidence = {
            "evidence_id": f"EVD-{len(self.evidence) + 1}",
            "deduplicated": False,
            **kwargs,
        }
        self.evidence.append(evidence)
        return evidence


class ExecuteActionTests(unittest.TestCase):
    def test_create_branch_blocks_without_write_credential(self) -> None:
        class ReadOnlyAdapter:
            can_write = False

        with patch.object(server, "GitHubAdapter", return_value=ReadOnlyAdapter()):
            result = server.execute_action(
                "FATHER-PLATFORM-001",
                "SCM.CREATE_BRANCH",
                {"branch_name": "feature/test-write"},
            )

        self.assertFalse(result["allowed"])
        self.assertEqual(
            result["reasons"],
            ["PROVIDER_WRITE_CREDENTIAL_UNAVAILABLE"],
        )

    def test_open_change_request_writes_audit_before_and_after_mutation(self) -> None:
        events = []

        class WritableAdapter:
            can_write = True

            def open_change_request(
                self,
                repository,
                title,
                head_ref,
                base_ref,
                body="",
                draft=True,
            ):
                return {
                    "provider": "github",
                    "repository": repository,
                    "number": 5,
                    "title": title,
                    "state": "open",
                    "draft": draft,
                    "head_ref": head_ref,
                    "base_ref": base_ref,
                    "reconciled": True,
                }

        evidence_store = FakeEvidenceStore()
        with (
            patch.object(server, "GitHubAdapter", return_value=WritableAdapter()),
            patch.object(server, "write_audit_event", side_effect=events.append),
            patch.object(server, "EVIDENCE_STORE", evidence_store),
        ):
            result = server.execute_action(
                "FATHER-PLATFORM-001",
                "SCM.OPEN_CHANGE_REQUEST",
                {
                    "title": "Prototype PR",
                    "head_ref": "feature/father-project-registry-v01",
                    "base_ref": "main",
                    "draft": True,
                },
            )

        self.assertTrue(result["allowed"])
        self.assertEqual(result["status"], "SUCCEEDED")
        self.assertEqual([event["status"] for event in events], ["EXECUTING", "SUCCEEDED"])

    def test_create_branch_writes_audit_before_and_after_mutation(self) -> None:
        events = []

        class WritableAdapter:
            can_write = True

            def create_branch(self, repository, branch_name, base_ref):
                self.repository = repository
                self.branch_name = branch_name
                self.base_ref = base_ref
                return {
                    "provider": "github",
                    "repository": repository,
                    "branch": branch_name,
                    "base_ref": base_ref,
                    "head_sha": "abc123",
                    "reconciled": True,
                }

        evidence_store = FakeEvidenceStore()
        with (
            patch.object(server, "GitHubAdapter", return_value=WritableAdapter()),
            patch.object(server, "write_audit_event", side_effect=events.append),
            patch.object(server, "EVIDENCE_STORE", evidence_store),
        ):
            result = server.execute_action(
                "FATHER-PLATFORM-001",
                "SCM.CREATE_BRANCH",
                {
                    "branch_name": "feature/test-write",
                    "base_ref": "feature/father-project-registry-v01",
                },
            )

        self.assertTrue(result["allowed"])
        self.assertTrue(result["provider_mutation"])
        self.assertEqual(result["status"], "SUCCEEDED")
        self.assertEqual([event["status"] for event in events], ["EXECUTING", "SUCCEEDED"])


    def test_successful_mutation_reports_evidence_degradation(self) -> None:
        events = []

        class WritableAdapter:
            can_write = True

            def create_branch(self, repository, branch_name, base_ref):
                return {
                    "provider": "github",
                    "repository": repository,
                    "branch": branch_name,
                    "base_ref": base_ref,
                    "head_sha": "abc123",
                    "reconciled": True,
                }

        evidence_store = FakeEvidenceStore(fail_store=True)
        with (
            patch.object(server, "GitHubAdapter", return_value=WritableAdapter()),
            patch.object(server, "write_audit_event", side_effect=events.append),
            patch.object(server, "EVIDENCE_STORE", evidence_store),
        ):
            result = server.execute_action(
                "FATHER-PLATFORM-001",
                "SCM.CREATE_BRANCH",
                {
                    "branch_name": "feature/evidence-degraded",
                    "base_ref": "feature/father-project-registry-v01",
                },
            )

        self.assertTrue(result["provider_mutation"])
        self.assertFalse(result["allowed"])
        self.assertEqual(result["status"], "SUCCEEDED_EVIDENCE_DEGRADED")
        self.assertEqual(result["reasons"], ["EVIDENCE_PERSIST_FAILED"])
        self.assertEqual(
            [event["status"] for event in events],
            ["EXECUTING", "SUCCEEDED", "SUCCEEDED_EVIDENCE_DEGRADED"],
        )


class RegistryContractTests(unittest.TestCase):
    def test_project_ids_are_unique(self) -> None:
        data = json.loads(
            (REPO_ROOT / "projects" / "registry.json").read_text(encoding="utf-8")
        )
        ids = [project["project_id"] for project in data["projects"]]
        self.assertEqual(len(ids), len(set(ids)))

    def test_required_provider_families_are_registered(self) -> None:
        data = json.loads(
            (REPO_ROOT / "config" / "dev_platform" / "providers.json").read_text(
                encoding="utf-8"
            )
        )
        ids = {provider["id"] for provider in data["providers"]}
        self.assertTrue(
            {
                "github",
                "gitlab",
                "gitverse",
                "sourcecraft",
                "gitflic",
                "azure_devops",
                "bitbucket",
                "forgejo",
                "gitea",
            }.issubset(ids)
        )

    def test_stage_state_projection_matches_project(self) -> None:
        project = server.project_by_id("FATHER-ACADEMY-OSINT-001")
        self.assertIsNotNone(project)
        state = server.project_stage_state(project)
        self.assertEqual(state["project_id"], project["project_id"])
        self.assertTrue(state["stages"])

    def test_browser_credentials_are_forbidden(self) -> None:
        data = json.loads(
            (REPO_ROOT / "config" / "dev_platform" / "providers.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertFalse(data["rules"]["credentials_in_browser"])


if __name__ == "__main__":
    unittest.main()
