---
name: "mouse-phenome-database"
description: "Retrieve quantitative phenotype measurements across inbred mouse strains from the Mouse Phenome Database (MPD) for metabolic, behavioral, and physiological traits. Query strain means and raw individual measurements for body weight, glucose, blood pressure, behavioral assays, and 40+ additional procedures. Use for QTL analysis support, cross-strain phenotype comparison, and identifying mouse models for metabolic or behavioral traits. For mouse gene-disease-phenotype associations use monarch-database; for mouse genome annotations use ensembl-database."
license: "CC-BY-4.0"
---

# mouse-phenome-database

## Overview

The Mouse Phenome Database (MPD) at the Jackson Laboratory catalogs standardized phenotype measurements across inbred, recombinant inbred, and collaborative cross mouse strains. It aggregates data from 700+ projects covering 40+ phenotype categories including body composition, metabolic parameters, cardiovascular, behavioral, and hematological measures. The REST API at `https://phenome.jax.org/api` provides programmatic access to strain summaries, individual animal data, and measurement protocols. No authentication is required; data is freely available under CC-BY-4.0.

## When to Use

- Identifying which inbred strains show extreme phenotypes (highest/lowest body weight, glucose, blood pressure) for selection as experimental models
- Retrieving phenotype data for QTL analysis using BXD, AXB, or DO panel strains
- Comparing strain means and distributions across metabolic traits for a hypothesis about genetic background effects
- Finding published MPD projects measuring a specific trait category (e.g., anxiety behavior, bone density, immune cell counts)
- Downloading individual-level measurement data for statistical modeling or power calculations
- Use `monarch-database` instead when you need disease-gene-phenotype knowledge graph associations (gene ontology, HPO phenotypes, human disease links)
- Use `ensembl-database` instead for genomic coordinate, transcript, and gene annotation lookups for specific mouse genes

## Prerequisites

- **Python packages**: `requests`, `pandas`, `matplotlib`
- **Data requirements**: strain names (e.g., `C57BL/6J`), measure IDs (e.g., `10001`), or project IDs (e.g., `Jaxwest1`)
- **Environment**: internet connection; no API key required
- **Rate limits**: no official published limits; use `time.sleep(0.5)` between batch requests; avoid bursts over 5 requests/second

```bash
pip install requests pandas matplotlib
```

## Quick Start

```python
import requests
import pandas as pd

MPD_API = "https://phenome.jax.org/api"

def mpd_get(endpoint: str, params: dict = None) -> dict:
    """GET request to MPD API; raises on HTTP errors."""
    r = requests.get(f"{MPD_API}{endpoint}", params=params, timeout=30)
    r.raise_for_status()
    return r.json()

# Retrieve strain summary for C57BL/6J
strain_info = mpd_get("/strain/C57BL%2F6J")
print(f"Strain: {strain_info.get('strainname')}")
print(f"Stock number: {strain_info.get('stocknum')}")
print(f"Background: {strain_info.get('category')}")

# Query body weight measurements across strains
result = mpd_get("/pheno/query", params={
    "measnum": "10001",    # body weight measure ID
    "sex": "m",
    "strain": "C57BL/6J,DBA/2J,BALB/cJ"
})
df = pd.DataFrame(result.get("data", []))
print(f"\nBody weight data: {len(df)} records")
if len(df) > 0:
    print(df[["strainname", "sex", "mean", "sd", "n"]].head())
```

## Core API

### Query 1: List Available Measurement Procedures

Browse available phenotype measurement categories and their procedure IDs. Use to discover what data exists before querying.

```python
import requests
import pandas as pd

MPD_API = "https://phenome.jax.org/api"

def mpd_get(endpoint, params=None):
    r = requests.get(f"{MPD_API}{endpoint}", params=params, timeout=30)
    r.raise_for_status()
    return r.json()

# List all available procedures (measurement categories)
procedures = mpd_get("/procedure")
print(f"Total procedures: {len(procedures)}")
df_proc = pd.DataFrame(procedures)
print(df_proc[["procedureid", "procedure", "category"]].head(15).to_string(index=False))
# procedureid  procedure                      category
#      10001   Body weight                    Morphology
#      10002   Body length                    Morphology
#      10010   Fasting plasma glucose         Metabolism
#      10020   Total cholesterol              Metabolism
#      10030   Triglycerides                  Metabolism
```

