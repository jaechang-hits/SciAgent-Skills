---
name: "scikit-learn-machine-learning"
description: "Classical ML in Python: classification, regression, clustering, dim reduction, evaluation, tuning, preprocessing pipelines. Linear models, tree ensembles, SVMs, K-Means, PCA, t-SNE. Use PyTorch/TF for deep learning; XGBoost/LightGBM for scale."
license: "BSD-3-Clause"
---

# scikit-learn

## Overview

scikit-learn is the standard Python library for classical machine learning. It provides consistent APIs for supervised learning (classification, regression), unsupervised learning (clustering, dimensionality reduction), model evaluation, and preprocessing, with seamless integration into NumPy/pandas workflows.

## When to Use

- Building classification models for labeled data (spam detection, disease diagnosis, species identification)
- Predicting continuous outcomes with regression (price prediction, dose-response modeling)
- Clustering unlabeled data into groups (patient stratification, gene expression clusters)
- Reducing dimensionality for visualization or feature engineering (PCA, t-SNE on multi-omics data)
- Evaluating and comparing model performance with cross-validation
- Tuning hyperparameters systematically (grid search, random search)
- Building reproducible ML pipelines with preprocessing and modeling steps
- For deep learning tasks (images, NLP), use `pytorch` or `transformers` instead
- For large-scale gradient boosting, use `xgboost` or `lightgbm` instead

## Prerequisites

- **Python packages**: `scikit-learn`, `numpy`, `pandas`
- **Optional**: `matplotlib`, `seaborn` for visualization
- **Data**: Tabular data as NumPy arrays or pandas DataFrames

```bash
pip install scikit-learn numpy pandas matplotlib seaborn
```

## Quick Start

```python
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
from sklearn.datasets import load_breast_cancer

# Load dataset, split, train, evaluate in 10 lines
X, y = load_breast_cancer(return_X_y=True)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

clf = RandomForestClassifier(n_estimators=100, random_state=42)
clf.fit(X_train, y_train)
y_pred = clf.predict(X_test)

print(f"Accuracy: {accuracy_score(y_test, y_pred):.3f}")
print(classification_report(y_test, y_pred, target_names=["malignant", "benign"]))
```

## Core API

### Module 1: Data Preprocessing

Scaling, encoding, imputation, and feature engineering.

```python
from sklearn.preprocessing import StandardScaler, MinMaxScaler, OneHotEncoder
from sklearn.impute import SimpleImputer
import numpy as np

# Scaling: zero mean, unit variance
X = np.array([[1, 2], [3, 4], [5, 6]])
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)
print(f"Mean: {X_scaled.mean(axis=0)}, Std: {X_scaled.std(axis=0)}")
# Mean: [0. 0.], Std: [1. 1.]

# Imputation: fill missing values
X_missing = np.array([[1, np.nan], [3, 4], [np.nan, 6]])
imputer = SimpleImputer(strategy="median")
X_filled = imputer.fit_transform(X_missing)
print(f"Filled:\n{X_filled}")
```

```python
from sklearn.preprocessing import OneHotEncoder, OrdinalEncoder, LabelEncoder

# One-hot encoding for nominal categories
enc = OneHotEncoder(sparse_output=False, handle_unknown="ignore")
X_cat = np.array([["red"], ["blue"], ["green"], ["red"]])
X_encoded = enc.fit_transform(X_cat)
print(f"Categories: {enc.categories_}")
print(f"Encoded shape: {X_encoded.shape}")  # (4, 3)
```

### Module 2: Supervised Learning — Classification

Classifiers for discrete target prediction.

```python
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
from sklearn.datasets import load_iris
from sklearn.model_selection import train_test_split

X, y = load_iris(return_X_y=True)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, stratify=y, random_state=42)

# Compare classifiers
classifiers = {
    "LogisticRegression": LogisticRegression(max_iter=200),
    "RandomForest": RandomForestClassifier(n_estimators=100, random_state=42),
    "SVM": SVC(kernel="rbf", C=1.0),
    "GradientBoosting": GradientBoostingClassifier(n_estimators=100, random_state=42),
}
for name, clf in classifiers.items():
    clf.fit(X_train, y_train)
    print(f"{name}: accuracy = {clf.score(X_test, y_test):.3f}")
```

