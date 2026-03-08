---
name: vaex-dataframes
description: >-
  Out-of-core DataFrame library for billion-row datasets using lazy evaluation and memory-mapped files.
  Use when data exceeds available RAM (10 GB to terabytes) and needs fast aggregation, filtering,
  virtual columns, and visualization without loading into memory. Supports HDF5, Apache Arrow, Parquet,
  CSV I/O with cloud storage (S3, GCS, Azure). Built-in ML transformers (scaling, encoding, PCA, K-means)
  with scikit-learn bridge. For in-memory speed use polars; for distributed computing use dask.
license: MIT
---

# Vaex DataFrames

## Overview

Vaex is a high-performance Python library for lazy, out-of-core DataFrame operations on datasets too large to fit in RAM. It processes over a billion rows per second using memory-mapped files and lazy evaluation, enabling interactive exploration and analysis without loading data into memory.

## When to Use

- Processing tabular datasets larger than available RAM (10 GB to terabytes)
- Fast statistical aggregations on massive datasets (mean, std, quantiles at billion-row scale)
- Creating visualizations (heatmaps, histograms) of large datasets without sampling
- Building ML preprocessing pipelines (scaling, encoding, PCA) on big data
- Converting between data formats (CSV to HDF5/Arrow for fast repeated access)
- Feature engineering with virtual columns that consume zero additional memory
- Working with astronomical catalogs, financial time series, or large scientific datasets
- For **in-memory speed** on data that fits in RAM, use **polars** instead
- For **distributed multi-node** computing, use **dask** instead

## Prerequisites

```bash
pip install vaex
# Optional extras:
pip install vaex-hdf5          # HDF5 support (recommended)
pip install vaex-arrow          # Apache Arrow support
pip install vaex-ml             # Machine learning transformers
pip install vaex-viz            # Visualization support
pip install vaex-jupyter        # Jupyter widget support
pip install s3fs gcsfs adlfs    # Cloud storage (S3, GCS, Azure)
```

Requires Python 3.7+. HDF5 and Arrow formats provide instant memory-mapped loading; CSV requires conversion for optimal performance.

## Quick Start

```python
import vaex
import numpy as np

df = vaex.from_arrays(
    x=np.random.normal(0, 1, 1_000_000),
    y=np.random.normal(0, 1, 1_000_000),
    category=np.random.choice(['A', 'B', 'C'], 1_000_000),
)

df['radius'] = (df.x**2 + df.y**2).sqrt()  # Virtual column, zero memory
df_inner = df[df.radius < 1.0]              # Filtered view
print(df_inner.radius.mean())               # ~0.48

result = df.groupby('category').agg({'radius': 'mean'})
print(result)  # shape: (3, 2)

df.export_hdf5('/tmp/sample.hdf5')          # Export to efficient format
df2 = vaex.open('/tmp/sample.hdf5')         # Future loads are instant
print(f"Loaded {len(df2):,} rows instantly")
```

## Core API

### 1. DataFrame Creation and I/O

Create DataFrames from files, arrays, pandas, or Arrow tables. HDF5 and Arrow files are memory-mapped for instant loading.

```python
import vaex
import numpy as np

# From files (HDF5/Arrow are instant via memory mapping)
df = vaex.open('data.hdf5')       # Recommended: instant, memory-mapped
df = vaex.open('data.arrow')      # Also instant, memory-mapped
df = vaex.open('data.parquet')    # Fast, columnar, compressed
df = vaex.open('data_*.hdf5')     # Wildcards: multiple files as one DataFrame

# From CSV (slow for large files — convert to HDF5)
df = vaex.from_csv('data.csv', convert='data.hdf5')  # Auto-converts

# From Python objects
df = vaex.from_arrays(x=np.arange(100), y=np.random.rand(100))
df = vaex.from_dict({'name': ['Alice', 'Bob'], 'age': [30, 25]})
df = vaex.from_pandas(pd.DataFrame({'a': [1, 2, 3]}), copy_index=False)

# From Arrow table
import pyarrow as pa
df = vaex.from_arrow_table(pa.table({'x': [1, 2, 3]}))

# Inspect
print(df.shape)          # (rows, cols)
print(df.column_names)   # Column names
df.describe()            # Statistical summary

# Export
df.export_hdf5('out.hdf5')                             # Recommended
df.export_arrow('out.arrow')                            # Interoperability
df.export_parquet('out.parquet', compression='snappy')   # Compressed
df.export_parquet('s3://bucket/data.parquet')            # Cloud storage
```

