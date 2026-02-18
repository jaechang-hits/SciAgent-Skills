# Molfeat — API Reference

Detailed API reference for molfeat's core modules: calculators, transformers, and model store.

## molfeat.calc — Calculators

### SerializableCalculator (Base Class)

All calculators inherit from `SerializableCalculator`. Required methods for subclasses:

| Method | Description |
|--------|-------------|
| `__call__(mol)` | Featurize a single molecule (SMILES or RDKit Mol) |
| `__len__()` | Return output feature length |
| `columns` | Property returning feature names (list of strings) |
| `batch_compute(mols)` | Optional batch processing override |

**State management** (all calculators):
```python
# Serialize
state_dict = calc.to_state_dict()
json_str = calc.to_state_json()
yaml_str = calc.to_state_yaml()

# Deserialize
calc = SerializableCalculator.from_state_dict(state_dict)
```

### FPCalculator — Full Parameter Reference

```python
from molfeat.calc import FPCalculator

calc = FPCalculator(
    method="ecfp",          # Fingerprint type (see available_featurizers.md)
    radius=3,               # Radius for circular FPs (ecfp, fcfp)
    fpSize=2048,            # Output bit length
    includeChirality=False, # Include chirality in hash
    counting=False,         # Count vector vs binary
)

fp = calc("CCO")            # numpy array
length = len(calc)           # 2048
names = calc.columns         # list of feature indices
```

### get_calculator Factory

```python
from molfeat.calc import get_calculator

# Instantiate any calculator by name
calc = get_calculator("ecfp", radius=3)
calc = get_calculator("maccs")
calc = get_calculator("desc2D")
# Raises ValueError for unsupported names
```

### Specialized Calculators

**CATSCalculator** — Pharmacophore pair distributions:
```python
from molfeat.calc import CATSCalculator

calc = CATSCalculator(
    mode="2D",       # "2D" (shortest path) or "3D" (Euclidean)
    dist_bins=None,  # Custom distance bins
    scale="raw"      # "raw", "num", or "count"
)
# Returns 21 descriptors by default (7 pharmacophore types × 3 distance bins)
```

**USRDescriptors** — Shape recognition:
```python
from molfeat.calc import USRDescriptors
calc = USRDescriptors()  # Returns 12-dim shape encoding
```

**ElectroShapeDescriptors** — Shape + electrostatics:
```python
from molfeat.calc import ElectroShapeDescriptors
calc = ElectroShapeDescriptors()  # Combines shape, chirality, electrostatics
```

**ScaffoldKeyCalculator** — Scaffold features:
```python
from molfeat.calc import ScaffoldKeyCalculator
calc = ScaffoldKeyCalculator()  # 40+ scaffold-based properties
```

**AtomCalculator / BondCalculator** — For GNN graph construction:
```python
from molfeat.calc import AtomCalculator, BondCalculator
atom_calc = AtomCalculator()  # Atom-level features (number, degree, charge, hybridization)
bond_calc = BondCalculator()  # Bond-level features (type, conjugation, ring, stereo)
```

## molfeat.trans — Transformers

### MoleculeTransformer

Scikit-learn compatible transformer wrapping any calculator for batch processing.

**Constructor parameters**:
```python
from molfeat.trans import MoleculeTransformer

transformer = MoleculeTransformer(
    featurizer=calc,       # Any Calculator instance
    n_jobs=1,              # Parallel workers (-1 = all cores)
    dtype=None,            # Output dtype (np.float32, torch.float32, etc.)
    verbose=False,         # Log processing details
    ignore_errors=False,   # Continue on invalid molecules (returns None)
)
```

**Key methods**:

| Method | Description |
|--------|-------------|
| `transform(mols)` | Batch featurize — returns numpy array or list |
| `__call__(mols)` | Alias for `transform()` |
| `preprocess(mol)` | Prepare single molecule (override for custom processing) |
| `_transform(mol)` | Featurize single molecule |
| `to_state_yaml_file(path)` | Save full configuration to YAML |
| `from_state_yaml_file(path)` | Class method — load from YAML |
| `to_state_json_file(path)` | Save to JSON |
| `from_state_json_file(path)` | Class method — load from JSON |

