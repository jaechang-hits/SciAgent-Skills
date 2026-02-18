---
name: "dailymed-database"
description: "Query FDA-approved drug labeling from DailyMed (NLM) via REST API. Search structured product labels (SPLs) by drug name, NDC code, set ID, or RxCUI. Retrieve indications, contraindications, dosage, warnings, adverse reactions, and packaging information. No authentication required. For adverse event reports use fda-database; for drug-drug interactions use ddinter-database."
license: "CC0-1.0"
---

# DailyMed Drug Label Database

## Overview

DailyMed is the National Library of Medicine's official repository of FDA-approved drug labeling information, containing 140,000+ structured product labels (SPLs) for prescription drugs, OTC medications, biologics, and vaccines. The REST API (v2) provides structured JSON/XML access to the full label content including indications, dosage, warnings, contraindications, adverse reactions, and packaging data — with no authentication required.

## When to Use

- Retrieving official FDA-approved prescribing information for a drug by name, NDC code, or set ID
- Extracting structured label sections (indications, warnings, dosage, adverse reactions) for pharmacological research
- Looking up all marketed formulations of an active ingredient with packaging and NDC codes
- Cross-referencing drug labels using RxCUI identifiers from RxNorm integration
- Building drug information pipelines that require authoritative FDA label content (not user-reported data)
- Comparing label content across brand name and generic formulations of the same drug
- For adverse event reports from FAERS, use `fda-database` instead; DailyMed contains label text, not post-market safety signals
- For drug-drug interaction severity data, use `ddinter-database`; DailyMed label text is unstructured for interactions

## Prerequisites

- **Python packages**: `requests`, `pandas`, `matplotlib`
- **Data requirements**: drug names, NDC codes, set IDs, or RxCUI identifiers
- **Environment**: internet connection; no API key required
- **Rate limits**: no officially published limit; ~100 requests/minute is safe for polite access; add `time.sleep(0.3)` in batch loops

```bash
pip install requests pandas matplotlib
```

## Quick Start

```python
import requests

BASE = "https://dailymed.nlm.nih.gov/dailymed/services/v2"

# Search drug labels by name
r = requests.get(f"{BASE}/spls.json", params={"drug_name": "metformin", "pagesize": 5})
r.raise_for_status()
data = r.json()
print(f"Total labels found: {data['metadata']['total_elements']}")
for spl in data["data"][:3]:
    print(f"  {spl['title']!r:60s}  setid={spl['setid']}")
```

## Core API

### Query 1: Search Drug Labels by Name

Search for structured product labels (SPLs) using drug name. Returns paginated list of matching labels with set IDs.

```python
import requests
import pandas as pd

BASE = "https://dailymed.nlm.nih.gov/dailymed/services/v2"

def search_spls(drug_name, pagesize=20, page=1):
    """Search DailyMed SPLs by drug name. Returns list of label summaries."""
    r = requests.get(f"{BASE}/spls.json",
                     params={"drug_name": drug_name, "pagesize": pagesize, "page": page},
                     timeout=15)
    r.raise_for_status()
    return r.json()

result = search_spls("atorvastatin", pagesize=10)
meta = result["metadata"]
print(f"Search: 'atorvastatin' → {meta['total_elements']} labels across {meta['total_pages']} pages")

df = pd.DataFrame(result["data"])
print(df[["setid", "title", "published_date"]].to_string(index=False))
# setid                                  title                                   published_date
# 8f6c7c7c-...  ATORVASTATIN CALCIUM tablet                               2024-03-15
# a4b7d3e1-...  ATORVASTATIN CALCIUM tablet, film coated                  2023-11-20
```

### Query 2: Retrieve Full Label by Set ID

Fetch the complete structured product label for a specific drug using its set ID. Returns all label sections including indications, warnings, dosage, and adverse reactions.

