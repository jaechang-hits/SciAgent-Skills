# TDC Oracles & Data Processing Utilities

Consolidated reference for molecular oracles (scoring functions for molecule generation) and data processing utilities (splits, evaluation, format conversion, filtering).

## Molecular Oracles

Oracles evaluate generated molecules across specific property dimensions. Used for goal-directed generation and distribution learning benchmarks.

### Basic Usage

```python
from tdc import Oracle

# Single molecule
oracle = Oracle(name='GSK3B')
score = oracle('CC(C)Cc1ccc(cc1)C(C)C(O)=O')

# Batch evaluation (faster than individual calls)
scores = oracle(['SMILES1', 'SMILES2', 'SMILES3'])
```

### Complete Oracle Catalog

#### Biochemical Oracles — Target-Specific Binding Predictors

| Oracle | Target | Therapeutic Area | Output |
|--------|--------|-----------------|--------|
| `DRD2` | Dopamine Receptor D2 | Neurological/psychiatric | 0-1 (binding probability) |
| `GSK3B` | Glycogen Synthase Kinase-3 Beta | Alzheimer's, diabetes, cancer | 0-1 (inhibition probability) |
| `JNK3` | c-Jun N-terminal Kinase 3 | Neurodegeneration | 0-1 (inhibition probability) |
| `5HT2A` | Serotonin 2A Receptor | Psychiatric | 0-1 (binding probability) |
| `ACE` | Angiotensin-Converting Enzyme | Hypertension | 0-1 (inhibition probability) |
| `MAPK` | Mitogen-Activated Protein Kinase | Cancer, inflammation | 0-1 (inhibition probability) |
| `CDK` | Cyclin-Dependent Kinase | Cancer | 0-1 (inhibition probability) |
| `P38` | p38 MAP Kinase | Inflammation | 0-1 (inhibition probability) |
| `PARP1` | Poly (ADP-ribose) Polymerase 1 | Cancer (DNA repair) | 0-1 (inhibition probability) |
| `PIK3CA` | PI3K Catalytic Alpha | Oncology | 0-1 (inhibition probability) |

All biochemical oracles are ML-based predictors (medium speed). Higher scores indicate stronger binding/inhibition.

#### Physicochemical Oracles — Drug-Likeness and Properties

| Oracle | Property | Output Range | Interpretation |
|--------|----------|-------------|----------------|
| `QED` | Quantitative Estimate of Drug-likeness | 0-1 | Higher = more drug-like |
| `SA` | Synthetic Accessibility | 1-10 | Lower = easier to synthesize |
| `LogP` | Octanol-Water Partition (lipophilicity) | ~-3 to 8 | Drug-like range: 0-5 |
| `MW` | Molecular Weight | ~50-1000 Da | Drug-like range: 150-500 |
| `Lipinski` | Rule of Five violations | 0-4 | 0 = fully compliant |

Physicochemical oracles are rule-based calculations (fast speed).

**Lipinski Rules**: MW <= 500, logP <= 5, HBD <= 5, HBA <= 10.

#### Composite Oracles — Multi-Property and Benchmark

| Oracle | Purpose | Output |
|--------|---------|--------|
| `Isomer_Meta` | Isomeric/stereochemistry optimization | 0-1 combined |
| `Median1` / `Median2` | Generate molecules with median properties | 0-1 |
| `Rediscovery` | Similarity to known reference drugs | 0-1 |
| `Similarity` | Structural similarity (Tanimoto fingerprint) | 0-1 |
| `Uniqueness` | Fraction of unique molecules in set | 0-1 |
| `Novelty` | Difference from training set molecules | 0-1 |

#### Specialized Oracles — External Software Required

| Oracle | Method | Requirements | Output |
|--------|--------|-------------|--------|
| `ASKCOS` | Retrosynthesis scoring | ASKCOS backend (IBM RXN) | Route availability score |
| `Docking` | Molecular docking | Protein structure + docking software | Lower = better binding |
| `Vina` | AutoDock Vina docking | AutoDock Vina installation | kcal/mol (more negative = stronger) |

Specialized oracles are slow (external computation required).

### Speed Tiers Summary

| Tier | Oracles | Typical Latency |
|------|---------|----------------|
| **Fast** | QED, SA, LogP, MW, Lipinski | <1 ms/molecule |
| **Medium** | DRD2, GSK3B, JNK3, 5HT2A, ACE, MAPK, CDK, P38, PARP1, PIK3CA | ~10-100 ms/molecule |
| **Slow** | Docking, Vina, ASKCOS | Seconds to minutes/molecule |