### Module 3: Supervised Learning — Regression

Regressors for continuous target prediction.

```python
from sklearn.linear_model import LinearRegression, Ridge, Lasso, ElasticNet
from sklearn.ensemble import RandomForestRegressor
from sklearn.datasets import make_regression
from sklearn.metrics import mean_squared_error, r2_score

X, y = make_regression(n_samples=200, n_features=10, noise=10, random_state=42)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

models = {
    "Linear": LinearRegression(),
    "Ridge": Ridge(alpha=1.0),
    "Lasso": Lasso(alpha=0.1),
    "RandomForest": RandomForestRegressor(n_estimators=100, random_state=42),
}
for name, model in models.items():
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)
    print(f"{name}: RMSE={mean_squared_error(y_test, y_pred, squared=False):.2f}, R²={r2_score(y_test, y_pred):.3f}")
```

### Module 4: Unsupervised Learning — Clustering

Clustering algorithms for unlabeled data.

```python
from sklearn.cluster import KMeans, DBSCAN, AgglomerativeClustering
from sklearn.metrics import silhouette_score
from sklearn.datasets import make_blobs

X, y_true = make_blobs(n_samples=300, centers=4, random_state=42)

# K-Means with elbow method
for k in [2, 3, 4, 5, 6]:
    km = KMeans(n_clusters=k, random_state=42, n_init=10)
    labels = km.fit_predict(X)
    sil = silhouette_score(X, labels)
    print(f"k={k}: silhouette={sil:.3f}, inertia={km.inertia_:.1f}")
```

```python
# DBSCAN — no need to specify k
from sklearn.cluster import DBSCAN

db = DBSCAN(eps=0.5, min_samples=5)
labels = db.fit_predict(X)
n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
n_noise = (labels == -1).sum()
print(f"DBSCAN: {n_clusters} clusters, {n_noise} noise points")
```

### Module 5: Dimensionality Reduction

PCA, t-SNE, and other methods for visualization and feature reduction.

```python
from sklearn.decomposition import PCA
from sklearn.manifold import TSNE
from sklearn.datasets import load_digits

X, y = load_digits(return_X_y=True)
print(f"Original shape: {X.shape}")  # (1797, 64)

# PCA — preserve 95% variance
pca = PCA(n_components=0.95)
X_pca = pca.fit_transform(X)
print(f"PCA: {X_pca.shape[1]} components, explained variance: {pca.explained_variance_ratio_.sum():.3f}")

# t-SNE — 2D visualization
tsne = TSNE(n_components=2, perplexity=30, random_state=42)
X_tsne = tsne.fit_transform(X)
print(f"t-SNE shape: {X_tsne.shape}")  # (1797, 2)
```

### Module 6: Model Evaluation & Selection

Cross-validation, metrics, hyperparameter tuning.

```python
from sklearn.model_selection import cross_val_score, GridSearchCV, StratifiedKFold
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.datasets import load_iris

X, y = load_iris(return_X_y=True)

# Cross-validation
clf = RandomForestClassifier(n_estimators=100, random_state=42)
scores = cross_val_score(clf, X, y, cv=StratifiedKFold(5), scoring="accuracy")
print(f"CV accuracy: {scores.mean():.3f} ± {scores.std():.3f}")
```

```python
# Hyperparameter tuning with GridSearchCV
param_grid = {
    "n_estimators": [50, 100, 200],
    "max_depth": [5, 10, None],
    "min_samples_split": [2, 5]
}
grid = GridSearchCV(
    RandomForestClassifier(random_state=42),
    param_grid, cv=5, scoring="accuracy", n_jobs=-1
)
grid.fit(X, y)
print(f"Best params: {grid.best_params_}")
print(f"Best score: {grid.best_score_:.3f}")
```

### Module 7: Pipelines