```python
# Filter procedures by category
metabolism_procs = [p for p in procedures if "Metabol" in p.get("category", "")]
print(f"Metabolic procedures: {len(metabolism_procs)}")
for p in metabolism_procs[:8]:
    print(f"  {p.get('procedureid'):>6}  {p.get('procedure')}")
```

### Query 2: Strain Phenotype Measurements

Query strain-level summary statistics (mean, SD, N) for a specific measurement across strains.

```python
def get_strain_phenotype(measnum: int, sex: str = "m",
                         strains: list = None) -> pd.DataFrame:
    """Retrieve strain-level phenotype summaries for a measure."""
    params = {"measnum": measnum, "sex": sex}
    if strains:
        params["strain"] = ",".join(strains)
    result = mpd_get("/pheno/query", params=params)
    return pd.DataFrame(result.get("data", []))

# Body weight (measnum=10001) in male common strains
common_strains = ["C57BL/6J", "DBA/2J", "BALB/cJ", "A/J", "C3H/HeJ",
                  "FVB/NJ", "SJL/J", "129S1/SvImJ", "NOD/ShiLtJ"]

df = get_strain_phenotype(measnum=10001, sex="m", strains=common_strains)
print(f"Body weight data (male, {len(df)} strain-project combinations):")
if len(df) > 0:
    print(df[["strainname", "mean", "sd", "n"]].sort_values("mean", ascending=False).head(8).to_string(index=False))
# strainname       mean    sd   n
# C57BL/6J         27.4   2.1  24
# NOD/ShiLtJ       25.8   2.8  18
```

### Query 3: Measurement Protocol Details

Retrieve detailed protocol metadata for a measurement including units, age at collection, and measurement description.

```python
def get_measurement_details(measnum: int) -> dict:
    """Retrieve measurement protocol metadata."""
    result = mpd_get(f"/measurement/{measnum}")
    return result

# Get details for fasting plasma glucose (10010)
meta = get_measurement_details(10010)
print(f"Measurement: {meta.get('measnum')} — {meta.get('varname')}")
print(f"Description: {meta.get('description', '')[:120]}")
print(f"Units: {meta.get('units')}")
print(f"Category: {meta.get('category')}")
print(f"Protocol notes: {meta.get('protocoldesc', '')[:150]}")
```

```python
# Batch-fetch metadata for multiple measures
measure_ids = [10001, 10010, 10020, 10030, 10040]
meta_rows = []
for mid in measure_ids:
    m = get_measurement_details(mid)
    meta_rows.append({
        "measnum": m.get("measnum"),
        "varname": m.get("varname"),
        "units": m.get("units"),
        "category": m.get("category"),
    })
df_meta = pd.DataFrame(meta_rows)
print(df_meta.to_string(index=False))
```

### Query 4: Individual Animal Data

Download raw per-animal measurements for a project and measure, enabling distribution analysis and mixed-effects modeling.

```python
def get_individual_data(project_id: str, measnum: int,
                        sex: str = None) -> pd.DataFrame:
    """Retrieve individual-level phenotype measurements for a project."""
    params = {"measnum": measnum}
    if sex:
        params["sex"] = sex
    result = mpd_get(f"/project/{project_id}/data", params=params)
    return pd.DataFrame(result.get("data", []))

# Individual body weight measurements from Jaxwest1 project
df_ind = get_individual_data("Jaxwest1", measnum=10001, sex="m")
print(f"Individual records: {len(df_ind)}")
if len(df_ind) > 0:
    print(f"Columns: {df_ind.columns.tolist()}")
    print(df_ind[["strainname", "sex", "value", "age"]].head(8).to_string(index=False))
    print(f"\nStrain means from raw data:")
    print(df_ind.groupby("strainname")["value"].agg(["mean", "std", "count"]).round(2).head(8))
```

