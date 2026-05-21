---
name: "metabolomics-workbench-database"
description: "Query Metabolomics Workbench REST API (4,200+ NIH studies) for metabolite ID, study discovery, RefMet standardization, m/z precursor searches, and gene/protein annotations. Quirks: compound input_item rejects `name` (use pubchem_cid/kegg_id/inchi_key/etc.); free-text → compound is a two-step refmet/match→refmet/name flow; moverz endpoint returns TSV text, not JSON. Use hmdb-database for local XML; pubchem-compound-search for general compound lookup."
license: "CC-BY-4.0"
---

# Metabolomics Workbench Database — REST API Access

## Overview

The Metabolomics Workbench (MW) REST API at `https://www.metabolomicsworkbench.org/rest/` exposes 4,200+ metabolomics studies hosted at UCSD under NIH Common Fund sponsorship. URL pattern is `/{context}/{input_item}/{input_value}/{output_item}/{format}`. Contexts include `compound`, `refmet`, `moverz`, `study`, `analysis`, `metabolite`, `gene`, `protein`. Notable quirks discovered live:

- `compound/name/{x}` is **rejected** — `name` is not an allowed input_item. Use `pubchem_cid`, `kegg_id`, `inchi_key`, `hmdb_id`, `regno`, `lm_id`, `formula`, `smiles`, or `abbrev`. For free-text input, go through `refmet/match/{x}` first.
- `refmet/name/{x}/all` requires the **exact** RefMet name (e.g. `Glucose`, not `D-glucose`); use `refmet/match/{x}` for fuzzy normalisation first.
- `moverz/{REFMET|LIPIDS|MB}/{mz}/{ion}/{tol}/txt` returns **TSV text** (no JSON variant).
- The `metstat/filter/...` endpoint shown in older examples returns `[]` — replace with `study/{context}/{value}/summary` (or `/metabolites`) + client-side filtering.

No authentication required.

## When to Use

- Searching metabolite records by PubChem CID, KEGG ID, InChIKey, HMDB ID, formula, or SMILES
- Discovering studies by species, disease, last_name, institute, analysis_type, or polarity
- Standardising metabolite names to RefMet nomenclature for cross-study integration
- Identifying unknown compounds from MS m/z values with adduct-aware matching (`moverz`)
- Retrieving experimental metabolite tables (analyses, abundances) from published studies
- Querying gene/protein annotations linked to metabolomics pathways
- Downloading raw mwTab files for local analysis
- For local 220K-metabolite XML parsing with NMR/MS spectra use `hmdb-database` instead
- For live 110M-compound property lookups use `pubchem-compound-search` instead

## Prerequisites

- **Python packages**: `requests`, `pandas`
- **No API key required**: publicly accessible
- **Rate limits**: MW does not enforce strict limits; add `time.sleep(0.3)` between bulk requests
- **Base URL**: `https://www.metabolomicsworkbench.org/rest`

```bash
pip install requests pandas
```

## Quick Start

```python
import requests

BASE = "https://www.metabolomicsworkbench.org/rest"

# Two-step free-text → compound (the API rejects compound/name/...)
def lookup_by_name(name):
    # 1) Normalise to RefMet name
    r = requests.get(f"{BASE}/refmet/match/{name}", timeout=30)
    r.raise_for_status()
    refmet = r.json()
    if not refmet.get("refmet_name"):
        return None
    # 2) Pull full compound record by RefMet name (or by pubchem_cid)
    r2 = requests.get(f"{BASE}/refmet/name/{refmet['refmet_name']}/all", timeout=30)
    rec = r2.json() if r2.json() else {}
    return rec if isinstance(rec, dict) else None

c = lookup_by_name("glucose")
print(f"{c['name']}: formula={c['formula']}, PubChem CID={c['pubchem_cid']}, "
      f"InChIKey={c['inchi_key']}")
# Glucose: formula=C6H12O6, PubChem CID=5793, InChIKey=WQZGKKKJIJFFOK-GASJEMHNSA-N
```

