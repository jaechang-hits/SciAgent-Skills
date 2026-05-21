---
name: "pdb-database"
description: "Query RCSB PDB (200K+ structures) via the public REST + GraphQL APIs with plain `requests` (no SDK). Search by text, attribute, sequence, or 3D structure similarity (Search API); retrieve metadata via GraphQL (Data API); download PDB/mmCIF from files.rcsb.org. For AlphaFold predictions use alphafold-database-access; for protein sequences only use uniprot-protein-database."
license: "BSD-3-Clause"
---

# PDB Database

> **Why no SDK?** The `rcsb-api` Python SDK is convenient sugar over three public, no-auth REST endpoints (`search.rcsb.org`, `data.rcsb.org`, `files.rcsb.org`). When the SDK is unavailable, every operation can be reproduced with plain `requests` and a small JSON payload. This SKILL.md uses the REST path throughout so the code runs in any environment with `requests` installed.

## Overview

RCSB PDB is the worldwide repository for 3D structural data of biological macromolecules with 200,000+ experimentally determined structures. Programmatic access is via three free, no-auth endpoints:

| API | Base URL | Method | Purpose |
|---|---|---|---|
| **Search** | `https://search.rcsb.org/rcsbsearch/v2/query` | `POST` JSON | Find PDB IDs by text, attribute filters, sequence, or 3D similarity |
| **Data** | `https://data.rcsb.org/graphql` | `POST` GraphQL | Retrieve structured metadata (entries, polymer entities, assemblies, ligands) |
| **Files** | `https://files.rcsb.org/download/{id}.{format}` | `GET` | Download coordinate files (mmCIF, PDB, FASTA) |

Use this skill for programmatic structural biology queries, drug target analysis, and protein family comparisons.

## When to Use

- Searching for protein or nucleic acid crystal/cryo-EM/NMR structures by keyword or property
- Finding structures similar to a query sequence (MMseqs2) or 3D geometry (BioZernike)
- Retrieving experimental metadata (resolution, method, organism, deposition date) for structure sets
- Downloading coordinate files (PDB, mmCIF) for molecular dynamics, docking, or visualization
- Building structure-based datasets for machine learning or drug discovery pipelines
- Comparing protein-ligand complexes across a target family
- For AlphaFold predicted structures, use `alphafold-database-access` instead
- For protein sequence/annotation queries without structures, use `uniprot-protein-database` instead

## Prerequisites

- **Python packages**: `requests` (only requirement). Optional: `biopython` for parsing downloaded coordinate files.
- **No API key required**: RCSB PDB is freely accessible.
- **Rate limits**: No published hard limit. Polite delays of `time.sleep(0.2-0.5)` between requests are sufficient; implement exponential backoff on HTTP 429.

```bash
pip install requests
# Optional, for coordinate parsing:
pip install biopython
```

## Quick Start

Typical search-then-fetch pattern: hit the Search API, get a list of PDB IDs, then resolve metadata via the GraphQL Data API.

```python
import requests

SEARCH = "https://search.rcsb.org/rcsbsearch/v2/query"
DATA   = "https://data.rcsb.org/graphql"

# 1. Search: human X-ray structures of "kinase" at resolution < 2.0 Å
payload = {
    "query": {
        "type": "group", "logical_operator": "and",
        "nodes": [
            {"type": "terminal", "service": "full_text",
             "parameters": {"value": "kinase"}},
            {"type": "terminal", "service": "text",
             "parameters": {"attribute": "rcsb_entity_source_organism.scientific_name",
                            "operator": "exact_match", "value": "Homo sapiens"}},
            {"type": "terminal", "service": "text",
             "parameters": {"attribute": "rcsb_entry_info.resolution_combined",
                            "operator": "less", "value": 2.0}},
        ],
    },
    "return_type": "entry",
    "request_options": {"paginate": {"rows": 10}},
}
r = requests.post(SEARCH, json=payload, timeout=30)
r.raise_for_status()
result = r.json()
pdb_ids = [hit["identifier"] for hit in result["result_set"]]
print(f"Total matches: {result['total_count']}, first batch: {pdb_ids}")

# 2. Fetch metadata for the first hit via GraphQL
gql = """{ entry(entry_id: "%s") {
  struct { title }
  exptl { method }
  rcsb_entry_info { resolution_combined deposited_atom_count polymer_entity_count }
} }""" % pdb_ids[0]
r2 = requests.post(DATA, json={"query": gql}, timeout=30)
entry = r2.json()["data"]["entry"]
print(entry["struct"]["title"])
print(f"Method: {entry['exptl'][0]['method']}, Resolution: {entry['rcsb_entry_info']['resolution_combined']} Å")
```

