---
name: "ddinter-database"
description: "Query drug-drug interaction (DDI) data from DDInter via REST API. Search interactions by drug name or ID, retrieve severity levels (major/moderate/minor), interaction mechanisms, and clinical recommendations for drug pairs. Covers 1.7M+ interactions across 2,400+ drugs. No authentication required. For FDA drug labeling use dailymed-database; for pharmacogenomics use clinpgx-database."
license: "CC-BY-4.0"
---

# DDInter Drug-Drug Interaction Database

## Overview

DDInter is an open, curated database of drug-drug interactions (DDIs) covering 2,400+ drugs and 1.7M+ pairwise interactions with structured severity levels (major, moderate, minor), mechanistic annotations, and clinical management recommendations. Access is provided via a JSON REST API at `https://ddinter.scbdd.com/api/` — no authentication or registration required.

## When to Use

- Checking whether two co-administered drugs have a known interaction and its severity (major/moderate/minor)
- Retrieving all known interactions for a given drug to support polypharmacy risk assessment
- Identifying the mechanistic basis (pharmacokinetic vs. pharmacodynamic) of a drug-drug interaction
- Screening a drug combination list for potential major interactions before clinical decision support
- Building automated DDI checking pipelines for medication review or drug repurposing workflows
- Analyzing the DDI network for a drug class (e.g., all major interactions for CYP3A4 substrates)
- For FDA-approved drug labeling text (indications, dosage, contraindications) use `dailymed-database`
- For pharmacogenomics interactions (CYP genotype-drug associations) use `clinpgx-database`; DDInter covers drug-drug not gene-drug pairs
- For drug adverse event reports from FAERS use `fda-database`

## Prerequisites

- **Python packages**: `requests`, `pandas`, `matplotlib`, `networkx`
- **Data requirements**: drug names or DDInter drug IDs
- **Environment**: internet connection; no API key required
- **Rate limits**: no officially published rate limit; use `time.sleep(0.3)` between requests in batch loops for polite access

```bash
pip install requests pandas matplotlib networkx
```

## Quick Start

```python
import requests

BASE = "https://ddinter.scbdd.com/api"

# Search for a drug by name
r = requests.get(f"{BASE}/drug/", params={"drug_name": "warfarin", "format": "json"}, timeout=15)
r.raise_for_status()
data = r.json()
print(f"Results for 'warfarin': {data['count']} drugs found")
for drug in data["results"][:3]:
    print(f"  ID={drug['ddinter_id']}  Name={drug['drug_name']}")
# Results for 'warfarin': 1 drugs found
#   ID=DDInter_D00001  Name=Warfarin
```

## Core API

### Query 1: Search Drug by Name

Find a drug's DDInter ID by searching its name. The DDInter ID is required for all interaction queries.

```python
import requests
import pandas as pd

BASE = "https://ddinter.scbdd.com/api"

def search_drug(drug_name):
    """Search DDInter for a drug by name. Returns list of matching drug records."""
    r = requests.get(f"{BASE}/drug/",
                     params={"drug_name": drug_name, "format": "json"},
                     timeout=15)
    r.raise_for_status()
    return r.json()

# Search for warfarin
result = search_drug("warfarin")
print(f"Matches: {result['count']}")
if result["results"]:
    drug = result["results"][0]
    print(f"DDInter ID: {drug['ddinter_id']}")
    print(f"Drug name: {drug['drug_name']}")
    # Store DDInter ID for interaction queries
    warfarin_id = drug["ddinter_id"]
    print(f"\nWarfarin DDInter ID: {warfarin_id}")

# Batch name lookup
drugs_to_find = ["warfarin", "aspirin", "atorvastatin", "metformin", "amiodarone"]
id_map = {}
for name in drugs_to_find:
    res = search_drug(name)
    if res["results"]:
        id_map[name] = res["results"][0]["ddinter_id"]
        print(f"  {name:20s} → {res['results'][0]['ddinter_id']}")
```

### Query 2: Get All Interactions for a Drug

Retrieve all known DDIs for a drug by its DDInter ID. Returns interaction partners, severity, and clinical information.