### 2. Filtering and Selection

Filter rows with boolean expressions. Named selections allow computing statistics on multiple subsets without creating new DataFrames.

```python
import vaex
import numpy as np

df = vaex.from_arrays(
    age=np.array([22, 35, 45, 19, 60]),
    salary=np.array([30000, 70000, 90000, 25000, 120000]),
    dept=np.array(['Eng', 'Sales', 'Eng', 'Sales', 'Eng']),
)

# Boolean filtering (creates a view, no copy)
df_eng_high = df[(df.dept == 'Eng') & (df.salary > 50000)]
print(len(df_eng_high))  # 2

# isin, between, string/null checks
df_mid = df[df.age.between(25, 50)]
# df[df.name.str.contains('Ali')], df[df.salary.notna()]

# Named selections (more efficient for multiple aggregations)
df.select(df.age >= 30, name='senior')
df.select(df.dept == 'Eng', name='engineers')
mean_senior = df.salary.mean(selection='senior')
mean_eng = df.salary.mean(selection='engineers')
print(f"Senior avg: {mean_senior}, Eng avg: {mean_eng}")
# Senior avg: 93333.33, Eng avg: 80000.0
```

### 3. Virtual Columns and Expressions

Virtual columns are computed on-the-fly with zero memory overhead. They are the core of Vaex's efficiency.

```python
import vaex
import numpy as np

df = vaex.from_arrays(
    price=np.array([10.0, 20.0, 30.0, 40.0]),
    quantity=np.array([5, 3, 8, 2]),
    discount=np.array([0.0, 0.1, 0.0, 0.2]),
)

# Arithmetic (virtual columns — no memory used)
df['revenue'] = df.price * df.quantity * (1 - df.discount)
df['log_price'] = df.price.log()

# Conditional logic
df['tier'] = (df.price >= 30).where('premium', 'standard')

# Math: .abs(), .sqrt(), .log(), .log10(), .exp(), .sin(), .cos(),
#        .round(n), .floor(), .ceil(), .astype('float64')

# Check virtual vs materialized
print(df.get_column_names(virtual=False))  # Materialized only

# Materialize when needed (complex expr used repeatedly)
df['revenue_mat'] = df.revenue.values  # Now stored in memory
```

### 4. Aggregation and GroupBy

Efficient aggregations across billions of rows. Use `delay=True` to batch multiple operations into a single data pass.

```python
import vaex
import numpy as np

np.random.seed(42)
n = 100_000
df = vaex.from_arrays(
    sales=np.random.uniform(10, 500, n),
    quantity=np.random.randint(1, 20, n),
    region=np.random.choice(['East', 'West', 'North'], n),
)

# Single-column aggregations
print(f"Mean: {df.sales.mean():.2f}, Std: {df.sales.std():.2f}")
# Also: .min(), .max(), .minmax(), .sum(), .count(), .nunique(),
#   .quantile(0.5), .median_approx(), .kurtosis(), .skew()
#   .correlation(df.x, df.y), .covar(df.x, df.y)

# Batch aggregations with delay=True (single pass through data)
mean_s = df.sales.mean(delay=True)
std_s = df.sales.std(delay=True)
sum_q = df.quantity.sum(delay=True)
results = vaex.execute([mean_s, std_s, sum_q])
print(f"Mean: {results[0]:.2f}, Std: {results[1]:.2f}, Total qty: {results[2]}")

# GroupBy
grouped = df.groupby('region').agg({'sales': ['sum', 'mean'], 'quantity': 'sum'})
print(grouped)  # shape: (3, 4)

# Multi-dimensional binned aggregation (for heatmap data)
counts = df.count(binby=[df.sales, df.quantity],
                  limits=[[0, 500], [1, 20]], shape=(50, 19))
print(f"2D histogram shape: {counts.shape}")  # (50, 19)
```