## Core API

### Module 1: Compound Queries

`compound/{input_item}/{input_value}/all/json` — `input_item` must be one of `regno`, `formula`, `inchi_key`, `lm_id`, `pubchem_cid`, `hmdb_id`, `kegg_id`, `smiles`, `abbrev`. The legacy `name` input is rejected by the server.

```python
import requests

BASE = "https://www.metabolomicsworkbench.org/rest"

# By PubChem CID
r = requests.get(f"{BASE}/compound/pubchem_cid/5793/all/json", timeout=30)
glucose = r.json()
print(f"PubChem 5793 -> {glucose['name']}, formula={glucose['formula']}, "
      f"HMDB={glucose.get('hmdb_id')}, KEGG={glucose.get('kegg_id')}")

# By KEGG ID
r = requests.get(f"{BASE}/compound/kegg_id/C00031/all/json", timeout=30)
print("KEGG C00031 ->", r.json()["name"])

# By InChIKey
r = requests.get(f"{BASE}/compound/inchi_key/WQZGKKKJIJFFOK-GASJEMHNSA-N/all/json", timeout=30)
print("InChIKey -> regno:", r.json()["regno"])
```

```python
# Compound by formula returns a paged dict (multiple matches)
import requests
BASE = "https://www.metabolomicsworkbench.org/rest"
r = requests.get(f"{BASE}/compound/formula/C6H12O6/all/json", timeout=30)
matches = r.json()
print(f"Compounds with formula C6H12O6: {len(matches)}")
for k in list(matches)[:3]:
    print(f"  regno={matches[k]['regno']}  name={matches[k]['name']}")
```

### Module 2: Study Discovery

`study/{input_item}/{input_value}/{output}` — `input_item` includes `study_id`, `study_title`, `last_name`, `institute`, `analysis_id`, `metabolite_id`, `kegg_id`, `refmet_name`. `output` includes `summary`, `metabolites`, `factors`, `data`, `available_studies`, `species`, `disease`. `summary` for `study_id` returns a dict (keyed by accession when multiple); for `last_name`/`institute` it returns a list.

```python
import requests, pandas as pd

BASE = "https://www.metabolomicsworkbench.org/rest"

# Single-study summary — `study/study_id/{id}/summary` returns a flat dict
# (keys: study_id, study_title, species, institute, analysis_type, ...)
r = requests.get(f"{BASE}/study/study_id/ST000001/summary", timeout=30)
s = r.json()
print(f"{s['study_id']}: {s['study_title'][:60]}")
print(f"  Species : {s.get('species')}  Institute: {s.get('institute')}")
print(f"  Submit  : {s.get('submission_date')}")
```

```python
# Studies that detected a metabolite — `study/refmet_name/{x}/summary` returns
# a thin index of (refmet_name, kegg_id, study_id) rows. Chain study_id → full summary
# to get title and species.
import requests, pandas as pd
BASE = "https://www.metabolomicsworkbench.org/rest"
r = requests.get(f"{BASE}/study/refmet_name/Glucose/summary", timeout=60)
d = r.json()
rows = list(d.values()) if isinstance(d, dict) else d
print(f"Studies referencing 'Glucose': {len(rows)}")
print(pd.DataFrame(rows).head(5).to_string(index=False))
# refmet_name kegg_id  study_id
#     Glucose  C00031  ST000001
#     Glucose  C00031  ST000002
#     ...
```

### Module 3: RefMet Standardisation

`refmet/match/{user_text}` is a fuzzy normaliser — returns the standard RefMet record (no `pubchem_cid`/`kegg_id` though). `refmet/name/{exact_refmet_name}/all` returns the full record including IDs. Use them as a two-step pipeline.