```python
import requests

BASE = "https://dailymed.nlm.nih.gov/dailymed/services/v2"

def get_spl(setid):
    """Retrieve full SPL document by set ID. Returns label metadata and XML/JSON."""
    r = requests.get(f"{BASE}/spls/{setid}.json", timeout=20)
    r.raise_for_status()
    return r.json()

# Use a known set ID from search results
setid = "8f6c7c7c-1f7f-4f1a-af86-8b2eef2a8b2c"   # example atorvastatin label
label = get_spl(setid)
data = label["data"]

print(f"Title: {data.get('title')}")
print(f"Set ID: {data.get('setid')}")
print(f"Published: {data.get('published_date')}")
print(f"Version: {data.get('version')}")

# Access structured sections
if "sections" in data:
    sections = data["sections"]
    print(f"\nLabel sections ({len(sections)} total):")
    for sec in sections[:5]:
        print(f"  [{sec.get('loinc_code', 'N/A')}] {sec.get('title', 'Untitled')}")
```

### Query 3: Search by NDC Code

Look up drug labels by National Drug Code (NDC) — useful when you have a product barcode or dispensing record.

```python
import requests

BASE = "https://dailymed.nlm.nih.gov/dailymed/services/v2"

def search_by_ndc(ndc_code):
    """Find SPL by NDC code (formatted as XXXXX-XXXX-XX or without dashes)."""
    r = requests.get(f"{BASE}/spls.json",
                     params={"ndc": ndc_code},
                     timeout=15)
    r.raise_for_status()
    return r.json()

# NDC for Lipitor 10mg (atorvastatin)
result = search_by_ndc("0071-0155-23")
if result["data"]:
    spl = result["data"][0]
    print(f"Drug: {spl['title']}")
    print(f"Set ID: {spl['setid']}")
    print(f"Published: {spl['published_date']}")
else:
    print("No label found for this NDC")
```

### Query 4: Retrieve Packaging Information

Get detailed packaging data (NDC codes, package types, quantities) for a specific drug label by set ID.

```python
import requests
import pandas as pd

BASE = "https://dailymed.nlm.nih.gov/dailymed/services/v2"

def get_packaging(setid):
    """Retrieve packaging information for a label (NDC codes, dosage forms, quantities)."""
    r = requests.get(f"{BASE}/spls/{setid}/packaging.json", timeout=15)
    r.raise_for_status()
    return r.json()

setid = "8f6c7c7c-1f7f-4f1a-af86-8b2eef2a8b2c"   # example setid
pkg = get_packaging(setid)

if pkg["data"]:
    packages = pkg["data"]
    print(f"Packaging variants: {len(packages)}")
    df = pd.DataFrame(packages)
    # Common fields: ndc, dosage_form, route, marketing_status
    for col in ["ndc", "dosage_form", "route", "marketing_status"]:
        if col in df.columns:
            print(f"\n{col.upper()}:")
            print(df[col].value_counts().head(5))
```

### Query 5: Look Up by RxCUI

Retrieve drug labels using RxNorm Concept Unique Identifier (RxCUI) for integration with RxNorm-based clinical systems.

```python
import requests
import time

BASE = "https://dailymed.nlm.nih.gov/dailymed/services/v2"

def get_spls_by_rxcui(rxcui):
    """Get all SPLs associated with an RxCUI. Returns list of set IDs and titles."""
    r = requests.get(f"{BASE}/rxcuis/{rxcui}/spls.json", timeout=15)
    r.raise_for_status()
    return r.json()

# RxCUI for atorvastatin: 83367
rxcui = "83367"
result = get_spls_by_rxcui(rxcui)
print(f"SPLs for RxCUI {rxcui} (atorvastatin):")
for spl in result["data"][:5]:
    print(f"  {spl['setid']} | {spl['title'][:70]}")
print(f"  Total: {result['metadata']['total_elements']} labels")
```

### Query 6: Search Drug Names Index

List all standardized drug names in DailyMed — useful for name normalization and autocomplete in drug lookup pipelines.

```python
import requests

BASE = "https://dailymed.nlm.nih.gov/dailymed/services/v2"

def search_drug_names(query, pagesize=20):
    """Search the DailyMed drug name index for name normalization."""
    r = requests.get(f"{BASE}/drugnames.json",
                     params={"drug_name": query, "pagesize": pagesize},
                     timeout=15)
    r.raise_for_status()
    return r.json()

result = search_drug_names("metformin")
print(f"Drug name matches for 'metformin': {result['metadata']['total_elements']}")
for entry in result["data"][:8]:
    print(f"  {entry['drug_name']}")
# METFORMIN HYDROCHLORIDE
# METFORMIN HYDROCHLORIDE AND SITAGLIPTIN PHOSPHATE
# METFORMIN HYDROCHLORIDE AND SAXAGLIPTIN
```

