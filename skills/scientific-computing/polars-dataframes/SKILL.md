---
name: polars-dataframes
description: >-
  Fast in-memory DataFrame library with lazy evaluation, parallel execution, and Apache Arrow backend.
  Use when processing tabular data that fits in RAM (1–100 GB) and pandas is too slow.
  Expression-based API for select, filter, group_by, joins, pivots, and window functions.
  Lazy mode enables query optimization (predicate/projection pushdown). Reads CSV, Parquet, JSON, Excel, databases, cloud storage.
  For larger-than-RAM data use Dask; for GPU acceleration use cuDF.
license: MIT
---

# Polars DataFrames

## Overview

Polars is a high-performance DataFrame library for Python built on Apache Arrow with a Rust backend. It provides an expression-based API with lazy evaluation and automatic parallelization for efficient data processing, transformation, and analysis.

## When to Use

- Processing tabular datasets from 100 MB to 100 GB that fit in RAM
- ETL pipelines requiring fast read/transform/write cycles
- Replacing pandas when performance matters (10–100x speedup typical)
- Lazy query pipelines with automatic optimization (predicate/projection pushdown)
- Joining, pivoting, and reshaping large tables
- Reading Parquet, CSV, JSON, or cloud-stored data efficiently
- Window functions and complex grouped aggregations
- For larger-than-RAM data, use **Dask** or **Vaex** instead
- For GPU-accelerated DataFrames, use **cuDF** instead

## Prerequisites

```bash
pip install polars
# Optional extras:
pip install polars[all]          # All I/O backends
pip install polars[pandas]       # Pandas interop
pip install polars[numpy]        # NumPy interop
pip install connectorx sqlalchemy  # Database connectivity
```

## Quick Start

```python
import polars as pl

# Create DataFrame
df = pl.DataFrame({
    "name": ["Alice", "Bob", "Charlie", "Diana"],
    "dept": ["Sales", "Eng", "Sales", "Eng"],
    "salary": [70000, 85000, 72000, 90000],
})

# Expression-based pipeline
result = (
    df.filter(pl.col("salary") > 71000)
    .with_columns(bonus=pl.col("salary") * 0.1)
    .group_by("dept")
    .agg(
        pl.col("salary").mean().alias("avg_salary"),
        pl.len().alias("count"),
    )
)
print(result)
# shape: (2, 3)
# ┌───────┬────────────┬───────┐
# │ dept  ┆ avg_salary ┆ count │
# ├───────┼────────────┼───────┤
# │ Eng   ┆ 87500.0    ┆ 2     │
# │ Sales ┆ 72000.0    ┆ 1     │
# └───────┴────────────┴───────┘
```

## Core API

### 1. DataFrame Operations

Select, filter, add/modify columns, sort, and sample rows.

```python
import polars as pl

df = pl.DataFrame({
    "id": [1, 2, 3, 4, 5],
    "name": ["Alice", "Bob", "Charlie", "Diana", "Eve"],
    "age": [25, 30, 35, 28, 32],
    "score": [88.5, 92.0, 76.3, 95.1, 84.7],
})

# Select columns (with computed expressions)
selected = df.select(
    "name",
    pl.col("age"),
    (pl.col("score") / 100).alias("score_pct"),
)
print(selected.shape)  # (5, 3)

# Filter rows (multiple conditions → implicit AND)
filtered = df.filter(
    pl.col("age") > 27,
    pl.col("score") > 80,
)
print(filtered.shape)  # (3, 4) — Bob, Diana, Eve

# Add columns (preserves existing)
enriched = df.with_columns(
    grade=pl.when(pl.col("score") >= 90).then(pl.lit("A"))
           .when(pl.col("score") >= 80).then(pl.lit("B"))
           .otherwise(pl.lit("C")),
    age_months=pl.col("age") * 12,
)
print(enriched.columns)
# ['id', 'name', 'age', 'score', 'grade', 'age_months']

# Sort
df.sort("score", descending=True).head(3)
```

### 2. GroupBy & Aggregations