```python
import requests

BASE = "https://www.metabolomicsworkbench.org/rest"

def normalise_to_refmet(user_text):
    r = requests.get(f"{BASE}/refmet/match/{user_text}", timeout=30)
    r.raise_for_status()
    m = r.json()
    if not m or not m.get("refmet_name"):
        return None
    return m["refmet_name"]

def refmet_full(refmet_name):
    r = requests.get(f"{BASE}/refmet/name/{refmet_name}/all", timeout=30)
    r.raise_for_status()
    rec = r.json()
    return rec if isinstance(rec, dict) and rec else None

name = normalise_to_refmet("alpha-D-glucose")  # -> 'Glucose'
print(f"Normalised: {name}")
rec = refmet_full(name)
print(f"  PubChem CID : {rec['pubchem_cid']}")
print(f"  InChIKey    : {rec['inchi_key']}")
print(f"  Super class : {rec['super_class']} / {rec['main_class']} / {rec['sub_class']}")
```

### Module 4: Study Filtering (replaces broken `metstat`)

The older `metstat/filter/...` endpoint returns `[]`. Use the study context endpoints with client-side filtering instead.

```python
import requests, pandas as pd

BASE = "https://www.metabolomicsworkbench.org/rest"

def study_ids_for_metabolite(refmet_name):
    """Return the study_id list that report a given RefMet name."""
    r = requests.get(f"{BASE}/study/refmet_name/{refmet_name}/summary", timeout=60)
    r.raise_for_status()
    d = r.json()
    rows = list(d.values()) if isinstance(d, dict) else d
    return sorted({row["study_id"] for row in rows if row.get("study_id")})

def study_summary(study_id):
    """Pull full summary (title, species, institute, dates) for one study_id.
    Response is a flat dict with keys study_id/study_title/species/institute/..."""
    return requests.get(f"{BASE}/study/study_id/{study_id}/summary", timeout=30).json()

# Find glucose studies, then enrich the first few
ids = study_ids_for_metabolite("Glucose")
print(f"Studies referencing 'Glucose': {len(ids)}")
rows = [study_summary(sid) for sid in ids[:5]]
df = pd.DataFrame(rows)
print(df[["study_id", "study_title", "species"]].head().to_string(index=False))
```

### Module 5: m/z Precursor Search (`moverz`)

`moverz/{REFMET|LIPIDS|MB}/{mz}/{ion}/{tolerance}/txt` returns **tab-separated text** (not JSON). The first DB selector (`REFMET`, `LIPIDS`, or `MB`) is required — `mz` as the first segment is rejected.

```python
import requests, io, pandas as pd

BASE = "https://www.metabolomicsworkbench.org/rest"

def moverz_search(db, mz, ion, tolerance=0.005):
    """Search precursor m/z in REFMET / LIPIDS / MB and return a DataFrame.
    Response is TSV text — no JSON variant."""
    assert db in {"REFMET", "LIPIDS", "MB"}
    r = requests.get(f"{BASE}/moverz/{db}/{mz}/{ion}/{tolerance}/txt", timeout=30)
    r.raise_for_status()
    return pd.read_csv(io.StringIO(r.text), sep="\t")

df = moverz_search("REFMET", 180.063, "M+H", 0.005)
print(f"Candidates at m/z 180.063 [M+H]+ (REFMET): {len(df)}")
print(df.head(5).to_string(index=False))
```

```python
# Same query against the LIPIDS database
import requests, io, pandas as pd
BASE = "https://www.metabolomicsworkbench.org/rest"
r = requests.get(f"{BASE}/moverz/LIPIDS/760.585/M+H/0.01/txt", timeout=30)
df_lipids = pd.read_csv(io.StringIO(r.text), sep="\t")
print(f"Lipid candidates at m/z 760.585: {len(df_lipids)}")
print(df_lipids.head(3).to_string(index=False))
```

### Module 6: Genes and Proteins

```python
import requests

BASE = "https://www.metabolomicsworkbench.org/rest"

r = requests.get(f"{BASE}/gene/gene_symbol/HMGCR/all", timeout=30)
g = r.json()
print(f"{g['gene_symbol']} -> MGP: {g.get('mgp_id')}  ({g.get('gene_name', '')[:60]})")

# Protein by UniProt accession
r2 = requests.get(f"{BASE}/protein/uniprot_id/P04035/all", timeout=30)
p = r2.json()
print(f"UniProt P04035: {p.get('protein_name', '')[:60]}  organism={p.get('organism')}")
```

