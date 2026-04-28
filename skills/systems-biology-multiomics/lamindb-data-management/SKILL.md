---
name: lamindb-data-management
description: "Open-source FAIR biology data framework. Version artifacts (AnnData, DataFrame, Zarr), track lineage, validate via ontologies (Bionty), query datasets. Integrates with Nextflow, Snakemake, W&B, scVI. For scRNA-seq use scanpy; for ontology lookups use bionty."
license: Apache-2.0
---

# LaminDB — Biological Data Management

## Overview

LaminDB is an open-source data framework for biology that makes data queryable, traceable, and FAIR (Findable, Accessible, Interoperable, Reusable). It combines data lakehouse architecture, lineage tracking, biological ontology validation, and a unified Python API for managing biological datasets from raw files to annotated, curated artifacts.

## When to Use

- Managing and versioning biological datasets (scRNA-seq, spatial, flow cytometry, multi-modal)
- Tracking computational lineage (which code produced which data)
- Validating and curating data against biological ontologies (cell types, genes, tissues, diseases)
- Building queryable data lakehouses across multiple experiments
- Ensuring reproducibility with automatic environment and provenance capture
- Integrating with workflow managers (Nextflow, Snakemake) or MLOps (W&B, MLflow)
- Standardizing metadata with ontology-based annotation (Bionty)
- For **single-cell analysis pipelines** (clustering, DE), use scanpy instead
- For **ontology lookups only** without data management, use bionty directly

## Prerequisites

```bash
pip install lamindb
# With extras for specific data types
pip install 'lamindb[bionty,zarr,fcs]'
```

**Setup**: Requires instance initialization before use:
```bash
lamin login
lamin init --storage ./my-data --name my-project
# Or with cloud storage:
# lamin init --storage s3://my-bucket --name my-project --db postgresql://...
```

**Instance types**: Local SQLite (development), Cloud + SQLite (small teams), Cloud + PostgreSQL (production).

## Quick Start

```python
import lamindb as ln

ln.track()  # Start lineage tracking

# Save an artifact
import pandas as pd
df = pd.DataFrame({"gene": ["TP53", "BRCA1"], "score": [0.95, 0.87]})
artifact = ln.Artifact.from_df(df, key="results/gene_scores.parquet", description="Gene importance scores")
artifact.save()
print(f"Saved: {artifact.uid}, size: {artifact.size}")

# Query artifacts
results = ln.Artifact.filter(key__startswith="results/").df()
print(f"Found {len(results)} artifacts")

ln.finish()
```

## Core API

### 1. Artifacts — Data Objects

Artifacts are versioned data objects (files, DataFrames, AnnData, arrays).

```python
import lamindb as ln
import pandas as pd
import anndata as ad

ln.track()

# From DataFrame
df = pd.DataFrame({"sample": ["A", "B"], "value": [1.5, 2.3]})
artifact = ln.Artifact.from_df(df, key="experiments/batch1.parquet").save()
print(f"ID: {artifact.uid}, Version: {artifact.version}")

# From AnnData
adata = ad.read_h5ad("counts.h5ad")
artifact = ln.Artifact.from_anndata(adata, key="scrna/batch1.h5ad", description="scRNA-seq batch 1").save()

# From file path
artifact = ln.Artifact("results/figure.png", key="figures/fig1.png").save()

# Load back
df_loaded = artifact.load()  # Returns DataFrame/AnnData/etc.
path = artifact.cache()       # Returns local file path
```

```python
# Versioning
artifact_v2 = ln.Artifact.from_df(df_updated, key="experiments/batch1.parquet", revises=artifact).save()
print(f"v1: {artifact.uid}, v2: {artifact_v2.uid}")
print(f"Latest version: {artifact_v2.is_latest}")

# Delete (archive first, then permanent)
artifact.delete(permanent=False)  # Archive
# artifact.delete(permanent=True)  # Permanent deletion
```

### 2. Lineage Tracking

Automatic provenance capture for reproducibility.

