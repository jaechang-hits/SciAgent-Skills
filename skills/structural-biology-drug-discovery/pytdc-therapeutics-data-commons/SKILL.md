---
name: pytdc-therapeutics-data-commons
description: >
  Therapeutics Data Commons (TDC) — AI-ready drug discovery dataset platform.
  Access curated ADME, toxicity, DTI, DDI datasets with scaffold/cold splits,
  standardized evaluation metrics, molecular oracles for optimization, and
  ADMET benchmark groups. Use for therapeutic ML model training, benchmarking,
  and molecular property prediction. For chemical database queries use
  chembl-database-bioactivity; for molecular featurization use molfeat.
license: MIT
---

# PyTDC (Therapeutics Data Commons)

## Overview

PyTDC is an open-science platform providing AI-ready datasets and benchmarks for drug discovery. It organizes therapeutics data into three categories: single-instance prediction (molecular/protein properties), multi-instance prediction (drug-target interactions), and generation (molecule design, retrosynthesis). All datasets come with standardized splits, evaluation metrics, and molecular oracles.

## When to Use

- Loading curated ADME, toxicity, or bioactivity datasets for ML model training
- Benchmarking drug discovery models with standardized 5-seed evaluation protocols
- Predicting drug-target or drug-drug interactions with proper cold-split evaluation
- Generating novel molecules and scoring them with molecular oracles (QED, SA, DRD2, GSK3B)
- Accessing scaffold-based or temporal train/test splits for pharmaceutical ML
- Converting molecular representations (SMILES to PyG graphs, ECFP fingerprints, SELFIES)
- For chemical database queries (compound search, bioactivity), use `chembl-database-bioactivity` instead
- For molecular featurization beyond format conversion, use `molfeat` instead

## Prerequisites

```bash
uv pip install PyTDC
# Core deps: numpy, pandas, scikit-learn, tqdm, fuzzywuzzy
# Optional: rdkit (scaffold splits), torch-geometric (PyG conversion)
```

**API Note**: TDC downloads datasets on first access (~10-500 MB per dataset). Specify `path='data/'` to control download location. No API key required.

## Quick Start

```python
from tdc.single_pred import ADME
from tdc import Evaluator

# Load dataset with scaffold split
data = ADME(name='Caco2_Wang')
split = data.get_split(method='scaffold', seed=42, frac=[0.7, 0.1, 0.2])
train, valid, test = split['train'], split['valid'], split['test']
print(f"Train: {len(train)}, Valid: {len(valid)}, Test: {len(test)}")
# Train: ~640, Valid: ~91, Test: ~182

# Evaluate predictions
evaluator = Evaluator(name='MAE')
# score = evaluator(test['Y'].values, predictions)
```

## Core API

### Module 1: Single-Instance Prediction — Dataset Access

Load datasets for predicting properties of individual molecules or proteins.

```python
from tdc.single_pred import ADME, Tox, HTS, QM

# ADME — pharmacokinetic properties
data = ADME(name='Caco2_Wang')       # Intestinal permeability (regression)
data = ADME(name='BBB_Martins')       # Blood-brain barrier (binary)
data = ADME(name='Lipophilicity_AstraZeneca')  # LogD (regression)
data = ADME(name='Solubility_AqSolDB')         # Aqueous solubility

# Toxicity — adverse effects
data = Tox(name='hERG')              # Cardiotoxicity (binary)
data = Tox(name='AMES')              # Mutagenicity (binary)
data = Tox(name='DILI')              # Drug-induced liver injury
data = Tox(name='ClinTox')           # Clinical trial toxicity

# Access data as DataFrame
df = data.get_data(format='df')
print(df.columns.tolist())
# ['Drug_ID', 'Drug', 'Y'] — Drug is SMILES, Y is target label
print(f"Dataset size: {len(df)}, Label range: [{df['Y'].min():.2f}, {df['Y'].max():.2f}]")
```

Other single-prediction tasks: `HTS` (screening), `QM` (quantum mechanics), `Yields`, `Epitope`, `Develop`, `CRISPROutcome`.