## Key Concepts

### Allowed `input_item` Values per Context

| Context | Valid input_item | Notes |
|---------|------------------|-------|
| `compound` | `regno`, `formula`, `inchi_key`, `lm_id`, `pubchem_cid`, `hmdb_id`, `kegg_id`, `smiles`, `abbrev` | `name` is **rejected** — go via `refmet/match` first |
| `refmet` | `match`, `name`, `formula`, `exactmass`, `inchi_key`, `pubchem_cid`, `regno` | `match` is fuzzy; `name` requires the canonical RefMet name |
| `study` | `study_id`, `study_title`, `last_name`, `institute`, `analysis_id`, `metabolite_id`, `kegg_id`, `refmet_name` | `summary` for `study_id` is a dict keyed by accession; for `last_name`/`institute` it's a list |
| `moverz` | (path) `REFMET` / `LIPIDS` / `MB` | First segment is the DB, not `mz` |
| `gene` | `gene_id`, `gene_symbol`, `gene_name`, `mgp_id` | Returns a dict |
| `protein` | `mgp_id`, `gene_id`, `uniprot_id`, `gene_symbol` | Returns a dict |

### Output Type Conventions

- `output=summary` returns a **dict** when the input identifier is unique (e.g. `study_id`), a **list** when it isn't (e.g. `last_name`).
- Appending `/json` to `study/.../summary` flips the response to TSV. Omit the format suffix — JSON is the default.
- `moverz` only emits `/txt` (TSV); there is no JSON variant.

### `refmet/match` vs `refmet/name`

- `refmet/match/{user_text}` — fuzzy. Always returns a single dict with `refmet_name`, `formula`, `exactmass`, classification. Does **not** include `pubchem_cid`/`inchi_key`.
- `refmet/name/{exact_refmet_name}/all` — requires the canonical RefMet name. Returns the full record including IDs. Returns an empty list if the name isn't canonical.

## Common Workflows

### Workflow 1: Free-Text → Full Compound Record

```python
import requests, pandas as pd

BASE = "https://www.metabolomicsworkbench.org/rest"

def resolve_to_compound(user_text):
    # 1) Normalise via refmet/match
    rm = requests.get(f"{BASE}/refmet/match/{user_text}", timeout=30).json()
    if not rm.get("refmet_name"):
        return None
    name = rm["refmet_name"]
    # 2) Fetch full RefMet record (includes pubchem_cid / inchi_key)
    full = requests.get(f"{BASE}/refmet/name/{name}/all", timeout=30).json()
    if not isinstance(full, dict) or not full:
        return None
    # 3) Optionally pull the matching compound record via PubChem CID
    cid = full.get("pubchem_cid")
    compound = None
    if cid:
        compound = requests.get(f"{BASE}/compound/pubchem_cid/{cid}/all/json",
                                timeout=30).json()
    return {
        "input": user_text,
        "refmet_name": name,
        "formula": full.get("formula"),
        "pubchem_cid": cid,
        "hmdb_id": compound.get("hmdb_id") if compound else None,
        "kegg_id": compound.get("kegg_id") if compound else None,
        "inchi_key": full.get("inchi_key"),
    }

queries = ["glucose", "alpha-D-glucose", "L-tyrosine", "cholesterol"]
df = pd.DataFrame([resolve_to_compound(q) for q in queries])
print(df.to_string(index=False))
df.to_csv("name_resolution.csv", index=False)
```

### Workflow 2: Annotate MS Hit List

**Goal**: Take a list of measured m/z values and assign RefMet candidate compounds.

