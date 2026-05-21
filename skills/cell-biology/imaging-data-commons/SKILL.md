---
name: "imaging-data-commons"
description: "Query and download NCI Imaging Data Commons (IDC) cancer radiology and pathology datasets via the idc-index Python client. No authentication required: the parquet index ships inside the pip wheel, SQL runs locally via DuckDB, and DICOM downloads stream from public S3/GCS buckets through s5cmd. Use sql_query() for DuckDB cohort selection, get_collections/get_patients/get_dicom_studies/get_dicom_series for hierarchical browsing, download_from_selection() for downloads, and get_viewer_URL() for OHIF/Slim links. Use pydicom-medical-imaging for local DICOM reading; histolab for whole-slide pathology preprocessing."
license: "MIT"
---

# NCI Imaging Data Commons (idc-index)

## Overview

NCI Imaging Data Commons (IDC) is the largest public collection of cancer imaging data, hosting 175+ DICOM collections (CT, MR, PET, slide microscopy, segmentations, structured reports). The idc-index Python client ships the entire IDC metadata catalog as a parquet file bundled inside the pip wheel; IDCClient() loads it into DuckDB, so sql_query() runs locally with zero network calls.

Image downloads stream from public AWS S3 (default) or Google Cloud Storage buckets via the bundled s5cmd executable. No GCP/AWS credentials, no BigQuery billing, no service account JSON.

## When to Use

- Searching publicly available cancer imaging datasets by modality, cancer type, anatomical site, or DICOM tag
- Building reproducible ML cohorts (segmentation, classification, multimodal) from versioned IDC releases
- Querying DICOM metadata at scale using SQL across all 175+ collections without any downloads
- Downloading specific DICOM series for local processing or model training
- Generating OHIF/Slim viewer URLs to share or inspect series interactively in a browser
- Use pydicom-medical-imaging instead when you only need to read, edit, or anonymize DICOM files that you already have locally
- For whole-slide pathology preprocessing (tiling, stain normalization) after download, use histolab instead

## Prerequisites

- **Python packages**: `idc-index` (>=0.12), `pandas`, `pydicom` (for reading DICOM files after download)
- **Data requirements**: none for querying. For downloads, free disk space matching `series_size_MB`
- **Environment**: **no authentication required**. All data is publicly accessible. The wheel bundles both the parquet index and the `s5cmd` executable used for high-speed S3 transfers
- **Rate limits**: none for local SQL queries (DuckDB on local parquet). Bulk downloads are limited by network bandwidth, not by API quotas

```bash
# Skip when already provisioned in a pixi or conda env
pip install idc-index pydicom
```

## Quick Start

```python
from idc_index import IDCClient

client = IDCClient()
print('IDC version:', client.get_idc_version())
print('Collections:', len(client.get_collections()))
print('First 5:', client.get_collections()[:5])
```

```python
df = client.sql_query("""
    SELECT collection_id, COUNT(DISTINCT SeriesInstanceUID) AS n_series
    FROM index
    WHERE Modality = 'CT'
    GROUP BY collection_id
    ORDER BY n_series DESC LIMIT 5
""")
print(df)
```

## Core API

### Module 1: Client Initialization and Collections

IDCClient() is the single entry point. It loads the parquet index, registers it as the DuckDB table named index, and validates the bundled s5cmd. get_collections() returns a plain Python list of lowercase collection IDs such as nsclc_radiomics, lidc_idri, and tcga_gbm.

```python
from idc_index import IDCClient

client = IDCClient()
collections = client.get_collections()
print("total:", len(collections), "type:", type(collections).__name__)
print("lung-related:", [c for c in collections if "lung" in c or "nsclc" in c][:5])
```

### Module 2: sql_query (DuckDB Over the Local Index)

The recommended cohort-selection API. The table name is index; additional tables (prior_versions_index and optional sm_index, clinical_index) are auto-registered when installed. Returns a pandas DataFrame. Use this for any filter involving Modality, BodyPartExamined, series_size_MB, or arbitrary DICOM tags. The legacy get_series(collection_id=..., modality=...) signature no longer exists in idc-index.

