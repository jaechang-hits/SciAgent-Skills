---
name: "aeon"
description: "aeon is a scikit-learn compatible Python toolkit for time series machine learning and data mining. Classify, cluster, regress, segment, and transform time series using 30+ algorithms including ROCKET, InceptionTime, KNN-DTW, HIVE-COTE, and WEASEL. Supports panel (multi-instance), multivariate, and unequal-length time series. Designed as the maintained successor to sktime. Alternatives: sktime (older, larger ecosystem), tslearn (less algorithms), catch22 (feature extraction only)."
license: "BSD-3-Clause"
---

# aeon

## Overview

aeon provides a unified scikit-learn-compatible API for time series ML tasks: classification, regression, clustering, segmentation, annotation, similarity search, and transformation. It follows the same `fit(X, y)` / `predict(X)` pattern as scikit-learn, where `X` is a 3D NumPy array of shape `(n_instances, n_channels, n_timepoints)`. aeon curates state-of-the-art algorithms from the time series literature — ROCKET and its variants (MiniROCKET, MultiROCKET) for classification, k-means with DTW for clustering, CLASP for segmentation — and provides benchmarking tools for comparing algorithms across datasets. It is the community-maintained fork of sktime following the 2022 governance split.

## When to Use

- Classifying ECG, EEG, accelerometer, or sensor time series using state-of-the-art algorithms
- Regressing a scalar target from a time series input (e.g., predicting patient severity from vital sign waveforms)
- Clustering time series by shape similarity when class labels are unavailable
- Detecting change points or segmenting a continuous recording into homogeneous intervals
- Extracting fixed-length feature vectors from variable-length time series for downstream ML
- Benchmarking time series algorithms on the UCR/UEA archive with reproducible comparisons
- Use sktime when you need a larger ecosystem or existing code depends on its API; use tslearn for DTW-focused work

## Prerequisites

- **Python packages**: `aeon`, `numpy`, `scikit-learn`, `matplotlib`
- **Data format**: 3D NumPy array `(n_instances, n_channels, n_timepoints)` or 2D `(n_instances, n_timepoints)` for univariate
- **Optional**: `numba` (required for ROCKET, DTW — install via `pip install aeon[all_extras]`)

```bash
pip install aeon
pip install aeon[all_extras]  # includes numba, statsmodels for full algorithm support
```

## Quick Start

```python
import numpy as np
from aeon.classification.convolution_based import RocketClassifier
from aeon.datasets import load_unit_test

# Load a small benchmark dataset
X_train, y_train = load_unit_test(split="train")  # shape: (n, 1, timepoints)
X_test, y_test = load_unit_test(split="test")

print(f"Train: {X_train.shape}, classes: {np.unique(y_train)}")

clf = RocketClassifier(num_kernels=500, random_state=42)
clf.fit(X_train, y_train)
accuracy = clf.score(X_test, y_test)
print(f"ROCKET accuracy: {accuracy:.3f}")
```

## Core API

### Module 1: Time Series Classification

30+ classifiers spanning convolution, dictionary, distance, feature, interval, and shapelet families.

```python
import numpy as np
from aeon.datasets import load_unit_test
from aeon.classification.convolution_based import RocketClassifier, MiniRocketClassifier
from aeon.classification.distance_based import KNeighborsTimeSeriesClassifier
from aeon.classification.feature_based import Catch22Classifier
from sklearn.metrics import accuracy_score

X_train, y_train = load_unit_test(split="train")
X_test, y_test   = load_unit_test(split="test")

classifiers = {
    "ROCKET":    RocketClassifier(num_kernels=1000, random_state=42),
    "MiniROCKET": MiniRocketClassifier(random_state=42),
    "KNN-DTW":   KNeighborsTimeSeriesClassifier(n_neighbors=1, distance="dtw"),
    "Catch22":   Catch22Classifier(random_state=42),
}

for name, clf in classifiers.items():
    clf.fit(X_train, y_train)
    acc = accuracy_score(y_test, clf.predict(X_test))
    print(f"{name:15s}: {acc:.3f}")
```

