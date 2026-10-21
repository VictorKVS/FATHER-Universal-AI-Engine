from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from document_store import DocumentConflictError, DocumentStore


class DocumentStoreTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.store = DocumentStore(self.root)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_create_and_edit_markdown_with_optimistic_hash(self) -> None:
        initial = self.store.read("docs/demo.md")
        self.assertFalse(initial["exists"])
        self.assertEqual(initial["sha256"], "NEW")

        created = self.store.write(
            "docs/demo.md",
            "# Demo\n",
            "NEW",
        )
        self.assertTrue(created["changed"])

        loaded = self.store.read("docs/demo.md")
        updated = self.store.write(
            "docs/demo.md",
            "# Demo\n\nUpdated.\n",
            loaded["sha256"],
        )
        self.assertNotEqual(
            updated["old_sha256"],
            updated["new_sha256"],
        )

    def test_stale_hash_is_rejected(self) -> None:
        self.store.write("docs/demo.md", "one", "NEW")
        loaded = self.store.read("docs/demo.md")
        self.store.write(
            "docs/demo.md",
            "two",
            loaded["sha256"],
        )
        with self.assertRaises(DocumentConflictError):
            self.store.write(
                "docs/demo.md",
                "stale",
                loaded["sha256"],
            )

    def test_path_escape_and_code_roots_are_rejected(self) -> None:
        for source_ref in (
            "../secret.txt",
            "prototype/app.py",
            ".github/workflows/ci.yml",
            "scripts/tool.py",
        ):
            with self.subTest(source_ref=source_ref):
                with self.assertRaises(ValueError):
                    self.store.resolve(source_ref)

    def test_invalid_json_is_rejected_before_write(self) -> None:
        with self.assertRaises(ValueError):
            self.store.write(
                "config/demo.json",
                "{invalid",
                "NEW",
            )


if __name__ == "__main__":
    unittest.main()
