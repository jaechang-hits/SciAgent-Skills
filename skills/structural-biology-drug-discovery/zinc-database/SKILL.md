---
name: "zinc-database"
description: "Query the ZINC22 virtual compound library (CartBlanche API, billions of make-on-demand + purchasable molecules). Look up substances by ZINC ID, resolve a SMILES to its ZINC ID (exact match), inspect purchasability/catalogs, and assemble compound sets for docking. Property (MW/logP) filtering is done locally with RDKit. For bioactivity use chembl-database-bioactivity; for approved drugs use drugbank-database-access."
license: "CC-BY-4.0"
---

# ZINC Chemical Library Database (ZINC22 / CartBlanche)

## Overview

ZINC (ZINC Is Not Commercial) is a free database of commercially available compounds curated for virtual screening. The current generation, **ZINC22**, holds billions of make-on-demand and in-stock molecules and is served through the **CartBlanche** web application at `cartblanche22.docking.org`. CartBlanche exposes a small JSON API to look up substances by ZINC ID, resolve a SMILES to its ZINC identifier, and inspect supplier/catalog purchasability.

> **Important — the old ZINC15 REST API no longer works for automated access.**
> `zinc15.docking.org` (and `zinc.docking.org`) now sits behind a site-wide CAPTCHA: every request to `/substances.json`, `/tranches/...`, `/substances/{id}.json`, etc. is redirected to a `/captcha/` page or returns `403 Forbidden`. Any script using the `mwt__gte` / `availability` / `similarity` query parameters against `zinc15.docking.org` will fail. Use the ZINC22 CartBlanche endpoints documented below instead.

Three things about ZINC22/CartBlanche that change how you use this skill:

1. **There is no server-side property-range query.** ZINC22/CartBlanche has no `mwt__gte` / `logp__lte` / `hbd__lte` search. You filter by molecular property by either (a) selecting **tranches** (a 2D MW x logP grid) for bulk download, or (b) retrieving compounds and filtering locally with RDKit. This skill shows the local-RDKit approach.
2. **SMILES lookup is asynchronous.** You POST a SMILES, receive a `task` id, and poll for the result. Exact-match lookup completes in seconds.
3. **Reliable programmatic search = exact match.** The API's broader analog search (`dist` > 0) is slow and frequently times out on the public server, and the Smallworld similarity search is a website-only flow. Treat exact SMILES → ZINC ID lookup as the dependable primitive; see the "Analog / Similarity Search" note for the (limited) alternatives.

## When to Use

- Looking up a known ZINC ID to get its SMILES, computed properties, and purchasability/suppliers
- Resolving a molecule you have as a SMILES to its ZINC22 identifier(s) to check availability
- Checking whether a hit compound is purchasable and from which catalogs before ordering
- Assembling a SMILES/ZINC-ID set to feed into a docking campaign
- For property-filtered library building, combine SMILES/tranche retrieval here with local RDKit filtering (`rdkit-cheminformatics`)
- For known drug bioactivity data use `chembl-database-bioactivity`; for approved drug structures use `drugbank-database-access`

## Prerequisites

- **Python packages**: `requests`, `pandas` (and `rdkit` for local property filtering)
- **Data requirements**: a ZINC ID, or a SMILES string
- **Environment**: internet connection; no API key needed; SMILES lookups are async (poll for the result)
- **Rate limits**: be courteous — serialize searches, cache results, and do not poll the task endpoint faster than once every few seconds

```bash
pip install requests pandas
# optional, for local property filtering:
pip install rdkit
```

## Quick Start

