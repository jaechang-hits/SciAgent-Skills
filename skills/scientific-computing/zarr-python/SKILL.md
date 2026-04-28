---
name: zarr-python
description: "Chunked N-D arrays with compression and cloud storage. NumPy-style indexing. Backends: local, S3, GCS, ZIP, memory. Dask/Xarray integration for parallel and labeled computation. For lineage use lamindb; for labeled arrays use xarray."
license: MIT
---

# Zarr Python — Chunked N-D Arrays

## Overview

Zarr is a Python library for storing large N-dimensional arrays with chunking, compression, and parallel I/O. It provides NumPy-compatible indexing with pluggable storage backends (local, cloud, in-memory), making it the standard format for cloud-native scientific data pipelines.

## When to Use

- Storing arrays too large for memory with chunked access (out-of-core computing)
- Cloud-native data workflows with S3 or GCS storage backends
- Parallel read/write with Dask for large-scale computation
- Hierarchical data organization (groups of named arrays with metadata)
- Converting between formats (HDF5 → Zarr, NetCDF → Zarr)
- Appending time-series data incrementally without rewriting
- For **labeled, coordinate-aware arrays** (time, lat, lon), use xarray with Zarr backend instead
- For **data management, lineage, and ontology validation**, use lamindb (which uses Zarr as a storage format)

## Prerequisites

```bash
pip install zarr
# Cloud storage support
pip install s3fs   # Amazon S3
pip install gcsfs  # Google Cloud Storage
```

Requires Python 3.11+.

## Quick Start

```python
import zarr
import numpy as np

# Create a chunked, compressed 2D array
z = zarr.create_array(
    store="data/my_array.zarr",
    shape=(10000, 10000),
    chunks=(1000, 1000),
    dtype="f4"
)

# Write with NumPy-style indexing
z[:, :] = np.random.random((10000, 10000)).astype("f4")

# Read a slice (only reads needed chunks)
subset = z[0:100, 0:100]
print(f"Shape: {subset.shape}, dtype: {subset.dtype}")
# Shape: (100, 100), dtype: float32
```

## Core API

### 1. Array Creation

```python
import zarr
import numpy as np

# Empty arrays
z = zarr.zeros(shape=(10000, 10000), chunks=(1000, 1000), dtype="f4", store="data.zarr")
z = zarr.ones((5000, 5000), chunks=(500, 500), dtype="f4")
z = zarr.full((1000, 1000), fill_value=42, chunks=(100, 100), dtype="i4")

# From existing NumPy data
data = np.arange(10000, dtype="f4").reshape(100, 100)
z = zarr.array(data, chunks=(10, 10), store="from_numpy.zarr")
print(f"Created: shape={z.shape}, chunks={z.chunks}, dtype={z.dtype}")

# Create like another array (matches shape, chunks, dtype)
z2 = zarr.zeros_like(z)
```

```python
# Open existing array
z = zarr.open_array("data.zarr", mode="r+")  # Read-write
z = zarr.open_array("data.zarr", mode="r")   # Read-only
z = zarr.open("data.zarr")                   # Auto-detect array vs group
```

### 2. Reading, Writing, and Indexing

```python
import zarr
import numpy as np

z = zarr.zeros((10000, 10000), chunks=(1000, 1000), dtype="f4")

# Write slices
z[0, :] = np.arange(10000, dtype="f4")
z[10:20, 50:60] = np.random.random((10, 10)).astype("f4")
z[:] = 42  # Fill entire array

# Read slices (returns NumPy array)
row = z[5, :]
block = z[0:100, 0:100]
print(f"Row shape: {row.shape}, block shape: {block.shape}")

# Advanced indexing
z.vindex[[0, 5, 10], [2, 8, 15]]  # Coordinate (fancy) indexing
z.oindex[0:10, [5, 10, 15]]       # Orthogonal indexing
z.blocks[0, 0]                     # Block/chunk indexing

# Resize and append
z.resize(15000, 15000)
z.append(np.random.random((1000, 10000)).astype("f4"), axis=0)
```