### Query 7: Batch Label Section Extraction

Extract specific label sections (e.g., indications, warnings) from multiple drug labels for comparative analysis.

```python
import requests
import time
import pandas as pd

BASE = "https://dailymed.nlm.nih.gov/dailymed/services/v2"

# LOINC codes for common SPL sections
SECTION_LOINC = {
    "34067-9": "Indications and Usage",
    "34068-7": "Dosage and Administration",
    "34071-1": "Warnings",
    "34084-4": "Adverse Reactions",
    "34070-3": "Contraindications",
    "43685-7": "Warnings and Precautions",
}

def get_label_sections(setid):
    """Extract structured sections from an SPL by set ID."""
    r = requests.get(f"{BASE}/spls/{setid}.json", timeout=20)
    r.raise_for_status()
    data = r.json()["data"]
    sections = {}
    for sec in data.get("sections", []):
        loinc = sec.get("loinc_code")
        if loinc in SECTION_LOINC:
            sections[SECTION_LOINC[loinc]] = sec.get("text", "")
    return sections

# Get indications for two statin labels
statins = [
    ("Atorvastatin", "8f6c7c7c-1f7f-4f1a-af86-8b2eef2a8b2c"),
    ("Rosuvastatin", "a3b2c4d5-1234-5678-abcd-ef0123456789"),   # example
]
records = []
for drug_name, setid in statins:
    try:
        sections = get_label_sections(setid)
        records.append({"drug": drug_name, "indications_length": len(sections.get("Indications and Usage", ""))})
    except Exception as e:
        print(f"Warning: {drug_name} failed — {e}")
    time.sleep(0.3)

df = pd.DataFrame(records)
print(df.to_string(index=False))
```

## Key Concepts

### Structured Product Label (SPL) and Set ID

An SPL is the official FDA-approved drug label in XML format, structured using Health Level 7 (HL7) Clinical Document Architecture (CDA). Each unique drug product label has a globally unique **set ID** (UUID format). Multiple versions of the same label share the same set ID but have different version numbers. Always use the most recent published version for current prescribing information.

### LOINC Section Codes

DailyMed SPLs use standardized LOINC codes to identify label sections, enabling consistent programmatic extraction across all labels:

| LOINC Code | Section Name |
|------------|-------------|
| `34067-9` | Indications and Usage |
| `34068-7` | Dosage and Administration |
| `34070-3` | Contraindications |
| `34071-1` | Warnings |
| `43685-7` | Warnings and Precautions |
| `34084-4` | Adverse Reactions |
| `34073-7` | Drug Interactions |
| `34076-0` | Patient Counseling Information |
| `42229-5` | Mechanism of Action |
| `34069-5` | How Supplied/Storage |

### NDC Code Format

National Drug Codes (NDCs) identify drug products with a three-segment numeric format: `labeler-product-package` (e.g., `0071-0155-23`). NDCs can also appear without dashes in some systems. DailyMed accepts both formats in API queries.

## Common Workflows

### Workflow 1: Drug Label Comparison by Active Ingredient

**Goal**: Retrieve and compare label content for all formulations of an active ingredient — useful for generic vs. brand name comparison.

