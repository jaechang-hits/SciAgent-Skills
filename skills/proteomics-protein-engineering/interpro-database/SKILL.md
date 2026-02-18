---
name: "interpro-database"
description: "Query the InterPro REST API for protein domain architecture, family classification, and member database integration. Search InterPro entries by name or accession, retrieve all domains in a protein (domain architecture), list proteins in a family, get taxonomic distribution, and link to PDB structures. Integrates Pfam, PANTHER, PIRSF, PRINTS, PROSITE, SMART, CDD, and NCBIfam into a unified hierarchy. For protein sequence and Swiss-Prot annotations use uniprot-protein-database; for experimental 3D structures use pdb-database."
license: "CC-BY-4.0"
---

# InterPro Database

## Overview

InterPro is the EBI's integrated protein family, domain, and functional site database. It consolidates signatures from 13 member databases (Pfam, PANTHER, PIRSF, PRINTS, PROSITE, SMART, CDD, NCBIfam, and others) into unified InterPro entries, each describing a homologous superfamily, domain, family, repeat, or conserved site. The REST API at `https://www.ebi.ac.uk/interpro/api/` is free and requires no authentication.

## When to Use

- Identifying all domains and families present in a protein by UniProt accession (domain architecture)
- Searching for proteins that contain a specific domain or belong to a specific family
- Finding the taxonomic distribution of organisms that encode a given domain or family
- Cross-linking a domain to experimental 3D structures in the PDB
- Checking which source databases (Pfam, PANTHER, SMART, etc.) cover an InterPro entry
- Discovering InterPro entries by keyword (e.g., "kinase domain") when you do not yet know the accession
- For protein sequence retrieval, functional annotations (GO, pathways, active sites), and ID mapping use `uniprot-protein-database`
- For downloading domain-aligned sequences or building HMM profiles use `Pfam` directly; InterPro is the meta-layer

## Prerequisites

- **Python packages**: `requests`, `pandas`, `matplotlib`
- **Data requirements**: UniProt accessions (e.g., `P04637`) or InterPro accessions (e.g., `IPR011009`)
- **Environment**: internet connection; no API key required
- **Rate limits**: no published hard limit; use `time.sleep(1.0)` between requests for batch queries; paginate with `?cursor=` or `?page_size=`

```bash
pip install requests pandas matplotlib
```

## Quick Start

```python
import requests

INTERPRO_BASE = "https://www.ebi.ac.uk/interpro/api"

def interpro_get(path: str, params: dict = None) -> dict:
    """Send a GET request to the InterPro API and return parsed JSON."""
    r = requests.get(
        f"{INTERPRO_BASE}/{path}",
        params=params,
        headers={"Accept": "application/json"},
        timeout=30
    )
    r.raise_for_status()
    return r.json()

# Get domain architecture for TP53 (P04637)
data = interpro_get("protein/uniprot/P04637/")
entries = data.get("entries", [])
print(f"InterPro entries for TP53: {len(entries)}")
for e in entries[:4]:
    print(f"  {e['metadata']['accession']}  {e['metadata']['type']:<20}  {e['metadata']['name']}")
# InterPro entries for TP53: 12
#   IPR011615  domain               P53 DNA-binding domain
#   IPR012346  homologous_superfamily  p53-like transcription factor
```

## Core API

### Query 1: Entry Search

Search for InterPro entries by name keyword or fetch a specific entry by accession.

```python
import requests

INTERPRO_BASE = "https://www.ebi.ac.uk/interpro/api"

def search_entries(query: str, entry_type: str = None,
                   page_size: int = 20) -> list:
    """Search InterPro entries by keyword; optionally filter by type."""
    params = {"search": query, "page_size": page_size}
    if entry_type:
        params["type"] = entry_type   # family, domain, homologous_superfamily, repeat, site
    r = requests.get(
        f"{INTERPRO_BASE}/entry/interpro/",
        params=params,
        headers={"Accept": "application/json"},
        timeout=30
    )
    r.raise_for_status()
    return r.json().get("results", [])

hits = search_entries("serine kinase", entry_type="domain")
print(f"InterPro domain entries matching 'serine kinase': {len(hits)}")
for h in hits[:5]:
    m = h["metadata"]
    print(f"  {m['accession']}  {m['type']:<10}  {m['name']}")
# InterPro domain entries matching 'serine kinase': 8
#   IPR000719  domain    Protein kinase domain
#   IPR008271  domain    Serine/threonine/tyrosine kinase, active site
```

