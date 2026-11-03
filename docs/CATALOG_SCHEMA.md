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

## Machine-readable export

Generate an offline JSON index from the Markdown cards:

```bash
python scripts/catalog_export.py --output reports/catalog-index.json
```

The export preserves one entry per source card, including its index, category, keywords, topics, and source path. The same repository may therefore appear more than once. See [Agent Integration](AGENT_INTEGRATION.md) and the [JSON Schema](../schemas/catalog-index.schema.json). The export labels classifications as discovery hints requiring human review and upstream status as not checked.

## Limits

A syntactically valid link does not prove that an upstream repository exists, is maintained, is safe, is government-operated, or is licensed for reuse. Upstream status, archived/deprecated status, commit freshness, license, security posture, and source authenticity require separate checks. The historical security scan only covered local Markdown/metadata at the time it ran; it did not scan linked upstream repositories.


## Baseline validation: 2026-11-03

The local validator processed **625 catalog cards** with zero structural errors and zero metadata warnings. It found **285 cross-index repository references**, which are expected because the same project may appear in the agency and interest-area indexes. It found no duplicate references confined to a single index.

The normalized interest-area counts include 164 machine-learning cards across the `ml`, `ML`, and `machine_learning` directory aliases, 25 neural-network cards, 9 large-language-model cards, and 2 digital-forensics/incident-response cards across `dfir` and `DFIR`.

These counts describe local catalog organization only. They do not measure upstream repository quality or freshness.
