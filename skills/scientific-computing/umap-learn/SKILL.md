---
name: umap-learn
description: >-
  UMAP dimensionality reduction for visualization, clustering prep, and feature
  engineering. Fast nonlinear manifold learning preserving local and global structure.
  Standard UMAP (fit/transform, sklearn-compatible), supervised/semi-supervised,
  Parametric UMAP (NN encoder/decoder, TensorFlow), DensMAP (density), AlignedUMAP
  (temporal/batch). 15+ distance metrics, custom Numba metrics, precomputed distances.
  For linear reduction use PCA; for neighborhood graphs use sklearn NearestNeighbors.
license: BSD-3-Clause
---

# UMAP-Learn

## Overview

UMAP (Uniform Manifold Approximation and Projection) is a dimensionality reduction algorithm for visualization and general non-linear dimensionality reduction. It is faster than t-SNE, scales to larger datasets, preserves both local and global structure, and supports supervised learning and embedding of new data points.

## When to Use

- Reducing high-dimensional data to 2D/3D for visualization
- Preprocessing for density-based clustering (HDBSCAN, DBSCAN)
- Feature engineering in ML pipelines (transform new data into learned embedding)
- Supervised/semi-supervised embedding with partial labels
- Tracking embeddings across time points or batches (AlignedUMAP)
- Density-preserving embeddings (DensMAP)
- Neural network-based embedding with custom architectures (Parametric UMAP)
- For linear dimensionality reduction use **PCA** (scikit-learn)
- For neighborhood-graph construction without embedding use **scikit-learn NearestNeighbors**

## Prerequisites

```bash
pip install umap-learn

# For Parametric UMAP (neural network variant)
pip install umap-learn[parametric_umap]  # requires TensorFlow 2.x
```

**Critical**: Always standardize features before applying UMAP to ensure equal weighting across dimensions.

## Quick Start

```python
import umap
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.datasets import load_digits

# Load and scale data
X, y = load_digits(return_X_y=True)
X_scaled = StandardScaler().fit_transform(X)

# Fit and transform
embedding = umap.UMAP(random_state=42).fit_transform(X_scaled)
print(f"Input: {X_scaled.shape}, Output: {embedding.shape}")
# Input: (1797, 64), Output: (1797, 2)
```

## Core API

### 1. Standard UMAP

Basic dimensionality reduction following scikit-learn conventions.

```python
import umap
from sklearn.preprocessing import StandardScaler

X_scaled = StandardScaler().fit_transform(data)

# Method 1: fit_transform (single step)
embedding = umap.UMAP(
    n_neighbors=15,     # local neighborhood size (2-200)
    min_dist=0.1,       # min distance between embedded points (0.0-0.99)
    n_components=2,     # output dimensions
    metric='euclidean', # distance metric
    random_state=42,    # reproducibility
).fit_transform(X_scaled)
print(f"Embedding shape: {embedding.shape}")

# Method 2: fit + access (for reuse)
reducer = umap.UMAP(random_state=42)
reducer.fit(X_scaled)
embedding = reducer.embedding_  # trained embedding
graph = reducer.graph_          # fuzzy simplicial set (sparse matrix)
```

```python
# Visualization
import matplotlib.pyplot as plt

plt.figure(figsize=(8, 6))
plt.scatter(embedding[:, 0], embedding[:, 1], c=labels, cmap='Spectral', s=5)
plt.colorbar()
plt.title('UMAP Embedding')
plt.tight_layout()
plt.savefig('umap_embedding.png', dpi=150)
```

### 2. Supervised & Semi-Supervised UMAP

Incorporate label information to guide embedding via the `y` parameter.

```python
import umap

# Supervised — all labels known
embedding = umap.UMAP(random_state=42).fit_transform(X_scaled, y=labels)

# Semi-supervised — partial labels (mark unlabeled as -1)
semi_labels = labels.copy()
semi_labels[unlabeled_indices] = -1
embedding = umap.UMAP(random_state=42).fit_transform(X_scaled, y=semi_labels)

# Control label influence with target_weight (0.0=unsupervised, 1.0=fully supervised)
reducer = umap.UMAP(
    target_weight=0.7,               # emphasize labels
    target_metric='categorical',     # for classification; use distance metric for regression
    random_state=42
)
embedding = reducer.fit_transform(X_scaled, y=labels)
print(f"Supervised embedding: {embedding.shape}")
```