Group rows and compute summary statistics.

```python
import polars as pl

sales = pl.DataFrame({
    "region": ["East", "West", "East", "West", "East", "West"],
    "product": ["A", "A", "B", "B", "A", "B"],
    "revenue": [100, 150, 200, 180, 120, 210],
    "units": [10, 15, 20, 18, 12, 21],
})

# Basic group_by
summary = sales.group_by("region").agg(
    pl.col("revenue").sum().alias("total_rev"),
    pl.col("revenue").mean().alias("avg_rev"),
    pl.len().alias("n_transactions"),
)
print(summary)

# Multiple keys + conditional aggregation
by_rp = sales.group_by("region", "product").agg(
    pl.col("revenue").sum(),
    (pl.col("units") > 15).sum().alias("large_orders"),
)
print(by_rp)
```

```python
# Window functions with over() — add group stats without collapsing rows
enriched = sales.with_columns(
    region_avg=pl.col("revenue").mean().over("region"),
    rank_in_region=pl.col("revenue").rank(descending=True).over("region"),
    pct_of_region=pl.col("revenue") / pl.col("revenue").sum().over("region"),
)
print(enriched.select("region", "product", "revenue", "region_avg", "rank_in_region"))
```

### 3. Joins

Combine DataFrames on shared keys.

```python
import polars as pl

customers = pl.DataFrame({
    "cid": [1, 2, 3, 4],
    "name": ["Alice", "Bob", "Charlie", "Diana"],
})
orders = pl.DataFrame({
    "oid": [101, 102, 103, 104],
    "cid": [1, 2, 1, 5],
    "amount": [100, 200, 150, 300],
})

# Inner join — only matching rows
inner = customers.join(orders, on="cid", how="inner")
print(inner.shape)  # (3, 4) — cid 1 (×2), cid 2

# Left join — all left rows, nulls where no match
left = customers.join(orders, on="cid", how="left")
print(left.shape)  # (4, 4) — Charlie and Diana have null amount

# Anti join — left rows WITHOUT a match in right
no_orders = customers.join(orders, on="cid", how="anti")
print(no_orders["name"].to_list())  # ['Charlie', 'Diana']

# Join on different column names
customers.join(orders, left_on="cid", right_on="cid", suffix="_order")
```

```python
# Asof join — match to nearest timestamp (time-series alignment)
quotes = pl.DataFrame({
    "time": [1.0, 2.0, 3.0, 4.0],
    "price": [100, 101, 102, 103],
}).cast({"time": pl.Float64})

trades = pl.DataFrame({
    "time": [1.5, 3.2],
    "qty": [50, 75],
}).cast({"time": pl.Float64})

result = trades.join_asof(quotes, on="time", strategy="backward")
print(result)
# time=1.5 matched price=100, time=3.2 matched price=102
```

### 4. Reshaping

Pivot, unpivot, explode, and transpose operations.

```python
import polars as pl

# --- Pivot (long → wide) ---
long = pl.DataFrame({
    "date": ["Jan", "Jan", "Feb", "Feb"],
    "product": ["A", "B", "A", "B"],
    "sales": [100, 150, 120, 160],
})
wide = long.pivot(values="sales", index="date", columns="product")
print(wide)
# date | A   | B
# Jan  | 100 | 150
# Feb  | 120 | 160

# --- Unpivot (wide → long) ---
back_to_long = wide.unpivot(
    index="date", on=["A", "B"],
    variable_name="product", value_name="sales",
)
print(back_to_long.shape)  # (4, 3)

# --- Explode list columns ---
nested = pl.DataFrame({
    "id": [1, 2],
    "tags": [["a", "b", "c"], ["d", "e"]],
})
flat = nested.explode("tags")
print(flat.shape)  # (5, 2)
```

### 5. Data I/O

Read and write CSV, Parquet, JSON, Excel, databases, and cloud storage.