```python
# Multivariate classification (multiple channels)
from aeon.classification.convolution_based import MultiRocketMultivariateClassifier

# Synthetic multivariate time series: 100 instances, 3 channels, 50 timepoints
np.random.seed(0)
X_mv_train = np.random.randn(100, 3, 50)
y_mv_train = (X_mv_train[:, 0, :].mean(axis=1) > 0).astype(str)
X_mv_test  = np.random.randn(30, 3, 50)
y_mv_test  = (X_mv_test[:, 0, :].mean(axis=1) > 0).astype(str)

clf_mv = MultiRocketMultivariateClassifier(random_state=42)
clf_mv.fit(X_mv_train, y_mv_train)
print(f"Multivariate accuracy: {clf_mv.score(X_mv_test, y_mv_test):.3f}")
```

### Module 2: Time Series Regression

Predict a continuous target from a time series input.

```python
import numpy as np
from aeon.regression.convolution_based import RocketRegressor
from aeon.regression.distance_based import KNeighborsTimeSeriesRegressor
from sklearn.metrics import mean_squared_error

# Synthetic regression: predict the mean of each series
np.random.seed(42)
X_train = np.random.randn(200, 1, 100)
y_train = X_train[:, 0, :].mean(axis=1) + np.random.randn(200) * 0.1
X_test  = np.random.randn(50, 1, 100)
y_test  = X_test[:, 0, :].mean(axis=1) + np.random.randn(50) * 0.1

reg = RocketRegressor(num_kernels=500, random_state=42)
reg.fit(X_train, y_train)
y_pred = reg.predict(X_test)
mse = mean_squared_error(y_test, y_pred)
print(f"ROCKET regressor MSE: {mse:.4f}")
```

### Module 3: Time Series Clustering

Group time series by shape similarity without class labels.

```python
import numpy as np
from aeon.clustering.k_means import TimeSeriesKMeans
from aeon.clustering.k_medoids import TimeSeriesKMedoids

# Synthetic clustering dataset: 3 distinct shapes
np.random.seed(0)
n_per_class = 30
class_0 = np.sin(np.linspace(0, 2*np.pi, 50)) + np.random.randn(n_per_class, 1, 50)*0.1
class_1 = np.cos(np.linspace(0, 2*np.pi, 50)) + np.random.randn(n_per_class, 1, 50)*0.1
class_2 = np.linspace(0, 1, 50) + np.random.randn(n_per_class, 1, 50)*0.05
X = np.concatenate([class_0, class_1, class_2], axis=0)

# K-Means with DTW averaging
km = TimeSeriesKMeans(n_clusters=3, metric="dtw", averaging_method="ba",
                       random_state=42, n_init=3, max_iter=50)
labels = km.fit_predict(X)
print(f"Cluster sizes: {np.bincount(labels)}")
print(f"Cluster centers shape: {km.cluster_centers_.shape}")
```

### Module 4: Segmentation and Change Point Detection

Detect boundaries between regimes in a continuous time series.

```python
import numpy as np
from aeon.segmentation import ClaSPSegmenter, EAggloSegmenter

# Simulate signal with 3 segments
np.random.seed(0)
seg1 = np.random.randn(100) * 0.5 + 0
seg2 = np.random.randn(100) * 0.5 + 3
seg3 = np.random.randn(100) * 0.5 - 2
signal = np.concatenate([seg1, seg2, seg3])

# CLASP: Classification Score Profile segmentation
clasp = ClaSPSegmenter(period_length=10, n_change_points=2)
labels = clasp.fit_predict(signal)
change_points = clasp.change_points_
print(f"Detected change points: {change_points}")
# Expected near indices 100 and 200
```

### Module 5: Transformation (Feature Extraction)

Convert time series into fixed-length feature vectors or transformed series.

```python
import numpy as np
from aeon.transformations.collection.convolution_based import Rocket, MiniRocket
from aeon.transformations.collection.feature_based import Catch22
from sklearn.linear_model import RidgeClassifierCV
from sklearn.pipeline import Pipeline

np.random.seed(42)
X_train = np.random.randn(100, 1, 50)
y_train = (X_train[:, 0, :].mean(axis=1) > 0).astype(str)
X_test  = np.random.randn(30, 1, 50)

# ROCKET transform → Ridge classifier (the classic ROCKET pipeline)
rocket_pipe = Pipeline([
    ("rocket", Rocket(num_kernels=1000, random_state=42)),
    ("clf", RidgeClassifierCV(alphas=[0.1, 1.0, 10.0])),
])
rocket_pipe.fit(X_train, y_train)
print(f"ROCKET pipeline accuracy: {rocket_pipe.score(X_test, (X_test[:, 0, :].mean(axis=1) > 0).astype(str)):.3f}")

# Catch22: 22 canonical time series features per channel
catch22 = Catch22()
X_features = catch22.fit_transform(X_train)
print(f"Catch22 feature matrix: {X_features.shape}")  # (n_instances, 22)
```