### Query 5: Project Discovery

List available projects (studies) and browse them by phenotype category or trait keyword.

```python
def list_projects(category: str = None, limit: int = 50) -> pd.DataFrame:
    """List MPD projects; optionally filter by category."""
    params = {"limit": limit}
    if category:
        params["category"] = category
    result = mpd_get("/project", params=params)
    records = result if isinstance(result, list) else result.get("data", [])
    return pd.DataFrame(records)

# List all available projects
df_projects = list_projects(limit=200)
print(f"Total projects available: {len(df_projects)}")
if len(df_projects) > 0:
    print(df_projects.columns.tolist())
    print(df_projects.head(5).to_string(index=False))
```

```python
# Search projects by keyword in description
import requests

def search_projects(keyword: str) -> list:
    """Find projects containing a keyword in name or description."""
    r = requests.get(f"{MPD_API}/project", timeout=30)
    r.raise_for_status()
    projects = r.json() if isinstance(r.json(), list) else r.json().get("data", [])
    keyword_lower = keyword.lower()
    return [p for p in projects
            if keyword_lower in str(p.get("projsym", "")).lower()
            or keyword_lower in str(p.get("title", "")).lower()]

glucose_projects = search_projects("glucose")
print(f"Projects with glucose data: {len(glucose_projects)}")
for p in glucose_projects[:5]:
    print(f"  {p.get('projsym'):<15}  {p.get('title', '')[:60]}")
```

### Query 6: Strain Details

Retrieve metadata for a specific inbred strain including stock number, origin, and sub-strain details.

```python
import urllib.parse

def get_strain_info(strain_name: str) -> dict:
    """Retrieve strain metadata from MPD."""
    encoded = urllib.parse.quote(strain_name, safe="")
    result = mpd_get(f"/strain/{encoded}")
    return result

strains_of_interest = ["C57BL/6J", "DBA/2J", "NOD/ShiLtJ"]
for strain in strains_of_interest:
    info = get_strain_info(strain)
    print(f"{strain}:")
    print(f"  Stock: {info.get('stocknum', 'N/A')}")
    print(f"  Category: {info.get('category', 'N/A')}")
    print(f"  Origin: {info.get('origin', 'N/A')[:80]}")
    print()
```

## Key Concepts

### MPD Measure Numbering

Each phenotype measurement has a unique integer `measnum`. Commonly used IDs:

| measnum | Phenotype | Units |
|---------|-----------|-------|
| 10001 | Body weight | g |
| 10002 | Body length (nose-to-rump) | cm |
| 10010 | Fasting plasma glucose | mg/dL |
| 10020 | Total cholesterol | mg/dL |
| 10030 | Triglycerides | mg/dL |
| 10040 | HDL cholesterol | mg/dL |
| 10100 | Systolic blood pressure | mmHg |
| 10200 | Open field total distance | cm |
| 10210 | Open field center time | s |

Use `GET /procedure` to discover the full list, then `GET /measurement/{measnum}` for detailed protocol metadata.

### Strain Name Formatting

MPD uses canonical JAX strain names (e.g., `C57BL/6J`, `DBA/2J`). When passing strain names as URL path parameters, URL-encode the slash: `C57BL%2F6J`. For query parameters in `requests`, use `params={"strain": "C57BL/6J"}` — `requests` handles encoding automatically.

### Project vs Measurement Units

A single `measnum` (phenotype measurement type) may be measured by multiple independent projects using slightly different protocols. When combining data across projects, verify that units and age at measurement are consistent using the `/measurement/{measnum}` and `/project/{project_id}` endpoints.

## Common Workflows

### Workflow 1: Strain Survey for Metabolic Trait Selection

**Goal**: Retrieve and rank inbred strains by fasting glucose, cholesterol, and body weight to select appropriate models for a metabolic study.