```python
import polars as pl

# --- CSV ---
df = pl.read_csv("data.csv")
df.write_csv("output.csv")

# --- Parquet (recommended for performance) ---
df = pl.read_parquet("data.parquet")
df.write_parquet("output.parquet", compression="zstd")

# --- JSON / NDJSON ---
df = pl.read_ndjson("data.ndjson")
df.write_ndjson("output.ndjson")

# --- Excel ---
df = pl.read_excel("data.xlsx", sheet_name="Sheet1")
df.write_excel("output.xlsx")

# --- Lazy scan (preferred for large files) ---
lf = pl.scan_csv("large.csv")
result = lf.filter(pl.col("value") > 0).select("id", "value").collect()
print(result.shape)
```

```python
# --- Database ---
df = pl.read_database_uri(
    "SELECT * FROM users WHERE age > 25",
    uri="postgresql://user:pass@localhost/db",
)

# --- Cloud storage (S3, GCS, Azure) ---
df = pl.read_parquet("s3://bucket/data.parquet")
df = pl.scan_parquet("gs://bucket/data/*.parquet").collect()

# --- Partitioned Parquet (Hive-style) ---
df.write_parquet("output_dir", partition_by=["year", "month"])
lf = pl.scan_parquet("output_dir/**/*.parquet")
```

### 6. Expression API

String, datetime, list, and conditional operations.

```python
import polars as pl
from datetime import date

df = pl.DataFrame({
    "text": ["Hello World", "foo bar", "POLARS"],
    "dt": [date(2023, 1, 15), date(2023, 6, 30), date(2024, 12, 1)],
    "values": [[1, 2, 3], [4, 5], [6]],
})

# String operations
strings = df.select(
    lower=pl.col("text").str.to_lowercase(),
    length=pl.col("text").str.len_chars(),
    contains_o=pl.col("text").str.contains("o"),
    split=pl.col("text").str.split(" "),
)
print(strings)

# Datetime operations
dates = df.select(
    year=pl.col("dt").dt.year(),
    month=pl.col("dt").dt.month(),
    weekday=pl.col("dt").dt.weekday(),
    quarter=pl.col("dt").dt.quarter(),
)
print(dates)

# List operations
lists = df.select(
    list_len=pl.col("values").list.len(),
    list_sum=pl.col("values").list.sum(),
    first=pl.col("values").list.first(),
)
print(lists)
```

```python
# Conditional expressions (when/then/otherwise)
df = pl.DataFrame({"score": [45, 72, 88, 95, 60]})
result = df.with_columns(
    grade=pl.when(pl.col("score") >= 90).then(pl.lit("A"))
           .when(pl.col("score") >= 80).then(pl.lit("B"))
           .when(pl.col("score") >= 70).then(pl.lit("C"))
           .otherwise(pl.lit("F")),
)
print(result)

# Null handling
df2 = pl.DataFrame({"x": [1, None, 3, None, 5]})
filled = df2.with_columns(
    filled=pl.col("x").fill_null(0),
    forward=pl.col("x").fill_null(strategy="forward"),
    is_null=pl.col("x").is_null(),
)
print(filled)

# Multi-column operations with regex selector
df3 = pl.DataFrame({"val_a": [1, 2], "val_b": [3, 4], "name": ["x", "y"]})
doubled = df3.select(pl.col("^val_.*$") * 2)
print(doubled)
```

### 7. Lazy Evaluation

Build optimized query plans before execution.

```python
import polars as pl

# Lazy mode: build plan, optimize, then execute
lf = pl.scan_csv("large_dataset.csv")

result = (
    lf
    .select("user_id", "category", "amount", "date")  # projection pushdown
    .filter(pl.col("amount") > 100)                     # predicate pushdown
    .with_columns(pl.col("date").str.to_date())
    .group_by("category")
    .agg(
        pl.col("amount").sum().alias("total"),
        pl.col("user_id").n_unique().alias("unique_users"),
    )
    .sort("total", descending=True)
)

# Inspect the optimized plan
print(result.explain())

# Execute
df = result.collect()
print(df)
```

