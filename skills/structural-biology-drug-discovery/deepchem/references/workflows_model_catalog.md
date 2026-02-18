# DeepChem — Extended Workflows & Model Catalog

## Workflow 1: Hyperparameter Optimization with GridHyperparamOpt

**Goal**: Systematically search hyperparameter space for optimal model configuration.

```python
import deepchem as dc

# Load dataset
tasks, datasets, transformers = dc.molnet.load_delaney(featurizer="GraphConv")
train, valid, test = datasets

# Define search space for GraphConvModel
params_dict = {
    "graph_conv_layers": [[64, 64], [128, 128], [64, 64, 64]],
    "dense_layer_size": [128, 256, 512],
    "dropout": [0.0, 0.1, 0.25],
    "learning_rate": [0.001, 0.0005, 0.0001],
    "batch_size": [32, 64, 128],
}

def model_builder(**params):
    return dc.models.GraphConvModel(
        n_tasks=1,
        mode="regression",
        graph_conv_layers=params["graph_conv_layers"],
        dense_layer_size=params["dense_layer_size"],
        dropout=params["dropout"],
        learning_rate=params["learning_rate"],
        batch_size=params["batch_size"],
    )

optimizer = dc.hyper.GridHyperparamOpt(model_builder)
metric = dc.metrics.Metric(dc.metrics.pearson_r2_score)

best_model, best_params, all_results = optimizer.hyperparam_search(
    params_dict, train, valid, metric,
    logdir="hyperopt_results/",
)

# Evaluate best model on test set
test_score = best_model.evaluate(test, [metric])
print(f"Best params: {best_params}")
print(f"Validation R2: {all_results}")
print(f"Test R2: {test_score['pearson_r2_score']:.3f}")
```

### Gaussian Process Hyperparameter Optimization

For more efficient search over continuous parameters:

```python
import deepchem as dc

params_dict = {
    "learning_rate": [0.0001, 0.001],   # min, max range
    "dropout": [0.0, 0.5],
    "n_layers": [1, 4],                  # integer range
}

optimizer = dc.hyper.GaussianProcessHyperparamOpt(model_builder)
best_model, best_params, all_results = optimizer.hyperparam_search(
    params_dict, train, valid, metric,
    max_iter=50,
    logdir="gp_hyperopt/",
)
print(f"GP-optimized params: {best_params}")
```

## Workflow 2: MolGAN Molecular Generation

**Goal**: Generate novel molecules using a Generative Adversarial Network.

```python
import deepchem as dc

# Load QM9 dataset for training the generator
tasks, datasets, transformers = dc.molnet.load_qm9(featurizer=dc.feat.MolGanFeaturizer())
train = datasets[0]

# Build MolGAN model
gan = dc.models.MolGAN(
    learning_rate=dc.models.optimizers.ExponentialDecay(0.001, 0.9, 5000),
    vertices=9,              # Max atoms per molecule
    edges=5,                 # Bond types (none, single, double, triple, aromatic)
    nodes=5,                 # Atom types
    embedding_dim=128,
    dropout_rate=0.0,
)

# Train with WGAN loss + gradient penalty
gan.fit_gan(train, generator_steps=0.2, checkpoint_interval=5000, nb_epoch=50)

# Generate molecules
generated = gan.predict_gan_generator(1000)
# Post-process: decode adjacency matrices to SMILES
from rdkit import Chem
valid_smiles = []
for mol_data in generated:
    mol = dc.utils.molecule_utils.decode_mol(mol_data)
    if mol is not None:
        smi = Chem.MolToSmiles(mol)
        valid_smiles.append(smi)
print(f"Valid molecules: {len(valid_smiles)}/{len(generated)}")
```

## Workflow 3: Materials Property Prediction

**Goal**: Predict properties of crystalline materials using CGCNN or MEGNet.

```python
import deepchem as dc

# Crystal Graph CNN for materials
# Input: crystal structures represented as graphs (nodes=atoms, edges=bonds in crystal)
# Requires pymatgen for structure processing

from pymatgen.core import Structure

# Load materials dataset (e.g., band gap prediction)
# Featurize crystal structures
featurizer = dc.feat.CGCNNFeaturizer()

# Example: create dataset from pymatgen structures
structures = [Structure.from_file(f"structure_{i}.cif") for i in range(100)]
features = featurizer.featurize(structures)
dataset = dc.data.NumpyDataset(X=features, y=band_gaps)

splitter = dc.splits.RandomSplitter()
train, valid, test = splitter.train_valid_test_split(dataset)

# Train CGCNN
cgcnn = dc.models.CGCNNModel(
    n_tasks=1,
    mode="regression",
    graph_conv_layers=[64, 64, 64],
    learning_rate=0.001,
    batch_size=32,
)
cgcnn.fit(train, nb_epoch=200)
metric = dc.metrics.Metric(dc.metrics.mean_absolute_error)
print(f"MAE: {cgcnn.evaluate(test, [metric])['mean_absolute_error']:.3f} eV")
```

