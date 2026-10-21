from __future__ import annotations

import importlib.util
import json
import unittest
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = APP_DIR.parents[1]
SERVER_FILE = APP_DIR / "server.py"

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

    def test_browser_credentials_are_forbidden(self) -> None:
        data = json.loads(
            (REPO_ROOT / "config" / "dev_platform" / "providers.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertFalse(data["rules"]["credentials_in_browser"])


if __name__ == "__main__":
    unittest.main()
