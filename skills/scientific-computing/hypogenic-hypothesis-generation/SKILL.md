---
name: "hypogenic-hypothesis-generation"
description: "LLM-driven hypothesis generation/testing on tabular data. Three methods: HypoGeniC (data-driven), HypoRefine (literature+data), Union. Iterative refinement, Redis caching, multi-hypothesis inference. Manual: hypothesis-generation; ideation: scientific-brainstorming."
license: "MIT"
---

# HypoGeniC Hypothesis Generation

## Overview

HypoGeniC automates scientific hypothesis generation and testing using LLMs on tabular datasets. Given labeled data (e.g., deception detection, AI-content identification), it generates testable hypotheses, iteratively refines them against validation performance, and runs inference to classify new samples. It supports three approaches: purely data-driven (HypoGeniC), literature-integrated (HypoRefine), and mechanistic union of both.

## When to Use

- Generating testable hypotheses from labeled observational datasets without prior theory
- Systematically testing multiple competing hypotheses on empirical data
- Combining insights from research papers with data-driven pattern discovery
- Accelerating hypothesis ideation in domains like deception detection, content analysis, mental health indicators
- Benchmarking LLM-based hypothesis generation methods against few-shot baselines
- For manual hypothesis formulation frameworks, use **hypothesis-generation** knowhow
- For general-purpose ML classification without hypothesis interpretability, use **scikit-learn-machine-learning**

## Prerequisites

- **Python packages**: `hypogenic`
- **Optional**: Redis server (port 6832) for LLM response caching; GROBID for PDF literature processing
- **API keys**: OpenAI, Anthropic, or compatible LLM API key in environment
- **Data**: Labeled JSON datasets in HypoGeniC format (see Key Concepts)

```bash
pip install hypogenic

# Optional: clone example datasets
git clone https://github.com/ChicagoHAI/HypoGeniC-datasets.git ./data
git clone https://github.com/ChicagoHAI/Hypothesis-agent-datasets.git ./data_lit
```

## Quick Start

```python
from hypogenic import BaseTask
import re

# Custom label extractor (must match dataset label format)
def extract_label(text: str) -> str:
    match = re.search(r'final answer:\s+(.*)', text, re.IGNORECASE)
    return match.group(1).strip() if match else text.strip()

# 1. Load task from config
task = BaseTask(
    config_path="./data/your_task/config.yaml",
    extract_label=extract_label
)

# 2. Generate hypotheses (data-driven)
task.generate_hypotheses(
    method="hypogenic",
    num_hypotheses=20,
    output_path="./output/hypotheses.json"
)

# 3. Run inference on test set
results = task.inference(
    hypothesis_bank="./output/hypotheses.json",
    test_data="./data/your_task/your_task_test.json"
)
print(f"Accuracy: {results['accuracy']:.3f}")
```

## Workflow

### Step 1: Prepare Dataset

Create train/val/test JSON files with text features and labels.

```python
import json

# Dataset: each key maps to a list of equal length
dataset = {
    "headline_1": [
        "What Up, Comet? You Just Got *PROBED*",
        "Scientists Made a Breakthrough in Quantum Computing"
    ],
    "headline_2": [
        "Scientists Were Holding Their Breath Today. Here's Why.",
        "New Quantum Computer Achieves Milestone"
    ],
    "label": [
        "Headline 2 has more clicks than Headline 1",
        "Headline 1 has more clicks than Headline 2"
    ]
}

# All lists must have equal length; labels must match extract_label output
for split in ["train", "val", "test"]:
    with open(f"my_task_{split}.json", "w") as f:
        json.dump(dataset, f, indent=2)
print(f"Created dataset with {len(dataset['label'])} samples")
```

### Step 2: Create Task Configuration

Write a `config.yaml` defining dataset paths and prompt templates.