### Custom Oracle Template

```python
class CustomOracle:
    def __init__(self):
        # Initialize your model/scoring method
        self.model = load_your_model()

    def __call__(self, smiles):
        if isinstance(smiles, list):
            return [self._score(s) for s in smiles]
        return self._score(smiles)

    def _score(self, smiles):
        # Implement scoring logic, return float
        return self.model.predict(smiles)

# Use like built-in oracles
custom_oracle = CustomOracle()
score = custom_oracle('CC(C)Cc1ccc(cc1)C(C)C(O)=O')
scores = custom_oracle(['SMILES1', 'SMILES2'])
```

### Multi-Objective Optimization Patterns

#### Weighted Combination

```python
from tdc import Oracle

qed_oracle = Oracle(name='QED')
sa_oracle = Oracle(name='SA')
drd2_oracle = Oracle(name='DRD2')

def multi_objective_score(smiles):
    qed = qed_oracle(smiles)
    sa = 1 / (1 + sa_oracle(smiles))  # Invert SA (lower is better)
    drd2 = drd2_oracle(smiles)
    return 0.3 * qed + 0.3 * sa + 0.4 * drd2

score = multi_objective_score('CC(C)Cc1ccc(cc1)C(C)C(O)=O')
```

#### Constraint Satisfaction

```python
from tdc import Oracle

constraints = {
    'QED': (Oracle(name='QED'), 0.5, 1.0),     # (oracle, min, max)
    'SA': (Oracle(name='SA'), 1.0, 4.0),
    'LogP': (Oracle(name='LogP'), -0.5, 5.0),
}

def check_constraints(smiles):
    all_pass = True
    for name, (oracle, lo, hi) in constraints.items():
        score = oracle(smiles)
        passed = lo <= score <= hi
        all_pass = all_pass and passed
        print(f"{name}: {score:.3f} [{'PASS' if passed else 'FAIL'}]")
    return all_pass
```

### Oracle Reliability Notes

- Oracles are ML model predictions, not experimental measurements — always validate top candidates experimentally
- May not generalize to all chemical spaces — use multiple oracles for cross-validation
- Some oracles require additional dependencies or API access (Docking, Vina, ASKCOS)

---

## Data Processing Utilities

### Format Conversion — MolConvert

Convert between ~15 molecular representations.

```python
from tdc.chem_utils import MolConvert

# SMILES to various targets
converter = MolConvert(src='SMILES', dst='PyG')
pyg_graph = converter('CC(C)Cc1ccc(cc1)C(C)C(O)=O')

# Batch conversion
converter = MolConvert(src='SMILES', dst='ECFP')
fingerprints = converter(['SMILES1', 'SMILES2', 'SMILES3'])
```

**Available Format Targets:**

| Category | Formats | Description |
|----------|---------|-------------|
| Text | SMILES, SELFIES, InChI | String representations |
| Fingerprints | ECFP (Morgan), MACCS, RDKit, AtomPair, TopologicalTorsion | Binary/count vectors |
| Graphs | PyG (PyTorch Geometric), DGL (Deep Graph Library) | Graph objects |
| 3D | Graph3D, Coulomb Matrix, Distance Matrix | 3D structure-based |

### Molecule Filters — MolFilter

Remove non-drug-like or problematic compounds using curated chemical rules.

```python
from tdc.chem_utils import MolFilter

mol_filter = MolFilter(
    rules=['PAINS', 'BMS'],
    property_filters_dict={
        'MW': (150, 500),
        'LogP': (-0.4, 5.6),
        'HBD': (0, 5),
        'HBA': (0, 10),
    }
)
filtered_smiles = mol_filter(smiles_list)
```

**Available Filter Rules:**

| Rule | Source | Description |
|------|--------|-------------|
| `PAINS` | Pan-Assay Interference Compounds | Frequent-hitter substructures |
| `BMS` | Bristol-Myers Squibb | HTS deck filters |
| `Glaxo` | GlaxoSmithKline | Medicinal chemistry filters |
| `Dundee` | University of Dundee | Academic compound filters |
| `Inpharmatica` | Inpharmatica | Property-based filters |
| `LINT` | Pfizer | LINT filter set |

### Label Transforms

#### Binarization

```python
from tdc.utils import binarize

binary_labels = binarize(y_continuous, threshold=5.0, order='ascending')
# order='ascending': values >= threshold become 1
# order='descending': values <= threshold become 1
```

#### Unit Conversion

