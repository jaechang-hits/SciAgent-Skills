---
name: "pubchem-compound-search"
description: "Query PubChem (110M+ compounds) directly via the PUG-REST/JSON API with plain `requests` — no SDK install required. Search by name/CID/SMILES/InChIKey/formula, retrieve properties (MW, XLogP, TPSA, H-bond counts), do similarity/substructure searches with async ListKey polling, fetch synonyms, descriptions, assay summaries, and download SDF/PNG. For local cheminformatics use rdkit; for bioactivity-centric workflows use chembl-database-bioactivity."
license: "CC-BY-4.0"
---

# PubChem Compound Search

## Overview

PubChem (NCBI) is the largest freely available chemical database — 110M+ compounds, 280M+ substances, and millions of bioassay records. Its **PUG-REST JSON API** is the canonical programmatic surface, and every example here uses it directly via plain `requests`. The Python `pubchempy` wrapper is *not* required; the PUG-REST URL grammar is small enough that direct calls are more transparent, easier to retry/cache, and avoid sandbox dependency issues (the library is not in `TOOL_STATUS.md`).

The URL pattern is fixed and predictable:

```
https://pubchem.ncbi.nlm.nih.gov/rest/pug/<input>/<operation>/<output>
```

- `<input>`   = `compound/{name,cid,smiles,inchikey,formula}/<value>`
- `<operation>` = `cids`, `property/<list>`, `synonyms`, `description`, `assaysummary`, `JSON` (full record), `SDF`, `PNG`
- `<output>`  = `JSON`, `CSV`, `TXT`, `SDF`, `PNG`

For long-running operations (similarity, substructure, formula) the API returns HTTP 202 + `{"Waiting": {"ListKey": "..."}}`; poll `compound/listkey/{key}/cids/JSON` until it returns `IdentifierList`. The skill handles this pattern in Module 4.

## When to Use

- Looking up a compound by name, SMILES, InChIKey, or formula to get its PubChem CID
- Retrieving molecular properties (molecular weight, XLogP, TPSA, H-bond donor/acceptor counts, rotatable bonds, formula, IUPAC name) for one or many CIDs in a single request
- Finding structurally similar compounds via Tanimoto similarity (async ListKey poll)
- Searching for compounds containing a substructure / pharmacophore motif
- Fetching every synonym / trade name / CAS number for a CID
- Pulling assay summary tables (active/inactive screening results) for a compound
- Converting between identifier formats (name ↔ CID ↔ SMILES ↔ InChI ↔ InChIKey) in one API call
- Downloading 2D SDF or PNG structures for figures or downstream RDKit work
- For local cheminformatics (fingerprints, descriptors, 3D conformers, scaffold extraction) use `rdkit`
- For deeper bioactivity / target-binding data (IC50, Ki against specific targets) use `chembl-database-bioactivity`

## Prerequisites

- **Python packages**: `requests`, `pandas` — both already in standard environments
- **No API key required** — PubChem is fully public
- **Rate limits**: max 5 requests/second and 400 requests/minute per IP. Throttle with `time.sleep(0.25)` in loops; return code 503 means you tripped the limit.

If you are inside a pixi/conda environment that already provides `requests` and `pandas`, skip the install and invoke scripts with `pixi run python ...`.

```bash
pip install requests pandas
```

## Quick Start

```python
import requests

BASE = "https://pubchem.ncbi.nlm.nih.gov/rest/pug"

# name → CID
cid = requests.get(f"{BASE}/compound/name/aspirin/cids/JSON").json()["IdentifierList"]["CID"][0]

# CID → properties (single call, many fields)
r = requests.get(
    f"{BASE}/compound/cid/{cid}/property/"
    "MolecularWeight,XLogP,TPSA,HBondDonorCount,HBondAcceptorCount,SMILES,IUPACName/JSON")
p = r.json()["PropertyTable"]["Properties"][0]
print(f"CID {cid} — {p['IUPACName']}")
print(f"  MW={p['MolecularWeight']}  XLogP={p['XLogP']}  TPSA={p['TPSA']}")
print(f"  HBD={p['HBondDonorCount']}  HBA={p['HBondAcceptorCount']}")
print(f"  SMILES={p['SMILES']}")
```

## Core API

### Module 1: Identifier lookup