```python
import requests
import pandas as pd

BASE = "https://ddinter.scbdd.com/api"

def get_drug_interactions(drug_id, page_size=100):
    """Get all DDIs for a drug by DDInter ID. Handles pagination automatically."""
    all_interactions = []
    url = f"{BASE}/interaction/"
    params = {"drug_id": drug_id, "format": "json", "page_size": page_size}

    while url:
        r = requests.get(url, params=params, timeout=20)
        r.raise_for_status()
        data = r.json()
        all_interactions.extend(data.get("results", []))
        url = data.get("next")   # None when last page
        params = {}              # next URL already includes params

    return all_interactions

# Get all interactions for warfarin (DDInter_D00001)
interactions = get_drug_interactions("DDInter_D00001")
print(f"Warfarin total interactions: {len(interactions)}")

# Summarize by severity
df = pd.DataFrame(interactions)
if not df.empty and "level" in df.columns:
    severity_counts = df["level"].value_counts()
    print("\nInteractions by severity:")
    for level, count in severity_counts.items():
        print(f"  {level:15s}: {count:4d}")
    # Major: 45
    # Moderate: 312
    # Minor: 198
```

### Query 3: Get Interaction Details by Interaction ID

Retrieve full details for a specific drug-drug interaction, including mechanism and clinical recommendation.

```python
import requests

BASE = "https://ddinter.scbdd.com/api"

def get_interaction_detail(interaction_id):
    """Get full details for a specific interaction by its DDInter interaction ID."""
    r = requests.get(f"{BASE}/interaction/{interaction_id}/",
                     params={"format": "json"},
                     timeout=15)
    r.raise_for_status()
    return r.json()

# Example interaction ID (format: DDInter_I_XXXXXX)
interaction_id = "DDInter_I_000001"   # example
try:
    detail = get_interaction_detail(interaction_id)
    print(f"Interaction: {detail.get('interaction_id')}")
    print(f"Drug A: {detail.get('drug_a')}")
    print(f"Drug B: {detail.get('drug_b')}")
    print(f"Severity: {detail.get('level')}")
    print(f"Mechanism: {detail.get('mechanism', 'Not specified')[:200]}")
    print(f"Recommendation: {detail.get('recommendation', 'Not specified')[:200]}")
    print(f"PK type: {detail.get('pharmacokinetic_type', 'N/A')}")
    print(f"PD type: {detail.get('pharmacodynamic_type', 'N/A')}")
except Exception as e:
    print(f"Note: Use a valid interaction ID from get_drug_interactions() results. Error: {e}")
```

### Query 4: Check Interaction Between Two Specific Drugs

Query interactions between exactly two drugs using their DDInter IDs.

```python
import requests

BASE = "https://ddinter.scbdd.com/api"

def check_drug_pair(drug_id_1, drug_id_2):
    """Check interactions between two specific drugs by their DDInter IDs."""
    r = requests.get(f"{BASE}/between/",
                     params={"drug1": drug_id_1, "drug2": drug_id_2, "format": "json"},
                     timeout=15)
    r.raise_for_status()
    return r.json()

def find_drug_id(drug_name):
    """Helper: resolve drug name to DDInter ID."""
    r = requests.get(f"{BASE}/drug/",
                     params={"drug_name": drug_name, "format": "json"},
                     timeout=15)
    r.raise_for_status()
    results = r.json()["results"]
    return results[0]["ddinter_id"] if results else None

# Check warfarin + aspirin interaction
warfarin_id = find_drug_id("warfarin")
aspirin_id = find_drug_id("aspirin")

if warfarin_id and aspirin_id:
    interactions = check_drug_pair(warfarin_id, aspirin_id)
    count = interactions.get("count", 0)
    print(f"Warfarin + Aspirin: {count} interaction(s) found")
    for ix in interactions.get("results", []):
        print(f"  Severity: {ix.get('level')}")
        print(f"  Mechanism: {ix.get('mechanism', 'N/A')[:200]}")
        print(f"  Recommendation: {ix.get('recommendation', 'N/A')[:200]}")
else:
    print(f"Could not resolve drug IDs: warfarin={warfarin_id}, aspirin={aspirin_id}")
```

### Query 5: Filter Interactions by Severity Level

Retrieve only high-severity (major) interactions for a drug — essential for rapid clinical risk screening.