### 5. String and DateTime Operations

String methods via `.str` accessor; datetime methods via `.dt` accessor.

```python
import vaex
import numpy as np

# String operations via .str accessor
df = vaex.from_dict({
    'name': ['Alice Smith', 'Bob Jones', 'Charlie Brown'],
    'email': ['ALICE@test.com', 'bob@TEST.com', 'charlie@test.com'],
})
df['email_clean'] = df.email.str.lower().str.strip()
df['first_name'] = df.name.str.split(' ')[0]
df['has_test'] = df.email_clean.str.contains('test')
# Also: .upper(), .title(), .startswith(), .endswith(), .len(),
#   .replace(), .pad(), .slice(start, end)

# DateTime operations via .dt accessor
dates = np.array(['2024-01-15', '2024-06-20', '2024-12-01'], dtype='datetime64')
df2 = vaex.from_arrays(timestamp=dates, value=np.array([100, 200, 300]))
df2['year'] = df2.timestamp.dt.year
df2['month'] = df2.timestamp.dt.month
df2['weekday'] = df2.timestamp.dt.dayofweek  # 0=Monday
# Also: .day, .hour, .minute, .second
print(df2[['timestamp', 'year', 'month']].head(3))
```

### 6. Visualization

Vaex visualizes billion-row datasets through efficient binning, using all data without sampling.

```python
import vaex
import numpy as np
import matplotlib.pyplot as plt

np.random.seed(0)
df = vaex.from_arrays(
    x=np.random.normal(0, 1, 500_000),
    y=np.random.normal(0, 1, 500_000),
    z=np.random.uniform(0, 10, 500_000),
)

# 1D histogram
df.plot1d(df.x, limits=[-4, 4], shape=80, figsize=(8, 4))
plt.title('X Distribution')
plt.savefig('hist1d.png', dpi=150, bbox_inches='tight')
plt.close()

# 2D density heatmap (core vaex visualization)
df.plot(df.x, df.y, limits='99.7%', shape=(256, 256),
        f='log', colormap='viridis', figsize=(8, 8))
plt.savefig('heatmap2d.png', dpi=150, bbox_inches='tight')
plt.close()

# Aggregation on grid (mean of z over x-y plane)
df.plot(df.x, df.y, what=df.z.mean(),
        limits=[[-3, 3], [-3, 3]], shape=(100, 100))
plt.savefig('mean_grid.png', dpi=150, bbox_inches='tight')
plt.close()
print("Saved: hist1d.png, heatmap2d.png, mean_grid.png")
```

### 7. ML Integration

`vaex.ml` provides transformers for preprocessing, dimensionality reduction, clustering, and scikit-learn model wrapping. All transformers create virtual columns (zero memory overhead).