```python
# Fetch a specific InterPro entry by accession
r = requests.get(
    f"{INTERPRO_BASE}/entry/interpro/IPR000719/",
    headers={"Accept": "application/json"},
    timeout=30
)
r.raise_for_status()
meta = r.json()["metadata"]
print(f"Accession    : {meta['accession']}")
print(f"Name         : {meta['name']}")
print(f"Type         : {meta['type']}")
print(f"Member DBs   : {list(meta.get('member_databases', {}).keys())}")
go_terms = meta.get("go_terms", [])
print(f"GO terms     : {[g['identifier'] for g in go_terms[:3]]}")
# Accession    : IPR000719
# Name         : Protein kinase domain
# Type         : domain
# Member DBs   : ['pfam', 'smart', 'cdd', 'ncbifam', 'panther']
# GO terms     : ['GO:0004672', 'GO:0005524', 'GO:0006468']
```

### Query 2: Protein Domain Architecture

Retrieve all InterPro entries (domains, families, sites) matched in a protein by UniProt accession.

```python
import requests

INTERPRO_BASE = "https://www.ebi.ac.uk/interpro/api"

def get_protein_domain_architecture(uniprot_acc: str) -> dict:
    """Return protein metadata and all InterPro domain matches."""
    r = requests.get(
        f"{INTERPRO_BASE}/protein/uniprot/{uniprot_acc}/",
        headers={"Accept": "application/json"},
        timeout=30
    )
    r.raise_for_status()
    return r.json()

data = get_protein_domain_architecture("P04637")   # TP53
print(f"Protein length : {data['metadata']['length']}")
print(f"Source DB      : {data['metadata']['source_database']}")
print(f"InterPro entries: {len(data.get('entries', []))}")
for entry in data.get("entries", [])[:6]:
    m = entry["metadata"]
    locs = entry.get("entry_protein_locations", [])
    loc_str = ", ".join(
        f"{frag['start']}-{frag['end']}"
        for loc in locs for frag in loc.get("fragments", [])
    )
    print(f"  {m['accession']}  {m['type']:<25}  {m['name'][:35]:<35}  [{loc_str}]")
```

```python
# Compare domain architectures of two proteins side-by-side
import pandas as pd

def domain_set(uniprot_acc: str) -> set:
    data = get_protein_domain_architecture(uniprot_acc)
    return {e["metadata"]["accession"] for e in data.get("entries", [])}

brca1_domains = domain_set("P38398")   # BRCA1
tp53_domains   = domain_set("P04637")  # TP53

shared = brca1_domains & tp53_domains
unique_brca1 = brca1_domains - tp53_domains
unique_tp53  = tp53_domains - brca1_domains
print(f"Shared InterPro entries: {len(shared)}")
print(f"BRCA1-unique           : {len(unique_brca1)}")
print(f"TP53-unique            : {len(unique_tp53)}")
```

### Query 3: Entry Proteins

List proteins that contain a specific InterPro entry (family or domain).

```python
import requests, time

INTERPRO_BASE = "https://www.ebi.ac.uk/interpro/api"

def get_entry_proteins(interpro_acc: str, reviewed_only: bool = True,
                       page_size: int = 50) -> list:
    """Return proteins (UniProt) containing a given InterPro entry."""
    db = "reviewed" if reviewed_only else "uniprot"
    r = requests.get(
        f"{INTERPRO_BASE}/entry/interpro/{interpro_acc}/protein/{db}/",
        params={"page_size": page_size},
        headers={"Accept": "application/json"},
        timeout=60
    )
    r.raise_for_status()
    return r.json().get("results", [])

proteins = get_entry_proteins("IPR011009")   # Protein kinase-like domain SF
print(f"Reviewed proteins with IPR011009: {len(proteins)}")
for p in proteins[:4]:
    m = p["metadata"]
    print(f"  {m['accession']}  {m.get('name', {}).get('short', ''):<25}  "
          f"len={m.get('length', '?')}")
```

