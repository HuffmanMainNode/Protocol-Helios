import json

from scripts.catalog_audit import audit_catalog, canonical_github_repo, normalize_taxonomy


CARD = """# example/project

**Description:** Example project description.

**URL:** [https://github.com/example/project](https://github.com/example/project)

**Matched Keywords:** framework, security

**Topics:** None
"""


def test_validates_catalog_cards_and_expected_cross_index_duplicates(tmp_path):
    agency = tmp_path / "By_Agency" / "Example"
    interest = tmp_path / "By_Interest_Area" / "ML"
    agency.mkdir(parents=True)
    interest.mkdir(parents=True)
    (agency / "project.md").write_text(CARD, encoding="utf-8")
    (interest / "project.md").write_text(CARD, encoding="utf-8")

    report = audit_catalog(tmp_path)
    assert report["catalog_cards_validated"] == 2
    assert report["errors"] == []
    assert len(report["expected_cross_index_references"]) == 1
    assert report["same_index_duplicates"] == []
    assert report["normalized_interest_taxonomy"]["machine-learning"] == 1


def test_rejects_noncanonical_or_malformed_urls(tmp_path):
    folder = tmp_path / "By_Agency" / "Example"
    folder.mkdir(parents=True)
    malformed = CARD.replace(
        "https://github.com/example/project",
        "https://github.com.example.evil/project",
    )
    (folder / "bad.md").write_text(malformed, encoding="utf-8")

    report = audit_catalog(tmp_path)
    assert report["catalog_cards_validated"] == 0
    assert any("canonical https" in error for error in report["errors"])


def test_requires_one_url_field(tmp_path):
    folder = tmp_path / "By_Agency" / "Example"
    folder.mkdir(parents=True)
    (folder / "missing.md").write_text("# example/project\nNo URL.\n", encoding="utf-8")

    report = audit_catalog(tmp_path)
    assert any("found 0" in error for error in report["errors"])


def test_canonical_url_and_taxonomy_helpers():
    assert canonical_github_repo("https://github.com/Example/Project.git") == "example/project"
    assert canonical_github_repo("http://github.com/example/project") is None
    assert canonical_github_repo("https://github.com.example.evil/example/project") is None
    assert canonical_github_repo("https://github.com/example/project/tree/main") is None
    assert normalize_taxonomy("machine_learning") == "machine-learning"
    assert normalize_taxonomy("DFIR") == "digital-forensics-incident-response"
