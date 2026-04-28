---
name: deepchem
description: "Deep learning for drug discovery. 60+ models (GCN, GAT, AttentiveFP, MPNN, ChemBERTa, GROVER), 50+ featurizers, MoleculeNet benchmarks, HPO, transfer learning. Unified load-featurize-split-train-evaluate API. For fingerprints use rdkit-cheminformatics; for featurization-only use molfeat."
license: MIT
---

# DeepChem — Deep Learning for Drug Discovery

## Overview

DeepChem is an open-source Python framework providing a unified API for molecular machine learning across drug discovery, materials science, and quantum chemistry. It wraps 60+ model architectures (graph neural networks, transformers, classical ML) with 50+ molecular featurizers and standardized datasets (MoleculeNet), enabling end-to-end workflows from SMILES strings to trained predictive models.

## When to Use

- Predicting molecular properties (solubility, toxicity, binding affinity) from SMILES
- Benchmarking models on MoleculeNet standardized datasets (BBBP, Tox21, ESOL, FreeSolv, etc.)
- Training graph neural networks on molecular graphs (GCN, GAT, AttentiveFP, MPNN, DMPNN)
- Fine-tuning pretrained chemical language models (ChemBERTa, GROVER, MolFormer)
- Running hyperparameter optimization for molecular ML models
- Virtual screening and hit prioritization with trained models
- Materials property prediction from crystal structures (CGCNN, MEGNet)
- Protein-ligand interaction modeling and binding affinity prediction
- For fingerprint-based cheminformatics without deep learning, use `rdkit-cheminformatics` instead
- For featurization only (no model training), use `molfeat-molecular-featurization` instead

## Prerequisites

- **Python packages**: `deepchem` (core), `torch` or `tensorflow` (backend-dependent models)
- **GPU**: Recommended for graph neural networks and transformer models; CPU sufficient for classical ML and fingerprint models
- **Data**: SMILES strings with property labels (CSV), or MoleculeNet datasets (auto-downloaded)

```bash
# Core installation (includes RDKit, scikit-learn, XGBoost)
pip install deepchem

# With PyTorch backend (GNN models)
pip install deepchem[torch]

# With TensorFlow backend (legacy models)
pip install deepchem[tensorflow]

# Full installation (all backends + extras)
pip install deepchem[all]
```

## Quick Start

```python
import deepchem as dc

# Load MoleculeNet dataset with featurization + scaffold split
tasks, datasets, transformers = dc.molnet.load_delaney(featurizer="ECFP")
train, valid, test = datasets

# Train and evaluate a multitask regressor
model = dc.models.MultitaskRegressor(n_tasks=1, n_features=1024, dropouts=0.2)
model.fit(train, nb_epoch=50)
metric = dc.metrics.Metric(dc.metrics.pearson_r2_score)
print(f"Test R2: {model.evaluate(test, [metric])}")  # {'pearson_r2_score': ~0.7}
```

## Core API

### Module 1: Data Loading and Processing

Load molecular data from CSV files or MoleculeNet benchmark datasets.

```python
import deepchem as dc

# Load from CSV (SMILES + property columns)
loader = dc.data.CSVLoader(
    tasks=["measured_log_solubility"],
    feature_field="smiles",
    featurizer=dc.feat.CircularFingerprint(size=2048, radius=3)
)
dataset = loader.create_dataset("solubility_data.csv")
print(f"Samples: {dataset.X.shape[0]}, Features: {dataset.X.shape[1]}")
# Samples: 1128, Features: 2048

# Load from SDF (3D structures)
sdf_loader = dc.data.SDFLoader(
    tasks=["activity"],
    featurizer=dc.feat.CoulombMatrix(max_atoms=50)
)
dataset_3d = sdf_loader.create_dataset("molecules.sdf")
```

```python
# Load MoleculeNet benchmark datasets (auto-download + featurize + split)
# Available: load_delaney, load_bbbp, load_tox21, load_hiv, load_qm7, load_qm9, etc.
tasks, datasets, transformers = dc.molnet.load_tox21(featurizer="ECFP", splitter="scaffold")
train, valid, test = datasets
print(f"Tasks: {len(tasks)}, Train: {len(train)}, Test: {len(test)}")
# Tasks: 12, Train: ~6264, Test: ~631

# Inverse-transform predictions back to original scale
y_pred = model.predict(test)
y_original = transformers[0].untransform(y_pred)
```

