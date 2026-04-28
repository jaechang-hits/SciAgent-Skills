---
name: dask-parallel-computing
description: "Parallel/distributed computing for larger-than-RAM data. Components: DataFrames (parallel pandas), Arrays (parallel NumPy), Bags, Futures, Schedulers. Scales laptop to HPC cluster. For single-machine speed use polars; for out-of-core without cluster use vaex."
license: BSD-3-Clause
---

# Dask — Parallel & Distributed Computing

## Overview

Dask is a Python library for parallel and distributed computing that scales familiar pandas/NumPy APIs to larger-than-memory datasets. It provides five main components (DataFrames, Arrays, Bags, Futures, Schedulers) and scales from single-machine multi-core to multi-node HPC clusters.

## When to Use

- Processing datasets that exceed available RAM (10 GB–100 TB)
- Parallelizing pandas or NumPy operations across multiple cores
- Processing multiple files efficiently (CSV, Parquet, JSON, HDF5, Zarr)
- Building custom parallel workflows with task dependencies
- Distributing workloads across HPC clusters (SLURM, Kubernetes)
- Streaming/ETL pipelines for unstructured data (logs, JSON records)
- For **in-memory single-machine speed**: use polars instead
- For **out-of-core single-machine analytics**: use vaex instead

## Prerequisites

```bash
pip install dask[complete]        # All components
pip install dask[dataframe]       # DataFrames only
pip install dask[distributed]     # Distributed scheduler + dashboard
pip install dask-jobqueue          # HPC cluster integration (SLURM, PBS)
```

## Core API

### 1. DataFrames — Parallel Pandas

```python
import dask.dataframe as dd

# Read multiple files as a single DataFrame
ddf = dd.read_csv('data/2024-*.csv')
ddf = dd.read_parquet('data/', columns=['id', 'value', 'category'])

# Operations are lazy until .compute()
filtered = ddf[ddf['value'] > 100]
result = filtered.groupby('category').agg({'value': ['mean', 'sum']}).compute()
print(result.shape)  # (n_categories, 2)

# Custom operations via map_partitions (preferred over apply)
def normalize_partition(df):
    df['norm_value'] = (df['value'] - df['value'].mean()) / df['value'].std()
    return df

ddf = ddf.map_partitions(normalize_partition)

# Joins
ddf_merged = ddf.merge(lookup_ddf, on='category', how='left')

# Write results
ddf.to_parquet('output/', engine='pyarrow')
```

```python
# Repartitioning for optimal chunk sizes
ddf = ddf.repartition(npartitions=20)         # By count
ddf = ddf.repartition(partition_size='100MB')  # By size

# Index management for sorted operations
ddf = ddf.set_index('timestamp', sorted=True)

# Debugging
print(f"Partitions: {ddf.npartitions}")
print(f"Dtypes: {ddf.dtypes}")
sample = ddf.get_partition(0).compute()  # Inspect first partition
```

### 2. Arrays — Parallel NumPy

```python
import dask.array as da
import numpy as np

# Create from various sources
x = da.random.random((100000, 1000), chunks=(10000, 1000))
x = da.from_array(np_array, chunks=(10000, 1000))
x = da.from_zarr('large_dataset.zarr')

# Standard operations (lazy)
y = (x - x.mean(axis=0)) / x.std(axis=0)  # Normalize
z = da.dot(x.T, x)                          # Matrix multiply
u, s, v = da.linalg.svd(x)                  # SVD

# Compute and persist
result = y.mean(axis=0).compute()
print(result.shape)  # (1000,)
```

```python
# Custom operations with map_blocks
def custom_filter(block):
    from scipy.ndimage import gaussian_filter
    return gaussian_filter(block, sigma=2)

filtered = da.map_blocks(custom_filter, x, dtype=x.dtype)

# Rechunking for different access patterns
x_rechunked = x.rechunk({0: 5000, 1: 500})

# Save to disk
da.to_zarr(y, 'normalized.zarr')
```

### 3. Bags — Unstructured Data Processing