```python
import vaex, vaex.ml
import numpy as np

np.random.seed(42)
n = 10_000
df = vaex.from_arrays(
    age=np.random.randint(18, 70, n).astype(float),
    income=np.random.uniform(20000, 150000, n),
    category=np.random.choice(['A', 'B', 'C'], n),
    target=np.random.randint(0, 2, n),
)

# Feature scaling (creates virtual columns: standard_scaled_age, ...)
scaler = vaex.ml.StandardScaler(features=['age', 'income'])
df = scaler.fit_transform(df)
# Also: MinMaxScaler, MaxAbsScaler, RobustScaler

# Categorical encoding
encoder = vaex.ml.LabelEncoder(features=['category'])
df = encoder.fit_transform(df)
# Also: OneHotEncoder, FrequencyEncoder, TargetEncoder, WeightOfEvidenceEncoder

# PCA
pca = vaex.ml.PCA(features=['standard_scaled_age', 'standard_scaled_income'],
                   n_components=2)
df = pca.fit_transform(df)
print(f"Explained variance: {pca.explained_variance_ratio_}")

# Scikit-learn bridge: wrap any sklearn model
from sklearn.ensemble import RandomForestClassifier
features = ['standard_scaled_age', 'standard_scaled_income',
            'label_encoded_category']
model = vaex.ml.sklearn.Predictor(
    features=features, target='target',
    model=RandomForestClassifier(n_estimators=50, random_state=42),
    prediction_name='rf_prediction',
)
train_df, test_df = df[:8000], df[8000:]
model.fit(train_df)
test_df = model.transform(test_df)  # Predictions as virtual columns
accuracy = (test_df.rf_prediction == test_df.target).mean()
print(f"Accuracy: {accuracy:.3f}")  # ~0.50 (random data)

# Save pipeline state (encoding + scaling + model)
train_df.state_write('pipeline_state.json')
# Deploy: prod_df.state_load('pipeline_state.json')
```

## Key Concepts

### Lazy Evaluation Model

Vaex operations build an expression graph without executing computation. Evaluation is triggered only when a result is accessed (printing a value, calling `.values`, exporting).

```python
import vaex, numpy as np
df = vaex.from_arrays(x=np.random.rand(1_000_000))

# NOT computed: virtual column, expression, filtered view
df['x_sq'] = df.x ** 2;  expr = df.x_sq.mean();  df_f = df[df.x > 0.5]

# COMPUTED: accessing value, .values, .to_pandas_df(), .export_hdf5()
print(f"Mean: {df.x.mean():.4f}")
```

### Virtual vs Materialized Columns

| Aspect | Virtual | Materialized |
|--------|---------|-------------|
| Memory | Zero overhead | Stores full array |
| Speed | Recomputed each use | Instant access |
| Creation | `df['col'] = expr` | `df['col'] = expr.values` |
| Best for | Simple expressions, infrequent use | Complex expressions used repeatedly |
| Check | `df.is_local('col')` returns `False` | Returns `True` |

**Rule of thumb:** Keep columns virtual unless the same complex expression is used in 3+ aggregations.

### Memory-Mapped File Architecture

HDF5 and Apache Arrow files are memory-mapped: the OS maps file pages to virtual memory on demand, so opening a 100 GB file is instant and uses minimal RAM. Data pages are read from disk only when accessed.

```python
# Opens instantly regardless of file size
df = vaex.open('100gb_dataset.hdf5')  # ~0.001s, minimal RAM
mean = df.column.mean()  # Streams through data, ~RSS stays low
```

### Format Comparison

| Feature | HDF5 | Arrow/Feather | Parquet | CSV |
|---------|------|---------------|---------|-----|
| Load speed | Instant | Instant | Fast | Slow |
| Memory-mapped | Yes | Yes | No | No |
| Compression | Optional (gzip, lzf, blosc) | No | Default (snappy, gzip, brotli) | No |
| Columnar | Yes | Yes | Yes | No |
| Portability | Good | Excellent | Excellent | Excellent |
| Best for | Local Vaex workflows | Cross-language interop | Distributed systems | Data exchange |

**Recommendation:** Convert CSV to HDF5 once (`vaex.from_csv('data.csv', convert='data.hdf5')`), then use HDF5 for all future loads.

## Common Workflows

### Workflow 1: Large CSV Exploration and Conversion