### Module 2: Molecular Featurization

Convert molecules to numerical representations for ML. DeepChem provides 50+ featurizers spanning fingerprints, descriptors, graph features, and Coulomb matrices.

```python
import deepchem as dc

smiles = ["CCO", "CC(=O)O", "c1ccccc1", "CC(C)O"]

# Fingerprints (most common for classical ML)
ecfp = dc.feat.CircularFingerprint(size=2048, radius=3)
fp_features = ecfp.featurize(smiles)
print(f"ECFP shape: {fp_features.shape}")  # (4, 2048)

# RDKit descriptors (interpretable physicochemical properties)
rdkit_desc = dc.feat.RDKitDescriptors()
desc_features = rdkit_desc.featurize(smiles)
print(f"Descriptor shape: {desc_features.shape}")  # (4, 208)

# Graph features (for GNN models — returns ConvMol objects)
graph_feat = dc.feat.ConvMolFeaturizer()
graphs = graph_feat.featurize(smiles)
print(f"Atoms in first mol: {graphs[0].get_num_atoms()}")  # 3

# Mol2Vec embeddings (pretrained word2vec on molecular substructures)
mol2vec = dc.feat.Mol2VecFingerprint()
embeddings = mol2vec.featurize(smiles)
print(f"Mol2Vec shape: {embeddings.shape}")  # (4, 300)
```

### Module 3: Model Training and Evaluation

DeepChem provides MultitaskRegressor and MultitaskClassifier as general-purpose models, plus specialized architectures for graph and sequence data.

```python
import deepchem as dc

# Load dataset
tasks, datasets, transformers = dc.molnet.load_delaney(featurizer="ECFP")
train, valid, test = datasets

# Regression model (fingerprint input)
model = dc.models.MultitaskRegressor(
    n_tasks=1,
    n_features=1024,
    layer_sizes=[1000, 500],
    dropouts=0.25,
    learning_rate=0.001,
    batch_size=64,
)
model.fit(train, nb_epoch=100)

# Evaluate with multiple metrics
metrics = [
    dc.metrics.Metric(dc.metrics.pearson_r2_score),
    dc.metrics.Metric(dc.metrics.mean_absolute_error),
    dc.metrics.Metric(dc.metrics.rms_score),
]
results = model.evaluate(test, metrics)
print(f"R2: {results['pearson_r2_score']:.3f}, MAE: {results['mean_absolute_error']:.3f}")
```

```python
# Classification model (e.g., Tox21 toxicity prediction)
tasks, datasets, transformers = dc.molnet.load_tox21(featurizer="ECFP")
train, valid, test = datasets

clf = dc.models.MultitaskClassifier(
    n_tasks=len(tasks),
    n_features=1024,
    layer_sizes=[1000, 500],
    dropouts=0.5,
    learning_rate=0.001,
)
clf.fit(train, nb_epoch=50)
roc_metric = dc.metrics.Metric(dc.metrics.roc_auc_score, np.mean)
print(f"Mean ROC-AUC: {clf.evaluate(test, [roc_metric])}")
```

### Module 4: Graph Neural Networks

GNNs operate directly on molecular graphs (atoms as nodes, bonds as edges), avoiding information loss from fixed fingerprints.

```python
import deepchem as dc

# Load with graph featurizer
tasks, datasets, transformers = dc.molnet.load_delaney(featurizer="GraphConv")
train, valid, test = datasets

# Graph Convolutional Network (Duvenaud et al.)
gcn_model = dc.models.GraphConvModel(
    n_tasks=1,
    mode="regression",
    graph_conv_layers=[64, 64],
    dense_layer_size=256,
    dropout=0.2,
    learning_rate=0.001,
    batch_size=64,
)
gcn_model.fit(train, nb_epoch=100)
metric = dc.metrics.Metric(dc.metrics.pearson_r2_score)
print(f"GCN R2: {gcn_model.evaluate(test, [metric])}")
```

```python
# AttentiveFP (Xiong et al.) — attention-based GNN, strong on molecular properties
tasks, datasets, transformers = dc.molnet.load_delaney(
    featurizer=dc.feat.MolGraphConvFeaturizer(use_edges=True)
)
train, valid, test = datasets

attfp_model = dc.models.AttentiveFPModel(
    n_tasks=1,
    mode="regression",
    num_layers=2,
    graph_feat_size=200,
    num_timesteps=2,
    dropout=0.2,
    learning_rate=0.001,
    batch_size=64,
)
attfp_model.fit(train, nb_epoch=100)
print(f"AttentiveFP R2: {attfp_model.evaluate(test, [metric])}")
```

