# Advanced Polars Operations

Operations and transformations beyond core select/filter/group_by/join covered in the main SKILL.md. Covers rolling windows, cumulative operations, struct/list manipulation, reshaping, sorting, renaming, and sampling.

## Rolling Window Operations

### Time-Based Rolling Windows

Roll over a temporal column with a duration-based window:

```python
import polars as pl
from datetime import date

df = pl.DataFrame({
    "date": pl.date_range(date(2023, 1, 1), date(2023, 1, 15), eager=True),
    "value": [10, 12, 15, 11, 13, 14, 16, 18, 12, 15, 17, 19, 20, 22, 21],
})

# 7-day rolling mean using rolling()
result = df.sort("date").rolling(index_column="date", period="7d").agg(
    pl.col("value").mean().alias("rolling_7d_mean"),
    pl.col("value").std().alias("rolling_7d_std"),
    pl.col("value").min().alias("rolling_7d_min"),
    pl.col("value").max().alias("rolling_7d_max"),
)
print(result.head(8))
# date       | rolling_7d_mean | rolling_7d_std | ...
# 2023-01-01 | 10.0            | null           | ...
# 2023-01-07 | 13.0            | 2.16           | ...
```

### Row-Based Rolling Windows

Fixed row-count windows (no temporal column needed):

```python
df = pl.DataFrame({
    "group": ["A"] * 6 + ["B"] * 6,
    "value": [10, 20, 30, 40, 50, 60, 5, 15, 25, 35, 45, 55],
})

# Rolling sum/mean over 3 rows, grouped
result = df.with_columns(
    rolling_sum_3=pl.col("value").rolling_sum(window_size=3).over("group"),
    rolling_mean_3=pl.col("value").rolling_mean(window_size=3).over("group"),
    rolling_max_3=pl.col("value").rolling_max(window_size=3).over("group"),
    rolling_min_3=pl.col("value").rolling_min(window_size=3).over("group"),
    rolling_std_3=pl.col("value").rolling_std(window_size=3).over("group"),
)
print(result)
# First 2 rows per group are null (insufficient window)
```

### Rolling with Custom Parameters

```python
# Center-aligned window and minimum periods
df = pl.DataFrame({"value": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]})
result = df.with_columns(
    # min_periods: require at least 2 values in window
    rolling_avg=pl.col("value").rolling_mean(window_size=5, min_periods=2),
    # Rolling variance
    rolling_var=pl.col("value").rolling_var(window_size=5),
    # Rolling median
    rolling_med=pl.col("value").rolling_median(window_size=5),
)
print(result)
```

## Cumulative Operations

Compute running totals, extremes, and products within groups:

```python
import polars as pl

df = pl.DataFrame({
    "group": ["A", "A", "A", "B", "B", "B"],
    "value": [10, 20, 30, 5, 15, 25],
    "flag": [True, False, True, True, True, False],
})

# Grouped cumulative operations
result = df.with_columns(
    cum_sum=pl.col("value").cum_sum().over("group"),
    cum_max=pl.col("value").cum_max().over("group"),
    cum_min=pl.col("value").cum_min().over("group"),
    cum_prod=pl.col("value").cum_prod().over("group"),
    cum_count=pl.col("value").cum_count().over("group"),
)
print(result)
# group | value | cum_sum | cum_max | cum_min | cum_prod | cum_count
# A     | 10    | 10      | 10      | 10      | 10       | 1
# A     | 20    | 30      | 20      | 10      | 200      | 2
# A     | 30    | 60      | 30      | 10      | 6000     | 3
# B     | 5     | 5       | 5       | 5       | 5        | 1
# B     | 15    | 20      | 15      | 5       | 75       | 2
# B     | 25    | 45      | 25      | 5       | 1875     | 3
```

### Cumulative with Reverse Order

```python
# Reverse cumulative (from bottom to top)
result = df.with_columns(
    reverse_cum_sum=pl.col("value").reverse().cum_sum().reverse().over("group"),
)
print(result)
```

## Shift and Lag/Lead Operations

Access previous or next row values for difference calculations and feature engineering:

```python
import polars as pl

df = pl.DataFrame({
    "user": ["A", "A", "A", "A", "B", "B", "B"],
    "day": [1, 2, 3, 4, 1, 2, 3],
    "spend": [100, 150, 120, 200, 50, 75, 60],
})

result = df.with_columns(
    # Previous value (lag 1)
    prev_spend=pl.col("spend").shift(1).over("user"),
    # Two-step lag
    prev2_spend=pl.col("spend").shift(2).over("user"),
    # Next value (lead 1)
    next_spend=pl.col("spend").shift(-1).over("user"),
    # Difference from previous
    spend_diff=pl.col("spend").diff().over("user"),
    # Percent change
    spend_pct_change=(
        (pl.col("spend") - pl.col("spend").shift(1))
        / pl.col("spend").shift(1)
    ).over("user"),
)
print(result)
# user | day | spend | prev_spend | prev2_spend | next_spend | spend_diff | spend_pct_change
# A    | 1   | 100   | null       | null        | 150        | null       | null
# A    | 2   | 150   | 100        | null        | 120        | 50         | 0.5
# A    | 3   | 120   | 150        | 100         | 200        | -30        | -0.2
# A    | 4   | 200   | 120        | 150         | null       | 80         | 0.667
```

### Fill Shifted Nulls

```python
# Fill boundary nulls from shift operations
result = df.with_columns(
    prev_spend=pl.col("spend").shift(1).fill_null(0).over("user"),
    next_spend=pl.col("spend").shift(-1).fill_null(
        pl.col("spend")  # fill with current value at boundary
    ).over("user"),
)
```

## Struct Operations

Create, access, and unnest composite column types:

```python
import polars as pl

df = pl.DataFrame({
    "name": ["Alice", "Bob", "Charlie"],
    "street": ["123 Main St", "456 Oak Ave", "789 Pine Rd"],
    "city": ["Boston", "Denver", "Seattle"],
    "zip": ["02101", "80201", "98101"],
})

# Create struct column from multiple columns
with_struct = df.with_columns(
    address=pl.struct("street", "city", "zip")
)
print(with_struct.schema)
# {'name': Utf8, 'street': Utf8, 'city': Utf8, 'zip': Utf8,
#  'address': Struct({'street': Utf8, 'city': Utf8, 'zip': Utf8})}

# Access individual struct fields
result = with_struct.select(
    "name",
    city=pl.col("address").struct.field("city"),
    zip_code=pl.col("address").struct.field("zip"),
)
print(result)

# Unnest struct back to flat columns
flat = with_struct.select("name", "address").unnest("address")
print(flat.columns)  # ['name', 'street', 'city', 'zip']
```

### Struct with Nested Data

```python
# Create from aggregation (group_by produces struct-like results)
orders = pl.DataFrame({
    "customer": ["A", "A", "B", "B", "B"],
    "amount": [100, 200, 50, 75, 125],
})

# Aggregation into struct
summary = orders.group_by("customer").agg(
    stats=pl.struct(
        total=pl.col("amount").sum(),
        avg=pl.col("amount").mean(),
        count=pl.len(),
    )
)
# Unnest to access
print(summary.unnest("stats"))
```

## List Column Operations

Advanced operations on list-typed columns:

```python
import polars as pl

df = pl.DataFrame({
    "id": [1, 2, 3],
    "scores": [[85, 92, 78], [90, 88], [95, 100, 97, 91]],
    "tags": [["python", "data"], ["rust", "polars", "data"], ["ml"]],
})

# List statistics
result = df.with_columns(
    n_scores=pl.col("scores").list.len(),
    mean_score=pl.col("scores").list.mean(),
    max_score=pl.col("scores").list.max(),
    min_score=pl.col("scores").list.min(),
    first_score=pl.col("scores").list.first(),
    last_score=pl.col("scores").list.last(),
    sorted_scores=pl.col("scores").list.sort(),
    unique_tags=pl.col("tags").list.unique(),
)
print(result.select("id", "n_scores", "mean_score", "max_score"))

# Get element by index
result = df.with_columns(
    second_score=pl.col("scores").list.get(1),
)

# Slice list
result = df.with_columns(
    top_2=pl.col("scores").list.slice(0, 2),
)

# Check membership
result = df.with_columns(
    has_python=pl.col("tags").list.contains("python"),
)
print(result.select("id", "has_python"))
```

### List Evaluation and Filtering

```python
# Filter elements within lists
result = df.with_columns(
    high_scores=pl.col("scores").list.eval(
        pl.element().filter(pl.element() >= 90)
    ),
)
print(result.select("id", "scores", "high_scores"))
# id | scores           | high_scores
# 1  | [85, 92, 78]     | [92]
# 2  | [90, 88]         | [90]
# 3  | [95, 100, 97, 91]| [95, 100, 97, 91]

# Explode lists to individual rows
exploded = df.select("id", "tags").explode("tags")
print(exploded)
# id | tags
# 1  | python
# 1  | data
# 2  | rust
# 2  | polars
# 2  | data
# 3  | ml
```

## Unique and Duplicate Operations

