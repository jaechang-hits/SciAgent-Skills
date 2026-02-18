---
name: flowio-flow-cytometry
description: "Parse and create FCS (Flow Cytometry Standard) files v2.0-3.1. Read event data as NumPy arrays, extract channel metadata, handle multi-dataset files, export to CSV/FCS. For advanced gating and compensation use FlowKit."
license: BSD-3-Clause
---

# FlowIO — Flow Cytometry File Handler

## Overview

FlowIO is a lightweight Python library for reading and writing Flow Cytometry Standard (FCS) files. It parses FCS metadata, extracts event data as NumPy arrays, and creates new FCS files. Supports FCS versions 2.0, 3.0, and 3.1. Minimal dependencies — ideal for data pipelines and preprocessing before advanced analysis.

## When to Use

- Parsing FCS files to extract event data as NumPy arrays
- Reading channel metadata (names, ranges, types) from FCS files
- Converting flow cytometry data to pandas DataFrames or CSV
- Creating new FCS files from NumPy arrays or processed data
- Handling multi-dataset FCS files (separating combined datasets)
- Batch processing directories of FCS files
- Preprocessing flow cytometry data before downstream analysis
- For **compensation, gating, and FlowJo workspace support**, use FlowKit instead
- For **advanced cytometry visualization** (density plots, gating plots), use matplotlib or plotly

## Prerequisites

```bash
pip install flowio numpy pandas
```

Requires Python 3.9+. No compiled dependencies — installs on any platform.

## Quick Start

```python
from flowio import FlowData

flow = FlowData("experiment.fcs")
print(f"Events: {flow.event_count}, Channels: {flow.channel_count}")
print(f"Channels: {flow.pnn_labels}")

events = flow.as_array()  # Shape: (n_events, n_channels)
print(f"Data shape: {events.shape}")
```

## Core API

### 1. Reading FCS Files

The `FlowData` class is the primary interface for reading FCS files.

```python
from flowio import FlowData

# Standard reading
flow = FlowData("sample.fcs")
print(f"Version: {flow.version}")          # '3.0', '3.1', etc.
print(f"Events: {flow.event_count}")
print(f"Channels: {flow.channel_count}")

# Event data
events = flow.as_array()                   # Preprocessed (gain, log scaling)
raw = flow.as_array(preprocess=False)      # Raw values
print(f"Shape: {events.shape}")            # (n_events, n_channels)

# Memory-efficient: metadata only (skip DATA segment)
flow_meta = FlowData("sample.fcs", only_text=True)
print(f"Instrument: {flow_meta.text.get('$CYT', 'Unknown')}")

# Handle problematic files
flow = FlowData("bad.fcs", ignore_offset_discrepancy=True)
flow = FlowData("bad.fcs", use_header_offsets=True)

# Exclude null channels
flow = FlowData("sample.fcs", null_channel_list=["Time", "Null"])
```

### 2. Channel Metadata

Extract channel names, types, and ranges from FCS files.

```python
flow = FlowData("sample.fcs")

# Channel names
pnn = flow.pnn_labels   # Short names: ['FSC-A', 'SSC-A', 'FL1-A', ...]
pns = flow.pns_labels   # Descriptive: ['Forward Scatter', 'Side Scatter', 'FITC', ...]
pnr = flow.pnr_values   # Range/max values per channel

# Channel type indices
scatter_idx = flow.scatter_indices   # [0, 1] — FSC, SSC
fluoro_idx = flow.fluoro_indices     # [2, 3, 4] — fluorescence channels
time_idx = flow.time_index           # Time channel index (or None)

# Access by type
events = flow.as_array()
scatter_data = events[:, scatter_idx]
fluoro_data = events[:, fluoro_idx]

# Full metadata (TEXT segment dictionary)
text = flow.text
print(f"Date: {text.get('$DATE', 'N/A')}")
print(f"Instrument: {text.get('$CYT', 'N/A')}")
```

### 3. Creating FCS Files

Generate new FCS files from NumPy arrays.

```python
import numpy as np
from flowio import create_fcs

# Basic creation
events = np.random.rand(10000, 5) * 1000
channels = ["FSC-A", "SSC-A", "FL1-A", "FL2-A", "Time"]
create_fcs("output.fcs", events, channels)

# With descriptive names and metadata
create_fcs(
    "output.fcs",
    events,
    channels,
    opt_channel_names=["Forward Scatter", "Side Scatter", "FITC", "PE", "Time"],
    metadata={"$SRC": "Python pipeline", "$DATE": "17-FEB-2026", "$CYT": "Synthetic"},
)
# Output: FCS 3.1, single-precision float
```

