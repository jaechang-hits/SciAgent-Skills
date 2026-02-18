# Data Handling & Competing Risks Reference

Detailed reference for data preparation, preprocessing pipelines, and competing risks analysis with scikit-survival. For core usage patterns, see Core API Modules 1 and 7 in the main SKILL.md.

## Survival Data Structure

### The Surv Object

Survival data uses NumPy structured arrays with two fields:
- **event** (bool): True if event occurred, False if censored
- **time** (float64): Time to event or censoring (must be positive)

```python
import numpy as np
from sksurv.util import Surv

# From separate arrays
event = np.array([True, False, True, False, True])
time = np.array([5.2, 10.1, 3.7, 8.9, 6.3])
y = Surv.from_arrays(event=event, time=time)
print(y.dtype)    # [('event', '?'), ('time', '<f8')]
print(y[0])       # (True, 5.2)
print(y["event"]) # [True, False, True, False, True]
print(y["time"])  # [5.2, 10.1, 3.7, 8.9, 6.3]
```

### Types of Censoring

**Right censoring** (most common, handled by sksurv):
- Subject did not experience event by end of study
- Subject lost to follow-up
- Subject withdrew from study

**Left censoring**: Event occurred before observation began (rare; use lifelines).

**Interval censoring**: Event occurred in known time interval (requires specialized methods; use lifelines or R packages).

## Loading Data

### Built-in Datasets

```python
from sksurv.datasets import (
    load_aids,                    # AIDS clinical trial
    load_breast_cancer,           # Breast cancer gene expression
    load_gbsg2,                   # German Breast Cancer Study Group 2
    load_veterans_lung_cancer,    # Veterans lung cancer trial
    load_whas500,                 # Worcester Heart Attack Study
    load_flchain,                 # Free light chain study
)

X, y = load_breast_cancer()
print(f"Features: {X.shape}")               # (198, 80)
print(f"Events: {y['event'].sum()}")         # number of events
print(f"Censoring rate: {1 - y['event'].mean():.1%}")
print(f"Median time: {np.median(y['time']):.1f}")
print(f"Time range: [{y['time'].min():.1f}, {y['time'].max():.1f}]")
```

### Loading Custom Data

```python
import pandas as pd
from sksurv.util import Surv

# From CSV via Surv.from_dataframe
df = pd.read_csv("survival_data.csv")
X = df.drop(["time", "event"], axis=1)
y = Surv.from_dataframe("event", "time", df)

# From CSV via Surv.from_arrays (more control)
y = Surv.from_arrays(
    event=df["event"].astype(bool),  # Ensure boolean
    time=df["time"].astype(float),    # Ensure float
)
```

```python
from sksurv.io import loadarff

# Load ARFF format (Weka format)
data = loadarff("survival_data.arff")
X_arff = data[0]  # pandas DataFrame
y_arff = data[1]  # structured array
```

## Data Preprocessing

### Handling Categorical Variables

```python
from sksurv.preprocessing import OneHotEncoder, encode_categorical
import pandas as pd

# Method 1: encode_categorical (auto-detect all categorical columns)
X_encoded = encode_categorical(X)

# Method 2: OneHotEncoder (survival-aware, for specific columns)
categorical_cols = ["gender", "race", "treatment"]
encoder = OneHotEncoder()
X_cat_encoded = encoder.fit_transform(X[categorical_cols])
numerical_cols = [c for c in X.columns if c not in categorical_cols]
X_processed = pd.concat([X[numerical_cols], X_cat_encoded], axis=1)

# Method 3: pandas get_dummies
X_encoded = pd.get_dummies(X, drop_first=True)
```

### Standardization

Critical for Cox models (with regularization) and SVMs. Not needed for tree-based models (RSF, GBS).

```python
from sklearn.preprocessing import StandardScaler
import pandas as pd

scaler = StandardScaler()
X_scaled = scaler.fit_transform(X_encoded)
X_scaled = pd.DataFrame(X_scaled, columns=X_encoded.columns, index=X_encoded.index)
```

### Handling Missing Data

```python
import numpy as np
from sklearn.impute import SimpleImputer

# Check missing values
missing = X.isnull().sum()
print(missing[missing > 0])

# Mean imputation for numerical features
num_imputer = SimpleImputer(strategy="mean")
X_num = X.select_dtypes(include=[np.number])
X_num_imputed = num_imputer.fit_transform(X_num)

# Most frequent for categorical
cat_imputer = SimpleImputer(strategy="most_frequent")
X_cat = X.select_dtypes(include=["object", "category"])
X_cat_imputed = cat_imputer.fit_transform(X_cat)
```

```python
# Advanced: iterative (MICE-like) imputation
from sklearn.experimental import enable_iterative_imputer
from sklearn.impute import IterativeImputer

imputer = IterativeImputer(random_state=42, max_iter=10)
X_imputed = imputer.fit_transform(X)
```

