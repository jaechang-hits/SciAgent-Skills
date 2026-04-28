---
name: alphafold-database-access
description: >
  Access AlphaFold DB's 200M+ predicted structures by UniProt ID. Download PDB/mmCIF,
  analyze pLDDT/PAE, bulk-fetch proteomes via Google Cloud. For experimental structures
  use PDB; for prediction use ColabFold or ESMFold.
license: CC-BY-4.0
---

# AlphaFold Database Access

## Overview

AlphaFold DB is a public repository of AI-predicted 3D protein structures for over 200 million proteins, maintained by DeepMind and EMBL-EBI. Access predictions via BioPython or REST API, download coordinate files in multiple formats, analyze confidence metrics, and retrieve bulk proteome datasets via Google Cloud.

## When to Use

- Retrieving AI-predicted protein structures by UniProt accession
- Downloading PDB/mmCIF coordinate files for structural analysis or docking
- Analyzing prediction confidence (pLDDT per-residue, PAE domain-level)
- Bulk-downloading entire proteome predictions via Google Cloud
- Comparing predicted structures with experimental PDB structures
- Building structural models for proteins lacking experimental data
- Identifying high-confidence binding sites for drug discovery
- For experimental structures only → use PDB directly
- For running AlphaFold predictions → use ColabFold or local AlphaFold

## Prerequisites

```bash
# Core (BioPython for structure access)
pip install biopython requests numpy matplotlib

# Optional: Google Cloud for bulk access
pip install google-cloud-bigquery google-cloud-storage
```

## Quick Start

```python
from Bio.PDB import alphafold_db, MMCIFParser
import requests, numpy as np

# 1. Get prediction for a protein
uniprot_id = "P00520"  # ABL1 kinase
predictions = list(alphafold_db.get_predictions(uniprot_id))
af_id = predictions[0]['entryId']  # AF-P00520-F1

# 2. Download structure
cif_file = alphafold_db.download_cif_for(predictions[0], directory="./structures")

# 3. Check confidence
conf = requests.get(f"https://alphafold.ebi.ac.uk/files/{af_id}-confidence_v4.json").json()
scores = conf['confidenceScore']
print(f"Mean pLDDT: {np.mean(scores):.1f}, High-conf residues: {sum(1 for s in scores if s > 90)}/{len(scores)}")
```

## Core API

### 1. Prediction Retrieval

**BioPython (recommended for single proteins):**

```python
from Bio.PDB import alphafold_db

# Get prediction metadata
predictions = list(alphafold_db.get_predictions("P00520"))
pred = predictions[0]
print(f"AlphaFold ID: {pred['entryId']}")
print(f"Gene: {pred['gene']}, Species: {pred['organismScientificName']}")

# Get Structure objects directly
structures = list(alphafold_db.get_structural_models_for("P00520"))
```

**REST API (for metadata or integration):**

```python
import requests

uniprot_id = "P00520"
url = f"https://alphafold.ebi.ac.uk/api/prediction/{uniprot_id}"
response = requests.get(url)
data = response.json()

# Response includes download URLs for all file types
pred = data[0]
print(f"CIF: {pred['cifUrl']}")
print(f"PDB: {pred['pdbUrl']}")
print(f"PAE: {pred['paeDocUrl']}")
```

**3D-Beacons federated API (query multiple structure providers):**

```python
url = f"https://www.ebi.ac.uk/pdbe/pdbe-kb/3dbeacons/api/uniprot/summary/{uniprot_id}.json"
data = requests.get(url).json()
af_structures = [s for s in data['structures'] if s['provider'] == 'AlphaFold DB']
```

### 2. Structure File Download

```python
import requests

af_id = "AF-P00520-F1"
version = "v4"
base = "https://alphafold.ebi.ac.uk/files"

# mmCIF (recommended — full metadata, supports large structures)
cif = requests.get(f"{base}/{af_id}-model_{version}.cif")
with open(f"{af_id}.cif", "w") as f:
    f.write(cif.text)

# PDB format (legacy — limited to 99,999 atoms)
pdb = requests.get(f"{base}/{af_id}-model_{version}.pdb")
with open(f"{af_id}.pdb", "wb") as f:
    f.write(pdb.content)

# Confidence JSON (per-residue pLDDT scores)
conf = requests.get(f"{base}/{af_id}-confidence_{version}.json").json()

# PAE matrix JSON (inter-residue confidence)
pae = requests.get(f"{base}/{af_id}-predicted_aligned_error_{version}.json").json()
```

### 3. Confidence Metrics Analysis