### 3. Chunking and Sharding

Chunk shape is the most important performance parameter.

```python
import zarr
from zarr.codecs import ShardingCodec

# Chunk aligned with access pattern
# Row-wise access → chunk spans columns
z_row = zarr.zeros((10000, 10000), chunks=(10, 10000), dtype="f4")

# Column-wise access → chunk spans rows
z_col = zarr.zeros((10000, 10000), chunks=(10000, 10), dtype="f4")

# Mixed access → balanced square chunks (~1MB each for float32)
z_bal = zarr.zeros((10000, 10000), chunks=(512, 512), dtype="f4")
# 512*512*4 bytes = ~1MB per chunk

# Sharding: group small chunks into larger storage objects
# Useful when millions of small chunks cause filesystem overhead
z_sharded = zarr.create_array(
    store="sharded.zarr",
    shape=(100000, 100000),
    chunks=(100, 100),       # Small chunks for fine-grained access
    shards=(1000, 1000),     # Groups 100 chunks per shard
    dtype="f4"
)
print(f"Chunks: {z_sharded.chunks}, shards reduce file count")
```

**Chunk size guidelines**:
- Target **1–10 MB per chunk** (minimum 1 MB)
- Align chunk shape with your most common access pattern
- Entire chunks load into memory during read → don't exceed available RAM
- Entire shards load into memory during write

### 4. Compression

```python
from zarr.codecs.blosc import BloscCodec
from zarr.codecs import GzipCodec, ZstdCodec, BytesCodec
import zarr

# Default: Blosc with Zstandard (good balance)
z = zarr.zeros((1000, 1000), chunks=(100, 100), dtype="f4")

# Explicit Blosc configuration
z = zarr.create_array(
    store="compressed.zarr",
    shape=(1000, 1000), chunks=(100, 100), dtype="f4",
    codecs=[BloscCodec(cname="zstd", clevel=5, shuffle="shuffle")]
)

# Speed-optimized (LZ4)
z_fast = zarr.create_array(
    store="fast.zarr",
    shape=(1000, 1000), chunks=(100, 100), dtype="f4",
    codecs=[BloscCodec(cname="lz4", clevel=1)]
)

# Maximum compression (Gzip level 9)
z_small = zarr.create_array(
    store="small.zarr",
    shape=(1000, 1000), chunks=(100, 100), dtype="f4",
    codecs=[GzipCodec(level=9)]
)

# No compression
z_raw = zarr.create_array(
    store="raw.zarr",
    shape=(1000, 1000), chunks=(100, 100), dtype="f4",
    codecs=[BytesCodec()]
)
```

**Codec selection**: Blosc/Zstd (default, balanced) → LZ4 (fastest) → Gzip (smallest). Enable `shuffle="shuffle"` for numeric data — it reorders bytes for better compression ratios.

### 5. Storage Backends

```python
import zarr
import numpy as np
from zarr.storage import LocalStore, MemoryStore, ZipStore

# Local filesystem (default — string paths create LocalStore automatically)
z = zarr.open_array("data/array.zarr", mode="w", shape=(1000, 1000),
                    chunks=(100, 100), dtype="f4")

# In-memory (not persisted)
store = MemoryStore()
z_mem = zarr.open_array(store=store, mode="w", shape=(1000, 1000),
                        chunks=(100, 100), dtype="f4")

# ZIP file storage
store = ZipStore("data.zip", mode="w")
z_zip = zarr.open_array(store=store, mode="w", shape=(1000, 1000),
                        chunks=(100, 100), dtype="f4")
z_zip[:] = np.random.random((1000, 1000)).astype("f4")
store.close()  # IMPORTANT: must close ZipStore
```

