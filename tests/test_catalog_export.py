import tempfile
import unittest
from pathlib import Path

from scripts.catalog_export import export_catalog


CARD = """# example/project

**Description:** A sample research repository.

**URL:** [https://github.com/example/project](https://github.com/example/project)

**Matched Keywords:** ML, research

**Topics:** machine-learning, research
"""


class CatalogExportTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.addCleanup(self.temp_dir.cleanup)

    def test_exports_machine_readable_entries_and_preserves_source_cards(self):
        agency = self.root / "By_Agency" / "Example"
        interest = self.root / "By_Interest_Area" / "ML"
        agency.mkdir(parents=True)
        interest.mkdir(parents=True)
        (agency / "project.md").write_text(CARD, encoding="utf-8")
        (interest / "project.md").write_text(CARD, encoding="utf-8")

        report = export_catalog(self.root)

        self.assertEqual(report["schema_version"], "1.0.0")
        self.assertEqual(report["catalog_card_count"], 2)
        self.assertEqual(report["unique_repository_count"], 1)
        self.assertEqual({entry["repository"] for entry in report["entries"]}, {"example/project"})
        self.assertEqual(
            {entry["category"] for entry in report["entries"]},
            {"Example", "machine-learning"},
        )
        self.assertTrue(all(
            entry["classification_status"] == "discovery_hint_requires_human_review"
            for entry in report["entries"]
        ))
        self.assertTrue(all(entry["upstream_status"] == "not_checked_by_export" for entry in report["entries"]))
        self.assertEqual(len({entry["source_card"] for entry in report["entries"]}), 2)

    def test_refuses_to_export_invalid_catalog(self):
        folder = self.root / "By_Agency" / "Example"
        folder.mkdir(parents=True)
        (folder / "broken.md").write_text("# broken\nNo canonical URL.\n", encoding="utf-8")

        with self.assertRaises(ValueError):
            export_catalog(self.root)


if __name__ == "__main__":
    unittest.main()