```python
import requests
import pandas as pd
import time
import matplotlib.pyplot as plt

MPD_API = "https://phenome.jax.org/api"

def mpd_get(endpoint, params=None):
    r = requests.get(f"{MPD_API}{endpoint}", params=params, timeout=30)
    r.raise_for_status()
    return r.json()

# Target measures: fasting glucose, total cholesterol, body weight
measures = {
    10010: "fasting_glucose_mgdL",
    10020: "total_cholesterol_mgdL",
    10001: "body_weight_g",
}

target_strains = [
    "C57BL/6J", "DBA/2J", "BALB/cJ", "A/J", "C3H/HeJ",
    "FVB/NJ", "SJL/J", "NOD/ShiLtJ", "NZO/HlLtJ", "AKR/J"
]

dfs = []
for measnum, col_name in measures.items():
    result = mpd_get("/pheno/query", params={
        "measnum": measnum,
        "sex": "m",
        "strain": ",".join(target_strains)
    })
    df = pd.DataFrame(result.get("data", []))
    if len(df) > 0:
        strain_means = df.groupby("strainname")["mean"].mean().reset_index()
        strain_means.columns = ["strain", col_name]
        dfs.append(strain_means)
    time.sleep(0.5)

# Merge all traits
from functools import reduce
if dfs:
    df_merged = reduce(lambda a, b: pd.merge(a, b, on="strain", how="outer"), dfs)
    df_merged = df_merged.sort_values("fasting_glucose_mgdL", ascending=False)
    print("Strain metabolic survey (sorted by fasting glucose):")
    print(df_merged.to_string(index=False))
    df_merged.to_csv("strain_metabolic_survey.csv", index=False)

    # Bar chart of fasting glucose by strain
    fig, ax = plt.subplots(figsize=(11, 5))
    df_plot = df_merged.dropna(subset=["fasting_glucose_mgdL"]).sort_values("fasting_glucose_mgdL")
    bars = ax.barh(df_plot["strain"], df_plot["fasting_glucose_mgdL"], color="#E65100")
    ax.bar_label(bars, fmt="%.0f", padding=3, fontsize=9)
    ax.set_xlabel("Fasting Plasma Glucose (mg/dL)")
    ax.set_title("Fasting Glucose by Inbred Strain (MPD, male)")
    plt.tight_layout()
    plt.savefig("mpd_fasting_glucose_strains.png", dpi=150, bbox_inches="tight")
    print("Saved mpd_fasting_glucose_strains.png")
```

### Workflow 2: Multi-Trait Strain Comparison and Correlation

**Goal**: Retrieve body weight and blood pressure for a strain panel, test their correlation, and identify outliers.

```python
import requests
import pandas as pd
import matplotlib.pyplot as plt
import time

MPD_API = "https://phenome.jax.org/api"

def mpd_get(endpoint, params=None):
    r = requests.get(f"{MPD_API}{endpoint}", params=params, timeout=30)
    r.raise_for_status()
    return r.json()

panel_strains = [
    "C57BL/6J", "DBA/2J", "BALB/cJ", "A/J", "C3H/HeJ",
    "FVB/NJ", "SJL/J", "NOD/ShiLtJ", "NZO/HlLtJ", "AKR/J",
    "CBA/J", "C57L/J", "LP/J", "P/J", "SM/J"
]

# Fetch body weight (10001) and systolic blood pressure (10100)
records = {}
for measnum, trait in [(10001, "body_weight_g"), (10100, "systolic_bp_mmHg")]:
    result = mpd_get("/pheno/query", params={
        "measnum": measnum,
        "sex": "m",
        "strain": ",".join(panel_strains)
    })
    df = pd.DataFrame(result.get("data", []))
    if len(df) > 0:
        records[trait] = df.groupby("strainname")["mean"].mean()
    time.sleep(0.5)

if len(records) == 2:
    df_corr = pd.DataFrame(records).dropna()
    print(f"Strains with both measures: {len(df_corr)}")

    # Pearson correlation
    r_val = df_corr["body_weight_g"].corr(df_corr["systolic_bp_mmHg"])
    print(f"Pearson r (weight vs BP): {r_val:.3f}")

    # Scatter plot
    fig, ax = plt.subplots(figsize=(7, 6))
    ax.scatter(df_corr["body_weight_g"], df_corr["systolic_bp_mmHg"],
               s=60, color="#1565C0", alpha=0.8)
    for strain, row in df_corr.iterrows():
        ax.annotate(strain, (row["body_weight_g"], row["systolic_bp_mmHg"]),
                    fontsize=7, ha="left", xytext=(3, 2), textcoords="offset points")
    ax.set_xlabel("Body Weight (g)")
    ax.set_ylabel("Systolic Blood Pressure (mmHg)")
    ax.set_title(f"Body Weight vs Systolic BP Across Strains\n(r={r_val:.3f})")
    plt.tight_layout()
    plt.savefig("mpd_weight_vs_bp.png", dpi=150, bbox_inches="tight")
    print("Saved mpd_weight_vs_bp.png")

    df_corr.reset_index().rename(columns={"strainname": "strain"}).to_csv(
        "mpd_weight_bp_correlation.csv", index=False
    )
```