```python
# Cloud storage: Amazon S3
import s3fs

s3 = s3fs.S3FileSystem(anon=False)
store = s3fs.S3Map(root="my-bucket/path/array.zarr", s3=s3)
z = zarr.open_array(store=store, mode="w", shape=(1000, 1000),
                    chunks=(500, 500), dtype="f4")
z[:] = np.random.random((1000, 1000)).astype("f4")

# Consolidate metadata for faster subsequent reads
zarr.consolidate_metadata(store)

# Google Cloud Storage
import gcsfs
gcs = gcsfs.GCSFileSystem(project="my-project")
store = gcsfs.GCSMap(root="my-bucket/path/array.zarr", gcs=gcs)
```

**Cloud best practices**: consolidate metadata, use 5–100 MB chunks, enable sharding to reduce object count, use Dask for parallel I/O.

### 6. Groups and Hierarchies

```python
import zarr

# Create hierarchical structure (like HDF5 groups)
root = zarr.group(store="hierarchy.zarr")

# Create sub-groups
temperature = root.create_group("temperature")
precipitation = root.create_group("precipitation")

# Create arrays within groups
temp_arr = temperature.create_array(
    name="t2m",
    shape=(365, 720, 1440),
    chunks=(1, 720, 1440),
    dtype="f4"
)
precip_arr = precipitation.create_array(
    name="prcp",
    shape=(365, 720, 1440),
    chunks=(1, 720, 1440),
    dtype="f4"
)

# Access by path
arr = root["temperature/t2m"]
print(root.tree())
# /
#  ├── temperature
#  │   └── t2m (365, 720, 1440) f4
#  └── precipitation
#      └── prcp (365, 720, 1440) f4
```

### 7. Attributes and Metadata

```python
import zarr

z = zarr.zeros((1000, 1000), chunks=(100, 100), dtype="f4")

# Attach metadata (must be JSON-serializable)
z.attrs["description"] = "Temperature data in Kelvin"
z.attrs["units"] = "K"
z.attrs["processing_version"] = 2.1

print(z.attrs["units"])  # K

# Group-level attributes
root = zarr.group("data.zarr")
root.attrs["project"] = "Climate Analysis"
root.attrs["institution"] = "Research Institute"
```

## Key Concepts

### Chunk Size Selection Guide

| Data Shape | Access Pattern | Recommended Chunks | Rationale |
|-----------|---------------|-------------------|-----------|
| (N, M) 2D | Row-wise | (small, M) | Each chunk spans full row |
| (N, M) 2D | Column-wise | (N, small) | Each chunk spans full column |
| (N, M) 2D | Random/mixed | (√(1MB/dtype), √(1MB/dtype)) | Balanced ~1MB per chunk |
| (T, H, W) time series | Time slice | (1, H, W) | One timestep per chunk |
| (T, H, W) time series | Spatial region | (T, small, small) | Full time for region |

**1 MB rule**: For float32 (4 bytes), 1 MB = 262,144 elements. For float64 (8 bytes), 1 MB = 131,072 elements.

### Consolidated Metadata

For stores with many arrays (10+), consolidate metadata into a single read:

```python
zarr.consolidate_metadata("data.zarr")
root = zarr.open_consolidated("data.zarr")  # Single metadata read
```

Critical for cloud storage (reduces N metadata requests to 1). Caveat: becomes stale if arrays update without re-consolidation.

## Common Workflows

### Workflow: Cloud-Native Data Pipeline

```python
import zarr
import numpy as np
import s3fs

# Step 1: Write to S3 with cloud-optimized chunks
s3 = s3fs.S3FileSystem()
store = s3fs.S3Map(root="s3://my-bucket/experiment.zarr", s3=s3)

root = zarr.group(store=store)
data_arr = root.create_array(
    name="measurements",
    shape=(10000, 10000),
    chunks=(500, 500),  # ~1MB chunks, good for cloud
    dtype="f4"
)
data_arr[:] = np.random.random((10000, 10000)).astype("f4")
data_arr.attrs["experiment"] = "batch_42"

# Step 2: Consolidate metadata
zarr.consolidate_metadata(store)

# Step 3: Read from anywhere
store_read = s3fs.S3Map(root="s3://my-bucket/experiment.zarr", s3=s3)
root_read = zarr.open_consolidated(store_read)
subset = root_read["measurements"][0:100, 0:100]
print(f"Read subset: {subset.shape}")
```

