# Polars I/O & Best Practices Reference

Comprehensive guide to data I/O formats, database connectivity, cloud storage, in-memory conversions, expression patterns, memory management, testing, and performance optimization. Supplements the main SKILL.md with detail not covered there.

## CSV Options

### Reading CSV with Full Options

```python
import polars as pl

# Full-featured CSV read
df = pl.read_csv(
    "data.csv",
    separator=",",          # delimiter character
    has_header=True,         # first row is header
    columns=["id", "name", "value"],  # select specific columns
    n_rows=1000,             # limit rows (for sampling/testing)
    skip_rows=10,            # skip header rows
    dtypes={"id": pl.Int64, "name": pl.Utf8, "value": pl.Float64},
    null_values=["NA", "null", "", "N/A"],  # values to interpret as null
    encoding="utf-8",
    ignore_errors=False,     # raise on parse errors
    try_parse_dates=True,    # auto-detect date columns
)
print(f"Shape: {df.shape}, Size: {df.estimated_size('mb'):.2f} MB")

# Lazy scan (recommended for large files)
lf = pl.scan_csv("data.csv")
result = lf.filter(pl.col("value") > 0).select("id", "value").collect()
```

### Writing CSV

```python
df.write_csv(
    "output.csv",
    separator=",",
    include_header=True,
    null_value="",           # how nulls are written
    quote_char='"',
    line_terminator="\n",
    datetime_format="%Y-%m-%d %H:%M:%S",  # format for datetime columns
    date_format="%Y-%m-%d",
)
```

### Multiple CSV Files

```python
# Read all CSVs matching glob pattern (lazy)
lf = pl.scan_csv("data/*.csv")
result = lf.filter(pl.col("date") > "2023-01-01").collect()

# Read explicit file list
lf = pl.scan_csv(["jan.csv", "feb.csv", "mar.csv"])
```

## Parquet Options

### Reading Parquet

```python
# Eager with options
df = pl.read_parquet(
    "data.parquet",
    columns=["col1", "col2"],    # projection pushdown
    n_rows=1000,
    parallel="auto",              # auto, columns, row_groups, none
)

# Lazy (recommended) — automatic predicate & projection pushdown
lf = pl.scan_parquet("data.parquet")
result = lf.filter(pl.col("age") > 25).select("name", "age").collect()

# Read multiple Parquet files
lf = pl.scan_parquet("data/*.parquet")
```

### Writing Parquet

```python
# With compression options
df.write_parquet(
    "output.parquet",
    compression="zstd",     # Options: snappy, gzip, brotli, lz4, zstd, uncompressed
    statistics=True,         # write column statistics for predicate pushdown
    use_pyarrow=False,       # use Rust writer (faster)
)
```

### Partitioned Parquet (Hive-style)

```python
# Write partitioned
df.write_parquet(
    "output_dir",
    partition_by=["year", "month"],
)
# Creates: output_dir/year=2023/month=01/data.parquet

# Read partitioned — hive columns auto-detected
lf = pl.scan_parquet("output_dir/**/*.parquet", hive_partitioning=True)
result = lf.filter(pl.col("year") == 2023, pl.col("month") == 6).collect()
```

## JSON and NDJSON

```python
# NDJSON (newline-delimited JSON) — recommended for large files
df = pl.read_ndjson("data.ndjson")
lf = pl.scan_ndjson("data.ndjson")  # lazy mode
df.write_ndjson("output.ndjson")

# Standard JSON
df = pl.read_json("data.json")
df.write_json("output.json")
```

## Excel (Multi-sheet)

```python
# Read specific sheet
df = pl.read_excel("data.xlsx", sheet_name="Sheet1")
# Or by index
df = pl.read_excel("data.xlsx", sheet_id=0)

# With options
df = pl.read_excel(
    "data.xlsx",
    sheet_name="Data",
    columns=["A", "B", "C"],
    n_rows=100,
    skip_rows=5,
    has_header=True,
)

# Write to Excel
df.write_excel("output.xlsx")
```

## Arrow IPC / Feather

Fastest serialization for inter-process data exchange:

```python
# Read
df = pl.read_ipc("data.arrow")
lf = pl.scan_ipc("data.arrow")   # lazy mode

# Write
df.write_ipc("output.arrow")
df.write_ipc("output.arrow", compression="zstd")  # with compression

# Arrow interop
import pyarrow as pa
arrow_table = pa.table({"col": [1, 2, 3]})
df = pl.from_arrow(arrow_table)
back = df.to_arrow()
```

## Database Connectivity

### Read from Databases

```python
import polars as pl

# PostgreSQL (via connectorx — fastest)
df = pl.read_database_uri(
    "SELECT * FROM users WHERE age > 25",
    uri="postgresql://user:pass@localhost:5432/mydb",
)

# MySQL
df = pl.read_database_uri(
    "SELECT * FROM orders",
    uri="mysql://user:pass@localhost:3306/mydb",
)

# SQLite
df = pl.read_database_uri(
    "SELECT * FROM products",
    uri="sqlite:///path/to/database.db",
)
```

### Write to Databases

```python
from sqlalchemy import create_engine

engine = create_engine("postgresql://user:pass@localhost/db")
df.write_database(
    "table_name",
    connection=engine,
    if_table_exists="replace",  # or "append", "fail"
)
```

### BigQuery

```python
# Via connectorx
df = pl.read_database_uri(
    "SELECT * FROM project.dataset.table",
    uri="bigquery://project",
)

# Via Google Cloud SDK (for complex queries)
from google.cloud import bigquery
client = bigquery.Client()
query = "SELECT * FROM project.dataset.table WHERE date > '2023-01-01'"
df = pl.from_pandas(client.query(query).to_dataframe())
```

## Cloud Storage

### AWS S3

```python
import os

# Set credentials (or use AWS config/IAM role)
os.environ["AWS_ACCESS_KEY_ID"] = "your_key"
os.environ["AWS_SECRET_ACCESS_KEY"] = "your_secret"
os.environ["AWS_REGION"] = "us-west-2"

df = pl.read_parquet("s3://bucket/path/file.parquet")
lf = pl.scan_parquet("s3://bucket/path/*.parquet")
df.write_parquet("s3://bucket/path/output.parquet")
```

### Azure Blob Storage

```python
os.environ["AZURE_STORAGE_ACCOUNT_NAME"] = "account"
os.environ["AZURE_STORAGE_ACCOUNT_KEY"] = "key"

df = pl.read_parquet("az://container/path/file.parquet")
df.write_parquet("az://container/path/output.parquet")
```

### Google Cloud Storage

```python
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "/path/to/credentials.json"

df = pl.read_parquet("gs://bucket/path/file.parquet")
lf = pl.scan_parquet("gs://bucket/*.parquet")
df.write_parquet("gs://bucket/path/output.parquet")
```

## In-Memory Format Conversions

### Python Dictionaries

```python
# From dict
df = pl.DataFrame({"col1": [1, 2, 3], "col2": ["a", "b", "c"]})

# To dict (column-oriented)
d = df.to_dict()            # {col: Series}
d = df.to_dict(as_series=False)  # {col: list}

# From list of dicts (row-oriented)
data = [{"name": "Alice", "age": 25}, {"name": "Bob", "age": 30}]
df = pl.DataFrame(data)

# To list of dicts
rows = df.to_dicts()        # [{"name": "Alice", "age": 25}, ...]
```

### NumPy Arrays

```python
import numpy as np

# From NumPy
arr = np.array([[1, 2], [3, 4], [5, 6]])
df = pl.DataFrame(arr, schema=["col1", "col2"])

# To NumPy
arr = df.to_numpy()          # 2D array
series_arr = df["col1"].to_numpy()  # 1D array
```

### Pandas DataFrames

```python
import pandas as pd

# Pandas → Polars
pd_df = pd.DataFrame({"col": [1, 2, 3]})
pl_df = pl.from_pandas(pd_df)

# Polars → Pandas
pd_df = pl_df.to_pandas()

# Zero-copy via Arrow (when possible)
pl_df = pl.from_arrow(pd_df)
```

## Format Selection Guide