### Module 5: Transfer Learning

Fine-tune pretrained chemical language models for downstream tasks with limited data.

```python
import deepchem as dc
from deepchem.models.torch_models import ChemBERTaModel

# ChemBERTa — SMILES-based transformer (pretrained on 77M molecules)
tasks, datasets, transformers = dc.molnet.load_bbbp(featurizer=dc.feat.SmilesTokenizer())
train, valid, test = datasets

chemberta = ChemBERTaModel(
    task="classification",
    n_tasks=1,
    model_dir="chemberta_finetuned/",
)
# Fine-tune on downstream task (BBB permeability)
chemberta.fit(train, nb_epoch=10)
metric = dc.metrics.Metric(dc.metrics.roc_auc_score)
print(f"ChemBERTa ROC-AUC: {chemberta.evaluate(test, [metric])}")
```

### Module 6: Predictions on New Molecules

Run inference on new molecules with a trained model.

```python
import deepchem as dc
import numpy as np

# Assume trained model from Module 3
# Featurize new molecules using same featurizer
featurizer = dc.feat.CircularFingerprint(size=1024, radius=2)
new_smiles = ["c1cc(O)ccc1", "CC(=O)Nc1ccc(O)cc1", "OC(=O)c1ccccc1"]
new_features = featurizer.featurize(new_smiles)
new_dataset = dc.data.NumpyDataset(X=new_features)

predictions = model.predict(new_dataset)
for smi, pred in zip(new_smiles, predictions):
    print(f"{smi}: {pred[0]:.2f}")

# Ensemble predictions from multiple models for robustness
models = [model1, model2, model3]  # trained models
all_preds = np.array([m.predict(new_dataset) for m in models])
ensemble_mean = all_preds.mean(axis=0)
ensemble_std = all_preds.std(axis=0)
print(f"Ensemble prediction: {ensemble_mean[0][0]:.2f} +/- {ensemble_std[0][0]:.2f}")
```

## Key Concepts

### Unified API Pattern

All DeepChem workflows follow a consistent 5-step pattern:

```
Load Data → Featurize → Split → Train → Evaluate
```

- **Load**: `CSVLoader`, `SDFLoader`, or `dc.molnet.load_*()` (auto-loads MoleculeNet datasets)
- **Featurize**: Pass featurizer to loader, or call `featurizer.featurize(smiles)` directly
- **Split**: `ScaffoldSplitter` (recommended for drug discovery), `RandomSplitter`, `ButinaSplitter`
- **Train**: `model.fit(train_dataset, nb_epoch=N)`
- **Evaluate**: `model.evaluate(test_dataset, metrics_list)`

### Model Selection Guide

| Data Type | Model | Key Feature | Use When |
|-----------|-------|-------------|----------|
| SMILES + fingerprints | `MultitaskRegressor` | Fast, baseline | First attempt, small datasets |
| SMILES + fingerprints | `MultitaskClassifier` | Multi-label | Multi-task classification (Tox21) |
| Molecular graphs | `GraphConvModel` | Learned fingerprints | Medium datasets, general properties |
| Molecular graphs | `GATModel` | Attention mechanism | When atom importance matters |
| Molecular graphs | `AttentiveFPModel` | Graph + timestep attention | State-of-art molecular properties |
| Molecular graphs | `MPNNModel` | Message passing | Complex molecular interactions |
| Molecular graphs | `DMPNNModel` | Directed MPNN | Bond-level predictions |
| SMILES strings | `ChemBERTaModel` | Pretrained transformer | Low-data regime, transfer learning |
| SMILES strings | `GROVERModel` | Graph + transformer | Rich molecular representations |
| Crystal structures | `CGCNNModel` | Crystal graph CNN | Materials property prediction |
| Crystal structures | `MEGNetModel` | Graph networks | Materials and molecules |
| Protein sequences | `ProteinLigandComplexModel` | Complex modeling | Binding affinity prediction |
| Tabular features | `XGBoostModel`, `RandomForestModel` | Classical ML | Interpretability, baselines |

### Featurizer Selection Guide