### 3. Transform New Data

Project unseen data into the trained embedding space.

```python
import umap
from sklearn.preprocessing import StandardScaler

scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

# Fit on training data
reducer = umap.UMAP(n_components=10, random_state=42)
X_train_emb = reducer.fit_transform(X_train_scaled)

# Transform test data
X_test_emb = reducer.transform(X_test_scaled)
print(f"Train: {X_train_emb.shape}, Test: {X_test_emb.shape}")

# Works in sklearn Pipelines
from sklearn.pipeline import Pipeline
from sklearn.svm import SVC

pipeline = Pipeline([
    ('scaler', StandardScaler()),
    ('umap', umap.UMAP(n_components=10, random_state=42)),
    ('classifier', SVC())
])
pipeline.fit(X_train, y_train)
accuracy = pipeline.score(X_test, y_test)
print(f"Pipeline accuracy: {accuracy:.3f}")
```

### 4. Parametric UMAP

Neural network-based embedding via TensorFlow/Keras. Enables efficient transform, reconstruction, and custom architectures.

```python
from umap.parametric_umap import ParametricUMAP

# Default architecture (3-layer, 100-neuron FC network)
embedder = ParametricUMAP(n_components=2, random_state=42)
embedding = embedder.fit_transform(X_scaled)
new_emb = embedder.transform(new_data)  # fast neural network inference
print(f"Parametric embedding: {embedding.shape}")
```

```python
import tensorflow as tf
from umap.parametric_umap import ParametricUMAP

# Custom encoder/decoder for autoencoder mode
input_dim = X_scaled.shape[1]
encoder = tf.keras.Sequential([
    tf.keras.layers.InputLayer(input_shape=(input_dim,)),
    tf.keras.layers.Dense(128, activation='relu'),
    tf.keras.layers.Dense(64, activation='relu'),
    tf.keras.layers.Dense(2),
])
decoder = tf.keras.Sequential([
    tf.keras.layers.InputLayer(input_shape=(2,)),
    tf.keras.layers.Dense(64, activation='relu'),
    tf.keras.layers.Dense(128, activation='relu'),
    tf.keras.layers.Dense(input_dim),
])

embedder = ParametricUMAP(
    encoder=encoder, decoder=decoder, dims=(input_dim,),
    parametric_reconstruction=True, autoencoder_loss=True,
    n_training_epochs=10, batch_size=128,
    n_neighbors=15, min_dist=0.1, random_state=42
)
embedding = embedder.fit_transform(X_scaled)
reconstructed = embedder.inverse_transform(embedding)
print(f"Reconstruction error: {np.mean((X_scaled - reconstructed)**2):.4f}")
```

### 5. DensMAP

Variant preserving local density information in the embedding.

```python
import umap

reducer = umap.UMAP(
    densmap=True,          # enable DensMAP
    dens_lambda=2.0,       # density preservation weight
    dens_frac=0.3,         # fraction for density estimation
    output_dens=True,      # output density estimates
    n_neighbors=15,
    min_dist=0.1,
    random_state=42
)
embedding = reducer.fit_transform(X_scaled)

# Access density estimates
original_density = reducer.rad_orig_  # density in original space
embedded_density = reducer.rad_emb_   # density in embedded space
print(f"DensMAP embedding: {embedding.shape}")
print(f"Density correlation: {np.corrcoef(original_density, embedded_density)[0,1]:.3f}")
```

### 6. AlignedUMAP

Align embeddings across multiple related datasets (time points, batches).