```python
import requests

BASE = "https://cartblanche22.docking.org"
HEADERS = {"User-Agent": "sciagent-zinc-skill/1.0"}

# Look up a substance by ZINC ID (synchronous, returns JSON immediately)
r = requests.get(f"{BASE}/substance/ZINC000000029632.json", headers=HEADERS, timeout=30)
r.raise_for_status()
c = r.json()

td = c["tranche_details"]
print(f"ZINC ID : {c['zinc_id']}  (db: {c['db']})")
print(f"SMILES  : {c['smiles']}")
print(f"MW      : {td['mwt']:.2f}   logP: {td['logp']:.2f}   heavy atoms: {td['heavy_atoms']}")
print(f"InChIKey: {td['inchikey']}")
print(f"Catalogs: {len(c.get('catalogs', []))} supplier entries")
```

Expected output (abridged):

```
ZINC ID : ZINC000000029632  (db: zinc20)
SMILES  : O=C([C@H]1CCCN1C(=O)Cc1c[nH]c2ccccc12)N1CCc2ccccc2C1
MW      : 387.48   logP: 3.29   heavy atoms: 29
InChIKey: QCEMBLKSDIWPBK-JOCHJYFZSA-N
Catalogs: 4 supplier entries
```

## Core API

The CartBlanche base URL and two reusable helpers used throughout:

```python
import requests, time

BASE = "https://cartblanche22.docking.org"
HEADERS = {"User-Agent": "sciagent-zinc-skill/1.0"}

def get_substance(zinc_id):
    """Fetch full record for one ZINC ID (synchronous)."""
    r = requests.get(f"{BASE}/substance/{zinc_id}.json", headers=HEADERS, timeout=30)
    r.raise_for_status()
    return r.json()

def smiles_lookup(smiles, dist=0, adist=0, database="zinc22", timeout=120, poll=5):
    """Resolve a SMILES to ZINC22 substance dicts via the async task API.

    dist=0, adist=0 -> exact match (fast, reliable; use this).
    dist/adist > 0  -> near-neighbor analog search (slow; may time out — see note).
    Returns a list of substance dicts (possibly empty).
    """
    files = {"smiles": (None, smiles), "dist": (None, str(dist)),
             "adist": (None, str(adist)), "database": (None, database)}
    sub = requests.post(f"{BASE}/smiles.json", files=files, headers=HEADERS, timeout=60)
    sub.raise_for_status()
    task = sub.json()["task"]                       # async: returns {"task": "<uuid>"}

    deadline = time.time() + timeout
    while time.time() < deadline:
        res = requests.get(f"{BASE}/search/result/{task}", headers=HEADERS, timeout=30).json()
        if res.get("status") == "SUCCESS":
            data = res.get("result")
            # result is {"zinc22": [...], "zinc20": [...]} when hits exist,
            # or an empty list when there are none.
            if isinstance(data, dict):
                return data.get("zinc22", []) + data.get("zinc20", [])
            return data or []
        time.sleep(poll)                            # status == "PROGRESS" until done
    raise TimeoutError(f"ZINC22 search task {task} did not finish in {timeout}s")
```

### Query 1: Retrieve a Compound by ZINC ID

Fetch the full record (SMILES, computed properties, formula, ring/heteroatom counts, supplier catalogs) for a known ZINC identifier.

```python
c = get_substance("ZINC000000029632")
td = c["tranche_details"]

print(f"ZINC ID    : {c['zinc_id']}")
print(f"SMILES     : {c['smiles']}")
print(f"Formula    : {c['mol_formula']}")
print(f"MW         : {td['mwt']:.2f}")
print(f"logP       : {td['logp']:.2f}")
print(f"Heavy atoms: {td['heavy_atoms']}")
print(f"Rings      : {c['rings']}   Hetero atoms: {c['hetero_atoms']}")
print(f"InChIKey   : {td['inchikey']}")
print(f"Suppliers  : {len(c.get('catalogs', []))}")
```

Both the modern `ZINCbq...`/`ZINCbj...` style IDs and the legacy 12-digit `ZINC000...` IDs resolve through this endpoint.

### Query 2: Resolve a ZINC ID from a SMILES (Exact Match)