```python
import vaex
import matplotlib.pyplot as plt

# Convert CSV to HDF5 (one-time); future loads instant
df = vaex.from_csv('large_data.csv', convert='large_data.hdf5')
print(f"Shape: {df.shape}, Columns: {df.column_names}")

# Feature engineering with virtual columns
df['log_value'] = df.value.log()
df['category_clean'] = df.category.str.lower().str.strip()
df['is_high'] = df.value > df.value.mean()

# Batch statistics (single pass)
delayed = [df.value.mean(delay=True), df.value.std(delay=True),
           df.value.quantile(0.5, delay=True), df.value.quantile(0.99, delay=True)]
results = vaex.execute(delayed)
print(f"Mean: {results[0]:.2f}, Std: {results[1]:.2f}, P99: {results[3]:.2f}")

# Visualize
fig, axes = plt.subplots(1, 2, figsize=(14, 5))
df.plot1d(df.value, ax=axes[0], show=False)
axes[0].set_title('Value Distribution')
df.plot1d(df.log_value, ax=axes[1], show=False)
axes[1].set_title('Log Value Distribution')
plt.tight_layout()
plt.savefig('exploration.png', dpi=150, bbox_inches='tight')
plt.close()
```

### Workflow 2: ML Pipeline with State Deployment

```python
import vaex, vaex.ml
import numpy as np
from sklearn.ensemble import GradientBoostingClassifier

np.random.seed(42)
n = 50_000
df = vaex.from_arrays(
    age=np.random.randint(18, 70, n).astype(float),
    income=np.random.uniform(20000, 150000, n),
    region=np.random.choice(['East', 'West', 'Central'], n),
    target=np.random.randint(0, 2, n),
)
train, test = df[:40_000], df[40_000:]

# Preprocessing pipeline
train = vaex.ml.LabelEncoder(features=['region']).fit_transform(train)
train = vaex.ml.StandardScaler(features=['age', 'income']).fit_transform(train)

# Train model
features = ['standard_scaled_age', 'standard_scaled_income', 'label_encoded_region']
model = vaex.ml.sklearn.Predictor(
    features=features, target='target',
    model=GradientBoostingClassifier(n_estimators=50, random_state=42),
    prediction_name='prediction',
)
model.fit(train)

# Save pipeline state (encoding + scaling + model in one file)
train.state_write('ml_pipeline.json')

# Deploy: apply saved state to new data
test.state_load('ml_pipeline.json')
accuracy = (test.prediction == test.target).mean()
print(f"Test accuracy: {accuracy:.3f}")  # ~0.50 (random data)
# Production: prod_df = vaex.open('new_batch.hdf5'); prod_df.state_load('ml_pipeline.json')
```

## Key Parameters

| Parameter | Module | Default | Range/Options | Effect |
|-----------|--------|---------|---------------|--------|
| `shape` | `plot`, `plot1d` | 64 (1D), (256,256) (2D) | 32-2048 | Histogram bin count / heatmap resolution |
| `limits` | `plot`, `plot1d` | `'minmax'` | `'99%'`, `'99.7%'`, `[min,max]` | Axis ranges; percentile-based for outlier handling |
| `f` | `plot` | `'identity'` | `'log'`, `'log10'`, `'sqrt'` | Color scale transform for density plots |
| `delay` | aggregations | `False` | `True/False` | Batch multiple aggregations into single pass |
| `convert` | `from_csv` | `None` | file path string | Auto-convert CSV to HDF5 during load |
| `chunk_size` | `from_csv` | 5,000,000 | 100K-50M | Rows per chunk for CSV processing |
| `n_components` | `PCA` | 2 | 1-n_features | Number of principal components |
| `n_clusters` | `KMeans` | 8 | 2-100+ | Number of clusters |
| `features` | all ML transformers | required | list of column names | Columns to transform |
| `compression` | `export_hdf5` | None | `'gzip'`, `'lzf'`, `'blosc'` | Trade file size for I/O speed |

## Best Practices

1. **Always convert CSV to HDF5 or Arrow for repeated access.** One-time conversion pays for itself on the first reload: `vaex.from_csv('data.csv', convert='data.hdf5')`.