```python
from umap import AlignedUMAP

# Multiple related datasets
datasets = [day1_data, day2_data, day3_data]

mapper = AlignedUMAP(
    n_neighbors=15,
    alignment_regularisation=1e-2,  # alignment strength
    alignment_window_size=2,        # align with N adjacent datasets
    n_components=2,
    random_state=42
)
mapper.fit(datasets)

aligned_embeddings = mapper.embeddings_  # list of aligned embedding arrays
print(f"Aligned {len(aligned_embeddings)} datasets")
for i, emb in enumerate(aligned_embeddings):
    print(f"  Dataset {i}: {emb.shape}")
```

## Key Concepts

### Parameter Tuning Guide

| Parameter | Low | Medium (default) | High | Effect |
|-----------|-----|-------------------|------|--------|
| `n_neighbors` | 2-5 | 15 | 50-200 | Local detail vs global structure |
| `min_dist` | 0.0 | 0.1 | 0.5-0.99 | Tight clusters vs spread out |
| `n_components` | 2 | 2 | 5-50 | Visualization vs ML/clustering |
| `spread` | 0.5 | 1.0 | 2.0 | Embedding scale (with min_dist) |

### Configuration by Use-Case

| Use-Case | n_neighbors | min_dist | n_components | metric |
|----------|-------------|----------|-------------|--------|
| Visualization | 15 | 0.1 | 2 | euclidean |
| Clustering (HDBSCAN) | 30 | 0.0 | 5-10 | euclidean |
| Text/document embedding | 15 | 0.1 | 2 | cosine |
| Global structure | 100 | 0.5 | 2 | euclidean |
| ML feature engineering | 15-30 | 0.1 | 10-50 | euclidean |
| Binary/set data | 15 | 0.1 | 2 | hamming/jaccard |

### Supported Metrics

Minkowski family: `euclidean`, `manhattan`, `chebyshev`, `minkowski`. Spatial: `canberra`, `braycurtis`, `haversine`. Correlation: `cosine`, `correlation`. Binary: `hamming`, `jaccard`, `dice`, `russellrao`, `rogerstanimoto`, `sokalmichener`, `sokalsneath`, `yule`. Special: `precomputed` (distance matrix), custom Numba-compiled callables.

### Standard UMAP vs Parametric UMAP

| Feature | Standard | Parametric |
|---------|----------|-----------|
| Backend | Direct optimization | TensorFlow neural network |
| Transform speed | Moderate | Fast (neural net inference) |
| Inverse transform | Approximate, expensive | Decoder network, fast |
| Custom architecture | No | Yes (CNNs, RNNs, etc.) |
| Requirements | umap-learn | umap-learn + TensorFlow 2.x |
| Best for | Quick exploration | Production pipelines, reconstruction |

## Common Workflows

### Workflow 1: UMAP + HDBSCAN Clustering Pipeline

```python
import umap
import hdbscan
import numpy as np
import matplotlib.pyplot as plt
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import adjusted_rand_score

# Step 1: Preprocess
X_scaled = StandardScaler().fit_transform(data)
print(f"Input shape: {X_scaled.shape}")

# Step 2: UMAP for clustering (NOT visualization parameters)
reducer = umap.UMAP(
    n_neighbors=30,     # more global structure for clustering
    min_dist=0.0,       # allow tight packing
    n_components=10,    # higher dims preserve density better than 2D
    metric='euclidean',
    random_state=42
)
embedding = reducer.fit_transform(X_scaled)

# Step 3: HDBSCAN clustering
clusterer = hdbscan.HDBSCAN(min_cluster_size=15, min_samples=5)
cluster_labels = clusterer.fit_predict(embedding)

n_clusters = len(set(cluster_labels)) - (1 if -1 in cluster_labels else 0)
noise = sum(cluster_labels == -1)
print(f"Clusters: {n_clusters}, Noise: {noise}")

# Step 4: Separate 2D embedding for visualization
vis_emb = umap.UMAP(n_neighbors=15, min_dist=0.1, random_state=42).fit_transform(X_scaled)
plt.scatter(vis_emb[:, 0], vis_emb[:, 1], c=cluster_labels, cmap='Spectral', s=5)
plt.colorbar()
plt.title(f'HDBSCAN Clusters (n={n_clusters})')
plt.tight_layout()
plt.savefig('umap_clusters.png', dpi=150)
```

