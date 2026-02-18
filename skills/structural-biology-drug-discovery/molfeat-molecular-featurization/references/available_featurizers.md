# Molfeat — Available Featurizers Catalog

Complete catalog of 100+ featurizers available in molfeat, organized by category. Use `ModelStore` to discover and load any featurizer programmatically.

## Transformer-Based Language Models

Pre-trained transformer models generating molecular embeddings from SMILES/SELFIES strings. Require `pip install "molfeat[transformer]"`.

| Model | Architecture | Training Data | Parameters |
|-------|-------------|--------------|------------|
| **ChemBERTa-77M-MLM** | RoBERTa (MLM) | 77M PubChem compounds | 77M |
| **ChemBERTa-77M-MTR** | RoBERTa (MTR) | 77M PubChem + properties | 77M |
| **Roberta-Zinc480M-102M** | RoBERTa (MLM) | 480M ZINC SMILES | 102M |
| **GPT2-Zinc480M-87M** | GPT-2 | 480M ZINC SMILES | 87M |
| **ChemGPT-1.2B** | GPT | PubChem10M | 1.2B |
| **ChemGPT-19M** | GPT | PubChem10M | 19M |
| **ChemGPT-4.7M** | GPT | PubChem10M | 4.7M |
| **MolT5** | T5 | Molecule captioning | Variable |

## Graph Neural Networks

Pre-trained GNN models operating on molecular graph structures. Require `pip install "molfeat[dgl]"` or `"molfeat[graphormer]"`.

| Model | Pre-training | Objective |
|-------|-------------|-----------|
| **gin-supervised-masking** | ChEMBL | Node masking |
| **gin-supervised-infomax** | ChEMBL | Graph-level mutual information |
| **gin-supervised-edgepred** | ChEMBL | Edge prediction |
| **gin-supervised-contextpred** | ChEMBL | Context prediction |
| **JTVAE_zinc_no_kl** | ZINC | Junction-tree VAE generation |
| **Graphormer-pcqm4mv2** | PCQM4Mv2 | HOMO-LUMO gap prediction |

## Molecular Fingerprints

Fixed-length binary or count vectors representing molecular substructures.

### Circular Fingerprints
- **ecfp** / **ecfp-count** — Extended-connectivity (radius-based), default 2048 bits. Most popular
- **fcfp** / **fcfp-count** — Functional-class variant, pharmacophore-aware

### Path-Based & Key-Based
- **rdkit** — RDKit topological (linear paths)
- **maccs** — 166-bit MACCS keys (predefined substructures)
- **avalon** — Avalon fingerprints (optimized similarity)
- **pattern** — Automated pattern fingerprints
- **layered** — Multi-layer substructure fingerprints

### Atom-Pair & Topological
- **atompair** / **atompair-count** — Atom pairs with distance encoding
- **topological** / **topological-count** — 4-atom torsion sequences

### Specialized
- **map4** — MinHashed atom-pair up to 4 bonds (1024 dims, fast large-scale)
- **secfp** — SMILES-based extended connectivity
- **erg** — Extended reduced graph (pharmacophoric points)
- **estate** — Electrotopological state indices

## Molecular Descriptors

Numerical physico-chemical properties and molecular characteristics.

| Calculator | Dimensions | Content |
|-----------|------------|---------|
| **desc2D** / **RDKitDescriptors2D** | 200+ | MW, logP, TPSA, H-bond donors/acceptors, rotatable bonds, ring counts |
| **desc3D** / **RDKitDescriptors3D** | ~30 | Inertial moments, PMI ratios, asphericity (requires conformer) |
| **mordred** / **MordredDescriptors** | 1800+ | Constitutional, topological, connectivity, WHIM, GETAWAY indices |

## Pharmacophore Descriptors

Features based on pharmacologically relevant functional groups.

| Calculator | Mode | Dimensions | Description |
|-----------|------|------------|-------------|
| **cats2D** | 2D shortest path | 21 | CATS pharmacophore pair distributions |
| **cats3D** | 3D Euclidean | 21 | 3D CATS (requires conformer) |
| **gobbi2D** | 2D | Variable | 8 pharmacophore types (hydrophobic, aromatic, H-bond, ionic) |
| **pmapper2D** | 2D | High-dim | Pharmacophore signatures |
| **pmapper3D** | 3D | High-dim | 3D pharmacophore signatures |
| **Pharmacophore2D** | 2D | Variable | RDKit pharmacophore fingerprints |
| **Pharmacophore3D** | 3D | Variable | Consensus pharmacophore from conformers |

## Shape Descriptors

3D molecular shape and electrostatic properties.

| Calculator | Dimensions | Description |
|-----------|------------|-------------|
| **usr** | 12 | Ultrafast shape recognition — shape distribution encoding |
| **usrcat** | 60 | USR + pharmacophoric constraints (12 per feature type) |
| **electroshape** | Variable | Combined shape, chirality, and electrostatics |

## Scaffold & Graph Featurizers

| Calculator | Purpose | Use Case |
|-----------|---------|----------|
| **scaffoldkeys** | 40+ scaffold-based properties | Core structure analysis |
| **atom-default** | Atom features (number, degree, charge, hybridization) | GNN input |
| **bond-default** | Bond features (type, conjugation, ring, stereo) | GNN input |
| **fcd** | Fréchet ChemNet Distance features | Generative model evaluation |

## Choosing by Task

| Task | Top Choices | Why |
|------|------------|-----|
| General QSAR | ecfp, maccs | Fast, well-validated, good default |
| Interpretable models | desc2D, mordred | Named properties, feature importance |
| Scaffold hopping | maccs, fcfp | Structural key / functional class based |
| Large-scale screening | map4, ecfp | Efficient computation, good discrimination |
| Transfer learning | ChemBERTa, ChemGPT | Captures latent chemical space |
| Graph-based DL | gin-supervised-* | Preserves molecular graph structure |
| Pharmacophore matching | fcfp, cats2D, gobbi2D | Functional group awareness |
| 3D shape similarity | usr, usrcat, electroshape | Shape-based virtual screening |

## Dependencies by Category

```bash
pip install "molfeat[transformer]"  # ChemBERTa, ChemGPT, MolT5, Roberta
pip install "molfeat[dgl]"          # GIN variants, JTVAE
pip install "molfeat[graphormer]"   # Graphormer
pip install "molfeat[fcd]"          # FCD
pip install "molfeat[map4]"         # MAP4
pip install "molfeat[all]"          # Everything
```

## Programmatic Discovery

```python
from molfeat.store.modelstore import ModelStore

store = ModelStore()
all_models = store.available_models

# Filter by type
transformers = [m for m in all_models if "transformer" in str(m.tags)]
fingerprints = [m for m in all_models if "fingerprint" in str(m.tags)]
```

---

*Condensed from original `references/available_featurizers.md` (334 lines → ~165 lines). Retained: all featurizer names and categories, dimension information, task-based selection, dependency mapping. Omitted: detailed prose descriptions per model (retained as table entries), performance speed tiers (→ Key Concepts selection guide in SKILL.md), extended "Usage Notes" (→ Best Practices in SKILL.md).*