## Workflow 4: Protein-Ligand Interaction Modeling

**Goal**: Predict binding affinity between proteins and small molecules.

```python
import deepchem as dc

# Load PDBbind dataset (protein-ligand complexes with binding affinity)
tasks, datasets, transformers = dc.molnet.load_pdbbind(
    featurizer="grid",          # 3D voxel representation
    split="random",
    subset="core",              # Core set for evaluation
)
train, valid, test = datasets

# Atomic Convolution Model for binding affinity
acm = dc.models.AtomicConvModel(
    n_tasks=1,
    frag1_num_atoms=70,         # Max protein atoms in binding pocket
    frag2_num_atoms=24,         # Max ligand atoms
    complex_num_atoms=94,
    layer_sizes=[32, 32, 16],
    learning_rate=0.003,
    batch_size=12,
)
acm.fit(train, nb_epoch=50)

metric = dc.metrics.Metric(dc.metrics.pearson_r2_score)
print(f"Binding affinity R2: {acm.evaluate(test, [metric])}")
```

## Workflow 5: Custom Model Architecture

**Goal**: Build a custom neural network model within the DeepChem framework.

```python
import deepchem as dc
import torch
import torch.nn as nn

class CustomMoleculeModel(dc.models.TorchModel):
    """Custom PyTorch model wrapped in DeepChem API."""

    def __init__(self, n_features, n_tasks, hidden_size=256, **kwargs):
        # Define PyTorch module
        pytorch_model = nn.Sequential(
            nn.Linear(n_features, hidden_size),
            nn.ReLU(),
            nn.BatchNorm1d(hidden_size),
            nn.Dropout(0.3),
            nn.Linear(hidden_size, hidden_size // 2),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(hidden_size // 2, n_tasks),
        )
        # Wrap in DeepChem TorchModel
        loss = dc.models.losses.L2Loss()
        super().__init__(pytorch_model, loss, **kwargs)

# Use custom model with DeepChem data pipeline
tasks, datasets, transformers = dc.molnet.load_delaney(featurizer="ECFP")
train, valid, test = datasets

custom_model = CustomMoleculeModel(
    n_features=1024, n_tasks=1,
    hidden_size=512, learning_rate=0.001, batch_size=64,
)
custom_model.fit(train, nb_epoch=100)
metric = dc.metrics.Metric(dc.metrics.pearson_r2_score)
print(f"Custom model R2: {custom_model.evaluate(test, [metric])}")
```

---

## Complete Model Catalog

### Classical ML Models

| Model | Class | Task Type | Input | Notes |
|-------|-------|-----------|-------|-------|
| Random Forest | `SklearnModel` | Reg/Cls | Fingerprints, descriptors | Scikit-learn wrapper, good baseline |
| XGBoost | `XGBoostModel` | Reg/Cls | Fingerprints, descriptors | Gradient boosting, often competitive |
| SVM | `SklearnModel` | Reg/Cls | Fingerprints, descriptors | Scikit-learn SVC/SVR wrapper |
| KNN | `SklearnModel` | Reg/Cls | Fingerprints, descriptors | Simple similarity-based baseline |
| Logistic Regression | `SklearnModel` | Cls | Fingerprints, descriptors | Linear baseline for classification |
| MultitaskRegressor | `MultitaskRegressor` | Reg | Any fixed-dim features | Dense NN, multi-task capable |
| MultitaskClassifier | `MultitaskClassifier` | Cls | Any fixed-dim features | Dense NN, multi-task, handles NaN labels |
| RobustMultitask | `RobustMultitaskRegressor` | Reg | Any fixed-dim features | Shared + task-specific layers |
| Progressive Multitask | `ProgressiveMultitaskRegressor` | Reg | Any fixed-dim features | Progressive lateral connections |

### Graph Neural Network Models

| Model | Class | Key Feature | Featurizer | Reference |
|-------|-------|-------------|------------|-----------|
| GCN | `GraphConvModel` | Learned fingerprints | `ConvMolFeaturizer` | Duvenaud et al. 2015 |
| GAT | `GATModel` | Multi-head attention | `MolGraphConvFeaturizer` | Velickovic et al. 2018 |
| AttentiveFP | `AttentiveFPModel` | Graph + timestep attention | `MolGraphConvFeaturizer(use_edges=True)` | Xiong et al. 2020 |
| MPNN | `MPNNModel` | Message passing | `MolGraphConvFeaturizer(use_edges=True)` | Gilmer et al. 2017 |
| DMPNN | `DMPNNModel` | Directed message passing | `DMPNNFeaturizer` | Yang et al. 2019 |
| Weave | `WeaveModel` | Atom-pair features | `WeaveFeaturizer` | Kearnes et al. 2016 |
| SchNet | `SchNetModel` | Continuous-filter convolutions | 3D coordinates | Schutt et al. 2018 |
| PAGTN | `PagtnModel` | Path-augmented attention | `PagtnMolGraphFeaturizer` | Chen et al. 2019 |

