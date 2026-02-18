---
name: "imaging-data-commons"
description: "Query NCI Imaging Data Commons (IDC) for cancer radiology and pathology imaging datasets hosted on Google Cloud. Search DICOM collections by modality, anatomical site, cancer type, or collection name. Download images via Google Cloud Storage or IDAT tool. 50TB+ of publicly accessible DICOM images. Requires Google Cloud account for large downloads; small queries work without billing. For local DICOM processing use pydicom-medical-imaging; for whole-slide pathology use histolab."
license: "CC0-1.0"
---

# NCI Imaging Data Commons

## Overview

NCI Imaging Data Commons (IDC) is NCI's cloud-based repository for cancer imaging data, hosting 50+ TB of publicly accessible DICOM images spanning radiology (CT, MRI, PET) and pathology (whole slide images) across 100+ collections. All data is hosted on Google Cloud Storage and BigQuery, enabling SQL queries over DICOM metadata without downloading. IDC integrates with Google Colab and BigQuery, making large-scale imaging research accessible without local storage.

## When to Use

- Searching for publicly available cancer imaging datasets by modality, cancer type, or anatomical site
- Downloading DICOM image series for model training (segmentation, classification, detection)
- Querying DICOM metadata at scale using SQL (BigQuery) without downloading the full dataset
- Exploring available imaging collections before committing to a full download
- Accessing pathology whole-slide images (WSI) and radiology scans from TCIA collections
- Building reproducible imaging ML pipelines with versioned public datasets
- For local DICOM file processing use `pydicom-medical-imaging`; for WSI preprocessing use `histolab`

## Prerequisites

- **Python packages**: `requests`, `pandas`, `google-cloud-bigquery` (for SQL queries), `idc-index`
- **Data requirements**: collection names, DICOM tags (StudyInstanceUID, SeriesInstanceUID), modality
- **Environment**: Google Cloud account (free tier sufficient for metadata queries); `gcloud auth` for downloads
- **Rate limits**: IDC web API: no hard limit; BigQuery: free tier = 1 TB/month queries

```bash
pip install requests pandas idc-index google-cloud-bigquery
# For downloads: install Google Cloud SDK and authenticate
# gcloud auth application-default login
```

## Quick Start

```python
from idc_index import index

# List all available IDC collections
idc_client = index.IDCClient()
collections = idc_client.get_collections()
print(f"Available IDC collections: {len(collections)}")
print(collections[["collection_id", "cancer_type", "location", "species"]].head(10))
```

## Core API

### Query 1: List and Search Collections

Browse available IDC collections and filter by cancer type or modality.

```python
from idc_index import index
import pandas as pd

idc_client = index.IDCClient()

# Get all collections with metadata
collections = idc_client.get_collections()
print(f"Total IDC collections: {len(collections)}")
print("Columns:", list(collections.columns))

# Filter for lung CT collections
lung_ct = collections[
    (collections["cancer_type"].str.contains("Lung", case=False, na=False)) |
    (collections["location"].str.contains("Lung", case=False, na=False))
]
print(f"\nLung-related collections: {len(lung_ct)}")
print(lung_ct[["collection_id", "cancer_type", "location"]].head())
```

```python
# List modalities available in a collection
collection_id = "LIDC-IDRI"  # Lung Image Database Consortium
series = idc_client.get_series(collection_id=collection_id)
modalities = series["Modality"].value_counts()
print(f"\nModalities in {collection_id}:")
print(modalities)
print(f"Total series: {len(series)}")
```

### Query 2: Search Series by Modality and Body Part

Query for specific imaging series within collections.

```python
from idc_index import index
import pandas as pd

idc_client = index.IDCClient()

# Get all CT series for lung cancer
ct_series = idc_client.get_series(
    collection_id="LIDC-IDRI",
    modality="CT"
)
print(f"CT series in LIDC-IDRI: {len(ct_series)}")
print(ct_series[["PatientID", "StudyInstanceUID", "SeriesInstanceUID", "Modality"]].head())
```