```python
import dask.bag as db
import json

# Read unstructured data
bag = db.read_text('logs/*.json').map(json.loads)

# Functional operations
valid = bag.filter(lambda x: x['status'] == 'success')
ids = valid.pluck('user_id')
flat = bag.map(lambda x: x['tags']).flatten()

# Aggregation — use foldby instead of groupby (much faster)
counts = bag.foldby(
    key='category',
    binop=lambda total, x: total + x['amount'],
    initial=0,
    combine=lambda a, b: a + b,
    combine_initial=0
).compute()

# Convert to DataFrame for structured analysis
ddf = valid.to_dataframe(meta={'user_id': 'str', 'amount': 'float64', 'category': 'str'})
```

### 4. Futures — Task-Based Parallelism

```python
from dask.distributed import Client

client = Client()  # Local cluster with all cores
print(client.dashboard_link)  # http://localhost:8787

# Submit individual tasks (executes immediately, not lazy)
def process(x, param):
    return x ** param

future = client.submit(process, 42, param=2)
print(future.result())  # 1764

# Map over many inputs
futures = client.map(process, range(100), param=2)
results = client.gather(futures)
print(len(results))  # 100
```

```python
# Scatter large data to workers (avoids repeated transfers)
import numpy as np
big_data = np.random.random((10000, 1000))
data_future = client.scatter(big_data, broadcast=True)

# Submit tasks using scattered data
futures = [client.submit(process_chunk, data_future, i) for i in range(10)]
results = client.gather(futures)

# Progressive result processing
from dask.distributed import as_completed
for future in as_completed(futures):
    result = future.result()
    print(f"Completed: {result}")

# Coordination primitives
from dask.distributed import Lock, Queue, Event
lock = Lock('resource-lock')
with lock:
    # Thread-safe operation across workers
    pass

client.close()
```

### 5. Schedulers & Configuration

```python
import dask

# Global scheduler setting
dask.config.set(scheduler='threads')       # Default: GIL-releasing numeric work
dask.config.set(scheduler='processes')     # Pure Python, GIL-bound work
dask.config.set(scheduler='synchronous')   # Debugging with pdb

# Context manager for temporary change
with dask.config.set(scheduler='synchronous'):
    result = computation.compute()  # Can use pdb here

# Per-compute override
result = ddf.mean().compute(scheduler='processes')

# Distributed scheduler with resource control
from dask.distributed import Client
client = Client(n_workers=4, threads_per_worker=2, memory_limit='4GB')
print(client.dashboard_link)
```

```python
# HPC cluster integration
from dask_jobqueue import SLURMCluster
from dask.distributed import Client

cluster = SLURMCluster(
    cores=24, memory='100GB',
    walltime='02:00:00', queue='regular'
)
cluster.scale(jobs=10)  # Request 10 SLURM jobs
client = Client(cluster)

# Adaptive scaling
cluster.adapt(minimum=2, maximum=20)

result = computation.compute()
client.close()
```

## Key Concepts

### Component Selection Guide

| Data Type | Component | When to Use |
|-----------|-----------|-------------|
| Tabular (CSV, Parquet) | **DataFrames** | Standard pandas-like operations at scale |
| Numeric arrays (HDF5, Zarr) | **Arrays** | NumPy operations, linear algebra, image processing |
| Text, JSON, logs | **Bags** | ETL/cleaning → convert to DataFrame for analysis |
| Custom parallel tasks | **Futures** | Dynamic workflows, parameter sweeps, task dependencies |
| Any of above | **Schedulers** | Control execution backend (threads/processes/distributed) |

**Control level**: DataFrames/Arrays/Bags = high-level lazy API. Futures = low-level immediate execution.

### Lazy Evaluation Model

All DataFrames, Arrays, and Bags build a **task graph** — nothing executes until `.compute()` or `.persist()`.

- `.compute()` — execute and return result to local memory
- `.persist()` — execute and keep result on workers (for reuse across multiple computations)
- `dask.compute(a, b, c)` — compute multiple results in a single pass (shares intermediates)

### Chunk Size Strategy

Target: **~100 MB per chunk** (or 10 chunks per core in worker memory).

| Chunk Size | Effect |
|-----------|--------|
| Too large (>1 GB) | Memory overflow, poor parallelization |
| Optimal (~100 MB) | Good parallelism, manageable memory |
| Too small (<1 MB) | Excessive scheduling overhead |

