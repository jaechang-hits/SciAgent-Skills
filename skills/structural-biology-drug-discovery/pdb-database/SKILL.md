---
name: "pdb-database"
description: "Query RCSB PDB (200K+ structures) via rcsb-api SDK. Text/attribute/sequence/3D similarity search; metadata via GraphQL; download PDB/mmCIF. For AlphaFold predictions use alphafold-database-access."
license: "BSD-3-Clause"
---

# PDB Database

## Overview

RCSB PDB is the worldwide repository for 3D structural data of biological macromolecules with 200,000+ experimentally determined structures. The `rcsb-api` Python SDK provides unified access to Search API (find PDB IDs by text, attributes, sequence, or structure similarity) and Data API (retrieve metadata and coordinates). Use this skill for programmatic structural biology queries, drug target analysis, and protein family comparisons.

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

- **Python packages**: `rcsb-api` (unified Search + Data SDK), optionally `requests` for file downloads, `biopython` for coordinate parsing
- **No API key required**: RCSB PDB is freely accessible
- **Rate limits**: No published hard limit; implement exponential backoff on HTTP 429. Recommended: 2-5 requests/second for batch operations

```bash
pip install rcsb-api requests
# Optional: pip install biopython  # for PDB/mmCIF coordinate parsing
```

## Quick Start

Typical search-then-fetch pattern:

```python
from rcsbapi.search import TextQuery, AttributeQuery
from rcsbapi.search.attrs import rcsb_entry_info, rcsb_entity_source_organism
from rcsbapi.data import fetch, Schema

# 1. Search: high-resolution human kinases
query = (
    TextQuery("kinase") &
    AttributeQuery(
        attribute=rcsb_entity_source_organism.scientific_name,
        operator="exact_match", value="Homo sapiens"
    ) &
    AttributeQuery(
        attribute=rcsb_entry_info.resolution_combined,
        operator="less", value=2.0
    )
)
pdb_ids = list(query())
print(f"Found {len(pdb_ids)} structures")  # e.g., Found 1523 structures

# 2. Fetch metadata for first hit
data = fetch(pdb_ids[0], schema=Schema.ENTRY)
print(data["struct"]["title"])
print(f"Resolution: {data['rcsb_entry_info']['resolution_combined']} A")
```

## Core API

### Module 1: Text and Attribute Search

**Text search** finds entries by keyword across all indexed fields.

```python
from rcsbapi.search import TextQuery

query = TextQuery("hemoglobin")
results = list(query())
print(f"Found {len(results)} structures")  # Found ~750 structures
```

**Attribute search** queries specific properties with typed operators.

```python
from rcsbapi.search import AttributeQuery
from rcsbapi.search.attrs import rcsb_entity_source_organism, exptl, rcsb_entry_info

# Human proteins
q_human = AttributeQuery(
    attribute=rcsb_entity_source_organism.scientific_name,
    operator="exact_match", value="Homo sapiens"
)

# X-ray only
q_xray = AttributeQuery(
    attribute=exptl.method,
    operator="exact_match", value="X-RAY DIFFRACTION"
)

# Resolution range
q_res = AttributeQuery(
    attribute=rcsb_entry_info.resolution_combined,
    operator="range", value=(1.5, 2.5)
)

results = list(q_human & q_xray & q_res)
print(f"Human X-ray 1.5-2.5A: {len(results)} structures")
```

### Module 2: Sequence Similarity Search

Find structures with similar sequences using MMseqs2. Supports protein, DNA, and RNA.

