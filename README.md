# Protocol Helios

Protocol Helios is a curated index of public GitHub repositories associated with government agencies and public-sector research. It organizes repository cards by agency and by technical interest area to make discovery and manual review easier.

**This repository is a catalog, not a security audit service.** Listing a repository does not mean that it is safe, maintained, official, endorsed, or suitable for production use.

## Catalog structure

- `By_Agency/`: repository cards grouped by the agency or organization associated with the upstream GitHub owner.
- `By_Interest_Area/`: a second index grouped by technical subject.
- A repository may intentionally appear in both indexes. The cards are metadata summaries and links; upstream source code remains at its original location.

Each card should include a repository title, short description, canonical GitHub URL, matched discovery keywords, and upstream topics.

## Validate the local catalog

Requirements: Python 3.11 or newer. No third-party packages or network access are required.

```bash
python scripts/catalog_audit.py --root .
python -m unittest discover -s tests -p 'test_*.py' -v
```

The validator checks local Markdown structure, GitHub URL syntax, title/URL consistency, missing metadata, duplicate references, and taxonomy aliases. Its November 3, 2026 baseline validated 625 cards with zero structural errors or metadata warnings. It found 285 expected cross-index references and no same-index duplicates. It does not contact GitHub or confirm upstream status.

See [Catalog Schema and Validation](docs/CATALOG_SCHEMA.md) for the record format, taxonomy normalization, and limitations. Agents and other tools can generate an offline JSON index with `python scripts/catalog_export.py --output reports/catalog-index.json`; see the [Agent Integration Guide](docs/AGENT_INTEGRATION.md) and [JSON Schema](schemas/catalog-index.schema.json).

To refresh read-only upstream GitHub metadata such as archived status, last push date, and license identifier, use [Upstream Status Refresh](docs/UPSTREAM_STATUS.md). This optional tool uses the GitHub REST API, requires no third-party packages, and is bounded to 50 repositories by default without a token.

## Research methodology and limits

The catalog's historical discovery process used repository metadata and keyword matching. The original PyGithub discovery scripts are not present in this repository, so automated upstream discovery and categorization are not currently reproducible from this checkout.

Keyword matches are discovery hints, not proof that a repository belongs in a category. For example, a generic match such as `ML` can produce false positives. Categories should be reviewed by a human and normalized over time.

The catalog may contain archived, deprecated, inactive, or unlicensed upstream projects. Before using a listed project:

1. Open the upstream repository and verify its owner and current status.
2. Check archived/deprecated notices and recent maintenance activity.
3. Read the upstream license and security policy.
4. Review source code and dependencies independently.
5. Confirm that the project is appropriate for the intended environment.

The historical [local metadata scan report](Audit_Reports/Security_Audit_Summary.md) describes only the catalog files scanned at that time. It does not report the security posture of linked repositories.

## Security and reporting

See [SECURITY.md](SECURITY.md) for vulnerability reporting. Do not submit credentials, personal data, or sensitive exploit details in public issues.

## License and terms

The repository includes a license file and separate terms. Review both before redistribution or commercial use. The terms contain proprietary-language statements that should be reconciled with the repository license by the maintainer; this README does not claim that the legal position is settled.