```python
# Query across all collections for specific modality + body part
all_series = idc_client.get_series()  # All IDC series metadata
mr_brain = all_series[
    (all_series["Modality"] == "MR") &
    (all_series["BodyPartExamined"].str.contains("BRAIN", case=False, na=False))
]
print(f"Brain MRI series across IDC: {len(mr_brain)}")
print(mr_brain["collection_id"].value_counts().head(10))
```

### Query 3: BigQuery SQL Queries for DICOM Metadata

Use BigQuery for scalable DICOM metadata queries across all IDC data.

```python
from google.cloud import bigquery
import pandas as pd

# BigQuery client (requires Google Cloud authentication)
client = bigquery.Client(project="your-gcp-project-id")

# Count series by modality and cancer type
query = """
SELECT
    Modality,
    collection_id,
    COUNT(DISTINCT SeriesInstanceUID) AS num_series,
    COUNT(DISTINCT PatientID) AS num_patients
FROM `bigquery-public-data.idc_current.dicom_all`
WHERE Modality IN ('CT', 'MR', 'PET')
GROUP BY Modality, collection_id
ORDER BY num_series DESC
LIMIT 20
"""
df = client.query(query).to_dataframe()
print(df.to_string(index=False))
```

```python
# Find all lung CT studies with tumor segmentation
query2 = """
SELECT DISTINCT
    d.PatientID,
    d.StudyInstanceUID,
    d.collection_id,
    d.Modality,
    d.BodyPartExamined
FROM `bigquery-public-data.idc_current.dicom_all` d
WHERE d.collection_id IN ('LIDC-IDRI', 'TCGA-LUAD', 'TCGA-LUSC')
  AND d.Modality = 'CT'
LIMIT 100
"""
df2 = client.query(query2).to_dataframe()
print(f"Lung CT studies: {len(df2)}")
print(df2.head())
```

### Query 4: Download Images via idc-index

Download DICOM series using the idc-index download utilities.

```python
from idc_index import index
import os

idc_client = index.IDCClient()

# Download a specific series by SeriesInstanceUID
series_uid = "1.3.6.1.4.1.14519.5.2.1.6279.6001.179049373636438705059720603192"
output_dir = "./downloaded_dicom/"
os.makedirs(output_dir, exist_ok=True)

idc_client.download_dicom_series(
    seriesInstanceUID=series_uid,
    downloadDir=output_dir,
    quiet=False
)
print(f"Downloaded series to {output_dir}")

# List downloaded files
import glob
files = glob.glob(f"{output_dir}/**/*.dcm", recursive=True)
print(f"Downloaded {len(files)} DICOM files")
```

### Query 5: Collection Summary and Statistics

Get detailed statistics for a specific IDC collection.

```python
from idc_index import index
import pandas as pd

idc_client = index.IDCClient()

collection_id = "TCGA-GBM"  # Glioblastoma
series = idc_client.get_series(collection_id=collection_id)

print(f"Collection: {collection_id}")
print(f"Total series: {len(series)}")
print(f"Patients: {series['PatientID'].nunique()}")
print(f"Studies: {series['StudyInstanceUID'].nunique()}")

modality_summary = series.groupby("Modality")["SeriesInstanceUID"].count()
print(f"\nModalities:")
print(modality_summary)

if "BodyPartExamined" in series.columns:
    print(f"\nBody parts: {series['BodyPartExamined'].value_counts().head()}")
```

### Query 6: IDC REST API for Collection Metadata

Use the IDC REST API for collection information without local client.

```python
import requests, pandas as pd

IDC_API = "https://api.imaging.datacommons.cancer.gov/v1"

# Get all collections
r = requests.get(f"{IDC_API}/collections")
r.raise_for_status()
collections = r.json()["collections"]
print(f"IDC collections via REST API: {len(collections)}")

# Convert to DataFrame
df = pd.DataFrame(collections)
print(df.columns.tolist())
print(df[["collection_id", "cancer_type", "location"]].head(5).to_string(index=False))
```