| Format | Best For | Compression | Type Preservation | Human-Readable | Lazy Scan |
|--------|----------|-------------|-------------------|----------------|-----------|
| **Parquet** | Large datasets, data lakes, archival | Excellent (5-10x vs CSV) | Full | No | Yes |
| **CSV** | Small data, legacy systems, sharing | None | None (all strings) | Yes | Yes |
| **NDJSON** | Streaming, APIs, nested data | None | Partial | Yes | Yes |
| **Arrow IPC** | Inter-process, temp storage | Good | Full | No | Yes |
| **Excel** | Business reports, manual review | N/A | Partial | Yes | No |

**Decision heuristic**: Default to Parquet. Use CSV only when human readability is required. Use Arrow IPC when zero-copy sharing between processes is needed. Use NDJSON for streaming/API integration.

## Schema Management and Error Handling

```python
import polars as pl

# Infer schema from sample, then apply to full read
schema = pl.read_csv("data.csv", n_rows=1000).schema
print(schema)
# {'id': Int64, 'name': Utf8, 'date': Utf8, 'value': Float64}

# Apply inferred schema (avoids re-inference on full file)
df = pl.read_csv("data.csv", dtypes=schema)

# Define schema explicitly
schema = {
    "id": pl.Int64,
    "name": pl.Utf8,
    "date": pl.Date,
    "value": pl.Float64,
}
df = pl.read_csv("data.csv", dtypes=schema)

# Validate schema after read
expected = {"id": pl.Int64, "name": pl.Utf8}
for col, dtype in expected.items():
    assert col in df.schema, f"Missing column: {col}"
    assert df.schema[col] == dtype, f"Wrong type for {col}: {df.schema[col]}"
```

### Error Handling

```python
try:
    df = pl.read_csv("data.csv")
except pl.exceptions.ComputeError as e:
    print(f"Parse error: {e}")
except FileNotFoundError:
    print("File not found")

# Ignore parse errors (skip malformed rows)
df = pl.read_csv("messy.csv", ignore_errors=True)

# Handle missing files gracefully
from pathlib import Path
files = list(Path("data/").glob("*.csv"))
if files:
    dfs = [pl.read_csv(f) for f in files]
    combined = pl.concat(dfs, how="diagonal")
else:
    print("No CSV files found")
```

## Expression Composition and Reuse

Define expressions once, use in multiple contexts:

```python
import polars as pl

# Reusable expression definitions
age_group = (
    pl.when(pl.col("age") < 18).then(pl.lit("minor"))
    .when(pl.col("age") < 65).then(pl.lit("adult"))
    .otherwise(pl.lit("senior"))
)

revenue_per_customer = pl.col("revenue") / pl.col("customer_count")

is_high_value = pl.col("revenue") > 100000

# Use in different contexts
df = pl.DataFrame({
    "name": ["Alice", "Bob", "Charlie"],
    "age": [15, 35, 70],
    "revenue": [50000, 150000, 80000],
    "customer_count": [10, 50, 20],
})

# In with_columns
result = df.with_columns(
    age_category=age_group,
    rpc=revenue_per_customer,
)

# In filter
high_value = df.filter(is_high_value)

# In group_by
summary = result.group_by("age_category").agg(
    pl.col("rpc").mean().alias("avg_rpc"),
)
print(summary)
```

### Column Selection Patterns

```python
import polars as pl

df = pl.DataFrame({
    "val_a": [1, 2], "val_b": [3, 4],
    "name": ["x", "y"], "active": [True, False],
    "score": [0.5, 0.8],
})

# By regex pattern
vals = df.select(pl.col("^val_.*$"))
print(vals.columns)  # ['val_a', 'val_b']

# By data type
numerics = df.select(pl.col(pl.NUMERIC_DTYPES))
print(numerics.columns)  # ['val_a', 'val_b', 'score']

strings = df.select(pl.col(pl.Utf8))
print(strings.columns)  # ['name']

# Exclude specific columns
no_name = df.select(pl.all().exclude("name", "active"))
print(no_name.columns)  # ['val_a', 'val_b', 'score']

# Apply same operation to multiple columns by pattern
doubled = df.select(pl.col("^val_.*$") * 2)
print(doubled)
```

