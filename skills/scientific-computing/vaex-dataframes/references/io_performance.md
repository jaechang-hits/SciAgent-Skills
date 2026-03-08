# I/O & Performance

Advanced file I/O patterns, cloud storage, database integration, state management, and performance optimization strategies for Vaex DataFrames.

## HDF5 and Parquet Compression

HDF5 supports optional compression. Uncompressed files are memory-mappable (instant load); compressed files require decompression on read. Parquet supports columnar codecs but is never memory-mapped.

```python
import vaex
import numpy as np
import os

df = vaex.from_arrays(
    x=np.random.normal(0, 1, 1_000_000),
    y=np.random.normal(0, 1, 1_000_000),
)

# HDF5 compression options
df.export_hdf5('/tmp/data_none.hdf5')                        # No compression (memory-mappable)
df.export_hdf5('/tmp/data_gzip.hdf5', compression='gzip')    # gzip (levels 1-9 via 'gzip-9')
df.export_hdf5('/tmp/data_lzf.hdf5', compression='lzf')      # lzf — fast, moderate ratio
df.export_hdf5('/tmp/data_blosc.hdf5', compression='blosc')   # blosc — best speed/size balance

# Parquet compression codecs
df.export_parquet('/tmp/data_snappy.parquet', compression='snappy')  # Default, fast
df.export_parquet('/tmp/data_brotli.parquet', compression='brotli')  # Higher ratio, slower
df.export_parquet('/tmp/data_gzip.parquet', compression='gzip')      # Widely compatible

for f in ['/tmp/data_none.hdf5', '/tmp/data_blosc.hdf5', '/tmp/data_snappy.parquet', '/tmp/data_brotli.parquet']:
    print(f"{os.path.basename(f)}: {os.path.getsize(f) / 1e6:.1f} MB")
# Typical: none ~16 MB, blosc ~11 MB, snappy ~12 MB, brotli ~9 MB
```

**Trade-off**: Use uncompressed HDF5 for interactive analysis (instant memory-mapped loads). Use compressed HDF5/Parquet for archiving, network transfer, or cloud storage.

## Arrow Integration

Apache Arrow provides zero-copy interoperability with Polars, Pandas 2.0+, DuckDB, and Spark.

```python
import vaex
import pyarrow as pa

# Create from Arrow table
arrow_table = pa.table({'id': [1, 2, 3], 'score': [85.5, 92.1, 78.3]})
df = vaex.from_arrow_table(arrow_table)
print(f"From Arrow: {len(df)} rows, columns: {df.column_names}")

# Convert back to Arrow
arrow_out = df.to_arrow_table()
print(f"To Arrow: {arrow_out.num_rows} rows, schema: {arrow_out.schema}")

# Export to Arrow IPC (Feather v2) — memory-mappable, cross-language
df.export_arrow('/tmp/data.arrow')
df_reloaded = vaex.open('/tmp/data.arrow')  # Instant, memory-mapped
print(f"Arrow IPC reload: {len(df_reloaded)} rows")
```

## FITS File Support

FITS (Flexible Image Transport System) tables used in astronomy are memory-mapped like HDF5.

```python
import vaex

# Read FITS table (instant, memory-mapped)
# df = vaex.open('catalog.fits')
# df = vaex.open('multi_ext.fits', hdu=1)  # Multi-extension: specify HDU
# df.export_fits('output.fits')
# Practical: convert FITS to HDF5 for faster column access
# df.export_hdf5('catalog.hdf5')
print("FITS: vaex.open('file.fits'), export_fits('out.fits'), hdu= for multi-extension")
```

## Chunked I/O Processing

Process large CSV files incrementally without loading everything at once.