## Core API

### Module 1: Text and Attribute Search

**Free-text search** uses `service: "full_text"` and searches across all indexed fields.

```python
import requests
SEARCH = "https://search.rcsb.org/rcsbsearch/v2/query"

def text_search(keyword, rows=25):
    payload = {
        "query": {"type": "terminal", "service": "full_text",
                  "parameters": {"value": keyword}},
        "return_type": "entry",
        "request_options": {"paginate": {"rows": rows}},
    }
    r = requests.post(SEARCH, json=payload, timeout=30)
    r.raise_for_status()
    data = r.json()
    return [hit["identifier"] for hit in data["result_set"]], data["total_count"]

ids, total = text_search("hemoglobin")
print(f"Found {total} structures; first batch: {ids[:5]}")
```

**Attribute search** uses `service: "text"` with structured `attribute`/`operator`/`value` parameters.

```python
import requests
SEARCH = "https://search.rcsb.org/rcsbsearch/v2/query"

def attribute_search(attribute, operator, value, return_type="entry", rows=25):
    payload = {
        "query": {"type": "terminal", "service": "text",
                  "parameters": {"attribute": attribute,
                                 "operator": operator,
                                 "value": value}},
        "return_type": return_type,
        "request_options": {"paginate": {"rows": rows}},
    }
    r = requests.post(SEARCH, json=payload, timeout=30)
    r.raise_for_status()
    return r.json()

# Human proteins
human = attribute_search("rcsb_entity_source_organism.scientific_name",
                          "exact_match", "Homo sapiens", rows=5)
print(f"Human structures: {human['total_count']}")

# X-ray only
xray = attribute_search("exptl.method", "exact_match", "X-RAY DIFFRACTION", rows=5)
print(f"X-ray structures: {xray['total_count']}")

# Resolution range: 1.5–2.5 Å
res = attribute_search(
    "rcsb_entry_info.resolution_combined", "range",
    {"from": 1.5, "to": 2.5, "include_lower": True, "include_upper": True},
    rows=5
)
print(f"1.5–2.5 Å: {res['total_count']}")
```

### Module 2: Sequence Similarity Search

Find structures with similar sequences using MMseqs2. Service is `"sequence"`; `target` selects protein vs. nucleic acid.

```python
import requests
SEARCH = "https://search.rcsb.org/rcsbsearch/v2/query"

kras_seq = ("MTEYKLVVVGAGGVGKSALTIQLIQNHFVDEYDPTIEDSYRKQVVIDGETCLLDILDTAGQ"
            "EEYSAMRDQYMRTGEGFLCVFAINNTKSFEDIHHYREQIKRVKDSEDVPMVLVGNKCDLPS"
            "RTVDTKQAQDLARSYGIPFIETSAKTRQGVDDAFYTLVREIRKHKEKMSK")

payload = {
    "query": {
        "type": "terminal", "service": "sequence",
        "parameters": {
            "target": "pdb_protein_sequence",  # or "pdb_dna_sequence", "pdb_rna_sequence"
            "value": kras_seq,
            "evalue_cutoff": 0.1,
            "identity_cutoff": 0.9,
        },
    },
    "return_type": "polymer_entity",
    "request_options": {"paginate": {"rows": 10}},
}
r = requests.post(SEARCH, json=payload, timeout=30)
r.raise_for_status()
data = r.json()
print(f"KRAS-like hits: {data['total_count']}")
for hit in data["result_set"][:5]:
    print(f"  {hit['identifier']}  score={hit.get('score', 'n/a')}")
```

### Module 3: Structure Similarity Search

Find structures with similar 3D geometry using BioZernike descriptors. Service is `"structure"`; pass the reference entry + assembly ID.

