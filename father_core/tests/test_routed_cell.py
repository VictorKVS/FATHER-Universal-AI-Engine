from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from father_core import build_cell


class RoutedCellTests(unittest.TestCase):
    def test_cell_002_falls_back_to_second_model(self) -> None:
        cell = build_cell(
            repo_root=REPO_ROOT,
            cell_id="CELL-002",
            test_mode=True,
        )
        result = cell.run({"task": "fallback proof"})

        self.assertEqual(result.status, "SUCCEEDED")
        self.assertEqual(result.routing_mode, "PRIMARY_FALLBACK")
        self.assertEqual(len(result.attempts), 2)
        self.assertEqual(result.attempts[0].status, "FAILED")
        self.assertEqual(
            result.attempts[0].error_code,
            "TEST_FORCED_FAILURE",
        )
        self.assertEqual(result.attempts[1].status, "SUCCEEDED")
        self.assertEqual(
            result.selected_model_id,
            "FATHER-MODEL-DETERMINISTIC-TEST-001",
        )
        self.assertTrue(result.routing_evidence["fallback_used"])
        self.assertTrue(
            result.routing_evidence[
                "semantic_input_hash_consistent"
            ]
        )
        self.assertEqual(
            result.attempts[0].evidence.input_sha256,
            result.attempts[1].evidence.input_sha256,
        )

    def test_real_two_model_cell_fails_closed_without_both_configs(self) -> None:
        with patch.dict(
            os.environ,
            {
                "FATHER_LLM_A_BASE_URL": "",
                "FATHER_LLM_A_MODEL": "",
                "FATHER_LLM_A_API_KEY": "",
                "FATHER_LLM_B_BASE_URL": "",
                "FATHER_LLM_B_MODEL": "",
                "FATHER_LLM_B_API_KEY": "",
            },
            clear=False,
        ):
            cell = build_cell(
                repo_root=REPO_ROOT,
                cell_id="CELL-002",
                test_mode=False,
            )
            result = cell.run("hello")

        self.assertEqual(result.status, "FAILED")
        self.assertEqual(len(result.attempts), 2)
        self.assertIsNone(result.selected_model_id)
        self.assertIsNone(result.output)
        self.assertEqual(
            [item.error_code for item in result.attempts],
            [
                "MODEL_ENV_UNAVAILABLE",
                "MODEL_ENV_UNAVAILABLE",
            ],
        )


if __name__ == "__main__":
    unittest.main()