```python
# Paginate all proteins for a family using cursor
def get_all_entry_proteins(interpro_acc: str,
                            reviewed_only: bool = True) -> list:
    INTERPRO_BASE = "https://www.ebi.ac.uk/interpro/api"
    db = "reviewed" if reviewed_only else "uniprot"
    url = f"{INTERPRO_BASE}/entry/interpro/{interpro_acc}/protein/{db}/"
    all_proteins = []
    params = {"page_size": 200}
    while url:
        r = requests.get(url, params=params,
                         headers={"Accept": "application/json"}, timeout=60)
        r.raise_for_status()
        data = r.json()
        all_proteins.extend(data.get("results", []))
        url = data.get("next")
        params = None   # next URL already has params encoded
        if url:
            time.sleep(1.0)
    return all_proteins

proteins = get_all_entry_proteins("IPR000719")   # Protein kinase domain
print(f"Total reviewed proteins with protein kinase domain: {len(proteins)}")
```

### Query 4: Entry Taxonomy

Get the taxonomic distribution of proteins annotated with a given InterPro entry.

```python
import requests

INTERPRO_BASE = "https://www.ebi.ac.uk/interpro/api"

def get_entry_taxonomy(interpro_acc: str,
                        page_size: int = 50) -> list:
    """Return taxonomic summary for proteins in a given InterPro entry."""
    r = requests.get(
        f"{INTERPRO_BASE}/entry/interpro/{interpro_acc}/taxonomy/uniprot/",
        params={"page_size": page_size},
        headers={"Accept": "application/json"},
        timeout=60
    )
    r.raise_for_status()
    return r.json().get("results", [])

taxa = get_entry_taxonomy("IPR000719")   # Protein kinase domain
print(f"Top taxa for protein kinase domain (IPR000719):")
for t in taxa[:8]:
    m = t["metadata"]
    protein_count = t.get("proteins", 0)
    print(f"  taxId={m['accession']}  {m.get('name', ''):<30}  proteins={protein_count}")
```

### Query 5: Structure Integration

Retrieve PDB structures associated with an InterPro entry.

```python
import requests

INTERPRO_BASE = "https://www.ebi.ac.uk/interpro/api"

def get_entry_structures(interpro_acc: str, page_size: int = 25) -> list:
    """Return PDB structures that include a match to a given InterPro entry."""
    r = requests.get(
        f"{INTERPRO_BASE}/structure/pdb/",
        params={"entry_interpro": interpro_acc, "page_size": page_size},
        headers={"Accept": "application/json"},
        timeout=60
    )
    r.raise_for_status()
    return r.json().get("results", [])

structures = get_entry_structures("IPR011009")   # Protein kinase-like SF
print(f"PDB structures linked to IPR011009: {len(structures)}")
for s in structures[:5]:
    m = s["metadata"]
    print(f"  {m['accession']}  resolution={m.get('resolution', 'N/A')} Å  "
          f"experiment={m.get('experiment_type', 'N/A')}")
# PDB structures linked to IPR011009: 25
#   1ATP  resolution=2.2 Å  experiment=X-ray diffraction
#   2SRC  resolution=1.5 Å  experiment=X-ray diffraction
```

### Query 6: Domain Sequence Retrieval

Download the FASTA sequences of proteins in an InterPro family for alignment or phylogenetics.