### Workflow: Dask Parallel Computation

```python
import dask.array as da
import zarr
import numpy as np

# Step 1: Create large Zarr array
z = zarr.open("large_data.zarr", mode="w", shape=(100000, 100000),
              chunks=(1000, 1000), dtype="f4")
# (populate with data...)

# Step 2: Load as Dask array (lazy — no data loaded yet)
dask_arr = da.from_zarr("large_data.zarr")
print(f"Dask array: {dask_arr.shape}, {dask_arr.npartitions} partitions")

# Step 3: Compute in parallel (out-of-core)
col_means = dask_arr.mean(axis=0).compute()
print(f"Column means: {col_means.shape}")

# Step 4: Write Dask result back to Zarr
large_random = da.random.random((100000, 100000), chunks=(1000, 1000))
da.to_zarr(large_random, "output.zarr")
```

### Workflow: Xarray-Zarr for Labeled Data

```python
import xarray as xr
import numpy as np
import pandas as pd

# Step 1: Create labeled dataset
ds = xr.Dataset(
    {
        "temperature": (["time", "lat", "lon"], np.random.random((365, 180, 360)).astype("f4")),
        "precipitation": (["time", "lat", "lon"], np.random.random((365, 180, 360)).astype("f4")),
    },
    coords={
        "time": pd.date_range("2024-01-01", periods=365),
        "lat": np.arange(-90, 90, 1.0),
        "lon": np.arange(-180, 180, 1.0),
    }
)

# Step 2: Save to Zarr
ds.to_zarr("climate.zarr")

# Step 3: Open with lazy loading
ds_loaded = xr.open_zarr("climate.zarr")
print(ds_loaded)

# Step 4: Label-based selection (only reads needed chunks)
subset = ds_loaded.sel(time="2024-06", lat=slice(30, 60))
print(f"June subset: {subset['temperature'].shape}")
```

### Workflow: Format Conversion

```python
import zarr
import numpy as np

# HDF5 → Zarr
import h5py
with h5py.File("data.h5", "r") as h5:
    z = zarr.array(h5["dataset_name"][:], chunks=(1000, 1000), store="from_hdf5.zarr")

# NumPy → Zarr
data = np.load("data.npy")
z = zarr.array(data, chunks="auto", store="from_numpy.zarr")

# Zarr → NetCDF (via Xarray)
import xarray as xr
ds = xr.open_zarr("data.zarr")
ds.to_netcdf("data.nc")
```

## Key Parameters

| Parameter | Module | Default | Options | Effect |
|-----------|--------|---------|---------|--------|
| `shape` | `create_array` | Required | Tuple of ints | Array dimensions |
| `chunks` | `create_array` | Auto | Tuple of ints, `"auto"` | Chunk shape per dimension |
| `shards` | `create_array` | None | Tuple of ints | Shard shape (groups chunks) |
| `dtype` | `create_array` | `"f8"` | NumPy dtype | Data type |
| `codecs` | `create_array` | Blosc/Zstd | List of codec objects | Compression pipeline |
| `mode` | `open_array` | `"r"` | `"r"`, `"r+"`, `"w"`, `"a"` | File access mode |
| `store` | All | LocalStore | Store object or path | Storage backend |
| `cname` | `BloscCodec` | `"zstd"` | `"lz4"`, `"zstd"`, `"gzip"`, etc. | Compressor algorithm |
| `clevel` | `BloscCodec` | 5 | 0–9 | Compression level |
| `shuffle` | `BloscCodec` | `"noshuffle"` | `"shuffle"`, `"bitshuffle"` | Byte reordering for compression |

## Best Practices

1. **Target 1–10 MB per chunk**: Smaller chunks = more metadata overhead; larger chunks = more memory per read. For float32: 512×512 ≈ 1 MB.

2. **Align chunks with access patterns**: The most common query dimension should be contiguous within chunks. A 65× performance difference is possible with misaligned chunks.