```python
# Streaming mode for very large data
lf = pl.scan_parquet("data/*.parquet")
result = (
    lf
    .filter(pl.col("year") >= 2023)
    .group_by("region")
    .agg(pl.col("sales").sum())
    .collect(streaming=True)  # processes in batches
)
print(result)

# Sink directly to file (no full materialization)
lf.filter(pl.col("active")).sink_parquet("filtered_output.parquet")
```

## Key Concepts

### Lazy vs Eager Comparison

| Aspect | Eager (`DataFrame`) | Lazy (`LazyFrame`) |
|--------|--------------------|--------------------|
| Created by | `pl.read_*()`, `pl.DataFrame()` | `pl.scan_*()`, `df.lazy()` |
| Execution | Immediate | On `.collect()` |
| Optimization | None | Predicate/projection pushdown, join reordering |
| Streaming | No | `collect(streaming=True)` |
| Best for | Small data, interactive | Large data, pipelines |

### Polars Data Types

| Type | Python equivalent | Notes |
|------|-------------------|-------|
| `Int8/16/32/64` | `int` | Choose smallest sufficient size |
| `UInt8/16/32/64` | `int` | Unsigned |
| `Float32/64` | `float` | Float64 default |
| `Boolean` | `bool` | |
| `Utf8` | `str` | String type |
| `Categorical` | — | Low-cardinality strings (faster groupby) |
| `Date` | `datetime.date` | Date without time |
| `Datetime` | `datetime.datetime` | With microsecond precision |
| `Duration` | `datetime.timedelta` | Time difference |
| `List` | `list` | Variable-length lists |
| `Struct` | `dict` | Named fields |
| `Null` | `None` | All-null column |

### Key Differences from Pandas

- **No index**: Row access by position only; no `.loc`/`.iloc` with labels
- **Strict typing**: No silent type coercion; explicit `.cast()` required
- **Expressions, not methods**: `pl.col("x").mean()` instead of `df["x"].mean()`
- **Parallel by default**: All column operations run in parallel
- **Lazy evaluation**: Available via `LazyFrame` for query optimization

## Common Workflows

### 1. ETL Pipeline (CSV → Clean → Parquet)

```python
import polars as pl

# Extract
lf = pl.scan_csv(
    "raw_data.csv",
    dtypes={"id": pl.Int64, "date": pl.Utf8, "amount": pl.Float64},
)

# Transform
cleaned = (
    lf
    .with_columns(pl.col("date").str.to_date("%Y-%m-%d"))
    .filter(pl.col("amount").is_not_null())
    .with_columns(
        year=pl.col("date").dt.year(),
        month=pl.col("date").dt.month(),
        amount_log=pl.col("amount").log(),
    )
    .drop_nulls()
)

# Load
cleaned.collect().write_parquet("clean_data.parquet", compression="zstd")
print("ETL complete")
```

### 2. Multi-Source Join and Aggregation

```python
import polars as pl

# Simulate three data sources
users = pl.DataFrame({
    "uid": [1, 2, 3, 4],
    "name": ["Alice", "Bob", "Charlie", "Diana"],
    "region": ["East", "West", "East", "West"],
})
orders = pl.DataFrame({
    "oid": range(1, 7),
    "uid": [1, 1, 2, 3, 3, 3],
    "amount": [100, 200, 150, 50, 75, 125],
})
products = pl.DataFrame({
    "oid": range(1, 7),
    "category": ["Elec", "Books", "Elec", "Books", "Elec", "Elec"],
})

# Join → aggregate
result = (
    orders
    .join(users, on="uid", how="left")
    .join(products, on="oid", how="left")
    .group_by("region", "category")
    .agg(
        pl.col("amount").sum().alias("total"),
        pl.col("amount").mean().alias("avg_order"),
        pl.len().alias("n_orders"),
    )
    .sort("total", descending=True)
)
print(result)
```

### 3. Time-Series Feature Engineering

Uses: GroupBy, Window functions, Joins, Expression API.