```python
import requests, time

INTERPRO_BASE = "https://www.ebi.ac.uk/interpro/api"

def get_family_fasta(interpro_acc: str,
                      reviewed_only: bool = True,
                      max_sequences: int = 100) -> str:
    """Retrieve FASTA sequences for proteins in an InterPro entry."""
    db = "reviewed" if reviewed_only else "uniprot"
    proteins = []
    url = f"{INTERPRO_BASE}/entry/interpro/{interpro_acc}/protein/{db}/"
    params = {"page_size": min(max_sequences, 200)}
    while url and len(proteins) < max_sequences:
        r = requests.get(url, params=params,
                         headers={"Accept": "application/json"}, timeout=60)
        r.raise_for_status()
        data = r.json()
        proteins.extend(data.get("results", []))
        url = data.get("next") if len(proteins) < max_sequences else None
        params = None
        if url:
            time.sleep(1.0)

    # Fetch FASTA from UniProt for each accession
    accessions = [p["metadata"]["accession"] for p in proteins[:max_sequences]]
    fasta_url = "https://rest.uniprot.org/uniprotkb/stream"
    query = " OR ".join(f"accession:{acc}" for acc in accessions)
    r = requests.get(fasta_url,
                     params={"query": query, "format": "fasta"},
                     timeout=120)
    r.raise_for_status()
    return r.text

fasta = get_family_fasta("IPR000719", reviewed_only=True, max_sequences=20)
seq_count = fasta.count(">")
print(f"FASTA sequences retrieved: {seq_count}")
print(fasta[:300])   # preview first sequence header + start
```

## Key Concepts

### InterPro Entry Types

InterPro classifies entries into five types. The type determines what biological relationship the match implies:

| Type | Description | Example |
|------|-------------|---------|
| `family` | Homologous group of proteins sharing common ancestry and function | IPR000719 (Protein kinase) |
| `domain` | Discrete structural and functional unit that can occur in multiple protein contexts | IPR011009 (Protein kinase-like SF) |
| `homologous_superfamily` | Structurally similar domains that may have diverged in sequence | IPR011993 (Pleckstrin-like) |
| `repeat` | Short, repeated sequence unit that occurs multiple times within a protein | IPR001440 (TPR repeat) |
| `site` | Short conserved motif: active site, binding site, or post-translational modification site | IPR008271 (Ser/Thr kinase active site) |

### Member Database Hierarchy

Each InterPro entry integrates signatures from one or more member databases. The InterPro accession (`IPR...`) is the unified meta-entry; member database accessions point to the underlying models:

| Member DB | Accession prefix | Modeling approach |
|-----------|-----------------|-------------------|
| Pfam | PF | Hidden Markov Models (profile HMMs) |
| PANTHER | PTHR | Phylogenetic trees + HMMs |
| PIRSF | PIRSF | Full-length HMMs |
| PRINTS | PR | Fingerprint motif groups |
| PROSITE | PS | Patterns and profiles |
| SMART | SM | HMMs with database integration |
| CDD | cd | Position-specific scoring matrices (PSSMs) |
| NCBIfam | NF | NCBI-curated HMMs |

### Pagination

The InterPro API paginates results at the collection level. Each response includes a `next` URL (or `null` when exhausted) and a `count` field. For large families (e.g., kinases: 10,000+ proteins) always iterate using the `next` cursor.

```python
import requests, time

def iterate_interpro(url: str, page_size: int = 200) -> list:
    """Generic paginator for any InterPro list endpoint."""
    results = []
    params = {"page_size": page_size}
    while url:
        r = requests.get(url, params=params,
                         headers={"Accept": "application/json"}, timeout=60)
        r.raise_for_status()
        data = r.json()
        results.extend(data.get("results", []))
        url = data.get("next")
        params = None
        if url:
            time.sleep(1.0)
    return results
```

## Common Workflows

### Workflow 1: Domain Architecture Report for a Protein Set

**Goal**: Retrieve all InterPro domains for a list of proteins and produce a summary table showing which domains each protein carries.

