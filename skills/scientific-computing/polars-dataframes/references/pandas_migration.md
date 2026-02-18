# Pandas to Polars Migration Guide

## Conceptual Differences

| Aspect | Pandas | Polars |
|--------|--------|--------|
| Index | Row labels (`.loc`, `.iloc`) | No index — integer position only |
| Type system | Flexible, silent coercion | Strict, explicit `.cast()` |
| Evaluation | Always eager | Eager + Lazy (optimized) |
| Parallelism | Single-threaded (most ops) | Multi-threaded by default |
| String type | `object` | `Utf8` (Arrow-native) |
| Null handling | `NaN` for float, various for others | Consistent `null` across all types |
| Memory | Copy-on-write (pandas 2.0+) | Zero-copy where possible (Arrow) |
| Mutability | In-place mutations (`inplace=True`) | Immutable — always returns new DataFrame |

## Operation Mapping

### Selection & Filtering

| Operation | Pandas | Polars |
|-----------|--------|--------|
| Select column | `df["col"]` or `df.col` | `df.select("col")` |
| Select multiple | `df[["a", "b"]]` | `df.select("a", "b")` |
| Select by dtype | `df.select_dtypes(include="number")` | `df.select(cs.numeric())` |
| Select by position | `df.iloc[:, 0:3]` | `df.select(pl.col(df.columns[0:3]))` |
| Filter rows | `df[df["col"] > 10]` | `df.filter(pl.col("col") > 10)` |
| Filter multiple | `df[(df.a > 1) & (df.b < 5)]` | `df.filter(pl.col("a") > 1, pl.col("b") < 5)` |
| Query method | `df.query("age > 25")` | `df.filter(pl.col("age") > 25)` |
| isin | `df[df["city"].isin(["NY", "LA"])]` | `df.filter(pl.col("city").is_in(["NY", "LA"]))` |
| isna/notna | `df[df["v"].isna()]` | `df.filter(pl.col("v").is_null())` |
| Head/tail | `df.head(10)` | `df.head(10)` |
| Sample | `df.sample(n=100)` | `df.sample(n=100)` |

### Column Operations

| Operation | Pandas | Polars |
|-----------|--------|--------|
| Add column | `df["new"] = ...` or `df.assign(new=...)` | `df.with_columns(new=...)` |
| Rename | `df.rename(columns={"a": "b"})` | `df.rename({"a": "b"})` |
| Drop column | `df.drop(columns=["a"])` | `df.drop("a")` |
| Change type | `df["a"].astype(int)` | `df.with_columns(pl.col("a").cast(pl.Int64))` |
| Apply function | `df["a"].apply(func)` | `df.with_columns(pl.col("a").map_elements(func, return_dtype=...))` |
| Conditional | `np.where(cond, a, b)` | `pl.when(cond).then(a).otherwise(b)` |

### Aggregation

| Operation | Pandas | Polars |
|-----------|--------|--------|
| Group + agg | `df.groupby("g").agg({"v": "sum"})` | `df.group_by("g").agg(pl.col("v").sum())` |
| Multiple aggs | `df.groupby("g").agg({"v": ["sum", "mean"]})` | `df.group_by("g").agg(pl.col("v").sum().alias("sum"), pl.col("v").mean().alias("mean"))` |
| Transform | `df.groupby("g")["v"].transform("mean")` | `df.with_columns(pl.col("v").mean().over("g"))` |
| Value counts | `df["a"].value_counts()` | `df["a"].value_counts()` |
| Describe | `df.describe()` | `df.describe()` |
| Group size | `df.groupby("g").size()` | `df.group_by("g").agg(pl.len())` |
| Nunique | `df.groupby("g")["v"].nunique()` | `df.group_by("g").agg(pl.col("v").n_unique())` |

### Window Functions

| Operation | Pandas | Polars |
|-----------|--------|--------|
| Transform | `df.groupby("g")["v"].transform("mean")` | `df.with_columns(pl.col("v").mean().over("g"))` |
| Rank | `df.groupby("g")["v"].rank()` | `df.with_columns(pl.col("v").rank().over("g"))` |
| Shift/lag | `df.groupby("g")["v"].shift(1)` | `df.with_columns(pl.col("v").shift(1).over("g"))` |
| Cumsum | `df.groupby("g")["v"].cumsum()` | `df.with_columns(pl.col("v").cum_sum().over("g"))` |
| Rolling mean | `df.rolling(7).mean()` | `df.with_columns(pl.col("v").rolling_mean(7))` |

### Joins & Reshaping