```python
import requests, io, pandas as pd, time

BASE = "https://www.metabolomicsworkbench.org/rest"

def annotate_peaks(mz_values, ion="M+H", tolerance=0.005):
    out = []
    for mz in mz_values:
        r = requests.get(f"{BASE}/moverz/REFMET/{mz}/{ion}/{tolerance}/txt", timeout=30)
        if r.status_code != 200 or not r.text.strip():
            time.sleep(0.3); continue
        df = pd.read_csv(io.StringIO(r.text), sep="\t")
        for _, row in df.iterrows():
            out.append({
                "query_mz": mz,
                "matched_mz": row["Matched m/z"],
                "delta": row["Delta"],
                "name": row["Name"],
                "formula": row["Formula"],
                "ion": row["Ion"],
                "main_class": row.get("Main class"),
            })
        time.sleep(0.3)
    return pd.DataFrame(out)

peaks = [180.063, 166.086, 90.055]   # glucose, phenylalanine, alanine
df_ann = annotate_peaks(peaks)
print(df_ann.head(10).to_string(index=False))
df_ann.to_csv("ms_annotations.csv", index=False)
```

### Workflow 3: Find Studies Detecting a Metabolite

```python
import requests, pandas as pd

BASE = "https://www.metabolomicsworkbench.org/rest"

def studies_with(refmet_name, enrich_n=20):
    """Return a DataFrame: study_id rows that report the metabolite, enriched with
    title + species for the first `enrich_n` IDs (via study/study_id/.../summary)."""
    r = requests.get(f"{BASE}/study/refmet_name/{refmet_name}/summary", timeout=60)
    r.raise_for_status()
    d = r.json()
    rows = list(d.values()) if isinstance(d, dict) else d
    ids = sorted({row["study_id"] for row in rows if row.get("study_id")})
    enriched = []
    for sid in ids[:enrich_n]:
        enriched.append(requests.get(
            f"{BASE}/study/study_id/{sid}/summary", timeout=30).json())
    return pd.DataFrame(enriched)

df = studies_with("Glucose", enrich_n=20)
print(f"Glucose-detecting studies (first 20 enriched): {len(df)}")
print(df.groupby("species").size().sort_values(ascending=False).head(8))
```

## Key Parameters

| Parameter | Endpoint | Default | Range / Options | Effect |
|-----------|----------|---------|-----------------|--------|
| `context` | path | required | `compound`, `refmet`, `moverz`, `study`, `analysis`, `metabolite`, `gene`, `protein` | API context selector |
| `input_item` | path | required | depends on context (see "Allowed `input_item` Values per Context") | Identifier type |
| `input_value` | path | required | string | The actual identifier or value |
| `output_item` | path | `all` | `all`, `summary`, `metabolites`, `factors`, `data`, etc. | What aspect to return |
| `format` | path | (varies) | `json`, `txt` | `moverz` only emits `txt`; do NOT append `/json` to `study/.../summary` |
| `mz` / `ion` / `tolerance` | `moverz` path | required | float / `M+H`, `M-H`, `M+Na`, `M+K`, etc. / float | Mass tolerance in Da |

## Best Practices

1. **Use `refmet/match` first for free-text input.** `compound/name/...` is rejected by the server (`name` is not an allowed `input_item`).
2. **`moverz` is TSV-only.** Parse with `pd.read_csv(io.StringIO(r.text), sep="\t")` — never call `.json()` on the response.
3. **Don't append `/json` to `study/.../summary`.** The default is JSON; the suffix flips the response to TSV.
4. **`refmet/name/{x}/all` needs the canonical RefMet name.** If you have user text, run it through `refmet/match` first.
5. **Compound results paged by formula come keyed `'1','2',...`** — iterate `dict.values()` or pass to `pd.DataFrame.from_dict(orient="index")`.
6. **Always `time.sleep(0.3)` in batch loops** — no rate limit is published but the server is shared.

## Common Recipes

### Recipe: Cross-Database ID Mapping (PubChem ↔ KEGG ↔ HMDB)