Resolve any external identifier to a PubChem CID via `/compound/{namespace}/{value}/cids/JSON`. Namespaces: `name`, `cid`, `smiles`, `inchikey`, `inchi`, `formula`.

```python
import requests
from urllib.parse import quote

BASE = "https://pubchem.ncbi.nlm.nih.gov/rest/pug"

# By name (returns all matching CIDs as a list)
cids = requests.get(f"{BASE}/compound/name/caffeine/cids/JSON").json()["IdentifierList"]["CID"]
print(f"caffeine CIDs: {cids}")

# By canonical SMILES (URL-encode!)
smi = quote("CC(=O)OC1=CC=CC=C1C(=O)O", safe="")
cid = requests.get(f"{BASE}/compound/smiles/{smi}/cids/JSON").json()["IdentifierList"]["CID"][0]
print(f"aspirin SMILES → CID {cid}")

# By InChIKey (exact match, fastest if you already have one)
ikey = "BSYNRYMUTXBXSQ-UHFFFAOYSA-N"
cid = requests.get(f"{BASE}/compound/inchikey/{ikey}/cids/JSON").json()["IdentifierList"]["CID"][0]
print(f"InChIKey → CID {cid}")
```

### Module 2: Property retrieval

`/compound/cid/{cid_or_csv}/property/<csv-list>/JSON` returns all requested properties in one round trip. **CIDs and property names are both CSV-joinable** — batch up to ~200 CIDs and many properties at once.

```python
import requests

BASE = "https://pubchem.ncbi.nlm.nih.gov/rest/pug"

# Full property set for a single compound (ibuprofen CID 3672)
url = (f"{BASE}/compound/cid/3672/property/"
       "MolecularWeight,XLogP,TPSA,HBondDonorCount,HBondAcceptorCount,"
       "RotatableBondCount,SMILES,InChIKey,IUPACName,MolecularFormula/JSON")
p = requests.get(url).json()["PropertyTable"]["Properties"][0]
print(f"{p['IUPACName']}  formula={p['MolecularFormula']}")
print(f"  MW={p['MolecularWeight']} XLogP={p['XLogP']} TPSA={p['TPSA']}")
print(f"  HBD={p['HBondDonorCount']} HBA={p['HBondAcceptorCount']} RotB={p['RotatableBondCount']}")
```

```python
import requests, pandas as pd

# Batch: 4 CIDs, 3 properties — one request, one round trip
cids = "2244,3672,2157,2662"   # aspirin, ibuprofen, naproxen, celecoxib
r = requests.get(
    f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/{cids}/property/"
    "MolecularWeight,XLogP,TPSA/JSON")
df = pd.DataFrame(r.json()["PropertyTable"]["Properties"])
print(df.to_string(index=False))
```

### Module 3: Synonyms and description

Synonyms (trade names, CAS numbers, alternative spellings) and curated descriptions live at `/compound/{ns}/{value}/{synonyms|description}/JSON`.

```python
import requests

BASE = "https://pubchem.ncbi.nlm.nih.gov/rest/pug"

# Full synonym list (aspirin has ~700)
info = requests.get(f"{BASE}/compound/cid/2244/synonyms/JSON").json()["InformationList"]["Information"][0]
print(f"aspirin synonyms: {len(info['Synonym'])}")
for s in info["Synonym"][:8]:
    print(f"  {s}")
```

```python
import requests

# Curated descriptions (NCBI MeSH, CAMEO, etc.)
r = requests.get("https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/aspirin/description/JSON")
for item in r.json()["InformationList"]["Information"]:
    if "Description" in item:
        print(f"[{item.get('DescriptionSourceName','?')}]")
        print(f"  {item['Description'][:200]}…")
        print()
```

### Module 4: Similarity & substructure search (async ListKey pattern)

Structure searches return HTTP 202 + `{"Waiting": {"ListKey": "..."}}`. Poll `/compound/listkey/{key}/cids/JSON` every ~2s until it returns `IdentifierList`. Wrap this in a helper since it's used everywhere.

