---
name: esm-protein-language-model
description: "Protein language models (ESM3, ESM C) for sequence generation, structure prediction, inverse folding, and embeddings. Design novel proteins, extract ML features, or fold sequences. Local GPU or EvolutionaryScale Forge API. Use AlphaFold for traditional folding; RDKit for small molecules."
license: MIT
---

# ESM — Protein Language Models

## Overview

ESM (Evolutionary Scale Modeling) provides pretrained protein language models for generative protein design and representation learning. ESM3 is a multimodal generative model conditioned on sequence, structure, and function simultaneously. ESM C is an efficient embedding model optimized for extracting protein representations for downstream ML tasks.

## When to Use

- Generating novel protein sequences conditioned on desired structure or function
- Extracting fixed-length embeddings from protein sequences for classification, clustering, or regression
- Predicting 3D structure from amino acid sequence
- Inverse folding: designing sequences that fold into a target structure
- Annotating proteins with functional keywords (GO terms, EC numbers)
- Comparing protein similarity via embedding distance instead of sequence alignment
- Chain-of-thought protein design: iterative refinement of sequence/structure/function
- For **traditional physics-based structure prediction**, use AlphaFold instead
- For **sequence alignment and homology search**, use BLAST/HMMER via BioPython instead

## Prerequisites

- **Python packages**: `esm` (EvolutionaryScale package)
- **Hardware**: GPU recommended for local inference (ESM3: 8GB+ VRAM; ESM C: 4GB+ VRAM). CPU works for small batches
- **Cloud alternative**: EvolutionaryScale Forge API (requires API token from forge.evolutionaryscale.ai)
- **Model weights**: Downloaded automatically on first use (~1-4 GB depending on model)

```bash
pip install esm
# For Forge cloud API
pip install esm[forge]
```

## Quick Start

```python
from esm.models.esmc import ESMC
from esm.sdk.api import ESMProtein

# Load ESM C model for embeddings
model = ESMC.from_pretrained("esmc_600m")

# Create protein from sequence
protein = ESMProtein(sequence="MKTAYIAKQRQISFVKSHFSRQLEERLGLIEVQAPILSRVGDGTQDNLSGAEKAVQVKVKALPDAQFEVVHSLAKWKRQQIAATGFHIIPGDKPDNRAGGYDN")

# Get per-residue embeddings
output = model(protein)
embeddings = output.embeddings  # shape: (1, seq_len, embedding_dim)
print(f"Embedding shape: {embeddings.shape}")
# Embedding shape: (1, 101, 1152)
```

## Core API

### 1. Protein Sequence Generation (ESM3)

Generate novel protein sequences conditioned on structure, function, or partial sequence.

```python
from esm.models.esm3 import ESM3
from esm.sdk.api import ESM3InferenceClient, ESMProtein, GenerationConfig

# Load ESM3 locally
model = ESM3.from_pretrained("esm3_sm_open_v1")

# Generate from partial sequence (fill in masked positions)
prompt = ESMProtein(sequence="MKTAYIAK____ISFVK____RQLEERLG")  # ____ = positions to generate
config = GenerationConfig(track="sequence", num_steps=10, temperature=0.7)
generated = model.generate(prompt, config)
print(f"Generated sequence: {generated.sequence[:50]}...")
```

```python
# Conditional generation: design sequence for a target structure
from esm.sdk.api import ESMProtein, GenerationConfig
from esm.utils.structure.protein_chain import ProteinChain

# Load target structure from PDB
chain = ProteinChain.from_pdb("target.pdb")
prompt = ESMProtein.from_protein_chain(chain)
prompt.sequence = None  # Clear sequence, keep structure

config = GenerationConfig(track="sequence", num_steps=16, temperature=0.5)
designed = model.generate(prompt, config)
print(f"Designed sequence ({len(designed.sequence)} residues): {designed.sequence[:50]}...")
```

### 2. Protein Embeddings (ESM C)

Extract fixed-length representations for downstream ML tasks.