### Feature Selection

```python
from sklearn.feature_selection import VarianceThreshold, SelectKBest

# Remove low-variance features
var_sel = VarianceThreshold(threshold=0.01)
X_var = var_sel.fit_transform(X)
print(f"Kept {X_var.shape[1]} / {X.shape[1]} features")

# Select top k features
kbest = SelectKBest(k=10)
X_best = kbest.fit_transform(X, y)
selected_features = X.columns[kbest.get_support()]
print(f"Selected: {list(selected_features)}")
```

## Data Quality Checks

### Validate Survival Data

```python
import numpy as np

def validate_survival_data(X, y):
    """Check survival data quality before modeling."""
    # Check for non-positive times
    if np.any(y["time"] <= 0):
        print(f"WARNING: {np.sum(y['time'] <= 0)} non-positive survival times")

    # Check for missing/infinite times
    if np.any(~np.isfinite(y["time"])):
        print(f"WARNING: {np.sum(~np.isfinite(y['time']))} missing survival times")

    # Censoring rate
    censor_rate = 1 - y["event"].mean()
    print(f"Censoring rate: {censor_rate:.1%}")
    if censor_rate > 0.7:
        print("  -> High censoring (>70%): use Uno's C-index, consider data collection")

    # Events per feature ratio (Cox rule of thumb: >= 10)
    n_events = y["event"].sum()
    n_features = X.shape[1]
    epf = n_events / n_features
    print(f"Events: {n_events}, Features: {n_features}, EPF: {epf:.1f}")
    if epf < 10:
        print("  -> Low EPF: use CoxNet, ensemble, or reduce features")

    # Time statistics
    print(f"Median time: {np.median(y['time']):.1f}")
    print(f"Range: [{y['time'].min():.1f}, {y['time'].max():.1f}]")

validate_survival_data(X, y)
```

## Train-Test Split

### Random Split

```python
from sklearn.model_selection import train_test_split

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42,
)
```

### Stratified Split

Maintain similar censoring rates and time distributions across splits:

```python
import pandas as pd
from sklearn.model_selection import train_test_split

# Stratify by event status + time quartiles
time_q = pd.qcut(y["time"], q=4, labels=False)
strat_labels = y["event"].astype(int) * 10 + time_q

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, stratify=strat_labels, random_state=42,
)

# Verify distributions
print(f"Train censoring: {1 - y_train['event'].mean():.1%}")
print(f"Test censoring:  {1 - y_test['event'].mean():.1%}")
print(f"Train median time: {np.median(y_train['time']):.1f}")
print(f"Test median time:  {np.median(y_test['time']):.1f}")
```

## Complete Preprocessing Pipeline

```python
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer
from sksurv.linear_model import CoxPHSurvivalAnalysis

# Preprocessing + model in one pipeline (prevents data leakage)
pipeline = Pipeline([
    ("imputer", SimpleImputer(strategy="mean")),
    ("scaler", StandardScaler()),
    ("model", CoxPHSurvivalAnalysis()),
])

pipeline.fit(X_train, y_train)
risk_scores = pipeline.predict(X_test)
print(f"Risk score range: [{risk_scores.min():.2f}, {risk_scores.max():.2f}]")
```

## Competing Risks Analysis

### Overview

Competing risks occur when multiple mutually exclusive events can happen. When one event occurs, it prevents others. Examples: relapse vs death in remission, death from different causes.

The **Cumulative Incidence Function (CIF)** gives P(T <= t, event type = k), accounting for competing events. This differs from Kaplan-Meier, which overestimates when competing risks exist.

### Data Format for Competing Risks

```python
import numpy as np
from sksurv.util import Surv

# Event types: 0=censored, 1=event type 1, 2=event type 2
event_types = np.array([0, 1, 2, 1, 0, 2, 1])
times = np.array([10.2, 5.3, 8.1, 3.7, 12.5, 6.8, 4.2])

# For CIF estimation: pass structured array with integer event codes
# For cause-specific Cox: create separate binary outcomes per event
y_any_event = Surv.from_arrays(event=(event_types > 0), time=times)
y_type1 = Surv.from_arrays(event=(event_types == 1), time=times)
y_type2 = Surv.from_arrays(event=(event_types == 2), time=times)
```

### Cumulative Incidence Estimation

```python
from sksurv.nonparametric import cumulative_incidence_competing_risks
import matplotlib.pyplot as plt

# Estimate CIF for each event type
time_pts, cif_1, cif_2 = cumulative_incidence_competing_risks(y_competing)

plt.figure(figsize=(10, 6))
plt.step(time_pts, cif_1, where="post", label="Relapse", linewidth=2)
plt.step(time_pts, cif_2, where="post", label="Death in remission", linewidth=2)
plt.xlabel("Time")
plt.ylabel("Cumulative Incidence")
plt.title("Competing Risks: Cumulative Incidence Functions")
plt.legend()
plt.grid(True, alpha=0.3)
plt.savefig("cif_plot.png", dpi=150)
```