```python
import requests
import pandas as pd

BASE = "https://ddinter.scbdd.com/api"

def get_major_interactions(drug_id):
    """Get only major-severity interactions for a drug."""
    all_interactions = []
    r = requests.get(f"{BASE}/interaction/",
                     params={"drug_id": drug_id, "format": "json", "page_size": 200},
                     timeout=20)
    r.raise_for_status()
    data = r.json()
    all_interactions.extend(data.get("results", []))

    # Filter to major severity
    major = [ix for ix in all_interactions
             if ix.get("level", "").lower() == "major"]
    return major

# Get major interactions for amiodarone (known high-interaction drug)
drug_id = "DDInter_D00023"   # example amiodarone ID; resolve with search_drug()
major_ixs = get_major_interactions(drug_id)
print(f"Major interactions: {len(major_ixs)}")

if major_ixs:
    df = pd.DataFrame(major_ixs)
    # Show drug partners and mechanism type
    for col in ["drug_a", "drug_b", "level", "pharmacokinetic_type"]:
        if col in df.columns:
            print(f"  {col}: {df[col].value_counts().head(3).to_dict()}")
    df.to_csv("amiodarone_major_interactions.csv", index=False)
    print("Saved: amiodarone_major_interactions.csv")
```

### Query 6: Polypharmacy Screening for a Drug List

Screen a medication list for all pairwise major and moderate interactions.

```python
import requests
import time
import itertools
import pandas as pd

BASE = "https://ddinter.scbdd.com/api"

def find_drug_id(drug_name):
    r = requests.get(f"{BASE}/drug/",
                     params={"drug_name": drug_name, "format": "json"},
                     timeout=15)
    r.raise_for_status()
    results = r.json()["results"]
    return (results[0]["ddinter_id"], results[0]["drug_name"]) if results else (None, None)

def check_pair(id1, id2):
    r = requests.get(f"{BASE}/between/",
                     params={"drug1": id1, "drug2": id2, "format": "json"},
                     timeout=15)
    r.raise_for_status()
    return r.json().get("results", [])

# Medication list to screen
medication_names = ["warfarin", "aspirin", "atorvastatin", "metformin", "amiodarone"]

# Resolve to DDInter IDs
id_map = {}
for name in medication_names:
    ddid, resolved_name = find_drug_id(name)
    if ddid:
        id_map[name] = (ddid, resolved_name)
        print(f"  {name:20s} → {ddid}")
    time.sleep(0.3)

# Check all pairs
flagged = []
for (n1, (id1, rn1)), (n2, (id2, rn2)) in itertools.combinations(id_map.items(), 2):
    ixs = check_pair(id1, id2)
    for ix in ixs:
        level = ix.get("level", "unknown")
        if level.lower() in ("major", "moderate"):
            flagged.append({
                "drug_1": rn1,
                "drug_2": rn2,
                "severity": level,
                "mechanism": ix.get("mechanism", "")[:100],
            })
    time.sleep(0.3)

df = pd.DataFrame(flagged)
print(f"\nFlagged interactions: {len(df)}")
if not df.empty:
    print(df.to_string(index=False))
    df.to_csv("polypharmacy_screening.csv", index=False)
    print("Saved: polypharmacy_screening.csv")
```

### Query 7: Visualize Interaction Network

Build and visualize a drug-drug interaction network for a set of drugs, with edges colored by severity.

