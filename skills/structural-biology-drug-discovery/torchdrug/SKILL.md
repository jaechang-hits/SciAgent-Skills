---
name: "torchdrug"
description: "TorchDrug is a PyTorch-based machine learning platform for drug discovery. Use it for graph-based molecular representation learning, molecular property prediction (ADMET, activity), retrosynthesis prediction, drug-target interaction (DTI) modeling, and pretraining on large molecular datasets. Provides GNN layers (GraphConv, GAT, MPNN), pretrained models, and benchmark datasets in a unified PyTorch-compatible API."
license: "Apache-2.0"
---

# torchdrug

## Overview

TorchDrug is a comprehensive machine learning framework for drug discovery built on PyTorch. It provides graph-based molecular representations (atoms as nodes, bonds as edges), a library of graph neural network (GNN) architectures, benchmark datasets, and pretrained models for tasks including molecular property prediction, drug-target interaction, retrosynthesis, and generative molecular design. TorchDrug integrates with PyTorch Lightning and standard ML tooling, making it accessible to both computational chemists and ML practitioners.

## When to Use

- **Molecular property prediction**: Training or fine-tuning GNN models to predict ADMET properties (solubility, toxicity, permeability) or bioactivity (IC50, Ki) from molecular graphs.
- **Drug-target interaction (DTI) prediction**: Building models that predict binding affinity between a compound (SMILES) and a protein (sequence or structure).
- **Retrosynthesis prediction**: Identifying plausible synthetic routes for a target molecule using template-based or template-free models.
- **Pretraining on large molecular datasets**: Leveraging pretrained GNN representations on ChEMBL or ZINC for transfer learning to small datasets.
- **Molecular generation**: Training graph-based generative models (GCPN, GraphAF) to design novel molecules with desired properties.
- **Benchmarking GNN architectures**: Comparing GraphConv, MPNN, GAT, AttentiveFP on standard MoleculeNet tasks.
- For fast fingerprint-based property prediction without deep learning, use RDKit + scikit-learn instead.
- For protein structure tasks (folding, docking), use ESMFold or DiffDock rather than TorchDrug.

## Prerequisites

- **Python packages**: `torchdrug`, `torch`, `torch-geometric`, `rdkit`
- **Environment**: Python 3.8+, CUDA-compatible GPU recommended for training
- **Data requirements**: SMILES strings or molecular SDF files; protein sequences for DTI tasks

```bash
pip install torch torchvision --extra-index-url https://download.pytorch.org/whl/cu118
pip install torch-geometric
pip install torchdrug
pip install rdkit
```

## Quick Start

```python
import torch
from torchdrug import data, datasets, models, tasks, core

# Load a benchmark dataset and train a GNN for property prediction
dataset = datasets.BBBP("~/data/bbbp", node_feature="default", edge_feature="default")
print(f"Dataset: {len(dataset)} molecules, task: BBBP (blood-brain barrier penetration)")

# Define model: GIN encoder
model = models.GIN(
    input_dim=dataset.node_feature_dim,
    hidden_dims=[256, 256],
    short_cut=True,
    batch_norm=True,
    concat_hidden=True,
)

# Define training task
task = tasks.PropertyPrediction(
    model, task=dataset.tasks,
    criterion="bce", metric=("auprc", "auroc"),
)

# Train with the Solver
optimizer = torch.optim.Adam(task.parameters(), lr=1e-3)
solver    = core.Engine(task, dataset, None, None, optimizer, gpus=[0])
solver.train(num_epoch=50)
print("Training complete")
```

## Core API

### Module 1: Molecular Graph Representation

TorchDrug represents molecules as typed graphs. `data.Molecule` is the core data structure.

```python
from torchdrug import data
from rdkit import Chem

# Create a molecule from SMILES
smiles = "CC(=O)Oc1ccccc1C(=O)O"   # aspirin
mol    = data.Molecule.from_smiles(smiles, node_feature="default", edge_feature="default")

print(f"Atoms: {mol.num_node}")
print(f"Bonds: {mol.num_edge}")
print(f"Node feature dim: {mol.node_feature.shape}")  # (N_atoms, feature_dim)
print(f"Edge feature dim: {mol.edge_feature.shape}")  # (N_bonds*2, feature_dim)
```

