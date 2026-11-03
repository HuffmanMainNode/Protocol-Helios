# Catalog Record Schema and Validation

## Current Markdown card shape

Each indexed repository is represented by a Markdown card with:

- A title in `owner/repository` form.
- A concise description.
- One canonical HTTPS GitHub repository URL.
- Matched discovery keywords.
- Upstream topics, or an explicit `None`.

The same upstream repository may appear once under `By_Agency` and once under `By_Interest_Area`. Those cross-index references are intentional. Multiple references within the same index should be reviewed for duplication.

## Local validator

Run:

```bash
python scripts/catalog_audit.py --root .
```

The validator checks local card structure, canonical GitHub URL syntax, title/URL consistency, missing metadata, duplicate references, and interest-area taxonomy aliases. It performs no network requests.

## Taxonomy normalization

Current aliases include `ml`, `ML`, and `machine_learning` mapping to `machine-learning`; `llm` and `LLM` mapping to `large-language-models`; and `dfir`/ `DFIR` mapping to `digital-forensics-incident-response`.

Normalization is reported, not destructively applied to directory names. Existing paths remain stable until a separate migration is reviewed.

## Limits

A syntactically valid link does not prove that an upstream repository exists, is maintained, is safe, is government-operated, or is licensed for reuse. Upstream status, archived/deprecated status, commit freshness, license, security posture, and source authenticity require separate checks. The historical security scan only covered local Markdown/metadata at the time it ran; it did not scan linked upstream repositories.