```python
from rcsbapi.search import SequenceQuery

# Protein sequence search (KRAS)
query = SequenceQuery(
    value="MTEYKLVVVGAGGVGKSALTIQLIQNHFVDEYDPTIEDSYRKQVVIDGETCLLDILDTAG"
          "QEEYSAMRDQYMRTGEGFLCVFAINNTKSFEDIHHYREQIKRVKDSEDVPMVLVGNKCDL"
          "PSRTVDTKQAQDLARSYGIPFIETSAKTRQGVDDAFYTLVREIRKHKEKMSK",
    evalue_cutoff=0.1,
    identity_cutoff=0.9
)
results = list(query())
print(f"Sequence hits: {len(results)}")

# DNA sequence search
dna_query = SequenceQuery(
    value="ACGTACGTACGTACGTACGT",
    evalue_cutoff=1e-5,
    identity_cutoff=0.8,
    sequence_type="dna"  # "protein" (default), "dna", "rna"
)
```

### Module 3: Structure Similarity Search

Find structures with similar 3D geometry using BioZernike descriptors.

```python
from rcsbapi.search import StructSimilarityQuery

# Search by full entry
query = StructSimilarityQuery(
    structure_search_type="entry",
    entry_id="4HHB"
)
results = list(query())
print(f"Structurally similar to 4HHB: {len(results)}")

# Search by specific chain
chain_query = StructSimilarityQuery(
    structure_search_type="chain",
    entry_id="4HHB",
    chain_id="A"
)

# Search by biological assembly
assembly_query = StructSimilarityQuery(
    structure_search_type="assembly",
    entry_id="4HHB",
    assembly_id="1"
)
```

### Module 4: Data Retrieval (Schema and GraphQL)

Fetch structured metadata for known PDB IDs using Schema objects or custom GraphQL.

```python
from rcsbapi.data import fetch, Schema

# Entry-level data
entry = fetch("4HHB", schema=Schema.ENTRY)
print(entry["struct"]["title"])
print(entry["exptl"][0]["method"])  # X-RAY DIFFRACTION
print(entry["rcsb_entry_info"]["resolution_combined"])  # 1.74

# Polymer entity data (append _N for entity number)
entity = fetch("4HHB_1", schema=Schema.POLYMER_ENTITY)
print(entity["entity_poly"]["pdbx_seq_one_letter_code"][:50])
print(entity["rcsb_entity_source_organism"][0]["scientific_name"])
```

**Custom GraphQL** for flexible cross-level queries in a single request:

```python
from rcsbapi.data import fetch

gql = """{
  entry(entry_id: "4HHB") {
    struct { title }
    exptl { method }
    rcsb_entry_info { resolution_combined deposited_atom_count polymer_entity_count }
    rcsb_accession_info { deposit_date initial_release_date }
  }
}"""
data = fetch(query_type="graphql", query=gql)
info = data["data"]["entry"]
print(f"Title: {info['struct']['title']}")
print(f"Atoms: {info['rcsb_entry_info']['deposited_atom_count']}")
```

### Module 5: File Download

Download coordinate files from RCSB file servers.

```python
import requests

def download_structure(pdb_id, fmt="cif", output_dir="."):
    """Download PDB/mmCIF/FASTA. URLs: .pdb, .cif, /fasta/entry/{ID}, .pdb1 (assembly)."""
    url = f"https://files.rcsb.org/download/{pdb_id}.{fmt}"
    resp = requests.get(url)
    if resp.status_code == 200:
        path = f"{output_dir}/{pdb_id}.{fmt}"
        with open(path, "w") as f:
            f.write(resp.text)
        print(f"Downloaded {path} ({len(resp.text)} bytes)")
        return path
    print(f"Error {resp.status_code} for {pdb_id}")
    return None

# Download both formats
download_structure("4HHB", fmt="pdb")
download_structure("4HHB", fmt="cif")
```

### Module 6: Query Composition

Combine queries with Python bitwise operators (`&` AND, `|` OR, `~` NOT).