1. Load time-series data with `pl.scan_csv()` or `pl.scan_parquet()`
2. Parse dates: `.with_columns(pl.col("date").str.to_date())`
3. Sort by entity and date: `.sort("entity_id", "date")`
4. Add lag features: `pl.col("value").shift(n).over("entity_id")`
5. Add rolling statistics: `pl.col("value").rolling_mean(window_size=7).over("entity_id")`
6. Compute percent change: `(pl.col("value") - pl.col("value").shift(1)) / pl.col("value").shift(1)`
7. Collect and write: `.collect().write_parquet("features.parquet")`

## Key Parameters

| Parameter | Function | Default | Range/Options | Effect |
|-----------|----------|---------|---------------|--------|
| `how` | `.join()` | `"inner"` | inner, left, outer, cross, semi, anti | Join type |
| `strategy` | `.join_asof()` | `"backward"` | backward, forward, nearest | Asof match direction |
| `streaming` | `.collect()` | `False` | True/False | Process in batches for large data |
| `compression` | `.write_parquet()` | `"zstd"` | snappy, gzip, brotli, lz4, zstd, uncompressed | Parquet compression |
| `partition_by` | `.write_parquet()` | None | List of columns | Hive-style partitioning |
| `rechunk` | `pl.concat()` | `False` | True/False | Rechunk memory after concat |
| `aggregate_function` | `.pivot()` | `"first"` | first, sum, mean, max, min, count | Duplicate handling in pivot |
| `n_rows` | `pl.read_csv()` | None | Positive int | Limit rows read (for sampling) |
| `parallel` | `pl.read_csv()` | `"auto"` | auto, columns, row_groups, none | Parallel reading strategy |
| `dtypes` | `pl.read_csv()` | None | Dict of column→type | Override type inference |

## Best Practices

1. **Use lazy mode for large datasets**: `pl.scan_csv()` not `pl.read_csv()`. Enables query optimization and streaming.

2. **Stay in the expression API**: Avoid `.map_elements()` (runs Python, no parallelism). Prefer native Polars operations — string, datetime, list namespaces cover most needs.

3. **Select early, filter early**: Place `.select()` and `.filter()` as early as possible in lazy pipelines. The optimizer can push these down but explicit placement helps.

4. **Use Categorical for low-cardinality strings**: `df.with_columns(pl.col("region").cast(pl.Categorical))` — dramatically speeds up groupby and joins on repeated string values.

5. **Prefer Parquet over CSV**: Parquet preserves types, supports predicate pushdown, and is 5–10x smaller. Use `compression="zstd"` for best compression/speed balance.

6. **Anti-pattern — Python loops over rows**: Never iterate rows with `for row in df.iter_rows()` for computation. Use expressions instead.

7. **Anti-pattern — chaining `.with_columns()` calls**: Combine multiple column additions into a single `.with_columns()` call for parallel execution.

## Common Recipes

### Recipe: Pandas Migration Pattern

```python
import polars as pl
import pandas as pd

# Convert pandas → polars
pd_df = pd.DataFrame({"col": [1, 2, 3], "group": ["a", "b", "a"]})
pl_df = pl.from_pandas(pd_df)

# Key operation mapping:
# pandas: df["col"]              → polars: df.select("col")
# pandas: df[df["col"] > 1]     → polars: df.filter(pl.col("col") > 1)
# pandas: df.assign(x=...)      → polars: df.with_columns(x=...)
# pandas: df.groupby().agg()    → polars: df.group_by().agg()
# pandas: df.groupby().transform → polars: pl.col(...).over(...)
# pandas: df.merge()            → polars: df.join()
# pandas: df.melt()             → polars: df.unpivot()

# Convert back
pd_result = pl_df.to_pandas()
```

### Recipe: Complex Aggregation Report