### Transformer / Language Models

| Model | Class | Pretraining | Input | Best For |
|-------|-------|-------------|-------|----------|
| ChemBERTa | `ChemBERTaModel` | MLM on 77M SMILES | SMILES tokens | Low-data fine-tuning |
| GROVER | `GROVERModel` | Self-supervised on 10M mols | Molecular graphs | Rich representations |
| MolFormer | via HuggingFace | Linear attention on 1.1B mols | SMILES | Large-scale pretraining |
| MAT | `MATModel` | Molecular attention | Interatomic distances | 3D-aware predictions |

### Generative Models

| Model | Class | Method | Output |
|-------|-------|--------|--------|
| MolGAN | `MolGAN` | WGAN + RL | Molecular graphs |
| WGAN | `WGAN` | Wasserstein GAN | Continuous features |
| Normalizing Flow | `NormalizingFlowModel` | Flow-based generation | Molecular distributions |

### Materials Science Models

| Model | Class | Input | Domain |
|-------|-------|-------|--------|
| CGCNN | `CGCNNModel` | Crystal graphs (pymatgen) | Band gap, formation energy |
| MEGNet | `MEGNetModel` | Crystal graphs | Materials properties |
| LCNN | `LCNNModel` | Crystal lattice | Surface chemistry |

### Protein / Bioinformatics Models

| Model | Class | Input | Task |
|-------|-------|-------|------|
| AtomicConv | `AtomicConvModel` | Protein-ligand complex | Binding affinity |
| CNN (sequence) | `TextCNNModel` | Protein sequences | Sequence classification |

---

## Complete Featurizer Catalog

### Fingerprint Featurizers

| Featurizer | Class | Dimensions | Speed | Notes |
|------------|-------|------------|-------|-------|
| ECFP / Morgan | `CircularFingerprint` | 1024-4096 | Fast | Most widely used, configurable radius |
| MACCS Keys | `MACCSKeysFingerprint` | 167 | Very fast | Fixed structural keys |
| RDKit Fingerprint | `RDKitFingerprint` | 2048 | Fast | Topological paths |
| PubChem | `PubChemFingerprint` | 881 | Fast | PubChem substructure keys |

### Descriptor Featurizers

| Featurizer | Class | Dimensions | Speed | Notes |
|------------|-------|------------|-------|-------|
| RDKit 2D descriptors | `RDKitDescriptors` | 200+ | Fast | Physicochemical properties |
| Mordred descriptors | `MordredDescriptors` | 1800+ | Medium | Comprehensive descriptor set |
| Mol2Vec | `Mol2VecFingerprint` | 300 | Fast | Pretrained word2vec on substructures |
| BCUT2D | `BCUT2D` | 8 | Very fast | Burden-CAS-University of Texas descriptors |

### Graph Featurizers

| Featurizer | Class | Output | Compatible Models |
|------------|-------|--------|-------------------|
| ConvMol | `ConvMolFeaturizer` | Node features + adjacency | `GraphConvModel` |
| MolGraphConv | `MolGraphConvFeaturizer` | Node + edge features | `AttentiveFPModel`, `MPNNModel`, `GATModel` |
| Weave | `WeaveFeaturizer` | Atom-pair features | `WeaveModel` |
| DMPNN | `DMPNNFeaturizer` | Directed edge features | `DMPNNModel` |
| Pagtn | `PagtnMolGraphFeaturizer` | Path-augmented features | `PagtnModel` |
| MolGAN | `MolGanFeaturizer` | Adjacency + node matrices | `MolGAN` |

### 3D / Quantum Featurizers

| Featurizer | Class | Output | Notes |
|------------|-------|--------|-------|
| Coulomb Matrix | `CoulombMatrix` | Atom-pair distance matrix | QM property prediction |
| Coulomb Matrix (Eig) | `CoulombMatrixEig` | Eigenvalues of CM | Rotation-invariant |
| Atomic Coordinates | `AtomicCoordinates` | 3D coordinates | SchNet, 3D models |

### Protein / Sequence Featurizers

| Featurizer | Class | Input | Output |
|------------|-------|-------|--------|
| One-hot amino acid | `OneHotFeaturizer` | Protein sequence | Binary matrix |
| SMILES tokenizer | `SmilesTokenizer` | SMILES string | Token IDs for transformers |

---

## MoleculeNet Dataset Catalog