```python
# Convert a MoleculeNet / custom SMILES list to a dataset
from torchdrug import data as td_data
import pandas as pd

df = pd.read_csv("compounds.csv")   # columns: smiles, label
molecules = [td_data.Molecule.from_smiles(s) for s in df["smiles"] if s]
print(f"Loaded {len(molecules)} valid molecules")

# Check feature dimensions
print(f"Default atom feature dim: {molecules[0].node_feature.shape[1]}")
```

### Module 2: GNN Architectures

TorchDrug provides GIN, RGCN, GraphSAGE, GAT, MPNN, AttentiveFP, and more.

```python
from torchdrug import models, datasets

dataset = datasets.ESOL("~/data/esol", node_feature="default", edge_feature="default")
feature_dim = dataset.node_feature_dim

# Graph Isomorphism Network (GIN) — good default for property prediction
gin = models.GIN(
    input_dim=feature_dim,
    hidden_dims=[256, 256, 256],
    short_cut=True,
    batch_norm=True,
    concat_hidden=True,      # concatenate layer representations
)
print(f"GIN output_dim: {gin.output_dim}")
```

```python
from torchdrug import models

# Message Passing Neural Network (MPNN) — captures edge features
mpnn = models.MPNN(
    input_dim=feature_dim,
    hidden_dim=256,
    edge_input_dim=16,       # edge feature dimension
    num_layer=4,
    num_gru_layer=1,
)

# Graph Attention Network (GAT) — attention-weighted neighbors
gat = models.GAT(
    input_dim=feature_dim,
    hidden_dims=[256, 256],
    edge_input_dim=16,
    num_head=8,
    batch_norm=True,
)
print(f"MPNN output_dim: {mpnn.output_dim}, GAT output_dim: {gat.output_dim}")
```

### Module 3: Molecular Property Prediction

Wrap a GNN encoder with a prediction head for classification or regression.

```python
import torch
from torchdrug import datasets, models, tasks, core

# Regression example: ESOL aqueous solubility
dataset = datasets.ESOL("~/data/esol", node_feature="default", edge_feature="default")
train, val, test = dataset.split()
print(f"Train: {len(train)}, Val: {len(val)}, Test: {len(test)}")

model = models.GIN(
    input_dim=dataset.node_feature_dim,
    hidden_dims=[300, 300],
    short_cut=True,
    batch_norm=True,
    concat_hidden=True,
)

task = tasks.PropertyPrediction(
    model,
    task=dataset.tasks,       # list of property names
    criterion="mse",          # "mse" for regression, "bce" for classification
    metric=("mae", "rmse"),
    num_mlp_layer=2,
)

optimizer = torch.optim.Adam(task.parameters(), lr=1e-3, weight_decay=1e-5)
solver    = core.Engine(task, train, val, test, optimizer,
                        batch_size=32, log_interval=50)
solver.train(num_epoch=100)

# Evaluate on test set
metrics = solver.evaluate("test")
print(f"Test RMSE: {metrics['rmse']:.4f}")
print(f"Test MAE:  {metrics['mae']:.4f}")
```

### Module 4: Drug-Target Interaction (DTI) Prediction

Predict binding affinity between molecules and protein sequences.