```python
import polars as pl

df = pl.DataFrame({
    "dept": ["Sales", "Eng", "Sales", "Eng", "Sales", "Eng"],
    "level": ["Jr", "Sr", "Sr", "Jr", "Jr", "Sr"],
    "salary": [50000, 95000, 75000, 70000, 55000, 100000],
})

report = (
    df.group_by("dept", "level")
    .agg(
        pl.col("salary").mean().alias("avg_sal"),
        pl.col("salary").median().alias("med_sal"),
        pl.col("salary").std().alias("std_sal"),
        pl.len().alias("count"),
    )
    .pivot(values="avg_sal", index="dept", columns="level")
    .with_columns(
        diff=pl.col("Sr") - pl.col("Jr"),
    )
)
print(report)
```

### Recipe: Reading Multiple Files with Schema Alignment

```python
import polars as pl
from pathlib import Path

# Read multiple CSVs with potentially different columns
files = sorted(Path("data/").glob("*.csv"))
dfs = [pl.read_csv(f) for f in files]

# Diagonal concat handles mismatched schemas (fills nulls)
combined = pl.concat(dfs, how="diagonal")
print(f"Combined: {combined.shape}")
print(f"Columns: {combined.columns}")

# Or use lazy scan for Parquet (automatic parallel)
lf = pl.scan_parquet("data/**/*.parquet")
result = lf.filter(pl.col("date") > "2023-01-01").collect()
```

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|---------|
| `SchemaError: column not found` | Column name typo or case mismatch | Check `df.columns`; Polars is case-sensitive |
| `ComputeError: cannot cast` | Type mismatch in operation | Use `.cast(pl.Type)` explicitly |
| `OutOfMemoryError` on collect | Data too large for eager mode | Use `lf.collect(streaming=True)` or filter first |
| Slow `.map_elements()` | Python UDF prevents parallelism | Rewrite using native expressions (str/dt/list namespaces) |
| Join produces more rows than expected | Duplicate keys in right DataFrame | Deduplicate first: `df.unique(subset=["key"])` |
| `InvalidOperationError: join on different types` | Key columns have different dtypes | Cast both to same type: `.cast(pl.Int64)` |
| `.over()` returns wrong values | Forgetting to include all group columns | Include all grouping columns in `.over("col1", "col2")` |
| Parquet file unreadable | Written with incompatible compression | Specify `compression="snappy"` for maximum compatibility |
| CSV dates read as strings | No automatic date parsing in CSV reader | Parse after reading: `pl.col("date").str.to_date("%Y-%m-%d")` |
| `concat` fails with different schemas | Columns don't match across DataFrames | Use `how="diagonal"` to fill missing columns with null |

## Bundled Resources

- **`references/pandas_migration.md`** — Pandas-to-Polars migration guide with operation mapping tables (selection, filtering, column ops, aggregation, window functions, joins, reshaping, string ops, datetime ops, missing data, I/O), interoperability code, common migration patterns with side-by-side code, migration pitfalls, and migration checklist.
  - Covers: all operation mapping content from original pandas_migration.md
  - Relocated inline: key pandas differences summary → SKILL.md Key Concepts "Key Differences from Pandas" section; basic conversion recipe → SKILL.md Common Recipes "Pandas Migration Pattern"
  - Omitted: anti-pattern code examples for row iteration and sequential pipe — covered in io_best_practices.md

- **`references/advanced_operations.md`** — Rolling windows (time-based and row-based), cumulative operations (cum_sum/max/min/prod), shift/lag/lead with grouped contexts, struct operations (create/access/unnest), list column manipulation (stats, eval, filter, explode), unique/duplicate detection, advanced sorting (nulls_last, expression-based, top-N per group), column renaming (dict, suffix/prefix/programmatic), sampling (fixed n, fraction, bootstrap), transpose, and advanced reshaping patterns (wide-long-wide, nested JSON to flat, multi-level unpivot, horizontal concat).
  - Covers: advanced operations from original operations.md + transformations from original transformations.md not in main SKILL.md
  - Relocated inline: basic selection/filtering → SKILL.md Core API section 1; groupby/aggregation → section 2; basic joins/asof → section 3; basic pivot/unpivot/explode/concat → section 4; string/date/list/conditional basics → section 6; basic window functions → section 2
  - Omitted: join performance tips (simple; covered in SKILL.md Best Practices); concatenation options (rechunk covered in Key Parameters table)