```python
import requests
SEARCH = "https://search.rcsb.org/rcsbsearch/v2/query"

payload = {
    "query": {
        "type": "terminal", "service": "structure",
        "parameters": {
            "value": {"entry_id": "4HHB", "assembly_id": "1"},
            "operator": "strict_shape_match",  # or "relaxed_shape_match"
        },
    },
    "return_type": "polymer_entity",
    "request_options": {"paginate": {"rows": 10}},
}
r = requests.post(SEARCH, json=payload, timeout=30)
r.raise_for_status()
data = r.json()
print(f"Structurally similar to 4HHB: {data['total_count']}")
for hit in data["result_set"][:5]:
    print(f"  {hit['identifier']}  score={hit.get('score', 'n/a')}")
```

### Module 4: Data Retrieval (GraphQL)

The GraphQL endpoint at `data.rcsb.org/graphql` is the canonical way to retrieve structured metadata for known PDB IDs. One request can pull fields across the full data hierarchy (entry → polymer_entity → assembly → chem_comp).

```python
import requests
DATA = "https://data.rcsb.org/graphql"

# Entry-level metadata
gql = """{ entry(entry_id: "4HHB") {
  struct { title }
  exptl { method }
  rcsb_entry_info { resolution_combined deposited_atom_count polymer_entity_count nonpolymer_entity_count }
  rcsb_accession_info { deposit_date initial_release_date }
} }"""
r = requests.post(DATA, json={"query": gql}, timeout=30)
entry = r.json()["data"]["entry"]
print(f"Title       : {entry['struct']['title']}")
print(f"Method      : {entry['exptl'][0]['method']}")
print(f"Resolution  : {entry['rcsb_entry_info']['resolution_combined']} Å")
print(f"Atoms       : {entry['rcsb_entry_info']['deposited_atom_count']}")
```

```python
# Polymer entity (sequence, organism, MW)
gql = """{ polymer_entity(entry_id: "4HHB", entity_id: "1") {
  entity_poly { pdbx_seq_one_letter_code }
  rcsb_polymer_entity { formula_weight }
  rcsb_entity_source_organism { scientific_name ncbi_taxonomy_id }
} }"""
r = requests.post(DATA, json={"query": gql}, timeout=30)
pe = r.json()["data"]["polymer_entity"]
print(f"Sequence (first 50): {pe['entity_poly']['pdbx_seq_one_letter_code'][:50]}")
print(f"Organism : {pe['rcsb_entity_source_organism'][0]['scientific_name']}")
print(f"MW       : {pe['rcsb_polymer_entity']['formula_weight']}")
```

```python
# Batch: pull metadata for many entries in one request
gql = """{ entries(entry_ids: ["4HHB", "1A3N", "1HHB"]) {
  rcsb_id
  struct { title }
  exptl { method }
  rcsb_entry_info { resolution_combined }
} }"""
r = requests.post(DATA, json={"query": gql}, timeout=30)
for e in r.json()["data"]["entries"]:
    res = e["rcsb_entry_info"]["resolution_combined"]
    print(f"  {e['rcsb_id']}: {e['exptl'][0]['method']:<25} {res} Å  — {e['struct']['title'][:40]}")
```

### Module 5: File Download

Coordinate files (mmCIF, PDB, FASTA, assembly variants) are served directly from `files.rcsb.org`.

```python
import requests

def download_structure(pdb_id, fmt="cif", output_dir="."):
    """Download mmCIF / PDB / FASTA. URLs: .pdb, .cif, /fasta/entry/{ID}, .pdb1 (assembly)."""
    url = f"https://files.rcsb.org/download/{pdb_id}.{fmt}"
    r = requests.get(url, timeout=60)
    if r.status_code == 200:
        path = f"{output_dir}/{pdb_id}.{fmt}"
        # mmCIF / PDB are text; assemblies and biological units are also text
        with open(path, "w") as f:
            f.write(r.text)
        print(f"Downloaded {path}  ({len(r.text)/1024:.1f} KB)")
        return path
    print(f"HTTP {r.status_code} for {pdb_id}.{fmt}")
    return None

download_structure("4HHB", fmt="cif")
download_structure("4HHB", fmt="pdb")
```

```python
# FASTA sequence for an entry
r = requests.get("https://www.rcsb.org/fasta/entry/4HHB", timeout=30)
r.raise_for_status()
print(r.text[:400])
```