| Featurizer | Class | Output | Best For |
|------------|-------|--------|----------|
| ECFP/Morgan | `CircularFingerprint` | Binary vector (1024-2048) | General QSAR, fast baselines |
| MACCS Keys | `MACCSKeysFingerprint` | 167-bit vector | Substructure filtering |
| RDKit 2D | `RDKitDescriptors` | 200+ descriptors | Interpretable models |
| Mol2Vec | `Mol2VecFingerprint` | 300-dim embedding | Similarity, clustering |
| ConvMol | `ConvMolFeaturizer` | Graph features | `GraphConvModel` input |
| MolGraph | `MolGraphConvFeaturizer` | Node + edge features | `AttentiveFPModel`, `MPNNModel` |
| Weave | `WeaveFeaturizer` | Pair features | `WeaveModel` input |
| Coulomb Matrix | `CoulombMatrix` | Atom-pair distances | QM property prediction |
| SMILES tokens | `SmilesTokenizer` | Token IDs | ChemBERTa, transformer models |

### Data Splitting Strategies

| Splitter | Use Case | Why |
|----------|----------|-----|
| `ScaffoldSplitter` | Drug discovery (default) | Tests generalization to new chemotypes |
| `RandomSplitter` | Quick experiments | Baseline, but overestimates performance |
| `ButinaSplitter` | Diversity-based | Clusters by Tanimoto similarity |
| `FingerprintSplitter` | Chemical similarity | Groups structurally similar molecules |
| `MaxMinSplitter` | Maximum diversity test | Extreme generalization test |

## Common Workflows

### Workflow 1: QSAR from CSV Data

**Goal**: Build a property prediction model from a CSV file with SMILES and activity columns.

```python
import deepchem as dc
import pandas as pd

# Step 1: Load and featurize CSV data
loader = dc.data.CSVLoader(
    tasks=["pIC50"],
    feature_field="smiles",
    featurizer=dc.feat.CircularFingerprint(size=2048, radius=3),
)
dataset = loader.create_dataset("bioactivity_data.csv")

# Step 2: Normalize targets
transformer = dc.trans.NormalizationTransformer(
    transform_y=True, dataset=dataset
)
dataset = transformer.transform(dataset)

# Step 3: Scaffold split (realistic for drug discovery)
splitter = dc.splits.ScaffoldSplitter()
train, valid, test = splitter.train_valid_test_split(dataset)
print(f"Train: {len(train)}, Valid: {len(valid)}, Test: {len(test)}")

# Step 4: Train model
model = dc.models.MultitaskRegressor(
    n_tasks=1, n_features=2048,
    layer_sizes=[1000, 500], dropouts=0.25,
    learning_rate=0.001, batch_size=64,
)
model.fit(train, nb_epoch=100)

# Step 5: Evaluate
metrics = [
    dc.metrics.Metric(dc.metrics.pearson_r2_score),
    dc.metrics.Metric(dc.metrics.mean_absolute_error),
]
results = model.evaluate(test, metrics)
print(f"R2: {results['pearson_r2_score']:.3f}, MAE: {results['mean_absolute_error']:.3f}")
```

### Workflow 2: MoleculeNet Benchmark Comparison

**Goal**: Compare multiple models on a MoleculeNet benchmark dataset.

```python
import deepchem as dc

# Load dataset with graph featurizer (supports both fingerprint and GNN models)
tasks, datasets, transformers = dc.molnet.load_bbbp(
    featurizer="GraphConv", splitter="scaffold"
)
train, valid, test = datasets
metric = dc.metrics.Metric(dc.metrics.roc_auc_score)

# Model 1: Graph Convolutional Network
gcn = dc.models.GraphConvModel(n_tasks=1, mode="classification", dropout=0.2)
gcn.fit(train, nb_epoch=50)
gcn_score = gcn.evaluate(test, [metric])

# Model 2: Random Forest baseline (needs fingerprints)
tasks_fp, datasets_fp, _ = dc.molnet.load_bbbp(featurizer="ECFP", splitter="scaffold")
train_fp, _, test_fp = datasets_fp
rf = dc.models.SklearnModel(
    model=dc.models.sklearn_models.RandomForestClassifier(n_estimators=500),
    model_dir="rf_model/"
)
rf.fit(train_fp)
rf_score = rf.evaluate(test_fp, [metric])

print(f"GCN ROC-AUC: {gcn_score['roc_auc_score']:.3f}")
print(f"RF  ROC-AUC: {rf_score['roc_auc_score']:.3f}")
```