| Operation | Pandas | Polars |
|-----------|--------|--------|
| Merge | `pd.merge(df1, df2, on="id")` | `df1.join(df2, on="id")` |
| Left merge | `pd.merge(df1, df2, on="id", how="left")` | `df1.join(df2, on="id", how="left")` |
| Different keys | `pd.merge(df1, df2, left_on="a", right_on="b")` | `df1.join(df2, left_on="a", right_on="b")` |
| Concat rows | `pd.concat([df1, df2])` | `pl.concat([df1, df2])` |
| Concat cols | `pd.concat([df1, df2], axis=1)` | `pl.concat([df1, df2], how="horizontal")` |
| Pivot | `df.pivot_table(values, index, columns)` | `df.pivot(values, index, columns)` |
| Melt | `df.melt(id_vars, value_vars)` | `df.unpivot(index, on)` |

### String Operations

| Operation | Pandas | Polars |
|-----------|--------|--------|
| Uppercase | `df["c"].str.upper()` | `pl.col("c").str.to_uppercase()` |
| Lowercase | `df["c"].str.lower()` | `pl.col("c").str.to_lowercase()` |
| Contains | `df["c"].str.contains("pat")` | `pl.col("c").str.contains("pat")` |
| Replace | `df["c"].str.replace("a", "b")` | `pl.col("c").str.replace("a", "b")` |
| Split | `df["c"].str.split(" ")` | `pl.col("c").str.split(" ")` |
| Length | `df["c"].str.len()` | `pl.col("c").str.len_chars()` |
| Strip | `df["c"].str.strip()` | `pl.col("c").str.strip_chars()` |

### Datetime Operations

| Operation | Pandas | Polars |
|-----------|--------|--------|
| Parse dates | `pd.to_datetime(df["c"])` | `pl.col("c").str.strptime(pl.Date, "%Y-%m-%d")` |
| Year | `df["d"].dt.year` | `pl.col("d").dt.year()` |
| Month | `df["d"].dt.month` | `pl.col("d").dt.month()` |
| Day | `df["d"].dt.day` | `pl.col("d").dt.day()` |
| Weekday | `df["d"].dt.dayofweek` | `pl.col("d").dt.weekday()` |
| Resample | `df.resample("M").sum()` | `df.group_by_dynamic("d", every="1mo").agg(...)` |

### Missing Data

| Operation | Pandas | Polars |
|-----------|--------|--------|
| Drop nulls | `df.dropna()` | `df.drop_nulls()` |
| Drop on subset | `df.dropna(subset=["a"])` | `df.drop_nulls(subset=["a"])` |
| Fill constant | `df.fillna(0)` | `df.fill_null(0)` |
| Forward fill | `df.fillna(method="ffill")` | `df.with_columns(pl.col("c").fill_null(strategy="forward"))` |
| Backward fill | `df.fillna(method="bfill")` | `df.with_columns(pl.col("c").fill_null(strategy="backward"))` |
| Check null | `df["c"].isna()` | `pl.col("c").is_null()` |
| Coalesce | `df["a"].combine_first(df["b"])` | `pl.coalesce("a", "b")` |

### I/O

| Operation | Pandas | Polars |
|-----------|--------|--------|
| Read CSV | `pd.read_csv("f.csv")` | `pl.read_csv("f.csv")` |
| Lazy read CSV | — | `pl.scan_csv("f.csv")` |
| Read Parquet | `pd.read_parquet("f.pq")` | `pl.read_parquet("f.pq")` |
| Lazy Parquet | — | `pl.scan_parquet("f.pq")` |
| Read SQL | `pd.read_sql(query, conn)` | `pl.read_database_uri(query, uri)` |
| Read Excel | `pd.read_excel("f.xlsx")` | `pl.read_excel("f.xlsx")` |
| Write CSV | `df.to_csv("f.csv")` | `df.write_csv("f.csv")` |
| Write Parquet | `df.to_parquet("f.pq")` | `df.write_parquet("f.pq")` |

## Interoperability

```python
import polars as pl
import pandas as pd

# Pandas → Polars
pd_df = pd.DataFrame({"a": [1, 2, 3]})
pl_df = pl.from_pandas(pd_df)

# Polars → Pandas
pd_df = pl_df.to_pandas()

# Polars → NumPy
arr = pl_df.to_numpy()

# Polars → Arrow (zero-copy)
arrow_table = pl_df.to_arrow()

# Arrow → Polars (zero-copy when possible)
pl_df = pl.from_arrow(arrow_table)
```

## Common Migration Patterns

### Pattern 1: Chained Operations

```python
# Pandas
result = (df
    .assign(new_col=lambda x: x["old_col"] * 2)
    .query("new_col > 10")
    .groupby("category")
    .agg({"value": "sum"})
    .reset_index()
)

# Polars (no reset_index needed — no index)
result = (df
    .with_columns(new_col=pl.col("old_col") * 2)
    .filter(pl.col("new_col") > 10)
    .group_by("category")
    .agg(pl.col("value").sum())
)
```

