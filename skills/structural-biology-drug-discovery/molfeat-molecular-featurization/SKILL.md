---
name: molfeat-molecular-featurization
description: Molecular featurization hub (100+ featurizers) for ML. Convert SMILES to numerical representations via fingerprints (ECFP, MACCS, MAP4), descriptors (RDKit 2D, Mordred), pretrained models (ChemBERTa, GIN, Graphormer), and pharmacophore features. Scikit-learn compatible transformers with parallelization, caching, and state persistence. For QSAR, virtual screening, similarity search, and deep learning on molecules.
license: Apache-2.0
---

# Molfeat — Molecular Featurization Hub

## Overview

Molfeat is a comprehensive Python library for molecular featurization that unifies 100+ pre-trained embeddings and hand-crafted featurizers under a scikit-learn compatible API. Convert SMILES strings into numerical representations (fingerprints, descriptors, deep learning embeddings) for QSAR modeling, virtual screening, similarity searching, and chemical space analysis.

## When to Use

- Building QSAR/QSPR models requiring molecular features as input
- Virtual screening — ranking compound libraries by predicted activity
- Similarity searching against molecular databases
- Chemical space analysis — clustering, visualization, dimensionality reduction
- Deep learning on molecules using pretrained embeddings (ChemBERTa, GIN)
- Featurization pipelines integrating with scikit-learn or PyTorch
- Comparing multiple molecular representations for benchmarking
- For molecular manipulation and filtering use datamol instead; for substructure-based molecular operations use rdkit-molecular-toolkit

## Prerequisites

```bash
uv pip install molfeat

# Optional extras for specific featurizer types
uv pip install "molfeat[transformer]"   # ChemBERTa, ChemGPT, MolT5
uv pip install "molfeat[dgl]"           # GIN graph neural networks
uv pip install "molfeat[graphormer]"    # Graphormer models
uv pip install "molfeat[fcd]"           # FCD descriptors
uv pip install "molfeat[map4]"          # MAP4 fingerprints
uv pip install "molfeat[all]"           # All dependencies
```

## Quick Start

```python
from molfeat.calc import FPCalculator
from molfeat.trans import MoleculeTransformer

smiles = ["CCO", "CC(=O)O", "c1ccccc1", "CC(C)O"]

# Create fingerprint calculator + transformer
calc = FPCalculator("ecfp", radius=3, fpSize=2048)
transformer = MoleculeTransformer(calc, n_jobs=-1)

# Featurize batch in parallel
features = transformer(smiles)
print(f"Shape: {features.shape}")  # (4, 2048)

# Save configuration for reproducibility
transformer.to_state_yaml_file("featurizer_config.yml")
```

## Key Concepts

### Architecture: Calculator → Transformer → Store

Molfeat organizes featurization into three layers:

| Layer | Class | Purpose | Use When |
|-------|-------|---------|----------|
| **Calculator** | `molfeat.calc.*` | Single molecule → feature vector | Custom loops, single molecules |
| **Transformer** | `molfeat.trans.MoleculeTransformer` | Batch processing with parallelization | Datasets, scikit-learn pipelines |
| **Store** | `molfeat.store.ModelStore` | Discovery and loading of pretrained models | Finding available featurizers |

**Calculators** are callable: `calc("CCO")` returns a numpy array. **Transformers** wrap calculators for batch processing: `transformer(smiles_list)` returns a 2D array. **Pretrained** transformers (`PretrainedMolTransformer`) add batched GPU inference and caching.

### Featurizer Selection Guide

| Task | Recommended | Dimensions | Speed |
|------|-------------|------------|-------|
| General QSAR | `ecfp` (radius=3) | 2048 | Fast |
| Scaffold similarity | `maccs` | 167 | Very fast |
| Large-scale screening | `map4` | 1024 | Fast |
| Interpretable models | `desc2D` (RDKitDescriptors2D) | 200+ | Fast |
| Comprehensive descriptors | `mordred` | 1800+ | Medium |
| Transfer learning | `ChemBERTa-77M-MLM` | 768 | Slow* |
| Graph-based DL | `gin-supervised-masking` | Variable | Slow* |
| Pharmacophore | `fcfp` or `cats2D` | 2048 / 21 | Fast |
| 3D shape | `usr` / `usrcat` | 12 / 60 | Fast |

*First run slow; subsequent runs cached.

### State Persistence

Save and reload exact featurizer configuration for reproducibility:

```python
# Save
transformer.to_state_yaml_file("config.yml")
transformer.to_state_json_file("config.json")

# Reload
loaded = MoleculeTransformer.from_state_yaml_file("config.yml")
```

## Core API

### 1. Fingerprint Calculators