```python
import vaex
import numpy as np
import pandas as pd

pd.DataFrame({'x': np.random.normal(0, 1, 100_000), 'y': np.random.uniform(0, 10, 100_000)}).to_csv('/tmp/large.csv', index=False)

# Chunked conversion with chunk_size control
df = vaex.from_csv('/tmp/large.csv', convert='/tmp/large.hdf5', chunk_size=50_000)
print(f"Converted: {len(df)} rows")

# Manual chunk processing (custom per-chunk logic)
for i, chunk in enumerate(vaex.from_csv('/tmp/large.csv', chunk_size=25_000)):
    print(f"Chunk {i}: {len(chunk)} rows, x_mean={chunk.x.mean():.4f}")
```

## Cloud Storage (S3, GCS, Azure)

Vaex reads/writes cloud storage via fsspec backends. Install `s3fs` (AWS), `gcsfs` (GCS), or `adlfs` (Azure).

```python
import vaex

# AWS S3 (pip install s3fs) — uses ~/.aws/credentials or env vars
# df = vaex.open('s3://bucket/data.hdf5')
# df = vaex.open('s3://bucket/data.parquet',
#                storage_options={'key': 'AKIA...', 'secret': 'wJal...'})
# df.export_parquet('s3://bucket/output/result.parquet')

# Google Cloud Storage (pip install gcsfs)
# df = vaex.open('gs://bucket/data.parquet',
#                storage_options={'token': '/path/to/keyfile.json'})

# Azure Blob Storage (pip install adlfs)
# df = vaex.open('az://container/data.parquet',
#                storage_options={'account_name': 'acct', 'account_key': 'key'})

# Wildcard patterns work with cloud storage
# df = vaex.open('s3://bucket/year=2024/*.parquet')
print("Cloud: vaex.open('s3://...'), storage_options={credentials}")
```

## Vaex Server (Remote Data Access)

Remote DataFrame access over WebSocket. Client API is identical to local DataFrames.

```python
import vaex

# Server: vaex server --port 9000 --filename data.hdf5
# Or programmatically:
# df = vaex.open('data.hdf5'); df.server = vaex.server('ws://0.0.0.0:9000')

# Client: connect and compute (computation happens server-side)
# df = vaex.open('ws://server-host:9000/data')
# mean_val = df.x.mean()
# df_local = df[df.category == 'A'].to_copy()  # Download subset
print("Server: vaex.server('ws://0.0.0.0:9000'), Client: vaex.open('ws://host:9000/name')")
```

## Database Integration (SQL via Pandas Bridge)

Vaex bridges through pandas for SQL database reads and writes.

```python
import vaex

# Read: chunked SQL → Vaex (for large tables)
# import pandas as pd, sqlalchemy
# engine = sqlalchemy.create_engine('postgresql://user:pass@host/db')
# chunks = []
# for chunk in pd.read_sql('SELECT * FROM big_table', engine, chunksize=100_000):
#     chunks.append(vaex.from_pandas(chunk, copy_index=False))
# df = vaex.concat(chunks)

# Write: small subsets via pandas bridge
# df[df.category == 'important'].to_pandas_df().to_sql('results', engine, if_exists='replace', index=False)

# Best pattern: SQL → HDF5 one-time, then use HDF5
# df.export_hdf5('big_table.hdf5')
print("SQL pattern: pd.read_sql → vaex.from_pandas → export_hdf5 (one-time)")
```

## State Files (Pipeline Persistence)

State files save transformation pipelines (virtual columns, selections, ML transformers) as JSON. They do NOT save data.

```python
import vaex
import numpy as np

df = vaex.from_arrays(
    price=np.array([10.0, 20.0, 30.0, 40.0, 50.0]),
    quantity=np.array([5, 3, 8, 2, 6]),
)
df['revenue'] = df.price * df.quantity
df['tier'] = (df.price >= 30).where('premium', 'standard')
df.select(df.revenue > 100, name='high_value')

# Save: virtual columns, selections, ML transformers, renames (NOT data)
df.state_write('/tmp/pipeline.json')

# Apply to new data (same column names required)
df_new = vaex.from_arrays(price=np.array([15.0, 25.0, 35.0]), quantity=np.array([4, 7, 1]))
df_new.state_load('/tmp/pipeline.json')
print(f"Columns after state load: {df_new.column_names}")
print(f"Revenue from state: {df_new.revenue.tolist()}")  # [60.0, 175.0, 35.0]
```