```python
import requests, time
from urllib.parse import quote

BASE = "https://pubchem.ncbi.nlm.nih.gov/rest/pug"

def poll_listkey(listkey, max_polls=10, interval=2.0):
    """Block until PubChem finishes async search; return CID list."""
    for _ in range(max_polls):
        time.sleep(interval)
        j = requests.get(f"{BASE}/compound/listkey/{listkey}/cids/JSON", timeout=20).json()
        if "IdentifierList" in j:
            return j["IdentifierList"]["CID"]
    raise TimeoutError(f"ListKey {listkey} did not complete")

# Tanimoto similarity (90% threshold, max 20 hits) — starting from aspirin SMILES
smi = quote("CC(=O)OC1=CC=CC=C1C(=O)O", safe="")
init = requests.get(
    f"{BASE}/compound/similarity/smiles/{smi}/JSON?Threshold=90&MaxRecords=20").json()
cids = poll_listkey(init["Waiting"]["ListKey"]) if "Waiting" in init \
       else init["IdentifierList"]["CID"]
print(f"aspirin @90% similarity: {len(cids)} hits, sample={cids[:5]}")
```

```python
import requests
from urllib.parse import quote

BASE = "https://pubchem.ncbi.nlm.nih.gov/rest/pug"

# Substructure search — all compounds containing a sulfonamide group
smi = quote("S(=O)(=O)N", safe="")
init = requests.get(
    f"{BASE}/compound/substructure/smiles/{smi}/JSON?MaxRecords=20").json()
cids = poll_listkey(init["Waiting"]["ListKey"]) if "Waiting" in init \
       else init["IdentifierList"]["CID"]
print(f"sulfonamide-containing CIDs: {len(cids)}, sample={cids[:5]}")
```

### Module 5: Assay summary (bioactivity data)

`/compound/cid/{cid}/assaysummary/JSON` returns a `Table` of every PubChem BioAssay the compound appears in (assay AID, target, outcome, micromolar activity if available).

```python
import requests, pandas as pd

BASE = "https://pubchem.ncbi.nlm.nih.gov/rest/pug"

r = requests.get(f"{BASE}/compound/cid/2244/assaysummary/JSON", timeout=30)
rows = r.json().get("Table", {}).get("Row", [])
cols = r.json().get("Table", {}).get("Columns", {}).get("Column", [])
print(f"aspirin appears in {len(rows)} bioassays")

# First few columns + rows as a DataFrame
df = pd.DataFrame([row["Cell"] for row in rows[:5]], columns=cols)
print(df.iloc[:, :6].to_string(index=False))
```

### Module 6: Structure file download (SDF / PNG)

`/compound/cid/{cid}/SDF` returns 2D MOL/SDF; `/compound/cid/{cid}/PNG` returns a structure image (use `?image_size=large` for higher resolution).

```python
import requests

BASE = "https://pubchem.ncbi.nlm.nih.gov/rest/pug"
cid = 2519   # caffeine

# 2D SDF for downstream RDKit / OpenBabel
sdf = requests.get(f"{BASE}/compound/cid/{cid}/SDF", timeout=15).text
with open("caffeine.sdf", "w") as f:
    f.write(sdf)
print(f"caffeine.sdf: {len(sdf)} chars, ends with M  END={'M  END' in sdf}")

# PNG structure image
png = requests.get(f"{BASE}/compound/cid/{cid}/PNG?image_size=large", timeout=15).content
with open("caffeine.png", "wb") as f:
    f.write(png)
print(f"caffeine.png: {len(png)} bytes")
```

## Key Concepts

### Async ListKey pattern

Similarity, substructure, and formula searches are **asynchronous** — the API kicks off a background job and returns HTTP 202 with `{"Waiting": {"ListKey": "<id>"}}`. Poll `/compound/listkey/{id}/cids/JSON` every ~2 seconds until the response contains `IdentifierList`. Most searches finish in 5–15s; tighten polling for tiny searches, loosen for very large ones. Use the `poll_listkey` helper from Module 4 everywhere.

A small fraction of fast searches return `IdentifierList` directly on the first call (no `Waiting` field); check for both possibilities.

### Property name reference