**pLDDT (per-residue confidence, 0–100):**

```python
import numpy as np

conf_url = f"https://alphafold.ebi.ac.uk/files/{af_id}-confidence_v4.json"
conf = requests.get(conf_url).json()
scores = conf['confidenceScore']

# Classify residues by confidence
very_high = sum(1 for s in scores if s > 90)
high = sum(1 for s in scores if 70 < s <= 90)
low = sum(1 for s in scores if 50 < s <= 70)
very_low = sum(1 for s in scores if s <= 50)
print(f"Very high (>90): {very_high}, High (70-90): {high}, Low (50-70): {low}, Very low (<50): {very_low}")
```

**PAE (Predicted Aligned Error) visualization:**

```python
import matplotlib.pyplot as plt

pae_url = f"https://alphafold.ebi.ac.uk/files/{af_id}-predicted_aligned_error_v4.json"
pae = requests.get(pae_url).json()
pae_matrix = np.array(pae['distance'])

plt.figure(figsize=(10, 8))
plt.imshow(pae_matrix, cmap='viridis_r', vmin=0, vmax=30)
plt.colorbar(label='PAE (Å)')
plt.title(f'Predicted Aligned Error: {af_id}')
plt.xlabel('Residue')
plt.ylabel('Residue')
plt.savefig(f'{af_id}_pae.png', dpi=300, bbox_inches='tight')
# Low PAE (<5 Å) = confident relative positioning; >15 Å = uncertain domain arrangement
```

### 4. Bulk Data Access (Google Cloud)

```bash
# List available data
gsutil ls gs://public-datasets-deepmind-alphafold-v4/

# Download entire proteome by taxonomy ID
gsutil -m cp gs://public-datasets-deepmind-alphafold-v4/proteomes/proteome-tax_id-9606-*_v4.tar .

# Download accession index
gsutil cp gs://public-datasets-deepmind-alphafold-v4/accession_ids.csv .
```

**BigQuery metadata queries:**

```python
from google.cloud import bigquery

client = bigquery.Client()
query = """
SELECT entryId, uniprotAccession, gene, organismScientificName,
       globalMetricValue, fractionPlddtVeryHigh
FROM `bigquery-public-data.deepmind_alphafold.metadata`
WHERE organismScientificName = 'Homo sapiens'
  AND fractionPlddtVeryHigh > 0.8
  AND isReviewed = TRUE
LIMIT 100
"""
df = client.query(query).to_dataframe()
print(f"Found {len(df)} high-confidence human proteins")
```

### 5. Structure Parsing & Analysis

```python
from Bio.PDB import MMCIFParser
import numpy as np
from scipy.spatial.distance import pdist, squareform

parser = MMCIFParser(QUIET=True)
structure = parser.get_structure("protein", f"{af_id}-model_v4.cif")

# Extract alpha-carbon coordinates
coords, plddt_scores = [], []
for model in structure:
    for chain in model:
        for residue in chain:
            if 'CA' in residue:
                coords.append(residue['CA'].get_coord())
                plddt_scores.append(residue['CA'].get_bfactor())  # pLDDT stored as B-factor

coords = np.array(coords)
print(f"Residues: {len(coords)}, Mean pLDDT: {np.mean(plddt_scores):.1f}")

# Contact map (Cα-Cα < 8 Å)
dist_matrix = squareform(pdist(coords))
contacts = np.where((dist_matrix > 0) & (dist_matrix < 8))
print(f"Contacts: {len(contacts[0]) // 2}")
```

## Key Concepts

### Confidence Interpretation

| Metric | Range | Interpretation | Suitable For |
|--------|-------|---------------|--------------|
| pLDDT >90 | Very high | Backbone + side-chain reliable | Detailed analysis, docking |
| pLDDT 70–90 | High | Backbone generally reliable | Fold analysis, domain ID |
| pLDDT 50–70 | Low | Use with caution | May be flexible/disordered |
| pLDDT <50 | Very low | Likely disordered | Exclude from analysis |
| PAE <5 Å | Confident | Reliable relative domain positions | Multi-domain assembly |
| PAE 5–10 Å | Moderate | Uncertain arrangement | Treat domains independently |
| PAE >15 Å | Uncertain | Domains may be mobile | Do not trust orientation |

### AlphaFold ID Format

Format: `AF-{UniProt_accession}-F{fragment_number}` (e.g., `AF-P00520-F1`). Large proteins may be split into fragments (F1, F2, ...). Current database version: **v4** — include version suffix in all file URLs.