```python
import requests
import time
import pandas as pd

BASE = "https://dailymed.nlm.nih.gov/dailymed/services/v2"

def search_spls(drug_name, pagesize=50):
    r = requests.get(f"{BASE}/spls.json",
                     params={"drug_name": drug_name, "pagesize": pagesize},
                     timeout=15)
    r.raise_for_status()
    return r.json()

def get_packaging(setid):
    r = requests.get(f"{BASE}/spls/{setid}/packaging.json", timeout=15)
    r.raise_for_status()
    return r.json()

# Search for all metformin labels
result = search_spls("metformin", pagesize=20)
labels = result["data"]
print(f"Found {len(labels)} metformin labels")

rows = []
for label in labels[:10]:   # limit for demo
    setid = label["setid"]
    try:
        pkg = get_packaging(setid)
        for item in pkg["data"][:2]:
            rows.append({
                "title": label["title"][:60],
                "setid": setid,
                "ndc": item.get("ndc"),
                "dosage_form": item.get("dosage_form"),
                "route": item.get("route"),
                "marketing_status": item.get("marketing_status"),
                "published_date": label.get("published_date"),
            })
    except Exception as e:
        print(f"Skipping {setid}: {e}")
    time.sleep(0.3)

df = pd.DataFrame(rows)
print(f"\nFormulations with packaging data: {len(df)}")
print(df[["title", "dosage_form", "route", "marketing_status"]].drop_duplicates().to_string(index=False))
df.to_csv("metformin_formulations.csv", index=False)
print("\nSaved: metformin_formulations.csv")
```

### Workflow 2: Extract Warnings and Adverse Reactions for Safety Analysis

**Goal**: Systematically extract structured warning and adverse reaction text from a set of drug labels for pharmacovigilance research.

```python
import requests
import time
import pandas as pd

BASE = "https://dailymed.nlm.nih.gov/dailymed/services/v2"

TARGET_SECTIONS = {
    "34071-1": "Warnings",
    "43685-7": "Warnings_and_Precautions",
    "34084-4": "Adverse_Reactions",
    "34070-3": "Contraindications",
}

def search_and_get_sections(drug_name, max_labels=5):
    """Search for labels and extract safety-relevant sections."""
    search_r = requests.get(f"{BASE}/spls.json",
                            params={"drug_name": drug_name, "pagesize": max_labels},
                            timeout=15)
    search_r.raise_for_status()
    labels = search_r.json()["data"][:max_labels]

    records = []
    for label in labels:
        setid = label["setid"]
        try:
            label_r = requests.get(f"{BASE}/spls/{setid}.json", timeout=20)
            label_r.raise_for_status()
            spl_data = label_r.json()["data"]

            row = {"drug_name": drug_name, "title": label["title"][:80], "setid": setid}
            for loinc, col in TARGET_SECTIONS.items():
                text = ""
                for sec in spl_data.get("sections", []):
                    if sec.get("loinc_code") == loinc:
                        text = sec.get("text", "")[:500]   # first 500 chars
                        break
                row[col] = text
            records.append(row)
        except Exception as e:
            print(f"  Skipping {setid}: {e}")
        time.sleep(0.3)

    return pd.DataFrame(records)

# Compare safety sections across ACE inhibitor labels
drugs = ["lisinopril", "enalapril"]
all_records = []
for drug in drugs:
    print(f"Processing: {drug}")
    df = search_and_get_sections(drug, max_labels=3)
    all_records.append(df)

combined = pd.concat(all_records, ignore_index=True)
print(f"\nExtracted safety sections: {len(combined)} labels")
print(combined[["drug_name", "title"]].to_string(index=False))
combined.to_csv("ace_inhibitor_safety_sections.csv", index=False)
print("Saved: ace_inhibitor_safety_sections.csv")
```

### Workflow 3: Visualize Label Distribution by Drug Class

**Goal**: Query multiple drugs in a class, count their labeled formulations, and visualize the distribution.

