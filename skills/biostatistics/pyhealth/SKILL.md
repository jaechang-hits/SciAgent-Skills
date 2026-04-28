---
name: "pyhealth"
description: "Python library for healthcare ML on EHR data: process MIMIC-III/IV, eICU, OMOP-CDM; encode medical codes (ICD, ATC, NDC); build patient-level datasets; train Transformer, RETAIN, GRASP, MedBERT for mortality, drug recommendation, readmission, diagnosis prediction. Alternatives: FIDDLE (preprocessing), clinical-longformer (clinical NLP), ehr-ml (embeddings)."
license: "BSD-3-Clause"
---

# PyHealth

## Overview

PyHealth provides an end-to-end pipeline for healthcare ML on EHR data: data loading → medical code processing → patient-level dataset construction → model training → evaluation. It natively supports MIMIC-III, MIMIC-IV, eICU-CRD, and OMOP-CDM structured databases, and handles the idiosyncratic data formats of each. Medical codes (ICD-9, ICD-10, ATC, NDC, SNOMED) are organized in a hierarchical code system that supports code-level embedding and cross-ontology mapping. Pre-built tasks — mortality prediction, drug recommendation, readmission, length-of-stay, diagnosis code prediction — can be instantiated in a few lines. Custom tasks follow a standardized interface.

## When to Use

- Training clinical outcome prediction models (mortality, readmission, LOS) from MIMIC-III or MIMIC-IV
- Building drug recommendation or drug interaction prediction models using ATC code hierarchy
- Processing OMOP-CDM formatted data from institutional EHR systems for ML
- Using pretrained clinical models (RETAIN, GRASP, MedBERT) as baselines on healthcare benchmarks
- Constructing patient visit sequences with temporal structure for RNN/Transformer models
- Evaluating clinical prediction models with appropriate metrics (AUROC, AUPRC, F1, Jaccard)
- Use FIDDLE for pure EHR preprocessing without ML; use clinical-longformer for clinical note NLP

## Prerequisites