## Archiving with Compression

Pattern for maintaining both a fast-access working copy and a compressed archive.

```python
import vaex
import numpy as np
import os

df = vaex.from_arrays(
    sensor_id=np.random.randint(0, 100, 200_000),
    reading=np.random.normal(25.0, 5.0, 200_000),
)

# Working copy: uncompressed HDF5 (memory-mappable, instant load)
df.export_hdf5('/tmp/working.hdf5')
# Archive: compressed HDF5 or Parquet (smaller, portable)
df.export_hdf5('/tmp/archive.hdf5', compression='blosc')
df.export_parquet('/tmp/archive.parquet', compression='brotli')

for f in ['/tmp/working.hdf5', '/tmp/archive.hdf5', '/tmp/archive.parquet']:
    print(f"{os.path.basename(f)}: {os.path.getsize(f) / 1e6:.1f} MB")
```

## Production Data Pipeline Pattern

```python
import vaex
import numpy as np

np.random.seed(42)
for year in [2022, 2023, 2024]:
    df = vaex.from_arrays(
        timestamp=np.random.randint(0, 365, 10_000) + (year - 2022) * 365,
        value=np.random.lognormal(3, 1, 10_000),
        region=np.random.choice(['US', 'EU', 'APAC'], 10_000),
    )
    df.export_hdf5(f'/tmp/data_{year}.hdf5')

# Load → engineer → batch stats → export → save state
df = vaex.open('/tmp/data_*.hdf5')
df['log_value'] = df.value.log()
df['year'] = (df.timestamp // 365).astype('int32') + 2022
stats = vaex.execute([df.value.mean(delay=True), df.value.std(delay=True)])
print(f"Combined {len(df):,} rows. Value: mean={stats[0]:.2f}, std={stats[1]:.2f}")
df.export_hdf5('/tmp/processed_all.hdf5')
df.state_write('/tmp/etl_state.json')
```

## Async Operations and Caching

Vaex supports promises/futures via `delay=True` for non-blocking batch execution. Results are automatically cached and deduplicated.

```python
import vaex
import numpy as np

df = vaex.from_arrays(x=np.random.normal(0, 1, 500_000), y=np.random.uniform(0, 10, 500_000))

# Promises with delay=True, executed in single pass
results = vaex.execute([df.x.mean(delay=True), df.x.std(delay=True), df.y.count(delay=True)])
print(f"Mean: {results[0]:.4f}, Std: {results[1]:.4f}, Count: {results[2]}")

# Async/await (Jupyter, web servers):
# async def compute(df): return await df.x.mean(delay=True)

# Automatic caching: first call computes, second is instant
mean1 = df.x.mean()
mean2 = df.x.mean()  # Cached
print(f"Cached: {mean1 == mean2}")  # True

# Cache invalidated on DataFrame changes (filtering, new columns)
# Duplicate expressions deduplicated in batch execution
# Manual cache: materialize with .values for repeated complex expressions
df['cached'] = (df.x ** 3 + df.y.log() * df.x.sin()).values
```

## Memory Management

```python
import vaex
import numpy as np

df = vaex.from_arrays(a=np.random.normal(0, 1, 500_000), b=np.random.uniform(0, 10, 500_000))

# Per-column memory
for col in df.column_names:
    print(f"{col}: {df[col].nbytes / 1e6:.2f} MB")

# Total materialized memory (virtual columns are zero bytes)
total = sum(df[col].nbytes for col in df.get_column_names(virtual=False))
print(f"Total materialized: {total / 1e6:.2f} MB")

df['c'] = df.a ** 2 + df.b  # Virtual: 0 bytes
virtual = [c for c in df.column_names if c not in df.get_column_names(virtual=False)]
print(f"Virtual (0 bytes): {virtual}")

# Slim view: only reference needed columns
df_slim = df[['a', 'b']]
print(f"Slim: {df_slim.column_names}")
```

## Parallel Computation and Dask Integration