**Example**: 8 cores, 32 GB RAM → target ~400 MB per chunk (32 GB / 8 cores / 10).

### Scheduler Selection Guide

| Scheduler | Overhead | Best For | GIL |
|-----------|----------|----------|-----|
| `threads` (default) | ~10 µs/task | NumPy, pandas, scikit-learn | Affected |
| `processes` | ~10 ms/task | Pure Python, text processing | Not affected |
| `synchronous` | ~1 µs/task | Debugging with pdb | N/A |
| `distributed` | ~1 ms/task | Dashboard, clusters, advanced features | Configurable |

## Common Workflows

### Workflow 1: Multi-File ETL Pipeline

```python
import dask.dataframe as dd
import dask

# Extract: Read all CSV files
ddf = dd.read_csv('raw_data/*.csv', dtype={'amount': 'float64'})

# Transform: Clean and process
ddf = ddf[ddf['status'] == 'valid']
ddf['amount'] = ddf['amount'].fillna(0)
ddf = ddf.dropna(subset=['category'])

# Aggregate
summary = ddf.groupby('category').agg({'amount': ['sum', 'mean', 'count']})

# Load: Save as Parquet (columnar, compressed)
summary.to_parquet('output/summary.parquet')
print(f"Processed {len(ddf)} rows across {ddf.npartitions} partitions")
```

### Workflow 2: Large-Scale Array Processing

```python
import dask.array as da

# Load large scientific dataset
x = da.from_zarr('experiment_data.zarr')  # e.g., (50000, 50000) float64
print(f"Shape: {x.shape}, Chunks: {x.chunks}")

# Normalize per-column
x_norm = (x - x.mean(axis=0)) / x.std(axis=0)

# Compute covariance matrix
cov = da.dot(x_norm.T, x_norm) / (x_norm.shape[0] - 1)

# SVD for dimensionality reduction (top-k)
u, s, v = da.linalg.svd_compressed(x_norm, k=50)

# Save results
da.to_zarr(u, 'pca_components.zarr')
print(f"Explained variance (top 5): {(s[:5]**2 / (s**2).sum()).compute()}")
```

### Workflow 3: Unstructured Data to Analysis

This workflow is a simple combination of Bags (Section 3) → DataFrames (Section 1): read JSON logs with Bags, filter/transform, convert to DataFrame for groupby analysis. Each step maps directly to Core API examples above.

## Key Parameters

| Parameter | Module | Default | Description |
|-----------|--------|---------|-------------|
| `npartitions` | DataFrame | auto | Number of partitions (controls parallelism) |
| `partition_size` | DataFrame | — | Target size per partition (e.g., '100MB') |
| `chunks` | Array | required | Chunk dimensions (e.g., `(10000, 1000)`) |
| `blocksize` | Bag | '128 MiB' | File read block size |
| `scheduler` | All | 'threads' | Execution backend ('threads', 'processes', 'synchronous') |
| `n_workers` | Distributed | auto | Number of worker processes |
| `threads_per_worker` | Distributed | auto | Threads per worker |
| `memory_limit` | Distributed | auto | Per-worker memory limit (e.g., '4GB') |
| `sorted` | `set_index` | False | Whether data is pre-sorted (enables optimizations) |
| `meta` | `map_partitions` | — | Output DataFrame/Series structure template |

## Best Practices

1. **Let Dask handle data loading** — Never load data into pandas/numpy first then convert. Use `dd.read_csv()` / `da.from_zarr()` directly.

2. **Batch compute calls** — Use `dask.compute(a, b, c)` instead of calling `.compute()` in loops. Allows sharing intermediates.

3. **Use `map_partitions` over `apply`** — `ddf.apply(func, axis=1)` creates one task per row. `ddf.map_partitions(func)` creates one task per partition.

4. **Persist reused intermediates** — Call `.persist()` on data accessed multiple times, then `del` when done.

5. **Use the dashboard** — `client.dashboard_link` shows task progress, memory usage, worker states. Essential for diagnosing performance issues.

6. **Anti-pattern — Excessively large task graphs**: If `len(ddf.__dask_graph__())` returns millions, increase chunk sizes or use `map_partitions`/`map_blocks` to fuse operations.