### Module 6: Query Composition (group + logical_operator)

Combine terminal queries with `type: "group"` and a `logical_operator` of `"and"` / `"or"`. Nested groups give arbitrary boolean expressions; negation is via `"node_id"` references with `"operator": "negate"` on the group (rare — usually expressed as the inverse attribute filter).

```python
import requests, datetime
SEARCH = "https://search.rcsb.org/rcsbsearch/v2/query"

# AND: high-resolution human structures
q_and = {
    "type": "group", "logical_operator": "and",
    "nodes": [
        {"type": "terminal", "service": "text",
         "parameters": {"attribute": "rcsb_entity_source_organism.scientific_name",
                        "operator": "exact_match", "value": "Homo sapiens"}},
        {"type": "terminal", "service": "text",
         "parameters": {"attribute": "rcsb_entry_info.resolution_combined",
                        "operator": "less", "value": 2.0}},
    ],
}

# OR: human or mouse
q_or = {
    "type": "group", "logical_operator": "or",
    "nodes": [
        {"type": "terminal", "service": "text",
         "parameters": {"attribute": "rcsb_entity_source_organism.scientific_name",
                        "operator": "exact_match", "value": "Homo sapiens"}},
        {"type": "terminal", "service": "text",
         "parameters": {"attribute": "rcsb_entity_source_organism.scientific_name",
                        "operator": "exact_match", "value": "Mus musculus"}},
    ],
}

# Combined: recent (last 30 days) + high-quality
one_month_ago = (datetime.date.today() - datetime.timedelta(days=30)).isoformat()
today = datetime.date.today().isoformat()
q_recent_hq = {
    "type": "group", "logical_operator": "and",
    "nodes": [
        {"type": "terminal", "service": "text",
         "parameters": {"attribute": "rcsb_entry_info.resolution_combined",
                        "operator": "less", "value": 2.0}},
        {"type": "terminal", "service": "text",
         "parameters": {"attribute": "refine.ls_R_factor_R_free",
                        "operator": "less", "value": 0.25}},
        {"type": "terminal", "service": "text",
         "parameters": {"attribute": "rcsb_accession_info.initial_release_date",
                        "operator": "range",
                        "value": {"from": one_month_ago, "to": today,
                                  "include_lower": True, "include_upper": True}}},
    ],
}

payload = {"query": q_recent_hq, "return_type": "entry",
           "request_options": {"paginate": {"rows": 5}}}
r = requests.post(SEARCH, json=payload, timeout=30)
print(f"Recent high-quality: {r.json()['total_count']} structures")
```

### Module 7: Pagination + Batch with Rate Limiting

Search responses include `total_count`. Paginate with `request_options.paginate.start` and `rows` (max ~10000 per page in practice; 100–500 is a good batch size).

```python
import requests, time
SEARCH = "https://search.rcsb.org/rcsbsearch/v2/query"

def search_all(query_node, return_type="entry", page=100, max_results=None, delay=0.3):
    """Paginate through every result; rate-limit between pages."""
    out, start = [], 0
    while True:
        payload = {"query": query_node, "return_type": return_type,
                   "request_options": {"paginate": {"start": start, "rows": page}}}
        r = requests.post(SEARCH, json=payload, timeout=30)
        r.raise_for_status()
        d = r.json()
        batch = [h["identifier"] for h in d.get("result_set", [])]
        if not batch:
            break
        out.extend(batch)
        if max_results and len(out) >= max_results:
            return out[:max_results]
        if len(batch) < page or len(out) >= d.get("total_count", 0):
            break
        start += page
        time.sleep(delay)
    return out

# Example: every insulin entry
ids = search_all(
    {"type": "terminal", "service": "full_text", "parameters": {"value": "insulin"}},
    max_results=300,
)
print(f"Insulin entries collected: {len(ids)}")
```