```python
import requests
import time
import itertools
import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt

BASE = "https://ddinter.scbdd.com/api"

def find_drug_id(drug_name):
    r = requests.get(f"{BASE}/drug/",
                     params={"drug_name": drug_name, "format": "json"},
                     timeout=15)
    r.raise_for_status()
    results = r.json()["results"]
    return (results[0]["ddinter_id"], results[0]["drug_name"]) if results else (None, None)

def check_pair(id1, id2):
    r = requests.get(f"{BASE}/between/",
                     params={"drug1": id1, "drug2": id2, "format": "json"},
                     timeout=15)
    r.raise_for_status()
    return r.json().get("results", [])

SEVERITY_COLORS = {"major": "#D32F2F", "moderate": "#F57C00", "minor": "#388E3C"}

# Drug list
drugs = ["warfarin", "aspirin", "atorvastatin", "fluconazole", "amiodarone"]
id_map = {}
for name in drugs:
    ddid, rname = find_drug_id(name)
    if ddid:
        id_map[name] = (ddid, rname)
    time.sleep(0.3)

# Build network
G = nx.Graph()
for name, (ddid, rname) in id_map.items():
    G.add_node(rname)

edge_colors = []
for (n1, (id1, rn1)), (n2, (id2, rn2)) in itertools.combinations(id_map.items(), 2):
    ixs = check_pair(id1, id2)
    for ix in ixs:
        level = ix.get("level", "minor").lower()
        G.add_edge(rn1, rn2, severity=level, weight=3 if level == "major" else 1)
    time.sleep(0.3)

# Visualize
fig, ax = plt.subplots(figsize=(9, 7))
pos = nx.spring_layout(G, seed=42, k=2)

for level, color in SEVERITY_COLORS.items():
    edges = [(u, v) for u, v, d in G.edges(data=True) if d.get("severity") == level]
    if edges:
        width = 4 if level == "major" else 2
        nx.draw_networkx_edges(G, pos, edgelist=edges, edge_color=color, width=width, alpha=0.8, ax=ax)

nx.draw_networkx_nodes(G, pos, node_color="#1565C0", node_size=1200, alpha=0.9, ax=ax)
nx.draw_networkx_labels(G, pos, font_color="white", font_size=8, font_weight="bold", ax=ax)

# Legend
from matplotlib.patches import Patch
legend = [Patch(color=c, label=l.capitalize()) for l, c in SEVERITY_COLORS.items()]
ax.legend(handles=legend, title="Severity", loc="upper right")
ax.set_title("Drug-Drug Interaction Network\n(DDInter)")
ax.axis("off")
plt.tight_layout()
plt.savefig("ddi_network.png", dpi=150, bbox_inches="tight")
print(f"Saved: ddi_network.png  ({G.number_of_nodes()} drugs, {G.number_of_edges()} interactions)")
```

## Key Concepts

### Severity Classification

DDInter classifies interactions into three severity levels, following established clinical pharmacology standards:

| Severity | Code | Clinical Meaning | Action |
|----------|------|-----------------|--------|
| **Major** | `major` | Potentially life-threatening or causing permanent damage | Avoid combination; use alternative |
| **Moderate** | `moderate` | May cause clinical deterioration; increased monitoring required | Use with caution; monitor closely |
| **Minor** | `minor` | Limited clinical effects; interaction is documented but rarely significant | Generally safe; monitor if symptomatic |

### Mechanism Types

Interactions are classified by mechanism:

- **Pharmacokinetic (PK)**: One drug affects the absorption, distribution, metabolism, or excretion (ADME) of the other (e.g., CYP enzyme inhibition)
- **Pharmacodynamic (PD)**: Drugs have additive, synergistic, or antagonistic effects at the pharmacological target level (e.g., additive bleeding risk)
- **Mixed**: Both PK and PD mechanisms contribute

### Drug Identification

DDInter uses its own sequential identifier scheme (e.g., `DDInter_D00001` for Warfarin). There is no direct mapping to ChEMBL IDs, PubChem CIDs, or RxCUI without a prior name search. Always resolve drug names to DDInter IDs using the `/drug/` endpoint before querying interactions.

## Common Workflows

### Workflow 1: Comprehensive DDI Profile for a Drug

**Goal**: Retrieve all interactions for a drug, stratify by severity, and export a structured report.

```python
import requests
import time
import pandas as pd

BASE = "https://ddinter.scbdd.com/api"

def find_drug_id(name):
    r = requests.get(f"{BASE}/drug/",
                     params={"drug_name": name, "format": "json"},
                     timeout=15)
    r.raise_for_status()
    res = r.json()["results"]
    return (res[0]["ddinter_id"], res[0]["drug_name"]) if res else (None, None)

def get_all_interactions(drug_id, page_size=200):
    all_results = []
    url = f"{BASE}/interaction/"
    params = {"drug_id": drug_id, "format": "json", "page_size": page_size}
    while url:
        r = requests.get(url, params=params, timeout=30)
        r.raise_for_status()
        data = r.json()
        all_results.extend(data.get("results", []))
        url = data.get("next")
        params = {}
    return all_results

# Build DDI profile for clopidogrel
drug_name = "clopidogrel"
drug_id, resolved_name = find_drug_id(drug_name)

if drug_id:
    print(f"Drug: {resolved_name} ({drug_id})")
    ixs = get_all_interactions(drug_id)
    df = pd.DataFrame(ixs)

    print(f"Total interactions: {len(df)}")
    if "level" in df.columns:
        print("\nSeverity breakdown:")
        for level, grp in df.groupby("level"):
            print(f"  {level:15s}: {len(grp):4d} interactions")

        # Major interactions table
        major = df[df["level"].str.lower() == "major"].copy()
        print(f"\nMajor interactions ({len(major)}):")
        for _, row in major.head(10).iterrows():
            partner = row.get("drug_b") if row.get("drug_a") == resolved_name else row.get("drug_a")
            mech = str(row.get("mechanism", ""))[:80]
            print(f"  + {partner}: {mech}")

    df.to_csv(f"{drug_name}_ddi_profile.csv", index=False)
    print(f"\nSaved: {drug_name}_ddi_profile.csv")
```