```python
from esm.models.esmc import ESMC
from esm.sdk.api import ESMProtein
import torch

model = ESMC.from_pretrained("esmc_600m")  # or "esmc_300m" for lighter model

sequences = [
    "MKTAYIAKQRQISFVKSHFSRQLEERLGLIEVQAPILSRVGDGTQDNLSGAEKAVQVKVKALPDAQFEVVHSLAKWKRQQIAATGFHIIPGDKPDNRAGGYDN",
    "MKWVTFISLLFLFSSAYSRGVFRRDAHKSEVAHRFKDLGEENFKALVLIAFAQYLQQCPFEDHVKLVNEVTEFAKTCVADESAENCDKS",
]

embeddings = []
for seq in sequences:
    protein = ESMProtein(sequence=seq)
    output = model(protein)
    # Mean-pool per-residue embeddings to get fixed-length vector
    mean_emb = output.embeddings.mean(dim=1)  # shape: (1, embedding_dim)
    embeddings.append(mean_emb)

emb_matrix = torch.cat(embeddings, dim=0)
print(f"Embedding matrix: {emb_matrix.shape}")  # (2, 1152)

# Compute pairwise similarity
similarity = torch.cosine_similarity(emb_matrix[0:1], emb_matrix[1:2])
print(f"Cosine similarity: {similarity.item():.4f}")
```

### 3. Structure Prediction

Predict 3D coordinates from amino acid sequence.

```python
from esm.models.esm3 import ESM3
from esm.sdk.api import ESMProtein, GenerationConfig

model = ESM3.from_pretrained("esm3_sm_open_v1")

protein = ESMProtein(sequence="MKTAYIAKQRQISFVKSHFSRQLEERLGLIEVQAPILSRVGDGTQDNLSGAEKAVQVKVKALPDAQFEVVHSLAKWKRQQIAATGFHIIPGDKPDNRAGGYDN")

# Generate structure from sequence
config = GenerationConfig(track="structure", num_steps=16)
result = model.generate(protein, config)

# Save predicted structure
result.to_pdb("predicted.pdb")
print(f"Saved structure: {len(result.sequence)} residues → predicted.pdb")
```

### 4. Inverse Folding

Design amino acid sequences that fold into a target 3D structure.

```python
from esm.models.esm3 import ESM3
from esm.sdk.api import ESMProtein, GenerationConfig
from esm.utils.structure.protein_chain import ProteinChain

model = ESM3.from_pretrained("esm3_sm_open_v1")

# Load target structure
chain = ProteinChain.from_pdb("target_structure.pdb")
prompt = ESMProtein.from_protein_chain(chain)

# Clear sequence but keep structure coordinates
prompt.sequence = None

# Generate multiple designs
designs = []
for i in range(5):
    config = GenerationConfig(track="sequence", num_steps=16, temperature=0.7)
    designed = model.generate(prompt, config)
    designs.append(designed.sequence)
    print(f"Design {i+1}: {designed.sequence[:40]}...")

print(f"Generated {len(designs)} sequence designs for target structure")
```

### 5. Function Conditioning

Generate proteins with desired functional annotations (GO terms, enzyme activity).

```python
from esm.models.esm3 import ESM3
from esm.sdk.api import ESMProtein, GenerationConfig

model = ESM3.from_pretrained("esm3_sm_open_v1")

# Condition on functional keywords
protein = ESMProtein(
    sequence=None,  # generate de novo
    function_annotations=["ATP binding", "kinase activity", "protein phosphorylation"],
)

config = GenerationConfig(track="sequence", num_steps=32, temperature=0.7)
result = model.generate(protein, config)
print(f"Function-conditioned sequence: {result.sequence[:50]}...")
print(f"Length: {len(result.sequence)} residues")
```

### 6. Forge Cloud API

Use EvolutionaryScale's cloud inference for large models without local GPU.

```python
from esm.sdk.forge import ESM3ForgeInferenceClient
from esm.sdk.api import ESMProtein, GenerationConfig

# Authenticate (requires FORGE_API_TOKEN env var or explicit token)
client = ESM3ForgeInferenceClient(model="esm3-open-2024-03", token="your_token_here")

protein = ESMProtein(sequence="MKTAYIAKQRQISFVKSHFSRQLEERLG")
config = GenerationConfig(track="structure", num_steps=16)
result = client.generate(protein, config)

result.to_pdb("forge_predicted.pdb")
print("Predicted structure via Forge API → forge_predicted.pdb")
```

## Key Concepts

### ESM3 vs ESM C: When to Use Which