Chain preprocessing and models; prevent data leakage.

```python
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.impute import SimpleImputer
from sklearn.ensemble import GradientBoostingClassifier

# Mixed-type preprocessing
numeric_features = ["age", "income"]
categorical_features = ["gender", "occupation"]

preprocessor = ColumnTransformer([
    ("num", Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler", StandardScaler())
    ]), numeric_features),
    ("cat", Pipeline([
        ("imputer", SimpleImputer(strategy="most_frequent")),
        ("onehot", OneHotEncoder(handle_unknown="ignore"))
    ]), categorical_features),
])

pipe = Pipeline([
    ("preprocessor", preprocessor),
    ("classifier", GradientBoostingClassifier(random_state=42))
])
# pipe.fit(X_train, y_train); pipe.predict(X_test)
print("Pipeline steps:", [name for name, _ in pipe.steps])
```

## Common Workflows

### Workflow 1: End-to-End Classification

**Goal**: Complete classification workflow from data loading to evaluation.

```python
import pandas as pd
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report
from sklearn.datasets import load_breast_cancer

# Load data
X, y = load_breast_cancer(return_X_y=True, as_frame=True)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, stratify=y, random_state=42)

# Build pipeline
pipe = Pipeline([
    ("scaler", StandardScaler()),
    ("clf", RandomForestClassifier(n_estimators=200, random_state=42))
])

# Cross-validate
cv_scores = cross_val_score(pipe, X_train, y_train, cv=5, scoring="f1")
print(f"CV F1: {cv_scores.mean():.3f} ± {cv_scores.std():.3f}")

# Final evaluation
pipe.fit(X_train, y_train)
y_pred = pipe.predict(X_test)
print(classification_report(y_test, y_pred))
```

### Workflow 2: Clustering with Visualization

**Goal**: Cluster data and visualize with dimensionality reduction.

```python
from sklearn.datasets import make_blobs
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.metrics import silhouette_score
import matplotlib.pyplot as plt

# Generate and scale data
X, _ = make_blobs(n_samples=500, centers=4, random_state=42)
X_scaled = StandardScaler().fit_transform(X)

# Cluster
km = KMeans(n_clusters=4, random_state=42, n_init=10)
labels = km.fit_predict(X_scaled)
print(f"Silhouette: {silhouette_score(X_scaled, labels):.3f}")

# Visualize
X_2d = PCA(n_components=2).fit_transform(X_scaled)
plt.scatter(X_2d[:, 0], X_2d[:, 1], c=labels, cmap="viridis", s=20, alpha=0.7)
plt.title("K-Means Clustering (PCA projection)")
plt.savefig("clustering_result.png", dpi=150, bbox_inches="tight")
print("Saved clustering_result.png")
```

### Workflow 3: Feature Selection + Model Pipeline

**Goal**: Select best features and build a tuned model.

```python
from sklearn.datasets import make_classification
from sklearn.feature_selection import SelectKBest, f_classif
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC
from sklearn.model_selection import GridSearchCV

X, y = make_classification(n_samples=500, n_features=50, n_informative=10, random_state=42)

pipe = Pipeline([
    ("scaler", StandardScaler()),
    ("selector", SelectKBest(f_classif)),
    ("svm", SVC(kernel="rbf"))
])

param_grid = {
    "selector__k": [5, 10, 20],
    "svm__C": [0.1, 1, 10],
    "svm__gamma": ["scale", "auto"]
}

grid = GridSearchCV(pipe, param_grid, cv=5, scoring="accuracy", n_jobs=-1)
grid.fit(X, y)
print(f"Best params: {grid.best_params_}")
print(f"Best accuracy: {grid.best_score_:.3f}")
```

## Key Parameters

