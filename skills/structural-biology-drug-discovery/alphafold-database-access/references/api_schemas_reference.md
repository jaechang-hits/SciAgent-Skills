# AlphaFold Database API Schemas & Reference

Detailed data schemas, field catalogs, error codes, and lookup tables for AlphaFold DB programmatic access.

## REST API Response Schema

### Prediction Endpoint Response Fields

`GET https://alphafold.ebi.ac.uk/api/prediction/{uniprot_id}` returns a JSON array:

| Field | Type | Description |
|-------|------|-------------|
| `entryId` | string | AlphaFold ID (format: `AF-{uniprot}-F{fragment}`) |
| `gene` | string | Gene symbol (e.g., "ABL1") |
| `uniprotAccession` | string | UniProt accession (e.g., "P00520") |
| `uniprotId` | string | UniProt entry name (e.g., "ABL1_HUMAN") |
| `uniprotDescription` | string | Protein description |
| `taxId` | integer | NCBI taxonomy ID (e.g., 9606 for human) |
| `organismScientificName` | string | Species scientific name |
| `uniprotStart` | integer | First residue covered (1-indexed) |
| `uniprotEnd` | integer | Last residue covered |
| `uniprotSequence` | string | Full protein sequence |
| `modelCreatedDate` | string | Initial prediction date (ISO format) |
| `latestVersion` | integer | Current model version (4 as of 2024) |
| `allVersions` | int[] | All available version numbers |
| `cifUrl` | string | mmCIF structure download URL |
| `bcifUrl` | string | Binary CIF download URL |
| `pdbUrl` | string | PDB format download URL |
| `paeImageUrl` | string | PAE heatmap PNG URL |
| `paeDocUrl` | string | PAE data JSON URL |

### 3D-Beacons Federated API

`GET https://www.ebi.ac.uk/pdbe/pdbe-kb/3dbeacons/api/uniprot/summary/{uniprot_id}.json`

Filter AlphaFold results: `s['provider'] == 'AlphaFold DB'` in the `structures` array.

## mmCIF Coordinate File Schema

AlphaFold mmCIF files use standard PDBx/mmCIF categories:

| Category | Key Fields | Description |
|----------|-----------|-------------|
| `_entry` | `id` | Entry-level metadata |
| `_struct` | `title`, `pdbx_descriptor` | Structure title and description |
| `_entity` | `id`, `type`, `pdbx_description` | Molecular entity information |
| `_atom_site` | See below | Atomic coordinates and properties |
| `_pdbx_struct_assembly` | `id`, `details` | Biological assembly info |

### `_atom_site` Fields (Coordinates)

| Field | Description | Example |
|-------|-------------|---------|
| `group_PDB` | Always "ATOM" for AlphaFold | `ATOM` |
| `id` | Atom serial number | `1` |
| `label_atom_id` | Atom name | `CA`, `N`, `C`, `O` |
| `label_comp_id` | Residue name (3-letter) | `ALA`, `GLY` |
| `label_seq_id` | Residue sequence number (1-indexed) | `42` |
| `Cartn_x` / `Cartn_y` / `Cartn_z` | Cartesian coordinates (Angstroms) | `12.345` |
| `B_iso_or_equiv` | **Contains pLDDT score** (not thermal B-factor) | `91.2` |

**Critical note**: AlphaFold stores per-residue pLDDT confidence in the B-factor column. Standard structure viewers auto-color by this field, effectively showing confidence. Values range 0-100 (not the typical B-factor range of 5-80).

## Confidence JSON Schema

`{af_id}-confidence_v4.json`:

```json
{
  "confidenceScore": [87.5, 91.2, 93.8],
  "confidenceCategory": ["high", "very_high", "very_high"]
}
```

| Field | Type | Description |
|-------|------|-------------|
| `confidenceScore` | float[] | pLDDT per residue (0-100), one per residue |
| `confidenceCategory` | string[] | Categorical: `very_high` (>90), `high` (70-90), `low` (50-70), `very_low` (<=50) |

## PAE JSON Schema

`{af_id}-predicted_aligned_error_v4.json`:

```json
{
  "distance": [[0.0, 2.3, 4.5], [2.3, 0.0, 3.1], [4.5, 3.1, 0.0]],
  "max_predicted_aligned_error": 31.75
}
```

| Field | Type | Description |
|-------|------|-------------|
| `distance` | float[][] | N x N matrix of PAE values (Angstroms) |
| `max_predicted_aligned_error` | float | Maximum PAE value in matrix |

**Interpretation**: `distance[i][j]` = expected position error of residue j when aligned on residue i. The matrix is **not symmetric** (`distance[i][j] != distance[j][i]`). Diagonal is always 0. Lower values = more confident relative positioning.