```python
import requests
import time
import pandas as pd
import matplotlib.pyplot as plt

BASE = "https://dailymed.nlm.nih.gov/dailymed/services/v2"

def count_labels(drug_name):
    """Return total SPL count for a drug name."""
    r = requests.get(f"{BASE}/spls.json",
                     params={"drug_name": drug_name, "pagesize": 1},
                     timeout=15)
    r.raise_for_status()
    return r.json()["metadata"]["total_elements"]

# Count labels for common statins
statins = {
    "atorvastatin": "Atorvastatin",
    "rosuvastatin": "Rosuvastatin",
    "simvastatin": "Simvastatin",
    "pravastatin": "Pravastatin",
    "lovastatin": "Lovastatin",
    "fluvastatin": "Fluvastatin",
    "pitavastatin": "Pitavastatin",
}

counts = {}
for query, label in statins.items():
    try:
        counts[label] = count_labels(query)
        print(f"  {label}: {counts[label]} labels")
    except Exception as e:
        print(f"  {label}: error — {e}")
    time.sleep(0.3)

# Visualization
df = pd.DataFrame(list(counts.items()), columns=["Drug", "Label_Count"])
df = df.sort_values("Label_Count", ascending=True)

fig, ax = plt.subplots(figsize=(9, 5))
bars = ax.barh(df["Drug"], df["Label_Count"], color="#2196F3", edgecolor="white")
ax.bar_label(bars, fmt="%d", padding=4, fontsize=9)
ax.set_xlabel("Number of DailyMed SPL Entries")
ax.set_title("DailyMed: FDA Drug Label Count by Statin\n(includes brand + generic formulations)")
ax.set_xlim(0, df["Label_Count"].max() * 1.15)
plt.tight_layout()
plt.savefig("statin_label_counts.png", dpi=150, bbox_inches="tight")
print(f"Saved: statin_label_counts.png  (total labels: {df['Label_Count'].sum()})")
```

## Key Parameters

| Parameter | Endpoint | Default | Range / Options | Effect |
|-----------|----------|---------|-----------------|--------|
| `drug_name` | `/spls`, `/drugnames` | — | any drug name string | Filter labels by drug name (partial match supported) |
| `ndc` | `/spls` | — | NDC code string | Filter labels by National Drug Code |
| `pagesize` | `/spls`, `/drugnames` | `20` | `1`–`100` | Results per page; max 100 |
| `page` | `/spls`, `/drugnames` | `1` | positive integer | Page number for pagination |
| `setid` | `/spls/{setid}`, `/spls/{setid}/packaging` | — | UUID string | Unique label identifier; required for direct access |
| `rxcui` | `/rxcuis/{rxcui}/spls` | — | RxNorm concept ID | Look up labels by RxCUI for clinical system integration |
| `format` | any endpoint | `json` | `json`, `xml` | Response format; JSON is default and preferred |

## Best Practices

1. **Resolve set IDs before batch processing**: Use the `/spls` search to get set IDs, then fetch full labels by set ID. Do not construct set IDs from drug names — they are UUID identifiers assigned by FDA.

2. **Add `time.sleep(0.3)` in batch loops**: DailyMed has no published rate limits but is public NIH infrastructure. Polite delays prevent throttling.
   ```python
   import time
   for drug in drug_list:
       result = search_spls(drug)
       time.sleep(0.3)   # 200 requests/minute safe upper bound
   ```

3. **Use LOINC codes for section extraction, not text parsing**: Label sections are indexed by LOINC code, providing consistent section access across all SPL documents without brittle regex on section headers.

4. **Pagination for comprehensive results**: The default `pagesize=20` may miss formulations. Use `metadata["total_elements"]` to detect if pagination is needed:
   ```python
   meta = result["metadata"]
   total_pages = meta["total_pages"]
   if total_pages > 1:
       for p in range(2, total_pages + 1):
           result = search_spls(drug_name, page=p)
   ```

5. **Prefer RxCUI for clinical integration**: When integrating with clinical systems (EHR, dispensing), use RxCUI-based lookups (`/rxcuis/{rxcui}/spls`) for standardized, unambiguous drug identification.

## Common Recipes

### Recipe: Check if a Drug Has Black Box Warnings

When to use: Quickly determine whether a drug carries the FDA's strongest warning level.

```python
import requests

BASE = "https://dailymed.nlm.nih.gov/dailymed/services/v2"
BLACK_BOX_LOINC = "34066-1"

def has_black_box_warning(setid):
    """Return True and warning text if drug label has a black box (boxed) warning."""
    r = requests.get(f"{BASE}/spls/{setid}.json", timeout=20)
    r.raise_for_status()
    sections = r.json()["data"].get("sections", [])
    for sec in sections:
        if sec.get("loinc_code") == BLACK_BOX_LOINC:
            return True, sec.get("text", "")[:300]
    return False, ""

# Example: check warfarin label
setid = "8b7c3d4e-5678-90ab-cdef-1234567890ab"   # example warfarin setid
has_warning, text = has_black_box_warning(setid)
print(f"Black box warning: {has_warning}")
if has_warning:
    print(f"Warning text (first 300 chars): {text}")
```