Find the ZINC22 identifier(s) for a molecule you have as a SMILES string. This is the dependable search primitive.

```python
hits = smiles_lookup("CC(=O)Nc1ccc(O)cc1")   # acetaminophen, exact (dist=0)
print(f"Exact matches: {len(hits)}")
for h in hits[:5]:
    td = h["tranche_details"]
    print(f"  {h['zinc_id']:22s}  MW {td['mwt']:.1f}  logP {td['logp']:.2f}  {h['smiles']}")
```

A single molecule can map to several ZINC IDs across ZINC22 sub-databases (e.g. `ZINCbq...` and `ZINCbj...`) — each represents the same structure in a different build.

### Query 3: Purchasability and Supplier Catalogs

Purchasability is embedded in the substance record under `catalogs` — no separate request needed.

```python
c = get_substance("ZINC000000029632")
catalogs = c.get("catalogs", [])
print(f"Supplier entries: {len(catalogs)}")
for cat in catalogs:
    print(f"  {cat.get('catalog_name', 'n/a'):24s} | "
          f"purchasable: {cat.get('purchase')} | "
          f"code: {cat.get('supplier_code', 'n/a')} | "
          f"price: {cat.get('price', 'n/a')} {cat.get('unit', '')}")
```

`purchase: 1` indicates the compound is orderable from that catalog; entries may include price, quantity, and lead time (`shipping`).

### Query 4: Property-Filtered Library (Local RDKit Filtering)

ZINC22 has no server-side MW/logP query. The portable pattern is: gather candidate SMILES (resolved ZINC IDs, a downloaded tranche file, or your own enumeration), then filter locally with RDKit.

```python
import pandas as pd
from rdkit import Chem
from rdkit.Chem import Descriptors, Lipinski

# Candidate SMILES (here: a small hand list; in practice load a tranche .smi or your own set)
smiles_list = [
    "CC(=O)Nc1ccc(O)cc1",            # acetaminophen  (MW 151 - too small, filtered out)
    "CC(C)NCC(O)COc1cccc2ccccc12",   # propranolol    (MW 259, logP 2.6 - lead-like)
    "CN(C)CCOC(c1ccccc1)c1ccccc1",   # diphenhydramine
    "c1ccc(NC(=O)c2ccccc2)cc1",      # benzanilide    (MW 197 - too small, filtered out)
]

def lead_like(smi):
    m = Chem.MolFromSmiles(smi)
    if m is None:
        return None
    mw, logp = Descriptors.MolWt(m), Descriptors.MolLogP(m)
    hbd, hba = Lipinski.NumHDonors(m), Lipinski.NumHAcceptors(m)
    ok = 250 <= mw <= 350 and 1 <= logp <= 3 and hbd <= 3 and hba <= 7
    return {"smiles": Chem.MolToSmiles(m), "mw": round(mw, 1), "logp": round(logp, 2),
            "hbd": hbd, "hba": hba} if ok else None

rows = [r for r in (lead_like(s) for s in smiles_list) if r]
df = pd.DataFrame(rows).drop_duplicates(subset=["smiles"])
print(f"Lead-like compounds after RDKit filter: {len(df)}")
print(df.head())
```

### Analog / Similarity Search (limited — read before relying on it)

The submit endpoint accepts `dist` (topological graph-edit distance, 0–3) and `adist` ("anon" distance, scaffold hops) for a near-neighbor **analog** search:

```python
# Near-neighbor analogs. Keep dist small (1) and the timeout generous; expect FEW results.
try:
    analogs = smiles_lookup("c1ccc(NC(=O)c2ccccc2)cc1", dist=1, adist=0, timeout=240)
    print(f"Analogs: {len(analogs)}")
    for h in analogs[:10]:
        print("  ", h["zinc_id"], h["smiles"])
except TimeoutError as e:
    print("Analog search timed out:", e)
```