### Workflow 2: Pairwise Interaction Matrix for a Drug Panel

**Goal**: Build a severity matrix showing all pairwise interactions between a curated drug panel — useful for clinical pharmacology and formulary review.

```python
import requests
import time
import itertools
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

BASE = "https://ddinter.scbdd.com/api"

SEVERITY_SCORE = {"major": 3, "moderate": 2, "minor": 1, "none": 0}

def find_drug_id(name):
    r = requests.get(f"{BASE}/drug/",
                     params={"drug_name": name, "format": "json"},
                     timeout=15)
    r.raise_for_status()
    res = r.json()["results"]
    return (res[0]["ddinter_id"], res[0]["drug_name"]) if res else (None, None)

def check_pair(id1, id2):
    r = requests.get(f"{BASE}/between/",
                     params={"drug1": id1, "drug2": id2, "format": "json"},
                     timeout=15)
    r.raise_for_status()
    return r.json().get("results", [])

# Drug panel
drug_names = ["warfarin", "aspirin", "atorvastatin", "fluconazole", "metformin"]
id_map = {}
for name in drug_names:
    ddid, rname = find_drug_id(name)
    if ddid:
        id_map[name] = (ddid, rname)
    time.sleep(0.3)

resolved = {name: rname for name, (ddid, rname) in id_map.items()}
n = len(id_map)
names = list(id_map.keys())
rnames = [resolved[n] for n in names]

# Build matrix
matrix = np.zeros((n, n), dtype=int)
for i, (n1, (id1, _)) in enumerate(id_map.items()):
    for j, (n2, (id2, _)) in enumerate(id_map.items()):
        if i < j:
            ixs = check_pair(id1, id2)
            if ixs:
                worst = max(SEVERITY_SCORE.get(ix.get("level", "none").lower(), 0) for ix in ixs)
                matrix[i, j] = matrix[j, i] = worst
            time.sleep(0.3)

# Heatmap
fig, ax = plt.subplots(figsize=(7, 6))
im = ax.imshow(matrix, cmap="RdYlGn_r", vmin=0, vmax=3)
ax.set_xticks(range(n))
ax.set_yticks(range(n))
ax.set_xticklabels(rnames, rotation=30, ha="right", fontsize=9)
ax.set_yticklabels(rnames, fontsize=9)
for i in range(n):
    for j in range(n):
        text = ["None", "Minor", "Mod", "Major"][matrix[i, j]]
        ax.text(j, i, text, ha="center", va="center", fontsize=7)
plt.colorbar(im, ax=ax, label="Severity (0=None, 3=Major)")
ax.set_title("Drug-Drug Interaction Severity Matrix\n(DDInter)")
plt.tight_layout()
plt.savefig("ddi_severity_matrix.png", dpi=150, bbox_inches="tight")
print("Saved: ddi_severity_matrix.png")
```

## Key Parameters

| Parameter | Endpoint | Default | Range / Options | Effect |
|-----------|----------|---------|-----------------|--------|
| `drug_name` | `/drug/` | — | any drug name string | Search term for drug name lookup |
| `drug_id` | `/interaction/` | — | `DDInter_DXXXXX` string | DDInter drug ID for interaction queries |
| `drug1`, `drug2` | `/between/` | — | `DDInter_DXXXXX` strings | Both required to check a specific drug pair |
| `format` | all endpoints | `json` | `json` | Response format; JSON only via API |
| `page_size` | `/interaction/`, `/drug/` | `10` | positive integer | Results per page; use `200` for bulk retrieval |
| `level` | response field | — | `major`, `moderate`, `minor` | Interaction severity; filter client-side |
| `pharmacokinetic_type` | response field | — | `PK`, `PD`, `mixed` | Mechanism category |