```python
from molfeat.calc import FPCalculator

# ECFP — most popular, general-purpose
ecfp = FPCalculator("ecfp", radius=3, fpSize=2048)
fp = ecfp("CCO")
print(f"ECFP shape: {fp.shape}")  # (2048,)

# MACCS keys — 167-bit structural keys, fast scaffold similarity
maccs = FPCalculator("maccs")
fp = maccs("c1ccccc1")
print(f"MACCS shape: {fp.shape}")  # (167,)

# Count-based fingerprints (non-binary)
ecfp_count = FPCalculator("ecfp-count", radius=3, fpSize=2048)

# MAP4 — MinHashed atom-pair, efficient for large databases
map4 = FPCalculator("map4")
print(f"MAP4 shape: {map4('CCO').shape}")  # (1024,)
```

**Available fingerprint types**: `ecfp`, `fcfp`, `maccs`, `rdkit`, `avalon`, `pattern`, `layered`, `atompair`, `topological`, `map4`, `secfp`, `erg`, `estate` (and count variants with `-count` suffix).

### 2. Descriptor Calculators

```python
from molfeat.calc import RDKitDescriptors2D, MordredDescriptors

# RDKit 2D — 200+ named properties (MW, logP, TPSA, etc.)
desc2d = RDKitDescriptors2D()
descriptors = desc2d("CCO")
print(f"2D descriptors: {len(descriptors)}")  # 200+
print(f"Feature names: {desc2d.columns[:5]}")

# Mordred — 1800+ comprehensive descriptors
mordred = MordredDescriptors()
descriptors = mordred("c1ccccc1O")
print(f"Mordred descriptors: {len(descriptors)}")  # 1800+
```

### 3. Pharmacophore & Shape Calculators

```python
from molfeat.calc import CATSCalculator, USRDescriptors

# CATS — pharmacophore point pair distributions
cats = CATSCalculator(mode="2D", scale="raw")
descriptors = cats("CC(C)Cc1ccc(C)cc1C")
print(f"CATS shape: {descriptors.shape}")  # (21,)

# USR — ultrafast shape recognition
usr = USRDescriptors()
shape = usr("CC(=O)Oc1ccccc1C(=O)O")
print(f"USR shape: {shape.shape}")  # (12,)
```

### 4. Batch Processing with Transformers

```python
from molfeat.trans import MoleculeTransformer, FeatConcat
from molfeat.calc import FPCalculator

smiles = ["CCO", "CC(=O)O", "c1ccccc1", "CC(C)O", "CCCC"]

# Parallel batch processing
transformer = MoleculeTransformer(FPCalculator("ecfp"), n_jobs=-1)
features = transformer(smiles)
print(f"Batch shape: {features.shape}")  # (5, 2048)

# Concatenate multiple featurizers
concat = FeatConcat([
    FPCalculator("maccs"),      # 167 dims
    FPCalculator("ecfp")        # 2048 dims
])
combo_transformer = MoleculeTransformer(concat, n_jobs=-1)
combo_features = combo_transformer(smiles)
print(f"Combined shape: {combo_features.shape}")  # (5, 2215)

# Error-tolerant processing
safe_transformer = MoleculeTransformer(
    FPCalculator("ecfp"), n_jobs=-1,
    ignore_errors=True, verbose=True
)
features = safe_transformer(["CCO", "invalid", "c1ccccc1"])
# Returns None for failed molecules
```

### 5. Pretrained Model Embeddings

```python
from molfeat.trans.pretrained import PretrainedMolTransformer

# ChemBERTa — RoBERTa trained on 77M PubChem compounds
chemberta = PretrainedMolTransformer("ChemBERTa-77M-MLM", n_jobs=-1)
embeddings = chemberta(["CCO", "CC(=O)O", "c1ccccc1"])
print(f"ChemBERTa shape: {embeddings.shape}")  # (3, 768)

# GIN — graph neural network pretrained on ChEMBL
gin = PretrainedMolTransformer("gin-supervised-masking", n_jobs=-1)
graph_emb = gin(["CCO", "CC(=O)O"])
print(f"GIN shape: {graph_emb.shape}")
```

### 6. ModelStore — Discovering Featurizers

```python
from molfeat.store.modelstore import ModelStore

store = ModelStore()
print(f"Total available: {len(store.available_models)}")

# Search for specific model
results = store.search(name="ChemBERTa")
for model in results:
    print(f"  {model.name}: {model.description}")

# View usage and load
card = store.search(name="ChemBERTa-77M-MLM")[0]
card.usage()
transformer = store.load("ChemBERTa-77M-MLM")
```

## Common Workflows

### Workflow 1: QSAR Model Building