```python
# config.yaml structure (write as YAML file)
config = """
task_name: my_task

train_data_path: ./my_task_train.json
val_data_path: ./my_task_val.json
test_data_path: ./my_task_test.json

prompt_templates:
  observations: |
    Feature 1: ${text_features_1}
    Feature 2: ${text_features_2}
    Observation: ${label}

  batched_generation:
    system: "You are a research scientist generating hypotheses."
    user: "Generate ${num_hypotheses} testable hypotheses from these observations."

  inference:
    system: "You are evaluating a hypothesis against data."
    user: "Hypothesis: ${hypothesis}\\nSample: ${sample_text}\\nFinal answer: ${label}"

  is_relevant:
    system: "Check hypothesis relevance."
    user: "Is this hypothesis relevant? ${hypothesis}"
"""

with open("config.yaml", "w") as f:
    f.write(config)
print("Configuration written to config.yaml")
```

### Step 3: Implement Label Extraction

Define a custom `extract_label` function matching your label format.

```python
import re

def extract_label(llm_output: str) -> str:
    """Parse LLM output to extract predicted label.

    Must return labels matching the 'label' field values in the dataset.
    Default: searches for 'final answer: <label>' pattern.
    """
    match = re.search(r'final answer:\s+(.*)', llm_output, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    # Domain-specific fallback
    if "Final prediction:" in llm_output:
        return llm_output.split("Final prediction:")[-1].strip()
    return llm_output.strip()

# Test against expected labels
assert extract_label("Final answer: Headline 1") == "Headline 1"
print("Label extractor validated")
```

### Step 4: Generate Hypotheses (HypoGeniC)

Run data-driven hypothesis generation with iterative refinement.

```python
from hypogenic import BaseTask

task = BaseTask(
    config_path="./config.yaml",
    extract_label=extract_label
)

# Generate hypotheses: initializes from data subset, iteratively refines
task.generate_hypotheses(
    method="hypogenic",       # Data-driven generation
    num_hypotheses=20,        # Target number of hypotheses
    output_path="./output/hypotheses.json"
)
# CLI equivalent:
# hypogenic_generation --config config.yaml --method hypogenic --num_hypotheses 20
print("Hypothesis bank saved to ./output/hypotheses.json")
```

### Step 5: Run Inference

Test generated hypotheses against the test set.

```python
results = task.inference(
    hypothesis_bank="./output/hypotheses.json",
    test_data="./my_task_test.json"
)
print(f"Test accuracy: {results['accuracy']:.3f}")
print(f"Predictions: {results['predictions'][:5]}")
# CLI equivalent:
# hypogenic_inference --config config.yaml --hypotheses output/hypotheses.json
```

### Step 6: Literature-Integrated Generation (HypoRefine)

Combine literature insights with data-driven hypotheses.

```python
# Requires GROBID setup and preprocessed PDFs
# bash ./modules/setup_grobid.sh  # first time
# bash ./modules/run_grobid.sh    # start GROBID service
# python pdf_preprocess.py --task_name my_task

task.generate_hypotheses(
    method="hyporefine",
    num_hypotheses=15,
    literature_path="./literature/my_task/",
    output_path="./output/"
)
# Generates 3 hypothesis banks:
# - HypoRefine (integrated literature+data)
# - Literature-only hypotheses
# - Literature union HypoRefine
print("HypoRefine generation complete: 3 hypothesis banks created")
```

### Step 7: Multi-Hypothesis Inference

Test multiple hypotheses simultaneously for ensemble classification.

```python
from examples.multi_hyp_inference import run_multi_hypothesis_inference

results = run_multi_hypothesis_inference(
    config_path="./config.yaml",
    hypothesis_bank="./output/hypotheses.json",
    test_data="./my_task_test.json"
)
print(f"Multi-hypothesis accuracy: {results['accuracy']:.3f}")
```

## Key Parameters