7. **Anti-pattern — Wrong scheduler for workload**: Using threads for pure Python text processing (GIL-bound) or processes for NumPy operations (unnecessary serialization overhead).

## Common Recipes

### Recipe: Dask-ML Integration

```python
from dask_ml.preprocessing import StandardScaler
from dask_ml.model_selection import train_test_split
import dask.array as da

X = da.random.random((100000, 50), chunks=(10000, 50))
y = da.random.randint(0, 2, size=100000, chunks=10000)

# Preprocessing
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# Train/test split
X_train, X_test, y_train, y_test = train_test_split(X_scaled, y, test_size=0.2)
print(f"Train: {X_train.shape}, Test: {X_test.shape}")
```

### Recipe: Actors for Stateful Computation

```python
from dask.distributed import Client

client = Client()

class RunningStats:
    def __init__(self):
        self.count = 0
        self.total = 0.0

    def add(self, value):
        self.count += 1
        self.total += value
        return self.total / self.count

# Create actor on a worker
stats = client.submit(RunningStats, actor=True).result()

# Call methods (~1ms roundtrip)
for v in [10, 20, 30]:
    mean = stats.add(v).result()
    print(f"Running mean: {mean}")

client.close()
```

### Recipe: Kubernetes Cluster

```python
from dask_kubernetes import KubeCluster
from dask.distributed import Client

cluster = KubeCluster()
cluster.adapt(minimum=2, maximum=50)
client = Client(cluster)

# Run computation on auto-scaling cluster
result = large_computation.compute()
client.close()
```

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| `MemoryError` during `.compute()` | Result too large for local memory | Use `.to_parquet()` or `.persist()` instead of `.compute()` |
| Slow computation start | Task graph has millions of tasks | Increase chunk sizes; use `map_partitions`/`map_blocks` |
| Poor parallelization | GIL contention with threads scheduler | Switch to `scheduler='processes'` for Python-heavy code |
| `TypeError` in `map_partitions` | Missing or wrong `meta` parameter | Provide `meta=pd.DataFrame({'col': pd.Series(dtype='float64')})` |
| Workers killed (OOM) | Chunks exceed worker memory | Decrease chunk size; increase `memory_limit` |
| `KilledWorker` exception | Worker process crashed | Check worker logs; reduce memory per task; increase `memory_limit` |
| Slow joins/merges | Data not pre-sorted on join key | Call `ddf.set_index('key', sorted=True)` before join |
| `NotImplementedError` | Operation not supported by Dask | Use `map_partitions` with pandas equivalent |
| Dashboard not accessible | Distributed client not started | Use `client = Client()` to enable distributed scheduler |
| Data type mismatch across partitions | Inconsistent CSV files | Specify `dtype` explicitly in `dd.read_csv()` |

## Bundled Resources

- **`references/collections_guide.md`** — Detailed DataFrames, Arrays, and Bags guide with comprehensive code examples for reading, transforming, aggregating, and writing data. Covers `map_partitions` patterns, meta parameter, chunking strategies, `map_blocks`, `foldby`, and collection conversion. Consolidated from original `dataframes.md`, `arrays.md`, and `bags.md`. Original `best-practices.md` content relocated to Best Practices section and Key Concepts inline.
- **`references/distributed_computing.md`** — Futures API, distributed coordination primitives (Locks, Queues, Events, Variables), Actors, scheduler configuration, HPC cluster setup (SLURM, Kubernetes), adaptive scaling, dashboard monitoring, and performance profiling. Consolidated from original `futures.md` and `schedulers.md`.

Not migrated: Original had 6 reference files. `best-practices.md` content consolidated into Best Practices section and Key Concepts (chunk strategy, scheduler selection). Remaining content organized into 2 reference files covering the 5 main components.

## Related Skills

- **polars-dataframes** — In-memory single-machine DataFrame library; faster than Dask for data that fits in RAM
- **zarr-python** — Chunked array storage format; primary Dask Array persistence backend
- **scikit-learn-machine-learning** — ML library; Dask-ML provides distributed wrappers

## References

- Official Documentation: https://docs.dask.org/
- Dask Best Practices: https://docs.dask.org/en/stable/best-practices.html
- Dask-ML: https://ml.dask.org/
- Dask-Jobqueue (HPC): https://jobqueue.dask.org/