### Workflow 2: Supervised Embedding for Classification

```python
import umap
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC
from sklearn.metrics import classification_report

# Split and scale
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
scaler = StandardScaler()
X_train_s = scaler.fit_transform(X_train)
X_test_s = scaler.transform(X_test)

# Supervised UMAP for feature engineering
reducer = umap.UMAP(n_components=10, random_state=42)
X_train_emb = reducer.fit_transform(X_train_s, y=y_train)
X_test_emb = reducer.transform(X_test_s)

# Downstream classifier
clf = SVC(kernel='rbf')
clf.fit(X_train_emb, y_train)
y_pred = clf.predict(X_test_emb)

print(classification_report(y_test, y_pred))
```

### Workflow 3: Exploring Embedding Space with Inverse Transform

Text-only — combines Core API modules 1 and 3 (inverse_transform on standard UMAP):

1. Fit standard UMAP on data (Core API: Standard UMAP)
2. Create a grid of points spanning the embedding space
3. Apply `reducer.inverse_transform(grid_points)` to reconstruct high-dimensional data
4. Visualize reconstructed samples to understand embedding regions

Note: inverse transform is approximate; works poorly outside the convex hull of the training embedding.

## Key Parameters

| Parameter | Module | Default | Range | Effect |
|-----------|--------|---------|-------|--------|
| `n_neighbors` | UMAP | 15 | 2-200 | Local vs global structure balance |
| `min_dist` | UMAP | 0.1 | 0.0-0.99 | Cluster tightness |
| `n_components` | UMAP | 2 | 2-100 | Output dimensionality |
| `metric` | UMAP | `'euclidean'` | See metrics list | Distance calculation method |
| `spread` | UMAP | 1.0 | >0 | Embedding scale (with min_dist) |
| `n_epochs` | UMAP | `None` (auto) | 50-500+ | Training iterations |
| `learning_rate` | UMAP | 1.0 | >0 | SGD step size |
| `init` | UMAP | `'spectral'` | spectral/random/pca | Embedding initialization |
| `random_state` | UMAP | `None` | int | Reproducibility seed |
| `target_weight` | UMAP | 0.5 | 0.0-1.0 | Label influence (supervised) |
| `densmap` | UMAP | `False` | bool | Enable DensMAP |
| `dens_lambda` | UMAP | 2.0 | >0 | DensMAP density weight |
| `low_memory` | UMAP | `True` | bool | Memory-efficient mode |
| `encoder` | ParametricUMAP | `None` | Keras model | Custom encoder network |
| `decoder` | ParametricUMAP | `None` | Keras model | Custom decoder network |
| `n_training_epochs` | ParametricUMAP | 1 | 1-100 | Neural network training epochs |
| `alignment_regularisation` | AlignedUMAP | 0.01 | >0 | Alignment strength |
| `alignment_window_size` | AlignedUMAP | 3 | 1-N | Adjacent datasets to align |

## Best Practices

1. **Always standardize features**: Use `StandardScaler` before UMAP — unscaled features with different ranges will dominate the embedding.

2. **Set `random_state` for reproducibility**: UMAP uses stochastic optimization; results vary between runs without a fixed seed.

3. **Use different parameters for clustering vs visualization**: Clustering needs `n_neighbors=30, min_dist=0.0, n_components=5-10`. Visualization needs `n_neighbors=15, min_dist=0.1, n_components=2`.

4. **Anti-pattern — interpreting distances literally**: UMAP preserves topology, not precise distances. Cluster separations and point distances in the embedding are not proportional to original distances.

5. **Anti-pattern — using 2D embeddings for clustering**: 2D projections lose density information. Use 5-10 components for HDBSCAN input.

6. **Consider PCA preprocessing for very high dimensions**: For data with >1000 features, reducing to 50-100 PCA components first can speed up UMAP without losing quality.