### Workflow 3: Individual-Level Data Export for QTL Analysis

**Goal**: Download individual animal measurements from a project and format them for QTL mapping software (R/qtl2, R/qtl).

```python
import requests
import pandas as pd

MPD_API = "https://phenome.jax.org/api"

def mpd_get(endpoint, params=None):
    r = requests.get(f"{MPD_API}{endpoint}", params=params, timeout=30)
    r.raise_for_status()
    return r.json()

# Download individual data (fasting glucose) from a specific project
project_id = "Jaxwest1"   # replace with target project
measnum = 10010            # fasting plasma glucose

result = mpd_get(f"/project/{project_id}/data", params={"measnum": measnum})
df = pd.DataFrame(result.get("data", []))
print(f"Individual records from {project_id}: {len(df)}")

if len(df) > 0:
    print(f"Columns: {df.columns.tolist()}")
    # Summary statistics per strain
    strain_stats = df.groupby(["strainname", "sex"])["value"].agg(
        ["mean", "std", "count"]
    ).round(2)
    print(f"\nStrain statistics (fasting glucose):")
    print(strain_stats.head(10))

    # Export in R/qtl-compatible format: rows = individuals, columns = phenotype + covariate
    df_qtl = df[["animalid", "strainname", "sex", "age", "value"]].copy()
    df_qtl.columns = ["id", "strain", "sex", "age_weeks", "fasting_glucose_mgdL"]
    df_qtl.to_csv(f"{project_id}_glucose_qtl_input.csv", index=False)
    print(f"\nExported {len(df_qtl)} animals to {project_id}_glucose_qtl_input.csv")
```

## Key Parameters

| Parameter | Function/Endpoint | Default | Range / Options | Effect |
|-----------|-------------------|---------|-----------------|--------|
| `measnum` | `/pheno/query`, `/project/{id}/data` | (required) | integer measure ID | Selects the phenotype measurement to retrieve |
| `sex` | `/pheno/query`, `/project/{id}/data` | (all sexes) | `"m"`, `"f"`, `"b"` (both) | Filters by animal sex |
| `strain` | `/pheno/query` | (all strains) | comma-separated strain names | Restricts results to specified strains |
| `project_id` | `/project/{id}/data` | (required) | MPD project symbol string | Specifies which study to retrieve individual data from |
| `strain_name` | `/strain/{name}` | (required) | URL-encoded strain name | Returns metadata for a specific inbred strain |
| `limit` | `/project` | varies | integer | Maximum records returned in project list |
| `category` | `/procedure` | (all) | category string | Filters procedure list by phenotype category |

## Best Practices

1. **Use `/procedure` to discover measure IDs**: MPD has hundreds of measure IDs. Query the procedure list first and filter by category to find relevant `measnum` values before fetching data.