```python
import requests, time, pandas as pd

INTERPRO_BASE = "https://www.ebi.ac.uk/interpro/api"

def get_domains(uniprot_acc: str) -> list:
    r = requests.get(
        f"{INTERPRO_BASE}/protein/uniprot/{uniprot_acc}/",
        headers={"Accept": "application/json"}, timeout=30
    )
    if r.status_code == 404:
        return []
    r.raise_for_status()
    data = r.json()
    return [
        {
            "protein": uniprot_acc,
            "accession": e["metadata"]["accession"],
            "name": e["metadata"]["name"],
            "type": e["metadata"]["type"],
            "source_db": list(e["metadata"].get("member_databases", {}).keys()),
        }
        for e in data.get("entries", [])
    ]

proteins = ["P04637", "P38398", "Q00987", "P10415"]  # TP53, BRCA1, MDM2, BCL2
rows = []
for acc in proteins:
    rows.extend(get_domains(acc))
    time.sleep(1.0)

df = pd.DataFrame(rows)
print(f"Total domain matches: {len(df)}")
print(df.groupby(["protein", "type"])["accession"].count().unstack(fill_value=0))

# Pivot: proteins × domain accessions
pivot = df[df["type"] == "domain"].pivot_table(
    index="protein", columns="accession", aggfunc="size", fill_value=0
)
pivot.to_csv("domain_architecture_matrix.csv")
print(f"\nDomain × protein matrix: {pivot.shape}")
```

### Workflow 2: Find Kinase Family Members with PDB Structures

**Goal**: Retrieve proteins in a kinase domain family that have experimental structures in the PDB, ranked by resolution.

```python
import requests, time, pandas as pd

INTERPRO_BASE = "https://www.ebi.ac.uk/interpro/api"

# Step 1: Get PDB structures linked to the protein kinase domain entry
r = requests.get(
    f"{INTERPRO_BASE}/structure/pdb/",
    params={"entry_interpro": "IPR000719", "page_size": 200},
    headers={"Accept": "application/json"}, timeout=60
)
r.raise_for_status()
structures = r.json().get("results", [])
print(f"PDB structures with IPR000719 (kinase domain): {len(structures)}")

rows = []
for s in structures:
    m = s["metadata"]
    rows.append({
        "pdb_id": m["accession"],
        "resolution": m.get("resolution"),
        "experiment": m.get("experiment_type", ""),
        "name": m.get("name", ""),
    })

df = pd.DataFrame(rows)
df = df.dropna(subset=["resolution"]).sort_values("resolution")
print(f"\nTop 10 highest-resolution kinase structures:")
print(df[["pdb_id", "resolution", "experiment", "name"]].head(10).to_string(index=False))
df.to_csv("kinase_structures.csv", index=False)
print(f"\nSaved kinase_structures.csv ({len(df)} X-ray / cryo-EM structures)")
```

### Workflow 3: Taxonomic Coverage Bar Chart for a Domain

**Goal**: Visualize how many reviewed proteins in each major kingdom carry a given InterPro domain.

```python
import requests, time
import pandas as pd
import matplotlib.pyplot as plt

INTERPRO_BASE = "https://www.ebi.ac.uk/interpro/api"

def get_taxonomy_counts(interpro_acc: str, page_size: int = 100) -> pd.DataFrame:
    results, url = [], f"{INTERPRO_BASE}/entry/interpro/{interpro_acc}/taxonomy/uniprot/"
    params = {"page_size": page_size}
    while url:
        r = requests.get(url, params=params,
                         headers={"Accept": "application/json"}, timeout=60)
        r.raise_for_status()
        data = r.json()
        for t in data.get("results", []):
            m = t["metadata"]
            results.append({
                "taxon_id": m["accession"],
                "name": m.get("name", ""),
                "proteins": t.get("proteins", 0),
                "rank": m.get("rank", ""),
            })
        url = data.get("next")
        params = None
        if url:
            time.sleep(1.0)
    return pd.DataFrame(results)

IPR_ACC = "IPR000719"   # Protein kinase domain
df = get_taxonomy_counts(IPR_ACC)
print(f"Tax entries for {IPR_ACC}: {len(df)}")

# Filter to top-level lineage entries with most proteins
top = df.nlargest(15, "proteins")
fig, ax = plt.subplots(figsize=(10, 5))
bars = ax.barh(top["name"], top["proteins"], color="#2171B5")
ax.bar_label(bars, fmt="%d", padding=3, fontsize=8)
ax.set_xlabel("Number of Reviewed Proteins")
ax.set_title(f"Taxonomic Distribution of {IPR_ACC} (Protein Kinase Domain)")
ax.invert_yaxis()
plt.tight_layout()
plt.savefig(f"{IPR_ACC}_taxonomy.png", dpi=150, bbox_inches="tight")
print(f"Saved {IPR_ACC}_taxonomy.png")
```

