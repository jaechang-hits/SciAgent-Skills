# Dask Collections Guide — DataFrames, Arrays, Bags

Detailed API reference for Dask's three high-level collection types.

## DataFrames — Detailed Operations

### Reading Data

```python
import dask.dataframe as dd

# Single file
ddf = dd.read_csv('data.csv')
ddf = dd.read_parquet('data.parquet', columns=['col1', 'col2'])

# Multiple files via glob
ddf = dd.read_csv('data/year=2024/month=*/data.csv')
ddf = dd.read_parquet('data/year=2024/', filters=[('month', '>=', 6)])

# From pandas (only for small DataFrames already in memory)
ddf = dd.from_pandas(small_df, npartitions=4)
```

### Filtering and Column Operations

```python
# Boolean filtering
ddf = ddf[ddf['value'] > 0]
ddf = ddf[(ddf['category'] == 'A') & (ddf['value'] > 100)]

# Column operations
ddf['ratio'] = ddf['value'] / ddf['count']
ddf = ddf.drop(columns=['temp_col'])
ddf = ddf.rename(columns={'old_name': 'new_name'})

# Value counts
counts = ddf['category'].value_counts().compute()
```

### GroupBy and Aggregations

```python
# Simple groupby
result = ddf.groupby('category')['value'].mean().compute()

# Multiple aggregations
result = ddf.groupby('category').agg({
    'value': ['mean', 'sum', 'std', 'count'],
    'score': ['min', 'max']
}).compute()

# Custom aggregation
result = ddf.groupby('category').apply(
    lambda group: group.nlargest(5, 'value'),
    meta=ddf
).compute()
```

### Joins and Sorting

```python
# Merge (like pandas merge)
merged = ddf1.merge(ddf2, on='key', how='inner')
merged = ddf1.merge(ddf2, left_on='id', right_on='ref_id', how='left')

# Sorting (expensive — triggers full shuffle)
sorted_ddf = ddf.sort_values('timestamp')

# Set sorted index (enables efficient range queries)
ddf = ddf.set_index('timestamp', sorted=True)
```

### map_partitions Pattern

```python
# Preferred over apply for custom operations
def enrich_partition(df):
    df['log_value'] = np.log1p(df['value'])
    df['category_upper'] = df['category'].str.upper()
    return df

ddf = ddf.map_partitions(enrich_partition)

# With meta (required when output schema differs)
def summarize(df):
    return pd.DataFrame({
        'mean': [df['value'].mean()],
        'count': [len(df)]
    })

result = ddf.map_partitions(
    summarize,
    meta=pd.DataFrame({'mean': [0.0], 'count': [0]})
)
```

### Writing Results

```python
# Parquet (recommended)
ddf.to_parquet('output/', engine='pyarrow', compression='snappy')

# CSV (one file per partition)
ddf.to_csv('output/part-*.csv', index=False)

# Single file (requires compute)
ddf.compute().to_csv('output/single_file.csv', index=False)
```

## Arrays — Detailed Operations

### Creating Arrays

```python
import dask.array as da
import numpy as np

# From NumPy
x = da.from_array(np.random.random((10000, 1000)), chunks=(1000, 1000))

# Random generators
x = da.random.random((100000, 100), chunks=(10000, 100))
x = da.random.normal(loc=0, scale=1, size=(50000, 200), chunks=(5000, 200))

# From disk
x = da.from_zarr('data.zarr')

import h5py
f = h5py.File('data.hdf5', 'r')
x = da.from_array(f['dataset'], chunks=(1000, 1000))

# Zeros, ones, empty
x = da.zeros((10000, 10000), chunks=(1000, 1000))
x = da.ones_like(x)
```

### Arithmetic and Reductions

```python
# Element-wise (lazy)
y = x + 100
y = da.exp(x)
y = da.log1p(x)

# Reductions
total = x.sum().compute()
col_means = x.mean(axis=0).compute()
row_maxes = x.max(axis=1).compute()
print(f"Shape of col_means: {col_means.shape}")  # (1000,)
```

### Linear Algebra

```python
# Matrix operations
z = da.dot(x.T, x)
u, s, v = da.linalg.svd(x)

# Compressed SVD (for large matrices)
u, s, v = da.linalg.svd_compressed(x, k=50)
```

### map_blocks Pattern