```python
# Batch metadata fetch via GraphQL `entries(...)` to avoid one round-trip per ID
DATA = "https://data.rcsb.org/graphql"

def batch_metadata(pdb_ids, chunk=50):
    """Fetch (title, method, resolution) for many entries with one POST per chunk."""
    all_rows = []
    for i in range(0, len(pdb_ids), chunk):
        ids_arr = pdb_ids[i:i+chunk]
        ids_str = ", ".join(f'"{p}"' for p in ids_arr)
        gql = f"""{{ entries(entry_ids: [{ids_str}]) {{
            rcsb_id
            struct {{ title }}
            exptl {{ method }}
            rcsb_entry_info {{ resolution_combined }}
        }} }}"""
        r = requests.post(DATA, json={"query": gql}, timeout=60)
        r.raise_for_status()
        for e in r.json()["data"]["entries"]:
            res = e["rcsb_entry_info"]["resolution_combined"]
            all_rows.append({
                "pdb_id": e["rcsb_id"],
                "method": e["exptl"][0]["method"] if e["exptl"] else None,
                "resolution": res[0] if isinstance(res, list) and res else res,
                "title": e["struct"]["title"],
            })
    return all_rows

rows = batch_metadata(ids[:20])
for r in rows[:5]:
    print(f"  {r['pdb_id']}: {r['method']:<25} {r['resolution']} Å  — {r['title'][:50]}")
```

## Key Concepts

### Search Service Cheat Sheet

| Service | Use case | Required parameters |
|---|---|---|
| `full_text` | Free-text keyword across all indexed fields | `value` (string) |
| `text` | Structured attribute filter | `attribute`, `operator`, `value` |
| `sequence` | MMseqs2 sequence similarity | `target` ∈ {`pdb_protein_sequence`, `pdb_dna_sequence`, `pdb_rna_sequence`}, `value` (sequence), `evalue_cutoff`, `identity_cutoff` |
| `seqmotif` | Pattern / regex / PROSITE motif | `value` (pattern), `pattern_type` ∈ {`simple`, `prosite`, `regex`} |
| `structure` | 3D shape similarity (BioZernike) | `value` (`{entry_id, assembly_id}`), `operator` ∈ {`strict_shape_match`, `relaxed_shape_match`} |
| `strucmotif` | 3D residue-arrangement motif | `value` (residue list), `rmsd_cutoff` |
| `chemical` | Ligand similarity by SMILES/InChI | `value`, `match_type` ∈ {`graph-exact`, `graph-relaxed`, `fingerprint-similarity`, `sub-structure-stereo-relaxed`} |

### AttributeQuery Operators (service: `"text"`)

| Operator | Value shape | Example |
|---|---|---|
| `exact_match` | string | `"Homo sapiens"` |
| `contains_words` / `contains_phrase` | string | `"tyrosine kinase"` |
| `equals` / `greater` / `less` / `greater_or_equal` / `less_or_equal` | number | `2.0` |
| `range` | `{from, to, include_lower, include_upper}` | `{"from": 1.5, "to": 2.5, "include_lower": True, "include_upper": True}` |
| `exists` | (none) | — |
| `in` | array | `["X-RAY DIFFRACTION", "ELECTRON MICROSCOPY"]` |

### Return Types

`return_type` controls the granularity of identifiers in `result_set`:

| `return_type` | Identifier shape | Example |
|---|---|---|
| `entry` | `4HHB` | One per PDB ID |
| `polymer_entity` | `4HHB_1` | One per polymer chain entity |
| `non_polymer_entity` | `4HHB_2` | Ligands, cofactors |
| `assembly` | `4HHB-1` | Biological unit |
| `polymer_instance` | `4HHB.A` | Individual chain coordinates |
| `mol_definition` | `HEM` | Chemical component (PDB ligand code) |

### Common Data API GraphQL Roots

| Root | Identifier shape | Returns |
|---|---|---|
| `entry(entry_id: ...)` | `"4HHB"` | Entry-level metadata |
| `entries(entry_ids: [...])` | array | Batch entry lookup |
| `polymer_entity(entry_id: ..., entity_id: ...)` | `"4HHB"`, `"1"` | Sequence + organism |
| `polymer_entity_instance(entry_id: ..., asym_id: ...)` | `"4HHB"`, `"A"` | Chain-level coords/metadata |
| `assembly(entry_id: ..., assembly_id: ...)` | `"4HHB"`, `"1"` | Biological assembly |
| `chem_comp(comp_id: ...)` | `"HEM"` | Small molecule reference |

### File Formats