3. **Anti-pattern — loading entire array with `z[:]`**: For large arrays, use Dask (`da.from_zarr`) or process in explicit chunks. `z[:]` loads everything into memory.

4. **Consolidate metadata for cloud stores**: Call `zarr.consolidate_metadata(store)` after creating all arrays. Then open with `zarr.open_consolidated()`. This reduces N metadata reads to 1 — critical for S3/GCS latency.

5. **Close ZipStore explicitly**: Unlike other stores, `ZipStore` requires `store.close()` after writing. Forgetting this corrupts the ZIP file.

6. **Use sharding for millions of small chunks**: When chunk count exceeds ~100k, filesystem overhead dominates. Sharding groups chunks into fewer storage objects.

7. **Anti-pattern — choosing chunk shape based on array shape alone**: Always consider access pattern first, then optimize chunk size. A "nice" shape (1000, 1000) may be terrible if you always read rows.

## Common Recipes

### Recipe: Profiling Array Performance

```python
import zarr

z = zarr.open("data.zarr")
print(z.info)
# Shows: type, shape, chunks, dtype, compressor, storage size

print(f"Compressed: {z.nbytes_stored / 1e6:.2f} MB")
print(f"Uncompressed: {z.nbytes / 1e6:.2f} MB")
print(f"Ratio: {z.nbytes / z.nbytes_stored:.1f}x")
```

### Recipe: Time Series Append

```python
import zarr
import numpy as np

# Create extensible array (start with 0 timesteps)
z = zarr.open("timeseries.zarr", mode="a",
              shape=(0, 720, 1440),
              chunks=(1, 720, 1440),
              dtype="f4")

# Append new timesteps incrementally
for day in range(365):
    new_step = np.random.random((1, 720, 1440)).astype("f4")
    z.append(new_step, axis=0)

print(f"Final shape: {z.shape}")  # (365, 720, 1440)
```

### Recipe: Parallel Write with Dask

```python
import dask.array as da

# Generate large dataset in parallel
data = da.random.random((100000, 100000), chunks=(1000, 1000))

# Write to Zarr (parallel across chunks)
da.to_zarr(data, "parallel_output.zarr")

# Verify
z = da.from_zarr("parallel_output.zarr")
print(f"Written: {z.shape}, {z.npartitions} partitions")
```

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| Slow read performance | Chunk shape misaligned with access pattern | Profile access pattern; realign chunks (row-access → wide chunks) |
| `MemoryError` on read | Loading entire array or chunk too large | Use Dask `da.from_zarr()` for out-of-core; reduce chunk size |
| High cloud latency | Many small metadata reads | Call `zarr.consolidate_metadata(store)` then `open_consolidated()` |
| Corrupted ZIP store | Forgot to call `store.close()` | Always close ZipStore after write; use context manager |
| Concurrent write conflicts | Multiple processes writing overlapping chunks | Use `ProcessSynchronizer` or ensure non-overlapping chunk writes |
| Poor compression ratio | No shuffle on numeric data | Add `shuffle="shuffle"` to BloscCodec |
| Stale consolidated metadata | Arrays modified after consolidation | Re-run `zarr.consolidate_metadata()` after updates |
| `ModuleNotFoundError: s3fs` | Missing cloud storage dependency | `pip install s3fs` (S3) or `pip install gcsfs` (GCS) |

## Related Skills

- **lamindb-data-management** — uses Zarr as a storage backend; provides data management, lineage, and ontology validation on top of Zarr arrays
- **anndata-annotated-data** — AnnData objects can be backed by Zarr stores for out-of-core single-cell data
- **sympy-symbolic-math** — unrelated but co-exists in scientific-computing category

## References

- [Zarr Python documentation](https://zarr.readthedocs.io/) — official user guide and API reference
- [Zarr specifications](https://zarr-specs.readthedocs.io/) — file format specification (V2, V3)
- [Zarr GitHub](https://github.com/zarr-developers/zarr-python) — source code, issues, changelog
- [NumCodecs](https://numcodecs.readthedocs.io/) — compression codec library used by Zarr
