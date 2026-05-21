---
name: "mouse-phenome-database"
description: "Retrieve mouse phenotype data from the Jackson Laboratory Mouse Phenome Database (MPD) via its REST API. Browse 520+ projects, look up per-project measure metadata, pull strain-level means (raw or LS-mean adjusted) and per-animal values, find measures by MP/VT ontology terms, and resolve strain nomenclature or gene coordinates. Use for QTL support, cross-strain comparison, mouse model selection, and ontology-driven phenotype discovery. Use monarch-database for disease-gene-phenotype knowledge graphs; ensembl-database for mouse genome annotations."
license: "CC-BY-4.0"
---

# mouse-phenome-database

## Overview

The Mouse Phenome Database (MPD), maintained at the Jackson Laboratory, catalogs standardized phenotype measurements across inbred, recombinant inbred (e.g., BXD), and Collaborative Cross / Diversity Outbred mouse panels. It aggregates 520+ projects spanning metabolic, cardiovascular, behavioral, hematological, and immunological traits. The REST API at `https://phenome.jax.org/api` is free, requires no authentication, and is documented at <https://phenome.jax.org/about/api>. MPD measurement IDs (`measnum`) are project-scoped 5-digit integers — there is no global "measnum 10001 = body weight" mapping; valid measnums must be discovered per project via the `measureinfo` endpoint.

## When to Use

- Selecting inbred strains with extreme phenotypes (highest/lowest fasted glucose, body weight, heart rate, etc.) as experimental models
- Pulling individual-animal data from BXD / CC / DO panels for QTL mapping with R/qtl2 or similar tools
- Comparing strain means and variance across metabolic, behavioral, or cardiovascular measures for genetic background studies
- Finding MPD projects that measure a trait of interest using ontology terms (MP, VT, MA) or free-text descriptions
- Validating mouse strain nomenclature (canonical JAX names ↔ stock numbers ↔ MGI IDs) before submitting orders or analyses
- Looking up coordinates and annotations for mouse genes in the MPD/MGI cross-reference
- Use `monarch-database` instead for disease-gene-phenotype knowledge graphs (HPO ↔ MP ↔ disease)
- Use `ensembl-database` instead for transcript-level mouse gene annotations and variant consequence prediction

## Prerequisites

- **Python packages**: `requests`, `pandas`, `matplotlib`
- **Data requirements**: a project symbol (e.g., `Jaxwest1`, `Auwerx1`) or a measnum (e.g., `15101`); strain names follow JAX canonical nomenclature (e.g., `C57BL/6J`, `DBA/2J`)
- **Environment**: internet connection; no API key required
- **Rate limits**: no published hard limit; keep bursts under ~5 requests/second and add `time.sleep(0.3)` between requests in loops

```bash
pip install requests pandas matplotlib
```

## Quick Start

```python
import requests

MPD = "https://phenome.jax.org/api"

# 1) Pick a project (Jaxwest1 — cardiovascular phenotyping on inbred panel)
r = requests.get(f"{MPD}/projects/Jaxwest1/strains", timeout=30)
strains = r.json()["strains"]
print(f"Jaxwest1: {len(strains)} strains tested")

# 2) Discover its measures
r = requests.get(f"{MPD}/pheno/measureinfo/Jaxwest1", timeout=30)
measures = r.json()["measures_info"]
print(f"Jaxwest1 measures: {len(measures)}; first: measnum={measures[0]['measnum']} "
      f"varname={measures[0]['varname']}  ({measures[0]['descrip']}, {measures[0]['units']})")

# 3) Pull strain means for heart rate (varname=HR, measnum=15101)
r = requests.get(f"{MPD}/pheno/strainmeans/15101", timeout=30)
sm = r.json()["strainmeans"]
print(f"\nHeart rate strain means: {len(sm)} rows  (one per strain × sex)")
top = sorted(sm, key=lambda x: x["mean"], reverse=True)[:5]
for s in top:
    print(f"  {s['strain']:<20}  sex={s['sex']}  mean={s['mean']:.0f} {s.get('varname','')}  n={s['nmice']}")
```

## Core API

### Module 1: Browse Projects — `/projects`

Lists all MPD projects with full metadata. Filter via `investigator`, `projsym`, `projid`, `mpdsector`, `largecollab`, `panelsym`. Use `/project_filters/{filtername}` to see the allowed values of `mpdsector`, `largecollab`, or `panelsym` before filtering.