## Memory Management

```python
import polars as pl

# Check DataFrame memory usage
df = pl.DataFrame({"a": range(1_000_000), "b": range(1_000_000)})
print(f"Estimated size: {df.estimated_size('mb'):.2f} MB")

# Reduce memory by optimizing types
optimized = df.with_columns(
    pl.col("a").cast(pl.Int32),     # downcast if values fit
    pl.col("b").cast(pl.Int32),
)
print(f"Optimized: {optimized.estimated_size('mb'):.2f} MB")

# Use Categorical for string columns with repeated values
str_df = pl.DataFrame({"category": ["A", "B", "A", "B", "A"] * 200_000})
print(f"String: {str_df.estimated_size('mb'):.2f} MB")
cat_df = str_df.with_columns(pl.col("category").cast(pl.Categorical))
print(f"Categorical: {cat_df.estimated_size('mb'):.2f} MB")

# Profile memory during lazy operations
lf = pl.scan_csv("data.csv")
query = lf.filter(pl.col("age") > 25).select("name", "age")
print(query.explain())  # shows optimized query plan
```

### Streaming for Large Data

```python
# Process data larger than RAM
lf = pl.scan_parquet("very_large.parquet")
result = lf.filter(pl.col("value") > 100).collect(streaming=True)

# Sink directly to file (no full materialization)
lf.filter(pl.col("active")).sink_parquet("filtered.parquet")
```

## Pipeline Functions

Organize complex transformations as composable pipeline steps:

```python
import polars as pl

def clean_data(lf: pl.LazyFrame) -> pl.LazyFrame:
    """Standardize column values and parse types."""
    return lf.with_columns(
        pl.col("name").str.to_uppercase(),
        pl.col("date").str.to_date("%Y-%m-%d"),
        pl.col("amount").fill_null(0),
    )

def add_features(lf: pl.LazyFrame) -> pl.LazyFrame:
    """Engineer temporal and derived features."""
    return lf.with_columns(
        month=pl.col("date").dt.month(),
        year=pl.col("date").dt.year(),
        amount_log=pl.col("amount").log(),
        is_large=pl.col("amount") > 1000,
    )

def summarize(lf: pl.LazyFrame) -> pl.LazyFrame:
    """Aggregate by year and month."""
    return lf.group_by("year", "month").agg(
        pl.col("amount").sum().alias("total"),
        pl.col("amount").mean().alias("avg"),
        pl.len().alias("count"),
    )

# Compose pipeline
result = (
    pl.scan_csv("transactions.csv")
    .pipe(clean_data)
    .pipe(add_features)
    .pipe(summarize)
    .sort("year", "month")
    .collect()
)
print(result)
```

## Testing and Debugging

### Inspect Query Plans

```python
lf = pl.scan_csv("data.csv")
query = lf.filter(pl.col("age") > 25).select("name", "age")

# Optimized plan (what will actually execute)
print(query.explain())
# Shows: FILTER, PROJECT pushdowns applied

# Unoptimized plan (for debugging)
print(query.explain(optimized=False))
```

### Schema Validation

```python
# Assert schema matches expectation
expected_schema = {"id": pl.Int64, "name": pl.Utf8, "date": pl.Date}
assert df.schema == expected_schema, f"Schema mismatch: {df.schema}"

# Check column existence
required_cols = {"id", "name", "value"}
missing = required_cols - set(df.columns)
assert not missing, f"Missing columns: {missing}"
```

### Performance Profiling

```python
import time

# Compare eager vs lazy execution
# Eager
start = time.time()
df_eager = pl.read_csv("data.csv").filter(pl.col("age") > 25)
eager_time = time.time() - start

# Lazy
start = time.time()
df_lazy = pl.scan_csv("data.csv").filter(pl.col("age") > 25).collect()
lazy_time = time.time() - start

print(f"Eager: {eager_time:.3f}s, Lazy: {lazy_time:.3f}s")

# Sample for development
df_sample = pl.read_csv("large.csv", n_rows=10_000)
```

## Performance Anti-Patterns

Patterns to avoid (not covered in main SKILL.md best practices):