```python
from rcsbapi.search import TextQuery, AttributeQuery
from rcsbapi.search.attrs import rcsb_entry_info, rcsb_entity_source_organism, refine
import datetime

# AND: high-resolution human structures
q_and = (
    AttributeQuery(attribute=rcsb_entity_source_organism.scientific_name,
                    operator="exact_match", value="Homo sapiens") &
    AttributeQuery(attribute=rcsb_entry_info.resolution_combined,
                    operator="less", value=2.0)
)

# OR: human or mouse
q_or = (
    AttributeQuery(attribute=rcsb_entity_source_organism.scientific_name,
                    operator="exact_match", value="Homo sapiens") |
    AttributeQuery(attribute=rcsb_entity_source_organism.scientific_name,
                    operator="exact_match", value="Mus musculus")
)

# NOT: exclude low resolution
q_not = TextQuery("protein") & ~AttributeQuery(
    attribute=rcsb_entry_info.resolution_combined, operator="greater", value=3.0
)

# Complex: recent high-quality structures
one_month_ago = (datetime.date.today() - datetime.timedelta(days=30)).isoformat()
from rcsbapi.search.attrs import rcsb_accession_info
q_complex = (
    AttributeQuery(attribute=rcsb_entry_info.resolution_combined,
                    operator="less", value=2.0) &
    AttributeQuery(attribute=refine.ls_R_factor_R_free,
                    operator="less", value=0.25) &
    AttributeQuery(attribute=rcsb_accession_info.initial_release_date,
                    operator="range", value=(one_month_ago, datetime.date.today().isoformat()))
)
print(f"Recent high-quality: {len(list(q_complex()))} structures")
```

### Module 7: Batch Operations with Rate Limiting

Fetch data for multiple structures with exponential backoff.

```python
import time
from rcsbapi.search import TextQuery
from rcsbapi.data import fetch, Schema

def batch_fetch(pdb_ids, schema=Schema.ENTRY, delay=0.5, max_retries=3):
    """Fetch metadata for multiple PDB IDs with rate-limit handling."""
    results = {}
    for i, pdb_id in enumerate(pdb_ids):
        wait = delay
        for attempt in range(max_retries):
            try:
                results[pdb_id] = fetch(pdb_id, schema=schema)
                break
            except Exception as e:
                if "429" in str(e):
                    print(f"Rate limited on {pdb_id}, waiting {wait}s...")
                    time.sleep(wait)
                    wait *= 2
                else:
                    print(f"Error {pdb_id}: {e}")
                    break
        if (i + 1) % 10 == 0:
            print(f"Fetched {i + 1}/{len(pdb_ids)}")
        time.sleep(delay)
    return results

# Usage
query = TextQuery("insulin")
pdb_ids = list(query())[:20]  # First 20 hits
data = batch_fetch(pdb_ids, delay=0.3)
for pid, d in list(data.items())[:3]:
    print(f"{pid}: {d['struct']['title']}")
```

## Key Concepts

### PDB Data Hierarchy

PDB organizes data in a strict hierarchy. Use the correct Schema for each level:

| Level | ID Format | Schema | Content |
|-------|-----------|--------|---------|
| Entry | `4HHB` | `Schema.ENTRY` | Experiment, resolution, deposition |
| Polymer Entity | `4HHB_1` | `Schema.POLYMER_ENTITY` | Sequence, organism, molecular weight |
| Nonpolymer Entity | `4HHB_1` | `Schema.NONPOLYMER_ENTITY` | Ligands, cofactors, ions |
| Branched Entity | `4HHB_1` | `Schema.BRANCHED_ENTITY` | Oligosaccharides |
| Assembly | `4HHB/1` | `Schema.ASSEMBLY` | Biological unit, stoichiometry |
| Chain Instance | `4HHB.A` | `Schema.POLYMER_ENTITY_INSTANCE` | Individual chain coordinates |
| Chemical Component | `ATP` | `Schema.CHEM_COMP` | Small molecule metadata |

### Common Data Fields

**Entry**: `struct.title`, `exptl[].method`, `rcsb_entry_info.resolution_combined`, `rcsb_entry_info.deposited_atom_count`, `rcsb_accession_info.deposit_date`, `rcsb_accession_info.initial_release_date`