### Module 2: Multi-Instance Prediction — Interaction Datasets

Load datasets for predicting interactions between pairs of biomedical entities.

```python
from tdc.multi_pred import DTI, DDI, PPI

# Drug-Target Interaction — binding affinity
data = DTI(name='BindingDB_Kd')      # 52,284 pairs, Kd values
data = DTI(name='DAVIS')             # 30,056 pairs, kinase binding
data = DTI(name='KIBA')              # 118,254 pairs, kinase bioactivity

# Drug-Drug Interaction — interaction type prediction
data = DDI(name='DrugBank')           # 191,808 pairs, 86 interaction types

# Protein-Protein Interaction
data = PPI(name='HuRI')

# Multi-instance data format
df = data.get_data(format='df')
print(df.columns.tolist())
# ['Drug_ID', 'Drug', 'Target_ID', 'Target', 'Y']
# Drug=SMILES, Target=protein sequence, Y=binding affinity or class
```

Other multi-instance tasks: `GDA`, `DrugRes`, `DrugSyn`, `PeptideMHC`, `AntibodyAff`, `MTI`, `Catalyst`, `TrialOutcome`.

### Module 3: Generation Tasks — Molecular Design

Load training sets and oracles for molecule generation and retrosynthesis.

```python
from tdc.generation import MolGen, RetroSyn, PairMolGen
from tdc import Oracle

# Molecule generation — training data
data = MolGen(name='ChEMBL_V29')     # 1.6M drug-like SMILES
split = data.get_split()
train_smiles = split['train']['Drug'].tolist()

# Oracle scoring — evaluate generated molecules
oracle = Oracle(name='GSK3B')         # GSK3B inhibition predictor (0-1)
score = oracle('CC(C)Cc1ccc(cc1)C(C)C(O)=O')
print(f"GSK3B score: {score:.4f}")

# Batch evaluation
scores = oracle(['CCO', 'c1ccccc1', 'CC(=O)O'])
print(f"Batch scores: {scores}")

# Retrosynthesis — reaction prediction
data = RetroSyn(name='USPTO')         # 1.9M reactions
split = data.get_split()

# Paired generation — prodrug design
data = PairMolGen(name='Prodrug')
```

### Module 4: Data Splits and Evaluation

Apply meaningful data splits and standardized evaluation metrics.

```python
from tdc.single_pred import ADME
from tdc.multi_pred import DTI
from tdc import Evaluator

# Scaffold split — ensures chemical diversity between sets
data = ADME(name='Caco2_Wang')
split = data.get_split(method='scaffold', seed=42, frac=[0.7, 0.1, 0.2])

# Cold splits — for DTI (unseen drugs/targets in test set)
data = DTI(name='BindingDB_Kd')
cold_drug = data.get_split(method='cold_drug', seed=1)
cold_target = data.get_split(method='cold_target', seed=1)

# Verify no overlap in cold split
train_drugs = set(cold_drug['train']['Drug_ID'])
test_drugs = set(cold_drug['test']['Drug_ID'])
print(f"Drug overlap: {len(train_drugs & test_drugs)}")  # 0

# Evaluation metrics
eval_mae = Evaluator(name='MAE')
eval_auc = Evaluator(name='ROC-AUC')
eval_spearman = Evaluator(name='Spearman')
# score = eval_mae(y_true, y_pred)
```

**Available split methods**: `random`, `scaffold` (Bemis-Murcko), `cold_drug`, `cold_target`, `cold_drug_target`, `temporal`.

**Available metrics**: Classification — `ROC-AUC`, `PR-AUC`, `F1`, `Accuracy`, `Kappa`. Regression — `RMSE`, `MAE`, `R2`, `MSE`. Ranking — `Spearman`, `Pearson`. Multi-label — `Micro-F1`, `Macro-F1`.

### Module 5: Benchmark Groups

Run standardized multi-seed evaluation protocols for model comparison.