```python
# Cohort: small CT series in NSCLC Radiomics, sorted by size for cheap testing
df = client.sql_query("""
    SELECT SeriesInstanceUID, StudyInstanceUID, PatientID, Modality, series_size_MB
    FROM index
    WHERE collection_id = 'nsclc_radiomics'
      AND Modality = 'CT'
    ORDER BY series_size_MB ASC
    LIMIT 5
""")
print(df[["PatientID", "Modality", "series_size_MB"]])
```

```python
# Cross-collection lung CT count, using DuckDB ILIKE for case-insensitive matching
df = client.sql_query("""
    SELECT collection_id, COUNT(DISTINCT SeriesInstanceUID) AS n
    FROM index
    WHERE Modality = 'CT' AND BodyPartExamined ILIKE '%LUNG%'
    GROUP BY collection_id
    ORDER BY n DESC LIMIT 5
""")
print(df)
```

### Module 3: Hierarchical Browsing (Patients, Studies, Series)

For DICOM-hierarchy navigation (Collection -> Patient -> Study -> Series), use the typed helpers. Each accepts an outputFormat of dict (default), df, or list. Note: get_dicom_series() takes a studyInstanceUID (not collection_id). Use sql_query() if you want to filter series by collection or modality.

```python
patients = client.get_patients('nsclc_radiomics', outputFormat='df')
print("patients:", patients.shape, list(patients.columns)[:5])

# Walk down the hierarchy from one patient
pid = patients["PatientID"].iloc[0]
studies = client.get_dicom_studies(pid, outputFormat='df')
print("studies for", pid, ":", studies.shape)

study_uid = studies["StudyInstanceUID"].iloc[0]
series = client.get_dicom_series(study_uid, outputFormat='df')
print("series in study:", series.shape, "modalities:", series["Modality"].unique().tolist())
```

### Module 4: download_from_selection (Modern Download Path)

The preferred download method. Accepts any combination of collection_id, patientId, studyInstanceUID, seriesInstanceUID, sopInstanceUID, or crdc_series_uuid (each a string or list). Filters apply in sequence. Use dry_run=True to size the cohort before pulling bytes. Files land under dirTemplate (default: %collection_id/%PatientID/%StudyInstanceUID/%Modality_%SeriesInstanceUID).

```python
import tempfile, glob, os

# Pick the smallest CT series for a fast smoke test (about 40 MB)
df = client.sql_query("""
    SELECT SeriesInstanceUID FROM index
    WHERE collection_id = 'nsclc_radiomics' AND Modality = 'CT'
    ORDER BY series_size_MB ASC LIMIT 1
""")
uid = df["SeriesInstanceUID"].iloc[0]

out = tempfile.mkdtemp(prefix='idc_dl_')
client.download_from_selection(
    downloadDir=out,
    seriesInstanceUID=[uid],
    quiet=True,
    show_progress_bar=False,
    source_bucket_location='aws',  # 'aws' (default) or 'gcs'
)
files = glob.glob(os.path.join(out, "**/*.dcm"), recursive=True)
print(f"downloaded {len(files)} DICOM files to {out}")
```

```python
# Size a cohort before downloading
client.download_from_selection(
    downloadDir='./preview',
    collection_id='nsclc_radiomics',
    dry_run=True,
)
```

### Module 5: download_dicom_series (Convenience Wrapper)

Single-series download. Internally calls download_from_selection(seriesInstanceUID=...). Accepts a string or list of UIDs.

```python
import tempfile, glob, os
out = tempfile.mkdtemp(prefix='idc_dl_')
client.download_dicom_series(
    seriesInstanceUID=uid,            # string or list
    downloadDir=out,
    quiet=True,
    show_progress_bar=False,
)
print("files:", len(glob.glob(os.path.join(out, "**/*.dcm"), recursive=True)))
```