2. **Check units and protocols before combining data across projects**: Multiple projects may measure the same trait with different protocols (fasted vs fed glucose, different ages). Use `GET /measurement/{measnum}` to verify protocol consistency before merging.

3. **Prefer strain-level summaries for initial screening, individual data for modeling**: The `/pheno/query` endpoint returns pre-computed strain means (fast); use `/project/{id}/data` for individual-level data only when statistical modeling requires it.

4. **URL-encode strain names with slashes when using path parameters**: Use `urllib.parse.quote("C57BL/6J", safe="")` → `C57BL%2F6J` for `/strain/{name}` endpoint; `requests` handles encoding automatically in `params` dictionaries.

5. **Handle missing data explicitly**: Not all strains have data for all measures. After querying, check for `NaN` values and note which strains lack data for your trait of interest before drawing conclusions about strain differences.

## Common Recipes

### Recipe: Find Strains with Extreme Phenotype Values

When to use: Select high- and low-phenotype strains for controlled genetic studies or F2 cross design.

```python
import requests
import pandas as pd

MPD_API = "https://phenome.jax.org/api"

def get_extreme_strains(measnum: int, sex: str = "m",
                        n_extremes: int = 5) -> pd.DataFrame:
    """Return top-N and bottom-N strains for a phenotype."""
    r = requests.get(f"{MPD_API}/pheno/query",
                     params={"measnum": measnum, "sex": sex},
                     timeout=30)
    r.raise_for_status()
    df = pd.DataFrame(r.json().get("data", []))
    if df.empty:
        return df
    strain_means = df.groupby("strainname")["mean"].mean().reset_index()
    strain_means.columns = ["strain", "mean_value"]
    strain_means = strain_means.sort_values("mean_value")
    high = strain_means.tail(n_extremes).assign(rank="high")
    low = strain_means.head(n_extremes).assign(rank="low")
    return pd.concat([low, high]).reset_index(drop=True)

df_extremes = get_extreme_strains(measnum=10010, sex="m", n_extremes=5)
print("Extreme strains for fasting glucose (male):")
print(df_extremes.to_string(index=False))
# strain           mean_value  rank
# A/J              101.2       low
# SJL/J            105.8       low
# ...
# NZO/HlLtJ        245.3       high
# NOD/ShiLtJ       198.7       high
```

### Recipe: Phenotype Distribution Plot for a Single Strain

When to use: Visualize the distribution of individual measurements within a strain for a QC or power analysis.

```python
import requests
import matplotlib.pyplot as plt
import pandas as pd

MPD_API = "https://phenome.jax.org/api"

def plot_strain_distribution(project_id: str, measnum: int,
                              strain: str, sex: str = "m",
                              units: str = ""):
    """Plot histogram of individual measurements for one strain."""
    r = requests.get(f"{MPD_API}/project/{project_id}/data",
                     params={"measnum": measnum, "sex": sex},
                     timeout=30)
    r.raise_for_status()
    df = pd.DataFrame(r.json().get("data", []))
    if df.empty:
        print(f"No data for project {project_id}, measnum {measnum}")
        return
    subset = df[df["strainname"] == strain]
    if subset.empty:
        print(f"Strain {strain} not found in project {project_id}")
        return
    vals = subset["value"].dropna()
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.hist(vals, bins=15, color="#1B5E20", edgecolor="white", alpha=0.8)
    ax.axvline(vals.mean(), color="red", linestyle="--", label=f"Mean={vals.mean():.1f}")
    ax.set_xlabel(units or "Value")
    ax.set_ylabel("Count")
    ax.set_title(f"{strain} — measure {measnum} ({project_id})\nn={len(vals)}, SD={vals.std():.1f}")
    ax.legend()
    plt.tight_layout()
    fname = f"{strain.replace('/', '_')}_{measnum}_dist.png"
    plt.savefig(fname, dpi=150, bbox_inches="tight")
    print(f"Saved {fname}")

plot_strain_distribution("Jaxwest1", measnum=10001, strain="C57BL/6J",
                          sex="m", units="Body weight (g)")
```