| Feature | ESM3 | ESM C |
|---------|------|-------|
| **Primary use** | Generative protein design | Embedding extraction |
| **Capabilities** | Sequence generation, structure prediction, inverse folding, function conditioning | Per-residue and mean-pooled embeddings |
| **Model sizes** | esm3_sm_open_v1 (~1.4B params) | esmc_300m, esmc_600m |
| **GPU requirement** | 8GB+ VRAM | 4GB+ VRAM (esmc_300m: 2GB) |
| **Use case** | Design new proteins, predict structures | Downstream ML (classification, clustering, regression) |
| **Cloud option** | Forge API (larger models available) | Local only |

### GenerationConfig Parameters

The `GenerationConfig` controls how ESM3 generates outputs:
- **`track`**: Which modality to generate (`"sequence"`, `"structure"`, `"function"`)
- **`num_steps`**: Number of iterative refinement steps (higher = better quality, slower)
- **`temperature`**: Sampling temperature (0.0 = greedy, 0.5-0.7 = diverse, 1.0 = maximum diversity)

### ESMProtein Object

The central data container holding sequence, structure coordinates, and functional annotations:
- `.sequence` — amino acid string (e.g., "MKTAY...")
- `.coordinates` — 3D atom positions (Nx3 tensor)
- `.function_annotations` — list of functional keywords
- Use `ESMProtein.from_protein_chain()` to load from PDB structures
- Use `.to_pdb()` to save predicted structures

## Common Workflows

### Workflow 1: Protein Embedding-Based Classification

**Goal**: Extract embeddings from protein sequences and train a downstream classifier.

```python
from esm.models.esmc import ESMC
from esm.sdk.api import ESMProtein
import torch
import numpy as np

model = ESMC.from_pretrained("esmc_600m")

# Embed a set of sequences
sequences = ["MKTAY...", "MKWVT...", "MSGLI..."]  # replace with actual sequences
labels = [0, 1, 0]  # binary labels

embeddings = []
for seq in sequences:
    protein = ESMProtein(sequence=seq)
    output = model(protein)
    mean_emb = output.embeddings.mean(dim=1).detach().cpu().numpy()
    embeddings.append(mean_emb.squeeze())

X = np.array(embeddings)
y = np.array(labels)
print(f"Feature matrix: {X.shape}")  # (n_samples, 1152)

# Train a simple classifier
from sklearn.linear_model import LogisticRegression
clf = LogisticRegression(max_iter=1000).fit(X, y)
print(f"Training accuracy: {clf.score(X, y):.2f}")
```

### Workflow 2: Structure-Conditioned Protein Design

**Goal**: Design multiple novel sequences that fold into a target structure, then rank by predicted quality.

1. Load target structure from PDB using `ProteinChain.from_pdb()` (Core API module 4)
2. Create ESMProtein prompt with structure but no sequence
3. Generate 10+ sequence designs with `temperature=0.7` for diversity (Core API module 1)
4. For each design, predict structure from designed sequence (Core API module 3)
5. Compare predicted structure to target structure (RMSD calculation) to rank designs
6. Select top designs for experimental validation

## Key Parameters

| Parameter | Module/Function | Default | Range / Options | Effect |
|-----------|----------------|---------|-----------------|--------|
| `num_steps` | `GenerationConfig` | varies | `1`–`64` | Iterative refinement steps; more = higher quality, slower |
| `temperature` | `GenerationConfig` | `1.0` | `0.0`–`1.5` | Sampling diversity; 0.0=greedy, 0.7=balanced, 1.0+=creative |
| `track` | `GenerationConfig` | — | `"sequence"`, `"structure"`, `"function"` | Which modality to generate |
| model name | `from_pretrained` | — | `"esm3_sm_open_v1"`, `"esmc_300m"`, `"esmc_600m"` | Model size/capability tradeoff |
| `token` | `ESM3ForgeInferenceClient` | env var | API token string | Forge cloud authentication |

## Best Practices

1. **Use ESM C for embedding tasks, ESM3 for generation**: ESM C is smaller, faster, and optimized for representation quality. Only use ESM3 when you need generative capabilities (sequence design, structure prediction, inverse folding).

2. **Mean-pool per-residue embeddings for fixed-length representations**: ESM C outputs per-residue embeddings (seq_len × dim). For downstream ML that requires fixed-length input, average across the sequence dimension: `embeddings.mean(dim=1)`.