```python
from torchdrug import datasets, models, tasks, core
import torch

# Load a DTI dataset (e.g., Davis kinase binding affinities)
dataset = datasets.Davis("~/data/davis",
                          mol_node_feature="default",
                          mol_edge_feature="default")
train, val, test = dataset.split()

# Molecule encoder
mol_model = models.GIN(
    input_dim=dataset.mol_node_feature_dim,
    hidden_dims=[256, 256],
    short_cut=True,
    batch_norm=True,
    concat_hidden=True,
)

# Protein encoder (CNN on sequence)
prot_model = models.ProteinCNN(
    input_dim=21,            # amino acid vocabulary size
    hidden_dims=[128, 128, 128],
    kernel_size=3,
)

task = tasks.InteractionPrediction(
    mol_model, prot_model,
    task=dataset.tasks,
    criterion="mse",
    metric=("rmse", "pearsonr"),
)

optimizer = torch.optim.Adam(task.parameters(), lr=1e-3)
solver    = core.Engine(task, train, val, test, optimizer,
                        batch_size=64, log_interval=100)
solver.train(num_epoch=50)

metrics = solver.evaluate("test")
print(f"DTI Test RMSE: {metrics['rmse']:.4f}")
print(f"DTI Pearson r: {metrics['pearsonr']:.4f}")
```

### Module 5: Retrosynthesis Prediction

Predict one-step retrosynthetic disconnections to find plausible building blocks.

```python
from torchdrug import datasets, models, tasks, core
import torch

# USPTO-50k retrosynthesis benchmark
dataset = datasets.USPTO50k("~/data/uspto50k",
                             as_synthon=False,
                             atom_feature="default",
                             bond_feature="default")
train, val, test = dataset.split()

# Reaction-predicting GNN
model = models.RGCN(
    input_dim=dataset.node_feature_dim,
    hidden_dims=[256, 256, 256],
    num_relation=dataset.num_bond_type,
    batch_norm=True,
)

task = tasks.CenterIdentification(
    model,
    feature=("graph", "atom", "bond"),
)

optimizer = torch.optim.Adam(task.parameters(), lr=1e-4)
solver    = core.Engine(task, train, val, test, optimizer,
                        batch_size=64, log_interval=100)
solver.train(num_epoch=50)
metrics = solver.evaluate("test")
print(f"Retrosynthesis top-1 accuracy: {metrics.get('accuracy', 'N/A')}")
```

### Module 6: Pretrained Models and Transfer Learning

Use TorchDrug's pretrained GNN representations as features for downstream tasks.

```python
from torchdrug import models

# Load a GNN pretrained on ChEMBL with context-prediction self-supervised learning
pretrained_gin = models.GIN(
    input_dim=39,
    hidden_dims=[300, 300, 300, 300, 300],
    short_cut=False,
    batch_norm=True,
    concat_hidden=False,
)

# Load pretrained weights (download from TorchDrug model zoo)
import torch
ckpt = torch.load("gin_supervised_contextpred.pth", map_location="cpu")
pretrained_gin.load_state_dict(ckpt)
pretrained_gin.eval()

print(f"Pretrained GIN loaded, output_dim={pretrained_gin.output_dim}")
print("Use as encoder in PropertyPrediction task for transfer learning")
```

## Key Concepts

### Graph-Based Molecular Representation

Molecules are represented as attributed graphs: atoms are nodes with features (atomic number, degree, charge, aromaticity) and bonds are edges with features (bond type, ring membership). All TorchDrug models operate on these graph representations rather than SMILES strings or fingerprints.

```python
from torchdrug import data

mol = data.Molecule.from_smiles("c1ccccc1")   # benzene
print(f"Atoms: {mol.num_node}, Bonds: {mol.num_edge // 2}")
print(f"Atom features (first atom): {mol.node_feature[0]}")
```

### Engine and Solver Pattern

TorchDrug uses a `core.Engine` (also called `Solver`) to handle the training loop, logging, checkpointing, and multi-GPU setup. Pass the task, train/val/test splits, and optimizer to the Engine rather than writing a manual training loop.

```python
# Engine handles: batch iteration, loss backward, logging, checkpointing
solver = core.Engine(
    task, train_set, valid_set, test_set, optimizer,
    batch_size=32,
    log_interval=100,
    gpus=[0, 1],         # multi-GPU support
)
solver.train(num_epoch=100)
solver.save("checkpoint.pth")
```

## Common Workflows

### Workflow 1: End-to-End ADMET Property Prediction

**Goal**: Train a GIN model to predict blood-brain barrier penetration from SMILES, then predict on new compounds.