```python
from molfeat.calc import FPCalculator
from molfeat.trans import MoleculeTransformer
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import cross_val_score

# Featurize molecules
transformer = MoleculeTransformer(FPCalculator("ecfp", radius=3), n_jobs=-1)
X = transformer(smiles_train)
print(f"Features shape: {X.shape}")

# Train and evaluate
model = RandomForestRegressor(n_estimators=100)
scores = cross_val_score(model, X, y_train, cv=5, scoring='r2')
print(f"R² = {scores.mean():.3f} ± {scores.std():.3f}")

# Save for deployment
transformer.to_state_yaml_file("production_featurizer.yml")
```

### Workflow 2: Virtual Screening Pipeline

```python
from sklearn.ensemble import RandomForestClassifier

# Step 1: Featurize known actives/inactives
transformer = MoleculeTransformer(FPCalculator("ecfp"), n_jobs=-1)
X_train = transformer(train_smiles)

# Step 2: Train classifier
clf = RandomForestClassifier(n_estimators=500, n_jobs=-1)
clf.fit(X_train, train_labels)

# Step 3: Screen library (e.g., 1M compounds)
X_screen = transformer(screening_smiles)
predictions = clf.predict_proba(X_screen)[:, 1]

# Step 4: Rank and select top hits
top_indices = predictions.argsort()[::-1][:1000]
top_hits = [screening_smiles[i] for i in top_indices]
print(f"Top 1000 hits selected from {len(screening_smiles)} compounds")
```

### Workflow 3: Featurizer Benchmarking

```python
from molfeat.calc import FPCalculator, RDKitDescriptors2D
from sklearn.metrics import roc_auc_score

featurizers = {
    'ECFP': FPCalculator("ecfp"),
    'MACCS': FPCalculator("maccs"),
    'Descriptors': RDKitDescriptors2D(),
}

for name, calc in featurizers.items():
    transformer = MoleculeTransformer(calc, n_jobs=-1)
    X_train = transformer(smiles_train)
    X_test = transformer(smiles_test)
    clf = RandomForestClassifier(n_estimators=100)
    clf.fit(X_train, y_train)
    auc = roc_auc_score(y_test, clf.predict_proba(X_test)[:, 1])
    print(f"{name}: AUC = {auc:.3f}")
```

## Common Recipes

### Recipe: Scikit-learn Pipeline Integration

```python
from sklearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestClassifier

pipeline = Pipeline([
    ('featurizer', MoleculeTransformer(FPCalculator("ecfp"), n_jobs=-1)),
    ('classifier', RandomForestClassifier(n_estimators=100))
])
pipeline.fit(smiles_train, y_train)
predictions = pipeline.predict(smiles_test)
```

### Recipe: Similarity Search

```python
from sklearn.metrics.pairwise import cosine_similarity

calc = FPCalculator("ecfp")
query_fp = calc("CC(=O)Oc1ccccc1C(=O)O").reshape(1, -1)  # Aspirin

transformer = MoleculeTransformer(calc, n_jobs=-1)
db_fps = transformer(database_smiles)

similarities = cosine_similarity(query_fp, db_fps)[0]
top_k = similarities.argsort()[-10:][::-1]
for i in top_k:
    print(f"  {database_smiles[i]}: {similarities[i]:.3f}")
```

### Recipe: Chunk Processing for Large Datasets

```python
import numpy as np

def featurize_chunks(smiles_list, transformer, chunk_size=10000):
    all_features = []
    for i in range(0, len(smiles_list), chunk_size):
        chunk = smiles_list[i:i+chunk_size]
        features = transformer(chunk)
        all_features.append(features)
        print(f"Processed {min(i+chunk_size, len(smiles_list))}/{len(smiles_list)}")
    return np.vstack(all_features)
```

## Key Parameters

| Parameter | Module | Default | Description |
|-----------|--------|---------|-------------|
| `method` | FPCalculator | — | Fingerprint type: `ecfp`, `maccs`, `map4`, etc. |
| `radius` | FPCalculator | 3 | Circular fingerprint radius |
| `fpSize` | FPCalculator | 2048 | Fingerprint bit length |
| `counting` | FPCalculator | False | Count vector instead of binary |
| `n_jobs` | MoleculeTransformer | 1 | Parallel workers (-1 = all cores) |
| `ignore_errors` | MoleculeTransformer | False | Skip invalid molecules (returns None) |
| `verbose` | MoleculeTransformer | False | Log processing details |
| `dtype` | MoleculeTransformer | float64 | Output type (float32 for memory) |
| `mode` | CATSCalculator | "2D" | Distance calculation mode |
| `scale` | CATSCalculator | "raw" | Scaling: `raw`, `num`, `count` |

## Best Practices