```python
import lamindb as ln

# Start tracking — captures notebook/script, environment, user
ln.track(params={"method": "PCA", "n_components": 50})

# All artifacts created within this block are linked to this run
input_data = ln.Artifact.get(key="raw/counts.h5ad")
adata = input_data.load()

# ... analysis code ...

output = ln.Artifact.from_anndata(adata, key="processed/pca.h5ad").save()

# View lineage graph
output.view_lineage()

ln.finish()  # Finalize tracking
```

### 3. Querying and Filtering

Search and filter artifacts by metadata, features, and annotations.

```python
import lamindb as ln

# Basic filtering
artifacts = ln.Artifact.filter(key__startswith="scrna/").df()
print(f"Found {len(artifacts)} scRNA-seq artifacts")

# Filter by metadata
recent = ln.Artifact.filter(
    created_at__gte="2026-01-01",
    size__gt=1000000
).df()

# Filter by annotated features
immune = ln.Artifact.filter(
    cell_types__name="T cell",
    tissues__name="PBMC"
).df()

# Single record retrieval
artifact = ln.Artifact.get(key="results/final.parquet")  # Exact match, raises if not found
artifact = ln.Artifact.filter(key="results/final.parquet").one_or_none()  # Returns None if missing

# Full-text search
results = ln.Artifact.search("gene expression PBMC")

# Streaming large files (without full load into memory)
artifact = ln.Artifact.get(key="large_dataset.h5ad")
backed = artifact.open()  # AnnData-backed mode
subset = backed[backed.obs["cell_type"] == "B cell"]
```

### 4. Annotation and Validation

Curate datasets against schemas and ontology terms.

```python
import lamindb as ln
import bionty as bt

# Annotate artifacts with features
artifact = ln.Artifact.get(key="scrna/batch1.h5ad")
artifact.features.add_values({
    "tissue": "PBMC",
    "condition": "treated",
    "organism": "human",
    "batch": 1
})

# Validate with schema
curator = ln.curators.AnnDataCurator(adata, schema)
try:
    curator.validate()
    artifact = curator.save_artifact(key="validated/batch1.h5ad")
    print("Validation passed")
except ln.errors.ValidationError as e:
    print(f"Validation failed: {e}")

# Standardize cell type names using ontology
adata.obs["cell_type"] = bt.CellType.standardize(adata.obs["cell_type"])
```

### 5. Biological Ontologies (Bionty)

Access standardized biological vocabularies for annotation.

```python
import bionty as bt

# Available ontologies
# bt.Gene (Ensembl), bt.Protein (UniProt), bt.CellType (CL),
# bt.Tissue (Uberon), bt.Disease (Mondo), bt.Pathway (GO),
# bt.CellLine (CLO), bt.Phenotype (HPO), bt.Organism (NCBItaxon)

# Import and search ontology
bt.CellType.import_source()
results = bt.CellType.search("T helper")
print(results.head())

# Get specific term
t_cell = bt.CellType.get(name="T cell")
print(f"Ontology ID: {t_cell.ontology_id}")

# Explore hierarchy
children = t_cell.children.all()
parents = t_cell.parents.all()
print(f"Children: {[c.name for c in children]}")

# Validate a list of terms
validated = bt.CellType.validate(["T cell", "B cell", "Unknown_type"])
# Returns boolean array: [True, True, False]
```

### 6. Collections and Organization

Group related artifacts for batch operations.

```python
import lamindb as ln

# Create a collection
artifacts = ln.Artifact.filter(key__startswith="scrna/batch_").all()
collection = ln.Collection(artifacts, name="scRNA-seq batches Q1 2026").save()
print(f"Collection: {collection.name}, {collection.n_objects} artifacts")

# Query collection
for artifact in collection.artifacts.all():
    print(f"  {artifact.key}: {artifact.size} bytes")

# Organize with hierarchical keys
# Convention: project/experiment/datatype/file
# e.g., "immunology/exp42/scrna/counts.h5ad"
```

## Key Concepts

### Core Entity Model

| Entity | Purpose | Example |
|--------|---------|---------|
| **Artifact** | Versioned data object | `counts.h5ad`, `results.parquet` |
| **Run** | Single code execution | Notebook run, script execution |
| **Transform** | Code definition (notebook, script, pipeline) | `analysis.ipynb` |
| **Feature** | Typed metadata field | `tissue`, `condition`, `batch` |
| **Collection** | Group of related artifacts | "Experiment batches" |
| **ULabel** | Universal label for custom categorization | "high_quality", "pilot" |