**Polymer entity**: `entity_poly.pdbx_seq_one_letter_code`, `rcsb_polymer_entity.formula_weight`, `rcsb_entity_source_organism.scientific_name`, `rcsb_entity_source_organism.ncbi_taxonomy_id`

**Assembly**: `rcsb_assembly_info.polymer_entity_count`, `rcsb_assembly_info.assembly_id`

### Search Query Types

| Query Type | Class | Use Case | Engine |
|------------|-------|----------|--------|
| Full text | `TextQuery` | Keyword search across all fields | Lucene |
| Attribute | `AttributeQuery` | Property filters (organism, resolution) | Exact match |
| Sequence | `SequenceQuery` | Sequence similarity (protein/DNA/RNA) | MMseqs2 |
| Sequence Motif | `SequenceMotifQuery` | Regex/PROSITE motif patterns | Custom |
| Structure | `StructSimilarityQuery` | 3D geometry similarity | BioZernike |
| Structure Motif | `StructMotifQuery` | 3D residue arrangement patterns | InvertedIndex |
| Chemical | `ChemSimilarityQuery` | Ligand similarity by SMILES/InChI | Fingerprint |

### AttributeQuery Operators

| Operator | Type | Example Value |
|----------|------|---------------|
| `exact_match` | String | `"Homo sapiens"` |
| `contains_words` | String | `"kinase inhibitor"` |
| `contains_phrase` | String | `"tyrosine kinase"` |
| `equals` | Numeric | `2.0` |
| `greater` / `less` | Numeric | `3.0` |
| `greater_or_equal` / `less_or_equal` | Numeric | `1.5` |
| `range` | Numeric/Date | `(1.5, 2.5)` or `("2024-01-01", "2024-12-31")` |
| `exists` | Any | `None` (field has value) |
| `in` | List | `["X-RAY DIFFRACTION", "ELECTRON MICROSCOPY"]` |

### File Format Comparison

| Format | Extension | Best For | Notes |
|--------|-----------|----------|-------|
| PDB | `.pdb` | Legacy tools, small structures | 99,999 atom limit, fixed-width |
| mmCIF | `.cif` | Modern standard, large structures | No atom limit, key-value pairs |
| BinaryCIF | `.bcif` | Web viewers, bandwidth-limited | Compressed binary, via ModelServer |

### Return Types

Control what search results return via `ReturnType`:

```python
from rcsbapi.search import TextQuery, ReturnType

query = TextQuery("hemoglobin")
# Default: PDB IDs
ids = list(query())  # ['4HHB', '1A3N', ...]
# With scores
scored = list(query(return_type=ReturnType.ENTRY, return_scores=True))
# [{'identifier': '4HHB', 'score': 0.95}, ...]
# Polymer entities
entities = list(query(return_type=ReturnType.POLYMER_ENTITY))
# ['4HHB_1', '4HHB_2', ...]
```

## Common Workflows

### Workflow 1: Drug Target Structure Search

**Goal**: Find high-resolution structures of a drug target with bound ligands.

```python
from rcsbapi.search import TextQuery, AttributeQuery
from rcsbapi.search.attrs import rcsb_entry_info, rcsb_entity_source_organism
from rcsbapi.data import fetch, Schema
import time

# Search: human EGFR, high resolution
query = (
    TextQuery("EGFR epidermal growth factor receptor") &
    AttributeQuery(attribute=rcsb_entity_source_organism.scientific_name,
                    operator="exact_match", value="Homo sapiens") &
    AttributeQuery(attribute=rcsb_entry_info.resolution_combined,
                    operator="less", value=2.5)
)
pdb_ids = list(query())
print(f"EGFR structures: {len(pdb_ids)}")

# Filter for structures with bound ligands
targets = []
for pid in pdb_ids[:10]:
    data = fetch(pid, schema=Schema.ENTRY)
    n_lig = data.get("rcsb_entry_info", {}).get("nonpolymer_entity_count", 0)
    if n_lig and n_lig > 0:
        targets.append({"pdb_id": pid, "title": data["struct"]["title"],
                         "resolution": data["rcsb_entry_info"]["resolution_combined"],
                         "ligands": n_lig})
    time.sleep(0.3)

for t in sorted(targets, key=lambda x: x["resolution"]):
    print(f"{t['pdb_id']}: {t['resolution']}A, {t['ligands']} ligands - {t['title'][:60]}")
```