### Sequential Pipe vs Parallel Expressions

```python
# BAD: Sequential pipe disables parallelization
def step1(df):
    return df.with_columns(a=pl.col("x") * 2)
def step2(df):
    return df.with_columns(b=pl.col("x") * 3)

result = df.pipe(step1).pipe(step2)

# GOOD: Single with_columns enables parallel execution
result = df.with_columns(
    a=pl.col("x") * 2,
    b=pl.col("x") * 3,
)
```

### Many Small DataFrames vs Chaining

```python
# BAD: Creates unnecessary intermediate DataFrames
df1 = df.filter(pl.col("age") > 25)
df2 = df1.select("name", "age")
df3 = df2.sort("age")
result = df3.head(10)

# GOOD: Chain operations (or use lazy mode)
result = (
    df.lazy()
    .filter(pl.col("age") > 25)
    .select("name", "age")
    .sort("age")
    .head(10)
    .collect()
)
```

### Modifying in Place

```python
# BAD: Polars is immutable — this may work but is not idiomatic
df["new_col"] = df["old_col"] * 2

# GOOD: Functional style
df = df.with_columns(new_col=pl.col("old_col") * 2)
```

### Not Specifying Types on CSV Read

```python
# BAD: Re-infers types on every read
df = pl.read_csv("data.csv")

# GOOD: Specify types for correctness and speed
df = pl.read_csv(
    "data.csv",
    dtypes={
        "id": pl.UInt32,          # smaller than default Int64
        "category": pl.Categorical,  # faster groupby
        "date": pl.Date,
        "small_int": pl.Int16,
    }
)
```

## Version Compatibility Notes

```python
import polars as pl
print(f"Polars version: {pl.__version__}")

# Key API changes to be aware of:
# - polars >= 0.19: `melt()` renamed to `unpivot()`
# - polars >= 0.20: `groupby()` renamed to `group_by()`
# - polars >= 1.0: stable API; `Utf8` aliased as `String`
# - polars >= 1.0: `streaming` parameter in collect() is stable
# - Always check docs.pola.rs for current API when using older tutorials
```

---

## Condensation Note

Consolidated from 3 original files:
- **io_guide.md** (558 lines): Retained all I/O format sections (CSV, Parquet, JSON, Excel, Arrow IPC), database connectivity (PostgreSQL, MySQL, SQLite, BigQuery), cloud storage (S3, Azure, GCS), in-memory conversions (dict, NumPy, pandas, Arrow), streaming/large files, schema management, error handling. Omitted: basic write examples duplicating read patterns (symmetric read/write pairs kept to one direction where obvious).
- **best_practices.md** (650 lines): Retained expression composition/reuse, column selection patterns, pipeline functions, memory management (estimated_size, type optimization, streaming), testing/debugging (query plans, schema validation, profiling), performance anti-patterns (sequential pipe, many small DataFrames, in-place modification, unspecified types), version compatibility. Omitted: basic lazy vs eager explanation (covered in SKILL.md section 7 + Key Concepts table), basic conditional logic examples (SKILL.md section 6), null handling basics (SKILL.md section 6), basic aggregation patterns (SKILL.md section 2), format selection rationale (summarized as table here).
- **core_concepts.md** (379 lines): Retained format selection guide (as summary table), version compatibility notes. Omitted: expression fundamentals (covered in SKILL.md sections 1, 6), data type reference table (SKILL.md Key Concepts), lazy vs eager comparison (SKILL.md Key Concepts table), parallelization concepts (SKILL.md Best Practices), strict type system explanation (SKILL.md Key Concepts), null handling (SKILL.md section 6), categorical data concepts (SKILL.md Best Practices item 4).

Combined source: 1,587 lines. This file: ~470 lines. Standalone retention: ~30%. Combined coverage with SKILL.md: core_concepts.md content relocated to SKILL.md Key Concepts + Best Practices accounts for ~250 lines; best_practices.md basics in SKILL.md account for ~80 lines; io_guide.md basics in SKILL.md section 5 account for ~40 lines. Combined coverage: (470 + 370) / 1,587 = ~53%.