```python
import requests, pandas as pd

MPD = "https://phenome.jax.org/api"

# List allowed panel symbols (e.g., BXD, CC, DO)
filters = requests.get(f"{MPD}/project_filters/panelsym", timeout=30).json()
print(f"Available panels ({filters['count']}):", [t['term'] for t in filters['terms']][:10])

# All projects in the BXD recombinant inbred panel
r = requests.get(f"{MPD}/projects", params={"panelsym": "BXD"}, timeout=30)
projects = r.json()["projects"]
print(f"BXD projects: {len(projects)}")
df = pd.DataFrame([{
    "projsym": p["projsym"],
    "pi": p.get("pistring", "")[:40],
    "nstrains": p.get("nstrains"),
    "ages": p.get("ages"),
    "sector": p.get("mpdsector"),
    "title": (p.get("title") or "")[:60],
} for p in projects])
print(df.head(10).to_string(index=False))
```

```python
# Filter by MPD sector — komp, pheno, qtla, snp, onestrain, phenoarchive
r = requests.get(f"{MPD}/projects", params={"mpdsector": "qtla"}, timeout=30)
qtl_projects = r.json()["projects"]
print(f"QTL-archive projects: {len(qtl_projects)}")
for p in qtl_projects[:5]:
    print(f"  {p['projsym']:<15} panel={p.get('panelsym') or '--':<6} nstrains={str(p.get('nstrains') or '--'):>4}  {(p.get('title') or '')[:55]}")
```

### Module 2: Project Detail — `/projects/{projsym}/...`

Each project has sub-resources for its dataset (CSV of every animal × every measure), the strain panel it tested, the publications it produced, and (for QTL projects) the genetic markers used.

```python
import requests, io, pandas as pd

MPD = "https://phenome.jax.org/api"

# Full per-animal dataset as CSV (default). Use json=yes for JSON.
r = requests.get(f"{MPD}/projects/Jaxwest1/dataset", timeout=60)
df = pd.read_csv(io.StringIO(r.text))
print(f"Jaxwest1 dataset: {df.shape[0]} animals × {df.shape[1]} columns")
print(df.columns[:12].tolist())
print(df[["strain", "sex", "animal_id", "HR", "QRS", "bw"]].head(5).to_string(index=False))
```

```python
# Strains tested in a project + publication list
strains = requests.get(f"{MPD}/projects/Jaxwest1/strains", timeout=30).json()
print(f"Jaxwest1 strains ({strains['count']}):")
for s in strains["strains"][:5]:
    print(f"  {s['strainname']:<20}  stock={s['stocknum']}  vendor={s['vendor']}")

pubs = requests.get(f"{MPD}/projects/Jaxwest1/publications", timeout=30).json()
print(f"\nPublications: {pubs['count']}")
```

### Module 3: Measure Discovery — `/pheno/measureinfo/{selector}`

This is the canonical way to discover valid `measnum` values. The selector is either a project symbol (returns all measures in that project) or a measnum (returns metadata for one measure).

```python
import requests, pandas as pd

MPD = "https://phenome.jax.org/api"

# All measures in the Jaxwest1 cardiovascular project
r = requests.get(f"{MPD}/pheno/measureinfo/Jaxwest1", timeout=30)
measures = r.json()["measures_info"]
df = pd.DataFrame([{
    "measnum": m["measnum"],
    "varname": m["varname"],
    "descrip": m["descrip"],
    "units": m.get("units"),
    "sex": m.get("sextested"),
    "age": m.get("ageweeks"),
} for m in measures])
print(f"Jaxwest1 has {len(df)} measures")
print(df.head(10).to_string(index=False))
```

```python
# Single-measure metadata lookup (protocol + dimensional details)
r = requests.get(f"{MPD}/pheno/measureinfo/15101", timeout=30).json()
m = r["measures_info"][0]
print(f"measnum {m['measnum']} ({m['varname']}): {m['descrip']}")
print(f"  units: {m.get('units')}")
print(f"  project: {m.get('projsym')}  panel: {m.get('panelsym') or m.get('paneldesc')}")
print(f"  sex tested: {m.get('sextested')}  age: {m.get('ageweeks')}")
print(f"  method:  {(m.get('method') or '')[:120]}")
```

### Module 4: Strain Means — `/pheno/strainmeans/{selector}`