| Format | URL pattern | Notes |
|---|---|---|
| mmCIF | `https://files.rcsb.org/download/{id}.cif` | Recommended; no atom-count limit |
| PDB | `https://files.rcsb.org/download/{id}.pdb` | Legacy; 99,999 atom limit |
| Assembly (mmCIF) | `https://files.rcsb.org/download/{id}-assembly{N}.cif` | Biological unit |
| FASTA | `https://www.rcsb.org/fasta/entry/{id}` | Sequence only |

## Common Workflows

### Workflow 1: Drug Target Structure Set

**Goal**: Find high-resolution human EGFR structures with bound ligands.

```python
import requests, time

SEARCH = "https://search.rcsb.org/rcsbsearch/v2/query"
DATA   = "https://data.rcsb.org/graphql"

payload = {
    "query": {
        "type": "group", "logical_operator": "and",
        "nodes": [
            {"type": "terminal", "service": "full_text",
             "parameters": {"value": "EGFR epidermal growth factor receptor"}},
            {"type": "terminal", "service": "text",
             "parameters": {"attribute": "rcsb_entity_source_organism.scientific_name",
                            "operator": "exact_match", "value": "Homo sapiens"}},
            {"type": "terminal", "service": "text",
             "parameters": {"attribute": "rcsb_entry_info.resolution_combined",
                            "operator": "less", "value": 2.5}},
        ],
    },
    "return_type": "entry",
    "request_options": {"paginate": {"rows": 50}},
}
r = requests.post(SEARCH, json=payload, timeout=30)
r.raise_for_status()
pdb_ids = [h["identifier"] for h in r.json()["result_set"]]
print(f"EGFR ≤2.5 Å human structures: {len(pdb_ids)}")

# Filter to entries with bound ligands via batch GraphQL
ids_str = ", ".join(f'"{p}"' for p in pdb_ids[:20])
gql = f"""{{ entries(entry_ids: [{ids_str}]) {{
    rcsb_id
    struct {{ title }}
    rcsb_entry_info {{ resolution_combined nonpolymer_entity_count }}
}} }}"""
r2 = requests.post(DATA, json={"query": gql}, timeout=60)
for e in r2.json()["data"]["entries"]:
    n_lig = e["rcsb_entry_info"]["nonpolymer_entity_count"] or 0
    if n_lig > 0:
        res = e["rcsb_entry_info"]["resolution_combined"]
        res_v = res[0] if isinstance(res, list) else res
        print(f"  {e['rcsb_id']}: {res_v} Å, ligands={n_lig}  — {e['struct']['title'][:60]}")
    time.sleep(0.05)
```

### Workflow 2: Protein Family — Sequence-Similar Structures

**Goal**: Find all PDB structures with sequence similar to a query (KRAS), then summarize their resolution + experimental method.

```python
import requests, time

SEARCH = "https://search.rcsb.org/rcsbsearch/v2/query"
DATA   = "https://data.rcsb.org/graphql"

kras_seq = ("MTEYKLVVVGAGGVGKSALTIQLIQNHFVDEYDPTIEDSYRKQVVIDGETCLLDILDTAGQ"
            "EEYSAMRDQYMRTGEGFLCVFAINNTKSFEDIHHYREQIKRVKDSEDVPMVLVGNKCDLPS"
            "RTVDTKQAQDLARSYGIPFIETSAKTRQGVDDAFYTLVREIRKHKEKMSK")

payload = {
    "query": {
        "type": "terminal", "service": "sequence",
        "parameters": {"target": "pdb_protein_sequence", "value": kras_seq,
                       "evalue_cutoff": 1e-5, "identity_cutoff": 0.5},
    },
    "return_type": "polymer_entity",
    "request_options": {"paginate": {"rows": 20}},
}
r = requests.post(SEARCH, json=payload, timeout=30)
hits = r.json()["result_set"]
print(f"KRAS family hits: {len(hits)}")

# Unique PDB IDs from polymer_entity identifiers (e.g., "4OBE_1" -> "4OBE")
entry_ids = sorted({h["identifier"].split("_")[0] for h in hits})

# Batch metadata
ids_str = ", ".join(f'"{p}"' for p in entry_ids)
gql = f"""{{ entries(entry_ids: [{ids_str}]) {{
    rcsb_id
    struct {{ title }}
    exptl {{ method }}
    rcsb_entry_info {{ resolution_combined }}
}} }}"""
r2 = requests.post(DATA, json={"query": gql}, timeout=60)
for e in sorted(r2.json()["data"]["entries"],
                key=lambda x: (x["rcsb_entry_info"]["resolution_combined"] or [99])[0] if isinstance(x["rcsb_entry_info"]["resolution_combined"], list) else (x["rcsb_entry_info"]["resolution_combined"] or 99)):
    res = e["rcsb_entry_info"]["resolution_combined"]
    res_v = res[0] if isinstance(res, list) else res
    print(f"  {e['rcsb_id']}: {res_v} Å  {e['exptl'][0]['method']:<25} {e['struct']['title'][:50]}")
```