### Workflow 3: Transfer Learning Pipeline

**Goal**: Fine-tune a pretrained model on a small dataset.

1. Load pretrained ChemBERTa model (see Module 5 for code)
2. Prepare downstream dataset with `SmilesTokenizer` featurizer
3. Fine-tune with reduced learning rate (`1e-5` to `5e-5`) for 5-15 epochs
4. Evaluate on held-out scaffold split — expect gains over fingerprint baselines when training data < 1000 samples
5. Save fine-tuned model: `model.save_checkpoint()`
6. See `references/workflows_model_catalog.md` Workflow 1 for complete hyperparameter optimization code

## Key Parameters

| Parameter | Module | Default | Range / Options | Effect |
|-----------|--------|---------|-----------------|--------|
| `n_features` | MultitaskRegressor/Classifier | Required | Matches featurizer output | Input feature dimension |
| `layer_sizes` | MultitaskRegressor/Classifier | `[1000]` | `[256]` to `[1000, 500, 250]` | Hidden layer dimensions |
| `dropouts` | All neural models | `0.0` | `0.0`-`0.5` | Regularization strength |
| `learning_rate` | All neural models | `0.001` | `1e-5`-`0.01` | Training step size |
| `batch_size` | All neural models | `100` | `16`-`256` | Samples per gradient update |
| `nb_epoch` | `model.fit()` | `10` | `10`-`300` | Training iterations |
| `size` | `CircularFingerprint` | `2048` | `512`-`4096` | Fingerprint bit length |
| `radius` | `CircularFingerprint` | `2` | `2`-`4` | Substructure neighborhood radius |
| `graph_conv_layers` | `GraphConvModel` | `[64, 64]` | `[32]` to `[128, 128, 64]` | Graph convolution widths |
| `num_layers` | `AttentiveFPModel` | `2` | `1`-`5` | GNN message passing depth |
| `graph_feat_size` | `AttentiveFPModel` | `200` | `64`-`512` | Graph feature dimension |
| `splitter` | `dc.molnet.load_*()` | `"scaffold"` | `"scaffold"`, `"random"`, `"butina"` | Data splitting strategy |

## Best Practices

1. **Always use scaffold splitting for drug discovery**: Random splits leak structural information and overestimate performance. Scaffold splits test generalization to novel chemotypes.

2. **Normalize regression targets**: Apply `NormalizationTransformer(transform_y=True)` before training. Remember to `untransform()` predictions for interpretable values.

3. **Start with fingerprint baselines**: Train `MultitaskRegressor` + ECFP first. Only move to GNNs if fingerprint baseline is insufficient — GNNs need more data and compute.
   ```python
   # Baseline first
   baseline = dc.models.MultitaskRegressor(n_tasks=1, n_features=2048)
   ```

4. **Match featurizer to model**: GNN models require graph featurizers (`ConvMolFeaturizer`, `MolGraphConvFeaturizer`). Fingerprint models need `CircularFingerprint`. Mixing causes silent errors.

5. **Anti-pattern -- Do not use random split for drug discovery benchmarks**: Results with `RandomSplitter` are not publishable for molecular property prediction. Reviewers expect scaffold or temporal splits.

6. **Handle missing labels in multi-task datasets**: Tox21 and many bioactivity datasets have missing values. DeepChem handles NaN labels automatically during training (masked loss), but verify with `np.isnan(dataset.y).sum()`.

7. **Use early stopping via validation set**: Monitor validation loss to prevent overfitting, especially with GNN models.

## Common Recipes

### Recipe: Hyperparameter Search

When to use: Optimize model performance before final evaluation.

```python
import deepchem as dc

tasks, datasets, transformers = dc.molnet.load_delaney(featurizer="ECFP")
train, valid, test = datasets

# Define parameter grid
params = {
    "n_features": [1024],
    "layer_sizes": [[500], [1000, 500], [1000, 500, 250]],
    "dropouts": [0.1, 0.25, 0.5],
    "learning_rate": [0.001, 0.0005],
}

optimizer = dc.hyper.GridHyperparamOpt(lambda **p: dc.models.MultitaskRegressor(**p))
metric = dc.metrics.Metric(dc.metrics.pearson_r2_score)
best_model, best_params, all_results = optimizer.hyperparam_search(
    params, train, valid, metric, logdir="hyperparam_logs/"
)
print(f"Best params: {best_params}")
print(f"Best R2: {best_model.evaluate(test, [metric])}")
```