Returns strain × sex summary statistics. The selector takes a project symbol (all strain means for the project) or one-or-more comma-separated measnums. Each row contains `measnum, varname, strain, strainid, sex, mean, sd, sem, cv, minval, maxval, nmice, zscore`.

```python
import requests, pandas as pd

MPD = "https://phenome.jax.org/api"

# Strain means for one measure (heart rate, measnum=15101 from Jaxwest1)
r = requests.get(f"{MPD}/pheno/strainmeans/15101", timeout=30)
sm = pd.DataFrame(r.json()["strainmeans"])
print(f"Rows: {len(sm)}  ({sm['strain'].nunique()} strains × {sm['sex'].nunique()} sexes)")

# Rank strains by male HR
male = sm[sm["sex"] == "m"].sort_values("mean", ascending=False)
print(male[["strain", "mean", "sd", "sem", "nmice", "zscore"]].head(8).to_string(index=False))
```

```python
# Optional: model-adjusted means (lsmeans) account for covariates fit in MPD's models.
# Use lsmeans when comparing strains across cohorts within a project.
r = requests.get(f"{MPD}/pheno/lsmeans/Jaxwest1", timeout=30).json()
print("LS-mean measures available for Jaxwest1:", r.get("ls_measures", [])[:10])
```

### Module 5: Per-Animal Values — `/pheno/animalvals/{measnum}`

Raw per-animal observations for one measure. Each row carries `animal_id, animal_projid, measnum, projsym, sex, stocknum, strain, strainid, value, varname, zscore`. Use this for QTL mapping, mixed-effects modeling, or distribution analysis.

```python
import requests, pandas as pd

MPD = "https://phenome.jax.org/api"

# Per-animal heart rate values
r = requests.get(f"{MPD}/pheno/animalvals/15101", timeout=30)
ad = pd.DataFrame(r.json()["animaldata"])
print(f"Animals measured: {len(ad)}")
print(ad[["animal_id", "strain", "sex", "value", "zscore"]].head(8).to_string(index=False))

# Compare male-only strain distributions
male = ad[ad["sex"] == "m"]
stats = male.groupby("strain")["value"].agg(["mean", "std", "count"]).round(2)
print(f"\nMale HR by strain (top 5 by mean):")
print(stats.sort_values("mean", ascending=False).head(5))
```

### Module 6: Ontology-Based Measure Discovery — `/pheno/measures_by_ontology/{ont_term}`

Find every MPD measure annotated to a Mammalian Phenotype (MP), Vertebrate Trait (VT), or Mouse Anatomy (MA) ontology term. Optional `this_term_only=yes` disables descendant-term expansion; `omit_baseline=yes` filters out baseline measures; `collapse_series=yes` collapses repeated time-points.

```python
import requests, pandas as pd

MPD = "https://phenome.jax.org/api"

# MP:0001262 = "decreased body weight"
r = requests.get(f"{MPD}/pheno/measures_by_ontology/MP:0001262",
                 params={"omit_baseline": "yes", "collapse_series": "yes"},
                 timeout=30).json()
print(f"Measures mapped to MP:0001262 ('{r['ontology_terms'][0]['descrip']}'): {r['count']}")
if r["count"]:
    df = pd.DataFrame(r["measures"])
    print(df[["measnum", "varname", "descrip", "projsym"]].head(8).to_string(index=False))
else:
    print("(no direct measures; consider a broader parent term)")
```

### Module 7: Strain Nomenclature — `/straininfo`