```python
# Get metadata for a specific collection
collection_id = "LIDC-IDRI"
r = requests.get(f"{IDC_API}/collections/{collection_id}")
if r.ok:
    data = r.json()
    print(f"Collection: {collection_id}")
    print(f"  Description: {str(data)[:200]}")
```

## Key Concepts

### DICOM Hierarchy

IDC organizes data following the DICOM hierarchy: **Collection** → **Patient** → **Study** (StudyInstanceUID) → **Series** (SeriesInstanceUID) → **Instance** (SOPInstanceUID). Downloads are typically at the Series level.

### Google Cloud Storage Access

All IDC images are stored in Google Cloud Storage (GCS) buckets. Files can be accessed directly via `gs://idc-open-data/{SeriesInstanceUID}/` paths using `gsutil` or the GCS Python client. BigQuery metadata tables link DICOM tags to GCS paths.

## Common Workflows

### Workflow 1: Build a Curated Dataset for ML Training

**Goal**: Select imaging series from IDC matching specific criteria and prepare download manifest.

```python
from idc_index import index
import pandas as pd

idc_client = index.IDCClient()

# Step 1: Get all series across IDC
all_series = idc_client.get_series()
print(f"Total IDC series: {len(all_series)}")

# Step 2: Filter for CT scans in specific cancer types
target_collections = ["LIDC-IDRI", "TCGA-LUAD", "TCGA-LUSC"]
ct_lung = all_series[
    (all_series["collection_id"].isin(target_collections)) &
    (all_series["Modality"] == "CT")
].copy()

print(f"CT lung series: {len(ct_lung)}")
print(ct_lung.groupby("collection_id")["SeriesInstanceUID"].count())

# Step 3: Sample balanced dataset
sample_size = 100
ct_sampled = ct_lung.sample(min(sample_size, len(ct_lung)), random_state=42)

# Step 4: Save manifest
ct_sampled[["SeriesInstanceUID", "PatientID", "collection_id", "Modality"]].to_csv(
    "ct_lung_manifest.csv", index=False
)
print(f"\nSaved manifest with {len(ct_sampled)} series → ct_lung_manifest.csv")
```

### Workflow 2: Download and Inspect a Collection Sample

**Goal**: Download a small sample from a collection for exploratory analysis.

```python
from idc_index import index
import pydicom
import glob
import os

idc_client = index.IDCClient()

# Get series from a collection
series = idc_client.get_series(collection_id="TCGA-GBM", modality="MR")
print(f"Brain MRI series: {len(series)}")

# Download first 2 series for exploration
sample_series = series["SeriesInstanceUID"].iloc[:2].tolist()
output_dir = "./tcga_gbm_sample/"
os.makedirs(output_dir, exist_ok=True)

for uid in sample_series:
    print(f"Downloading series: {uid[:30]}...")
    idc_client.download_dicom_series(
        seriesInstanceUID=uid,
        downloadDir=output_dir,
        quiet=True
    )

# Inspect one downloaded DICOM file
dcm_files = glob.glob(f"{output_dir}/**/*.dcm", recursive=True)
if dcm_files:
    ds = pydicom.dcmread(dcm_files[0])
    print(f"\nDICOM file info:")
    print(f"  Patient ID  : {ds.PatientID}")
    print(f"  Modality    : {ds.Modality}")
    print(f"  Rows x Cols : {ds.Rows} x {ds.Columns}")
    print(f"  Pixel array : {ds.pixel_array.shape}")
```

## Key Parameters

| Parameter | Module | Default | Range / Options | Effect |
|-----------|--------|---------|-----------------|--------|
| `collection_id` | get_series/download | — | IDC collection name | Filter by specific collection |
| `modality` | get_series | — | `"CT"`, `"MR"`, `"PET"`, `"SM"` (slide microscopy) | Filter by imaging modality |
| `seriesInstanceUID` | download | required | DICOM UID string | Specific series to download |
| `downloadDir` | download | required | directory path | Local directory for DICOM files |
| `quiet` | download | `False` | `True`/`False` | Suppress download progress output |
| BigQuery dataset | BigQuery | `idc_current` | `idc_current`, `idc_v17` | IDC BigQuery version |