Vaex uses all CPU cores by default. Control via `VAEX_NUM_THREADS`. For distributed multi-node computing, bridge to Dask.

```python
import vaex
import numpy as np
import os, time

os.environ['VAEX_NUM_THREADS'] = '4'
df = vaex.from_arrays(x=np.random.normal(0, 1, 2_000_000), group=np.random.choice(['A', 'B', 'C'], 2_000_000))

t0 = time.time()
result = df.groupby('group').agg({'x': ['mean', 'std']})
print(f"GroupBy: {time.time() - t0:.3f}s")
print(result)

# Dask integration for multi-node distributed computing:
# df.export_parquet('/tmp/parts/', partition_on='group')
# import dask.dataframe as dd
# ddf = dd.read_parquet('/tmp/parts/')
print(f"Threads: VAEX_NUM_THREADS={os.environ.get('VAEX_NUM_THREADS', 'auto')}")
```

## JIT Compilation with Numba

Accelerate custom functions that cannot be expressed as Vaex vectorized expressions.

```python
import vaex
import numpy as np
import numba, time

@numba.jit(nopython=True)
def weighted_distance(x, y):
    return np.sqrt(x**2 + 2 * y**2)

@numba.jit(nopython=True)
def weighted_mean(values, weights):
    total_w, w_sum = 0.0, 0.0
    for i in range(len(values)):
        if not np.isnan(values[i]) and not np.isnan(weights[i]):
            w_sum += values[i] * weights[i]
            total_w += weights[i]
    return w_sum / total_w if total_w > 0 else np.nan

n = 500_000
df = vaex.from_arrays(x=np.random.normal(0, 1, n), y=np.random.normal(0, 1, n))

t0 = time.time()
df['distance'] = weighted_distance(df.x.values, df.y.values)
print(f"Numba distance ({n:,} rows): {time.time() - t0:.3f}s, mean={df.distance.mean():.4f}")

wmean = weighted_mean(df.x.values, np.abs(df.y.values))
print(f"Weighted mean: {wmean:.4f}")
```

## Optimization: Selections vs Filtering

Named selections are more efficient than filtered DataFrames for multi-subset statistics.

```python
import vaex
import numpy as np
import time

n = 1_000_000
df = vaex.from_arrays(
    value=np.random.lognormal(3, 1, n),
    region=np.random.choice(['US', 'EU', 'APAC', 'LATAM'], n),
)

# SLOW: separate filtered DataFrames (4 passes)
t0 = time.time()
for r in ['US', 'EU', 'APAC', 'LATAM']:
    _ = df[df.region == r].value.mean()
print(f"Filtered: {time.time() - t0:.3f}s")

# FAST: named selections + batch execution (1 pass)
t0 = time.time()
for r in ['US', 'EU', 'APAC', 'LATAM']:
    df.select(df.region == r, name=f's_{r}')
results = vaex.execute([df.value.mean(selection=f's_{r}', delay=True) for r in ['US', 'EU', 'APAC', 'LATAM']])
for r, v in zip(['US', 'EU', 'APAC', 'LATAM'], results):
    print(f"  {r}: mean={v:.2f}")
print(f"Selections+batch: {time.time() - t0:.3f}s")
```

## Expression Optimization

```python
import vaex
import numpy as np

df = vaex.from_arrays(x=np.random.normal(0, 1, 500_000), y=np.random.normal(0, 1, 500_000))

# GOOD: chain expressions (single pass, zero memory)
df['r'] = (df.x**2 + df.y**2).sqrt()
# BAD: intermediate materialization wastes memory
# df['x_sq'] = (df.x**2).values; df['r'] = np.sqrt(df.x_sq + ...)

# GOOD: vectorized string methods (C++)
df_s = vaex.from_dict({'name': ['Alice Smith', 'Bob Jones'] * 100_000})
df_s['first'] = df_s.name.str.split(' ')[0]
# BAD: df_s.name.apply(lambda s: s.split(' ')[0])  # Python loop

print(f"Expression for r: {df.r.expression}")
print(f"Is virtual: {not df.is_local('r')}")
```

