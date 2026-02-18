# STRING API — Advanced Features & Integration

Advanced API features, integration examples, output format details, and operational reference for the STRING protein-protein interaction database.

## Values/Ranks Enrichment API

For differential expression or proteomics data with quantitative values per protein:

### Step 1: Obtain API Key

```python
import requests, json

response = requests.get("https://string-db.org/api/json/get_api_key")
api_key = json.loads(response.text)
print(f"API key: {api_key}")
```

### Step 2: Submit Quantitative Data

Submit tab-separated protein ID + value pairs (complete protein set, no pre-filtering):

```python
# Format: one protein per line, tab-separated ID and value
data_lines = "TP53\t2.5\nBRCA1\t-1.8\nMDM2\t3.1\nATM\t0.2"

response = requests.post(
    "https://string-db.org/api/json/valuesranks_submit",
    data={
        "identifiers": data_lines,
        "species": 9606,
        "api_key": api_key,
        "caller_identity": "python_script"
    }
)
job_id = json.loads(response.text)["job_id"]
```

### Step 3: Check Status and Retrieve Results

```python
import time

while True:
    status = requests.get(
        "https://string-db.org/api/json/valuesranks_enrichment_status",
        params={"job_id": job_id}
    )
    result = json.loads(status.text)
    if result.get("status") == "completed":
        break
    time.sleep(10)

# Retrieve enrichment results
enrichment = requests.get(
    "https://string-db.org/api/tsv/valuesranks_enrichment",
    params={"job_id": job_id}
)
print(enrichment.text[:500])
```

**Requirements**: Complete protein set (no filtering), numeric values for each protein, proper species identifier.

## Bulk Network Upload

For proteome-scale analysis (too large for API):

1. Navigate to https://string-db.org/
2. Select "Upload proteome" option
3. Upload FASTA file — STRING generates complete interaction network and predicts functions
4. Alternatively, download pre-computed networks from https://string-db.org/cgi/download

**When to use bulk downloads vs API**: For >500 proteins or complete interactome analysis, bulk downloads are faster and more reliable than batched API calls.

## Version-Specific URLs

For reproducible research, use version-pinned base URLs:

```python
# Version-specific (recommended for publications)
STRING_API = "https://version-12-0.string-db.org/api"

# Current version (always latest)
STRING_API = "https://string-db.org/api"
```

Always report the STRING version in methods sections. Check with:
```python
version = string_query("version", {})
# "Protein interactions queried from STRING v{version} (accessed YYYY-MM-DD)"
```

## POST vs GET for Large Queries

For protein lists exceeding ~20 identifiers, use POST to avoid URL length limits:

```python
import requests

# POST method for large protein lists
response = requests.post(
    "https://string-db.org/api/tsv/network",
    data={
        "identifiers": "\n".join(large_protein_list),  # newline-separated
        "species": 9606,
        "required_score": 400,
        "caller_identity": "python_script"
    }
)
```

## R Integration — STRINGdb Package

```R
# Install from Bioconductor
if (!requireNamespace("BiocManager", quietly = TRUE))
    install.packages("BiocManager")
BiocManager::install("STRINGdb")

# Usage
library(STRINGdb)
string_db <- STRINGdb$new(version = "12", species = 9606, score_threshold = 400)

# Map identifiers
genes <- data.frame(gene = c("TP53", "BRCA1", "MDM2"))
mapped <- string_db$map(genes, "gene", removeUnmappedRows = TRUE)

# Get interactions
interactions <- string_db$get_interactions(mapped$STRING_id)

# Plot network
string_db$plot_network(mapped$STRING_id)

# Enrichment
enrichment <- string_db$get_enrichment(mapped$STRING_id)
```

## Cytoscape Integration

Import STRING networks into Cytoscape for advanced visualization:

**Method 1: stringApp plugin** (recommended)
1. Install stringApp from Cytoscape App Manager
2. Apps → STRING → Protein query → Enter gene names
3. Adjust confidence threshold and species

**Method 2: Import TSV data**
1. Query network via API (TSV format)
2. File → Import → Network from File → Select TSV
3. Map columns: Source = `preferredName_A`, Target = `preferredName_B`, Edge Attribute = `score`
4. Apply layouts (e.g., force-directed) and styling

## Output Formats — Complete Reference

| Format | URL Segment | Content Type | Use Case |
|--------|-------------|-------------|----------|
| TSV | `/tsv/` | Tab-separated text | Data processing (default) |
| JSON | `/json/` | Structured JSON | Programmatic access |
| XML | `/xml/` | XML document | Standards-compliant exchange |
| PSI-MI | `/psi-mi/` | XML (PSI standard) | Proteomics standard format |
| PSI-MITAB | `/psi-mi-tab/` | Tab-delimited PSI | Flat-file proteomics exchange |
| PNG | `/image/` | Binary image | Network visualization |
| SVG | (add `?format=svg`) | Vector graphics | Publication figures |

**High-resolution images**: Append `?highres=1` to image requests for publication-quality PNG output.

**SVG output**: Scalable vector graphics for lossless resizing — preferred for journal submissions and presentations.

## HTTP Error Codes

| Status | Meaning | Common Cause | Resolution |
|--------|---------|-------------|------------|
| 200 | Success | — | — |
| 400 | Bad Request | Malformed identifiers, missing required params | Check `%0d` separators, verify species param |
| 404 | Not Found | Protein/species not in STRING | Verify identifiers with `get_string_ids` first |
| 500 | Server Error | Server overload or internal issue | Retry after 30s; use version-specific URL |

**Timeout handling**: If requests consistently timeout, reduce protein count per query (max ~200 for network, ~500 for enrichment) or switch to bulk downloads.

## Data License

STRING data is available under **Creative Commons Attribution 4.0 (CC-BY-4.0)**:
- Free for academic and commercial use
- Attribution required — cite: Szklarczyk et al. (latest STRING publication)
- Modifications and redistribution allowed with attribution

**Citation format**: "Protein-protein interactions were obtained from the STRING database v{version} (Szklarczyk et al., {year}; https://string-db.org)."

## Caller Identity

Always include `caller_identity` parameter in API calls:

```python
params["caller_identity"] = "your_app_name"
```

This helps STRING track API usage patterns and is requested in their documentation. Use a descriptive name for your application or script.

---

*Condensed from original `references/string_reference.md` (456 lines → ~175 lines). Retained: values/ranks enrichment API, bulk upload, R/Cytoscape integration, output formats, HTTP errors, data license, version-specific URLs, POST method. Omitted: species table (→ Key Concepts in SKILL.md), confidence scores (→ Key Concepts), identifier format (→ Key Concepts), individual endpoint parameter tables (→ Core API in SKILL.md), basic Python urllib examples (→ replaced by requests-based helper in SKILL.md Quick Start).*
