#!/usr/bin/env python3
"""Export the local Protocol Helios catalog as a machine-readable JSON index."""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

try:
    from scripts.catalog_audit import (
        audit_catalog,
        canonical_github_repo,
        normalize_taxonomy,
        URL_PATTERN,
    )
except ModuleNotFoundError as error:
    # Support both package import in tests and direct execution as a script.
    if error.name != "scripts":
        raise
    from catalog_audit import (
        audit_catalog,
        canonical_github_repo,
        normalize_taxonomy,
        URL_PATTERN,
    )

FIELD_PATTERNS = {
    "description": re.compile(r"^\*\*Description:\*\*\s*(.*)$", re.MULTILINE),
    "keywords": re.compile(r"^\*\*Matched Keywords:\*\*\s*(.*)$", re.MULTILINE),
    "topics": re.compile(r"^\*\*Topics:\*\*\s*(.*)$", re.MULTILINE),
}


def split_values(value: str) -> list[str]:
    if not value.strip() or value.strip().lower() == "none":
        return []
    return sorted({item.strip() for item in value.split(",") if item.strip()}, key=str.casefold)


def export_catalog(root: str | Path) -> dict:
    root = Path(root).resolve()
    audit = audit_catalog(root)
    if audit["errors"]:
        raise ValueError("Catalog validation errors must be fixed before export.")

    entries = []
    for index_root in (root / "By_Agency", root / "By_Interest_Area"):
        index_type = index_root.name
        for card_path in sorted(index_root.rglob("*.md")):
            content = card_path.read_text(encoding="utf-8")
            matches = URL_PATTERN.findall(content)
            if len(matches) != 1:
                continue
            _display_url, linked_url = matches[0]
            repository = canonical_github_repo(linked_url)
            if repository is None:
                continue

            fields = {}
            for name, pattern in FIELD_PATTERNS.items():
                match = pattern.search(content)
                fields[name] = match.group(1).strip() if match else ""

            category = card_path.parent.name
            entries.append({
                "repository": repository,
                "url": f"https://github.com/{repository}",
                "index": index_type,
                "category": (
                    normalize_taxonomy(category)
                    if index_type == "By_Interest_Area"
                    else category
                ),
                "description": fields["description"],
                "matched_keywords": split_values(fields["keywords"]),
                "upstream_topics": split_values(fields["topics"]),
                "source_card": card_path.relative_to(root).as_posix(),
                "classification_status": "discovery_hint_requires_human_review",
                "upstream_status": "not_checked_by_export",
            })

    entries.sort(key=lambda item: (
        item["repository"],
        item["index"],
        item["category"].casefold(),
        item["source_card"],
    ))
    return {
        "schema_version": "1.0.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "catalog_card_count": len(entries),
        "unique_repository_count": len({entry["repository"] for entry in entries}),
        "entries": entries,
        "interpretation": {
            "classification": "Matched keywords and categories are discovery hints, not verified semantic classifications.",
            "upstream_status": "No live upstream status was checked during this export.",
            "source_card": "Path to the original Markdown catalog card in this repository.",
        },
        "limitations": [
            "A catalog entry does not prove that an upstream repository exists, is maintained, official, safe, or licensed for reuse.",
            "Cross-index entries are intentionally retained as separate source cards; group by repository when a unique-repository view is needed.",
            "Keyword matches can be false positives and require human review.",
            "This export performs no network requests and does not inspect upstream source code.",
        ],
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".", help="Catalog repository root")
    parser.add_argument("--output", help="Optional JSON output path; defaults to stdout")
    args = parser.parse_args(argv)
    try:
        report = export_catalog(args.root)
    except (OSError, UnicodeDecodeError, ValueError) as error:
        print(f"Catalog export failed: {error}", file=sys.stderr)
        return 2

    rendered = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