## Best Practices

1. **Use idc-index for metadata filtering first**: Always query metadata (series, modality, patient count) before downloading. Downloads can be large (GB to TB per collection).

2. **Use BigQuery for complex cross-collection queries**: The IDC BigQuery tables (`bigquery-public-data.idc_current.dicom_all`) enable SQL-based filtering across all 50+ TB of metadata without any downloads.

3. **Download only needed series**: IDC series can range from 1 MB to 5 GB; always save a manifest CSV of SeriesInstanceUIDs to download rather than bulk-downloading entire collections.

4. **Version-lock your datasets**: IDC releases versioned datasets (v14, v15…). Always note the IDC version used (`idc_client.get_idc_version()`) for reproducibility.

5. **Use Google Cloud credits**: IDC BigQuery queries and GCS egress are free within certain limits; for large downloads, consider requesting Google Cloud for Researchers credits.

## Common Recipes

### Recipe: Find Collections by Cancer Type

When to use: Identify all IDC collections covering a specific cancer type.

```python
from idc_index import index

idc_client = index.IDCClient()
collections = idc_client.get_collections()
glioma = collections[collections["cancer_type"].str.contains("Glioma|Glioblastoma", case=False, na=False)]
print(glioma[["collection_id", "cancer_type", "location"]].to_string(index=False))
```

### Recipe: Count Patients with Both CT and MRI

When to use: Find patients with multimodal imaging for fusion or cross-modal studies.

```python
from idc_index import index
import pandas as pd

idc_client = index.IDCClient()
series = idc_client.get_series(collection_id="TCGA-GBM")

ct_patients = set(series[series["Modality"] == "CT"]["PatientID"])
mr_patients = set(series[series["Modality"] == "MR"]["PatientID"])
multimodal = ct_patients & mr_patients
print(f"Patients with both CT and MRI: {len(multimodal)}")
```

### Recipe: Get GCS Path for a Series

When to use: Construct Google Cloud Storage URL to access DICOM files directly.

```python
from idc_index import index

idc_client = index.IDCClient()
series = idc_client.get_series(collection_id="LIDC-IDRI", modality="CT")
uid = series["SeriesInstanceUID"].iloc[0]

# IDC GCS path pattern
gcs_path = f"gs://idc-open-data/{uid}/"
print(f"GCS path: {gcs_path}")
print(f"Access with: gsutil ls {gcs_path}")
```

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| `idc_index` authentication error | Not authenticated with GCP | Run `gcloud auth application-default login` |
| BigQuery billing error | No billing account linked | Link billing in GCP console; first 1 TB/month of queries is free |
| Download very slow | GCS egress charges or throttling | Use Google Compute Engine or Colab (co-located with GCS) |
| `SeriesInstanceUID` not found | Old idc-index version cached | Run `idc_client.fetch_index()` to refresh the local index |
| `pydicom` can't read downloaded file | Corrupted download | Re-download; verify file size matches expected |
| Empty modality filter result | Modality string capitalization | Use uppercase modality codes: `"CT"` not `"ct"` |

## Related Skills

- `pydicom-medical-imaging` — Local DICOM file processing for downloaded IDC images
- `histolab-wsi-processing` — Whole slide image preprocessing for IDC pathology (SM modality) series
- `pathml` — ML pipeline for computational pathology using IDC slide data

## References

- [NCI Imaging Data Commons](https://imaging.datacommons.cancer.gov/) — Official IDC portal
- [IDC documentation](https://learn.canceridc.dev/) — Getting started guides and tutorials
- [idc-index PyPI](https://pypi.org/project/idc-index/) — Python client library
- [IDC BigQuery public data](https://console.cloud.google.com/bigquery?project=bigquery-public-data&dataset=idc_current) — BigQuery tables for DICOM metadata