Caveats verified against the live public server:
- `dist=0` (exact) is fast and reliable. `dist >= 1` runs across billions of molecules on a shared cluster and **frequently times out** (e.g. `dist=3` did not return within ~270 s); even when it succeeds it often returns only the query and a handful of near-identical structures.
- For broad **whole-molecule similarity** (Tanimoto over graph-edit distance), CartBlanche provides a separate **Smallworld** search on the website (`cartblanche22.docking.org` → Similarity → Smallworld, `/similarity/sw`). It is an interactive flow and is not exposed as a simple GET/POST JSON endpoint here — use the web UI for large similarity jobs.
- Do not build automated pipelines that assume analog search returns a rich set. Base workflows on exact lookup + local RDKit/cheminformatics expansion instead.

## Key Concepts

### ZINC22 IDs

ZINC22 introduced short alphanumeric IDs such as `ZINCbq0000001gLA` (the prefix letters encode the sub-database / tranche). Legacy 12-digit IDs like `ZINC000000029632` (from ZINC15/ZINC20) still resolve through `/substance/{id}.json`. Always pass the ID exactly as given.

### Asynchronous Search Model

SMILES searches are queued as tasks:

1. `POST /smiles.json` (multipart form: `smiles`, `dist`, `adist`, `database`) → `{"task": "<uuid>"}`
2. `GET /search/result/{task}` → `{"status": "PROGRESS"}` while running, then `{"status": "SUCCESS", "result": {...}}`
3. On success, `result` is a dict keyed by sub-database (`zinc22`, sometimes `zinc20`) when there are hits, or an empty list when there are none. The helper above normalizes both shapes.

### Tranches

ZINC organizes molecules into a 2D grid of "tranches" by heavy-atom count / MW (H-codes, e.g. `H11`) and logP (letter bins). The CartBlanche **Tranches** browser (`cartblanche22.docking.org`, "3D"/"2D" tranche pages) lets you select property regions and bulk-download SMILES/SDF for docking. Tranche bulk download is interactive (and large); for programmatic property filtering prefer the RDKit approach in Query 4, or fetch tranche files from `files.docking.org` and filter locally.

### Result Fields

Each search/substance record exposes: `zinc_id`, `smiles`, `mol_formula`, `rings`, `hetero_atoms`, `db`, `catalogs[]`, and `tranche_details` (`mwt`, `logp`, `heavy_atoms`, `inchi`, `inchikey`). SMILES search rows additionally include `sub_id`, `matched_smiles`, and the `tranche` code.

## Common Workflows

### Workflow 1: Check Purchasability of a Hit List

**Goal**: Given SMILES of docking hits, resolve their ZINC22 IDs and report which are purchasable.

```python
import pandas as pd

hit_smiles = [
    "CC(=O)Nc1ccc(O)cc1",            # acetaminophen
    "c1ccc(NC(=O)c2ccccc2)cc1",      # benzanilide
]

rows = []
for smi in hit_smiles:
    matches = smiles_lookup(smi)                   # exact
    if not matches:
        rows.append({"query_smiles": smi, "zinc_id": None, "purchasable": False})
        continue
    for m in matches:
        cats = m.get("catalogs", [])
        rows.append({
            "query_smiles": smi,
            "zinc_id": m["zinc_id"],
            "mw": m["tranche_details"]["mwt"],
            "n_catalogs": len(cats),
            "purchasable": any(c.get("purchase") for c in cats) or bool(cats),
        })

df = pd.DataFrame(rows)
print(df)
df.to_csv("hit_purchasability.csv", index=False)
print("Saved: hit_purchasability.csv")
```

### Workflow 2: Resolve and Property-Filter a Candidate Set for Docking

**Goal**: Take a list of candidate SMILES (your own enumeration or a tranche file), keep the ones present/purchasable in ZINC22, filter to lead-like space, and export SMILES for docking.

