<!-- Template: Pipeline Sub-type — for tools with a linear input→processing→output flow.
     For toolkit-style tools (multiple independent modules), use SKILL_TEMPLATE_TOOLKIT.md instead. -->
---
name: "Skill Name Here"
description: "Brief description of what this skill does and when to use it (max 1024 chars)"
license: "CC-BY-4.0"  # Use tool's license if known; CC-BY-4.0 for original content
---

# Skill Name Here

## Overview

Brief description of the skill (2-3 sentences). What problem does it solve? What is the expected output?

## When to Use

<!-- 5+ items. Write from the USER'S TASK perspective, not keyword-matching.
     Good: "Identifying differentially expressed genes between conditions"
     Bad:  "Users mention 'DESeq2' or 'differential expression'" -->

- Use case 1: description
- Use case 2: description
- Use case 3: description

## Prerequisites

- **Python packages**: `package1`, `package2`
- **Data requirements**: description of input data format
- **Environment**: any special setup needed

```bash
pip install package1 package2
```

## Quick Start

<!-- Optional but recommended. Complete minimal pipeline in one code block (10-20 lines).
     Lets users copy-paste and run immediately without reading the full Workflow. -->

```python
import package1

# 1. Load data
data = package1.load("input_file.csv")

# 2. Process
results = package1.process(data, param1="value1")

# 3. Output
results.to_csv("output_results.csv")
print(f"Done: {len(results)} results saved")
```

## Workflow

<!-- Each step MUST have its own code block. Target: 1 code block per step, 5-8 steps total.
     Include standard visualization (plots) as Workflow steps, not in Common Recipes. -->

### Step 1: Data Loading

Description of what this step does.

```python
import package1

# Load input data
data = package1.load("input_file.csv")
print(f"Loaded {len(data)} records")
```

### Step 2: Processing

Description of the processing step.

```python
# Process the data
results = package1.process(data, param1="value1")
print(f"Processing complete: {results.summary()}")
```

### Step 3: Output Generation

Description of output generation.

```python
# Generate and save outputs
results.to_csv("output_results.csv")
results.plot(save="output_figure.png")
print("Results saved to output_results.csv")
```

## Key Parameters

<!-- List the most important tunable parameters with defaults and recommended ranges. -->

| Parameter | Default | Range / Options | Effect |
|-----------|---------|-----------------|--------|
| `param1` | `value1` | `value1`-`value3` | Controls X behavior |
| `param2` | `10` | `5`-`50` | Adjusts Y granularity |
| `param3` | `"auto"` | `"auto"`, `"manual"` | Selects Z mode |

## Common Recipes

<!-- 2-4 self-contained snippets for ALTERNATIVE APPROACHES or OPTIONAL EXTENSIONS
     beyond the main workflow. Do NOT duplicate Workflow steps here.
     Examples: batch correction, multi-contrast testing, QC diagnostics, save/reload. -->

### Recipe: Alternative Approach A

When to use: brief scenario description.

```python
# Self-contained snippet
result = package1.alternative_method(data, option="A")
```

### Recipe: Alternative Approach B

When to use: brief scenario description.

```python
# Self-contained snippet
result = package1.other_method(data, correction=True)
```

## Expected Outputs

- `output_results.csv` — tabular results with columns: col1, col2, col3
- `output_figure.png` — visualization showing key findings

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| `ModuleNotFoundError` | Package not installed | `pip install package1` |
| `MemoryError` | Dataset too large | Use chunked processing or subsample |
| Empty results | Input format mismatch | Check input file has expected columns |

## References

- [Tool documentation](https://example.com/docs) — official docs
- [Protocol reference](https://protocols.io/xxx) — original protocol (CC-BY)