| API name              | Meaning                                   |
| --------------------- | ----------------------------------------- |
| `MolecularWeight`     | Molecular weight (g/mol, string)          |
| `MolecularFormula`    | Hill-system formula                       |
| `SMILES`              | Isomeric SMILES, with stereochemistry (2025+ name; was `IsomericSMILES`) |
| `ConnectivitySMILES`  | Connectivity-only SMILES, no stereo (2025+ name; was `CanonicalSMILES`) |
| `IUPACName`           | Curated IUPAC name                        |
| `InChI` / `InChIKey`  | IUPAC InChI / InChIKey                    |
| `XLogP`               | Computed logP (octanol/water)             |
| `TPSA`                | Topological polar surface area (Å²)       |
| `HBondDonorCount`     | Number of H-bond donors                   |
| `HBondAcceptorCount`  | Number of H-bond acceptors                |
| `RotatableBondCount`  | Number of rotatable bonds                 |
| `HeavyAtomCount`      | Non-hydrogen atom count                   |
| `Charge`              | Formal charge                             |

CSV-join any subset in a single `/property/<csv>/JSON` URL. Note that `MolecularWeight` returns as a string; cast to `float` before arithmetic.

### Response envelope shapes

- `cids/JSON`             → `{"IdentifierList": {"CID": [int, ...]}}`
- `property/.../JSON`     → `{"PropertyTable": {"Properties": [{...}, ...]}}` (one dict per CID, in input order)
- `synonyms/JSON`         → `{"InformationList": {"Information": [{"CID": int, "Synonym": [str, ...]}]}}`
- `description/JSON`      → `{"InformationList": {"Information": [{"CID": int, "Description": str, "DescriptionSourceName": str, ...}, ...]}}`
- `assaysummary/JSON`     → `{"Table": {"Columns": {"Column": [...]}, "Row": [{"Cell": [...]}, ...]}}`
- async-init (similarity, substructure, formula) → 202 with `{"Waiting": {"ListKey": "..."}}`
- listkey poll            → `{"IdentifierList": {"CID": [...]}}` when ready

## Common Workflows

### Workflow 1: Property comparison across a drug panel

**Goal**: side-by-side physicochemical comparison of a small molecule set.

```python
import requests, pandas as pd, time
from urllib.parse import quote

BASE = "https://pubchem.ncbi.nlm.nih.gov/rest/pug"

drugs = ["aspirin", "ibuprofen", "naproxen", "celecoxib"]

# Resolve names → CIDs in a loop (rate-limited)
cids = []
for d in drugs:
    cid = requests.get(f"{BASE}/compound/name/{quote(d)}/cids/JSON",
                       timeout=15).json()["IdentifierList"]["CID"][0]
    cids.append(cid)
    time.sleep(0.25)

# Single batched property pull
cid_csv = ",".join(str(c) for c in cids)
r = requests.get(
    f"{BASE}/compound/cid/{cid_csv}/property/"
    "MolecularWeight,XLogP,TPSA,HBondDonorCount,HBondAcceptorCount/JSON")
df = pd.DataFrame(r.json()["PropertyTable"]["Properties"])
df["Name"] = drugs
df = df[["Name", "CID", "MolecularWeight", "XLogP", "TPSA",
         "HBondDonorCount", "HBondAcceptorCount"]]
print(df.to_string(index=False))
```

### Workflow 2: Lead compound → similar analogs → properties

**Goal**: starting from a kinase inhibitor (gefitinib), find 85%-similar analogs and pull their properties.

```python
import requests, time
from urllib.parse import quote

BASE = "https://pubchem.ncbi.nlm.nih.gov/rest/pug"

def poll_listkey(listkey, max_polls=10, interval=2.0):
    for _ in range(max_polls):
        time.sleep(interval)
        j = requests.get(f"{BASE}/compound/listkey/{listkey}/cids/JSON",
                         timeout=20).json()
        if "IdentifierList" in j:
            return j["IdentifierList"]["CID"]
    raise TimeoutError("listkey timeout")

# 1. lead → CID → canonical SMILES
ref_cid = requests.get(
    f"{BASE}/compound/name/gefitinib/cids/JSON").json()["IdentifierList"]["CID"][0]
ref_smi = requests.get(
    f"{BASE}/compound/cid/{ref_cid}/property/SMILES/JSON"
    ).json()["PropertyTable"]["Properties"][0]["SMILES"]
print(f"gefitinib CID={ref_cid}  SMILES={ref_smi}")

# 2. similarity search
smi_q = quote(ref_smi, safe="")
init = requests.get(
    f"{BASE}/compound/similarity/smiles/{smi_q}/JSON?Threshold=85&MaxRecords=15"
    ).json()
sim_cids = poll_listkey(init["Waiting"]["ListKey"]) if "Waiting" in init \
           else init["IdentifierList"]["CID"]
print(f"  {len(sim_cids)} analogs @85% Tanimoto")

# 3. batch-pull properties for top 5 analogs
cid_csv = ",".join(str(c) for c in sim_cids[:5])
r = requests.get(
    f"{BASE}/compound/cid/{cid_csv}/property/"
    "MolecularWeight,XLogP,TPSA,RotatableBondCount/JSON")
for row in r.json()["PropertyTable"]["Properties"]:
    print(f"  CID {row['CID']}: MW={row['MolecularWeight']} XLogP={row['XLogP']}")
```