```python
from tdc.benchmark_group import admet_group

# Load ADMET benchmark (22 datasets)
group = admet_group(path='data/')

# Standard 5-seed evaluation protocol
benchmark = group.get('Caco2_Wang')
predictions = {}

for seed in [1, 2, 3, 4, 5]:
    train_df = benchmark['train']
    valid_df = benchmark['valid']
    test_df = benchmark['test']
    # Train your model on train_df, tune on valid_df
    # predictions[seed] = model.predict(test_df['Drug'])
    predictions[seed] = test_df['Y'].values  # placeholder

# Get benchmark results
results = group.evaluate(predictions)
print(f"Mean MAE: {results['Caco2_Wang'][0]:.4f} ± {results['Caco2_Wang'][1]:.4f}")
```

## Key Concepts

### Dataset Organization

| Category | Import Path | Task Examples | Data Format |
|----------|-------------|---------------|-------------|
| Single-Instance | `tdc.single_pred` | ADME, Tox, HTS, QM | Drug (SMILES) + Y (label) |
| Multi-Instance | `tdc.multi_pred` | DTI, DDI, PPI, DrugSyn | Drug + Target + Y |
| Generation | `tdc.generation` | MolGen, RetroSyn | SMILES collections |
| Benchmark | `tdc.benchmark_group` | admet_group | Curated splits |

### Oracle Categories

| Category | Examples | Speed | Output Range |
|----------|----------|-------|-------------|
| Biochemical | DRD2, GSK3B, JNK3, 5HT2A | Medium (ML) | 0-1 probability |
| Physicochemical | QED, SA, LogP, MW | Fast (rule-based) | Varies by metric |
| Composite | Isomer_Meta, Median1/2, Rediscovery | Medium | 0-1 combined |
| Specialized | ASKCOS, Docking, Vina | Slow (external) | Varies |

### Data Processing Utilities

| Utility | Function | Example |
|---------|----------|---------|
| Format conversion | `MolConvert(src, dst)` | SMILES → PyG, ECFP, SELFIES, DGL |
| Molecule filters | `MolFilter(filters)` | PAINS, BMS, Glaxo, drug-likeness |
| Label binarization | `label_transform()` | Continuous → binary at threshold |
| Unit conversion | `label_transform(from_unit, to_unit)` | nM → pIC50 |
| ID resolution | `cid2smiles()`, `uniprot2seq()` | PubChem CID → SMILES |
| Dataset listing | `retrieve_dataset_names(task)` | List all ADME datasets |

## Common Workflows

### Workflow 1: Multi-Seed ADME Model Evaluation

```python
from tdc.single_pred import ADME
from tdc import Evaluator
import numpy as np

data = ADME(name='Caco2_Wang')
evaluator = Evaluator(name='MAE')

results = []
for seed in [1, 2, 3, 4, 5]:
    split = data.get_split(method='scaffold', seed=seed)
    train, valid, test = split['train'], split['valid'], split['test']
    # model.fit(train['Drug'], train['Y'])
    # preds = model.predict(test['Drug'])
    preds = test['Y'].values + np.random.normal(0, 0.1, len(test))  # placeholder
    score = evaluator(test['Y'].values, preds)
    results.append(score)
    print(f"Seed {seed}: MAE = {score:.4f}")

print(f"Mean MAE: {np.mean(results):.4f} ± {np.std(results):.4f}")
```

### Workflow 2: Multi-Objective Molecular Scoring

```python
from tdc import Oracle
import numpy as np

# Define multi-objective scoring
oracles = {
    'QED': (Oracle(name='QED'), 0.3),      # drug-likeness
    'SA': (Oracle(name='SA'), 0.3),         # synthetic accessibility
    'GSK3B': (Oracle(name='GSK3B'), 0.4),   # target activity
}

test_smiles = ['CC(C)Cc1ccc(cc1)C(C)C(O)=O', 'c1ccc2c(c1)cc1ccc3cccc4ccc2c1c34']

for smi in test_smiles:
    scores = {}
    weighted_sum = 0
    for name, (oracle, weight) in oracles.items():
        score = oracle(smi)
        scores[name] = score
        weighted_sum += score * weight
    print(f"SMILES: {smi[:30]}...")
    print(f"  Scores: {scores}")
    print(f"  Weighted: {weighted_sum:.4f}")
```