| Parameter | Module | Default | Range / Options | Effect |
|-----------|--------|---------|-----------------|--------|
| `n_estimators` | RandomForest, GradientBoosting | `100` | `50`-`1000` | Number of trees; higher = better but slower |
| `max_depth` | Tree-based models | `None` | `1`-`50`, `None` | Tree depth; `None` = no limit (can overfit) |
| `C` | SVM, LogisticRegression | `1.0` | `0.001`-`1000` | Regularization strength (inverse); lower = more regularization |
| `alpha` | Ridge, Lasso | `1.0` | `0.001`-`100` | Regularization strength; higher = more regularization |
| `n_clusters` | KMeans | required | `2`-`N` | Number of clusters to form |
| `eps` | DBSCAN | `0.5` | `0.01`-`10` | Neighborhood radius; smaller = more clusters |
| `n_components` | PCA | required | `1`-`N` or `0.0`-`1.0` | Components to keep; float = variance ratio |
| `perplexity` | t-SNE | `30` | `5`-`50` | Balance local/global structure |
| `cv` | GridSearchCV | `5` | `2`-`10` | Cross-validation folds |
| `scoring` | GridSearchCV, cross_val_score | varies | `accuracy`, `f1`, `roc_auc`, etc. | Evaluation metric |

## Common Recipes

### Recipe: Feature Importance Analysis

When to use: Understanding which features drive model predictions.

```python
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.datasets import load_iris

X, y = load_iris(return_X_y=True)
clf = RandomForestClassifier(n_estimators=200, random_state=42).fit(X, y)

importances = clf.feature_importances_
indices = np.argsort(importances)[::-1]
feature_names = load_iris().feature_names
for i in range(X.shape[1]):
    print(f"{feature_names[indices[i]]}: {importances[indices[i]]:.4f}")
```

### Recipe: Learning Curve Diagnosis

When to use: Diagnosing overfitting vs underfitting.

```python
from sklearn.model_selection import learning_curve
import matplotlib.pyplot as plt
import numpy as np

train_sizes, train_scores, val_scores = learning_curve(
    clf, X, y, cv=5, train_sizes=np.linspace(0.1, 1.0, 10), scoring="accuracy"
)
plt.plot(train_sizes, train_scores.mean(axis=1), label="Train")
plt.plot(train_sizes, val_scores.mean(axis=1), label="Validation")
plt.xlabel("Training size"); plt.ylabel("Accuracy"); plt.legend()
plt.savefig("learning_curve.png", dpi=150, bbox_inches="tight")
print("Saved learning_curve.png")
```

### Recipe: Save and Load Models

When to use: Persisting trained models for later use.

```python
import joblib

# Save
joblib.dump(pipe, "model_pipeline.joblib")
print("Model saved to model_pipeline.joblib")

# Load
loaded_pipe = joblib.load("model_pipeline.joblib")
y_pred = loaded_pipe.predict(X_test)
print(f"Loaded model predictions: {y_pred[:5]}")
```

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| `ConvergenceWarning` | Model didn't converge | Increase `max_iter` (e.g., 1000) or scale features with `StandardScaler` |
| High train accuracy, low test accuracy | Overfitting | Add regularization, reduce `max_depth`, use cross-validation |
| `ValueError: unknown categories` | New categories in test data | Use `OneHotEncoder(handle_unknown='ignore')` |
| `MemoryError` with large data | Full dataset in memory | Use `SGDClassifier`/`MiniBatchKMeans` for incremental learning |
| Poor clustering results | Unscaled features or wrong k | Scale features first; use silhouette score to find optimal k |
| `NotFittedError` | Predict before fit | Call `model.fit(X_train, y_train)` first |
| Different results each run | Missing `random_state` | Set `random_state=42` in model and `train_test_split` |
| Slow GridSearchCV | Large parameter grid | Use `RandomizedSearchCV` or `HalvingGridSearchCV`; add `n_jobs=-1` |

## References

- [scikit-learn User Guide](https://scikit-learn.org/stable/user_guide.html) — official documentation
- [scikit-learn API Reference](https://scikit-learn.org/stable/api/index.html) — complete API
- [scikit-learn Examples Gallery](https://scikit-learn.org/stable/auto_examples/) — tutorials
- Pedregosa et al. (2011). Scikit-learn: Machine Learning in Python. *JMLR* 12:2825-2830.