### Workflow 2: Protein Family Structural Comparison

**Goal**: Compare structures across a protein family by sequence similarity.

```python
from rcsbapi.search import SequenceQuery
from rcsbapi.data import fetch, Schema
import time

# Find structures similar to KRAS
query = SequenceQuery(
    value="MTEYKLVVVGAGGVGKSALTIQLIQNHFVDEYDPTIEDSYRKQVVIDGETCLLDILDTAG",
    evalue_cutoff=1e-5, identity_cutoff=0.5
)
hits = list(query())
print(f"Family members: {len(hits)}")

# Collect metadata with rate limiting
family = []
for pid in hits[:15]:
    try:
        d = fetch(pid, schema=Schema.ENTRY)
        family.append({"pdb_id": pid, "title": d["struct"]["title"],
                        "resolution": d.get("rcsb_entry_info", {}).get("resolution_combined"),
                        "method": d["exptl"][0]["method"]})
    except Exception as e:
        print(f"Skip {pid}: {e}")
    time.sleep(0.3)

for f in sorted(family, key=lambda x: x["resolution"] or 99):
    res = f"{f['resolution']:.1f}" if f["resolution"] else "N/A"
    print(f"{f['pdb_id']}: {res}A {f['method']:<20} {f['title'][:50]}")
```

### Workflow 3: Structure Download and Coordinate Parsing

**Goal**: Download a structure and extract chain-level information with BioPython.

```python
import requests
from Bio.PDB import PDBParser, MMCIFParser

# Download mmCIF
pdb_id = "4HHB"
url = f"https://files.rcsb.org/download/{pdb_id}.cif"
resp = requests.get(url)
with open(f"{pdb_id}.cif", "w") as f:
    f.write(resp.text)

# Parse and analyze
parser = MMCIFParser(QUIET=True)
structure = parser.get_structure(pdb_id, f"{pdb_id}.cif")

for model in structure:
    for chain in model:
        residues = [r for r in chain if r.id[0] == " "]  # standard residues
        atoms = sum(len(list(r.get_atoms())) for r in residues)
        print(f"Chain {chain.id}: {len(residues)} residues, {atoms} atoms")
# Chain A: 141 residues, 1070 atoms
# Chain B: 146 residues, 1123 atoms
# ...
```

## Key Parameters

| Parameter | Function/Endpoint | Default | Range / Options | Effect |
|-----------|-------------------|---------|-----------------|--------|
| `evalue_cutoff` | `SequenceQuery` | `0.1` | `1e-10` to `10` | E-value threshold for sequence hits |
| `identity_cutoff` | `SequenceQuery` | `0.9` | `0.0`-`1.0` | Minimum sequence identity fraction |
| `sequence_type` | `SequenceQuery` | `"protein"` | `"protein"`, `"dna"`, `"rna"` | Query sequence type |
| `operator` | `AttributeQuery` | (required) | See Operators table | Comparison type for attribute filter |
| `structure_search_type` | `StructSimilarityQuery` | (required) | `"entry"`, `"chain"`, `"assembly"` | Granularity of structure comparison |
| `return_type` | `query()` | `ReturnType.ENTRY` | `ENTRY`, `POLYMER_ENTITY`, `ASSEMBLY`, etc. | What identifiers to return |
| `schema` | `fetch()` | (required) | `Schema.ENTRY`, `POLYMER_ENTITY`, `ASSEMBLY`, etc. | Data hierarchy level to retrieve |

## Best Practices