### Module 6: Dataset Loading and Benchmarking

```python
from aeon.datasets import load_classification, load_from_tsf_file
from aeon.benchmarking.results_loaders import get_estimator_results_as_array
import numpy as np

# Load UCR/UEA dataset
X_train, y_train = load_classification("BasicMotions", split="train")
X_test, y_test   = load_classification("BasicMotions", split="test")
print(f"BasicMotions: train={X_train.shape}, classes={np.unique(y_train)}")

# Load custom .ts file (UCR format)
# X, y = load_from_tsf_file("my_dataset.ts")

# Compare to published benchmark results
# from aeon.benchmarking import plot_critical_difference_diagram
```

## Key Concepts

### Data Format Convention

aeon uses 3D NumPy arrays of shape `(n_instances, n_channels, n_timepoints)`:
- `n_instances`: number of time series (like `n_samples` in sklearn)
- `n_channels`: number of variables per time series (1 for univariate)
- `n_timepoints`: length of each series (can differ between instances for unequal-length)

Scikit-learn expects 2D `(n_samples, n_features)`. Use aeon's transformers to convert.

### ROCKET Family

ROCKET (Random Convolutional Kernel Transform) randomly generates 10,000 convolutional kernels of varying lengths, dilations, and biases, then applies them to each series to extract PPV (proportion of positive values) and max features. These 20,000 features are then classified with a linear model. MiniROCKET uses fewer, fixed kernels and is ~75× faster than ROCKET with similar accuracy. MultiROCKET extends to multivariate series.

## Common Workflows

### Workflow 1: Cross-Validated Classifier Comparison

```python
import numpy as np
from aeon.datasets import load_unit_test
from aeon.classification.convolution_based import RocketClassifier, MiniRocketClassifier
from aeon.classification.feature_based import Catch22Classifier
from sklearn.model_selection import cross_val_score

X, y = load_unit_test()  # Full dataset (train+test merged)

classifiers = {
    "ROCKET":     RocketClassifier(num_kernels=500, random_state=42),
    "MiniROCKET": MiniRocketClassifier(random_state=42),
    "Catch22":    Catch22Classifier(random_state=42),
}

print(f"Dataset: {X.shape}, classes: {np.unique(y)}")
for name, clf in classifiers.items():
    scores = cross_val_score(clf, X, y, cv=5, scoring="accuracy")
    print(f"{name:15s}: {scores.mean():.3f} ± {scores.std():.3f}")
```

### Workflow 2: Pipeline with Preprocessing and Classification

```python
import numpy as np
from aeon.datasets import load_unit_test
from aeon.transformations.collection.convolution_based import Rocket
from aeon.transformations.collection.normalize import TimeSeriesScaler
from sklearn.pipeline import Pipeline
from sklearn.linear_model import RidgeClassifierCV
from sklearn.preprocessing import StandardScaler

X_train, y_train = load_unit_test(split="train")
X_test, y_test   = load_unit_test(split="test")

# Normalize series → ROCKET features → Ridge
pipe = Pipeline([
    ("normalize", TimeSeriesScaler()),
    ("rocket",    Rocket(num_kernels=2000, random_state=42)),
    ("scale",     StandardScaler(with_mean=False)),
    ("clf",       RidgeClassifierCV(alphas=[0.01, 0.1, 1.0, 10.0])),
])

pipe.fit(X_train, y_train)
print(f"Pipeline accuracy: {pipe.score(X_test, y_test):.3f}")
```

## Key Parameters