### Pattern 2: Conditional Column

```python
# Pandas
df["cat"] = np.where(
    df["v"] > 100, "high",
    np.where(df["v"] > 50, "medium", "low")
)

# Polars
df = df.with_columns(
    cat=pl.when(pl.col("v") > 100).then(pl.lit("high"))
       .when(pl.col("v") > 50).then(pl.lit("medium"))
       .otherwise(pl.lit("low"))
)
```

### Pattern 3: Group Transform

```python
# Pandas
df["group_mean"] = df.groupby("cat")["value"].transform("mean")

# Polars
df = df.with_columns(
    group_mean=pl.col("value").mean().over("cat")
)
```

### Pattern 4: Multiple Aggregations

```python
# Pandas
result = df.groupby("cat").agg({
    "value": ["mean", "sum", "count"],
    "price": ["min", "max"]
})

# Polars (explicit naming — no multi-index)
result = df.group_by("cat").agg(
    pl.col("value").mean().alias("value_mean"),
    pl.col("value").sum().alias("value_sum"),
    pl.col("value").count().alias("value_count"),
    pl.col("price").min().alias("price_min"),
    pl.col("price").max().alias("price_max"),
)
```

## Performance Patterns

### Pandas (sequential)
```python
# Each assign runs sequentially; lambda sees previous results
result = (
    df.assign(col_a=lambda d: d["value"] * 10)
      .assign(col_b=lambda d: d["value"] * 100)
)
```

### Polars (parallel)
```python
# All expressions computed simultaneously
result = df.with_columns(
    col_a=pl.col("value") * 10,
    col_b=pl.col("value") * 100,
)
```

## Common Migration Pitfalls

1. **No index**: `df.loc["2023-01"]` does not exist. Filter instead: `df.filter(pl.col("date") == "2023-01")`
2. **No inplace**: Polars always returns new DataFrames. No `inplace=True` parameter
3. **No `NaN` for non-float**: Polars uses `null` consistently. Check with `.is_null()` not `isna()`
4. **Column names are strings**: No integer column access; always use string names
5. **Chained indexing doesn't work**: `df["a"]["b"]` does not select two columns. Use `df.select("a", "b")`
6. **No MultiIndex**: Polars has no hierarchical indexing. Use `group_by()` with multiple keys and explicit `.alias()` naming
7. **groupby vs group_by**: Note the underscore — `df.group_by()` not `df.groupby()`
8. **melt is now unpivot**: `df.melt()` is renamed to `df.unpivot()` in Polars
9. **apply breaks parallelism**: `map_elements()` runs Python; rewrite with native expressions wherever possible
10. **Date parsing is explicit**: No automatic date detection. Use `str.strptime(pl.Date, fmt)` or `str.to_date()`

## Migration Checklist

1. Remove all index operations (`.set_index()`, `.reset_index()`, `.loc`, `.iloc` with labels)
2. Replace `df["col"] = ...` with `df.with_columns(...)`
3. Replace `.apply()` / `.map()` with native expressions
4. Change `.groupby().transform()` to `.over()` window functions
5. Update string methods: `.str.upper()` → `.str.to_uppercase()`, `.str.strip()` → `.str.strip_chars()`
6. Add explicit `.cast()` for type conversions
7. Switch to `scan_*()` for large file reads (lazy mode)
8. Update aggregation syntax to explicit `.alias()` naming
9. Replace `.melt()` with `.unpivot()`
10. Remove all `inplace=True` arguments

## When to Stay with Pandas

- Working with complex time-series requiring `.resample()` with custom logic
- Extensive ecosystem dependency (libraries accepting only pandas DataFrames)
- Data is small (<100 MB) and performance is not a concern
- Advanced pandas features without Polars equivalents (e.g., `MultiIndex` operations)

## When to Switch to Polars

- Performance-critical pipelines (10-100x speedup typical)
- Datasets exceeding 1 GB
- Need lazy evaluation and query optimization
- Want better type safety and consistent null handling
- Starting a new project (no migration debt)
- Need parallel execution without external tools (Dask)

---

## Condensation Note

Condensed from original pandas_migration.md: 418 lines. Retained: conceptual differences table, all operation mapping tables (selection, column ops, aggregation, joins/reshaping, I/O), interoperability code, performance patterns, migration patterns (chained ops, conditional, group transform, multiple aggs), migration pitfalls, migration checklist, when to stay/switch guidance. Expanded: added window functions table, string operations table, datetime operations table, missing data table (all from original operations.md), added select-by-position and query-method rows, added migration pitfalls 6-10, added resample equivalent. Omitted: anti-pattern code examples for row iteration and sequential pipe (covered in io_best_practices.md Performance Anti-Patterns section), compatibility layer detail (kept as concise Interoperability section).