7. **Use Parametric UMAP for production**: When you need fast transform on new data or reconstruction capabilities, Parametric UMAP's neural network provides consistent, fast inference.

## Common Recipes

### Recipe: Custom Numba Distance Metric

```python
from numba import njit
import umap

@njit()
def weighted_euclidean(x, y):
    """Custom distance with feature weights."""
    result = 0.0
    for i in range(x.shape[0]):
        result += (x[i] - y[i]) ** 2 * (1.0 + i * 0.01)  # increasing weight
    return np.sqrt(result)

embedding = umap.UMAP(metric=weighted_euclidean, random_state=42).fit_transform(data)
```

### Recipe: Precomputed Distance Matrix

```python
import umap
from scipy.spatial.distance import pdist, squareform

# Compute custom distance matrix
dist_matrix = squareform(pdist(data, metric='correlation'))

# Use precomputed distances
embedding = umap.UMAP(
    metric='precomputed', random_state=42
).fit_transform(dist_matrix)
print(f"Embedding from precomputed: {embedding.shape}")
```

### Recipe: Metric Learning Pipeline

```python
import umap
from sklearn.svm import SVC

# Train supervised embedding on labeled data
mapper = umap.UMAP(n_components=10, random_state=42)
train_emb = mapper.fit_transform(X_train, y=y_train)

# Transform unlabeled test data using learned metric
test_emb = mapper.transform(X_test)

# Downstream classifier
clf = SVC().fit(train_emb, y_train)
predictions = clf.predict(test_emb)
print(f"Accuracy: {(predictions == y_test).mean():.3f}")
```

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| Disconnected/fragmented clusters | `n_neighbors` too low | Increase `n_neighbors` (try 30-50) |
| Clusters too spread out | `min_dist` too high | Decrease `min_dist` (try 0.0-0.05) |
| All points collapsed | Bad preprocessing or `min_dist` too low | Check `StandardScaler`; increase `min_dist` |
| Poor clustering results | Using visualization parameters for clustering | Set `n_neighbors=30, min_dist=0.0, n_components=5-10` |
| Transform results differ from training | Distribution shift | Ensure test data matches training distribution; use Parametric UMAP |
| Slow on large datasets (>100k) | Default settings | Set `low_memory=True`; preprocess with PCA to 50-100 dims |
| First run very slow | Numba JIT compilation | Expected — subsequent runs are fast (compiled cache) |
| `ImportError: umap` | Name conflict with `umap` package | `pip install umap-learn` (not `pip install umap`) |
| Parametric UMAP import error | Missing TensorFlow | `pip install umap-learn[parametric_umap]` |
| Non-reproducible results | Missing `random_state` | Always set `random_state=42` (or any int) |

## Bundled Resources

### references/api_reference.md

Complete UMAP constructor parameter reference (60+ parameters organized by category: core, training, advanced structural, supervised, transform, performance, DensMAP), all methods and attributes, ParametricUMAP class with autoencoder parameters, AlignedUMAP class, utility functions (nearest_neighbors, fuzzy_simplicial_set). Core parameter tuning guidance was relocated to SKILL.md Key Concepts and Core API modules. Usage examples duplicating SKILL.md workflows omitted.

## Related Skills

- **scikit-learn-machine-learning** — ML classifiers, preprocessing, pipelines for downstream tasks
- **matplotlib-scientific-plotting** — Visualization of UMAP embeddings
- **scikit-bio** — Biological distance matrices that can feed into UMAP via `metric='precomputed'`

## References

- McInnes L, Healy J, Melville J. UMAP: Uniform Manifold Approximation and Projection for Dimension Reduction. arXiv:1802.03426
- Sainburg T, McInnes L, Gentner TQ. Parametric UMAP Embeddings for Representation and Semisupervised Learning. Neural Computation (2021)
- Narayan A, Berger B, Cho H. Assessing single-cell transcriptomic variability through density-preserving data visualization. Nature Biotechnology (2021) — DensMAP
- Official docs: https://umap-learn.readthedocs.io/
- GitHub: https://github.com/lmcinnes/umap