### Data Types Supported

| Format | Method | Use Case |
|--------|--------|----------|
| DataFrame | `Artifact.from_df()` | Tabular data, metadata tables |
| AnnData | `Artifact.from_anndata()` | Single-cell data |
| MuData | `Artifact.from_mudata()` | Multi-modal data |
| Any file | `Artifact("path")` | Images, FASTQ, custom formats |
| Zarr | Via zarr extra | Large array data |
| TileDB-SOMA | Via tiledbsoma extra | Scalable cell-level queries |

### track() / finish() Pattern

Every analysis session should be wrapped:
```python
ln.track(params={"key": "value"})   # Start: captures code, environment, user
# ... analysis ...
ln.finish()                          # End: finalizes lineage links
```

## Common Workflows

### Workflow: Multi-Experiment Data Lakehouse

```python
import lamindb as ln
import anndata as ad

ln.track()

# Register multiple experiments
data_files = ["batch1.h5ad", "batch2.h5ad", "batch3.h5ad"]
tissues = ["PBMC", "bone_marrow", "PBMC"]
conditions = ["control", "treated", "treated"]

for i, (file, tissue, condition) in enumerate(zip(data_files, tissues, conditions)):
    adata = ad.read_h5ad(file)
    artifact = ln.Artifact.from_anndata(
        adata, key=f"scrna/batch_{i}.h5ad", description=f"scRNA-seq batch {i}"
    ).save()
    artifact.features.add_values({
        "tissue": tissue, "condition": condition, "batch": i
    })
    print(f"Registered batch {i}: {artifact.uid}")

# Query across all experiments
treated_pbmc = ln.Artifact.filter(
    key__startswith="scrna/",
    features__tissue="PBMC",
    features__condition="treated"
).all()
print(f"Found {len(treated_pbmc)} matching datasets")

# Load and concatenate
import anndata as ad
adatas = [a.load() for a in treated_pbmc]
combined = ad.concat(adatas)
print(f"Combined: {combined.shape}")

ln.finish()
```

### Workflow: Validated Data Curation

```python
import lamindb as ln
import bionty as bt
import anndata as ad

ln.track()

# 1. Import ontologies
bt.CellType.import_source()
bt.Gene.import_source(organism="human")

# 2. Load raw data
adata = ad.read_h5ad("raw_counts.h5ad")
print(f"Raw: {adata.shape}")

# 3. Validate and standardize cell types
validated = bt.CellType.validate(adata.obs["cell_type"].unique())
if not all(validated):
    adata.obs["cell_type"] = bt.CellType.standardize(adata.obs["cell_type"])

# 4. Validate gene names
gene_validated = bt.Gene.validate(adata.var_names)
print(f"Valid genes: {sum(gene_validated)}/{len(gene_validated)}")

# 5. Curate and save
curator = ln.curators.AnnDataCurator(adata, schema)
curator.validate()
artifact = curator.save_artifact(key="curated/validated_counts.h5ad")
print(f"Saved curated artifact: {artifact.uid}")

ln.finish()
```

### Workflow: Nextflow Pipeline Integration

1. In each Nextflow process, import lamindb and call `ln.track()`
2. Load input artifacts with `ln.Artifact.get(key=...)`; cache to local path
3. Run analysis; save output as new artifact with `ln.Artifact(...).save()`
4. Call `ln.finish()` — lineage automatically links inputs to outputs

## Key Parameters

| Parameter | Function | Default | Options | Effect |
|-----------|----------|---------|---------|--------|
| `key` | `Artifact()` | None | String path | Hierarchical storage key (e.g., "project/data.h5ad") |
| `description` | `Artifact()` | None | String | Human-readable description |
| `revises` | `Artifact()` | None | Artifact | Previous version to revise |
| `params` | `ln.track()` | None | Dict | Parameters for the current run |
| `organism` | `bt.Gene.import_source()` | None | "human", "mouse" | Organism for ontology |
| `permanent` | `.delete()` | False | True/False | Permanent vs archive deletion |
| `__startswith` | `.filter()` | — | String | Key prefix filter |
| `__gte`, `__lte` | `.filter()` | — | Value | Greater/less than or equal |
| `__contains` | `.filter()` | — | String | Substring match |