```python
import torch
import pandas as pd
from torchdrug import data, datasets, models, tasks, core

# 1. Load dataset
dataset = datasets.BBBP("~/data/bbbp", node_feature="default", edge_feature="default")
train, val, test = dataset.split()
print(f"BBBP: {len(train)} train, {len(val)} val, {len(test)} test molecules")

# 2. Build model
model = models.GIN(
    input_dim=dataset.node_feature_dim,
    hidden_dims=[256, 256],
    short_cut=True, batch_norm=True, concat_hidden=True,
)
task = tasks.PropertyPrediction(
    model, task=dataset.tasks,
    criterion="bce", metric=("auroc", "auprc"),
)

# 3. Train
optimizer = torch.optim.Adam(task.parameters(), lr=1e-3)
solver    = core.Engine(task, train, val, test, optimizer,
                        batch_size=32, log_interval=50)
solver.train(num_epoch=100)
metrics = solver.evaluate("test")
print(f"Test AUROC: {metrics['auroc']:.4f}")

# 4. Predict on new SMILES
new_smiles = ["CC(=O)Oc1ccccc1C(=O)O", "c1ccc(cc1)N"]
task.eval()
with torch.no_grad():
    for smi in new_smiles:
        mol = data.Molecule.from_smiles(smi, node_feature="default", edge_feature="default")
        batch = data.Batch.from_data_list([mol])
        pred  = task.predict(batch)
        print(f"  {smi}: BBB penetration probability = {pred.sigmoid().item():.3f}")
```

### Workflow 2: Multi-Task Property Prediction on Tox21

**Goal**: Simultaneously predict 12 toxicity endpoints using a shared GNN encoder.

```python
import torch
from torchdrug import datasets, models, tasks, core

# Tox21: 12 toxicity assays, multi-label classification
dataset = datasets.Tox21("~/data/tox21", node_feature="default", edge_feature="default")
train, val, test = dataset.split()
print(f"Tox21 tasks ({len(dataset.tasks)}): {dataset.tasks}")

model = models.GIN(
    input_dim=dataset.node_feature_dim,
    hidden_dims=[300, 300, 300],
    short_cut=True, batch_norm=True, concat_hidden=True,
)

# Multi-task: one output head per toxicity assay
task = tasks.PropertyPrediction(
    model, task=dataset.tasks,
    criterion="bce",
    metric=("auroc",),
    num_mlp_layer=2,
)

optimizer = torch.optim.Adam(task.parameters(), lr=1e-3)
solver    = core.Engine(task, train, val, test, optimizer, batch_size=64)
solver.train(num_epoch=100)

metrics = solver.evaluate("test")
for name, val_score in metrics.items():
    print(f"  {name}: {val_score:.4f}")
```

## Key Parameters

| Parameter | Module | Default | Range / Options | Effect |
|-----------|--------|---------|-----------------|--------|
| `hidden_dims` | GIN/MPNN/GAT | `[256, 256]` | list of int | Width and depth of GNN layers |
| `short_cut` | GIN | `False` | `True`, `False` | Add residual connection between layers |
| `batch_norm` | GIN/MPNN | `False` | `True`, `False` | Apply batch normalization after each layer |
| `concat_hidden` | GIN | `False` | `True`, `False` | Concatenate all layer outputs as final representation |
| `num_mlp_layer` | PropertyPrediction | `1` | `1`–`4` | Depth of MLP prediction head after GNN |
| `criterion` | PropertyPrediction | `"mse"` | `"mse"`, `"bce"`, `"ce"` | Loss function: regression, binary/multi-label classification |
| `batch_size` | Engine | `32` | `8`–`512` | Training batch size |

## Best Practices

1. **Use `concat_hidden=True` for GIN on small datasets**: Concatenating all layer outputs provides a richer molecular representation and often improves performance when training data is limited (<10,000 molecules).

2. **Apply `batch_norm=True` for training stability**: Batch normalization reduces sensitivity to learning rate and initialization, especially with deep GNNs (3+ layers).