```python
import requests, pandas as pd

BASE = "https://www.metabolomicsworkbench.org/rest"

def cross_refs(refmet_name):
    rm = requests.get(f"{BASE}/refmet/name/{refmet_name}/all", timeout=30).json()
    if not isinstance(rm, dict) or not rm:
        return None
    cid = rm.get("pubchem_cid")
    if not cid:
        return {"refmet": refmet_name, "pubchem_cid": None}
    c = requests.get(f"{BASE}/compound/pubchem_cid/{cid}/all/json", timeout=30).json()
    return {"refmet": refmet_name,
            "pubchem_cid": cid,
            "kegg_id": c.get("kegg_id"),
            "hmdb_id": c.get("hmdb_id"),
            "inchi_key": rm.get("inchi_key")}

df = pd.DataFrame([cross_refs(n) for n in ["Glucose", "L-Tyrosine", "Cholesterol"]])
print(df.to_string(index=False))
```

### Recipe: Pull a Study's Metabolite Table

```python
import requests, pandas as pd

BASE = "https://www.metabolomicsworkbench.org/rest"
r = requests.get(f"{BASE}/study/study_id/ST000001/metabolites", timeout=60)
r.raise_for_status()
rows = list(r.json().values())
df = pd.DataFrame(rows)
print(f"ST000001 metabolites: {len(df)}")
print(df[["analysis_id", "analysis_summary", "metabolite_name", "refmet_name"]].head(5).to_string(index=False))
```

### Recipe: Gene → Metabolomics Pathways

```python
import requests

BASE = "https://www.metabolomicsworkbench.org/rest"
g = requests.get(f"{BASE}/gene/gene_symbol/HMGCR/all", timeout=30).json()
print({k: g.get(k) for k in ["gene_symbol", "gene_id", "mgp_id",
                              "gene_name", "gene_synonyms"]})
```

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| `"This input item (name) is not allowed..."` | `compound/name/...` is rejected | Use one of the allowed `input_item` values (`pubchem_cid`, `kegg_id`, `inchi_key`, `hmdb_id`, etc.); for free text, go through `refmet/match/{x}` first |
| `JSONDecodeError` on `moverz` response | `moverz` returns TSV text, not JSON | Parse with `pd.read_csv(io.StringIO(r.text), sep="\t")` |
| Empty list from `refmet/name/{x}/all` | Need the canonical RefMet name (case-sensitive) | Normalise via `refmet/match/{user_text}` first, then plug `refmet_name` into `refmet/name/.../all` |
| `metstat/filter/...` returns `[]` | Endpoint syntax is non-functional | Use `study/{refmet_name|last_name|institute|...}/{value}/summary` and filter client-side |
| `study/.../summary` returns TSV instead of JSON | The `/json` suffix flips to TSV | Drop the trailing `/json` — JSON is the default |
| Compound query by formula returns a dict, not a list | Server pages multiple matches as `{'1': {...}, '2': {...}}` | Iterate `dict.values()` (or `pd.DataFrame.from_dict(d, orient='index')`) |
| `refmet/match` response lacks `pubchem_cid` | `match` returns the lightweight record | Use `refmet/name/{refmet_name}/all` for the full record |

## Related Skills

- `hmdb-database` — Local HMDB XML (220K metabolites, NMR/MS spectra, disease links) for offline queries
- `pubchem-compound-search` — General compound property lookups (110M+ compounds) via PubChemPy
- `kegg-database` — Pathway and orthology data complementary to MW's study/metabolite hits
- `chembl-database-bioactivity` — Bioactivity data for the same compounds

## References

- [Metabolomics Workbench home](https://www.metabolomicsworkbench.org/)
- [REST API documentation (PDF)](https://www.metabolomicsworkbench.org/tools/MWRestAPIv1.0.pdf)
- [RefMet nomenclature](https://www.metabolomicsworkbench.org/databases/refmet/index.php)
- Sud M et al. "Metabolomics Workbench: An international repository for metabolomics data and metadata." *Nucleic Acids Research* 44(D1): D463–D470 (2016). https://doi.org/10.1093/nar/gkv1042