### Recipe: Batch Multi-Trait Summary Table

When to use: Build a wide-format table of multiple phenotypes per strain for comparative analysis or heatmap generation.

```python
import requests
import pandas as pd
import time

MPD_API = "https://phenome.jax.org/api"

def build_phenotype_table(measure_ids: dict, strains: list,
                           sex: str = "m") -> pd.DataFrame:
    """
    Build a wide-format DataFrame: rows=strains, columns=phenotypes.
    measure_ids: dict of {measnum: column_name}
    """
    frames = []
    for measnum, col_name in measure_ids.items():
        r = requests.get(f"{MPD_API}/pheno/query",
                         params={"measnum": measnum, "sex": sex,
                                 "strain": ",".join(strains)},
                         timeout=30)
        r.raise_for_status()
        df = pd.DataFrame(r.json().get("data", []))
        if not df.empty:
            avg = df.groupby("strainname")["mean"].mean().rename(col_name)
            frames.append(avg)
        time.sleep(0.5)
    if not frames:
        return pd.DataFrame()
    wide = pd.concat(frames, axis=1).reset_index().rename(columns={"strainname": "strain"})
    return wide

panel = ["C57BL/6J", "DBA/2J", "BALB/cJ", "A/J", "NOD/ShiLtJ", "NZO/HlLtJ"]
measures = {10001: "body_wt_g", 10010: "fast_glucose_mgdL",
            10020: "cholesterol_mgdL", 10100: "systolic_bp_mmHg"}

df_wide = build_phenotype_table(measures, panel)
print(df_wide.round(1).to_string(index=False))
df_wide.to_csv("mpd_multi_trait_table.csv", index=False)
print(f"\nSaved mpd_multi_trait_table.csv ({df_wide.shape[0]} strains x {df_wide.shape[1]-1} traits)")
```

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| Empty `data` list from `/pheno/query` | Measure ID not present for requested strains | Confirm `measnum` is valid via `/procedure`; not all strains have all measures |
| `404 Not Found` for `/strain/{name}` | Slash not URL-encoded in path | Use `urllib.parse.quote("C57BL/6J", safe="")` → `C57BL%2F6J`; or use query param approach |
| `requests.exceptions.Timeout` | Slow API response for large strain lists | Reduce strain list size; increase `timeout=60`; split large batches |
| Project `/data` endpoint returns no data | Project symbol is wrong or project has no individual data | Verify project symbol using `/project` endpoint; some projects only have summary data |
| Units inconsistent across projects for same measnum | Different protocols in different labs | Confirm units via `/measurement/{measnum}`; filter to a single project when protocol consistency is critical |
| Strain name mismatch | MPD uses specific JAX strain nomenclature | Search for similar names using the `/strain` listing; verify exact spelling with JAX stock number |
| `KeyError` when accessing response keys | API response structure varies by endpoint | Print `r.json().keys()` or `r.json()` to inspect actual structure before parsing |

## Related Skills

- `monarch-database` — disease-gene-phenotype knowledge graph with HPO annotations and cross-species gene associations
- `ensembl-database` — mouse genome annotation, gene coordinates, and transcript information
- `gwas-database` — GWAS Catalog for human SNP-trait associations (parallel to MPD mouse QTL data)
- `gseapy-gene-enrichment` — pathway enrichment analysis on gene lists derived from QTL-driven candidate gene sets

## References

- [Mouse Phenome Database](https://phenome.jax.org/) — main portal with dataset browser and download interface
- [MPD REST API Documentation](https://phenome.jax.org/api) — interactive Swagger documentation for all endpoints
- [Bogue et al., Mammalian Genome 2020](https://doi.org/10.1007/s00335-020-09839-9) — MPD overview paper (data content, strain coverage, use cases)
- [Jackson Laboratory Inbred Strain Catalog](https://www.jax.org/inbred-strains) — canonical strain names and stock numbers
- [MPD Data Use Policy](https://phenome.jax.org/about/datause) — CC-BY-4.0 license terms and citation requirements