```python
from tdc.chem_utils import label_transform

y_pkd = label_transform(y_nM, from_unit='nM', to_unit='p')   # nM to pKd
y_nM = label_transform(y_uM, from_unit='uM', to_unit='nM')   # uM to nM
```

**Available conversions**: nM, uM, pKd, pKi, pIC50, log transformations.

#### Label Meaning

```python
label_map = data.get_label_map(name='DrugBank')
# {0: 'No interaction', 1: 'Increased effect', 2: 'Decreased effect', ...}
```

### Entity Resolution

Convert between database identifiers for cross-referencing.

```python
from tdc.utils import cid2smiles, uniprot2seq

# PubChem CID to SMILES
smiles = cid2smiles(2244)  # Aspirin → 'CC(=O)Oc1ccccc1C(=O)O'

# UniProt ID to amino acid sequence
sequence = uniprot2seq('P12345')  # → 'MVKVYAPASS...'

# Batch retrieval
smiles_list = [cid2smiles(cid) for cid in [2244, 5090, 6323]]
sequences = [uniprot2seq(uid) for uid in ['P12345', 'Q9Y5S9']]
```

### Data Balancing, Negative Sampling, and Graph Transformation

```python
from tdc.utils import balance, negative_sample, create_graph_from_pairs

# Class balancing
X_bal, y_bal = balance(X, y, method='oversample')    # or 'undersample'

# Negative sampling for interaction prediction
neg_pairs = negative_sample(
    positive_pairs=known_interactions,
    all_drugs=drug_list, all_targets=target_list, ratio=1.0
)

# Convert pair data to graph
graph = create_graph_from_pairs(pairs=ddi_pairs, format='edge_list')  # or 'PyG', 'DGL'
```

---

## Split Strategies — Detailed Comparison

| Method | Mechanism | Use Case | Difficulty |
|--------|-----------|----------|-----------|
| `random` | Random shuffling | Baseline evaluation, prototyping | Easiest (inflated metrics) |
| `scaffold` | Bemis-Murcko scaffold grouping | Default for molecular property prediction | Moderate |
| `cold_drug` | Unseen drugs in test set | DTI generalization to new compounds | Hard |
| `cold_target` | Unseen targets in test set | DTI generalization to new proteins | Hard |
| `cold_drug_target` | Novel drug-target pairs | Most challenging DTI evaluation | Hardest |
| `temporal` | Time-based partitioning | Prospective prediction, clinical trials | Varies |

### Split API

```python
# Scaffold split (single-instance tasks)
split = data.get_split(method='scaffold', seed=42, frac=[0.7, 0.1, 0.2])
# Returns: {'train': DataFrame, 'valid': DataFrame, 'test': DataFrame}

# Cold splits (multi-instance tasks)
from tdc.multi_pred import DTI
data = DTI(name='BindingDB_Kd')
split = data.get_split(method='cold_drug', seed=1)

# Stratified split (preserves label distribution for imbalanced classes)
split = data.get_split(method='scaffold', stratified=True)
```

### Scaffold Split Mechanism

1. Extract Bemis-Murcko scaffold from each molecule (requires RDKit)
2. Group molecules by scaffold identity
3. Assign entire scaffold groups to train/valid/test — test molecules have scaffolds never seen during training

### Cold Split Verification and Cross-Validation

```python
# Verify no entity leakage in cold splits
train_drugs = set(split['train']['Drug_ID'])
test_drugs = set(split['test']['Drug_ID'])
assert len(train_drugs & test_drugs) == 0, "Drug leakage detected!"

# K-fold cross-validation
from tdc.utils import create_fold
folds = create_fold(data, fold=5, seed=42)
# Returns list of (train_idx, test_idx) tuples
```

---

## Evaluation Metrics — Detailed Comparison

### Classification Metrics

| Metric | API Name | Input | Range | Best For |
|--------|----------|-------|-------|----------|
| ROC-AUC | `ROC-AUC` | y_true, y_pred_proba | 0-1 (higher better, 0.5=random) | Binary, imbalanced data |
| PR-AUC | `PR-AUC` | y_true, y_pred_proba | 0-1 (higher better) | Highly imbalanced, rare positive |
| F1 | `F1` | y_true, y_pred_binary | 0-1 (higher better) | Precision-recall balance |
| Accuracy | `Accuracy` | y_true, y_pred_binary | 0-1 (higher better) | Balanced datasets only |
| Cohen's Kappa | `Kappa` | y_true, y_pred_binary | -1 to 1 (higher better) | Chance-corrected agreement |

### Regression Metrics