**Interpretation**:
- CIF(t) for event k = probability of experiencing event k by time t
- Sum of all CIFs = total event probability
- 1 - sum(CIFs) = probability of being event-free

### Stratified Group Comparison

```python
from sksurv.nonparametric import cumulative_incidence_competing_risks
import matplotlib.pyplot as plt

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

for group, mask in [("Treatment A", mask_a), ("Treatment B", mask_b)]:
    t, cif1, cif2 = cumulative_incidence_competing_risks(y[mask])
    ax1.step(t, cif1, where="post", label=group, linewidth=2)
    ax2.step(t, cif2, where="post", label=group, linewidth=2)

ax1.set_title("Event Type 1: Relapse")
ax1.set_xlabel("Time")
ax1.set_ylabel("Cumulative Incidence")
ax1.legend()
ax1.grid(True, alpha=0.3)

ax2.set_title("Event Type 2: Death")
ax2.set_xlabel("Time")
ax2.set_ylabel("Cumulative Incidence")
ax2.legend()
ax2.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig("cif_by_group.png", dpi=150)
```

### Cause-Specific Hazard Models

Fit separate Cox models for each event type, treating other events as censored.

```python
from sksurv.linear_model import CoxPHSurvivalAnalysis
from sksurv.util import Surv
from sksurv.metrics import concordance_index_ipcw
import numpy as np

# Separate outcomes per event type
y_relapse = Surv.from_arrays(event=(event_types == 1), time=times)
y_death = Surv.from_arrays(event=(event_types == 2), time=times)

# Fit cause-specific models
cox_relapse = CoxPHSurvivalAnalysis()
cox_relapse.fit(X, y_relapse)

cox_death = CoxPHSurvivalAnalysis()
cox_death.fit(X, y_death)

# Interpret: a covariate may increase risk for one event but decrease for another
print("Relapse Model:")
for name, coef in zip(X.columns, cox_relapse.coef_):
    print(f"  {name:15s}: HR = {np.exp(coef):.3f}")

print("\nDeath Model:")
for name, coef in zip(X.columns, cox_death.coef_):
    print(f"  {name:15s}: HR = {np.exp(coef):.3f}")
```

### When to Use Competing Risks

**Use competing risks when**:
- Multiple mutually exclusive event types exist
- One event prevents observation of others
- Competing event rate > 10-20% of total events
- Need event-type-specific probability estimates

**Approach comparison**:

| Approach | Best For | In sksurv? |
|----------|----------|------------|
| Cause-specific hazard | Understanding etiology, direct effect | Yes (separate Cox) |
| Fine-Gray subdistribution | Clinical prediction, risk stratification | No (use lifelines/R) |
| Cumulative incidence | Non-parametric estimation | Yes |

### Common Mistakes in Competing Risks

1. **Using KM for event-specific probabilities**: Kaplan-Meier treating competing events as censored overestimates. Always use CIF.
2. **Ignoring competing risks when substantial**: If competing event rate > 10-20%, standard methods are biased.
3. **Confusing cause-specific and subdistribution hazards**: They answer different questions (etiology vs prediction).

---

Condensed from originals: `data-handling.md` (494 lines), `competing-risks.md` (397 lines). Total original: 891 lines.

Retained: Surv array creation (from_arrays, from_dataframe), built-in dataset loading, ARFF I/O, categorical encoding (3 methods), standardization, missing data handling (simple + iterative), feature selection (variance + k-best), data validation checks, train-test split (random + stratified), complete Pipeline, competing risks overview, CIF estimation and plotting, data format for competing risks, stratified group comparison, cause-specific hazard modeling with interpretation, when-to-use decision guidance, common mistakes.

Omitted from data-handling.md: Custom `preprocess_survival_data()` function with docstring (40+ lines; duplicates sklearn Pipeline pattern in Complete Preprocessing Pipeline section and SKILL.md Workflow 1). `check_events_per_feature()` standalone function (capability consolidated into `validate_survival_data()`). "Summary: Complete Data Preparation Workflow" (duplicates Pipeline section). Time-varying covariates note (sksurv does not support; 3-line reference to lifelines).

Omitted from competing-risks.md: Fine-Gray subdistribution model code (not available in sksurv; noted as lifelines/R alternative in approach comparison table). Gray's test code (not in sksurv; noted as lifelines). Full simulated data example (60+ lines generating synthetic competing risks dataset; the cause-specific hazard modeling code block demonstrates the same concepts with real data patterns). Detailed censoring-in-competing-risks explanation (3 types of censoring in CR context; core concept retained in "Common Mistakes" and "When to Use" sections).

Combined coverage: ~290 retained lines + ~50 lines relocated to SKILL.md Core API Modules 1 and 7 = ~340 lines (~38% of 891 originals). All critical data handling and competing risks capabilities represented.