2. **Keep columns virtual until you must materialize.** Virtual columns have zero memory cost. Materialize only when a complex expression is reused in 3+ aggregations.

3. **Batch aggregations with `delay=True`.** Each separate aggregation call scans the entire dataset. Batching with `vaex.execute([df.x.mean(delay=True), df.x.std(delay=True)])` reduces N passes to 1.

4. **Use selections instead of creating filtered DataFrames** when computing statistics on multiple subsets. `df.select(df.age > 30, name='senior')` then `df.salary.mean(selection='senior')` is more efficient than creating `df_senior = df[df.age > 30]`.

5. **Avoid `.values` and `.to_pandas_df()` on large data.** These load data into RAM, defeating Vaex's purpose. Use only on small subsets or samples.

6. **Save pipeline state for reproducibility.** `df.state_write('state.json')` captures virtual columns, selections, and ML transformers for deployment.

7. **Anti-pattern -- row iteration.** Never iterate rows in Vaex. Use vectorized expressions and aggregations instead.

## Common Recipes

### Recipe: Multi-Source Data Consolidation

```python
import vaex

# Load from multiple sources and formats
df_csv = vaex.from_csv('data_2022.csv')
df_hdf = vaex.open('data_2023.hdf5')
df_pq = vaex.open('data_2024.parquet')

# Concatenate vertically
df_all = vaex.concat([df_csv, df_hdf, df_pq])
print(f"Combined: {len(df_all):,} rows")

# Export as unified HDF5
df_all.export_hdf5('unified_data.hdf5')
# Future: vaex.open('unified_data.hdf5')
```

### Recipe: Handling Missing Data

```python
import vaex
import numpy as np

df = vaex.from_arrays(
    x=np.array([1.0, np.nan, 3.0, np.nan, 5.0]),
    y=np.array([10, 20, 30, 40, 50]),
)

# Detect missing
missing_pct = df.x.isna().mean() * 100
print(f"Missing: {missing_pct:.0f}%")
# Missing: 40%

# Fill with value or column mean
df['x_filled'] = df.x.fillna(df.x.mean())

# Filter out missing
df_clean = df[df.x.notna()]
print(f"Clean rows: {len(df_clean)}")
# Clean rows: 3
```

### Recipe: Comparison Visualization with Selections

```python
import vaex
import numpy as np
import matplotlib.pyplot as plt

df = vaex.from_arrays(
    value=np.concatenate([
        np.random.normal(50, 10, 200_000),
        np.random.normal(70, 15, 200_000),
    ]),
    group=np.array(['Control'] * 200_000 + ['Treatment'] * 200_000),
)

# Named selections for efficient comparison
df.select(df.group == 'Control', name='ctrl')
df.select(df.group == 'Treatment', name='treat')

plt.figure(figsize=(10, 5))
df.plot1d(df.value, selection='ctrl', label='Control', show=False)
df.plot1d(df.value, selection='treat', label='Treatment', show=False)
plt.legend()
plt.title('Distribution Comparison')
plt.savefig('comparison.png', dpi=150, bbox_inches='tight')
plt.close()
print("Saved comparison.png")
```

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|---------|
| CSV loading extremely slow | CSV is not memory-mappable; parsed row-by-row | Convert once: `vaex.from_csv('data.csv', convert='data.hdf5')`. Use HDF5 for all future loads |
| `MemoryError` on simple operations | Calling `.values` or `.to_pandas_df()` on full dataset | Keep operations lazy. Use `.sample(n=1000).to_pandas_df()` for inspection |
| Empty or all-white 2D plot | Axis limits don't match data range | Use `limits='99.7%'` or `limits='minmax'` instead of manual limits |
| Heatmap shows only one bright spot | Linear color scale overwhelmed by high-density region | Use `f='log'` for logarithmic color scaling |
| Virtual column recomputes slowly in loop | Complex expression recomputed on every access | Materialize: `df['col'] = df.complex_expr.values` |
| `FileNotFoundError` with cloud paths | Missing filesystem library | Install `s3fs` (S3), `gcsfs` (GCS), or `adlfs` (Azure) |
| Slow export with many virtual columns | Each virtual column recomputed during export | Materialize first: `df.materialize().export_hdf5('out.hdf5')` |
| Column shows as string when numeric expected | CSV auto-detection chose wrong type | Cast: `df['col_num'] = df.col.astype('float64')` |
| `state_load` fails on new data | Column names in state don't match new DataFrame | Ensure new data has identical column names as the training data |