```python
import polars as pl

df = pl.DataFrame({
    "id": [1, 2, 2, 3, 3, 3],
    "name": ["Alice", "Bob", "Bob", "Charlie", "Charlie", "Charlie"],
    "value": [10, 20, 21, 30, 31, 32],
})

# Unique rows (all columns)
print(df.unique().shape)  # (6, 3) — all rows are unique across all columns

# Unique on subset (keep first or last occurrence)
first_per_id = df.unique(subset=["id"], keep="first")
print(first_per_id)
# id | name    | value
# 1  | Alice   | 10
# 2  | Bob     | 20
# 3  | Charlie | 30

last_per_id = df.unique(subset=["id"], keep="last")
print(last_per_id)
# id | name    | value
# 1  | Alice   | 10
# 2  | Bob     | 21
# 3  | Charlie | 32

# Identify duplicates
result = df.with_columns(
    is_dup=pl.col("id").is_duplicated(),
    is_first_occurrence=pl.col("id").is_first_distinct(),
)
print(result)

# Count duplicates per value
dup_counts = (
    df.group_by("id")
    .agg(pl.len().alias("count"))
    .filter(pl.col("count") > 1)
)
print(dup_counts)
# id | count
# 2  | 2
# 3  | 3

# N unique values
print(df["id"].n_unique())  # 3
```

## Advanced Sorting

```python
import polars as pl

df = pl.DataFrame({
    "name": ["Charlie", "Alice", "Bob", "Diana", None],
    "score": [88, 95, None, 88, 92],
    "dept": ["Eng", "Sales", "Eng", "Sales", "Eng"],
})

# Nulls placement control
sorted_nulls_last = df.sort("score", nulls_last=True)
sorted_nulls_first = df.sort("score", nulls_last=False)

# Sort by expression
by_name_length = df.sort(pl.col("name").str.len_chars(), nulls_last=True)
print(by_name_length)

# Mixed ascending/descending across columns
mixed = df.sort(
    ["dept", "score"],
    descending=[False, True],  # dept ascending, score descending
    nulls_last=True,
)
print(mixed)
# dept  | name    | score
# Eng   | null    | 92
# Eng   | Charlie | 88
# Eng   | Bob     | null
# Sales | Alice   | 95
# Sales | Diana   | 88

# Sort by multiple expressions
result = df.sort(
    pl.col("dept"),
    pl.col("score").fill_null(0),  # treat null as 0 for sort order
    descending=[False, True],
)
```

### Top-N per Group

```python
# Get top 2 scores per department
top_per_dept = (
    df.filter(pl.col("score").is_not_null())
    .sort("score", descending=True)
    .group_by("dept")
    .head(2)
)
print(top_per_dept)
```

## Column Renaming

```python
import polars as pl

df = pl.DataFrame({
    "First Name": ["Alice", "Bob"],
    "Last Name": ["Smith", "Jones"],
    "Age": [25, 30],
})

# Rename specific columns with dict
renamed = df.rename({"First Name": "first_name", "Last Name": "last_name"})
print(renamed.columns)  # ['first_name', 'last_name', 'Age']

# Batch rename with name expressions
suffixed = df.select(pl.all().name.suffix("_raw"))
print(suffixed.columns)  # ['First Name_raw', 'Last Name_raw', 'Age_raw']

prefixed = df.select(pl.all().name.prefix("col_"))
print(prefixed.columns)  # ['col_First Name', 'col_Last Name', 'col_Age']

# Rename to lowercase with custom mapping
lowered = df.select(pl.all().name.to_lowercase())
print(lowered.columns)  # ['first name', 'last name', 'age']

# Programmatic rename (replace spaces with underscores)
clean = df.rename({c: c.lower().replace(" ", "_") for c in df.columns})
print(clean.columns)  # ['first_name', 'last_name', 'age']
```

## Sampling

```python
import polars as pl

df = pl.DataFrame({
    "id": range(1000),
    "value": [i * 1.5 for i in range(1000)],
})

# Sample fixed number of rows
sample_n = df.sample(n=10, seed=42)
print(sample_n.shape)  # (10, 2)

# Sample fraction of rows
sample_frac = df.sample(fraction=0.05, seed=42)
print(sample_frac.shape)  # (50, 2)

# Sample with replacement (bootstrap)
bootstrap = df.sample(n=1000, with_replacement=True, seed=42)
print(bootstrap.shape)  # (1000, 2) — may have duplicates

# Shuffle all rows
shuffled = df.sample(fraction=1.0, seed=42, shuffle=True)
```

## Transpose

Swap rows and columns:

```python
import polars as pl

df = pl.DataFrame({
    "metric": ["revenue", "cost", "profit"],
    "Q1": [1000, 600, 400],
    "Q2": [1200, 700, 500],
    "Q3": [1100, 650, 450],
})

# Transpose with header column
transposed = df.transpose(
    include_header=True,
    header_name="quarter",
    column_names="metric",
)
print(transposed)
# quarter | revenue | cost | profit
# Q1      | 1000    | 600  | 400
# Q2      | 1200    | 700  | 500
# Q3      | 1100    | 650  | 450
```

## Advanced Reshaping Patterns

### Wide to Long to Wide

```python
import polars as pl

wide = pl.DataFrame({
    "id": [1, 2, 3],
    "score_math": [90, 85, 92],
    "score_eng": [88, 91, 87],
    "score_sci": [95, 82, 89],
})

# Wide → Long
long = wide.unpivot(
    index="id",
    on=["score_math", "score_eng", "score_sci"],
    variable_name="subject",
    value_name="score",
)
# Clean up subject names
long = long.with_columns(
    pl.col("subject").str.replace("score_", "")
)
print(long)

# Long → Wide (back to original shape)
back_to_wide = long.pivot(
    values="score",
    index="id",
    columns="subject",
)
print(back_to_wide)
```

### Nested JSON to Flat Table

```python
import polars as pl

# Nested data (e.g., from JSON API response)
df = pl.DataFrame({
    "user_id": [1, 2],
    "purchases": [
        [{"item": "laptop", "qty": 1, "price": 999},
         {"item": "mouse", "qty": 2, "price": 25}],
        [{"item": "keyboard", "qty": 1, "price": 75}],
    ]
})

# Explode list → unnest struct
flat = df.explode("purchases").unnest("purchases")
print(flat)
# user_id | item     | qty | price
# 1       | laptop   | 1   | 999
# 1       | mouse    | 2   | 25
# 2       | keyboard | 1   | 75

# Compute totals
totals = flat.with_columns(
    line_total=(pl.col("qty") * pl.col("price"))
).group_by("user_id").agg(
    pl.col("line_total").sum().alias("order_total"),
    pl.col("item").count().alias("n_items"),
)
print(totals)
```

### Multi-Level Unpivot

Extract structure from column names during reshaping:

```python
import polars as pl

df = pl.DataFrame({
    "id": [1, 2],
    "Q1_revenue": [100, 200],
    "Q1_cost": [60, 120],
    "Q2_revenue": [150, 250],
    "Q2_cost": [80, 140],
})

# Unpivot all Q columns
long = df.unpivot(
    index="id",
    on=["Q1_revenue", "Q1_cost", "Q2_revenue", "Q2_cost"],
)

# Extract quarter and metric from variable names
result = (
    long.with_columns(
        quarter=pl.col("variable").str.extract(r"(Q\d)", 1),
        metric=pl.col("variable").str.extract(r"Q\d_(.*)", 1),
    )
    .drop("variable")
    .pivot(values="value", index=["id", "quarter"], columns="metric")
)
print(result)
# id | quarter | revenue | cost
# 1  | Q1      | 100     | 60
# 1  | Q2      | 150     | 80
# 2  | Q1      | 200     | 120
# 2  | Q2      | 250     | 140
```

### Horizontal Concatenation

```python
import polars as pl

df1 = pl.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})
df2 = pl.DataFrame({"c": [7, 8, 9], "d": [10, 11, 12]})

# Stack columns side by side (requires same row count)
result = pl.concat([df1, df2], how="horizontal")
print(result.columns)  # ['a', 'b', 'c', 'd']
print(result.shape)     # (3, 4)
```

---

## Condensation Note

Consolidated from 2 original files:
- **operations.md** (603 lines): Retained rolling windows, cumulative ops, shift/lag, struct ops, list ops, unique/duplicate, sorting, renaming, sampling. Omitted: basic selection/filtering/groupby/aggregation/window/string/date operations (covered in main SKILL.md Core API sections 1, 2, 6), basic conditional when/then/otherwise (SKILL.md section 6).
- **transformations.md** (550 lines): Retained transpose, horizontal concat, advanced reshaping (wide-long-wide, nested-to-flat, multi-level unpivot). Omitted: basic joins (SKILL.md section 3), basic vertical/diagonal concat (SKILL.md section 4), basic pivot/unpivot/explode (SKILL.md section 4), asof joins (SKILL.md section 3), join performance tips (SKILL.md Best Practices).

Combined source: 1,153 lines. This file: ~390 lines. Standalone retention: ~34%. Combined coverage with SKILL.md: operations.md content relocated to SKILL.md sections 1-6 accounts for ~200 lines; transformations.md content in SKILL.md sections 3-4 accounts for ~80 lines. Combined coverage: (390 + 280) / 1,153 = ~58%.