1. **Search then fetch**: Use Search API to get PDB IDs first, then Data API to retrieve metadata. Avoid fetching blindly.

2. **Use GraphQL for complex queries**: When you need fields from multiple hierarchy levels (entry + entity + assembly), a single GraphQL query is more efficient than multiple REST calls.

3. **Cache aggressively**: PDB data changes weekly (Wednesday releases). Cache results within a session to avoid redundant requests.

4. **Prefer mmCIF over PDB format**: PDB format has a 99,999 atom limit and is being phased out. Always use `.cif` for new work.

5. **Use typed attribute imports**: Import attributes from `rcsbapi.search.attrs` for IDE autocompletion and typo prevention:
   ```python
   from rcsbapi.search.attrs import rcsb_entry_info
   # Better than raw string: "rcsb_entry_info.resolution_combined"
   ```

6. **Inspect query JSON for debugging**: Call `query.to_dict()` to see the JSON payload sent to the API.

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| `ModuleNotFoundError: rcsbapi` | Package not installed | `pip install rcsb-api` (not `rcsbsearchapi`, which is deprecated) |
| HTTP 404 on fetch | PDB ID obsolete or invalid | Check ID at rcsb.org; use `rcsb_accession_info.status_code` to find superseding entry |
| HTTP 429 Too Many Requests | Rate limit exceeded | Add `time.sleep(0.5)` between requests; use exponential backoff (see Module 7) |
| HTTP 500 Internal Server Error | Temporary server issue | Retry after 5-10s delay; check status.rcsb.org |
| Empty search results | Query too restrictive or attribute name wrong | Relax filters; verify attribute paths via `rcsbapi.search.attrs` |
| `KeyError` on fetch result | Field not present for this entry | Use `.get()` with default: `data.get("rcsb_entry_info", {}).get("resolution_combined")` |
| Sequence search returns 0 hits | E-value or identity too strict | Lower `identity_cutoff` (try 0.3) and raise `evalue_cutoff` (try 1.0) |
| Downloaded PDB file truncated | Structure too large for PDB format | Download mmCIF (`.cif`) instead; PDB has 99,999 atom limit |

## Bundled Resources

**Self-contained consolidation**: Consolidates original SKILL.md (308 lines) and references/api_reference.md (618 lines, 926 total). ~150 lines of duplicated code deduplicated; effective original ~776 lines.

Content from api_reference.md consolidated into: Key Concepts (data hierarchy, fields, query types, operators, return types), Core API Modules 1-7 (search patterns, GraphQL, download helper, rate limiting, batch), Workflows (drug-target, quality filtering), Troubleshooting table.

**Omitted**: ModelServer API, VolumeServer API, Sequence Coordinates API, Alignment API (4 specialized server APIs -- rarely used programmatically; documented at data.rcsb.org). Debugging subprocess/curl tip replaced by `to_dict()` in Best Practices.

## Related Skills

- **alphafold-database-access** -- AI-predicted structures; use when no experimental structure exists
- **uniprot-protein-database** -- protein annotations, sequences, ID mapping (UniProt accession needed for AlphaFold)
- **biopython-molecular-biology** -- parse downloaded PDB/mmCIF files, extract coordinates, compute distances
- **autodock-vina-docking** -- downstream molecular docking using PDB structures as receptors
- **rdkit-cheminformatics** -- analyze ligands extracted from PDB complexes

## References

- [RCSB PDB](https://www.rcsb.org) -- main portal and web search
- [rcsb-api Python SDK documentation](https://rcsbapi.readthedocs.io/) -- official SDK docs
- [rcsb-api GitHub repository](https://github.com/rcsb/py-rcsb-api) -- source code and issues
- [RCSB PDB Web APIs overview](https://www.rcsb.org/docs/programmatic-access/web-apis-overview) -- REST, GraphQL, and search API docs
- [Data API reference](https://data.rcsb.org/redoc/index.html) -- full endpoint documentation
