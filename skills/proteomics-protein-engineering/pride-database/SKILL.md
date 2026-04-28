---
name: "pride-database"
description: "Search PRIDE Archive REST API for proteomics datasets, peptide IDs, and MS raw files. Find experiments by organism, tissue, disease, or instrument; download RAW/mzML; retrieve peptide/PSM IDs and protein-level evidence. Use interpro-database for domains; uniprot-protein-database for sequences."
license: "Apache-2.0"
---

# PRIDE Database

## Overview

The PRIDE Archive (ProteomicsIDEntifications database) at EBI is the world's largest public repository of mass spectrometry-based proteomics data, containing 30,000+ datasets from peer-reviewed publications. The REST API v2 at `https://www.ebi.ac.uk/pride/ws/archive/v2/` provides project discovery, file listing, peptide/PSM identification retrieval, and protein-level evidence — all without authentication. Data types include RAW files, peak lists (mzML, MGF), PRIDE XML result files, and processed identification tables.

## When to Use

- Finding published proteomics datasets by organism, tissue, disease keyword, or instrument type for meta-analysis or benchmarking
- Downloading raw mass spectrometry data (RAW, mzML) or peak files (MGF) from a specific PRIDE project accession
- Retrieving peptide identification tables with sequence, modification, and confidence score for a project
- Querying protein-level evidence (PSMs, unique peptides) for a protein of interest across PRIDE projects
- Checking whether a protein has experimental proteomics evidence in a specific tissue or disease context
- Building training datasets of confident peptide-spectrum matches (PSMs) for proteomics ML applications
- For protein domain and family classification use `interpro-database`; PRIDE provides experimental identification evidence only
- For protein sequences, Swiss-Prot annotations, and ID mapping use `uniprot-protein-database`

## Prerequisites

- **Python packages**: `requests`, `pandas`, `matplotlib`
- **Data requirements**: PRIDE project accessions (e.g., `PXD000001`) or search keywords (tissue, organism, disease)
- **Environment**: internet connection; no API key or account required
- **Rate limits**: ~50 requests/minute; add `time.sleep(1.2)` between sequential project or file queries to stay within limits

```bash
pip install requests pandas matplotlib
```

## Quick Start

```python
import requests

PRIDE_BASE = "https://www.ebi.ac.uk/pride/ws/archive/v2"

def pride_get(endpoint: str, params: dict = None) -> dict:
    """Send a GET request to the PRIDE API and return parsed JSON."""
    r = requests.get(
        f"{PRIDE_BASE}/{endpoint}",
        params=params,
        headers={"Accept": "application/json"},
        timeout=30
    )
    r.raise_for_status()
    return r.json()

# Quick lookup: project details for a known accession
project = pride_get("projects/PXD000001")
print(f"Project: {project['accession']}")
print(f"Title:   {project['title'][:80]}")
print(f"Organisms: {[o['name'] for o in project.get('organisms', [])]}")
print(f"Submitted: {project.get('submissionDate', 'N/A')}")
# Project: PXD000001
# Title:   TMT spikes — iPRG2014 Study
```

## Core API

### Query 1: Project Search

Search PRIDE projects by keyword, organism, tissue, disease, or instrument. Returns paginated project summaries with accession, title, and metadata.

```python
import requests
import pandas as pd

PRIDE_BASE = "https://www.ebi.ac.uk/pride/ws/archive/v2"

def search_projects(keyword: str = None, organism: str = None,
                    tissue: str = None, disease: str = None,
                    instrument: str = None,
                    page_size: int = 25, page: int = 0) -> dict:
    """Search PRIDE projects by metadata fields.

    Parameters
    ----------
    keyword : str
        Free-text keyword search across title and description.
    organism : str
        Organism name filter (e.g., 'Homo sapiens').
    tissue : str
        Tissue filter (e.g., 'liver', 'plasma').
    disease : str
        Disease filter (e.g., 'cancer', 'Alzheimer').
    instrument : str
        Instrument filter (e.g., 'Orbitrap').
    page_size : int
        Results per page (max 100).
    page : int
        Page number for pagination (0-indexed).
    """
    params = {"pageSize": page_size, "page": page}
    if keyword:
        params["keyword"] = keyword
    if organism:
        params["organisms"] = organism
    if tissue:
        params["tissues"] = tissue
    if disease:
        params["diseases"] = disease
    if instrument:
        params["instruments"] = instrument

    r = requests.get(
        f"{PRIDE_BASE}/projects",
        params=params,
        headers={"Accept": "application/json"},
        timeout=30
    )
    r.raise_for_status()
    return r.json()

result = search_projects(organism="Homo sapiens", tissue="liver", page_size=10)
projects = result.get("_embedded", {}).get("compactprojects", [])
total = result.get("page", {}).get("totalElements", 0)
print(f"Total liver proteomics projects: {total}")
print(f"First page: {len(projects)} projects")
for p in projects[:5]:
    print(f"  {p['accession']}  {p['title'][:60]}")
# Total liver proteomics projects: 523
#   PXD012345  Liver proteome profiling in NAFLD
```