| Parameter | Default | Range / Options | Effect |
|-----------|---------|-----------------|--------|
| `method` | `"hypogenic"` | `"hypogenic"`, `"hyporefine"`, `"union"` | Generation strategy |
| `num_hypotheses` | `20` | `5`-`50` | Number of hypotheses to generate |
| `batch_size` | `5` | `3`-`10` | Samples per generation batch |
| `max_iterations` | `10` | `1`-`50` | Refinement iterations |
| `temperature` | `0.7` | `0.0`-`1.0` | LLM sampling temperature |
| `confidence_threshold` | `0.7` | `0.5`-`0.95` | Inference confidence cutoff |
| `num_papers` | `10` | `5`-`30` | Papers for HypoRefine literature extraction |
| `inference_method` | `"voting"` | `"voting"`, `"weighted"`, `"ensemble"` | How multiple hypotheses combine predictions |

## Key Concepts

### Dataset Format

HypoGeniC expects JSON files with parallel lists:

```json
{
  "text_features_1": ["sample_1_feat1", "sample_2_feat1"],
  "text_features_2": ["sample_1_feat2", "sample_2_feat2"],
  "label": ["class_A", "class_B"]
}
```

- All lists must have equal length
- Feature keys are customizable (`review_text`, `post_content`, etc.)
- Labels must match the `extract_label()` output format exactly
- Three splits required: `<TASK>_train.json`, `<TASK>_val.json`, `<TASK>_test.json`

### Three Generation Methods

| Method | Input | Process | Best For |
|--------|-------|---------|----------|
| **HypoGeniC** | Data only | Init from subset, iteratively refine on validation | Exploratory research, novel datasets without literature |
| **HypoRefine** | Data + PDFs | Extract literature insights, merge with data patterns, refine both | Extending or validating existing theories |
| **Union** | Literature + HypoGeniC | Mechanistic combination, deduplication | Maximum hypothesis diversity and coverage |

### Configuration Template

Minimal required `config.yaml` structure:

```yaml
task_name: my_task
train_data_path: ./my_task_train.json
val_data_path: ./my_task_val.json
test_data_path: ./my_task_test.json

model:
  name: "gpt-4"                    # or claude-3, gpt-3.5-turbo
  api_key_env: "OPENAI_API_KEY"
  temperature: 0.7

generation:
  method: "hypogenic"
  num_hypotheses: 20
  batch_size: 5
  max_iterations: 10

cache:
  enabled: true                    # Redis on localhost:6832
  host: "localhost"
  port: 6832

prompt_templates:
  observations: |
    Feature 1: ${text_features_1}
    Observation: ${label}
  batched_generation:
    system: "Generate testable hypotheses."
    user: "Generate ${num_hypotheses} hypotheses."
  inference:
    system: "Evaluate hypothesis against sample."
    user: "Hypothesis: ${hypothesis}\nSample: ${sample_text}"
  is_relevant:
    system: "Check relevance."
    user: "Is ${hypothesis} relevant?"
```

## Common Recipes

### Recipe: Custom Task from Scratch

When to use: creating a new classification task with domain-specific data.

```python
import json
from hypogenic import BaseTask

# 1. Prepare data splits
for split_name, data in [("train", train_data), ("val", val_data), ("test", test_data)]:
    with open(f"my_task_{split_name}.json", "w") as f:
        json.dump(data, f)

# 2. Define domain-specific label extractor
def my_extractor(text):
    if "positive" in text.lower():
        return "positive"
    elif "negative" in text.lower():
        return "negative"
    return text.strip()

# 3. Create task and run full pipeline
task = BaseTask(config_path="./my_task/config.yaml", extract_label=my_extractor)
task.generate_hypotheses(method="hypogenic", num_hypotheses=15, output_path="./output/")
results = task.inference(hypothesis_bank="./output/hypotheses.json")
print(f"Custom task accuracy: {results['accuracy']:.3f}")
```

### Recipe: Literature Processing Setup

When to use: setting up GROBID for PDF-to-structured-text conversion before HypoRefine.