## Best Practices

1. **Always wrap analysis with `ln.track()` / `ln.finish()`**: This captures lineage automatically. Without it, artifacts have no provenance.

2. **Use hierarchical keys**: Structure as `project/experiment/datatype/file.ext` (e.g., `immunology/exp42/scrna/counts.h5ad`). This enables prefix-based queries.

3. **Anti-pattern — duplicating data instead of versioning**: Use the `revises=` parameter to create new versions, not new keys for the same dataset.

4. **Validate early**: Run schema validation before analysis. Catching bad metadata early saves debugging time downstream.

5. **Use ontologies for standardization**: Map free-text labels to ontology terms (e.g., "T helper cell" → CL:0000912). This enables cross-dataset queries.

6. **Anti-pattern — loading large files without checking size**: Use `.filter().df()` to inspect metadata first, then `.load()` or `.open()` (backed mode) for large files.

7. **Query metadata first, load data second**: Filter with `.filter()` to find relevant artifacts, then load only what you need.

## Common Recipes

### Recipe: Bulk Dataset Registration

```python
import lamindb as ln
from pathlib import Path

ln.track()

data_dir = Path("raw_data/")
for fcs_file in data_dir.glob("*.fcs"):
    artifact = ln.Artifact(str(fcs_file), key=f"flow_cytometry/{fcs_file.name}").save()
    artifact.features.add_values({"assay": "flow_cytometry", "source": "batch_import"})
    print(f"Registered: {fcs_file.name} -> {artifact.uid}")

ln.finish()
```

### Recipe: View and Export Lineage

```python
import lamindb as ln

artifact = ln.Artifact.get(key="results/final_analysis.h5ad")

# View lineage graph (opens in browser or notebook)
artifact.view_lineage()

# Programmatic lineage access
run = artifact.run
print(f"Created by: {run.transform.name}")
print(f"User: {run.created_by.name}")
print(f"Date: {run.created_at}")
print(f"Input artifacts: {[a.key for a in run.input_artifacts.all()]}")
```

### Recipe: Ontology Hierarchy Exploration

```python
import bionty as bt

bt.CellType.import_source()
t_cell = bt.CellType.get(name="T cell")

# Explore hierarchy
print(f"Parents: {[p.name for p in t_cell.parents.all()]}")
print(f"Children: {[c.name for c in t_cell.children.all()]}")

# Find all descendants
descendants = t_cell.children.all()
for child in descendants:
    grandchildren = child.children.all()
    print(f"  {child.name}: {[gc.name for gc in grandchildren]}")
```

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| `InstanceNotSetupError` | Instance not initialized | Run `lamin init --storage ./data --name my-project` |
| `ln.track()` fails | No transform context | Run inside a notebook/script, not REPL; or pass `transform` explicitly |
| Artifact `key` conflict | Key already exists (not a version) | Use `revises=` for versioning, or choose a different key |
| `ValidationError` | Data doesn't match schema | Run `curator.validate()` to see specific failures; standardize terms |
| Slow queries on large instances | No index on filtered field | Use `.df()` for overview first; add database indexes for frequently filtered fields |
| Ontology import fails | Network issue or wrong organism | Check internet connection; specify `organism="human"` explicitly |
| `FileNotFoundError` on `.cache()` | Cloud artifact not synced | Check storage connectivity; use `artifact.load()` instead for in-memory access |

## Related Skills

- **anndata-annotated-data** — AnnData format used as primary data container in LaminDB for single-cell data
- **scanpy-scrna-seq** — single-cell analysis pipeline; LaminDB manages data that scanpy analyzes
- **scvi-tools-single-cell** — deep learning models for single-cell; integrates with LaminDB for data/model tracking

## References

- [LaminDB documentation](https://docs.lamin.ai) — official user guide and API reference
- [LaminDB tutorial](https://docs.lamin.ai/tutorial) — step-by-step introduction
- [Bionty documentation](https://docs.lamin.ai/bionty) — biological ontology management
- [LaminDB GitHub](https://github.com/laminlabs/lamindb) — source code and issues