### 4. Multi-Dataset FCS Files

Handle FCS files containing multiple datasets.

```python
from flowio import FlowData, read_multiple_data_sets, MultipleDataSetsError

# Detect multi-dataset files
try:
    flow = FlowData("sample.fcs")
except MultipleDataSetsError:
    datasets = read_multiple_data_sets("sample.fcs")
    print(f"Found {len(datasets)} datasets")
    for i, ds in enumerate(datasets):
        print(f"Dataset {i}: {ds.event_count} events, {ds.channel_count} channels")
        events = ds.as_array()

# Read specific dataset by offset
first = FlowData("multi.fcs", nextdata_offset=0)
next_offset = int(first.text.get("$NEXTDATA", "0"))
if next_offset > 0:
    second = FlowData("multi.fcs", nextdata_offset=next_offset)
```

### 5. Modifying and Re-Exporting

Read, modify, and save FCS data.

```python
from flowio import FlowData, create_fcs

# Read original
flow = FlowData("original.fcs")
events = flow.as_array(preprocess=False)  # Use raw for modification

# Filter events (e.g., threshold on FSC)
mask = events[:, 0] > 500
filtered = events[mask]
print(f"Before: {len(events)}, After: {len(filtered)}")

# Save filtered data as new FCS
create_fcs(
    "filtered.fcs",
    filtered,
    flow.pnn_labels,
    opt_channel_names=flow.pns_labels,
    metadata={**flow.text, "$SRC": "Filtered"},
)

# Or write with updated metadata (no event modification)
flow.write_fcs("updated.fcs", metadata={"$SRC": "Updated"})
```

## Key Concepts

### FCS File Structure

FCS files consist of four segments:

| Segment | Content | FlowData attribute |
|---------|---------|-------------------|
| HEADER | Version, byte offsets | `flow.header` |
| TEXT | Key-value metadata (`$DATE`, `$CYT`, channel names) | `flow.text` |
| DATA | Event data (binary/float) | `flow.events` (bytes), `flow.as_array()` |
| ANALYSIS | Optional processed results | `flow.analysis` |

### Preprocessing (as_array)

When `preprocess=True` (default), FlowIO applies:
1. **Gain scaling**: Multiply by PnG gain values
2. **Log transform**: Apply PnE exponential transform if present (`value = a × 10^(b × raw)`)
3. **Time scaling**: Convert time channel to proper units

Use `preprocess=False` when you need raw values for modification or custom transforms.

## Common Workflows

### Workflow: Batch FCS Summary

```python
from pathlib import Path
from flowio import FlowData
import pandas as pd

fcs_files = list(Path("data/").glob("*.fcs"))
summaries = []
for f in fcs_files:
    try:
        flow = FlowData(str(f), only_text=True)
        summaries.append({
            "file": f.name, "version": flow.version,
            "events": flow.event_count, "channels": flow.channel_count,
            "date": flow.text.get("$DATE", "N/A"),
        })
    except Exception as e:
        print(f"Error: {f.name}: {e}")

df = pd.DataFrame(summaries)
print(df)
```

### Workflow: FCS to DataFrame with Channel Statistics

```python
from flowio import FlowData
import pandas as pd
import numpy as np

flow = FlowData("sample.fcs")
df = pd.DataFrame(flow.as_array(), columns=flow.pnn_labels)

# Per-channel statistics
for col in df.columns:
    print(f"{col}: mean={df[col].mean():.1f}, median={df[col].median():.1f}, std={df[col].std():.1f}")

# Export
df.to_csv("output.csv", index=False)
print(f"Exported {len(df)} events, {len(df.columns)} channels")
```

## Key Parameters

| Parameter | Function | Default | Options | Effect |
|-----------|----------|---------|---------|--------|
| `preprocess` | `as_array()` | `True` | `True`/`False` | Apply gain/log scaling |
| `only_text` | `FlowData()` | `False` | `True`/`False` | Skip DATA segment (metadata only) |
| `ignore_offset_discrepancy` | `FlowData()` | `False` | `True`/`False` | Tolerate HEADER/TEXT offset mismatch |
| `use_header_offsets` | `FlowData()` | `False` | `True`/`False` | Prefer HEADER over TEXT offsets |
| `ignore_offset_error` | `FlowData()` | `False` | `True`/`False` | Skip all offset validation |
| `null_channel_list` | `FlowData()` | `None` | List of names | Exclude channels during parsing |
| `nextdata_offset` | `FlowData()` | `None` | byte offset | Read specific dataset in multi-dataset files |
| `opt_channel_names` | `create_fcs()` | `None` | List of names | Descriptive channel names (PnS) |
| `metadata` | `create_fcs()` | `None` | Dict | Custom TEXT segment key-value pairs |