```bash
# 1. Setup GROBID (first time only)
bash ./modules/setup_grobid.sh

# 2. Place PDFs in literature directory
mkdir -p literature/my_task/raw/
cp papers/*.pdf literature/my_task/raw/

# 3. Start GROBID and process
bash ./modules/run_grobid.sh
cd examples && python pdf_preprocess.py --task_name my_task
# Output: structured text files in literature/my_task/processed/
```

### Recipe: Union Method for Maximum Coverage

When to use: combining literature and data-driven hypotheses for comprehensive coverage.

```python
# Generate literature hypotheses first (via HypoRefine)
task.generate_hypotheses(
    method="hyporefine",
    num_hypotheses=15,
    literature_path="./literature/my_task/",
    output_path="./output/"
)

# Union combines and deduplicates both banks
# CLI alternative:
# hypogenic_generation --config config.yaml --method union \
#   --literature_hypotheses output/lit_hypotheses.json

# Compare all three approaches
for bank in ["hypogenic", "hyporefine", "union"]:
    r = task.inference(hypothesis_bank=f"./output/{bank}_hypotheses.json")
    print(f"{bank}: accuracy={r['accuracy']:.3f}")
```

## Expected Outputs

- `hypotheses.json` -- hypothesis bank with ranked, testable hypotheses (typically 10-20)
- Inference results with per-sample predictions and overall accuracy
- For HypoRefine: three hypothesis banks (literature-only, integrated, union)
- Reported improvements: ~9% over few-shot baselines, ~16% over literature-only approaches
- 80-84% hypothesis pair diversity (non-redundant insights)

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| `ModuleNotFoundError: hypogenic` | Package not installed | `pip install hypogenic` |
| Generic/untestable hypotheses | Prompt templates too vague | Add domain-specific context to `batched_generation` prompt |
| Poor inference accuracy | Few training examples or bad label extraction | Increase training data; verify `extract_label` matches dataset labels |
| GROBID PDF processing fails | GROBID service not running | `bash ./modules/run_grobid.sh`; ensure PDFs are valid papers |
| Label extraction mismatches | `extract_label` output differs from dataset labels | Print both formats and align; test with `assert extract_label(sample) == expected` |
| Redis connection errors | Redis not running or wrong port | Start Redis on port 6832 or set `cache.enabled: false` |
| API rate limit errors | Too many concurrent LLM calls | Reduce `batch_size`; enable Redis caching to avoid duplicate calls |
| Empty hypothesis bank | Config missing required prompt templates | Include all four templates: observations, batched_generation, inference, is_relevant |

## Bundled Resources

This entry is self-contained. The original `references/config_template.yaml` (151 lines) has been consolidated into the Key Concepts "Configuration Template" subsection, retaining the essential YAML structure, model/cache/generation parameters, and prompt template patterns. Omitted from the template: evaluation metrics block, logging configuration, task-specific feature/label metadata descriptions -- these are standard YAML patterns users can add as needed.

## Related Skills

- **hypothesis-generation** -- knowhow for manual hypothesis formulation frameworks and scientific method
- **scikit-learn-machine-learning** -- classical ML for classification when hypothesis interpretability is not needed
- **pubmed-database** -- literature search to find papers for HypoRefine input

## References

- Zhou, Y., Liu, H., Srivastava, T., Mei, H., & Tan, C. (2024). "Hypothesis Generation with Large Language Models." EMNLP Workshop NLP for Science. https://aclanthology.org/2024.nlp4science-1.10/
- Liu, H., Zhou, Y., Li, M., Yuan, C., & Tan, C. (2024). "Literature Meets Data: A Synergistic Approach to Hypothesis Generation." arXiv:2410.17309. https://arxiv.org/abs/2410.17309
- Liu, H., Huang, S., Hu, J., Zhou, Y., & Tan, C. (2025). "HypoBench: Towards Systematic and Principled Benchmarking for Hypothesis Generation." arXiv:2504.11524. https://arxiv.org/abs/2504.11524
- GitHub Repository: https://github.com/ChicagoHAI/hypothesis-generation
- PyPI Package: https://pypi.org/project/hypogenic/