## Bundled Resources

This entry includes two reference files in `references/`:

- **`references/io_performance.md`** -- Consolidated from original `io_operations.md` (704 lines) and `performance.md` (572 lines).
  Covers: format-specific I/O details (HDF5 compression options, Parquet compression, Arrow integration, FITS), chunked I/O processing, cloud storage (S3/GCS/Azure with credentials), Vaex server (remote data), database integration (SQL read/write via pandas bridge), state files (save/load pipeline state), memory management, parallel computation (multithreading, Dask integration), JIT compilation with Numba, async operations, and detailed profiling/benchmarking patterns.
  Relocated inline: format comparison table, CSV-to-HDF5 conversion pattern, `delay=True` batching, memory-mapped architecture explanation, basic export methods.
  Omitted: redundant "Best Practices" lists that duplicated content already in the main file; "Related Resources" cross-links (superseded by Bundled Resources section).

- **`references/ml_visualization.md`** -- Consolidated from original `machine_learning.md` (729 lines) and `visualization.md` (614 lines).
  Covers: full ML transformer catalog (MinMaxScaler, MaxAbsScaler, RobustScaler, FrequencyEncoder, TargetEncoder, WeightOfEvidenceEncoder, CycleTransformer, Discretizer, RandomProjection), KMeans clustering, external library integration (XGBoost, LightGBM, CatBoost, Keras), cross-validation, feature selection, imbalanced data handling, advanced visualization (contour plots, vector field overlays, interactive Jupyter widgets, faceted plots, batch plotting, Plotly/seaborn integration).
  Relocated inline: StandardScaler, LabelEncoder, OneHotEncoder, PCA, scikit-learn Predictor wrapper, basic plot1d/plot/what patterns, selection-based visualization.
  Omitted: model evaluation metrics section (standard sklearn metrics, not vaex-specific -- use scikit-learn directly); "Related Resources" cross-links.

**Original reference file disposition:**
- `core_dataframes.md` (368 lines) -- fully consolidated into Core API Module 1 (DataFrame Creation & I/O) and Key Concepts. Combined coverage: ~65 lines inline covering all creation methods (open, from_csv, from_arrays, from_dict, from_pandas, from_arrow_table), inspection, export, and expression basics. Omitted: detailed row/column manipulation patterns (covered in Module 2-4), copy/concat patterns (covered in Recipes).
- `data_processing.md` (556 lines) -- fully consolidated into Core API Modules 2-5. Filtering, virtual columns, expressions, aggregation, groupby, string ops, datetime ops, missing data, joining, column management all represented inline. Omitted: advanced binning (searchsorted patterns, statistical binning details) -- niche usage, consult official docs.

## Related Skills

- **polars-dataframes** -- In-memory DataFrame library; use when data fits in RAM for 10-100x faster processing
- **dask-parallel-computing** -- Distributed computing for multi-node clusters and parallel pandas/NumPy
- **pandas** (planned) -- Standard Python DataFrame library; Vaex interoperates via `from_pandas`/`to_pandas_df`

## References

- Vaex documentation: https://vaex.io/docs/latest/
- Vaex GitHub repository: https://github.com/vaexio/vaex
- Vaex PyPI: https://pypi.org/project/vaex/
- Breddels & Veljanoski (2018), "Vaex: Big Data exploration in the era of Gaia", Astronomy & Astrophysics, https://doi.org/10.1051/0004-6361/201732493