## Best Practices

1. **Use `only_text=True` for metadata scanning**: When processing many files, skip DATA segment parsing for 10-100x speedup.

2. **Use `preprocess=False` for data modification**: Always work with raw values when filtering/modifying events, then re-export. Preprocessing is irreversible.

3. **Anti-pattern — modifying `flow.events` directly**: FlowIO does not support in-place event modification. Extract with `as_array()`, modify, then `create_fcs()` to save.

4. **Preserve metadata on re-export**: Pass `flow.text` as metadata to `create_fcs()` to retain original acquisition info.

5. **Check for multi-dataset files**: Catch `MultipleDataSetsError` and use `read_multiple_data_sets()` — some instruments write multiple acquisitions into one file.

## Common Recipes

### Recipe: Extract Fluorescence Channels Only

```python
from flowio import FlowData
import numpy as np

flow = FlowData("sample.fcs")
events = flow.as_array()
fluoro = events[:, flow.fluoro_indices]
names = [flow.pnn_labels[i] for i in flow.fluoro_indices]
print(f"Fluorescence channels: {names}, shape: {fluoro.shape}")
```

### Recipe: File Inspection Report

```python
from flowio import FlowData

flow = FlowData("unknown.fcs")
print(f"Version: {flow.version} | Events: {flow.event_count:,} | Channels: {flow.channel_count}")
for i, (pnn, pns) in enumerate(zip(flow.pnn_labels, flow.pns_labels)):
    ctype = "scatter" if i in flow.scatter_indices else "fluoro" if i in flow.fluoro_indices else "time" if i == flow.time_index else "other"
    print(f"  [{i}] {pnn:10s} | {pns:30s} | {ctype}")
for key in ["$DATE", "$CYT", "$INST", "$SRC"]:
    print(f"  {key}: {flow.text.get(key, 'N/A')}")
```

### Recipe: Normalize Events to [0, 1] Range

When to use: Prepare fluorescence channels for machine learning or cross-sample comparison.

```python
from flowio import FlowData
import numpy as np

flow = FlowData("sample.fcs")
events = flow.as_array()

# Normalize each fluorescence channel to [0, 1]
fluoro_idx = flow.fluoro_indices
fluoro = events[:, fluoro_idx]
pnr = np.array(flow.pnr_values)[fluoro_idx]  # Per-channel max range
normalized = fluoro / pnr
print(f"Normalized shape: {normalized.shape}, range: [{normalized.min():.3f}, {normalized.max():.3f}]")
```

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| `DataOffsetDiscrepancyError` | HEADER/TEXT offset mismatch | Use `ignore_offset_discrepancy=True` |
| `MultipleDataSetsError` | File contains multiple datasets | Use `read_multiple_data_sets()` instead |
| `FCSParsingError` | Corrupt or non-standard FCS file | Try `ignore_offset_error=True`; verify file is valid FCS |
| Out of memory on large files | Millions of events loaded at once | Use `only_text=True` for metadata; process in chunks by channel |
| Unexpected channel count | Null/padding channels in file | Use `null_channel_list=["Time", "Null"]` to exclude |
| Modified data has wrong values | Applied preprocessing before modification | Use `preprocess=False` for raw data when modifying events |
| Channel names missing (empty PnS) | Instrument didn't set descriptive names | Use `pnn_labels` (short names) instead; PnS is optional in FCS spec |

## Related Skills

- **matplotlib-scientific-plotting** — create scatter plots, density plots, and histograms from extracted cytometry data
- **scikit-learn-machine-learning** — clustering and dimensionality reduction on cytometry event data

## References

- [FlowIO documentation](https://github.com/whitews/FlowIO) — official GitHub repository and API
- [FCS file format specification](https://www.isac-net.org/page/Data-Standards) — ISAC data standards for flow cytometry
- Spidlen et al. (2010) "Data File Standard for Flow Cytometry, Version FCS 3.1" — Cytometry Part A
