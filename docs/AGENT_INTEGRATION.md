# Agent Integration Guide

Protocol Helios provides a local catalog of public GitHub repository links. It is a discovery aid, not a trust authority.

## Generate the machine-readable index

From the repository root:

```bash
python scripts/catalog_export.py --output reports/catalog-index.json
```

Or write JSON to standard output:

```bash
python scripts/catalog_export.py
```

The export is built from the validated Markdown cards and follows [catalog-index.schema.json](../schemas/catalog-index.schema.json).

## Required agent behavior

1. Treat each entry as a lead for research, not a recommendation or trusted dependency.
2. Preserve `source_card` so a human can inspect the original catalog entry.
3. Treat `matched_keywords` and `category` as discovery hints. They can be false positives.
4. Do not infer government ownership or endorsement from an agency folder.
5. Independently check upstream existence, owner, archived status, activity, license, security policy, and suitability before use.
6. Do not clone, execute, install, or invoke an upstream project merely because it appears in this catalog.
7. Do not infer permission to reuse code when a license is missing or unclear.
8. Keep the distinction between a catalog's local metadata and independently verified upstream evidence.

## Duplicate handling

The same repository may have multiple entries because it appears in both agency and interest-area indexes. The export deliberately preserves those cards and their paths. Group by the normalized `repository` field only when a unique-repository view is needed; do not discard source-card provenance.

## Status fields

- `classification_status=discovery_hint_requires_human_review`: category and keyword labels are not validated semantic claims.
- `upstream_status=not_checked_by_export`: export is offline and did not query GitHub.

The optional [upstream status refresh](UPSTREAM_STATUS.md) checks limited GitHub metadata. It does not establish source-code safety, official status, or license rights.