### File Types

| File | URL Suffix | Format | Use |
|------|-----------|--------|-----|
| Model coordinates | `-model_v4.cif` | mmCIF | Structural analysis (recommended) |
| Model coordinates | `-model_v4.pdb` | PDB | Legacy tools (<99,999 atoms) |
| Model coordinates | `-model_v4.bcif` | Binary CIF | Compressed (~70% smaller) |
| Confidence | `-confidence_v4.json` | JSON | Per-residue pLDDT array |
| Aligned error | `-predicted_aligned_error_v4.json` | JSON | N×N PAE matrix |
| PAE image | `-predicted_aligned_error_v4.png` | PNG | Quick visual assessment |

## Common Workflows

### Workflow 1: Single Protein Structure Analysis

```python
from Bio.PDB import alphafold_db, MMCIFParser
import requests, numpy as np

uniprot_id = "P04637"  # p53 tumor suppressor

# Retrieve and download
predictions = list(alphafold_db.get_predictions(uniprot_id))
cif_file = alphafold_db.download_cif_for(predictions[0], directory="./structures")
af_id = predictions[0]['entryId']

# Parse structure
parser = MMCIFParser(QUIET=True)
structure = parser.get_structure("p53", cif_file)

# Extract pLDDT from B-factors
plddt = [r['CA'].get_bfactor() for m in structure for c in m for r in c if 'CA' in r]
print(f"Length: {len(plddt)}, Mean pLDDT: {np.mean(plddt):.1f}")

# Identify high-confidence regions for docking
high_conf_regions = [(i+1, s) for i, s in enumerate(plddt) if s > 90]
print(f"High-confidence residues: {len(high_conf_regions)}/{len(plddt)}")
```

### Workflow 2: Batch Protein Processing

```python
from Bio.PDB import alphafold_db
import requests, numpy as np, pandas as pd, time

uniprot_ids = ["P00520", "P12931", "P04637", "P38398"]
results = []

for uid in uniprot_ids:
    try:
        preds = list(alphafold_db.get_predictions(uid))
        if not preds:
            continue
        af_id = preds[0]['entryId']
        conf = requests.get(f"https://alphafold.ebi.ac.uk/files/{af_id}-confidence_v4.json").json()
        scores = conf['confidenceScore']
        results.append({
            'uniprot': uid, 'alphafold_id': af_id,
            'length': len(scores), 'mean_plddt': np.mean(scores),
            'frac_high_conf': sum(1 for s in scores if s > 90) / len(scores)
        })
        time.sleep(0.2)  # Rate limit: 100-200ms between requests
    except Exception as e:
        print(f"Error {uid}: {e}")

df = pd.DataFrame(results)
print(df.to_string(index=False))
```

## Key Parameters

| Parameter | Module | Default | Range | Effect |
|-----------|--------|---------|-------|--------|
| `uniprot_id` | All | — | UniProt accession | Primary query identifier |
| `version` | Download | `v4` | v1–v4 | Database version (always use latest) |
| `directory` | BioPython | `"."` | Path | Download destination |
| `QUIET` | MMCIFParser | `False` | bool | Suppress parser warnings |
| `vmin/vmax` | PAE plot | 0/30 | Å | PAE colormap range |
| `taxonomy_id` | GCS bulk | — | NCBI tax ID | Species for proteome download |
| `fractionPlddtVeryHigh` | BigQuery | — | 0.0–1.0 | Filter by high-confidence fraction |
| Concurrent requests | API | — | ≤10 | Max parallel API requests |
| Request delay | API | — | 100–200ms | Delay between sequential requests |

## Best Practices

1. **Use BioPython for single proteins, Google Cloud for bulk** — individual API downloads are slow for >100 proteins; GCS parallel download is orders of magnitude faster
2. **Always check pLDDT before downstream analysis** — low-confidence regions (pLDDT <50) are likely disordered and should be excluded from docking, contact analysis, or binding site prediction
3. **Anti-pattern — trusting all regions equally**: AlphaFold predictions lack ligands, PTMs, cofactors, and multi-chain context. High pLDDT does not guarantee functional accuracy
4. **Cache downloaded files locally** — avoid re-downloading the same structures; AlphaFold files are static per version
5. **Use PAE for multi-domain proteins** — pLDDT tells you per-residue confidence, but PAE reveals whether domain orientations are reliable. Low inter-domain PAE (<5 Å) = trust the arrangement; high PAE (>15 Å) = treat domains independently
6. **Pin database version in reproducible analyses** — include `_v4` in URLs and document which version was used

