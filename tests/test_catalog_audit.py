import tempfile
import unittest
from pathlib import Path

from scripts.catalog_audit import audit_catalog, canonical_github_repo, normalize_taxonomy


CARD = """# example/project

**Description:** Example project description.

**URL:** [https://github.com/example/project](https://github.com/example/project)

**Matched Keywords:** framework, security

**Topics:** None
"""


class CatalogAuditTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.addCleanup(self.temp_dir.cleanup)

    def test_validates_cards_and_expected_cross_index_duplicates(self):
        agency = self.root / "By_Agency" / "Example"
        interest = self.root / "By_Interest_Area" / "ML"
        agency.mkdir(parents=True)
        interest.mkdir(parents=True)
        (agency / "project.md").write_text(CARD, encoding="utf-8")
        (interest / "project.md").write_text(CARD, encoding="utf-8")

        report = audit_catalog(self.root)
        self.assertEqual(report["catalog_cards_validated"], 2)
        self.assertEqual(report["errors"], [])
        self.assertEqual(len(report["expected_cross_index_references"]), 1)
        self.assertEqual(report["same_index_duplicates"], [])
        self.assertEqual(report["normalized_interest_taxonomy"]["machine-learning"], 1)

    def test_detects_same_index_duplicates_even_when_cross_indexed(self):
        agency = self.root / "By_Agency" / "Example"
        interest = self.root / "By_Interest_Area" / "ML"
        agency.mkdir(parents=True)
        interest.mkdir(parents=True)
        (agency / "project-one.md").write_text(CARD, encoding="utf-8")
        (agency / "project-two.md").write_text(CARD, encoding="utf-8")
        (interest / "project.md").write_text(CARD, encoding="utf-8")

        report = audit_catalog(self.root)

        self.assertEqual(len(report["expected_cross_index_references"]), 1)
        self.assertEqual(len(report["same_index_duplicates"]), 1)
        self.assertEqual(report["same_index_duplicates"][0]["index"], "By_Agency")
        self.assertEqual(len(report["same_index_duplicates"][0]["paths"]), 2)

    def test_rejects_noncanonical_or_malformed_urls(self):
        folder = self.root / "By_Agency" / "Example"
        folder.mkdir(parents=True)
        malformed = CARD.replace(
            "https://github.com/example/project",
            "https://github.com.example.evil/project",
        )
        (folder / "bad.md").write_text(malformed, encoding="utf-8")

        report = audit_catalog(self.root)
        self.assertEqual(report["catalog_cards_validated"], 0)
        self.assertTrue(any("canonical https" in error for error in report["errors"]))

    def test_requires_one_url_field(self):
        folder = self.root / "By_Agency" / "Example"
        folder.mkdir(parents=True)
        (folder / "missing.md").write_text("# example/project\nNo URL.\n", encoding="utf-8")

        report = audit_catalog(self.root)
        self.assertTrue(any("found 0" in error for error in report["errors"]))

    def test_canonical_url_and_taxonomy_helpers(self):
        self.assertEqual(
            canonical_github_repo("https://github.com/Example/Project.git"),
            "example/project",
        )
        self.assertIsNone(canonical_github_repo("http://github.com/example/project"))
        self.assertIsNone(canonical_github_repo("https://github.com.example.evil/example/project"))
        self.assertIsNone(canonical_github_repo("https://github.com/example/project/tree/main"))
        self.assertIsNone(canonical_github_repo("https://github.com/example/project?tab=readme"))
        self.assertEqual(normalize_taxonomy("machine_learning"), "machine-learning")
        self.assertEqual(
            normalize_taxonomy("DFIR"),
            "digital-forensics-incident-response",
        )


if __name__ == "__main__":
    unittest.main()