3. **Start with pretrained GNN weights for small datasets**: TorchDrug's model zoo provides GINs pretrained on ChEMBL via self-supervised learning. Fine-tuning from these outperforms random initialization on datasets <1,000 molecules.

4. **Validate on scaffold splits, not random splits**: Random train/test splits overestimate generalization because structurally similar molecules appear in both sets. Use `dataset.split(test_scaffold_ratio=0.1)` for more realistic evaluation.

5. **Handle missing labels in multi-task datasets**: Many MoleculeNet datasets (Tox21, SIDER) have missing assay values. TorchDrug's `PropertyPrediction` task handles NaN labels automatically, but verify that missing rates are not too high for rare assays.

## Common Recipes

### Recipe: Generate Molecular Embeddings for Clustering

When to use: Visualize a molecular library in embedding space or use GNN features in scikit-learn models.

```python
import torch
import numpy as np
from torchdrug import data, models

model = models.GIN(input_dim=39, hidden_dims=[300, 300], concat_hidden=True)
model.eval()

smiles_list = ["CC(=O)O", "c1ccccc1", "CCN", "CC(=O)Oc1ccccc1C(=O)O"]
embeddings  = []
with torch.no_grad():
    for smi in smiles_list:
        mol   = data.Molecule.from_smiles(smi, node_feature="default")
        batch = data.Batch.from_data_list([mol])
        graph_feat = model(batch, batch.node_feature.float())["graph_feature"]
        embeddings.append(graph_feat.squeeze(0).numpy())

emb_matrix = np.stack(embeddings)
print(f"Embedding matrix: {emb_matrix.shape}")   # (N_mols, embed_dim)
```

### Recipe: Custom Molecular Dataset from CSV

When to use: Training on proprietary assay data rather than benchmark datasets.

```python
from torchdrug import data
import torch

class CustomDataset(data.MoleculeDataset):
    def __init__(self, csv_path, smiles_col="smiles", label_col="activity"):
        import pandas as pd
        df = pd.read_csv(csv_path).dropna(subset=[smiles_col])
        smiles_list = df[smiles_col].tolist()
        targets     = df[label_col].tolist()
        self.load_smiles(smiles_list, {"activity": targets},
                         node_feature="default", edge_feature="default")
        self.tasks = ["activity"]

dataset = CustomDataset("assay_data.csv", smiles_col="smiles", label_col="pIC50")
print(f"Custom dataset: {len(dataset)} molecules")
```

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| `ImportError: torchdrug` | Package not installed | `pip install torchdrug` after installing PyTorch |
| `CUDA error: device-side assert` | Label dtype mismatch | Ensure regression labels are `float`, classification labels are `long` |
| Poor test metrics with small dataset | Overfitting | Use pretrained weights, add dropout, or reduce model depth |
| `KeyError: task name` in `dataset.tasks` | Task name mismatch | Print `dataset.tasks` to see exact task names; pass the same list to `PropertyPrediction` |
| `RuntimeError: Expected all tensors on same device` | Mixed CPU/GPU tensors | Use `solver = core.Engine(..., gpus=[0])` to ensure consistent device placement |
| Slow training | CPU-only mode | Install CUDA-compatible PyTorch; set `gpus=[0]` in Engine |
| Missing assay values cause NaN loss | Dataset has missing labels | Set `criterion="bce"` — TorchDrug masks NaN labels during loss computation |

## Related Skills

- `rdkit` — molecular fingerprints and cheminformatics preprocessing before TorchDrug
- `diffdock` — structure-based docking complementary to TorchDrug's ligand-based prediction

## References

- [TorchDrug Documentation](https://torchdrug.ai/docs/) — official docs and tutorials
- [TorchDrug GitHub (DeepGraphLearning/torchdrug)](https://github.com/DeepGraphLearning/torchdrug) — source code
- [Zhu et al. (2022), arXiv — TorchDrug paper](https://arxiv.org/abs/2202.08320) — original platform paper
- [MoleculeNet Benchmark](https://moleculenet.org/) — standardized datasets used in TorchDrug
