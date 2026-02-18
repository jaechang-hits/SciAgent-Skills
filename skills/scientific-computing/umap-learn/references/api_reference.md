# UMAP API Reference

Complete parameter and method reference for UMAP, ParametricUMAP, and AlignedUMAP.

## UMAP Class Constructor

```python
umap.UMAP(n_neighbors=15, n_components=2, metric='euclidean', n_epochs=None,
          learning_rate=1.0, init='spectral', min_dist=0.1, spread=1.0,
          low_memory=True, set_op_mix_ratio=1.0, local_connectivity=1.0,
          repulsion_strength=1.0, negative_sample_rate=5, transform_queue_size=4.0,
          a=None, b=None, random_state=None, metric_kwds=None,
          angular_rp_forest=False, target_n_neighbors=-1,
          target_metric='categorical', target_metric_kwds=None, target_weight=0.5,
          transform_seed=42, transform_mode='embedding',
          force_approximation_algorithm=False, verbose=False, unique=False,
          densmap=False, dens_lambda=2.0, dens_frac=0.3, dens_var_shift=0.1,
          output_dens=False, disconnection_distance=None,
          precomputed_knn=(None, None, None))
```

## Advanced Structural Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `local_connectivity` | 1.0 | Nearest neighbors assumed locally connected. Higher = more connected manifold |
| `set_op_mix_ratio` | 1.0 | Interpolation union (1.0) vs intersection (0.0) for fuzzy set construction |
| `repulsion_strength` | 1.0 | Weight of negative samples in optimization. Higher = more spread |
| `negative_sample_rate` | 5 | Negative samples per positive. Higher = more repulsion, slower |

## Supervised Learning Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `target_n_neighbors` | -1 | KNN for target simplicial set. -1 uses `n_neighbors` |
| `target_metric` | `'categorical'` | Distance metric for labels. `'categorical'` for classification |
| `target_metric_kwds` | `None` | Additional args for target metric |
| `target_weight` | 0.5 | Label vs data balance. 0.0=unsupervised, 1.0=fully supervised |

## Transform Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `transform_queue_size` | 4.0 | KNN search queue size for transform. Larger = more accurate, slower |
| `transform_seed` | 42 | Random seed for transform reproducibility |
| `transform_mode` | `'embedding'` | `'embedding'` (standard) or `'graph'` (nearest neighbor graph) |

## Performance Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `low_memory` | `True` | Memory-efficient implementation |
| `verbose` | `False` | Print progress during fitting |
| `unique` | `False` | Consider only unique points (set True for many duplicates) |
| `force_approximation_algorithm` | `False` | Force approximate KNN even for small datasets |
| `angular_rp_forest` | `False` | Angular random projection forest for normalized high-dim data |

## DensMAP Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `densmap` | `False` | Enable density-preserving DensMAP |
| `dens_lambda` | 2.0 | Weight of density preservation term |
| `dens_frac` | 0.3 | Fraction of dataset for density estimation |
| `dens_var_shift` | 0.1 | Regularization for density estimation |
| `output_dens` | `False` | Output density estimates (`rad_orig_`, `rad_emb_` attributes) |

## Other Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `a` | `None` | Curve parameter (auto from min_dist, spread) |
| `b` | `None` | Curve parameter (auto from min_dist, spread) |
| `metric_kwds` | `None` | Additional metric keyword arguments |
| `disconnection_distance` | `None` | Distance threshold for disconnected points |
| `precomputed_knn` | `(None, None, None)` | Pre-computed KNN: `(indices, dists, search_index)` |

## Methods

### fit(X, y=None)

Fit UMAP to data. Sets `embedding_`, `graph_`, and internal attributes.

- `X`: array-like (n_samples, n_features)
- `y`: optional labels for supervised mode
- Returns: self

### fit_transform(X, y=None)

Fit and return embedding.

- Returns: array (n_samples, n_components)

### transform(X)

Project new data into trained embedding. Model must be fitted first.

- Returns: array (n_samples, n_components)
- Quality depends on distribution match between train and test data

### inverse_transform(X)

Reconstruct original-space data from embedding coordinates.

- Returns: array (n_samples, n_features)
- Computationally expensive; poor outside convex hull of training embedding

### update(X)

Incrementally update model with new data. Experimental.

## Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `embedding_` | ndarray | Embedded training data (n_samples, n_components) |
| `graph_` | scipy.sparse.csr_matrix | Fuzzy simplicial set (weighted adjacency) |
| `_raw_data` | ndarray | Copy of training data |
| `_sparse_data` | bool | Whether training data was sparse |
| `_small_data` | bool | Whether small-dataset algorithm was used |
| `_knn_indices` | ndarray | KNN indices per training point |
| `_knn_dists` | ndarray | KNN distances per training point |
| `_rp_forest` | list | Random projection forest for approximate KNN |

## ParametricUMAP Class

```python
umap.ParametricUMAP(encoder=None, decoder=None,
                     parametric_reconstruction=False, autoencoder_loss=False,
                     reconstruction_validation=None, dims=None, batch_size=None,
                     n_training_epochs=1, loss_report_frequency=10,
                     optimizer=None, keras_fit_kwargs={}, **kwargs)
```

### Additional Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `encoder` | `None` | Keras encoder model. Default: 3-layer FC (100 neurons) |
| `decoder` | `None` | Keras decoder model. Required for reconstruction |
| `parametric_reconstruction` | `False` | Use decoder for parametric reconstruction |
| `autoencoder_loss` | `False` | Include reconstruction loss in optimization |
| `reconstruction_validation` | `None` | `(X_val, y_val)` for monitoring reconstruction |
| `dims` | `None` | Input dimensions tuple. Required with custom encoder |
| `batch_size` | `None` | Neural network batch size (auto if None) |
| `n_training_epochs` | 1 | Neural network training epochs |
| `loss_report_frequency` | 10 | Loss reporting interval |
| `optimizer` | `None` | Keras optimizer (default: Adam) |
| `keras_fit_kwargs` | `{}` | Additional kwargs for Keras fit() |

Methods: same as UMAP, but `transform()` and `inverse_transform()` use neural networks.

## AlignedUMAP Class

```python
umap.AlignedUMAP(n_neighbors=15, n_components=2, metric='euclidean',
                  alignment_regularisation=1e-2, alignment_window_size=3, **kwargs)
```

### Additional Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `alignment_regularisation` | 0.01 | Alignment strength between datasets |
| `alignment_window_size` | 3 | Number of adjacent datasets to align |

### fit(X) — X is a list of arrays

### Attribute: `embeddings_` — list of aligned embedding arrays

## Utility Functions

### umap.nearest_neighbors(X, n_neighbors, metric, ...)

Compute KNN. Returns: `(knn_indices, knn_dists, rp_forest)`

### umap.fuzzy_simplicial_set(X, n_neighbors, random_state, metric, ...)

Construct fuzzy simplicial set. Returns: sparse matrix

### umap.simplicial_set_embedding(data, graph, n_components, ...)

Low-level embedding optimization. Returns: embedding array

### umap.find_ab_params(spread, min_dist)

Compute curve parameters from spread and min_dist. Returns: `(a, b)` tuple

Condensed from original: references/api_reference.md (533 lines). Retained: all constructor parameters organized by category, all methods with signatures, all attributes, ParametricUMAP and AlignedUMAP classes, utility functions. Omitted: usage examples duplicating SKILL.md workflows; parameter tuning guidance relocated to SKILL.md Key Concepts.