| Parameter | Module/Class | Default | Range / Options | Effect |
|-----------|-------------|---------|-----------------|--------|
| `num_kernels` | `Rocket`, `RocketClassifier` | 10000 | 500–50000 | Number of random kernels; more = better accuracy, slower |
| `n_clusters` | `TimeSeriesKMeans` | 8 | 2–50 | Number of clusters for K-Means |
| `metric` | `TimeSeriesKMeans`, `KNN` | `"dtw"` | `"dtw"`, `"euclidean"`, `"msm"`, `"twe"` | Distance metric for similarity computation |
| `n_change_points` | `ClaSPSegmenter` | 1 | 1–20 | Expected number of change points to detect |
| `period_length` | `ClaSPSegmenter` | auto | 5–100 | Minimum segment length |
| `n_neighbors` | `KNeighborsTimeSeriesClassifier` | 1 | 1–20 | k for KNN; k=1 often best for time series |
| `averaging_method` | `TimeSeriesKMeans` | `"ba"` | `"ba"` (Barycentre), `"mean"` | Method for computing cluster prototypes |
| `random_state` | All stochastic | None | int | Seed for reproducibility |

## Common Recipes

### Recipe: Export ROCKET Features to DataFrame for AutoML

```python
import numpy as np
import pandas as pd
from aeon.transformations.collection.convolution_based import MiniRocket

np.random.seed(0)
X = np.random.randn(200, 1, 100)  # 200 univariate time series, length 100
y = (X[:, 0, :].mean(axis=1) > 0).astype(int)

transformer = MiniRocket(random_state=42)
X_features = transformer.fit_transform(X)  # shape: (200, 9996)

df = pd.DataFrame(X_features, columns=[f"f{i}" for i in range(X_features.shape[1])])
df["label"] = y
df.to_parquet("rocket_features.parquet", index=False)
print(f"Feature matrix: {df.shape}, saved to rocket_features.parquet")
```

### Recipe: Load and Classify a Custom Dataset

```python
import numpy as np
from aeon.classification.convolution_based import RocketClassifier

# Custom dataset: time series stored as 3D array
# Shape: (n_instances, n_channels, n_timepoints)
np.random.seed(42)
X_train = np.random.randn(150, 2, 80)  # 150 bivariate series, length 80
y_train = np.random.choice(["class_A", "class_B", "class_C"], 150)
X_test  = np.random.randn(50, 2, 80)
y_test  = np.random.choice(["class_A", "class_B", "class_C"], 50)

clf = RocketClassifier(num_kernels=2000, random_state=42)
clf.fit(X_train, y_train)
print(f"Test accuracy: {clf.score(X_test, y_test):.3f}")

# Save predictions
y_pred = clf.predict(X_test)
print(f"Predictions: {y_pred[:10]}")
```

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| `ImportError: numba` when using ROCKET | numba not installed | `pip install aeon[all_extras]` or `pip install numba` |
| Input shape error: expected 3D array | Passing 2D `(n, t)` instead of 3D `(n, 1, t)` | Reshape: `X = X[:, np.newaxis, :]` |
| KNN-DTW very slow on large datasets | DTW is O(n·m) per pair; all-pairs comparison is O(N²) | Use ROCKET instead for N>1000; or reduce series length |
| Clustering assigns all points to one cluster | Initial centroids too close or metric not suited | Set `n_init=10`; try different `metric` (`"msm"` or `"euclidean"`) |
| `load_classification` fails with download error | Network timeout or dataset name typo | Check available datasets: `aeon.datasets.list_datasets()`; download manually |
| `ClaSPSegmenter` detects wrong number of change points | `n_change_points` too high or `period_length` wrong | Set `period_length` to expected minimum segment length; validate with known signal |
| Memory error with large panel dataset | ROCKET transforms require `n_kernels × n_instances` matrix | Reduce `num_kernels`; process in batches with `partial_fit` |

## Related Skills

- `neurokit2` — time series generation (ECG, EDA) that feeds into aeon classifiers
- `scikit-learn-machine-learning` — sklearn-compatible downstream models for aeon features
- `matplotlib-scientific-plotting` — visualization of time series and classification results

## References

- [aeon documentation](https://www.aeon-toolkit.org/) — API reference, algorithm catalog, and tutorials
- [aeon GitHub](https://github.com/aeon-toolkit/aeon) — source code, benchmarks, and contribution guide
- [ROCKET paper: Dempster et al. (2020), DMKD](https://doi.org/10.1007/s10618-020-00701-z) — ROCKET algorithm description and UCR benchmark results
- [MiniROCKET paper: Dempster et al. (2021), KDD](https://doi.org/10.1145/3447548.3467231) — faster variant with comparable accuracy
- [UCR Time Series Archive](https://www.timeseriesclassification.com/) — 128 benchmark datasets for time series classification