### Recipe: Multi-Page Search with All Results

When to use: Retrieve all matching labels for a drug when total count exceeds one page.

```python
import requests
import time

BASE = "https://dailymed.nlm.nih.gov/dailymed/services/v2"

def search_all_spls(drug_name, pagesize=100, delay=0.3):
    """Retrieve all SPLs for a drug name across multiple pages."""
    all_labels = []
    page = 1
    while True:
        r = requests.get(f"{BASE}/spls.json",
                         params={"drug_name": drug_name, "pagesize": pagesize, "page": page},
                         timeout=15)
        r.raise_for_status()
        data = r.json()
        all_labels.extend(data["data"])
        if page >= data["metadata"]["total_pages"]:
            break
        page += 1
        time.sleep(delay)
    return all_labels

labels = search_all_spls("ibuprofen")
print(f"Total ibuprofen labels: {len(labels)}")
```

### Recipe: Export Label Summary to CSV

When to use: Build a flat reference table of drug labels for offline analysis.

```python
import requests
import pandas as pd

BASE = "https://dailymed.nlm.nih.gov/dailymed/services/v2"

def export_drug_labels(drug_name, pagesize=50):
    """Export label summaries for a drug name to DataFrame."""
    r = requests.get(f"{BASE}/spls.json",
                     params={"drug_name": drug_name, "pagesize": pagesize},
                     timeout=15)
    r.raise_for_status()
    data = r.json()
    df = pd.DataFrame(data["data"])
    df["drug_query"] = drug_name
    return df, data["metadata"]["total_elements"]

df, total = export_drug_labels("amoxicillin")
print(f"Retrieved {len(df)} of {total} amoxicillin labels")
df[["setid", "title", "published_date"]].to_csv("amoxicillin_labels.csv", index=False)
print(f"Saved: amoxicillin_labels.csv  (columns: {list(df.columns[:5])})")
```

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| `404 Not Found` on `/spls/{setid}` | Invalid or retired set ID | Re-search by drug name to get current set IDs |
| Empty `data` list from search | Drug name not matching any labels | Try shorter name (e.g., `"metformin"` not `"metformin HCl tablets"`); check spelling |
| Missing sections in SPL JSON | Older labels may not have all LOINC-coded sections | Check `len(sections)` before iterating; fall back to XML format for legacy labels |
| `ConnectionError` / timeout | DailyMed server overload | Retry with exponential backoff; increase `timeout=30` |
| Pagination returning duplicates | Page boundary race condition | De-duplicate results by `setid` after all pages collected |
| Packaging endpoint returns empty | Label exists but has no packaging records | Some biologics and vaccines lack packaging data; use label data directly |
| RxCUI lookup returns no results | RxCUI not mapped in DailyMed | Verify RxCUI via RxNorm API before querying; some experimental drugs are not mapped |

## Related Skills

- `fda-database` — openFDA for adverse event reports (FAERS), drug recalls, and enforcement actions
- `ddinter-database` — drug-drug interaction severity and mechanisms from DDInter
- `drugbank-database-access` — comprehensive drug information including targets, pathways, and chemical properties
- `clinicaltrials-database-search` — ClinicalTrials.gov for clinical trial data on drugs

## References

- [DailyMed](https://dailymed.nlm.nih.gov/dailymed/) — official drug label repository (NLM/NIH)
- [DailyMed Web Services API v2](https://dailymed.nlm.nih.gov/dailymed/webservices.cfm) — complete REST API documentation
- [SPL Standard (HL7)](https://www.hl7.org/implement/standards/product_brief.cfm?product_id=4) — Structured Product Labeling standard documentation
- [LOINC Document Ontology](https://loinc.org/document-ontology/) — LOINC codes for SPL section identification
- [NLM DailyMed Overview](https://dailymed.nlm.nih.gov/dailymed/about-dailymed.cfm) — data coverage and update frequency