### Workflow 3: Cold-Split DTI Evaluation (text-only)

1. Load DTI dataset — `DTI(name='BindingDB_Kd')` (Core API Module 2)
2. Apply cold_drug split — `data.get_split(method='cold_drug', seed=seed)` (Core API Module 4)
3. Verify zero drug overlap between train and test sets (Module 4 overlap check)
4. Train model on train set, predict on test set
5. Evaluate with Spearman correlation — `Evaluator(name='Spearman')` (Module 4)
6. Repeat for 5 seeds and report mean ± std (same pattern as Workflow 1)

## Key Parameters

| Parameter | Function/Module | Default | Range/Options | Effect |
|-----------|----------------|---------|---------------|--------|
| `method` | `get_split()` | `'scaffold'` | `random`, `scaffold`, `cold_drug`, `cold_target`, `temporal` | Split strategy for train/test |
| `seed` | `get_split()` | `42` | 1-5 for benchmarks | Reproducibility; use 5 seeds for benchmarks |
| `frac` | `get_split()` | `[0.7, 0.1, 0.2]` | Sum must equal 1.0 | Train/valid/test proportions |
| `name` | `Evaluator()` | — | `MAE`, `RMSE`, `ROC-AUC`, `Spearman`, etc. | Evaluation metric |
| `name` | `Oracle()` | — | `QED`, `SA`, `GSK3B`, `DRD2`, etc. | Scoring function for molecules |
| `src`/`dst` | `MolConvert()` | — | `SMILES`, `SELFIES`, `PyG`, `DGL`, `ECFP4` | Molecular representation formats |
| `path` | `admet_group()` | `'data/'` | Any directory | Dataset download/cache location |
| `format` | `get_data()` | `'df'` | `'df'`, `'dict'` | Output data format |

## Best Practices

1. **Always use scaffold splits** for molecular property prediction — random splits leak structural information and inflate performance metrics
2. **Report 5-seed evaluations** with mean ± std — single-seed results are unreliable for method comparison
3. **Use cold splits for interaction prediction** — `cold_drug` tests generalization to unseen drugs, `cold_target` to unseen targets
4. **Filter molecules early** with `MolFilter` (PAINS, drug-likeness) before training to remove problematic compounds
5. **Normalize oracles appropriately** — QED returns 0-1, SA returns 1-10 (lower is better), binding scores vary. Check oracle documentation before combining
6. **Cache datasets** by specifying a persistent `path` — avoids re-downloading large datasets across sessions

## Common Recipes

### Recipe 1: Dataset Exploration and Statistics

```python
from tdc.single_pred import ADME
from tdc.utils import retrieve_dataset_names

# List all ADME datasets
datasets = retrieve_dataset_names('ADME')
print(f"Available ADME datasets: {datasets}")

# Load and inspect
data = ADME(name='Caco2_Wang')
df = data.get_data(format='df')
print(f"Size: {len(df)}")
print(f"Label stats: mean={df['Y'].mean():.2f}, std={df['Y'].std():.2f}")
print(f"SMILES example: {df['Drug'].iloc[0]}")
```

### Recipe 2: Molecule Format Conversion Pipeline

```python
from tdc.chem_utils import MolConvert

# SMILES to multiple representations
smiles = 'CC(C)Cc1ccc(cc1)C(C)C(O)=O'

converter_ecfp = MolConvert(src='SMILES', dst='ECFP4')
converter_selfies = MolConvert(src='SMILES', dst='SELFIES')

ecfp = converter_ecfp(smiles)
selfies = converter_selfies(smiles)
print(f"ECFP4 shape: {ecfp.shape}")    # (1024,) binary fingerprint
print(f"SELFIES: {selfies}")
```

### Recipe 3: Custom Oracle with Constraint Satisfaction

