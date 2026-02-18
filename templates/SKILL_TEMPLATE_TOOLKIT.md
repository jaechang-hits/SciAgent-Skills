<!-- Template: Toolkit Sub-type — for tools that are collections of independent functional modules.
     For pipeline-style tools (linear input→processing→output), use SKILL_TEMPLATE.md instead.
     For database/API wrapper tools, use this template with adaptations noted in CLAUDE.md. -->
---
name: "Toolkit Name Here"
description: "Brief description of what this toolkit does and when to use it (max 1024 chars)"
license: "CC-BY-4.0"
---

# Toolkit Name Here

## Overview

Brief description of the toolkit (2-3 sentences). What domain does it cover? What kinds of tasks does it enable?

## When to Use

<!-- 5+ items. Write from the USER'S TASK perspective.
     Include 1-2 comparison notes: "For X use Y instead" to help agents route correctly. -->

- Use case 1: description
- Use case 2: description
- Use case 3: description
- Use case 4: description
- Use case 5: description
- For [alternative use-case], use `alternative-tool` instead

## Prerequisites

- **Python packages**: `package1`, `package2`
- **Data requirements**: description of common input data formats
- **Environment**: any special setup needed
<!-- For database/API skills, add: **Rate limits**: max N requests/second -->

```bash
pip install package1 package2
```

## Quick Start

<!-- Optional but recommended for large toolkits. Minimal example showing the most common
     use-case in a single code block (5-15 lines). -->

```python
import package1

data = package1.read("input.ext")
result = package1.analyze(data)
print(f"Result: {result}")
```

## Core API

<!-- Organize by functional module (4-8 subsections). Each subsection covers one module with 1-2 code blocks.
     Target: 8-16 code blocks total in this section.
     For database skills: organize by query type instead of library module. -->

### Module 1: Data I/O

Loading and saving data in various formats.

```python
import package1

# Load from file
data = package1.read("input_file.ext")
print(f"Loaded: {type(data)}, records: {len(data)}")

# Save to file
package1.write(data, "output_file.ext")
```

### Module 2: Core Processing

Primary data transformations and operations.

```python
# Transform data
result = package1.transform(data, method="default")
print(f"Transformed: {result.shape}")
```

```python
# Alternative transformation
result2 = package1.transform(data, method="advanced", param=0.5)
print(f"Advanced result: {result2.shape}")
```

### Module 3: Analysis Functions

Analytical computations and metrics.

```python
# Compute metrics
metrics = package1.analyze(data)
print(f"Metric A: {metrics['a']:.3f}")
print(f"Metric B: {metrics['b']:.3f}")
```

### Module 4: Visualization

Plotting and figure generation.

```python
import matplotlib.pyplot as plt

fig, ax = plt.subplots(figsize=(8, 6))
package1.plot(data, ax=ax, style="publication")
plt.savefig("output_plot.png", dpi=300, bbox_inches="tight")
print("Saved output_plot.png")
```

## Key Concepts

<!-- Optional but recommended when the tool has non-obvious data model or domain-specific
     abstractions. 2-4 subsections explaining what users must understand to read the code.
     Examples: COBRApy's DictList, exchange reaction sign conventions; AnnData's obs/var/layers. -->

### Concept 1: Data Model Name

Brief explanation of the concept (2-3 sentences).

```python
# Short example demonstrating the concept
```

## Common Workflows

<!-- End-to-end pipelines combining multiple Core API modules.
     At least 2 must be complete runnable code blocks.
     For large toolkits (6+ modules), additional workflows may be text-only numbered steps. -->

### Workflow 1: Standard Analysis Pipeline

**Goal**: Describe what this workflow achieves end-to-end.

```python
import package1
import pandas as pd

# Step 1: Load data
data = package1.read("input.ext")

# Step 2: Filter and preprocess
filtered = package1.filter(data, criterion="quality", value=0.8)

# Step 3: Analyze
results = package1.analyze(filtered)

# Step 4: Visualize
package1.plot(results, save="analysis_results.png")

# Step 5: Export
df = pd.DataFrame(results)
df.to_csv("analysis_results.csv", index=False)
print(f"Pipeline complete: {len(df)} results saved")
```

### Workflow 2: Batch Processing Pipeline

**Goal**: Describe what this workflow achieves for batch/multi-sample processing.

```python
import package1
import pandas as pd
from pathlib import Path

# Process multiple inputs
input_dir = Path("inputs/")
all_results = []

for f in sorted(input_dir.glob("*.ext")):
    data = package1.read(str(f))
    result = package1.analyze(data)
    result["source"] = f.stem
    all_results.append(result)

# Combine and export
combined = pd.DataFrame(all_results)
combined.to_csv("batch_results.csv", index=False)
print(f"Processed {len(all_results)} files → batch_results.csv")
```

## Key Parameters

<!-- List the most important tunable parameters across modules.
     Add a Module column to indicate which module each parameter belongs to.
     For universal parameters, use "All" in the Module column. -->

| Parameter | Module | Default | Range / Options | Effect |
|-----------|--------|---------|-----------------|--------|
| `param1` | Core Processing | `"default"` | `"default"`, `"advanced"` | Controls processing method |
| `param2` | Analysis | `0.5` | `0.0`-`1.0` | Threshold for significance |
| `param3` | Filtering | `None` | Any numeric | Minimum quality cutoff |
| `param4` | Visualization | `"publication"` | `"publication"`, `"interactive"` | Plot style |
| `param5` | All | `"default"` | `"default"`, `"strict"` | Global stringency |

## Best Practices

<!-- Optional but recommended for large toolkits. 3-7 items.
     Include brief code examples where helpful.
     Weave conceptual pitfalls in as "Don't..." items here (not a separate section). -->

1. **Always do X**: Rationale for best practice
   ```python
   # Example code
   ```

2. **Use Y instead of Z**: Rationale with comparison

3. **Don't do W**: Why this is a common mistake and what to do instead

## Common Recipes

<!-- Short, self-contained code snippets for frequent tasks. 2-4 recipes. -->

### Recipe: Quick Summary Statistics

When to use: Get a fast overview of your data without full analysis.

```python
data = package1.read("input.ext")
summary = package1.summarize(data)
for key, val in summary.items():
    print(f"  {key}: {val}")
```

### Recipe: Format Conversion

When to use: Convert between file formats.

```python
data = package1.read("input.format_a")
package1.write(data, "output.format_b")
print("Converted format_a → format_b")
```

## Troubleshooting

<!-- Table of problem/cause/solution (5+ rows).
     For technical errors only. Conceptual pitfalls go in Best Practices.
     If a solution needs multi-line code, use hybrid format: table + subsection. -->

| Problem | Cause | Solution |
|---------|-------|----------|
| `ModuleNotFoundError` | Package not installed | `pip install package1` |
| `MemoryError` | Dataset too large | Process in batches or use streaming mode |
| Empty results | Input format mismatch | Check input file format matches expected type |
| Slow computation | Large pairwise comparisons | Use approximate methods or subsample first |
| `ValueError: invalid input` | Corrupted or malformed data | Validate input with `package1.validate(data)` |

## Related Skills

<!-- Optional but recommended for ecosystem tools. List connected tools with brief descriptions.
     Especially important when the tool is part of a larger ecosystem (scverse, tidyverse, etc.). -->

- **related-tool-1** — how this tool connects (e.g., "downstream analysis after data preparation")
- **related-tool-2** — how this tool connects (e.g., "alternative for X use-case")

## References

- [Tool documentation](https://example.com/docs) — official docs
- [API reference](https://example.com/api) — complete API reference
- [Tutorial collection](https://example.com/tutorials) — official tutorials
