from __future__ import annotations

import sys
import unittest
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from migration_engine import build_migration_plan


class MigrationEngineTests(unittest.TestCase):
    def setUp(self) -> None:
        self.project = {
            "project_id": "P-1",
            "repository": "owner/repo",
            "branch": "feature/demo",
            "dev_platform": {
                "primary_provider": "github",
                "repository": "owner/repo",
                "branch": "feature/demo",
            },
        }
        self.registry = {
            "providers": [
                {
                    "id": "github",
                    "adapter_status": "IMPLEMENTED_READ_WRITE_LIMITED",
                },
                {
                    "id": "gitlab",
                    "adapter_status": "IMPLEMENTED_READ_WRITE_LIMITED",
                },
                {
                    "id": "gitverse",
                    "adapter_status": "IMPLEMENTED_READ_ONLY",
                },
                {
                    "id": "planned",
                    "adapter_status": "PLANNED",
                },
            ]
        }

    def test_plan_preserves_project_identity_and_requires_evidence(self) -> None:
        plan = build_migration_plan(
            self.project,
            "gitlab",
            self.registry,
        )
        self.assertEqual(plan["project_id"], "P-1")
        self.assertEqual(plan["source_provider"], "github")
        self.assertEqual(plan["target_provider"], "gitlab")
        self.assertIn("REF_PARITY_REPORT", plan["required_evidence"])
        self.assertIn("MIGRATION_EXECUTION_NOT_IMPLEMENTED", plan["blockers"])
        self.assertFalse(plan["executable"])

    def test_same_provider_is_blocked(self) -> None:
        plan = build_migration_plan(
            self.project,
            "github",
            self.registry,
        )
        self.assertIn("TARGET_EQUALS_SOURCE", plan["blockers"])

    def test_planned_target_adapter_is_visible_blocker(self) -> None:
        plan = build_migration_plan(
            self.project,
            "planned",
            self.registry,
        )
        self.assertIn("TARGET_ADAPTER_NOT_IMPLEMENTED", plan["blockers"])

    def test_read_only_target_warns_about_write_capability(self) -> None:
        plan = build_migration_plan(
            self.project,
            "gitverse",
            self.registry,
        )
        self.assertIn("TARGET_WRITE_CAPABILITY_INCOMPLETE", plan["warnings"])


if __name__ == "__main__":
    unittest.main()