**Custom preprocessing**:
```python
import datamol as dm

class StandardizedTransformer(MoleculeTransformer):
    def preprocess(self, mol):
        if isinstance(mol, str):
            mol = dm.to_mol(mol)
        mol = dm.standardize_mol(mol)
        mol = dm.remove_salts(mol)
        return mol
```

### FeatConcat

Concatenates multiple calculators into a single feature vector:

```python
from molfeat.trans import FeatConcat

concat = FeatConcat([
    FPCalculator("maccs"),      # 167 dims
    FPCalculator("ecfp"),       # 2048 dims
    RDKitDescriptors2D()        # 200+ dims
])
# Total: ~2415 dims

transformer = MoleculeTransformer(concat, n_jobs=-1)
features = transformer(smiles)  # (n, ~2415)
```

### PretrainedMolTransformer

Subclass for deep learning models with batched inference and caching.

```python
from molfeat.trans.pretrained import PretrainedMolTransformer

transformer = PretrainedMolTransformer(
    kind="ChemBERTa-77M-MLM",  # Model name from ModelStore
    n_jobs=-1,
    dtype=None,
)
embeddings = transformer(smiles)  # (n, embedding_dim)
```

**Unique methods**:
- `_embed(smiles_batch)` — Batched neural network inference
- `_convert(smiles)` — Convert SMILES to model input (SELFIES for language models, DGL graphs for GNNs)

### PrecomputedMolTransformer

For cached/precomputed features — loads pre-generated embeddings by molecule key.

## molfeat.store — Model Store

### ModelStore

Central hub for discovering and loading featurizers.

```python
from molfeat.store.modelstore import ModelStore

store = ModelStore()

# Discovery
all_models = store.available_models    # List[ModelCard]
results = store.search(name="gin")     # Search by name
results = store.search(tags="gnn")     # Search by tag

# Loading
transformer = store.load("ChemBERTa-77M-MLM", n_jobs=-1)

# Registration (custom models)
store.register(name="my_model", card=my_model_card)
```

### ModelCard

Metadata container for each featurizer.

| Attribute | Type | Description |
|-----------|------|-------------|
| `name` | str | Model identifier |
| `description` | str | Model description |
| `version` | str | Model version |
| `authors` | str | Model authors |
| `tags` | list | Categorization tags |

**Methods**:
- `usage()` — Display usage examples and documentation
- `load(**kwargs)` — Load the model as a transformer

## Data Type Control

```python
import numpy as np
import torch

# NumPy output (default)
transformer = MoleculeTransformer(calc, dtype=np.float32)

# PyTorch tensors
transformer = MoleculeTransformer(calc, dtype=torch.float32)
features = transformer(smiles)  # Returns torch.Tensor
```

## PyTorch Dataset Integration

```python
import torch
from torch.utils.data import Dataset, DataLoader

class MoleculeDataset(Dataset):
    def __init__(self, smiles, labels, transformer):
        self.features = transformer(smiles)  # Pre-compute all
        self.labels = torch.tensor(labels, dtype=torch.float32)

    def __len__(self):
        return len(self.labels)

    def __getitem__(self, idx):
        return (
            torch.tensor(self.features[idx], dtype=torch.float32),
            self.labels[idx]
        )

# Usage
transformer = MoleculeTransformer(FPCalculator("ecfp"))
dataset = MoleculeDataset(smiles, labels, transformer)
loader = DataLoader(dataset, batch_size=32, shuffle=True)
```

---

*Condensed from original `references/api_reference.md` (429 lines → ~190 lines). Retained: SerializableCalculator base class, FPCalculator full parameters, get_calculator factory, all specialized calculators, MoleculeTransformer full API, FeatConcat, PretrainedMolTransformer, PrecomputedMolTransformer, ModelStore/ModelCard API, data type control, PyTorch integration. Omitted: duplicate common patterns (→ SKILL.md Core API), persistence examples (→ SKILL.md Key Concepts), basic error handling (→ SKILL.md Troubleshooting). Relocated inline: core FPCalculator/MoleculeTransformer usage → SKILL.md Core API 1 & 4; ModelStore basic search → SKILL.md Core API 6.*