## Key Parameters

| Parameter | Endpoint | Default | Range / Options | Effect |
|-----------|----------|---------|-----------------|--------|
| `search` | `entry/interpro/` | — | free-text string | Keyword filter on entry name and short name |
| `type` | `entry/interpro/` | all types | `family`, `domain`, `homologous_superfamily`, `repeat`, `site` | Filter entries by InterPro type |
| `page_size` | all list endpoints | `20` | `1`–`200` | Results returned per page |
| `entry_interpro` | `structure/pdb/` | — | `IPR######` | Filter structures by linked InterPro entry |
| `source_database` | `protein/` | — | `reviewed`, `uniprot`, `trembl` | Filter proteins by UniProt curation level |
| `reviewed` (URL path) | `entry/{ipr}/{acc}/protein/` | uniprot | `reviewed`, `uniprot` | Swiss-Prot reviewed only vs all UniProtKB |
| `relations` | `entry/interpro/{acc}/` | — | `contains`, `contained_by`, `child_of`, `parent_of` | Navigate the InterPro hierarchy |
| `next` | all list endpoints | — | URL from response | Cursor-based pagination; use the full URL from the `next` field |

## Best Practices

1. **Use `reviewed` proteins for curated domain lists**: The unreviewed TrEMBL set is 5–10× larger and contains automated predictions. For benchmarking, family analysis, or training sets, restrict to `reviewed` (Swiss-Prot) entries to avoid noise from unreviewed predictions.

2. **Chunk large taxonomy or protein lists**: Retrieving all 10,000+ proteins for a broad family like the protein kinase superfamily can take minutes and produce large payloads. Limit queries with `page_size=200` and the `next` cursor; store intermediate results to disk.

3. **Add `time.sleep(1.0)` between paginated calls**: The InterPro API is shared EBI infrastructure with no published rate limit. A 1-second pause per page is a safe minimum for batch scripts.

4. **Prefer InterPro accessions over member DB accessions for cross-database queries**: A Pfam PF00069 and PANTHER PTHR24340 both model kinase domains but with different protein coverage. Using the parent InterPro `IPR000719` gives the union of all member DB matches in one query.

5. **Check `type` before interpreting `entry_protein_locations`**: Only `domain`, `repeat`, and `site` entries carry meaningful position information. `family` and `homologous_superfamily` entries typically span the full protein and their coordinates are less informative.

## Common Recipes

### Recipe: Quick Domain Check for a Protein

When to use: Given a UniProt accession, rapidly list which InterPro domains it contains.

```python
import requests

INTERPRO_BASE = "https://www.ebi.ac.uk/interpro/api"

def list_protein_domains(uniprot_acc: str) -> list:
    """Return list of (accession, type, name) tuples for a protein."""
    r = requests.get(
        f"{INTERPRO_BASE}/protein/uniprot/{uniprot_acc}/",
        headers={"Accept": "application/json"}, timeout=30
    )
    r.raise_for_status()
    return [
        (e["metadata"]["accession"], e["metadata"]["type"], e["metadata"]["name"])
        for e in r.json().get("entries", [])
    ]

domains = list_protein_domains("P00533")   # EGFR
print(f"InterPro entries in EGFR (P00533): {len(domains)}")
for acc, etype, name in domains:
    print(f"  {acc}  {etype:<25}  {name}")
# InterPro entries in EGFR (P00533): 10
#   IPR009030  homologous_superfamily   Growth factor receptor, cysteine-rich
#   IPR000719  domain                   Protein kinase domain
```

### Recipe: Find All Proteins in a Family with Source DB Coverage

When to use: Map how many proteins in a domain family are covered by each member database (Pfam vs PANTHER vs SMART, etc.).

