#!/usr/bin/env python3
"""Validate the local Markdown catalog without making network requests."""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path
from urllib.parse import urlparse

URL_PATTERN = re.compile(
    r"^\*\*URL:\*\*\s*\[([^\]]+)\]\((https?://[^)]+)\)\s*$",
    re.MULTILINE,
)
DESCRIPTION_PATTERN = re.compile(r"^\*\*Description:\*\*\s*.+$", re.MULTILINE)
KEYWORDS_PATTERN = re.compile(r"^\*\*Matched Keywords:\*\*\s*.+$", re.MULTILINE)
TOPICS_PATTERN = re.compile(r"^\*\*Topics:\*\*\s*.+$", re.MULTILINE)

TAXONOMY_ALIASES = {
    "ml": "machine-learning",
    "ML": "machine-learning",
    "machine_learning": "machine-learning",
    "neural-network": "neural-networks",
    "llm": "large-language-models",
    "LLM": "large-language-models",
    "dfir": "digital-forensics-incident-response",
    "DFIR": "digital-forensics-incident-response",
    "ai_agent": "ai-agents",
    "generative_ai": "generative-ai",
}


def normalize_taxonomy(folder_name: str) -> str:
    return TAXONOMY_ALIASES.get(folder_name, folder_name.replace("_", "-").lower())


def canonical_github_repo(url: str) -> str | None:
    parsed = urlparse(url)
    if parsed.scheme != "https" or parsed.hostname != "github.com":
        return None
    if parsed.username or parsed.password or parsed.port not in (None, 443):
        return None
    segments = [segment for segment in parsed.path.strip("/").split("/") if segment]
    if len(segments) != 2:
        return None
    owner, repository = segments
    if not re.fullmatch(r"[A-Za-z0-9_.-]+", owner):
        return None
    if not re.fullmatch(r"[A-Za-z0-9_.-]+", repository):
        return None
    return f"{owner.lower()}/{repository.removesuffix('.git').lower()}"


def audit_catalog(root: str | Path) -> dict:
    root = Path(root).resolve()
    index_roots = (root / "By_Agency", root / "By_Interest_Area")
    records = []
    errors = []
    warnings = []
    taxonomy_counts: dict[str, int] = defaultdict(int)

    for index_root in index_roots:
        if not index_root.is_dir():
            errors.append(f"Missing catalog directory: {index_root.name}")
            continue
        index_type = index_root.name
        for file_path in sorted(index_root.rglob("*.md")):
            relative_path = file_path.relative_to(root).as_posix()
            folder = file_path.parent.name
            if file_path.parent == index_root:
                errors.append(f"Catalog card is not inside a category folder: {relative_path}")
                continue
            taxonomy = normalize_taxonomy(folder) if index_type == "By_Interest_Area" else None
            if taxonomy:
                taxonomy_counts[taxonomy] += 1

            try:
                content = file_path.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError) as error:
                errors.append(f"Cannot read {relative_path}: {type(error).__name__}")
                continue

            matches = URL_PATTERN.findall(content)
            if len(matches) != 1:
                errors.append(
                    f"{relative_path}: expected exactly one canonical URL field, found {len(matches)}"
                )
                continue

            display_url, linked_url = matches[0]
            canonical = canonical_github_repo(linked_url)
            if canonical is None or display_url.rstrip("/") != linked_url.rstrip("/"):
                errors.append(f"{relative_path}: URL must be a canonical https://github.com/owner/repo link")
                continue

            title_match = re.search(r"^#\s+([^\r\n]+)", content, re.MULTILINE)
            if not title_match:
                warnings.append(f"{relative_path}: missing Markdown title")
            elif title_match.group(1).strip().lower() != canonical:
                warnings.append(
                    f"{relative_path}: title does not match canonical repository {canonical}"
                )

            if not DESCRIPTION_PATTERN.search(content):
                warnings.append(f"{relative_path}: missing description")
            if not KEYWORDS_PATTERN.search(content):
                warnings.append(f"{relative_path}: missing matched-keywords field")
            if not TOPICS_PATTERN.search(content):
                warnings.append(f"{relative_path}: missing topics field")

            records.append({
                "path": relative_path,
                "index": index_type,
                "repository": canonical,
                "taxonomy": taxonomy,
            })

    paths_by_repo: dict[str, list[str]] = defaultdict(list)
    indexes_by_repo: dict[str, set[str]] = defaultdict(set)
    for record in records:
        paths_by_repo[record["repository"]].append(record["path"])
        indexes_by_repo[record["repository"]].add(record["index"])

    duplicate_references = [
        {"repository": repository, "paths": sorted(paths)}
        for repository, paths in sorted(paths_by_repo.items())
        if len(paths) > 1
    ]
    cross_index_references = [
        item for item in duplicate_references
        if len(indexes_by_repo[item["repository"]]) > 1
    ]
    same_index_duplicates = [
        item for item in duplicate_references
        if len(indexes_by_repo[item["repository"]]) == 1
    ]

    return {
        "catalog_cards_validated": len(records),
        "errors": errors,
        "warnings": warnings,
        "duplicate_repository_references": duplicate_references,
        "expected_cross_index_references": cross_index_references,
        "same_index_duplicates": same_index_duplicates,
        "normalized_interest_taxonomy": dict(sorted(taxonomy_counts.items())),
        "network_checks_performed": False,
        "limitations": [
            "This validates local Markdown structure and URL syntax only.",
            "It does not confirm that an upstream repository exists, is current, safe, official, or licensed for reuse.",
            "Cross-index references are expected in a dual-index catalog; metadata consistency is not guaranteed by URL matching alone.",
        ],
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".", help="Catalog repository root")
    args = parser.parse_args(argv)
    report = audit_catalog(args.root)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 1 if report["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