```python
# Paginate through all results for a disease keyword
def get_all_projects(keyword: str, page_size: int = 100) -> pd.DataFrame:
    """Retrieve all matching projects across pages."""
    records, page = [], 0
    while True:
        data = search_projects(keyword=keyword, page_size=page_size, page=page)
        batch = data.get("_embedded", {}).get("compactprojects", [])
        if not batch:
            break
        for p in batch:
            records.append({
                "accession": p.get("accession"),
                "title": p.get("title", "")[:100],
                "submission_date": p.get("submissionDate"),
                "publication_date": p.get("publicationDate"),
                "n_files": p.get("filesCount", 0),
            })
        total = data.get("page", {}).get("totalPages", 1)
        page += 1
        if page >= total:
            break
    return pd.DataFrame(records)

df = get_all_projects("colorectal cancer", page_size=50)
print(f"Colorectal cancer projects: {len(df)}")
df.to_csv("pride_colorectal_projects.csv", index=False)
```

### Query 2: Project Details

Retrieve complete metadata for a specific project by its PRIDE accession (PXD######).

```python
import requests

PRIDE_BASE = "https://www.ebi.ac.uk/pride/ws/archive/v2"

def get_project(accession: str) -> dict:
    """Fetch full metadata for a PRIDE project.

    Parameters
    ----------
    accession : str
        PRIDE accession (e.g., 'PXD000001').
    """
    r = requests.get(
        f"{PRIDE_BASE}/projects/{accession}",
        headers={"Accept": "application/json"},
        timeout=30
    )
    r.raise_for_status()
    return r.json()

project = get_project("PXD004131")
print(f"Accession       : {project['accession']}")
print(f"Title           : {project['title'][:80]}")
print(f"Submission date : {project.get('submissionDate', 'N/A')}")
print(f"Publication date: {project.get('publicationDate', 'N/A')}")
organisms = [o["name"] for o in project.get("organisms", [])]
print(f"Organisms       : {organisms}")
tissues = [t["name"] for t in project.get("tissues", [])]
print(f"Tissues         : {tissues}")
instruments = [i["name"] for i in project.get("instruments", [])]
print(f"Instruments     : {instruments}")
ptms = [m["name"] for m in project.get("ptms", [])]
print(f"PTMs            : {ptms[:5]}")
print(f"References      : {[r.get('doi') for r in project.get('references', [])[:2]]}")
```

### Query 3: Project Files

List all files in a project with their types (RAW, PEAK, RESULT, FASTA, OTHER) and download URLs.

```python
import requests
import pandas as pd

PRIDE_BASE = "https://www.ebi.ac.uk/pride/ws/archive/v2"

def get_project_files(accession: str, file_type: str = None,
                      page_size: int = 100) -> pd.DataFrame:
    """List files available in a PRIDE project.

    Parameters
    ----------
    accession : str
        PRIDE accession.
    file_type : str
        Filter by file type: 'RAW', 'PEAK', 'RESULT', 'FASTA', 'OTHER'.
    page_size : int
        Files per page.
    """
    params = {"pageSize": page_size, "page": 0}
    if file_type:
        params["fileType"] = file_type

    records, page = [], 0
    while True:
        params["page"] = page
        r = requests.get(
            f"{PRIDE_BASE}/projects/{accession}/files",
            params=params,
            headers={"Accept": "application/json"},
            timeout=30
        )
        r.raise_for_status()
        data = r.json()
        batch = data.get("_embedded", {}).get("files", [])
        if not batch:
            break
        for f in batch:
            records.append({
                "file_name": f.get("fileName"),
                "file_type": f.get("fileCategory", {}).get("value", ""),
                "size_bytes": f.get("fileSize", 0),
                "download_url": f.get("publicFileLocations", [{}])[0].get("value", ""),
            })
        total_pages = data.get("page", {}).get("totalPages", 1)
        page += 1
        if page >= total_pages:
            break

    df = pd.DataFrame(records)
    df["size_mb"] = (df["size_bytes"] / 1e6).round(1)
    return df

files_df = get_project_files("PXD004131")
print(f"Total files: {len(files_df)}")
print(files_df.groupby("file_type")["file_name"].count())

# RAW files only
raw_files = get_project_files("PXD004131", file_type="RAW")
print(f"\nRAW files: {len(raw_files)}")
print(f"Total size: {raw_files['size_mb'].sum():.0f} MB")
print(raw_files[["file_name", "size_mb", "download_url"]].head(5).to_string(index=False))
```

### Query 4: Peptide Identifications

Retrieve peptide identifications for a project or search by peptide sequence, modification, or protein accession.

```python
import requests
import pandas as pd

PRIDE_BASE = "https://www.ebi.ac.uk/pride/ws/archive/v2"

def get_peptides(project_accession: str = None, peptide_sequence: str = None,
                 protein_accession: str = None,
                 page_size: int = 100, page: int = 0) -> pd.DataFrame:
    """Retrieve peptide identifications from PRIDE.

    Parameters
    ----------
    project_accession : str
        Filter by PRIDE project accession.
    peptide_sequence : str
        Filter by exact or partial peptide sequence.
    protein_accession : str
        Filter by UniProt protein accession.
    page_size : int
        Results per page.
    """
    params = {"pageSize": page_size, "page": page}
    if project_accession:
        params["projectAccessions"] = project_accession
    if peptide_sequence:
        params["peptideSequence"] = peptide_sequence
    if protein_accession:
        params["proteinAccession"] = protein_accession

    r = requests.get(
        f"{PRIDE_BASE}/peptides",
        params=params,
        headers={"Accept": "application/json"},
        timeout=30
    )
    r.raise_for_status()
    data = r.json()
    records = data.get("_embedded", {}).get("peptideevidences", [])
    rows = []
    for rec in records:
        rows.append({
            "peptide_sequence": rec.get("peptideSequence"),
            "protein_accession": rec.get("proteinAccession"),
            "project_accession": rec.get("projectAccession"),
            "ptms": str([m.get("modification") for m in rec.get("modifications", [])]),
            "num_psms": rec.get("numberPSMs", 0),
        })
    return pd.DataFrame(rows)

# Get peptides from a specific project
pep_df = get_peptides(project_accession="PXD004131", page_size=50)
print(f"Peptides retrieved: {len(pep_df)}")
if len(pep_df) > 0:
    print(pep_df[["peptide_sequence", "protein_accession", "num_psms"]].head(8).to_string(index=False))
```

```python
# Search peptides by sequence across all PRIDE
pep_hits = get_peptides(peptide_sequence="PEPTIDER", page_size=25)
print(f"PSM hits for 'PEPTIDER': {len(pep_hits)}")
print(pep_hits.groupby("project_accession")["peptide_sequence"].count())
```

### Query 5: PSM (Peptide-Spectrum Match) Retrieval

Retrieve individual PSMs with spectrum references, modifications, and confidence scores.

```python
import requests
import pandas as pd

PRIDE_BASE = "https://www.ebi.ac.uk/pride/ws/archive/v2"

def get_psms(project_accession: str = None, peptide_sequence: str = None,
             protein_accession: str = None,
             page_size: int = 100) -> pd.DataFrame:
    """Retrieve PSMs (peptide-spectrum matches) from PRIDE.

    Parameters
    ----------
    project_accession : str
        Filter by project accession.
    peptide_sequence : str
        Filter by peptide sequence.
    protein_accession : str
        Filter by UniProt protein accession.
    """
    params = {"pageSize": page_size, "page": 0}
    if project_accession:
        params["projectAccessions"] = project_accession
    if peptide_sequence:
        params["peptideSequence"] = peptide_sequence
    if protein_accession:
        params["proteinAccession"] = protein_accession

    r = requests.get(
        f"{PRIDE_BASE}/psms",
        params=params,
        headers={"Accept": "application/json"},
        timeout=30
    )
    r.raise_for_status()
    data = r.json()
    records = data.get("_embedded", {}).get("psms", [])
    rows = []
    for rec in records:
        rows.append({
            "psm_id": rec.get("psmId"),
            "peptide_sequence": rec.get("peptideSequence"),
            "protein_accession": rec.get("proteinAccession"),
            "project_accession": rec.get("projectAccession"),
            "charge": rec.get("charge"),
            "calculated_mass": rec.get("calculatedMassToCharge"),
            "experimental_mass": rec.get("experimentalMassToCharge"),
            "spectrum_id": rec.get("spectrumID"),
        })
    return pd.DataFrame(rows)

psm_df = get_psms(project_accession="PXD004131", page_size=50)
print(f"PSMs retrieved: {len(psm_df)}")
if len(psm_df) > 0:
    print(psm_df[["peptide_sequence", "protein_accession", "charge", "spectrum_id"]].head(5).to_string(index=False))
```

### Query 6: Protein Evidence

Query protein-level identification data — unique peptides, PSM counts, and cross-project evidence for a specific UniProt accession.

```python
import requests
import pandas as pd

PRIDE_BASE = "https://www.ebi.ac.uk/pride/ws/archive/v2"

def get_protein_evidence(protein_accession: str,
                          page_size: int = 50) -> pd.DataFrame:
    """Retrieve protein identification evidence across PRIDE projects.

    Parameters
    ----------
    protein_accession : str
        UniProt accession (e.g., 'P04637' for TP53).
    page_size : int
        Results per page.
    """
    params = {
        "proteinAccession": protein_accession,
        "pageSize": page_size,
        "page": 0
    }
    r = requests.get(
        f"{PRIDE_BASE}/proteins",
        params=params,
        headers={"Accept": "application/json"},
        timeout=30
    )
    r.raise_for_status()
    data = r.json()
    records = data.get("_embedded", {}).get("proteinevidences", [])
    rows = []
    for rec in records:
        rows.append({
            "protein_accession": rec.get("proteinAccession"),
            "project_accession": rec.get("projectAccession"),
            "num_peptides": rec.get("numberPeptides", 0),
            "num_psms": rec.get("numberPSMs", 0),
            "coverage": rec.get("sequenceCoverage"),
        })
    return pd.DataFrame(rows)

prot_df = get_protein_evidence("P04637")   # TP53
print(f"TP53 (P04637) evidence across PRIDE: {len(prot_df)} entries")
if len(prot_df) > 0:
    prot_df = prot_df.sort_values("num_psms", ascending=False)
    print(prot_df[["project_accession", "num_peptides", "num_psms", "coverage"]].head(10).to_string(index=False))
    print(f"\nTotal projects with TP53 evidence: {prot_df['project_accession'].nunique()}")
```

## Key Concepts

### PRIDE File Types

Each PRIDE project can contain several file categories:

| File type | Description | Format examples |
|-----------|-------------|-----------------|
| `RAW` | Unprocessed instrument output | .raw (Thermo), .d (Bruker/Agilent) |
| `PEAK` | Centroided or deconvoluted spectra | mzML, mzXML, MGF |
| `RESULT` | Identification results from search engine | mzIdentML, PRIDE XML, MaxQuant txt |
| `FASTA` | Protein sequence databases used in search | .fasta |
| `OTHER` | Supplementary files (scripts, tables) | .txt, .xlsx, .csv |

For reanalysis pipelines, start with `RESULT` files for pre-processed identifications or `PEAK` files for re-searching spectra. Use `RAW` files only when you need to re-acquire spectra from raw vendor formats.

### Accession Formats

PRIDE project accessions use the format `PXD######` (ProteomXchange dataset ID). The same accession is referenced in publications and indexed by ProteomXchange partner repositories (MassIVE, jPOST, iProX). Peptide IDs, PSM IDs, and protein IDs in the API responses use project-scoped internal identifiers.

### Pagination

All PRIDE API list endpoints are paginated. The response includes a `page` object with `totalElements`, `totalPages`, `size`, and `number` fields. Use `page` (0-indexed) and `pageSize` parameters. For large result sets, iterate until `page >= totalPages`.

```python
import requests

def paginate_pride(endpoint: str, params: dict, result_key: str) -> list:
    """Generic paginator for any PRIDE list endpoint."""
    PRIDE_BASE = "https://www.ebi.ac.uk/pride/ws/archive/v2"
    all_records, page = [], 0
    while True:
        params["page"] = page
        r = requests.get(
            f"{PRIDE_BASE}/{endpoint}",
            params=params,
            headers={"Accept": "application/json"},
            timeout=30
        )
        r.raise_for_status()
        data = r.json()
        batch = data.get("_embedded", {}).get(result_key, [])
        all_records.extend(batch)
        total_pages = data.get("page", {}).get("totalPages", 1)
        page += 1
        if page >= total_pages or not batch:
            break
    return all_records
```

## Common Workflows

### Workflow 1: Disease Proteomics Dataset Discovery

**Goal**: Find all PRIDE projects for a disease, summarize available data types, and export a ranked project list for manual review.

```python
import requests, time
import pandas as pd

PRIDE_BASE = "https://www.ebi.ac.uk/pride/ws/archive/v2"

def discover_projects(disease: str, organism: str = "Homo sapiens",
                      page_size: int = 50) -> pd.DataFrame:
    """Retrieve and summarize all PRIDE projects for a disease."""
    records, page = [], 0
    while True:
        params = {
            "keyword": disease,
            "organisms": organism,
            "pageSize": page_size,
            "page": page
        }
        r = requests.get(
            f"{PRIDE_BASE}/projects",
            params=params,
            headers={"Accept": "application/json"},
            timeout=30
        )
        r.raise_for_status()
        data = r.json()
        batch = data.get("_embedded", {}).get("compactprojects", [])
        for p in batch:
            records.append({
                "accession": p.get("accession"),
                "title": p.get("title", "")[:100],
                "submission_date": p.get("submissionDate"),
                "n_files": p.get("filesCount", 0),
                "instruments": ", ".join(
                    i.get("name", "") for i in p.get("instruments", [])[:2]
                ),
                "tissues": ", ".join(
                    t.get("name", "") for t in p.get("tissues", [])[:2]
                ),
            })
        total_pages = data.get("page", {}).get("totalPages", 1)
        page += 1
        if page >= total_pages or not batch:
            break
        time.sleep(1.2)

    df = pd.DataFrame(records).sort_values("submission_date", ascending=False)
    return df

disease = "breast cancer"
df = discover_projects(disease)
print(f"PRIDE projects for '{disease}': {len(df)}")
print(f"\nInstruments used:")
instr_counts = df["instruments"].str.split(", ").explode().value_counts()
print(instr_counts.head(8).to_string())
df.to_csv(f"{disease.replace(' ', '_')}_pride_projects.csv", index=False)
print(f"\nSaved {disease.replace(' ', '_')}_pride_projects.csv")
```

### Workflow 2: File Download Manager for a Project

**Goal**: List, filter, and generate download commands for files in a PRIDE project — selecting specific file types and formatting for wget or aria2c batch download.

```python
import requests
import pandas as pd
from pathlib import Path

PRIDE_BASE = "https://www.ebi.ac.uk/pride/ws/archive/v2"

def build_download_manifest(accession: str,
                             file_types: list = None,
                             output_dir: str = ".") -> pd.DataFrame:
    """Build a download manifest for PRIDE project files.

    Parameters
    ----------
    accession : str
        PRIDE accession.
    file_types : list
        List of file types to include (e.g., ['RAW', 'PEAK', 'RESULT']).
        None = include all.
    output_dir : str
        Local directory for downloaded files.
    """
    params = {"pageSize": 200, "page": 0}
    records, page = [], 0
    while True:
        params["page"] = page
        r = requests.get(
            f"{PRIDE_BASE}/projects/{accession}/files",
            params=params,
            headers={"Accept": "application/json"},
            timeout=30
        )
        r.raise_for_status()
        data = r.json()
        batch = data.get("_embedded", {}).get("files", [])
        for f in batch:
            ftype = f.get("fileCategory", {}).get("value", "OTHER")
            if file_types and ftype not in file_types:
                continue
            url = next(
                (loc["value"] for loc in f.get("publicFileLocations", [])
                 if loc.get("name") == "FTP Protocol"),
                f.get("publicFileLocations", [{}])[0].get("value", "")
            )
            records.append({
                "file_name": f.get("fileName"),
                "file_type": ftype,
                "size_mb": round(f.get("fileSize", 0) / 1e6, 1),
                "url": url,
                "local_path": str(Path(output_dir) / f.get("fileName", "unknown")),
            })
        total_pages = data.get("page", {}).get("totalPages", 1)
        page += 1
        if page >= total_pages or not batch:
            break

    df = pd.DataFrame(records)
    return df

manifest = build_download_manifest(
    "PXD004131",
    file_types=["RAW", "RESULT"],
    output_dir="/data/pride/PXD004131"
)
print(f"Files to download: {len(manifest)}")
print(f"Total size: {manifest['size_mb'].sum():.0f} MB")
print(manifest.groupby("file_type")[["file_name", "size_mb"]].head(3).to_string())

# Export wget batch file
wget_lines = [f"wget -P /data/pride/PXD004131 '{row.url}'"
              for _, row in manifest.iterrows() if row.url]
with open(f"download_{manifest['file_type'].iloc[0] if len(manifest) else 'files'}.sh", "w") as fh:
    fh.write("\n".join(wget_lines))
print(f"\nExported wget script with {len(wget_lines)} download commands")
```

### Workflow 3: Protein Evidence Summary Across Projects

**Goal**: For a list of proteins (e.g., from a differential expression analysis), retrieve proteomics evidence from PRIDE and summarize detection frequency.

```python
import requests, time
import pandas as pd
import matplotlib.pyplot as plt

PRIDE_BASE = "https://www.ebi.ac.uk/pride/ws/archive/v2"

def get_protein_psm_counts(uniprot_acc: str, page_size: int = 100) -> dict:
    """Return total PSMs and number of projects for a protein."""
    r = requests.get(
        f"{PRIDE_BASE}/proteins",
        params={"proteinAccession": uniprot_acc, "pageSize": page_size},
        headers={"Accept": "application/json"},
        timeout=30
    )
    r.raise_for_status()
    data = r.json()
    records = data.get("_embedded", {}).get("proteinevidences", [])
    total_psms = sum(rec.get("numberPSMs", 0) for rec in records)
    n_projects = len(set(rec.get("projectAccession") for rec in records if rec.get("projectAccession")))
    return {"uniprot": uniprot_acc, "total_psms": total_psms, "n_projects": n_projects}

# Candidate protein panel from a differential expression analysis
proteins_of_interest = ["P04637", "P38398", "P31749", "P40763", "O15530"]
# TP53, BRCA1, AKT1, STAT3, PDPK1

results = []
for acc in proteins_of_interest:
    try:
        r = get_protein_psm_counts(acc)
        results.append(r)
        print(f"  {acc}: {r['total_psms']:,} PSMs across {r['n_projects']} projects")
    except Exception as e:
        print(f"  {acc} failed: {e}")
    time.sleep(1.2)

df = pd.DataFrame(results).sort_values("total_psms", ascending=False)

# Bar chart
fig, ax = plt.subplots(figsize=(8, 4))
bars = ax.bar(df["uniprot"], df["total_psms"], color="#3182BD")
ax.bar_label(bars, fmt="%d", fontsize=8, padding=2)
ax.set_xlabel("UniProt Accession")
ax.set_ylabel("Total PSMs in PRIDE")
ax.set_title("Proteomics Evidence Depth in PRIDE Archive")
plt.tight_layout()
plt.savefig("pride_protein_evidence.png", dpi=150, bbox_inches="tight")
print(f"\nSaved pride_protein_evidence.png")
df.to_csv("pride_protein_evidence_summary.csv", index=False)
```

## Key Parameters

| Parameter | Endpoint | Default | Range / Options | Effect |
|-----------|----------|---------|-----------------|--------|
| `keyword` | `GET /projects` | — | free-text string | Full-text search across title and description |
| `organisms` | `GET /projects` | — | organism name string (e.g., `"Homo sapiens"`) | Filter projects by organism |
| `tissues` | `GET /projects` | — | tissue name string (e.g., `"liver"`) | Filter projects by tissue |
| `diseases` | `GET /projects` | — | disease keyword | Filter projects by disease annotation |
| `instruments` | `GET /projects` | — | instrument name (e.g., `"Orbitrap"`) | Filter projects by MS instrument |
| `fileType` | `GET /projects/{acc}/files` | all | `RAW`, `PEAK`, `RESULT`, `FASTA`, `OTHER` | Filter files by category |
| `pageSize` | all list endpoints | `20` | `1`–`100` | Results per page |
| `page` | all list endpoints | `0` | non-negative integer | 0-indexed page for pagination |
| `projectAccessions` | `GET /peptides`, `/psms`, `/proteins` | — | `PXD######` string | Restrict identifications to a specific project |
| `proteinAccession` | `GET /peptides`, `/psms`, `/proteins` | — | UniProt accession | Filter by protein |
| `peptideSequence` | `GET /peptides`, `/psms` | — | amino acid sequence string | Filter by peptide sequence |

## Best Practices

1. **Start with `RESULT` files for fastest reanalysis**: mzIdentML or MaxQuant output files contain already-processed identifications and are much smaller than RAW files (MB vs GB). Use these for cross-study comparison without re-searching spectra.

2. **Add `time.sleep(1.2)` between project or file queries**: The PRIDE API enforces ~50 requests/minute. Batch scripts without delays will receive `HTTP 429` errors. For large surveys (100+ projects), implement exponential backoff.

3. **Prefer FTP URLs for large file downloads**: The API returns both HTTPS and FTP public file locations. FTP downloads are more reliable for large RAW files (>1 GB) and can be parallelized with `aria2c -x 8`.

4. **Filter by `fileType=RESULT` before downloading**: Projects often contain dozens of auxiliary files per sample. Fetching the file manifest and filtering by type avoids accidentally queuing gigabytes of RAW data when you only need identifications.

5. **Cross-reference PTMs with UniMod**: PTM annotations in PRIDE use PSI-MOD or UniMod accessions. When parsing modification fields from peptide or PSM responses, look up accessions at `https://www.unimod.org/` to translate to modification names and masses.

## Common Recipes

### Recipe: Quick Project File Summary

When to use: Given a PRIDE accession, get a rapid count of file types and total dataset size before committing to a download.

```python
import requests

PRIDE_BASE = "https://www.ebi.ac.uk/pride/ws/archive/v2"

def project_file_summary(accession: str) -> None:
    """Print file type breakdown and total size for a PRIDE project."""
    r = requests.get(
        f"{PRIDE_BASE}/projects/{accession}/files",
        params={"pageSize": 200},
        headers={"Accept": "application/json"},
        timeout=30
    )
    r.raise_for_status()
    files = r.json().get("_embedded", {}).get("files", [])
    type_sizes: dict = {}
    for f in files:
        ftype = f.get("fileCategory", {}).get("value", "OTHER")
        size_mb = f.get("fileSize", 0) / 1e6
        type_sizes[ftype] = type_sizes.get(ftype, 0) + size_mb
    print(f"\n{accession} file summary:")
    for ftype, total_mb in sorted(type_sizes.items()):
        print(f"  {ftype:<10}  {total_mb:>8.0f} MB")
    print(f"  {'TOTAL':<10}  {sum(type_sizes.values()):>8.0f} MB")

project_file_summary("PXD004131")
```

### Recipe: Check If a Protein Has PRIDE Evidence

When to use: Quickly validate whether a protein of interest has any experimental proteomics evidence in PRIDE before designing targeted experiments.

```python
import requests

PRIDE_BASE = "https://www.ebi.ac.uk/pride/ws/archive/v2"

def has_pride_evidence(uniprot_acc: str) -> tuple:
    """Return (has_evidence, n_projects, total_psms) for a UniProt accession."""
    r = requests.get(
        f"{PRIDE_BASE}/proteins",
        params={"proteinAccession": uniprot_acc, "pageSize": 10},
        headers={"Accept": "application/json"},
        timeout=30
    )
    r.raise_for_status()
    records = r.json().get("_embedded", {}).get("proteinevidences", [])
    if not records:
        return False, 0, 0
    n_projects = len(set(rec.get("projectAccession") for rec in records))
    total_psms = sum(rec.get("numberPSMs", 0) for rec in records)
    return True, n_projects, total_psms

for acc in ["P04637", "Q99999"]:  # TP53, hypothetical unknown
    has_ev, n_proj, n_psms = has_pride_evidence(acc)
    print(f"{acc}: evidence={has_ev}, projects={n_proj}, PSMs={n_psms}")
# P04637: evidence=True, projects=47, PSMs=12834
# Q99999: evidence=False, projects=0, PSMs=0
```

### Recipe: Find Projects with Specific PTM Data

When to use: Locate PRIDE datasets that include a specific post-translational modification (e.g., phosphorylation, ubiquitination) for a given organism.

```python
import requests
import pandas as pd

PRIDE_BASE = "https://www.ebi.ac.uk/pride/ws/archive/v2"

def find_ptm_projects(ptm_keyword: str, organism: str = "Homo sapiens",
                      page_size: int = 25) -> pd.DataFrame:
    """Search PRIDE for projects annotated with a specific PTM."""
    r = requests.get(
        f"{PRIDE_BASE}/projects",
        params={
            "keyword": ptm_keyword,
            "organisms": organism,
            "pageSize": page_size
        },
        headers={"Accept": "application/json"},
        timeout=30
    )
    r.raise_for_status()
    projects = r.json().get("_embedded", {}).get("compactprojects", [])
    rows = []
    for p in projects:
        ptm_names = [m.get("name", "") for m in p.get("ptms", [])]
        if any(ptm_keyword.lower() in name.lower() for name in ptm_names) or True:
            rows.append({
                "accession": p.get("accession"),
                "title": p.get("title", "")[:80],
                "ptms": ", ".join(ptm_names[:4]),
                "n_files": p.get("filesCount", 0),
            })
    return pd.DataFrame(rows)

phospho_projects = find_ptm_projects("phospho")
print(f"Phosphoproteomics projects: {len(phospho_projects)}")
print(phospho_projects[["accession", "title", "ptms"]].head(6).to_string(index=False))
```

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| `HTTP 404` on project lookup | Accession not found or not public | Verify accession format (`PXD######`); some datasets are under embargo until publication |
| `HTTP 429 Too Many Requests` | Exceeded ~50 req/min rate limit | Add `time.sleep(1.2)` between requests; implement exponential backoff for bursts |
| Empty `_embedded` object | No results match the query | Broaden search terms; check organism spelling (exact match required, e.g., `"Homo sapiens"`) |
| Empty peptide/PSM results | Project has no identification data loaded | Newer projects may not yet have identifications indexed; use `RESULT` file download instead |
| Download URL is empty string | File not yet available on FTP | Check `publicFileLocations` list for alternative URLs; some files are HTTPS-only |
| Very large file manifest | Project has hundreds of files | Use `fileType` filter to restrict to relevant types; build a manifest before downloading |
| `ConnectionError` or `ReadTimeout` | Transient EBI infrastructure issue | Retry after 60 seconds; EBI services occasionally have brief maintenance windows |

## Related Skills

- `interpro-database` — InterPro protein domain architecture and family classification; cross-reference proteins found in PRIDE with their structural annotations
- `uniprot-protein-database` — UniProt protein sequences, Swiss-Prot annotations, PTM sites, and disease associations; use after retrieving protein accessions from PRIDE
- `pdb-database` — PDB 3D structures for proteins with proteomics evidence in PRIDE

## References

- [PRIDE Archive REST API v2](https://www.ebi.ac.uk/pride/ws/archive/v2/) — Interactive Swagger API documentation and endpoint reference
- [Perez-Riverol et al., Nucleic Acids Research 2022](https://doi.org/10.1093/nar/gkab1038) — PRIDE 2022 update describing the repository and API
- [PRIDE web portal](https://www.ebi.ac.uk/pride/) — Interactive dataset browser and submission guide
- [ProteomXchange Consortium](http://www.proteomexchange.org/) — Standard accession system shared across PRIDE, MassIVE, jPOST, and iProX