```python
import requests, time
import pandas as pd

INTERPRO_BASE = "https://www.ebi.ac.uk/interpro/api"

interpro_acc = "IPR000719"   # Protein kinase domain
r = requests.get(
    f"{INTERPRO_BASE}/entry/interpro/{interpro_acc}/",
    headers={"Accept": "application/json"}, timeout=30
)
r.raise_for_status()
member_dbs = r.json()["metadata"].get("member_databases", {})
print(f"Member databases for {interpro_acc}:")
for db, details in member_dbs.items():
    print(f"  {db}: {details}")

# Visualize member database source breakdown
labels = list(member_dbs.keys())
import matplotlib.pyplot as plt
fig, ax = plt.subplots(figsize=(7, 4))
ax.bar(labels, [1] * len(labels), color="#4472C4")   # presence/absence per DB
ax.set_ylabel("Integrated (1=yes)")
ax.set_title(f"Member databases in {interpro_acc}")
plt.tight_layout()
plt.savefig(f"{interpro_acc}_member_dbs.png", dpi=150, bbox_inches="tight")
```

### Recipe: Get GO Terms for an InterPro Entry

When to use: Bridge from structural domain to functional GO annotation.

```python
import requests

INTERPRO_BASE = "https://www.ebi.ac.uk/interpro/api"

def get_go_terms_for_entry(interpro_acc: str) -> list:
    """Return GO terms associated with an InterPro entry."""
    r = requests.get(
        f"{INTERPRO_BASE}/entry/interpro/{interpro_acc}/",
        headers={"Accept": "application/json"}, timeout=30
    )
    r.raise_for_status()
    go_terms = r.json()["metadata"].get("go_terms", [])
    return [
        {"id": g["identifier"], "name": g["name"],
         "category": g.get("category", {}).get("name", "")}
        for g in go_terms
    ]

go_terms = get_go_terms_for_entry("IPR000719")
print(f"GO terms for IPR000719 (protein kinase domain): {len(go_terms)}")
for g in go_terms:
    print(f"  {g['id']}  [{g['category'][:2].upper()}]  {g['name']}")
# GO terms for IPR000719 (protein kinase domain): 3
#   GO:0004672  [MO]  protein kinase activity
#   GO:0005524  [MO]  ATP binding
#   GO:0006468  [BI]  protein phosphorylation
```

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| `HTTP 404` on protein lookup | Accession not found in InterPro | Verify the UniProt accession exists; isoform accessions (P12345-2) may not be indexed separately |
| Empty `entries` list for a protein | Protein has no InterPro matches (e.g., intrinsically disordered) | Check UniProt directly; not all proteins have classified domains |
| `HTTP 400` on entry search | Invalid query parameters or unsupported `type` value | Use one of: `family`, `domain`, `homologous_superfamily`, `repeat`, `site` |
| Pagination stops early | `next` is `null` before expected count | This is correct; all results have been returned |
| Very slow response for large families | Protein set has thousands of members | Increase `page_size` to `200`; persist results after each page |
| `ConnectionError` or `Timeout` | Transient network or server issue | Retry with exponential backoff; EBI services occasionally have brief downtimes |
| Member DB accessions missing | Entry is new and member DB integration is pending | Use the InterPro accession for queries; member DB-level details update with each release |

## Related Skills

- `uniprot-protein-database` — UniProt REST API for protein sequences, Swiss-Prot functional annotations (active sites, PTMs, disease associations), and ID mapping
- `esm-protein-language-model` — Generate protein language model embeddings for sequences; useful after identifying a protein family with InterPro
- `pdb-database` — Retrieve and download experimental 3D structures by PDB ID; cross-reference structure IDs discovered via InterPro structure queries

## References

- [InterPro REST API documentation](https://interpro-documentation.readthedocs.io/en/latest/api.html) — Endpoint reference, filters, and example queries
- [Blum et al., Nucleic Acids Research 2021](https://doi.org/10.1093/nar/gkaa977) — InterPro flagship paper describing member database integration
- [InterPro web portal](https://www.ebi.ac.uk/interpro/) — Interactive protein domain browser
- [Paysan-Lafosse et al., Nucleic Acids Research 2023](https://doi.org/10.1093/nar/gkac993) — InterPro 2023 update describing new entry types and member databases