```python
import pandas as pd
from rdkit import Chem
from rdkit.Chem import Descriptors

candidates = [
    "CC(=O)Nc1ccc(O)cc1",
    "O=C([C@H]1CCCN1C(=O)Cc1c[nH]c2ccccc12)N1CCc2ccccc2C1",
    "c1ccc(NC(=O)c2ccccc2)cc1",
]

rows = []
for smi in candidates:
    m = Chem.MolFromSmiles(smi)
    if m is None:
        continue
    mw, logp = Descriptors.MolWt(m), Descriptors.MolLogP(m)
    if not (200 <= mw <= 500 and -1 <= logp <= 5):     # lead-like local filter
        continue
    matches = smiles_lookup(smi)                        # confirm it exists in ZINC22
    if not matches:
        continue
    m0 = matches[0]
    rows.append({"zinc_id": m0["zinc_id"], "smiles": Chem.MolToSmiles(m),
                 "mw": round(mw, 1), "logp": round(logp, 2),
                 "purchasable": bool(m0.get("catalogs"))})

df = pd.DataFrame(rows).drop_duplicates(subset=["smiles"])
print(f"ZINC22-confirmed lead-like compounds: {len(df)}")
df[["smiles", "zinc_id"]].to_csv("docking_library.smi", sep=" ", index=False, header=False)
print("Saved: docking_library.smi")
print(df)
```

## Key Parameters

| Parameter | Endpoint | Default | Range / Options | Effect |
|-----------|----------|---------|-----------------|--------|
| (path) | `GET /substance/{zinc_id}.json` | — | ZINC ID | Synchronous substance lookup |
| `smiles` | `POST /smiles.json` | — | valid SMILES | Query molecule |
| `dist` | `POST /smiles.json` | `0` | `0`–`3` | Topological distance; `0` = exact (reliable), `>=1` = analog search (slow, may time out) |
| `adist` | `POST /smiles.json` | `0` | `0`–`3` | Anonymous-graph distance (scaffold hopping); `0` = off |
| `database` | `POST /smiles.json` | `zinc22` | `"zinc22"`, `"zinc20"` | Which ZINC build to search |
| `task` | `GET /search/result/{task}` | — | UUID from submit | Poll handle for async result |

## Best Practices

1. **Use ZINC22 (CartBlanche), not ZINC15.** The `zinc15.docking.org` REST API is CAPTCHA-walled and will not work from scripts. All endpoints here target `cartblanche22.docking.org`.

2. **Lean on exact lookup; don't depend on analog search.** `dist=0` is the reliable primitive. For analogs/similarity, expand locally (RDKit, `rdkit-cheminformatics`) or use the Smallworld web UI — the analog API times out on broad queries.

3. **Filter properties locally with RDKit.** There is no server-side MW/logP/HBD query in ZINC22. Retrieve candidates, then filter with RDKit — this is also where you apply PAINS/Brenk alerts.

4. **Poll politely.** SMILES lookups are async; poll `/search/result/{task}` every few seconds, set a sensible timeout, and handle the `PROGRESS` → `SUCCESS` transition (and `TimeoutError`).

5. **Deduplicate by canonical SMILES.** A structure can appear under multiple ZINC IDs / catalogs. Canonicalize with RDKit (`Chem.MolToSmiles(Chem.MolFromSmiles(smi))`) before docking.

6. **Verify purchasability via `catalogs`.** Treat `catalogs` entries with `purchase: 1` as orderable; record `supplier_code` and `catalog_name` for procurement.

7. **Cache results.** ZINC data updates periodically; cache substance/search JSON with a date-stamped filename and avoid re-querying within a project.

## Common Recipes

### Recipe: Lookup ZINC22 ID and purchasability from a SMILES

```python
matches = smiles_lookup("CC(=O)Nc1ccc(O)cc1")   # acetaminophen
for m in matches:
    cats = m.get("catalogs", [])
    print(f"{m['zinc_id']} | MW {m['tranche_details']['mwt']:.1f} | "
          f"catalogs {len(cats)} | purchasable {bool(cats)}")
```