Validate and normalise strain names. Accepts `name`, `stocknum`, or `mginum` query params. Returns both `jaxinfo[]` (JAX availability/nomenclature) and `mpdinfo[]` (MPD's own metadata, including how many projects test this strain).

```python
import requests

MPD = "https://phenome.jax.org/api"

# Validate C57BL/6J — note `requests` URL-encodes the slash automatically in params
r = requests.get(f"{MPD}/straininfo", params={"name": "C57BL/6J"}, timeout=30).json()
jax = r["jaxinfo"][0]
mpd = r["mpdinfo"][0]
print(f"JAX:  {jax['nomenclature']}  stock={jax['stocknum']}  status={jax['avl_status']}")
print(f"MPD:  longname={mpd['longname']}  type={mpd['straintype']}  "
      f"projects={mpd['nproj']}  snp_projects={mpd['nsnpproj']}  MGI={mpd['mginum']}")
```

### Module 8: Gene Info — `/geneinfo/{symbol}`

Mouse-gene coordinates (GRCm39, in bp), strand, MGI ID, and a short description. Note the response key is the literal string `"gene info"` (with a space).

```python
import requests

MPD = "https://phenome.jax.org/api"

r = requests.get(f"{MPD}/geneinfo/Lep", timeout=30).json()
for g in r["gene info"]:
    print(f"{g['descrip']}  chr{g['chrom']}:{g['startbp']:,}–{g['endbp']:,} ({g['strand']})")
    print(f"  type: {g['featuretype']}  MGI: {g['mginum']}  cM: {g['centimorgan']}")
```

## Key Concepts

### Measnums Are Project-Scoped, Not Global

Every `measnum` belongs to exactly one project. `15101` is "heart rate" only within Jaxwest1; the same physiological trait in another project has a different measnum (e.g., `35702` for body weight in Lightfoot1). Never hardcode measnums for a trait — always resolve them by:

1. Finding the project: `GET /projects?panelsym=...` or `GET /projects?investigator=...`
2. Listing its measures: `GET /pheno/measureinfo/{projsym}`
3. Picking the right `varname` / `descrip` / `units` triple from the response

Or go the other way and discover measures by ontology term first (Module 6).

### Selectors: Projsym vs Measnum

Most `/pheno/*` endpoints take a "selector" path parameter that's overloaded:

| Endpoint | Accepts as selector |
|----------|---------------------|
| `/pheno/strainmeans/{selector}` | projsym (e.g., `Jaxwest1`) **or** one or more comma-separated measnums |
| `/pheno/lsmeans/{selector}` | same |
| `/pheno/measureinfo/{selector}` | same |
| `/pheno/animalvals/{measnum}` | measnum only (use measureinfo to discover) |
| `/pheno/animalvals/series/{measnum}` | for timecourse/dose-response series |

If you pass an unrecognised selector you get a 400 JSON response (`{"error": "...selector arg must either be measure IDs or a project symbol"}`), not an HTML 404 — those are diagnostic and worth surfacing.

### Strain Means vs LS-Means

- `strainmeans` are unadjusted: simple per-strain × per-sex arithmetic means of the raw animal values.
- `lsmeans` are model-adjusted least-squares means from MPD's pre-fit ANOVA-style models (accounting for cohort, batch, or covariate effects when present).

For cross-project comparisons or analyses sensitive to batch effects, prefer `lsmeans` when available. For simple ranking and exploratory work, `strainmeans` is fine.

### MPD Sectors (`mpdsector` filter)

| Sector | Content |
|--------|---------|
| `pheno` | Standard inbred-strain phenotyping projects |
| `qtla` | QTL Archive — historical mapping studies with markers |
| `komp` | Knockout Mouse Project (KOMP / JaxLIMS) data |
| `snp` | SNP genotype panels (use `/snpdata`) |
| `phenoarchive` | Archived legacy phenotype projects |
| `onestrain` | Single-strain deep phenotyping |

Discover the live list any time with `GET /project_filters/mpdsector`.

## Common Workflows

### Workflow 1: Pick a Trait → Find a Project → Plot Strain Means

**Goal**: From "I want to compare heart rate across inbred strains" → land on real data and produce a ranked barplot.

```python
import requests, pandas as pd, matplotlib.pyplot as plt, time

MPD = "https://phenome.jax.org/api"

# 1) Find candidate projects whose name/description hints at the trait
projects = requests.get(f"{MPD}/projects", timeout=30).json()["projects"]
candidates = [p for p in projects
              if any(kw in (p.get("title") or "").lower()
                     for kw in ["cardiovascular", "heart", "ekg", "ecg"])]
print(f"Candidate cardiovascular projects: {len(candidates)}")
for p in candidates[:5]:
    print(f"  {p['projsym']:<15}  nstrains={str(p.get('nstrains') or '--'):>3}  {(p.get('title') or '')[:60]}")

# 2) Inspect measures for the chosen project
projsym = "Jaxwest1"
mi = requests.get(f"{MPD}/pheno/measureinfo/{projsym}", timeout=30).json()["measures_info"]
hr = next(m for m in mi if m["varname"] == "HR")
print(f"\nPicked: {projsym} measnum={hr['measnum']} varname={hr['varname']} ({hr['descrip']}, {hr['units']})")

# 3) Pull strain means, plot male strains ranked
sm = pd.DataFrame(requests.get(f"{MPD}/pheno/strainmeans/{hr['measnum']}", timeout=30).json()["strainmeans"])
male = sm[sm["sex"] == "m"].sort_values("mean", ascending=False).reset_index(drop=True)

fig, ax = plt.subplots(figsize=(9, 4))
bars = ax.bar(male["strain"], male["mean"], yerr=male["sem"],
              color="#1976D2", capsize=3, edgecolor="white")
ax.bar_label(bars, fmt="%.0f", padding=3, fontsize=8)
ax.set_xlabel("Strain")
ax.set_ylabel(f"Mean {hr['varname']} ({hr['units']})")
ax.set_title(f"{hr['descrip']} by inbred strain (male) — {projsym}")
plt.xticks(rotation=30, ha="right")
plt.tight_layout()
plt.savefig("mpd_strain_means.png", dpi=150, bbox_inches="tight")
print("Saved mpd_strain_means.png")
```

### Workflow 2: Per-Animal Data → R/qtl2 CSV Export

**Goal**: Pull individual animal observations for a measure and shape them into a phenotype file ready for QTL mapping.

```python
import requests, pandas as pd

MPD = "https://phenome.jax.org/api"

measnum = 15101  # heart rate in Jaxwest1
mi = requests.get(f"{MPD}/pheno/measureinfo/{measnum}", timeout=30).json()["measures_info"][0]
ad = pd.DataFrame(requests.get(f"{MPD}/pheno/animalvals/{measnum}", timeout=30).json()["animaldata"])
print(f"measnum {measnum}: {mi['varname']} ({mi['descrip']}, {mi['units']}) — {len(ad)} animals")

# R/qtl2-ready phenotype CSV: rows = individuals, cols = id + covariates + phenotype
out = ad[["animal_id", "strain", "sex", "value"]].rename(
    columns={"animal_id": "id", "value": mi["varname"]}
)
out.to_csv(f"{measnum}_{mi['varname']}_qtl_pheno.csv", index=False)
print(f"Wrote {measnum}_{mi['varname']}_qtl_pheno.csv  ({len(out)} animals)")
print(out.head().to_string(index=False))
```

### Workflow 3: Multi-Measure Heatmap Across a Strain Panel

**Goal**: Build a wide-format strain × measure table (z-scored) from one project for comparative visualisation.

```python
import requests, pandas as pd, matplotlib.pyplot as plt

MPD = "https://phenome.jax.org/api"
projsym = "Jaxwest1"

# Pull all strain means for the project in one call
sm = pd.DataFrame(requests.get(f"{MPD}/pheno/strainmeans/{projsym}", timeout=30).json()["strainmeans"])

# Use the precomputed z-scores; pivot to strain × varname (male only for simplicity)
male = sm[sm["sex"] == "m"]
wide = male.pivot_table(index="strain", columns="varname", values="zscore", aggfunc="mean")
print(f"Shape: {wide.shape}  (strains × measures)")

# Subset to a handful of measures with full coverage
keep = wide.dropna(axis=1, thresh=int(0.8 * len(wide))).columns[:10]
wide = wide[keep].dropna()
print(f"After coverage filter: {wide.shape}")

fig, ax = plt.subplots(figsize=(8, max(3, 0.3 * len(wide))))
im = ax.imshow(wide.values, aspect="auto", cmap="RdBu_r", vmin=-2, vmax=2)
ax.set_xticks(range(len(wide.columns)))
ax.set_xticklabels(wide.columns, rotation=45, ha="right", fontsize=8)
ax.set_yticks(range(len(wide.index)))
ax.set_yticklabels(wide.index, fontsize=8)
fig.colorbar(im, ax=ax, label="z-score")
ax.set_title(f"{projsym} — strain × measure z-score heatmap (male)")
plt.tight_layout()
plt.savefig("mpd_strain_measure_heatmap.png", dpi=150, bbox_inches="tight")
print("Saved mpd_strain_measure_heatmap.png")
```

## Key Parameters

| Parameter | Endpoint | Default | Range / Options | Effect |
|-----------|----------|---------|-----------------|--------|
| `panelsym` | `/projects` | — | strain panel symbol (`BXD`, `CC`, `DO`, …) | Filter projects to one mouse panel |
| `mpdsector` | `/projects` | — | `pheno`, `qtla`, `komp`, `snp`, `phenoarchive`, `onestrain` | Filter projects by data sector |
| `investigator` | `/projects`, `/investigators` | — | investigator name substring | Filter projects by PI |
| `csv` | `/projects`, `/investigators`, `/projects/{projsym}/dataset`, etc. | `no` | `yes` | Return CSV instead of JSON |
| `json` | `/projects/{projsym}/dataset` | — | `yes` | Return JSON instead of default CSV |
| `this_term_only` | `/pheno/measures_by_ontology/{ont_term}` | `no` | `yes` | Disable descendant-term expansion |
| `omit_baseline` | `/pheno/measures_by_ontology/{ont_term}` | `no` | `yes` | Drop baseline measures from results |
| `collapse_series` | `/pheno/measures_by_ontology/{ont_term}` | `no` | `yes` | Collapse timecourse/dose series into single entries |
| `region`, `dataset`, `strains` | `/snpdata` | required | genomic region, dataset name, strain CSV | Pull SNP genotypes for region across strains |
| `name` / `stocknum` / `mginum` | `/straininfo` | one required | strain name, JAX stock #, or MGI ID | Validate / look up strain |

## Best Practices

1. **Always discover measnums via `/pheno/measureinfo/{projsym}` before querying data.** Measnums are project-scoped 5-digit integers; there is no global trait → measnum table. Hardcoding measnums you got from elsewhere will silently 404 or return "no data".

2. **Use plural resource paths.** MPD uses `/projects`, `/projects/{projsym}/strains`, `/projects/{projsym}/dataset` — not singular. Old MPD documentation and several third-party wrappers list singular paths that return HTML 404s.

3. **Prefer the project-level dataset CSV for bulk analysis.** When you want every animal × every measure for a project, `GET /projects/{projsym}/dataset` returns a single CSV in one request — much faster than looping `animalvals` per measnum.

4. **Use `lsmeans` instead of `strainmeans` when MPD has fit a model.** LS-means adjust for covariates (cohort, age, batch) baked into MPD's project-level statistical models. For comparative ranking across strains within a project, lsmeans is the more honest summary when available (`/pheno/lsmeans/{projsym}` returns the list of `ls_measures`).

5. **Validate strain names with `/straininfo` before assuming a match.** MPD uses strict JAX canonical nomenclature; nearby synonyms (`B6`, `C57Bl/6`, `C57BL/6`) won't always resolve. `/straininfo?name=...` returns both JAX and MPD records and tells you the canonical form.

6. **Be polite — add `time.sleep(0.3)` in loops.** MPD doesn't publish a hard rate limit, but the server runs on shared academic infrastructure. Keep bursts under ~5 req/s.

## Common Recipes

### Recipe: Find Projects Testing a Trait by Free-Text Search

```python
import requests, pandas as pd

MPD = "https://phenome.jax.org/api"

def find_projects(keyword):
    """Search project titles for a keyword (case-insensitive)."""
    projects = requests.get(f"{MPD}/projects", timeout=30).json()["projects"]
    kw = keyword.lower()
    hits = [p for p in projects if kw in (p.get("title") or "").lower()]
    return pd.DataFrame([{
        "projsym": p["projsym"],
        "panel": p.get("panelsym"),
        "nstrains": p.get("nstrains"),
        "year": p.get("projyear"),
        "title": (p.get("title") or "")[:80],
    } for p in hits])

print(find_projects("glucose").head(10).to_string(index=False))
```

### Recipe: Pull a Whole Project as a DataFrame in One Call

```python
import requests, io, pandas as pd

MPD = "https://phenome.jax.org/api"

def load_project_dataset(projsym):
    """Fetch /projects/{projsym}/dataset CSV directly into a DataFrame."""
    r = requests.get(f"{MPD}/projects/{projsym}/dataset", timeout=120)
    r.raise_for_status()
    return pd.read_csv(io.StringIO(r.text))

df = load_project_dataset("Jaxwest1")
print(f"Jaxwest1: {df.shape[0]} animals × {df.shape[1]} columns")
print("Numeric columns:", df.select_dtypes("number").columns.tolist()[:8])
```

### Recipe: Cross-Strain Comparison from Strain Means

```python
import requests, pandas as pd

MPD = "https://phenome.jax.org/api"

# Multiple measnums in one call (comma-separated selector)
selector = "15101,15102,15103"   # HR, QRS, PR from Jaxwest1
sm = pd.DataFrame(requests.get(f"{MPD}/pheno/strainmeans/{selector}", timeout=30).json()["strainmeans"])
wide = (sm[sm["sex"] == "m"]
        .pivot_table(index="strain", columns="varname", values="mean", aggfunc="mean")
        .round(1))
print(wide.head(8).to_string())
```

### Recipe: Resolve Gene → Coordinates → Adjacent Region

```python
import requests

MPD = "https://phenome.jax.org/api"

def gene_window(symbol, flank_kb=100):
    r = requests.get(f"{MPD}/geneinfo/{symbol}", timeout=30).json()
    if not r.get("gene info"):
        return None
    g = r["gene info"][0]
    return {
        "symbol": symbol,
        "chrom": g["chrom"],
        "start": max(0, g["startbp"] - flank_kb * 1000),
        "stop": g["endbp"] + flank_kb * 1000,
        "mgi": g["mginum"],
        "descrip": g["descrip"],
    }

print(gene_window("Lep", flank_kb=50))
# {'symbol': 'Lep', 'chrom': '6', 'start': 29010220, 'stop': 29123877, 'mgi': 'MGI:104663', ...}
```

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| `HTTP 404` with HTML body on `/strain/...`, `/procedure`, `/pheno/query`, `/measurement/...`, `/project/...` | These paths don't exist — MPD's real API uses plural resource names and a different layout | Use `/projects` (plural), `/projects/{projsym}/dataset`, `/pheno/strainmeans/{selector}`, `/pheno/measureinfo/{selector}`, `/straininfo` |
| `HTTP 400` with `{"error": "...selector arg must either be measure IDs or a project symbol"}` | The path's selector arg got something else (a strain name, a varname, a category) | Resolve the right projsym or measnum first via `/projects` or `/pheno/measureinfo/{projsym}` |
| `HTTP 404` with `{"error": "No strainmeans data found for {selector}"}` | The selector is the right kind but has no data (e.g., a measnum from a different project, or a typo) | Confirm the measnum exists via `/pheno/measureinfo/{measnum}`; check it belongs to the project you think |
| `KeyError: 'gene info'` when parsing `/geneinfo/{sym}` | Response key has a literal space: `"gene info"`, not `gene_info` | Access via `r.json()["gene info"]` exactly |
| `dataset` endpoint returns plain text instead of JSON | Default content type is CSV | Pass `params={"json": "yes"}` to force JSON; or parse the CSV with `pd.read_csv(io.StringIO(r.text))` |
| Strain name returns empty `mpdinfo` from `/straininfo` | Non-canonical name (e.g., `B6`, `C57Bl/6`) | Use exact JAX nomenclature (`C57BL/6J`); try `stocknum=` lookup if you have the JAX stock number |
| `/pheno/measures_by_ontology/{term}` returns `count: 0` but the term exists | No direct mappings; the term is too specific | Re-query with the term's parent (the response includes `ontology_terms[].parent`); or drop `this_term_only=yes` |
| `HTTP 5xx` intermittently on large CSV pulls | MPD's per-project datasets can be tens of MB | Increase `timeout=120`; for very large projects use `csv=yes` + stream with `requests.get(..., stream=True)` |

## Related Skills

- `monarch-database` — disease-gene-phenotype knowledge graph with HPO ↔ MP cross-mappings; complement MPD's mouse-only data with human disease links
- `ensembl-database` — mouse genome annotation (GRCm39 coordinates, transcripts, VEP) — pairs with MPD `/geneinfo` for fine-grained gene-model details
- `gwas-database` — human GWAS Catalog SNP-trait associations; conceptual analogue of MPD's QTL projects for human populations
- `clinvar-database` — clinical variant interpretation; relevant when mapping a mouse QTL to a human disease gene

## References

- [Mouse Phenome Database portal](https://phenome.jax.org/) — interactive dataset browser and download UI
- [MPD REST API documentation](https://phenome.jax.org/about/api) — authoritative endpoint reference (the one used to build this skill)
- [Bogue et al., *Mammalian Genome* 2020](https://doi.org/10.1007/s00335-020-09839-9) — MPD overview paper (architecture, data content, strain coverage)
- [Jackson Laboratory Inbred Strain Catalog](https://www.jax.org/inbred-strains) — canonical strain nomenclature and stock numbers
- [Mammalian Phenotype Ontology](https://www.informatics.jax.org/vocab/mp_ontology) — MP term browser (used by `/pheno/measures_by_ontology/{term}`)
- [MPD Data Use Policy](https://phenome.jax.org/about/datause) — CC-BY-4.0 license terms and citation requirements