```python
# Apply NumPy/SciPy function to each chunk
def custom_filter(block):
    from scipy.ndimage import gaussian_filter
    return gaussian_filter(block, sigma=1)

filtered = da.map_blocks(custom_filter, x, dtype=x.dtype)

# When output shape differs
def extract_features(block):
    return np.array([block.mean(), block.std(), block.max()])

features = da.map_blocks(
    extract_features, x,
    dtype='float64',
    drop_axis=1,          # Input 2D → output 1D
    new_axis=None,
    chunks=(3,)
)
```

### Chunking Strategy

```python
# View current chunks
print(x.chunks)  # ((1000, 1000, ...), (1000, 1000, ...))

# Rechunk for different access patterns
x_rechunked = x.rechunk({0: 5000, 1: 500})

# Rechunk for row-wise operations
x_rows = x.rechunk({0: -1, 1: 1000})  # Full rows, chunked columns

# Rechunk for column-wise operations
x_cols = x.rechunk({0: 1000, 1: -1})  # Chunked rows, full columns
```

### Saving Arrays

```python
# Zarr (recommended)
da.to_zarr(x, 'output.zarr', overwrite=True)

# HDF5
da.to_hdf5('output.hdf5', {'dataset': x})

# Multiple arrays to one Zarr store
import zarr
store = zarr.open('multi.zarr', mode='w')
da.to_zarr(x, store, component='features')
da.to_zarr(y, store, component='labels')
```

## Bags — Detailed Operations

### Creating Bags

```python
import dask.bag as db

# From text files
bag = db.read_text('logs/*.log')
bag = db.read_text('data/*.json').map(json.loads)

# From Python sequence
bag = db.from_sequence(range(1000), npartitions=10)

# With blocksize for large files
bag = db.read_text('huge_file.log', blocksize='10MB')
```

### Functional Operations

```python
# Map, filter, pluck
processed = bag.map(lambda x: x.strip().lower())
valid = bag.filter(lambda x: len(x) > 0)
ids = bag.pluck('user_id')          # Extract field from dicts
tags = bag.pluck('tags').flatten()   # Flatten nested lists

# Reductions
count = bag.count().compute()
unique = bag.distinct().compute()
sample = bag.take(5)                 # First 5 elements (no compute needed)
```

### foldby vs groupby

```python
# groupby — EXPENSIVE (requires full shuffle)
grouped = bag.groupby('category').compute()

# foldby — PREFERRED (streaming aggregation)
result = bag.foldby(
    key=lambda x: x['category'],
    binop=lambda total, x: total + x['amount'],
    initial=0,
    combine=lambda a, b: a + b,
    combine_initial=0
).compute()
# Returns list of (key, aggregate) tuples
```

### Converting to DataFrame

```python
# Explicit meta for type safety
ddf = bag.to_dataframe(meta={
    'user_id': 'str',
    'amount': 'float64',
    'category': 'str',
    'timestamp': 'datetime64[ns]'
})

# Then use DataFrame operations
result = ddf.groupby('category')['amount'].sum().compute()
```

## Collection Conversion

```python
# Bag → DataFrame
ddf = bag.to_dataframe(meta={'col1': 'str', 'col2': 'float64'})

# DataFrame → Array (numeric columns only)
arr = ddf[['col1', 'col2']].to_dask_array(lengths=True)

# Array → DataFrame
ddf = dd.from_dask_array(arr, columns=['feature_1', 'feature_2'])
```

## Lazy Evaluation Patterns

```python
import dask

# Single compute
result = ddf.mean().compute()

# Batch compute (shares intermediates — ALWAYS prefer this)
mean, std, count = dask.compute(ddf.mean(), ddf.std(), ddf.count())

# Persist on workers (for reuse)
ddf = ddf.persist()           # Keep on workers
result1 = ddf.mean().compute()
result2 = ddf.std().compute()  # Reuses persisted data
del ddf                         # Release worker memory

# Visualize task graph (for debugging)
ddf.mean().visualize(filename='task_graph.png')
```

Condensed from original: dataframes.md (369 lines), arrays.md (498 lines), bags.md (469 lines) = 1,336 lines total. Retained: all read/write patterns, filtering, groupby, joins, map_partitions/map_blocks with meta, chunking strategies, foldby, collection conversion, lazy evaluation patterns. Omitted: XArray integration (separate tool), verbose prose explanations, duplicate code patterns already shown in SKILL.md Core API.