## Performance Profiling

```python
import vaex
import numpy as np
import time

n = 1_000_000
df = vaex.from_arrays(x=np.random.normal(0, 1, n), y=np.random.uniform(0, 100, n),
                      cat=np.random.choice(['A', 'B', 'C', 'D', 'E'], n))

def bench(label, func, iters=3):
    times = [time.time() for _ in range(1)]  # warmup
    times = []
    for _ in range(iters):
        t0 = time.time(); func(); times.append(time.time() - t0)
    print(f"{label}: {np.mean(times):.4f}s +/- {np.std(times):.4f}s")

bench("mean(x)", lambda: df.x.mean())
bench("groupby+agg", lambda: df.groupby('cat').agg({'x': 'mean', 'y': 'sum'}))

# Sequential vs batched comparison
bench("sequential (4 passes)", lambda: [df.x.mean(), df.x.std(), df.y.mean(), df.y.std()])
bench("batched (1 pass)", lambda: vaex.execute([df.x.mean(delay=True), df.x.std(delay=True),
                                                 df.y.mean(delay=True), df.y.std(delay=True)]))
```

## Common Performance Issues and Solutions

| Issue | Cause | Solution |
|-------|-------|---------|
| Slow aggregation on many groups | High-cardinality groupby | Reduce cardinality with binning or `.str.slice(0, 3)` |
| High memory during export | Virtual columns recomputed | Materialize selectively: `df['col'] = df.col.values` |
| Slow CSV reading | Row-by-row parsing | Convert once: `vaex.from_csv('f.csv', convert='f.hdf5')` |
| Slow repeated aggregations | Each call scans full data | Batch: `delay=True` + `vaex.execute()` |
| Memory spike on `.values` | Full column in RAM | Use `.sample(n=1000).values` or stay lazy |
| Slow custom function | Python loop over rows | Numba JIT or vectorized expression |
| Slow string operations | `.apply(lambda)` | Use `.str.lower()`, `.str.contains()` (C++) |
| Export slower than expected | Thread contention | Set `VAEX_NUM_THREADS` to physical core count |

---

Condensed from io_operations.md (704 lines) + performance.md (572 lines) = 1,276 lines. Retained: HDF5 compression options (gzip/lzf/blosc), Parquet compression (snappy/brotli/gzip), Arrow integration (from_arrow_table/to_arrow_table/IPC), FITS file support, chunked I/O processing, cloud storage (S3/GCS/Azure with credentials and storage_options), Vaex server (ws:// protocol), database integration (SQL read/write via pandas bridge), state files (state_write/state_load with what's saved), production data pipeline pattern, archiving with compression (merged into compression section), async operations (delay/promises/await), caching strategies (automatic cache/invalidation/materialization), memory management (nbytes/column monitoring), parallel computation (VAEX_NUM_THREADS/Dask integration), JIT compilation with Numba (custom functions/aggregations), optimization strategies (selections vs filtering/expression optimization), performance profiling patterns (timing/benchmarking), common performance issues table. Omitted from io_operations.md: format comparison table, CSV-to-HDF5 conversion pattern, basic export methods (export_hdf5/export_arrow/export_parquet), multi-source data loading pattern -- relocated to SKILL.md Core API and Key Concepts. "Best Practices" lists -- duplicated content already in SKILL.md Best Practices section. "Related Resources" cross-links -- superseded by Bundled Resources section. Omitted from performance.md: lazy evaluation concept, virtual vs materialized decision criteria, memory-mapped architecture explanation, delay=True batching basic pattern -- relocated to SKILL.md Key Concepts and Core API Module 4. "Best Practices" summary list -- duplicated SKILL.md Best Practices. "Related Resources" cross-links -- superseded by Bundled Resources section. Relocated to SKILL.md: format comparison table, CSV-to-HDF5 conversion pattern, basic export methods, lazy evaluation model, virtual vs materialized table, memory-mapped file architecture, delay=True batching pattern.