### Recipe: Save and Reload Models

When to use: Deploy trained models or resume training.

```python
# Save model checkpoint
model.save_checkpoint(model_dir="saved_model/")

# Reload model
loaded_model = dc.models.MultitaskRegressor(n_tasks=1, n_features=2048)
loaded_model.restore(model_dir="saved_model/")
predictions = loaded_model.predict(test)
```

### Recipe: Custom Metric

When to use: Evaluate models with domain-specific metrics.

```python
import deepchem as dc
import numpy as np

def enrichment_factor(y_true, y_pred, top_fraction=0.01):
    """Enrichment factor at top X% of ranked predictions."""
    n = len(y_true)
    n_top = max(int(n * top_fraction), 1)
    top_indices = np.argsort(y_pred.flatten())[-n_top:]
    hits_in_top = y_true.flatten()[top_indices].sum()
    expected = y_true.sum() * top_fraction
    return hits_in_top / expected if expected > 0 else 0.0

ef_metric = dc.metrics.Metric(enrichment_factor, mode="regression")
print(f"EF@1%: {model.evaluate(test, [ef_metric])}")
```

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| `ModuleNotFoundError: torch` | PyTorch not installed | `pip install deepchem[torch]` for GNN models |
| `ValueError: n_features mismatch` | Featurizer output size does not match model `n_features` | Check `dataset.X.shape[1]` and set `n_features` accordingly |
| NaN loss during training | Learning rate too high or unnormalized targets | Apply `NormalizationTransformer`, reduce learning rate to `1e-4` |
| Low scaffold-split performance | Model memorizes scaffolds, not properties | Use more data, try GNN models, or add regularization (dropout 0.3-0.5) |
| `RuntimeError: CUDA out of memory` | Batch size too large for GPU | Reduce `batch_size` (32 or 16), or use CPU for small datasets |
| `FeaturizationError` on some SMILES | Invalid or complex SMILES strings | Pre-filter with RDKit: `Chem.MolFromSmiles(smi) is not None` |
| Model predicts constant values | Targets not normalized or too few epochs | Apply `NormalizationTransformer`, increase `nb_epoch` |
| Slow featurization | Large dataset with expensive featurizer | Use `CircularFingerprint` (fast) or parallelize with `n_jobs` parameter |

## Bundled Resources

- **references/workflows_model_catalog.md** -- Extended workflows (hyperparameter optimization with full code, MolGAN generative models, materials property prediction with CGCNN/MEGNet, protein-ligand modeling, custom model architecture) plus complete model catalog (60+ models organized by category) and complete featurizer catalog (50+ featurizers). Covers: workflows 4-8 from original, extended model and featurizer inventories, MoleculeNet dataset catalog. Relocated inline: top 3 workflows (QSAR, MoleculeNet benchmark, transfer learning) are in Common Workflows; core model/featurizer tables are in Key Concepts. Omitted: detailed installation troubleshooting for TensorFlow 1.x (deprecated) and Docker-specific setup (covered by official docs).

## Related Skills

- **rdkit-cheminformatics** -- molecular manipulation, fingerprints, substructure search (upstream featurization)
- **molfeat-molecular-featurization** -- 100+ featurizers with scikit-learn API (featurization-only alternative)
- **datamol-cheminformatics** -- Pythonic molecular processing (upstream data prep)
- **pytdc-therapeutics-data-commons** -- curated ADMET/DTI datasets with standardized splits (complementary data source)
- **torch-geometric-graph-neural-networks** -- lower-level PyG for custom GNN architectures (alternative for advanced users)
- **scikit-learn-machine-learning** -- classical ML baselines that DeepChem wraps via `SklearnModel`

## References

- [DeepChem documentation](https://deepchem.readthedocs.io/) -- official API docs and tutorials
- [DeepChem GitHub](https://github.com/deepchem/deepchem) -- source code, examples, issues
- [MoleculeNet benchmark paper](https://doi.org/10.1039/C7SC02664A) -- Wu et al. 2018, benchmark dataset descriptions
- [DeepChem tutorials](https://github.com/deepchem/deepchem/tree/master/examples/tutorials) -- Jupyter notebook tutorials