### Workflow 3: Pharmacophore screen via substructure → bioactivity check

**Goal**: find compounds with a sulfonamide motif and check which have bioactivity records.

```python
import requests, time
from urllib.parse import quote

BASE = "https://pubchem.ncbi.nlm.nih.gov/rest/pug"

def poll_listkey(listkey, max_polls=10, interval=2.0):
    for _ in range(max_polls):
        time.sleep(interval)
        j = requests.get(f"{BASE}/compound/listkey/{listkey}/cids/JSON",
                         timeout=20).json()
        if "IdentifierList" in j:
            return j["IdentifierList"]["CID"]
    raise TimeoutError("listkey timeout")

smi = quote("S(=O)(=O)N", safe="")
init = requests.get(
    f"{BASE}/compound/substructure/smiles/{smi}/JSON?MaxRecords=10").json()
cids = poll_listkey(init["Waiting"]["ListKey"]) if "Waiting" in init \
       else init["IdentifierList"]["CID"]
print(f"sulfonamide CIDs: {cids}")

# Bioactivity row counts for the first few hits
for cid in cids[:3]:
    rows = requests.get(f"{BASE}/compound/cid/{cid}/assaysummary/JSON",
                        timeout=30).json().get("Table", {}).get("Row", [])
    print(f"  CID {cid}: {len(rows)} assay rows")
    time.sleep(0.3)
```

## Key Parameters

| Parameter         | Endpoint / Module                | Default | Range / Options                            | Effect                                                                  |
| ----------------- | -------------------------------- | ------- | ------------------------------------------ | ----------------------------------------------------------------------- |
| `<namespace>`     | `/compound/{ns}/<value>/...`     | —       | `name`, `cid`, `smiles`, `inchikey`, `inchi`, `formula` | Input identifier type                                                  |
| `<property csv>`  | `/.../property/<csv>/JSON`       | —       | any subset of property names (see table)   | Which properties to return (one DB call per request)                    |
| `Threshold`       | similarity (M4)                  | `90`    | `0`–`100`                                  | Tanimoto cutoff (percent)                                               |
| `MaxRecords`      | similarity / substructure / formula | (server-side default) | `1`–`10000`                       | Cap on async result list                                                |
| `image_size`      | `/compound/cid/{cid}/PNG`        | medium  | `small`, `large`, `WxH` (e.g. `500x500`)   | PNG output resolution                                                   |
| `record_type`     | `/compound/cid/{cid}/SDF`        | `2d`    | `2d`, `3d`                                 | SDF dimensionality (`?record_type=3d`)                                  |
| `MaxAssayResults` | `/compound/cid/{cid}/assaysummary/JSON` | —    | int                                        | Limit assay rows when compound has thousands of records                 |

## Best Practices

1. **Always go through `cids/JSON` first** when starting from a name or external identifier. The name→CID resolution and the CID→property lookup are separate calls; doing both at once via `name → property` works but throws away the canonical CID list that downstream queries need.

2. **Batch properties, never loop them.** `compound/cid/2244,3672,2157,.../property/MolecularWeight,XLogP,.../JSON` accepts up to ~200 CIDs and any number of properties — one round trip instead of N. Looping `get_compounds` per name is the most common rate-limit trap.