## BigQuery Metadata Schema

**Dataset**: `bigquery-public-data.deepmind_alphafold`
**Table**: `metadata`

| Field | Type | Description | Use |
|-------|------|-------------|-----|
| `entryId` | STRING | AlphaFold entry ID | Join key |
| `uniprotAccession` | STRING | UniProt accession | Primary filter |
| `gene` | STRING | Gene symbol | Gene-level queries |
| `organismScientificName` | STRING | Species name | Species filter |
| `taxId` | INTEGER | NCBI taxonomy ID | Proteome-level queries |
| `globalMetricValue` | FLOAT | Overall quality metric | Quality ranking |
| `fractionPlddtVeryHigh` | FLOAT | Fraction pLDDT >= 90 | High-confidence filter |
| `fractionPlddtVeryLow` | FLOAT | Fraction pLDDT <= 50 | Disorder filter |
| `isReviewed` | BOOLEAN | Swiss-Prot reviewed | Curated subset |
| `sequenceLength` | INTEGER | Protein length | Size filter |

### Example Queries

```sql
-- High-confidence human proteins
SELECT entryId, gene, fractionPlddtVeryHigh
FROM `bigquery-public-data.deepmind_alphafold.metadata`
WHERE taxId = 9606 AND fractionPlddtVeryHigh > 0.8 AND isReviewed = TRUE
ORDER BY fractionPlddtVeryHigh DESC LIMIT 100;

-- Highly disordered proteins (potential IDPs)
SELECT entryId, gene, fractionPlddtVeryLow
FROM `bigquery-public-data.deepmind_alphafold.metadata`
WHERE taxId = 9606 AND fractionPlddtVeryLow > 0.5
LIMIT 50;
```

## Google Cloud Storage Structure

**Bucket**: `gs://public-datasets-deepmind-alphafold-v4`

| Path | Size | Description |
|------|------|-------------|
| `accession_ids.csv` | ~13.5 GB | Index of all entries |
| `sequences.fasta` | ~16.5 GB | All protein sequences |
| `proteomes/proteome-tax_id-{taxId}-*_v4.tar` | Varies | Per-species archives |

Common taxonomy IDs: Human (9606), Mouse (10090), E. coli (83333), Yeast (559292), Drosophila (7227), Zebrafish (7955), Arabidopsis (3702).

## HTTP Error Codes

| Code | Meaning | Action |
|------|---------|--------|
| 200 | Success | Process response |
| 404 | Not Found | No prediction for this UniProt ID; verify at alphafold.ebi.ac.uk |
| 429 | Too Many Requests | Implement backoff; add `time.sleep(0.2)` between requests |
| 500 | Server Error | Retry with exponential backoff (1s, 2s, 4s) |
| 503 | Service Unavailable | Temporary outage; retry after 30-60 seconds |

## Rate Limiting Guidelines

- Maximum **10 concurrent requests** to REST API
- Add **100-200ms delay** between sequential requests
- Use **Google Cloud Storage** for bulk downloads (>100 proteins)
- Cache all downloaded files locally (files are static per version)
- BigQuery free tier: 1 TB/month queries; use `LIMIT` and targeted `WHERE` clauses

## Version History

| Version | Year | Key Changes |
|---------|------|-------------|
| v1 | 2021 | Initial release, ~350K structures (21 model organisms) |
| v2 | 2022 | Expanded to 200M+ structures (48 organisms + UniRef90 clusters) |
| v3 | 2023 | Updated models, expanded coverage |
| v4 | 2024 | Current version; improved confidence metrics, broader proteome coverage |

Always include `_v4` suffix in file URLs for reproducibility.

## Citation

1. Jumper, J. et al. Highly accurate protein structure prediction with AlphaFold. *Nature* 596, 583-589 (2021).
2. Varadi, M. et al. AlphaFold Protein Structure Database in 2024. *Nucleic Acids Res.* 52, D368-D375 (2024).

Condensed from original: api_reference.md (423 lines). Retained: all REST API response fields, mmCIF schema with atom_site fields, confidence JSON schema, PAE JSON schema with asymmetry note, BigQuery metadata table with example queries, GCS bucket structure with taxonomy IDs, HTTP error codes, rate limiting guidelines, version history, citation. Original endpoint code patterns (curl examples, Python requests, batch download bash) relocated to SKILL.md Core API sections 1-4. 3D-Beacons integration code relocated to SKILL.md Core API section 1. Omitted: verbose file type prose descriptions (condensed to SKILL.md Key Concepts "File Types" table), detailed best practices section (consolidated into SKILL.md Best Practices), additional resources links (in SKILL.md References).