| Metric | API Name | Input | Range | Best For |
|--------|----------|-------|-------|----------|
| RMSE | `RMSE` | y_true, y_pred | 0-inf (lower better) | Penalize large errors |
| MAE | `MAE` | y_true, y_pred | 0-inf (lower better) | Robust to outliers |
| R-squared | `R2` | y_true, y_pred | -inf to 1 (higher better) | Variance explained |
| MSE | `MSE` | y_true, y_pred | 0-inf (lower better) | Raw squared error |

### Ranking Metrics

| Metric | API Name | Range | Best For |
|--------|----------|-------|----------|
| Spearman | `Spearman` | -1 to 1 (higher better) | Rank correlation, non-linear |
| Pearson | `Pearson` | -1 to 1 (higher better) | Linear correlation |

### Multi-Label Metrics

Available: `Micro-F1`, `Macro-F1`, `Micro-AUPR`, `Macro-AUPR`.

### Evaluator API

```python
from tdc import Evaluator

evaluator = Evaluator(name='MAE')
score = evaluator(y_true, y_pred)
```

Benchmark group 5-seed evaluation protocol: see SKILL.md Core API Module 5.

---

## Best Practices for Splits and Evaluation

1. **Always use scaffold splits** for molecular property prediction — random splits leak structural information and produce artificially inflated metrics

2. **Use cold splits for interaction tasks** — `cold_drug` tests generalization to new compounds; `cold_target` to unseen proteins; `cold_drug_target` is the most realistic but hardest setting

3. **Report 5-seed evaluations** with mean +/- std — single-seed results are unreliable for method comparison. Use seeds 1-5 for benchmark comparability

4. **Choose metrics matching your task**:
   - Binary classification → ROC-AUC (general) or PR-AUC (imbalanced)
   - Regression → MAE (robust) or RMSE (penalize outliers)
   - Ranking → Spearman correlation
   - Never use Accuracy for imbalanced datasets

5. **Filter molecules before training** — apply PAINS and drug-likeness filters early in the pipeline to remove problematic compounds

6. **Normalize oracle outputs before combining** — QED is 0-1, SA is 1-10 (invert), binding scores vary. Always check oracle documentation

7. **Cache dataset downloads** — specify a persistent `path` argument to avoid re-downloading across sessions

8. **Convert molecules in batch** — use list inputs for both `MolConvert` and `Oracle` for significantly faster processing

---

**Condensation note**: Consolidated from original `oracles.md` (401 lines) + `utilities.md` (685 lines) = 1,086 lines into ~400 lines (~37% retention, meeting multi-file consolidation floor).

**Retained from oracles.md**: All 17+ oracle entries with categories, output ranges, and speed tiers; custom oracle template; multi-objective optimization patterns (weighted combination, constraint satisfaction); goal-directed generation workflow; batch processing guidance; reliability notes.

**Retained from utilities.md**: MolConvert format targets table; MolFilter rules catalog; label binarization and unit conversion; entity resolution (cid2smiles, uniprot2seq); data balancing; negative sampling; graph transformation; all split methods with mechanisms; all evaluation metrics with ranges and use cases; benchmark group evaluation protocol; cross-validation folds; best practices.

**Relocated inline to SKILL.md**: Quick Start oracle usage (Core API Module 3); top split methods and evaluation metrics summary (Core API Module 4); MolConvert basic pattern (Recipe 2); constraint satisfaction pattern (Recipe 3); benchmark 5-seed protocol (Core API Module 5); data format options (Key Parameters).

**Omitted from oracles.md**: Per-oracle individual code blocks showing `oracle = Oracle(name='X'); score = oracle(smiles)` — repetitive pattern; replaced with catalog table plus single usage example. Distribution learning KS-test comparison example — niche statistical use case. GuacaMol integration example (`evaluate_guacamol`) — incomplete API, platform-specific.

**Omitted from utilities.md**: Complete data pipeline workflow (Workflow 1) — largely duplicates SKILL.md Workflow 1. Multi-task learning preparation workflow (Workflow 2) — thin wrapper around benchmark group. DTI cold split workflow (Workflow 3) — covered inline in SKILL.md Module 4. Fuzzy search examples — trivial feature. Data format options (`get_data(format=...)`) — covered in SKILL.md Key Parameters. `retrieve_dataset_names` usage — covered in datasets_catalog.md. Performance tips — generic advice (batch mode, caching) consolidated into Best Practices. Label distribution visualization (`label_distribution()`, `print_stats()`) — covered in SKILL.md Recipe 1.