3. **URL-encode every SMILES.** Use `urllib.parse.quote(smiles, safe="")`. Bare SMILES with `=`, `#`, `(`, `)`, `[`, `]` will sometimes work but breaks unpredictably on `+`, `/`, `\`, or query-string-looking substrings.

4. **Treat similarity/substructure/formula as async.** Branch on `"Waiting" in response` and poll `listkey` rather than re-issuing the search. Re-issuing creates a new ListKey and wastes the server's job slot.

5. **Throttle ≤ 5 req/sec, ≤ 400/min.** Insert `time.sleep(0.25)` in any tight loop. HTTP 503 means you tripped the limit — wait 10s and reduce concurrency.

6. **Cast `MolecularWeight` to `float`.** It's returned as a string (`"180.16"`) for full decimal fidelity. Comparing strings against numeric thresholds is a silent bug.

7. **For 100+ CIDs use POST.** GET URLs over ~2000 chars get truncated by some HTTP proxies. PubChem also accepts `POST` with `cid` in the form body: `requests.post(f"{BASE}/compound/cid/property/MolecularWeight/JSON", data={"cid": cid_csv})`.

8. **2025 SMILES property rename.** PubChem renamed two SMILES properties in the 2025 PUG-REST schema: old `IsomericSMILES` (with stereo) → `SMILES`, and old `CanonicalSMILES` (connectivity only, no stereo) → `ConnectivitySMILES`. The URL path still accepts the legacy names as *input* (e.g. `/property/CanonicalSMILES/JSON` returns 200), but the response JSON is keyed with the **new** names. So a request succeeds and only the parse step breaks with `KeyError`. Use `SMILES` / `ConnectivitySMILES` in new code and read those keys.

## Common Recipes

### Recipe 1 — Lipinski's Rule of Five check

```python
import requests
from urllib.parse import quote

BASE = "https://pubchem.ncbi.nlm.nih.gov/rest/pug"

def check_lipinski(name):
    cid = requests.get(f"{BASE}/compound/name/{quote(name)}/cids/JSON"
                       ).json()["IdentifierList"]["CID"][0]
    p = requests.get(
        f"{BASE}/compound/cid/{cid}/property/"
        "MolecularWeight,XLogP,HBondDonorCount,HBondAcceptorCount/JSON"
        ).json()["PropertyTable"]["Properties"][0]
    mw, xlogp = float(p["MolecularWeight"]), p.get("XLogP", 0) or 0
    hbd, hba  = p["HBondDonorCount"], p["HBondAcceptorCount"]
    rules = {"MW ≤ 500": mw <= 500, "XLogP ≤ 5": xlogp <= 5,
             "HBD ≤ 5": hbd <= 5,   "HBA ≤ 10": hba <= 10}
    v = sum(1 for ok in rules.values() if not ok)
    return rules, v

rules, v = check_lipinski("metformin")
print(f"violations: {v}/4 ({'PASS' if v <= 1 else 'FAIL'})")
for r, ok in rules.items(): print(f"  {'✓' if ok else '✗'} {r}")
```

### Recipe 2 — Pull every synonym / trade name

```python
import requests

r = requests.get("https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/aspirin/synonyms/JSON")
syns = r.json()["InformationList"]["Information"][0]["Synonym"]
print(f"{len(syns)} synonyms")
for s in syns[:10]:
    print(f"  {s}")
```

### Recipe 3 — Download a structure PNG

```python
import requests

cid = 2519   # caffeine
png = requests.get(
    f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/{cid}/PNG?image_size=large"
    ).content
with open("caffeine.png", "wb") as f:
    f.write(png)
print(f"wrote caffeine.png ({len(png)} bytes)")
```

### Recipe 4 — Robust session with retry / 429 handling

```python
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

s = requests.Session()
s.headers.update({"Accept": "application/json"})
s.mount("https://", HTTPAdapter(max_retries=Retry(
    total=4, backoff_factor=1.0,
    status_forcelist=[429, 500, 502, 503, 504],
    allowed_methods=["GET", "POST"])))

r = s.get(
    "https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/2244/property/MolecularWeight/JSON",
    timeout=15)