- **`references/io_best_practices.md`** — Full I/O format guide (CSV options, Parquet options with partitioning, JSON/NDJSON, Excel multi-sheet, Arrow IPC), database connectivity (PostgreSQL, MySQL, SQLite, BigQuery), cloud storage (S3, Azure, GCS), in-memory format conversions (dict, NumPy, pandas, Arrow), format selection decision guide, schema management and error handling, expression composition and reuse patterns, column selection patterns (by type, regex, exclude), memory management (estimated_size, type optimization, streaming), pipeline functions for composable transforms, testing/debugging (query plans, schema validation, profiling), performance anti-patterns (sequential pipe, many DataFrames, in-place mutation, unspecified types), and version compatibility notes.
  - Covers: all I/O content from original io_guide.md + expression/memory/testing/performance content from original best_practices.md + format selection and version notes from original core_concepts.md
  - Relocated inline: basic CSV/Parquet/JSON/Excel/database read/write → SKILL.md Core API section 5; lazy vs eager comparison → SKILL.md Key Concepts table; basic expression context/syntax → SKILL.md section 6; parallelization/type system concepts → SKILL.md Key Concepts + Best Practices; null handling → SKILL.md section 6; categorical recommendation → SKILL.md Best Practices item 4
  - Omitted: detailed expression fundamentals (what are expressions, expression contexts) — fully covered in SKILL.md Core API; basic conditional logic examples — covered in SKILL.md section 6; basic aggregation patterns — covered in SKILL.md section 2

### Per-Reference-File Disposition (Original 6 files)

| Original File | Lines | Disposition | Target |
|---------------|-------|-------------|--------|
| `operations.md` | 603 | Consolidated | Advanced ops → `references/advanced_operations.md`; basic selection/filter/groupby/window/string/date → SKILL.md Core API sections 1-2, 6 |
| `transformations.md` | 550 | Consolidated | Reshaping/transpose → `references/advanced_operations.md`; basic joins/pivot/unpivot/explode/concat → SKILL.md Core API sections 3-4 |
| `io_guide.md` | 558 | Consolidated | Full I/O detail → `references/io_best_practices.md`; basic read/write → SKILL.md Core API section 5 |
| `best_practices.md` | 650 | Consolidated | Expression reuse, memory, testing, anti-patterns → `references/io_best_practices.md`; core best practices → SKILL.md Best Practices |
| `core_concepts.md` | 379 | Consolidated | Format selection, version notes → `references/io_best_practices.md`; data types, lazy/eager, parallelism → SKILL.md Key Concepts |
| `pandas_migration.md` | 418 | Migrated | → `references/pandas_migration.md` (expanded with window/string/datetime/missing data tables) |

### Intentional Omissions

- **Row iteration examples** (operations.md): Not documented as a positive capability; only referenced as anti-pattern in Best Practices
- **Expression fundamentals tutorial** (core_concepts.md): Expression syntax, contexts, and expansion are fully covered by SKILL.md Core API sections; a separate tutorial would duplicate
- **Detailed parallelization internals** (core_concepts.md): "What gets parallelized" list omitted — users only need the Best Practices guidance to stay in the expression API
- **Copy-on-write comparison** (core_concepts.md): Pandas 2.0+ copy-on-write details omitted — migration-focused, not Polars-centric

## Related Skills

- **zarr-python** — Chunked array storage; Polars can read/write Parquet that Zarr processes
- **matplotlib-scientific-plotting** — Visualization; convert to pandas with `.to_pandas()` for plotting
- **scikit-learn-machine-learning** — ML pipelines; use `.to_numpy()` or `.to_pandas()` for sklearn input

## References

- Polars User Guide: https://docs.pola.rs/
- Polars API Reference: https://docs.pola.rs/api/python/stable/reference/
- GitHub: https://github.com/pola-rs/polars
- Polars Cookbook: https://docs.pola.rs/user-guide/