## Best Practices

1. **Always resolve drug names to DDInter IDs first**: The API does not accept free-text drug names in interaction queries. Use `/drug/?drug_name=` to obtain the `ddinter_id`, then pass it to `/interaction/` or `/between/`.

2. **Handle pagination for complete interaction lists**: The default page returns at most 10 results. Drugs like warfarin or amiodarone have hundreds of interactions — iterate `next` URLs until `null`:
   ```python
   while url:
       data = requests.get(url, params=params).json()
       results.extend(data["results"])
       url = data.get("next")
       params = {}   # clear params after first request
   ```

3. **Use `check_pair()` for targeted queries, `get_interactions()` for full profiles**: The `/between/` endpoint is faster when you need one pair. The `/interaction/` endpoint is needed for comprehensive DDI profiling.

4. **Add `time.sleep(0.3)` in batch loops**: DDInter has no published rate limits, but polite delays prevent server-side throttling on this publicly hosted research database.

5. **Filter by severity client-side**: The API does not support server-side severity filtering on the `/interaction/` endpoint. Retrieve all interactions and filter in pandas:
   ```python
   df = pd.DataFrame(interactions)
   major_only = df[df["level"].str.lower() == "major"]
   ```

6. **Cross-reference with clinical databases for decision support**: DDInter provides evidence-based interaction records, but for clinical decisions always verify against current prescribing information in `dailymed-database` and institutional drug interaction tools.

## Common Recipes

### Recipe: Quick Safety Check for a Drug Pair

When to use: Rapid single-pair interaction lookup before combining two drugs.

```python
import requests

BASE = "https://ddinter.scbdd.com/api"

def quick_check(drug1_name, drug2_name):
    """Check interaction between two drugs by name. Returns severity or 'No interaction found'."""
    def get_id(name):
        r = requests.get(f"{BASE}/drug/",
                         params={"drug_name": name, "format": "json"},
                         timeout=15)
        r.raise_for_status()
        results = r.json()["results"]
        return (results[0]["ddinter_id"], results[0]["drug_name"]) if results else (None, name)

    id1, rn1 = get_id(drug1_name)
    id2, rn2 = get_id(drug2_name)

    if not id1 or not id2:
        return f"Drug not found: {drug1_name if not id1 else drug2_name}"

    r = requests.get(f"{BASE}/between/",
                     params={"drug1": id1, "drug2": id2, "format": "json"},
                     timeout=15)
    r.raise_for_status()
    ixs = r.json().get("results", [])

    if not ixs:
        return f"{rn1} + {rn2}: No interaction found in DDInter"

    worst = max(ixs, key=lambda x: {"major": 3, "moderate": 2, "minor": 1}.get(x.get("level", "minor").lower(), 0))
    return f"{rn1} + {rn2}: {worst.get('level', 'unknown').upper()} — {worst.get('mechanism', 'N/A')[:120]}"

print(quick_check("warfarin", "aspirin"))
print(quick_check("metformin", "atorvastatin"))
print(quick_check("warfarin", "fluconazole"))
```

### Recipe: Count Interactions by Severity for Multiple Drugs

When to use: Generate a summary table comparing DDI burden across multiple drugs.

```python
import requests
import time
import pandas as pd

BASE = "https://ddinter.scbdd.com/api"

def get_severity_summary(drug_name):
    """Return severity counts (major/moderate/minor) for a drug."""
    r = requests.get(f"{BASE}/drug/",
                     params={"drug_name": drug_name, "format": "json"},
                     timeout=15)
    r.raise_for_status()
    results = r.json()["results"]
    if not results:
        return None
    drug_id = results[0]["ddinter_id"]

    # Get all interactions
    all_ixs = []
    url = f"{BASE}/interaction/"
    params = {"drug_id": drug_id, "format": "json", "page_size": 200}
    while url:
        r2 = requests.get(url, params=params, timeout=20)
        r2.raise_for_status()
        data = r2.json()
        all_ixs.extend(data.get("results", []))
        url = data.get("next")
        params = {}

    from collections import Counter
    counts = Counter(ix.get("level", "unknown").lower() for ix in all_ixs)
    return {
        "drug": results[0]["drug_name"],
        "total": len(all_ixs),
        "major": counts.get("major", 0),
        "moderate": counts.get("moderate", 0),
        "minor": counts.get("minor", 0),
    }

drugs = ["warfarin", "amiodarone", "metformin", "atorvastatin"]
records = []
for name in drugs:
    summary = get_severity_summary(name)
    if summary:
        records.append(summary)
        print(f"  {name:20s} total={summary['total']:4d}  major={summary['major']:3d}  mod={summary['moderate']:3d}  minor={summary['minor']:3d}")
    time.sleep(0.5)

df = pd.DataFrame(records)
df = df.sort_values("major", ascending=False)
df.to_csv("ddi_severity_summary.csv", index=False)
print(f"\nSaved: ddi_severity_summary.csv")
```