### Recipe: Batch-resolve a list of ZINC IDs

```python
zinc_ids = ["ZINC000000029632", "ZINCbq0000001gLA"]
for zid in zinc_ids:
    try:
        c = get_substance(zid)
        print(f"{zid}: {c['smiles']}  MW {c['tranche_details']['mwt']:.1f}")
    except requests.HTTPError as e:
        print(f"{zid}: not found ({e.response.status_code})")
```

### Recipe: Property Distribution of a Library

```python
import pandas as pd
from rdkit import Chem
from rdkit.Chem import Descriptors

df = pd.read_csv("docking_library.smi", sep=" ", names=["smiles", "zinc_id"])
df["mw"] = df["smiles"].map(lambda s: Descriptors.MolWt(Chem.MolFromSmiles(s)))
df["logp"] = df["smiles"].map(lambda s: Descriptors.MolLogP(Chem.MolFromSmiles(s)))
print(f"Library size: {len(df)}")
print(df[["mw", "logp"]].describe())
```

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| Requests to `zinc15.docking.org` redirect to `/captcha/` or return `403` | The legacy ZINC15 REST API is CAPTCHA-walled and unusable from scripts | Switch all calls to `cartblanche22.docking.org` (ZINC22 / CartBlanche) as shown here |
| `GET /substances/{id}.json` (plural) returns HTML | Wrong path — that is the SPA catch-all | Use the **singular** `/substance/{id}.json` |
| Endpoint returns `200` with `content-type: application/json` but body is HTML | CartBlanche serves the SPA shell for unknown routes (misleading content-type) | Check the body actually parses as JSON; only the documented endpoints return data |
| `POST /smiles.json` returns `{"task": ...}` but you expected results | SMILES search is asynchronous | Poll `GET /search/result/{task}` until `status == "SUCCESS"` |
| `400 No Valid SMILES, please try again` | SMILES rejected (or wrong request form) | Validate the SMILES with RDKit; submit via multipart form fields `smiles`/`dist`/`adist`/`database` |
| `KeyError: 'data'` / `'zinc22'` on a successful task | `result` is a dict when there are hits, but an empty list when there are none | Handle both shapes (see `smiles_lookup` helper) |
| Analog search (`dist >= 1`) times out or returns only the exact match | Very large search space on a shared cluster | Use `dist=0` (exact); for similarity use the Smallworld web UI; expand analogs locally with RDKit |
| `/substance/random.json` returns `400`; `/substance/random/{n}.json` returns `{"status":"PENDING"}` | The random endpoint is async/non-trivial | Not needed for scripting; pick known ZINC IDs instead |
| `HTTP 404` for a compound ID | ID typo or not present in this build | Verify the ZINC ID; try `database="zinc20"` for legacy IDs |

## Related Skills

- `rdkit-cheminformatics` — Compute properties and apply PAINS/Brenk filters on retrieved ZINC compounds (required for property filtering here)
- `autodock-vina-docking` — Use exported ZINC SMILES/SDF files for molecular docking campaigns
- `chembl-database-bioactivity` — Bioactivity data for compounds identified in ZINC virtual screens
- `drugbank-database-access` — Approved-drug structures and annotations

## References

- [CartBlanche / ZINC22 web app](https://cartblanche22.docking.org/) — Substance lookup, SMILES search, tranche browser
- [ZINC22 paper](https://doi.org/10.1021/acs.jcim.2c01253) — Tingle et al., "ZINC-22, A Free Multi-Billion-Scale Database of Tangible Compounds for Ligand Discovery," J. Chem. Inf. Model. 2023
- [docking.org wiki](https://wiki.docking.org/) — CartBlanche usage and ZINC22 download documentation
- [files.docking.org](https://files.docking.org/) — Bulk tranche file downloads for ZINC22