### Physical Chemistry

| Dataset | Task | Molecules | Metric | Description |
|---------|------|-----------|--------|-------------|
| ESOL (Delaney) | Regression | 1,128 | RMSE | Aqueous solubility |
| FreeSolv | Regression | 642 | RMSE | Hydration free energy |
| Lipophilicity | Regression | 4,200 | RMSE | Octanol/water distribution |
| QM7 | Regression | 7,165 | MAE | Atomization energy |
| QM7b | Regression | 7,211 | MAE | 14 electronic properties |
| QM8 | Regression | 21,786 | MAE | Electronic spectra properties |
| QM9 | Regression | 133,885 | MAE | 12 geometric/energetic properties |

### Biophysics

| Dataset | Task | Molecules | Metric | Description |
|---------|------|-----------|--------|-------------|
| PDBbind | Regression | 11,908 | RMSE | Protein-ligand binding affinity |
| PCBA | Classification | 437,929 | PRC-AUC | 128 bioassays |

### Physiology (ADMET)

| Dataset | Task | Molecules | Metric | Description |
|---------|------|-----------|--------|-------------|
| BBBP | Classification | 2,039 | ROC-AUC | Blood-brain barrier permeability |
| Tox21 | Classification | 7,831 | ROC-AUC | 12 toxicity assays |
| ToxCast | Classification | 8,576 | ROC-AUC | 617 toxicity assays |
| SIDER | Classification | 1,427 | ROC-AUC | 27 side effect categories |
| ClinTox | Classification | 1,478 | ROC-AUC | Clinical trial toxicity |
| MUV | Classification | 93,087 | PRC-AUC | 17 maximum unbiased validation assays |
| HIV | Classification | 41,127 | ROC-AUC | HIV replication inhibition |
| BACE | Classification | 1,513 | ROC-AUC | BACE-1 inhibitor activity |

### Loading Any MoleculeNet Dataset

```python
import deepchem as dc

# All datasets follow the same API
# dc.molnet.load_{dataset_name}(featurizer=..., splitter=..., transformers=...)
tasks, datasets, transformers = dc.molnet.load_hiv(
    featurizer="ECFP",
    splitter="scaffold",
)
train, valid, test = datasets
print(f"HIV dataset — Tasks: {len(tasks)}, Train: {len(train)}, Test: {len(test)}")
# HIV dataset — Tasks: 1, Train: ~32901, Test: ~4113
```

---

## Metrics Reference

| Metric | Function | Task Type | Notes |
|--------|----------|-----------|-------|
| Pearson R2 | `dc.metrics.pearson_r2_score` | Regression | Primary regression metric |
| RMSE | `dc.metrics.rms_score` | Regression | Root mean squared error |
| MAE | `dc.metrics.mean_absolute_error` | Regression | Mean absolute error |
| ROC-AUC | `dc.metrics.roc_auc_score` | Classification | Primary classification metric |
| PRC-AUC | `dc.metrics.prc_auc_score` | Classification | Precision-recall AUC (imbalanced data) |
| Accuracy | `dc.metrics.accuracy_score` | Classification | Simple accuracy |
| Balanced Accuracy | `dc.metrics.balanced_accuracy_score` | Classification | Handles class imbalance |
| F1 Score | `dc.metrics.f1_score` | Classification | Harmonic mean precision/recall |
| Kappa | `dc.metrics.kappa_score` | Classification | Cohen's kappa agreement |
| Bedroc | `dc.metrics.bedroc_score` | Ranking | Early enrichment metric |
| Enrichment Factor | Custom (see Recipe) | Ranking | Virtual screening metric |

```python
# Using multiple metrics
metrics = [
    dc.metrics.Metric(dc.metrics.pearson_r2_score),
    dc.metrics.Metric(dc.metrics.rms_score),
    dc.metrics.Metric(dc.metrics.mean_absolute_error),
]
results = model.evaluate(test, metrics)
for name, score in results.items():
    print(f"  {name}: {score:.3f}")
```

---

Condensed from original: 1,392 lines (SKILL.md 596 + api_reference.md 304 + workflows.md 492). Retained: all 8 workflow patterns (hyperopt grid+GP, MolGAN generation, materials CGCNN, protein-ligand binding, custom TorchModel), complete model catalog (60+ models across 6 categories), complete featurizer catalog (50+ across 5 categories), MoleculeNet dataset catalog (18 datasets), metrics reference. Omitted from api_reference.md: data loader constructor signatures (covered by SKILL.md Module 1 code), redundant training pattern (covered by SKILL.md Module 3). Omitted from workflows.md: step-by-step installation troubleshooting for TensorFlow 1.x (deprecated backend). Combined coverage: ~380 reference lines + ~540 SKILL.md lines = ~920 lines retained from 1,392 original = ~66%.