## Common Recipes

### Recipe 1: Proteome Download by Species

```python
import subprocess

def download_proteome(taxonomy_id: int, output_dir: str = "./proteomes"):
    """Download all AlphaFold predictions for a species via GCS."""
    if not isinstance(taxonomy_id, int):
        raise ValueError("taxonomy_id must be an integer")
    pattern = f"gs://public-datasets-deepmind-alphafold-v4/proteomes/proteome-tax_id-{taxonomy_id}-*_v4.tar"
    subprocess.run(["gsutil", "-m", "cp", pattern, f"{output_dir}/"], check=True)

# Human (9606), E. coli (83333), Mouse (10090)
download_proteome(9606)
```

### Recipe 2: High-Confidence Region Extraction

```python
def extract_high_conf_residues(plddt_scores, threshold=90):
    """Extract contiguous high-confidence regions."""
    regions, start = [], None
    for i, score in enumerate(plddt_scores):
        if score > threshold and start is None:
            start = i
        elif score <= threshold and start is not None:
            regions.append((start + 1, i, i - start))  # 1-indexed
            start = None
    if start is not None:
        regions.append((start + 1, len(plddt_scores), len(plddt_scores) - start))
    return regions

# Usage: regions = extract_high_conf_residues(plddt_scores)
# Returns: [(start_res, end_res, length), ...]
```

### Recipe 3: PAE-Based Domain Segmentation

```python
import numpy as np

def segment_domains(pae_matrix, threshold=10.0):
    """Simple domain segmentation from PAE matrix."""
    n = pae_matrix.shape[0]
    # Average PAE for each residue pair -> symmetric
    sym_pae = (pae_matrix + pae_matrix.T) / 2
    # Cluster: residues with low mutual PAE are in the same domain
    domains, current_domain = [0] * n, 0
    for i in range(1, n):
        if sym_pae[i-1, i] > threshold:
            current_domain += 1
        domains[i] = current_domain
    return domains
```

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|---------|
| `404 Not Found` from API | No AlphaFold prediction for this UniProt ID | Check if protein is in AlphaFold DB; some organisms not covered |
| `429 Too Many Requests` | Exceeded rate limit | Add `time.sleep(0.2)` between requests; use GCS for bulk |
| Empty predictions list | UniProt ID not in database | Verify ID at alphafold.ebi.ac.uk; try canonical isoform |
| Large protein split into fragments | Protein >2700 residues | Check all fragments (F1, F2, ...); stitch manually if needed |
| pLDDT values all low (<50) | Intrinsically disordered protein | Expected behavior; structure prediction unreliable for IDPs |
| PAE matrix asymmetric | PAE[i][j] ≠ PAE[j][i] by design | PAE measures error when aligned on residue i; symmetrize for clustering |
| `ModuleNotFoundError: Bio.PDB.alphafold_db` | BioPython version too old | Upgrade: `pip install --upgrade biopython>=1.80` |
| GCS download fails | gsutil not configured | Run `gcloud auth login` or use anonymous access for public data |
| BigQuery quota exceeded | Free tier limit (1 TB/month) | Optimize queries with `LIMIT`; use GCS for bulk file access instead |

## Bundled Resources

### references/api_schemas_reference.md

Detailed API data schemas and lookup tables: REST API response fields, mmCIF data categories, confidence JSON schema, PAE JSON schema, BigQuery metadata table fields, HTTP error codes, rate limiting guidelines, and version history (v1–v4). Consult for field-level details when parsing API responses or building custom queries. Scripts functionality (none in original). Original api_reference.md content partially relocated to Core API (endpoints, common code patterns) and Key Concepts (confidence thresholds, file types table); schemas, field catalogs, and error codes retained in this reference.

## Related Skills

- **autodock-vina** — molecular docking using AlphaFold structures as receptor
- **biopython** — general protein structure parsing and analysis beyond AlphaFold

## References

- AlphaFold DB: https://alphafold.ebi.ac.uk/
- API Documentation: https://alphafold.ebi.ac.uk/api-docs
- Jumper et al. (2021) Nature 596, 583–589: https://doi.org/10.1038/s41586-021-03819-2
- Varadi et al. (2024) Nucleic Acids Res. 52, D368–D375: https://doi.org/10.1093/nar/gkad1011
- BioPython AlphaFold module: https://biopython.org/docs/dev/api/Bio.PDB.alphafold_db.html
- Google Cloud AlphaFold: https://console.cloud.google.com/marketplace/product/bigquery-public-data/deepmind-alphafold