- **Python packages**: `pyhealth`, `torch`, `pandas`, `scikit-learn`
- **Data requirements**: MIMIC-III/IV CSV files (requires PhysioNet credentialing), eICU, or OMOP-CDM database
- **MIMIC access**: request at [physionet.org](https://physionet.org/) (free; requires CITI training, ~1 week)

```bash
pip install pyhealth torch pandas scikit-learn
# Download MIMIC-III: https://physionet.org/content/mimiciii/
# Download MIMIC-IV: https://physionet.org/content/mimiciv/
```

## Quick Start

```python
from pyhealth.datasets import MIMIC3Dataset

# Load MIMIC-III (specify path to downloaded CSV files)
dataset = MIMIC3Dataset(
    root="path/to/mimic-iii/",
    tables=["DIAGNOSES_ICD", "PRESCRIPTIONS", "PROCEDURES_ICD"],
    code_mapping={"ICD9CM": "CCSCM"},  # map ICD-9 codes to CCS multi-level
    dev=True,  # dev=True uses 1% of data for fast testing
)

print(f"Patients: {dataset.stat()['num_patients']}")
print(f"Visits: {dataset.stat()['num_visits']}")
```

## Core API

### Module 1: Dataset Loading

Load MIMIC-III, MIMIC-IV, eICU, and OMOP-CDM datasets.

```python
from pyhealth.datasets import MIMIC3Dataset, MIMIC4Dataset, eICUDataset

# MIMIC-III
mimic3 = MIMIC3Dataset(
    root="data/mimic-iii/",
    tables=["DIAGNOSES_ICD", "PRESCRIPTIONS", "PROCEDURES_ICD", "LABEVENTS"],
    code_mapping={"ICD9CM": "CCSCM", "NDC": "ATC3"},  # standardize codes
    dev=False,
)
stats = mimic3.stat()
print(f"MIMIC-III: {stats['num_patients']} patients, {stats['num_visits']} visits")

# MIMIC-IV
mimic4 = MIMIC4Dataset(
    root="data/mimic-iv/",
    tables=["diagnoses_icd", "prescriptions", "procedures_icd"],
    code_mapping={"ICD10CM": "CCSCM"},
    dev=True,
)

# eICU
eicu = eICUDataset(
    root="data/eicu/",
    tables=["diagnosis", "medication", "treatment"],
    dev=True,
)
print(f"eICU loaded: {eicu.stat()}")
```

```python
# Explore dataset structure
patient_id = list(mimic3.patients.keys())[0]
patient = mimic3.patients[patient_id]
print(f"Patient {patient_id}: {len(patient.visits)} visits")

for visit in patient.visits[:2]:
    print(f"  Visit {visit.visit_id}:")
    print(f"    Diagnoses: {visit.get_code_list('CCSCM')[:5]}")
    print(f"    Medications: {visit.get_code_list('ATC3')[:3]}")
```

### Module 2: Task Construction

Convert raw datasets into ML-ready task datasets.

```python
from pyhealth.tasks import mortality_prediction_mimic3_fn
from pyhealth.datasets import SampleDataset

# Mortality prediction task
# Each sample: patient's visit history → binary mortality label
mortality_dataset = SampleDataset(
    dataset=mimic3,
    task_fn=mortality_prediction_mimic3_fn,
)

print(f"Task: mortality prediction")
print(f"Samples: {len(mortality_dataset)}")

# Inspect a sample
sample = mortality_dataset[0]
print(f"Sample keys: {list(sample.keys())}")
print(f"Conditions (ICD codes): {sample['conditions'][:3]}")
print(f"Drugs (ATC codes): {sample['drugs'][:3]}")
print(f"Label (mortality): {sample['label']}")
```

```python
# Custom task: 30-day readmission prediction
def readmission_30day_fn(patient):
    """Custom task function: predict 30-day readmission after discharge."""
    samples = []
    for i, visit in enumerate(patient.visits[:-1]):
        next_visit = patient.visits[i + 1]
        # Compute days between discharge and next admission
        days_gap = (next_visit.encounter_time - visit.discharge_time).days
        label = int(days_gap <= 30)

        samples.append({
            "visit_id": visit.visit_id,
            "patient_id": patient.patient_id,
            "conditions": visit.get_code_list("CCSCM"),
            "drugs": visit.get_code_list("ATC3"),
            "procedures": visit.get_code_list("ICD9PROC"),
            "label": label,
        })
    return samples

readmission_dataset = SampleDataset(dataset=mimic3, task_fn=readmission_30day_fn)
print(f"Readmission samples: {len(readmission_dataset)}")
pos_rate = sum(s["label"] for s in readmission_dataset) / len(readmission_dataset)
print(f"Positive rate (30-day readmission): {pos_rate:.2%}")
```

### Module 3: Medical Code Systems

Work with ICD, ATC, NDC, and other hierarchical medical code systems.

```python
from pyhealth.medcode import InnerMap

# ICD-9-CM diagnosis codes
icd9 = InnerMap.load("ICD9CM")
code = "428.0"  # Heart failure, unspecified
print(f"Code: {code}")
print(f"Description: {icd9.lookup(code)}")
print(f"Ancestors: {icd9.get_ancestors(code)}")
print(f"Children: {icd9.get_children(code)[:5]}")

# ATC drug classification
atc = InnerMap.load("ATC")
drug_code = "A10BA02"  # Metformin
print(f"\nATC: {drug_code}")
print(f"Drug: {atc.lookup(drug_code)}")
print(f"L1 class: {atc.get_ancestors(drug_code)}")
```

```python
# Cross-ontology code mapping
from pyhealth.medcode import CrossMap

# Map NDC (drug product codes) to ATC level 3
ndc_to_atc = CrossMap.load("NDC", "ATC3")
ndc_code = "0069-2587-30"  # example NDC
atc3_codes = ndc_to_atc.map(ndc_code)
print(f"NDC {ndc_code} → ATC3: {atc3_codes}")

# Map ICD-9 to ICD-10
icd9_to_icd10 = CrossMap.load("ICD9CM", "ICD10CM")
icd10 = icd9_to_icd10.map("428.0")
print(f"ICD-9 428.0 → ICD-10: {icd10}")
```

### Module 4: Model Training

Train pre-implemented clinical ML models.

```python
from pyhealth.models import Transformer, RETAIN
from pyhealth.datasets import split_by_patient, get_dataloader
import torch

# Train/val/test split (patient-level, no leakage)
train_ds, val_ds, test_ds = split_by_patient(mortality_dataset, [0.7, 0.1, 0.2])

train_loader = get_dataloader(train_ds, batch_size=32, shuffle=True)
val_loader   = get_dataloader(val_ds,   batch_size=64, shuffle=False)
test_loader  = get_dataloader(test_ds,  batch_size=64, shuffle=False)

print(f"Train: {len(train_ds)} | Val: {len(val_ds)} | Test: {len(test_ds)}")

# Transformer model for EHR sequence modeling
model = Transformer(
    dataset=mortality_dataset,
    feature_keys=["conditions", "drugs", "procedures"],
    label_key="label",
    mode="binary",        # binary classification
    embedding_dim=128,
    num_heads=4,
    num_layers=2,
    dropout=0.1,
)

print(f"Model parameters: {sum(p.numel() for p in model.parameters()):,}")
```

```python
# RETAIN: Reverse Time Attention model (interpretable clinical ML)
retain_model = RETAIN(
    dataset=mortality_dataset,
    feature_keys=["conditions", "drugs"],
    label_key="label",
    mode="binary",
    embedding_dim=64,
)
```

### Module 5: Training and Evaluation

```python
from pyhealth.trainer import Trainer

trainer = Trainer(
    model=model,
    metrics=["pr_auc", "roc_auc", "f1"],  # PR-AUC, ROC-AUC, F1
)

trainer.train(
    train_dataloader=train_loader,
    val_dataloader=val_loader,
    epochs=20,
    optimizer_params={"lr": 1e-3},
    weight_decay=1e-5,
    monitor="pr_auc",           # early stopping metric
    monitor_criterion="max",
    load_best_model_after_train=True,
)

# Evaluate on test set
results = trainer.evaluate(test_loader)
print("Test results:")
for metric, value in results.items():
    print(f"  {metric}: {value:.4f}")
```

### Module 6: Drug Recommendation

Predict which drugs a patient should receive based on visit history.

```python
from pyhealth.tasks import drug_recommendation_mimic3_fn
from pyhealth.models import GAMENet
from pyhealth.datasets import SampleDataset, split_by_patient, get_dataloader

# Drug recommendation task
drug_dataset = SampleDataset(
    dataset=mimic3,
    task_fn=drug_recommendation_mimic3_fn,
)

train_ds, val_ds, test_ds = split_by_patient(drug_dataset, [0.7, 0.1, 0.2])

# GAMENet: graph-augmented memory network for drug recommendation
gamenet = GAMENet(
    dataset=drug_dataset,
    feature_keys=["conditions", "procedures"],
    label_key="drugs",
    mode="multilabel",     # recommend multiple drugs per visit
    embedding_dim=64,
)

train_loader = get_dataloader(train_ds, batch_size=16, shuffle=True)

trainer = Trainer(model=gamenet, metrics=["jaccard", "f1", "prauc"])
trainer.train(train_dataloader=train_loader,
              val_dataloader=get_dataloader(val_ds, 32),
              epochs=30, monitor="jaccard")
print("Drug recommendation model trained")
```

## Key Concepts

### Patient-Visit-Event Hierarchy

PyHealth organizes EHR data as `Patient` → `Visit` → medical codes. Each `Visit` contains timestamped events across multiple tables (diagnoses, medications, procedures, labs). ML models see each patient as a sequence of visits, each visit as a set of medical codes, capturing temporal disease progression.

### Code Mapping and Standardization

Raw EHR codes (ICD-9, NDC) are highly specific and numerous. PyHealth's `code_mapping` parameter automatically converts them to coarser ontologies (CCSCM has ~260 categories vs. ~15,000 ICD-9 codes), reducing vocabulary size and enabling transfer between datasets.

## Common Workflows

### Workflow 1: Full Mortality Prediction Pipeline

```python
from pyhealth.datasets import MIMIC3Dataset, SampleDataset, split_by_patient, get_dataloader
from pyhealth.tasks import mortality_prediction_mimic3_fn
from pyhealth.models import Transformer
from pyhealth.trainer import Trainer

# 1. Load data
dataset = MIMIC3Dataset(
    root="data/mimic-iii/",
    tables=["DIAGNOSES_ICD", "PRESCRIPTIONS", "PROCEDURES_ICD"],
    code_mapping={"ICD9CM": "CCSCM", "NDC": "ATC3"},
    dev=True,
)

# 2. Build task dataset
task_ds = SampleDataset(dataset, task_fn=mortality_prediction_mimic3_fn)
print(f"Samples: {len(task_ds)}, Positive rate: {sum(s['label'] for s in task_ds)/len(task_ds):.2%}")

# 3. Split
train_ds, val_ds, test_ds = split_by_patient(task_ds, [0.7, 0.1, 0.2])

# 4. Model
model = Transformer(
    dataset=task_ds,
    feature_keys=["conditions", "drugs"],
    label_key="label",
    mode="binary",
    embedding_dim=128,
)

# 5. Train
trainer = Trainer(model=model, metrics=["pr_auc", "roc_auc"])
trainer.train(
    train_dataloader=get_dataloader(train_ds, 32, shuffle=True),
    val_dataloader=get_dataloader(val_ds, 64),
    epochs=15,
    monitor="pr_auc",
)

# 6. Evaluate
results = trainer.evaluate(get_dataloader(test_ds, 64))
print(f"Test PR-AUC: {results['pr_auc']:.4f}")
print(f"Test ROC-AUC: {results['roc_auc']:.4f}")
```

### Workflow 2: Model Comparison Benchmark

```python
from pyhealth.models import Transformer, RETAIN, MedBERT
from pyhealth.trainer import Trainer
from pyhealth.datasets import get_dataloader
import pandas as pd

models = {
    "Transformer": Transformer(task_ds, ["conditions", "drugs"], "label", "binary"),
    "RETAIN":      RETAIN(task_ds, ["conditions", "drugs"], "label", "binary"),
}

results_list = []
for name, model in models.items():
    trainer = Trainer(model=model, metrics=["pr_auc", "roc_auc", "f1"])
    trainer.train(
        train_dataloader=get_dataloader(train_ds, 32, shuffle=True),
        val_dataloader=get_dataloader(val_ds, 64),
        epochs=10,
        monitor="pr_auc",
    )
    test_results = trainer.evaluate(get_dataloader(test_ds, 64))
    test_results["model"] = name
    results_list.append(test_results)
    print(f"{name}: PR-AUC={test_results['pr_auc']:.4f}, ROC-AUC={test_results['roc_auc']:.4f}")

results_df = pd.DataFrame(results_list).set_index("model")
results_df.to_csv("model_comparison.csv")
print(results_df)
```

## Key Parameters

| Parameter | Module/Class | Default | Range / Options | Effect |
|-----------|-------------|---------|-----------------|--------|
| `tables` | `MIMIC3Dataset` | — | list of MIMIC table names | Which EHR tables to load; more tables = richer features, slower load |
| `code_mapping` | `MIMIC3Dataset` | `{}` | `{"ICD9CM": "CCSCM"}` | Maps raw codes to standardized ontologies |
| `dev` | `MIMIC3Dataset` | `False` | `True`/`False` | `True` uses 1% of data for fast development |
| `feature_keys` | All models | — | list of code type strings | Which medical code types to use as model input |
| `embedding_dim` | Transformer, RETAIN | 128 | 64–512 | Hidden size for code and patient embeddings |
| `num_heads` | `Transformer` | 4 | 1–16 | Multi-head attention heads (must divide `embedding_dim`) |
| `num_layers` | `Transformer` | 2 | 1–6 | Number of Transformer encoder layers |
| `dropout` | All models | 0.1 | 0–0.5 | Dropout rate for regularization |
| `mode` | All models | — | `"binary"`, `"multiclass"`, `"multilabel"` | Prediction task type |
| `monitor` | `Trainer.train` | `"loss"` | `"pr_auc"`, `"roc_auc"`, `"f1"` | Metric for early stopping and model selection |

## Best Practices

1. **Always use `split_by_patient`, never random split**: Splitting by visit (random) causes data leakage — the same patient can appear in train and test sets across different visits. PyHealth's `split_by_patient` ensures strict patient-level separation.

2. **Use `dev=True` during development**: MIMIC-III contains ~46,000 patients. Loading the full dataset takes minutes; dev mode loads ~460 patients in seconds. Switch to `dev=False` only for final training runs.

3. **Apply code mapping to standardize across datasets**: Raw ICD-9 codes have ~15,000 unique values; CCSCM reduces this to ~260 clinically meaningful groups. This dramatically reduces model vocabulary and enables meaningful code embeddings, especially important for small datasets.

4. **Evaluate with PR-AUC alongside ROC-AUC**: Clinical datasets are typically highly imbalanced (e.g., 10% mortality rate). PR-AUC is more informative than ROC-AUC for imbalanced tasks — a model that predicts all negatives achieves ROC-AUC ~0.5 but PR-AUC approaching the positive rate (~0.1).

## Common Recipes

### Recipe: Export Patient Embeddings

```python
import torch
from pyhealth.datasets import get_dataloader
import numpy as np

model.eval()
embeddings = []
labels = []

with torch.no_grad():
    for batch in get_dataloader(test_ds, batch_size=64):
        # Get patient-level representation (before classification head)
        hidden = model.get_patient_representation(batch)
        embeddings.append(hidden.cpu().numpy())
        labels.append(batch["label"].numpy())

embeddings = np.concatenate(embeddings, axis=0)
labels = np.concatenate(labels, axis=0)
np.save("patient_embeddings.npy", embeddings)
np.save("patient_labels.npy", labels)
print(f"Embeddings: {embeddings.shape}")
```

### Recipe: Class-Imbalance Handling with Weighted Sampler

```python
import torch
from torch.utils.data import WeightedRandomSampler
from pyhealth.datasets import get_dataloader

# Compute class weights for imbalanced mortality prediction
labels = [sample["label"] for sample in train_ds]
pos = sum(labels)
neg = len(labels) - pos
weights = [1.0/neg if l == 0 else 1.0/pos for l in labels]
sampler = WeightedRandomSampler(weights, num_samples=len(weights), replacement=True)

# Use sampler in dataloader
balanced_loader = torch.utils.data.DataLoader(
    train_ds, batch_size=32, sampler=sampler,
    collate_fn=train_ds.collate_fn
)
print(f"Balanced loader: {len(balanced_loader)} batches")
```

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| `FileNotFoundError` on dataset load | Wrong `root` path or missing MIMIC CSV files | Verify `root` contains the correct CSV files; list contents with `ls data/mimic-iii/*.csv` |
| `KeyError` for code type in `feature_keys` | Code type not loaded or mapping failed | Ensure `tables` includes the required table and `code_mapping` maps to the expected ontology |
| All samples have `label=0` in task dataset | Task function logic error or data issue | Print `task_fn(patient)` on a single patient; check label derivation logic |
| Memory error loading full MIMIC | Large dataset; insufficient RAM | Use `dev=True` during development; use chunked loading or reduce `tables` list |
| ROC-AUC ~0.5 on test set | Severe class imbalance causing trivial predictor | Use `WeightedRandomSampler`; report PR-AUC instead; lower classification threshold |
| CUDA out of memory during training | Batch size too large | Reduce `batch_size` from 32 to 8 or 16; use gradient accumulation |
| Code mapping returns empty list | Code not found in cross-map | Check code format (e.g., ICD-9 with decimal vs. without); try `InnerMap.load("ICD9CM").lookup(code)` |

## Related Skills

- `statsmodels-statistical-modeling` — logistic regression baselines for clinical outcome prediction
- `scikit-learn-machine-learning` — traditional ML baselines (random forest, gradient boosting) on PyHealth features
- `clinical-decision-support-documents` — translating clinical ML model outputs to decision support tools

## References

- [PyHealth documentation](https://pyhealth.readthedocs.io/) — API reference, tutorials, and task descriptions
- [PyHealth paper: Zhao et al. (2021), arXiv](https://arxiv.org/abs/2101.04209) — library design and benchmark tasks
- [MIMIC-III paper: Johnson et al. (2016), Nature Scientific Data](https://doi.org/10.1038/sdata.2016.35) — dataset description
- [MIMIC-IV paper: Johnson et al. (2023), Nature Scientific Data](https://doi.org/10.1038/s41597-022-01899-x) — updated dataset
- [RETAIN paper: Choi et al. (2016), NeurIPS](https://arxiv.org/abs/1608.05745) — interpretable clinical prediction model
- [PyHealth GitHub](https://github.com/sunlabuiuc/PyHealth) — source code and examples