- **Use `n_jobs=-1`** for parallel processing on all CPU cores — significant speedup for batch featurization
- **Start with ECFP** for initial baselines — best general-purpose fingerprint before trying deep learning
- **Use `ignore_errors=True`** for large datasets — invalid SMILES won't crash the pipeline
- **Save configurations** with `to_state_yaml_file()` for reproducibility — recreate exact featurizer later
- **Use float32** when memory matters: `MoleculeTransformer(calc, dtype=np.float32)`
- **Cache pretrained embeddings** — first ChemBERTa/GIN inference is slow, subsequent runs use cache
- **Process in chunks** for datasets >100K — prevents memory exhaustion (see Recipes)
- **Combine fingerprints** with `FeatConcat` to capture complementary molecular information

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| `ValueError: unsupported featurizer` | Unknown method name | Check `FPCalculator` supported types or use `ModelStore.search()` |
| `ImportError` for pretrained model | Missing optional dependency | Install extras: `pip install "molfeat[transformer]"` or `"molfeat[dgl]"` |
| `None` in output array | Invalid SMILES with `ignore_errors=True` | Filter results: `[f for f in features if f is not None]` |
| Memory error on large dataset | Too many molecules at once | Process in chunks of 10K-50K (see Recipes) |
| Slow pretrained model inference | First run downloads model weights | Normal — subsequent runs use cache |
| Shape mismatch in pipeline | Mixed valid/invalid molecules | Ensure `ignore_errors=True` and filter None before ML model |
| Reproducibility issues | Different molfeat versions | Pin version and save config: `transformer.to_state_yaml_file()` |

## Related Skills

- `datamol-molecular-toolkit` — High-level molecular manipulation (standardization, I/O, conformers)
- `rdkit-molecular-toolkit` — Low-level cheminformatics (substructure, reactions, 3D)
- `scikit-learn` — ML models consuming molfeat features

## References

- Official documentation: https://molfeat-docs.datamol.io/
- GitHub repository: https://github.com/datamol-io/molfeat
- PyPI package: https://pypi.org/project/molfeat/
- Tutorial: https://portal.valencelabs.com/datamol/post/types-of-featurizers-b1e8HHrbFMkbun6

## Bundled Resources

**Main SKILL.md** + 2 reference files. Original total: 1,273 lines (SKILL.md 510 + api_reference.md 429 + available_featurizers.md 334). Scripts: none. Examples: 724 lines (examples.md).

**references/available_featurizers.md**: Complete catalog of all 100+ featurizers organized by category — transformer models, GNNs, descriptors, fingerprints, pharmacophore, shape, scaffold, graph featurizers. Includes dimensions, dependencies, and selection guidance per category. Purely lookup-oriented content preserved as reference.

**references/api_reference.md**: Detailed API reference for `molfeat.calc`, `molfeat.trans`, and `molfeat.store` modules. Covers SerializableCalculator base class, all calculator subclasses with parameters, MoleculeTransformer methods, PretrainedMolTransformer, FeatConcat, ModelStore/ModelCard API, data type control, and PyTorch integration patterns.

**Original file disposition**:
- `SKILL.md` (510 lines) → Core API modules 1-6, Key Concepts (architecture, selection guide), Quick Start, Workflows 1-3. "Choosing the Right Featurizer" → Key Concepts selection guide table. "Advanced Features" (custom preprocessing, batch processing, caching) → Recipes + Best Practices. "Common Featurizers Reference" table → Key Concepts selection guide. "Performance Tips" → Best Practices. Per-use-case disposition: QSAR Modeling → Workflow 1, Virtual Screening → Workflow 2, Similarity Search → Recipe, Chemical Space → When to Use bullet, scikit-learn Pipeline → Recipe, Featurizer Comparison → Workflow 3
- `references/api_reference.md` (429 lines) → Migrated to new `references/api_reference.md`. Core patterns (FPCalculator, MoleculeTransformer, basic ModelStore) relocated to SKILL.md Core API modules 1-6. Detailed class methods, SerializableCalculator base class, PrecomputedMolTransformer, and PyTorch integration retained in reference
- `references/available_featurizers.md` (334 lines) → Migrated to new `references/available_featurizers.md`. Top-level summary → Key Concepts selection guide table. Full categorized catalog retained in reference
- `references/examples.md` (724 lines) → Fully consolidated inline: installation → Prerequisites; calculator examples → Core API 1-3; transformer examples → Core API 4; pretrained examples → Core API 5; ML integration → Workflows 1-3 + Recipes; advanced patterns (custom preprocessing, caching, chunk processing) → Recipes + Best Practices; troubleshooting → Troubleshooting table. No separate reference file needed — all content absorbed into SKILL.md sections

**Retention**: ~490 lines (SKILL.md) + ~170 lines (available_featurizers) + ~190 lines (api_reference) = ~850 / 1,273 original (excl. examples.md treated as consolidated) = ~67%. Including examples.md in denominator: ~850 / 1,997 = ~43%.