### Workflow 3: Download + Parse with BioPython

**Goal**: Download mmCIF, then enumerate chains with BioPython.

```python
import requests
from Bio.PDB import MMCIFParser

pdb_id = "4HHB"
r = requests.get(f"https://files.rcsb.org/download/{pdb_id}.cif", timeout=60)
r.raise_for_status()
with open(f"{pdb_id}.cif", "w") as f:
    f.write(r.text)

parser = MMCIFParser(QUIET=True)
structure = parser.get_structure(pdb_id, f"{pdb_id}.cif")
for model in structure:
    for chain in model:
        std_res = [r for r in chain if r.id[0] == " "]
        atoms = sum(len(list(r.get_atoms())) for r in std_res)
        print(f"Chain {chain.id}: {len(std_res)} residues, {atoms} atoms")
```

## Key Parameters

| Parameter | Endpoint | Default | Range / Options | Effect |
|-----------|----------|---------|-----------------|--------|
| `value` | search `sequence` | required | protein/DNA/RNA sequence string | Query sequence for MMseqs2 |
| `evalue_cutoff` | search `sequence` | `0.1` | `1e-10`–`10` | E-value threshold |
| `identity_cutoff` | search `sequence` | `0.9` | `0.0`–`1.0` | Minimum identity fraction |
| `target` | search `sequence` | `"pdb_protein_sequence"` | `pdb_protein_sequence`, `pdb_dna_sequence`, `pdb_rna_sequence` | Sequence type |
| `operator` | search `text` (attribute) | required | see Attribute Operators | Comparison kind |
| `operator` | search `structure` | `strict_shape_match` | `strict_shape_match`, `relaxed_shape_match` | 3D match stringency |
| `return_type` | all search | `entry` | `entry`, `polymer_entity`, `assembly`, `polymer_instance`, `mol_definition`, … | Identifier granularity |
| `paginate.start` / `paginate.rows` | `request_options` | `0` / `25` | up to ~10000 rows/page in practice | Pagination window |
| GraphQL field `entries(entry_ids: [...])` | `data.rcsb.org/graphql` | — | array of PDB IDs | Batch entry metadata |

## Best Practices

1. **Search → fetch**: Use the Search API to get a list of IDs, then GraphQL `entries(entry_ids: [...])` for batch metadata. Avoid one GraphQL request per ID.

2. **Use `full_text` vs `text` deliberately**: free-text keyword search needs `"service": "full_text"`. Structured attribute filters need `"service": "text"`. They are not interchangeable.

3. **mmCIF over PDB format**: PDB format is being phased out and has a 99,999 atom limit. Always download `.cif` for new code.

4. **Set realistic `paginate.rows`**: `rows: 100` is a good default for batch work; the API may slow down beyond ~10000. Loop with `paginate.start` for full traversal.

5. **Rate limit with `time.sleep(0.2)` in batch loops**: No published hard cap, but the public infrastructure is shared. On `HTTP 429`, back off exponentially.

6. **Inspect the payload before posting**: `print(json.dumps(payload, indent=2))` is the cheapest way to debug `HTTP 400` errors.

7. **`entries(entry_ids: [...])` does not validate every ID**: if one ID is wrong, the whole array returns `null` entries. Validate IDs separately if you can't trust the source.

## Common Recipes

### Recipe: Get FASTA for a PDB ID

```python
import requests
r = requests.get("https://www.rcsb.org/fasta/entry/4HHB", timeout=30)
print(r.text)
```

### Recipe: All chains in an entry

