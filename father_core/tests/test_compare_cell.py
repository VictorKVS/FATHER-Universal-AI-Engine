from __future__ import annotations

import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from father_core import build_cell


class CompareCellTests(unittest.TestCase):
    def test_cell_003_compares_two_successful_model_runs(self) -> None:
        cell = build_cell(
            repo_root=REPO_ROOT,
            cell_id="CELL-003",
            test_mode=True,
        )
        result = cell.run({"task": "compare proof"})

        self.assertEqual(result.status, "SUCCEEDED")
        self.assertEqual(result.mode, "FAN_OUT_COMPARE")
        self.assertEqual(len(result.runs), 2)
        self.assertTrue(result.comparison["semantic_input_equal"])
        self.assertTrue(result.comparison["both_succeeded"])
        self.assertFalse(result.comparison["output_exact_match"])
        self.assertFalse(result.comparison["selection_made"])
        self.assertEqual(
            result.comparison["selection_reason"],
            "NO_JUDGE_IN_CELL_003",
        )
        self.assertEqual(
            result.runs[0].evidence.input_sha256,
            result.runs[1].evidence.input_sha256,
        )
        self.assertNotEqual(
            result.runs[0].evidence.output_sha256,
            result.runs[1].evidence.output_sha256,
        )


if __name__ == "__main__":
    unittest.main()
