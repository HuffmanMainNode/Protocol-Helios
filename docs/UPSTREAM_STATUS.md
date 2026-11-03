# Upstream Repository Status Refresh

Run a bounded GitHub metadata refresh from the catalog root:

```bash
python scripts/upstream_status.py --limit 25 --output reports/upstream-status.json
```

Set `GITHUB_TOKEN` in the environment to use authenticated GitHub API rate limits. Without a token, the default maximum is 50 repositories per run. The tool uses only Python's standard library and makes read-only GitHub REST API requests.

## Report fields

For each repository, the report records the API status, archived/disabled flags, default branch, last push timestamp, license SPDX identifier, visibility, and canonical upstream URL when returned.

## Interpretation

- `archived=true` means GitHub marks the repository as archived.
- `not_found_or_private` is intentionally ambiguous. A 404 does not reveal whether the repository was deleted, renamed, or made private.
- `pushed_at` is activity metadata, not proof of active maintenance or security.
- `license_spdx_id=null` means the API did not identify a license. It is not permission to reuse the code.
- A successful API response does not establish that the repository is officially operated by the named agency.

The tool does not clone repositories, inspect source code, run dependencies, check vulnerabilities, or make changes to the catalog. Review the JSON report before updating any cards.