### Module 6: get_viewer_URL (Browser Visualization)

Returns a shareable URL to the IDC OHIF (radiology) or Slim (slide microscopy) viewer. Auto-selects the viewer based on modality if viewer_selector is omitted.

```python
url = client.get_viewer_URL(seriesInstanceUID=uid)
print("Open in browser:", url)

# Force a specific viewer
url_v2 = client.get_viewer_URL(seriesInstanceUID=uid, viewer_selector='ohif_v2')
print(url_v2)
```

### Module 7: Inspecting Downloaded DICOM with pydicom

After download, files are organized under dirTemplate. Use pydicom for header and pixel inspection.

```python
import pydicom, glob, os
dcm_files = sorted(glob.glob(os.path.join(out, "**/*.dcm"), recursive=True))
ds = pydicom.dcmread(dcm_files[0])
print("PatientID:", ds.PatientID)
print("Modality :", ds.Modality)
print("Rows x Cols:", ds.Rows, "x", ds.Columns)
print("Pixel array:", ds.pixel_array.shape)
```

## Key Concepts

### Local-First, Auth-Free Architecture

The IDC client is unusual: client = IDCClient() is fully offline for queries. The parquet index (hundreds of MB, ships in idc-index-data) is read into memory and registered as the DuckDB table named index. Every sql_query(), get_collections(), get_patients(), etc. is a local pandas/DuckDB operation. Network traffic only happens during download_from_selection() / download_dicom_series(), which shell out to the bundled s5cmd executable to copy from public buckets (s3://idc-open-data/... by default; switch to gcs via source_bucket_location=gcs). Consequently: no gcloud auth, no GCP project ID, no BigQuery billing, no API keys.

### DICOM Hierarchy and Identifiers

IDC follows the standard DICOM model: Collection (collection_id, lowercase with underscores like nsclc_radiomics) -> Patient (PatientID) -> Study (StudyInstanceUID) -> Series (SeriesInstanceUID) -> Instance (SOPInstanceUID). Downloads operate at the series level by default. The crdc_series_uuid is an alternative immutable identifier preferred for long-term references.

### Versioning

The index is pinned to the installed idc-index-data package version (client.get_idc_version(), e.g., v24). For reproducibility, pin both idc-index and idc-index-data in your environment. Older releases remain accessible via the prior_versions_index table inside sql_query().

## Common Workflows

### Workflow 1: Cohort Selection -> Manifest -> Download

**Goal**: Build a CSV manifest of small CT series for ML prototyping, then download them.

```python
from idc_index import IDCClient
import pandas as pd, tempfile, os, glob

client = IDCClient()

# Step 1: SQL cohort: small CTs across three lung collections
cohort = client.sql_query("""
    SELECT SeriesInstanceUID, PatientID, collection_id, Modality, series_size_MB
    FROM index
    WHERE collection_id IN ('nsclc_radiomics', 'tcga_luad', 'tcga_lusc')
      AND Modality = 'CT'
      AND series_size_MB < 60
    ORDER BY series_size_MB ASC
""")
print(f"Cohort: {len(cohort)} series, total {cohort['series_size_MB'].sum():.1f} MB")

# Step 2: Save manifest
cohort.to_csv('ct_lung_manifest.csv', index=False)

# Step 3: Download a small subset
out = tempfile.mkdtemp(prefix='idc_cohort_')
client.download_from_selection(
    downloadDir=out,
    seriesInstanceUID=cohort["SeriesInstanceUID"].head(2).tolist(),
    quiet=True,
    show_progress_bar=False,
)
print("downloaded", len(glob.glob(os.path.join(out, "**/*.dcm"), recursive=True)), "files")
```

### Workflow 2: Hierarchical Inspection of One Patient

**Goal**: Drill from collection -> patient -> studies -> series -> DICOM headers without writing SQL.

```python
from idc_index import IDCClient
import tempfile, glob, os, pydicom

client = IDCClient()

# Pick first patient in the collection
patients = client.get_patients('nsclc_radiomics', outputFormat='df')
pid = patients["PatientID"].iloc[0]

studies = client.get_dicom_studies(pid, outputFormat='df')
series_df = client.get_dicom_series(studies["StudyInstanceUID"].iloc[0], outputFormat='df')
print(f"Patient {pid}: {len(studies)} studies, {len(series_df)} series in first study")
print("modalities:", series_df["Modality"].unique().tolist())

# Pick the smallest image series (CT/MR, not SR/SEG) and download
imaging = series_df[series_df["Modality"].isin(["CT", "MR", "PT"])]
target_uid = imaging.sort_values("series_size_MB").iloc[0]["SeriesInstanceUID"]
out = tempfile.mkdtemp(prefix='idc_one_')
client.download_dicom_series(seriesInstanceUID=target_uid, downloadDir=out,
                             quiet=True, show_progress_bar=False)

ds = pydicom.dcmread(sorted(glob.glob(os.path.join(out, "**/*.dcm"), recursive=True))[0])
print("first slice:", ds.Modality, ds.pixel_array.shape)
print("viewer:", client.get_viewer_URL(seriesInstanceUID=target_uid))
```

## Key Parameters

| Parameter | Module / Function | Default | Range / Options | Effect |
|-----------|-------------------|---------|-----------------|--------|
| outputFormat | get_patients / get_dicom_studies / get_dicom_series | dict | dict, df, list | Return type of accessor methods |
| seriesInstanceUID | download_from_selection / download_dicom_series | None | str or list[str] | Filter by DICOM SeriesInstanceUID |
| collection_id | download_from_selection / get_patients | None / required | lowercase string(s) like nsclc_radiomics | Filter by collection (lowercase, underscored) |
| source_bucket_location | download_from_selection / download_dicom_series | aws | aws, gcs | Public bucket to pull from |
| dirTemplate | download_from_selection | %collection_id/%PatientID/%StudyInstanceUID/%Modality_%SeriesInstanceUID | template string with %-prefixed DICOM tags, or None for flat layout | On-disk folder hierarchy |
| dry_run | download_from_selection / download_dicom_series | False | True/False | Compute cohort size without downloading |
| use_s5cmd_sync | download_from_selection / download_dicom_series | False | True/False | Use s5cmd sync (resume partial) instead of cp |
| viewer_selector | get_viewer_URL | None (auto) | ohif_v2, ohif_v3, slim | Force a specific browser viewer |

## Best Practices

1. **Use sql_query() for any filter beyond a single hierarchy step**: It returns DataFrames, scales to the full ~10M-row index instantly via DuckDB, and supports arbitrary DICOM tags. Reach for get_patients / get_dicom_studies / get_dicom_series only when you already have the parent UID.

2. **Always dry-run large cohorts**: Calling download_from_selection(..., dry_run=True) prints the total size before any bytes move. A small collection like lidc_idri is ~120 GB, while nlst exceeds 10 TB.

3. **Pin both idc-index and idc-index-data**: The index version drives reproducibility. Record client.get_idc_version() (e.g., v24) in your dataset card or paper methods.

4. **Prefer AWS for most downloads**: source_bucket_location=aws is the default and is fastest from most academic networks. Switch to gcs only when running on GCP compute that is co-located with the bucket.

5. **Do not try to use the legacy BigQuery flow as a default**: bigquery-public-data.idc_current.dicom_all still works, but requires GCP auth and billing and is no longer the recommended path. See Recipes for one optional snippet.

## Common Recipes

### Recipe: Cross-Modal Patient Cohort (CT and MR for the Same Patient)

When to use: Build a multimodal study where each patient must have both modalities.

```python
df = client.sql_query("""
    SELECT PatientID
    FROM index
    WHERE collection_id = 'tcga_gbm'
    GROUP BY PatientID
    HAVING SUM(CASE WHEN Modality = 'CT' THEN 1 ELSE 0 END) > 0
       AND SUM(CASE WHEN Modality = 'MR' THEN 1 ELSE 0 END) > 0
""")
print(f"Patients with both CT and MR in TCGA-GBM: {len(df)}")
```

### Recipe: Generate a Batch of Viewer URLs for QA

When to use: Send collaborators a shortlist of series to inspect visually.

```python
sample = client.sql_query("""
    SELECT SeriesInstanceUID, Modality
    FROM index WHERE collection_id = 'lidc_idri' AND Modality = 'CT'
    LIMIT 5
""")
for _, row in sample.iterrows():
    print(row.Modality, client.get_viewer_URL(seriesInstanceUID=row.SeriesInstanceUID))
```

### Recipe: Optional Advanced (BigQuery for Cross-Dataset Joins)

When to use: You need to join IDC metadata against another BigQuery public dataset (e.g., TCGA clinical) and have a GCP project with billing already configured. For all other use cases, prefer sql_query().

```python
# Requires: a google-cloud-bigquery install and gcloud application-default credentials.
from google.cloud import bigquery
bq = bigquery.Client(project='your-gcp-project-id')
df = bq.query("""
    SELECT collection_id, Modality, COUNT(DISTINCT SeriesInstanceUID) AS n
    FROM `bigquery-public-data.idc_current.dicom_all`
    WHERE Modality IN ('CT', 'MR', 'PET')
    GROUP BY collection_id, Modality
    ORDER BY n DESC LIMIT 20
""").to_dataframe()
print(df)
```

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| ImportError: No module named `idc_index` | Package not installed | Run pip install idc-index (no auth setup needed) |
| IDCClient() slow on first call | Loading parquet index into memory (1-3 s, one-time per process) | Reuse the client across queries; do not re-instantiate per call |
| sql_query: Catalog Error: Table idc_index does not exist | Wrong table name | The DuckDB table is named `index`, not `idc_index` or `dicom_all` |
| get_dicom_series(collection_id=..., modality=...) raises TypeError | Outdated API; that signature was removed | Use sql_query with WHERE collection_id and Modality filters instead |
| download_from_selection errors with s5cmd: command not found | Bundled s5cmd not on PATH | Reinstall idc-index; the wheel bundles s5cmd. On NixOS/non-glibc systems, set IDC_INDEX_S5CMD_EXE to a system s5cmd |
| Downloads stall or are very slow | Network bottleneck, not auth | Try source_bucket_location=gcs if on GCP; otherwise use use_s5cmd_sync=True to resume |
| ValueError: collection_id ... does not exist | Collection ID is case-sensitive and underscored | Use lowercase with underscores: lidc_idri not LIDC-IDRI; check client.get_collections() |
| pydicom cannot read pixel data | Compressed transfer syntax | Install pylibjpeg, pylibjpeg-libjpeg, gdcm, then retry ds.pixel_array |

## Related Skills

- **pydicom-medical-imaging** - Read, edit, and anonymize the DICOM files you downloaded from IDC
- **histolab-wsi-processing** - Tile and stain-normalize whole-slide images (IDC SM modality)
- **pathml** - End-to-end ML pipelines for computational pathology that consume IDC slide collections

## References

- [idc-index GitHub](https://github.com/ImagingDataCommons/idc-index) - Source, README, and issue tracker (authoritative API)
- [idc-index on PyPI](https://pypi.org/project/idc-index/) - Latest releases
- [learn.canceridc.dev](https://learn.canceridc.dev/) - Official IDC tutorials, notebooks, and conceptual guides
- [IDC portal](https://imaging.datacommons.cancer.gov/) - Browser UI for exploring collections and viewer URLs
- [IDC BigQuery dataset](https://console.cloud.google.com/bigquery?project=bigquery-public-data&dataset=idc_current) - Optional advanced/cross-dataset SQL (requires GCP billing)