```python
from tdc import Oracle

# Define property constraints
constraints = {
    'QED': (Oracle(name='QED'), 0.5, 1.0),       # min, max
    'SA': (Oracle(name='SA'), 1.0, 4.0),
    'LogP': (Oracle(name='LogP'), -0.5, 5.0),
}

def check_constraints(smiles):
    """Check if molecule satisfies all property constraints."""
    results = {}
    all_pass = True
    for name, (oracle, lo, hi) in constraints.items():
        score = oracle(smiles)
        passed = lo <= score <= hi
        results[name] = {'score': score, 'passed': passed}
        all_pass = all_pass and passed
    return all_pass, results

passed, details = check_constraints('CC(C)Cc1ccc(cc1)C(C)C(O)=O')
for name, info in details.items():
    status = "PASS" if info['passed'] else "FAIL"
    print(f"{name}: {info['score']:.3f} [{status}]")
```

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| `ModuleNotFoundError: tdc` | Package not installed | `uv pip install PyTDC` |
| Scaffold split fails | Missing RDKit dependency | `uv pip install rdkit` for scaffold decomposition |
| Dataset download timeout | Large dataset or slow connection | Set `path='data/'` for persistent cache; retry |
| `KeyError` on dataset name | Wrong name or task category | Use `retrieve_dataset_names('ADME')` to list valid names |
| Oracle returns NaN | Invalid SMILES or RDKit parse failure | Validate SMILES with RDKit `MolFromSmiles()` first |
| Cold split empty test set | Too few unique entities | Use `frac=[0.7, 0.1, 0.2]` with larger datasets |
| Benchmark evaluation error | Wrong prediction format | Pass `dict` with seeds as keys: `{1: preds1, 2: preds2, ...}` |
| Memory error on large dataset | Full dataset loaded to memory | Process in chunks or use smaller split fractions |
| PyG conversion fails | torch-geometric not installed | `uv pip install torch-geometric` for graph conversion |

## Bundled Resources

### references/datasets_catalog.md
Covers: complete catalog of all TDC datasets organized by task category (single-instance, multi-instance, generation) with dataset names, sizes, label types, and data sources. Relocated inline: top ADME/Tox/DTI datasets with code examples consolidated into Core API Modules 1-2. Omitted: None — all dataset entries preserved in catalog format.

### references/oracles_utilities.md
Covers: detailed oracle documentation (all 17+ oracles with parameters, speed tiers, output ranges, custom oracle template) and data processing utilities (format conversion targets, molecule filter types, label transformation, entity resolution). Consolidated from original `oracles.md` + `utilities.md`. Relocated inline: Quick Start oracle usage pattern, top evaluation metrics, split methods, MolConvert pattern → Core API Modules 3-4. Omitted: distribution learning KS-test example — niche statistical comparison; leaderboard submission guide — platform-specific.

### Script Disposition
- `load_and_split_data.py` (215 lines): scaffold/cold split patterns → Core API Module 4; custom split fractions → Key Parameters; evaluation examples → Workflow 1. Thin wrappers around `get_split()` and `Evaluator()`.
- `benchmark_evaluation.py` (328 lines): 5-seed protocol → Core API Module 5 + Workflow 1; multi-dataset evaluation → Workflow 1 pattern; leaderboard guide → omitted (platform-specific).
- `molecular_generation.py` (405 lines): single/batch oracle usage → Core API Module 3; multi-objective scoring → Workflow 2; constraint satisfaction → Recipe 3; distribution learning → omitted (niche).

## Related Skills

- **chembl-database-bioactivity** — for querying ChEMBL compound/target/activity data directly
- **molfeat** — for advanced molecular featurization beyond TDC's built-in MolConvert
- **rdkit-cheminformatics** — for molecular manipulation, substructure search, descriptor calculation

## References

- TDC Official Website: https://tdcommons.ai
- TDC Documentation: https://tdc.readthedocs.io
- GitHub Repository: https://github.com/mims-harvard/TDC
- Huang et al. "Therapeutics Data Commons" NeurIPS 2021 Datasets and Benchmarks