### Recipe: Export All Major Interactions Across a Drug List

When to use: Build a prioritized interaction alert list for formulary review or clinical decision support.

```python
import requests
import time
import pandas as pd

BASE = "https://ddinter.scbdd.com/api"

drug_list = ["warfarin", "aspirin", "clopidogrel", "amiodarone", "fluconazole"]
all_major = []

for drug_name in drug_list:
    r = requests.get(f"{BASE}/drug/",
                     params={"drug_name": drug_name, "format": "json"}, timeout=15)
    r.raise_for_status()
    res = r.json()["results"]
    if not res:
        continue
    drug_id, resolved = res[0]["ddinter_id"], res[0]["drug_name"]

    r2 = requests.get(f"{BASE}/interaction/",
                      params={"drug_id": drug_id, "format": "json", "page_size": 200}, timeout=30)
    r2.raise_for_status()
    for ix in r2.json().get("results", []):
        if ix.get("level", "").lower() == "major":
            all_major.append({
                "query_drug": resolved,
                "interaction_partner": ix.get("drug_a") if ix.get("drug_b") == resolved else ix.get("drug_b"),
                "severity": "major",
                "mechanism": str(ix.get("mechanism", ""))[:200],
                "recommendation": str(ix.get("recommendation", ""))[:200],
            })
    time.sleep(0.5)

df = pd.DataFrame(all_major).drop_duplicates()
print(f"Total major interactions across {len(drug_list)} drugs: {len(df)}")
df.to_csv("major_interactions_alert_list.csv", index=False)
print("Saved: major_interactions_alert_list.csv")
```

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| `404 Not Found` on `/interaction/` | Invalid or malformed DDInter drug ID | Re-query `/drug/?drug_name=` to get a valid ID; format must be `DDInter_DXXXXX` |
| `count: 0` from `/drug/` search | Drug name not matching DDInter nomenclature | Try INN name (e.g., `"acetylsalicylic acid"` not `"aspirin"`); try partial name |
| Interaction list is incomplete | Default `page_size=10` truncates results | Set `page_size=200` and iterate `next` URLs until `null` |
| `/between/` returns empty results | Drug pair has no curated interaction in DDInter | Absence does not mean no interaction — check `dailymed-database` label text |
| `ConnectionError` or timeout | Server temporarily unavailable | Retry with `timeout=30`; use exponential backoff for bulk requests |
| Duplicate interactions in bulk export | Same interaction appears from both drug perspectives | Deduplicate by `(drug_a, drug_b)` pair after sorting drug IDs alphabetically |
| `JSONDecodeError` | Server returned non-JSON error page | Check HTTP status code; `r.raise_for_status()` before parsing |

## Related Skills

- `dailymed-database` — FDA-approved drug label text including drug interaction sections (unstructured)
- `fda-database` — openFDA for adverse event reports and drug recall data
- `drugbank-database-access` — DrugBank local XML with structured DDI and target data
- `clinpgx-database` — PharmGKB for drug-gene (pharmacogenomics) interaction data
- `pytdc-therapeutics-data-commons` — TDC DDI benchmark datasets for ML model training

## References

- [DDInter Database](https://ddinter.scbdd.com/) — official web interface and documentation
- [DDInter REST API](https://ddinter.scbdd.com/api/) — browsable API with endpoint documentation
- [Xiong et al., Nucleic Acids Research 2022](https://doi.org/10.1093/nar/gkab880) — DDInter database paper describing curation methodology, data sources, and coverage
- [WHO INN Drug Names](https://www.who.int/teams/health-product-and-policy-standards/inn) — International Nonproprietary Names for resolving drug name variants
