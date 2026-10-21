from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from father_core import FactoryCell
from father_core.zoo import Zoo, ZooError


class FactoryCellTests(unittest.TestCase):
    def test_zoo_resolves_cell_agent_and_model(self) -> None:
        zoo = Zoo(REPO_ROOT)
        cell = zoo.cell("CELL-001")
        agent = zoo.agent(cell["agent_id"])
        model = zoo.model(cell["test_model_id"])

        self.assertEqual(agent["agent_id"], "FATHER-MINIMAL-AGENT-001")
        self.assertEqual(
            model["model_id"],
            "FATHER-MODEL-DETERMINISTIC-TEST-001",
        )

    def test_existing_design_agent_is_indexed_but_not_runtime_ready(self) -> None:
        zoo = Zoo(REPO_ROOT)
        with self.assertRaises(ZooError):
            zoo.agent("FATHER-OPS-TIMA-001")

    def test_text_run_uses_one_agent_one_model_contract(self) -> None:
        cell = FactoryCell(
            repo_root=REPO_ROOT,
            cell_id="CELL-001",
            test_mode=True,
        )
        result = cell.run("hello")

        self.assertEqual(result.status, "SUCCEEDED")
        self.assertEqual(result.input.content_type, "text/plain")
        self.assertIsNotNone(result.output)
        self.assertEqual(
            result.output.payload,
            "DETERMINISTIC_RESULT: hello",
        )
        self.assertEqual(
            result.evidence.agent_id,
            "FATHER-MINIMAL-AGENT-001",
        )
        self.assertEqual(
            result.evidence.model_id,
            "FATHER-MODEL-DETERMINISTIC-TEST-001",
        )
        self.assertEqual(
            result.evidence.adapter_type,
            "deterministic_test",
        )
        self.assertTrue(result.evidence.input_sha256)
        self.assertTrue(result.evidence.output_sha256)
        self.assertFalse(
            result.output.constraints["hidden_reasoning_persistence"]
        )

    def test_json_input_passes_same_processor(self) -> None:
        cell = FactoryCell(
            repo_root=REPO_ROOT,
            cell_id="CELL-001",
            test_mode=True,
        )
        result = cell.run({"z": 2, "a": 1})

        self.assertEqual(result.status, "SUCCEEDED")
        self.assertEqual(
            result.input.content_type,
            "application/json",
        )
        self.assertIn('"a": 1', result.output.payload)
        self.assertEqual(
            result.evidence.transformations,
            [
                "INPUT_NORMALIZE",
                "AGENT_CONTEXT_BUILD",
                "MODEL_REQUEST_BUILD",
                "MODEL_INVOKE",
                "OUTPUT_NORMALIZE",
            ],
        )

    def test_real_model_missing_environment_fails_closed(self) -> None:
        with patch.dict(
            "os.environ",
            {
                "FATHER_LLM_BASE_URL": "",
                "FATHER_LLM_MODEL": "",
                "FATHER_LLM_API_KEY": "",
            },
            clear=False,
        ):
            cell = FactoryCell(
                repo_root=REPO_ROOT,
                cell_id="CELL-001",
                test_mode=False,
            )
            result = cell.run("hello")

        self.assertEqual(result.status, "FAILED")
        self.assertEqual(
            result.error_code,
            "MODEL_ENV_UNAVAILABLE",
        )
        self.assertIsNone(result.output)
        self.assertIsNone(result.evidence.output_sha256)

    def test_run_result_contains_no_environment_secret(self) -> None:
        secret = "VERY-SECRET-DO-NOT-PERSIST"
        with patch.dict(
            "os.environ",
            {"FATHER_LLM_API_KEY": secret},
            clear=False,
        ):
            cell = FactoryCell(
                repo_root=REPO_ROOT,
                cell_id="CELL-001",
                test_mode=True,
            )
            result = cell.run("safe input")

        encoded = json.dumps(
            result.to_dict(),
            ensure_ascii=False,
        )
        self.assertNotIn(secret, encoded)


if __name__ == "__main__":
    unittest.main()