r.raise_for_status()
print(r.json()["PropertyTable"]["Properties"][0]["MolecularWeight"])
```

## Expected Outputs

- **CID lookup** (`/.../cids/JSON`): `{"IdentifierList": {"CID": [...]}}` — list of integer CIDs, ordered by relevance for name searches.
- **Properties** (`/.../property/.../JSON`): `{"PropertyTable": {"Properties": [{"CID": ..., "MolecularWeight": "180.16", ...}, ...]}}`. One row per CID in input order; `MolecularWeight` is a *string*.
- **Synonyms**: `{"InformationList": {"Information": [{"CID": 2244, "Synonym": ["aspirin", "ACETYLSALICYLIC ACID", "50-78-2", ...]}]}}`.
- **Async search init**: HTTP 202 with `{"Waiting": {"ListKey": "12345..."}}`. Poll `/compound/listkey/{key}/cids/JSON` until it returns `IdentifierList`.
- **Assay summary**: `{"Table": {"Columns": {"Column": [...col names...]}, "Row": [{"Cell": [...]}, ...]}}`.
- **SDF**: plain text starting with the CID header line; ends with `M  END` followed by SDF property blocks.
- **PNG**: binary `image/png`, ~2–4 KB at default size, ~10–20 KB at `image_size=large`.

## Troubleshooting

| Problem                                                                         | Cause                                                                              | Solution                                                                                                                            |
| ------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------- |
| HTTP 404 `PUGREST.NotFound`                                                     | Name / SMILES / formula matched no record                                          | Try a CAS number or InChIKey; check spelling in the PubChem web UI; canonical SMILES from RDKit often resolves where input SMILES doesn't |
| HTTP 202 stuck in `{"Waiting":...}` for a similarity/substructure call           | Async job still running                                                            | Poll `/compound/listkey/{key}/cids/JSON` every 2s up to ~30s; reduce `MaxRecords` if it never completes                              |
| HTTP 503 `PUGREST.ServerBusy`                                                   | Tripped the 5-req/s or 400-req/min rate limit                                      | Insert `time.sleep(0.25)` in loops; use the Retry session in Recipe 4; reduce concurrency                                            |
| HTTP 400 on a SMILES URL                                                        | SMILES wasn't URL-encoded                                                          | Wrap in `urllib.parse.quote(smi, safe="")` — `#`, `+`, `/` and `\` all break path parsing                                            |
| `KeyError: 'CanonicalSMILES'` / `KeyError: 'IsomericSMILES'`                    | Requested old name; URL returns 200 but 2025 JSON is keyed `ConnectivitySMILES` / `SMILES` | Read `p["ConnectivitySMILES"]` (connectivity, no stereo) or `p["SMILES"]` (with stereo); update the property CSV to the new names    |
| `TypeError: '>' not supported between instances of 'str' and 'int'`             | `MolecularWeight` is a string                                                      | `float(p["MolecularWeight"])` before any arithmetic comparison                                                                       |
| Batch `cid/2244,3672,...` returns only some rows                                | URL exceeded server limit                                                          | Switch to `requests.post(url, data={"cid": "2244,3672,..."})`; same URL minus the value, body carries the CSV                        |
| Empty `assaysummary` Table                                                      | CID has no bioassay records                                                        | Not all compounds are assayed; verify on the PubChem web page                                                                        |
| `XLogP` is `None` for a valid CID                                               | Property not computed for that compound                                            | Guard with `p.get("XLogP", 0) or 0` before arithmetic                                                                                |

## Related Skills

- `chembl-database-bioactivity` — IC50 / Ki / Kd target-binding data, deeper than PubChem's assay summaries
- `rdkit-cheminformatics` — local SMILES/MOL manipulation, fingerprints, descriptors, scaffold extraction
- `pdb-database` — protein structures co-crystallized with the small molecules found via PubChem CIDs

## References

- [PubChem PUG-REST documentation](https://pubchem.ncbi.nlm.nih.gov/docs/pug-rest) — Full URL grammar reference
- [PUG-REST tutorial with worked examples](https://pubchem.ncbi.nlm.nih.gov/docs/pug-rest-tutorial) — Step-by-step API walk-through
- [PubChem property table](https://pubchem.ncbi.nlm.nih.gov/docs/pug-rest#section=Compound-Property-Tables) — Authoritative list of `/property/<name>` values and their semantics
- [PubChem main site](https://pubchem.ncbi.nlm.nih.gov/) — Web interface for spot-checks
- [Kim et al. (2023) Nucleic Acids Res — PubChem 2023 update](https://doi.org/10.1093/nar/gkac956)