3. **Use temperature 0.5–0.7 for protein design**: Temperature 1.0 produces very diverse but potentially non-functional sequences. Temperature 0.5–0.7 balances diversity with quality. Use temperature 0.0 only for deterministic structure prediction.

4. **Increase num_steps for higher-quality generation**: More iterative refinement steps improve output quality at the cost of computation time. Use 8–16 steps for quick exploration, 32+ for final designs.

5. **Batch sequences to maximize GPU utilization**: Processing one sequence at a time underutilizes the GPU. When embedding many sequences, batch them (limited by VRAM).

6. **Use Forge API for large-scale or large-model inference**: The open-weight ESM3 is a smaller variant. For production-quality protein design, the Forge API provides access to larger models.

## Common Recipes

### Recipe: Pairwise Protein Similarity Matrix

```python
from esm.models.esmc import ESMC
from esm.sdk.api import ESMProtein
import torch
import numpy as np

model = ESMC.from_pretrained("esmc_300m")

sequences = {
    "Protein_A": "MKTAYIAKQRQISFVK...",
    "Protein_B": "MKWVTFISLLFLFSSAYS...",
    "Protein_C": "MSGLILQRAAVIAAGASSAG...",
}

# Extract embeddings
embs = {}
for name, seq in sequences.items():
    protein = ESMProtein(sequence=seq)
    output = model(protein)
    embs[name] = output.embeddings.mean(dim=1).detach().squeeze()

# Compute similarity matrix
names = list(embs.keys())
sim_matrix = np.zeros((len(names), len(names)))
for i, n1 in enumerate(names):
    for j, n2 in enumerate(names):
        sim_matrix[i, j] = torch.cosine_similarity(embs[n1].unsqueeze(0), embs[n2].unsqueeze(0)).item()

print("Similarity matrix:")
for i, name in enumerate(names):
    print(f"  {name}: {sim_matrix[i].round(3)}")
```

### Recipe: Save/Load Embeddings for Reuse

```python
from esm.models.esmc import ESMC
from esm.sdk.api import ESMProtein
import torch
import numpy as np

model = ESMC.from_pretrained("esmc_600m")

# Generate and save
protein = ESMProtein(sequence="MKTAYIAKQRQISFVK...")
output = model(protein)
np.save("embedding.npy", output.embeddings.detach().cpu().numpy())
print("Saved embedding.npy")

# Load later (no GPU needed)
embedding = np.load("embedding.npy")
print(f"Loaded embedding: {embedding.shape}")
```

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| `CUDA out of memory` | Model too large for GPU | Use smaller model (`esmc_300m`), reduce batch size, or use Forge cloud API |
| `RuntimeError: no CUDA device` | No GPU available | Models work on CPU (slower). Set `device="cpu"` or use Forge API |
| Slow generation | Too many `num_steps` or CPU inference | Reduce `num_steps` (8 for drafts), use GPU, or use Forge API for large models |
| `ImportError: esm` | Package not installed | `pip install esm` (note: this is EvolutionaryScale's `esm`, not the older Facebook Research `esm`) |
| Low-quality generated sequences | Temperature too high or too few steps | Lower temperature to 0.5, increase `num_steps` to 32+ |
| Forge API authentication error | Invalid or missing API token | Set `FORGE_API_TOKEN` env var or pass `token=` explicitly; get token from forge.evolutionaryscale.ai |
| `KeyError` loading model weights | Wrong model name | Use exact names: `"esm3_sm_open_v1"`, `"esmc_300m"`, `"esmc_600m"` |

## Related Skills

- **alphafold-database** — retrieve predicted structures from AlphaFold DB; use ESM for de novo structure prediction
- **biopython** — sequence I/O and alignment; preprocess sequences before ESM embedding
- **scikit-learn** — downstream ML on ESM embeddings (classification, clustering, regression)
- **rdkit** — cheminformatics for small-molecule drug design (complementary to protein design)

## References

- [ESM GitHub](https://github.com/evolutionaryscale/esm) — source code and model weights
- [EvolutionaryScale Forge](https://forge.evolutionaryscale.ai/) — cloud inference API
- Hayes et al. (2024) "Simulating 500 million years of evolution with a language model" — [bioRxiv](https://doi.org/10.1101/2024.07.01.600583)
- Lin et al. (2023) "Evolutionary-scale prediction of atomic-level protein structure with a language model" — [Science](https://doi.org/10.1126/science.ade2574)