```python
import requests
DATA = "https://data.rcsb.org/graphql"
gql = """{ entry(entry_id: "4HHB") {
  polymer_entities {
    rcsb_id
    rcsb_polymer_entity_container_identifiers { auth_asym_ids }
    entity_poly { rcsb_entity_polymer_type pdbx_seq_one_letter_code_can }
  }
} }"""
r = requests.post(DATA, json={"query": gql}, timeout=30)
for pe in r.json()["data"]["entry"]["polymer_entities"]:
    chains = pe["rcsb_polymer_entity_container_identifiers"]["auth_asym_ids"]
    seq    = pe["entity_poly"]["pdbx_seq_one_letter_code_can"][:50]
    print(f"  {pe['rcsb_id']} chains={chains}  type={pe['entity_poly']['rcsb_entity_polymer_type']}  seq={seq}…")
```

### Recipe: List all ligands in an entry

```python
import requests
DATA = "https://data.rcsb.org/graphql"
gql = """{ entry(entry_id: "1IEP") {
  nonpolymer_entities {
    rcsb_id
    nonpolymer_comp { chem_comp { id name formula } }
  }
} }"""
r = requests.post(DATA, json={"query": gql}, timeout=30)
for npe in r.json()["data"]["entry"]["nonpolymer_entities"]:
    cc = npe["nonpolymer_comp"]["chem_comp"]
    print(f"  {npe['rcsb_id']}: {cc['id']} ({cc['name']})  {cc['formula']}")
```

### Recipe: Inspect available search attributes

The Search API exposes a JSON schema at `https://search.rcsb.org/rcsbsearch/v2/metadata/schema`. Use it to look up valid attribute paths.

```python
import requests
r = requests.get("https://search.rcsb.org/rcsbsearch/v2/metadata/schema", timeout=30)
schema = r.json()
# Schema lists hundreds of attribute paths; sample a few
sample_paths = [k for k in schema if "resolution" in k.lower()][:5]
print(sample_paths)
```

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| `HTTP 400 — Invalid request to the [ text ] service` on a free-text query | Wrong service name | Use `"service": "full_text"` for keyword search; `"service": "text"` is for structured attribute filters |
| `HTTP 400` with cryptic schema message | Bad operator/value shape | Check the AttributeQuery Operators table; `range` needs the `{from,to,include_lower,include_upper}` dict |
| Empty `result_set` | Filters too strict | Relax filters one at a time; verify attribute names via the schema endpoint |
| `HTTP 404` on `entries(entry_ids: ["XYZW"])` | The entry doesn't exist | RCSB returns `null` rather than 404 inside the GraphQL response — check each `data.entries[i]` for null |
| `HTTP 429 Too Many Requests` | Burst pace | Add `time.sleep(0.3)` between requests; exponential backoff on 429 |
| `HTTP 500` from search | Server-side glitch | Retry after 5–10 s; check `status.rcsb.org` |
| Downloaded `.pdb` file truncated | >99,999 atoms (legacy format limit) | Download `.cif` instead |
| GraphQL response has `errors` array | Field name typo or wrong root | Read the error message; the API is strict about field names — check the schema browser at <https://data.rcsb.org/index.html#graphql-api> |

## Related Skills

- **alphafold-database-access** — AI-predicted structures; use when no experimental structure exists
- **uniprot-protein-database** — protein annotations, sequences, ID mapping (UniProt accession needed for AlphaFold)
- **biopython-molecular-biology** — parse downloaded PDB/mmCIF files, extract coordinates, compute distances
- **autodock-vina-docking** — downstream molecular docking using PDB structures as receptors
- **rdkit-cheminformatics** — analyze ligands extracted from PDB complexes

## References

- [RCSB PDB](https://www.rcsb.org) — main portal and web search
- [Search API v2 docs](https://search.rcsb.org/) — full JSON-payload reference and Swagger
- [Data API GraphQL browser](https://data.rcsb.org/index.html#graphql-api) — schema explorer
- [Search API attribute schema](https://search.rcsb.org/rcsbsearch/v2/metadata/schema) — JSON of every searchable attribute
- [RCSB PDB Web APIs overview](https://www.rcsb.org/docs/programmatic-access/web-apis-overview) — index of all programmatic surfaces
- For SDK-based usage, see the `rcsb-api` PyPI package; this SKILL.md uses the underlying REST/GraphQL directly so no SDK install is needed.
