# ML Transformers & Visualization

## Advanced Scalers

```python
import vaex, vaex.ml
import numpy as np

np.random.seed(42)
df = vaex.from_arrays(
    income=np.random.uniform(20000, 150000, 10_000),
    age=np.random.randint(18, 70, 10_000).astype(float),
    score=np.random.uniform(-50, 300, 10_000),
)

# MinMaxScaler — scales to [0, 1] range
df = vaex.ml.MinMaxScaler(features=['income', 'age']).fit_transform(df)
print(f"MinMax income: [{df.minmax_scaled_income.min():.1f}, {df.minmax_scaled_income.max():.1f}]")  # [0.0, 1.0]

# MaxAbsScaler — scales by absolute max, preserves sign and sparsity
df = vaex.ml.MaxAbsScaler(features=['score']).fit_transform(df)
print(f"MaxAbs score: [{df.maxabs_scaled_score.min():.2f}, {df.maxabs_scaled_score.max():.2f}]")

# RobustScaler — uses median/IQR, robust to outliers
df = vaex.ml.RobustScaler(features=['income']).fit_transform(df)
print(f"Robust income median ~0: {df.robust_scaled_income.median_approx():.2f}")
```

## Advanced Encoders

```python
import vaex, vaex.ml
import numpy as np

np.random.seed(42)
df = vaex.from_arrays(
    city=np.random.choice(['NYC', 'LA', 'Chicago', 'Houston'], 10_000),
    category=np.random.choice(['A', 'B', 'C'], 10_000),
    target=np.random.randint(0, 2, 10_000),
)

# FrequencyEncoder — encodes by relative frequency of each category
df = vaex.ml.FrequencyEncoder(features=['city']).fit_transform(df)
print(f"Frequency encoded NYC: {df[df.city == 'NYC'].frequency_encoded_city.values[0]:.3f}")

# TargetEncoder — encodes by mean of target per category (supervised)
df = vaex.ml.TargetEncoder(features=['category'], target='target').fit_transform(df)
print(f"Target encoded unique: {df.target_encoded_category.unique()}")

# WeightOfEvidenceEncoder — log(odds) per category, used in credit scoring
df = vaex.ml.WeightOfEvidenceEncoder(features=['city'], target='target').fit_transform(df)
print(f"WoE columns: {[c for c in df.column_names if 'woe' in c]}")
```

## CycleTransformer (Cyclic Features)

Encodes cyclic features (hour, day-of-week, month) as sine/cosine pairs so that boundary values (e.g., hour 23 and hour 0) remain close.

```python
import vaex, vaex.ml
import numpy as np

df = vaex.from_arrays(hour=np.arange(24, dtype=float), month=np.tile(np.arange(1, 13), 2)[:24].astype(float))

df = vaex.ml.CycleTransformer(features=['hour'], n=24).fit_transform(df)
print(f"Hour columns: {[c for c in df.column_names if 'hour' in c and c != 'hour']}")  # ['hour_x', 'hour_y']
print(f"Hour 0:  x={df[df.hour==0].hour_x.values[0]:.3f}, y={df[df.hour==0].hour_y.values[0]:.3f}")
print(f"Hour 23: x={df[df.hour==23].hour_x.values[0]:.3f}, y={df[df.hour==23].hour_y.values[0]:.3f}")

df = vaex.ml.CycleTransformer(features=['month'], n=12).fit_transform(df)
```

## Discretizer (Binning)

```python
import vaex, vaex.ml
import numpy as np

df = vaex.from_arrays(age=np.random.uniform(18, 80, 10_000), income=np.random.lognormal(11, 0.5, 10_000))

df = vaex.ml.Discretizer(features=['age'], n_bins=5, strategy='uniform').fit_transform(df)
print(f"Age bins (uniform): {sorted(df.discretized_age.unique())}")  # [0, 1, 2, 3, 4]

df = vaex.ml.Discretizer(features=['income'], n_bins=4, strategy='quantile').fit_transform(df)
for b in sorted(df.discretized_income.unique()):
    print(f"  Bin {b}: {len(df[df.discretized_income == b])} samples")  # ~2500 each
```

## RandomProjection

Faster than PCA for very high-dimensional data; uses Johnson-Lindenstrauss random matrices.

```python
import vaex, vaex.ml
import numpy as np

features = [f'f{i}' for i in range(50)]
df = vaex.from_dict({f: np.random.randn(5_000) for f in features})

df = vaex.ml.RandomProjection(features=features, n_components=10).fit_transform(df)
rp_cols = [c for c in df.column_names if c.startswith('random_projection')]
print(f"Projected dims: {len(rp_cols)}")  # 10
```

## KMeans Clustering

```python
import vaex, vaex.ml
import numpy as np

np.random.seed(42)
centers = [(-3, -3), (0, 3), (3, -1)]
x = np.concatenate([np.random.normal(c[0], 0.8, 3000) for c in centers])
y = np.concatenate([np.random.normal(c[1], 0.8, 3000) for c in centers])
df = vaex.from_arrays(x=x, y=y)

df = vaex.ml.StandardScaler(features=['x', 'y']).fit_transform(df)
kmeans = vaex.ml.KMeans(features=['standard_scaled_x', 'standard_scaled_y'], n_clusters=3, n_init=5)
df = kmeans.fit_transform(df)

for label in sorted(df.prediction_kmeans.unique()):
    print(f"  Cluster {label}: {len(df[df.prediction_kmeans == label])} samples")
print(f"Centers shape: {np.array(kmeans.cluster_centers).shape}")  # (3, 2)
```

## External Library Integration

All sklearn-compatible models work via `vaex.ml.sklearn.Predictor`. The pattern is identical for XGBoost, LightGBM, CatBoost, and any sklearn-API model.

```python
import vaex, vaex.ml
import numpy as np

np.random.seed(42)
n = 10_000
df = vaex.from_arrays(f1=np.random.randn(n), f2=np.random.randn(n),
                       target=(np.random.randn(n) > 0).astype(int))
train, test = df[:8000], df[8000:]
features = ['f1', 'f2']

# --- XGBoost ---
import xgboost as xgb
m = vaex.ml.sklearn.Predictor(features=features, target='target',
    model=xgb.XGBClassifier(n_estimators=100, max_depth=3, eval_metric='logloss'),
    prediction_name='xgb_pred')
m.fit(train); test = m.transform(test)
print(f"XGBoost: {(test.xgb_pred == test.target).mean():.3f}")

# --- LightGBM ---
import lightgbm as lgb
m = vaex.ml.sklearn.Predictor(features=features, target='target',
    model=lgb.LGBMClassifier(n_estimators=100, verbose=-1),
    prediction_name='lgb_pred')
m.fit(train); test = m.transform(test)
print(f"LightGBM: {(test.lgb_pred == test.target).mean():.3f}")

# --- CatBoost ---
from catboost import CatBoostClassifier
m = vaex.ml.sklearn.Predictor(features=features, target='target',
    model=CatBoostClassifier(iterations=100, verbose=0),
    prediction_name='cat_pred')
m.fit(train); test = m.transform(test)
print(f"CatBoost: {(test.cat_pred == test.target).mean():.3f}")
```

### Keras/TensorFlow Integration

Wrap Keras as an sklearn-compatible estimator (`BaseEstimator` + `ClassifierMixin` with `fit`/`predict`) to use with `vaex.ml.sklearn.Predictor`. The wrapper must set `self.classes_` in `fit()` and return integer predictions from `predict()`. Then use identically: `vaex.ml.sklearn.Predictor(features=..., model=KerasWrapper(), prediction_name=...)`.

## Cross-Validation (Manual K-Fold)

```python
import vaex, vaex.ml
import numpy as np
from sklearn.ensemble import RandomForestClassifier

np.random.seed(42)
df = vaex.from_arrays(f1=np.random.randn(10_000), f2=np.random.randn(10_000),
                       target=(np.random.randn(10_000) > 0).astype(int))
k, fold_size, scores = 5, 2000, []
for i in range(k):
    s, e = i * fold_size, (i + 1) * fold_size
    train_fold = vaex.concat([df[:s], df[e:]])
    m = vaex.ml.sklearn.Predictor(features=['f1','f2'], target='target',
        model=RandomForestClassifier(n_estimators=50, random_state=42),
        prediction_name='cv_pred')
    m.fit(train_fold); test_fold = m.transform(df[s:e])
    scores.append((test_fold.cv_pred == test_fold.target).mean())
print(f"CV accuracy: {np.mean(scores):.3f} +/- {np.std(scores):.3f}")
```

## Feature Selection

```python
import vaex, numpy as np

df = vaex.from_arrays(f1=np.random.randn(10_000), f2=np.random.randn(10_000), target=np.random.randn(10_000))
df['f3'] = df.f1 * 0.9 + np.random.randn(10_000) * 0.1  # correlated with f1

# Correlation-based: use df.correlation() to find redundant features
for a, b in [('f1','f2'), ('f1','f3'), ('f2','f3')]:
    r = df.correlation(df[a], df[b])
    if abs(r) > 0.9: print(f"DROP one of {a}-{b}: r={r:.3f}")

# Variance-based: use df[col].var() to find near-constant features
df2 = vaex.from_arrays(high=np.random.randn(10_000)*10, const=np.ones(10_000))
for f in df2.column_names:
    print(f"  {f}: var={df2[f].var():.4f} {'KEEP' if df2[f].var() > 0.01 else 'DROP'}")
```

## Imbalanced Data Handling

```python
import vaex, vaex.ml, numpy as np
from sklearn.ensemble import RandomForestClassifier

target = np.concatenate([np.zeros(9500), np.ones(500)]).astype(int); np.random.shuffle(target)
df = vaex.from_arrays(f1=np.random.randn(10_000), f2=np.random.randn(10_000), target=target)

# Method 1: Class weights (pass class_weight='balanced' to sklearn model)
m = vaex.ml.sklearn.Predictor(features=['f1','f2'], target='target',
    model=RandomForestClassifier(class_weight='balanced', random_state=42), prediction_name='pred')
m.fit(df[:8000]); print(f"Weighted acc: {(m.transform(df[8000:]).pred == df[8000:].target).mean():.3f}")

# Method 2: Undersampling — slice majority to match minority count
minority, majority = df[df.target == 1], df[df.target == 0]
balanced = vaex.concat([minority, majority[np.random.choice(len(majority), len(minority), replace=False)]])
print(f"Balanced: {len(balanced)} ({len(minority)} per class)")

# Method 3: Oversampling minority with Gaussian noise
oi = np.random.choice(len(minority), size=len(majority)-len(minority), replace=True)
synth = vaex.from_arrays(f1=minority.f1.values[oi]+np.random.randn(len(oi))*0.1,
    f2=minority.f2.values[oi]+np.random.randn(len(oi))*0.1, target=np.ones(len(oi), dtype=int))
print(f"Oversampled: {len(vaex.concat([df, synth]))} rows")
```

## End-to-End Classification Pipeline

```python
import vaex, vaex.ml, numpy as np
from sklearn.ensemble import GradientBoostingClassifier

np.random.seed(42); n = 20_000
df = vaex.from_arrays(age=np.random.randint(18,70,n).astype(float),
    income=np.random.lognormal(11,0.5,n), hours=np.random.randint(0,24,n).astype(float),
    dept=np.random.choice(['Eng','Sales','Marketing','HR'], n), target=np.random.randint(0,2,n))

# Preprocessing chain: encode, scale, cycle, discretize
df = vaex.ml.LabelEncoder(features=['dept']).fit_transform(df)
df = vaex.ml.StandardScaler(features=['age','income']).fit_transform(df)
df = vaex.ml.CycleTransformer(features=['hours'], n=24).fit_transform(df)
df = vaex.ml.Discretizer(features=['income'], n_bins=5, strategy='quantile').fit_transform(df)

feats = ['standard_scaled_age','standard_scaled_income','label_encoded_dept',
         'hours_x','hours_y','discretized_income']
model = vaex.ml.sklearn.Predictor(features=feats, target='target',
    model=GradientBoostingClassifier(n_estimators=100, max_depth=3, random_state=42),
    prediction_name='prediction')
train, test = df[:16000], df[16000:]
model.fit(train); test = model.transform(test)
print(f"Accuracy: {(test.prediction == test.target).mean():.3f}")
train.state_write('pipeline.json')  # Deploy: new_df.state_load('pipeline.json')
```

## Feature Engineering Pipeline

```python
import vaex, vaex.ml, numpy as np

np.random.seed(42); n = 10_000
df = vaex.from_arrays(price=np.random.lognormal(4,1,n), qty=np.random.randint(1,100,n).astype(float),
    hour=np.random.randint(0,24,n).astype(float), dow=np.random.randint(0,7,n).astype(float),
    store=np.random.choice(['A','B','C'], n))

df['revenue'] = df.price * df.qty; df['log_price'] = df.price.log()  # Virtual columns
df['is_weekend'] = (df.dow >= 5).astype('int')
df = vaex.ml.CycleTransformer(features=['hour'], n=24).fit_transform(df)
df = vaex.ml.CycleTransformer(features=['dow'], n=7).fit_transform(df)
df = vaex.ml.FrequencyEncoder(features=['store']).fit_transform(df)
df = vaex.ml.Discretizer(features=['price'], n_bins=4, strategy='quantile').fit_transform(df)
df = vaex.ml.RobustScaler(features=['revenue','log_price','qty']).fit_transform(df)

new_cols = [c for c in df.column_names if c not in ['price','qty','hour','dow','store']]
print(f"Engineered features ({len(new_cols)}): {sorted(new_cols)}")
df.state_write('feature_engineering_state.json')
```

## Advanced Color Scales and Resolution

```python
import vaex, numpy as np, matplotlib.pyplot as plt

df = vaex.from_arrays(x=np.random.normal(0,1,500_000), y=np.random.normal(0,1,500_000))

# Color scale transforms: identity (linear), log, log10, sqrt
fig, axes = plt.subplots(2, 2, figsize=(12, 10))
for ax, f in zip(axes.flat, ['identity', 'log', 'log10', 'sqrt']):
    df.plot(df.x, df.y, f=f, limits='99.7%', shape=(128,128), colormap='inferno', ax=ax, show=False)
    ax.set_title(f'f={f!r}')
plt.tight_layout(); plt.savefig('color_scales.png', dpi=150, bbox_inches='tight'); plt.close()
# Resolution: shape=(32,32) for fast preview, (512,512) for publication quality
```

## Multiple Statistics Subplots

```python
import vaex, numpy as np, matplotlib.pyplot as plt

df = vaex.from_arrays(x=np.random.normal(0,1,200_000), y=np.random.normal(0,1,200_000),
                       value=np.random.exponential(10,200_000))
fig, axes = plt.subplots(1, 4, figsize=(24, 5))
stats = [('count(*)', 'log'), (vaex.stat.mean(df.value), None),
         (vaex.stat.std(df.value), None), (vaex.stat.sum(df.value), 'log')]
titles = ['Count (log)', 'Mean', 'Std', 'Sum (log)']
for ax, (what, f), t in zip(axes, stats, titles):
    kw = dict(what=what, limits='99%', shape=(100,100), ax=ax, show=False)
    if f: kw['f'] = f
    df.plot(df.x, df.y, **kw); ax.set_title(t)
plt.tight_layout(); plt.savefig('stats_subplots.png', dpi=150, bbox_inches='tight'); plt.close()
```

## Faceted Plots and Batch Plotting

```python
import vaex, numpy as np, matplotlib.pyplot as plt

df = vaex.from_arrays(x=np.random.normal(0,1,100_000), y=np.random.normal(0,1,100_000),
    cat=np.random.choice(['A','B','C','D'], 100_000), metric=np.random.exponential(5, 100_000))

# Faceted: all categories in one figure
cats = sorted(df.cat.unique())
fig, axes = plt.subplots(1, len(cats), figsize=(5*len(cats), 5))
for ax, c in zip(axes, cats):
    sub = df[df.cat == c]
    sub.plot(sub.x, sub.y, limits=[[-3,3],[-3,3]], shape=(64,64), f='log', ax=ax, show=False)
    ax.set_title(f'{c} (n={len(sub):,})')
plt.tight_layout(); plt.savefig('faceted.png', dpi=150, bbox_inches='tight'); plt.close()

# Batch: separate files per group
for c in cats:
    sub = df[df.cat == c]
    fig, ax = plt.subplots(figsize=(6, 4))
    sub.plot1d(sub.metric, limits=[0,30], shape=60, ax=ax, show=False)
    ax.set_title(f'{c} Distribution')
    plt.tight_layout(); plt.savefig(f'batch_{c}.png', dpi=150, bbox_inches='tight'); plt.close()
```

## Interactive Jupyter Widgets

Requires `vaex-jupyter`. In Jupyter: `df.plot_widget(df.x, df.y, f='log', shape=256, selection=[True, False])` for interactive heatmaps; `df.sample(n=10_000).scatter_widget(df.x, df.y, color=df.z)` for scatter. Selections are interactive -- brush to select regions, linked plots update automatically.

## Contour Plots from Binned Data

```python
import vaex, numpy as np, matplotlib.pyplot as plt

df = vaex.from_arrays(x=np.random.normal(0,1,500_000), y=np.random.normal(0,1,500_000))
counts = df.count(binby=[df.x, df.y], limits=[[-4,4],[-4,4]], shape=(100,100))
xe, ye = np.linspace(-4, 4, 100), np.linspace(-4, 4, 100)

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
ax1.contourf(xe, ye, np.log1p(counts.T), levels=20, cmap='viridis'); ax1.set_title('Filled')
ax2.contour(xe, ye, np.log1p(counts.T), levels=10, cmap='plasma'); ax2.set_title('Line')
plt.tight_layout(); plt.savefig('contours.png', dpi=150, bbox_inches='tight'); plt.close()
```

## Vector Field Overlay

```python
import vaex, numpy as np, matplotlib.pyplot as plt

df = vaex.from_arrays(x=np.random.uniform(-5,5,200_000), y=np.random.uniform(-5,5,200_000),
                       vx=np.random.normal(0,1,200_000), vy=np.random.normal(0,1,200_000))
lim, gs = [[-5,5],[-5,5]], (20, 20)
fig, ax = plt.subplots(figsize=(10, 10))
df.plot(df.x, df.y, f='log', limits=lim, shape=(128,128), colormap='Greys', ax=ax, show=False)
mvx = df.mean(df.vx, binby=[df.x, df.y], limits=lim, shape=gs)
mvy = df.mean(df.vy, binby=[df.x, df.y], limits=lim, shape=gs)
X, Y = np.meshgrid(np.linspace(-5,5,gs[0]), np.linspace(-5,5,gs[1]))
ax.quiver(X, Y, mvx.T, mvy.T, color='red', alpha=0.7, scale=30)
plt.savefig('vector_field.png', dpi=150, bbox_inches='tight'); plt.close()
```

## Plotly Integration

```python
import vaex, numpy as np, plotly.graph_objects as go

df = vaex.from_arrays(x=np.random.normal(0,1,200_000), y=np.random.normal(0,1,200_000))
counts = df.count(binby=[df.x, df.y], limits=[[-4,4],[-4,4]], shape=(100,100))
fig = go.Figure(data=go.Heatmap(z=np.log1p(counts.T), x=np.linspace(-4,4,100),
    y=np.linspace(-4,4,100), colorscale='Viridis'))
fig.update_layout(title='Vaex + Plotly', width=700, height=600)
fig.write_html('plotly_heatmap.html')
```

## Seaborn Styling and Saving Figures

```python
import vaex, numpy as np, matplotlib.pyplot as plt
import seaborn as sns

df = vaex.from_arrays(x=np.random.normal(0,1,100_000), y=np.random.normal(0,1,100_000),
                       group=np.random.choice(['A','B'], 100_000))
sns.set_theme(style='whitegrid', palette='Set2', font_scale=1.2)

fig, axes = plt.subplots(1, 2, figsize=(14, 5))
df.select(df.group == 'A', name='a'); df.select(df.group == 'B', name='b')
df.plot1d(df.x, selection='a', label='A', ax=axes[0], show=False)
df.plot1d(df.x, selection='b', label='B', ax=axes[0], show=False)
axes[0].legend(); axes[0].set_title('By Group')
df.plot(df.x, df.y, f='log', limits='99.7%', shape=(128,128), colormap='mako', ax=axes[1], show=False)
plt.tight_layout()

# Save in multiple formats
plt.savefig('plot.png', dpi=300, bbox_inches='tight', facecolor='white')  # Raster
plt.savefig('plot.pdf', bbox_inches='tight')  # Vector, publications
plt.savefig('plot.svg', bbox_inches='tight')  # Vector, web/Illustrator
plt.close(); sns.reset_defaults()
```

## EDA and Group Comparison Patterns

```python
import vaex, numpy as np, matplotlib.pyplot as plt

# --- Multi-panel EDA ---
df = vaex.from_arrays(a=np.random.lognormal(2,1,200_000), b=np.random.normal(50,15,200_000),
    c=np.random.exponential(10,200_000), label=np.random.choice(['Pos','Neg'], 200_000))

fig, axes = plt.subplots(2, 3, figsize=(20, 12))
df.plot1d(df.a, limits=[0,50], shape=80, ax=axes[0,0], show=False); axes[0,0].set_title('A')
df.plot1d(df.b, limits=[0,100], shape=80, ax=axes[0,1], show=False); axes[0,1].set_title('B')
df.plot1d(df.c, limits=[0,50], shape=80, ax=axes[0,2], show=False); axes[0,2].set_title('C')
df.plot(df.a, df.b, f='log', limits='99%', shape=(80,80), ax=axes[1,0], show=False)
df.plot(df.b, df.c, f='log', limits='99%', shape=(80,80), ax=axes[1,1], show=False)
df.select(df.label=='Pos', name='pos'); df.select(df.label=='Neg', name='neg')
df.plot1d(df.a, selection='pos', limits=[0,50], label='Pos', ax=axes[1,2], show=False)
df.plot1d(df.a, selection='neg', limits=[0,50], label='Neg', ax=axes[1,2], show=False)
axes[1,2].legend()
plt.tight_layout(); plt.savefig('eda_panel.png', dpi=150, bbox_inches='tight'); plt.close()

# --- Group comparison with summary statistics ---
groups = np.random.choice(['Control','Treatment_A','Treatment_B'], 150_000)
df2 = vaex.from_arrays(val=np.where(groups=='Control', np.random.normal(50,10,150_000),
    np.where(groups=='Treatment_A', np.random.normal(55,12,150_000),
             np.random.normal(60,8,150_000))), group=groups)

fig, axes = plt.subplots(1, 2, figsize=(16, 6))
colors = ['#1f77b4','#ff7f0e','#2ca02c']
ugroups = sorted(df2.group.unique())
for g, c in zip(ugroups, colors):
    df2.select(df2.group == g, name=g)
    df2.plot1d(df2.val, selection=g, limits=[10,100], shape=60,
              label=f'{g} (mean={df2.val.mean(selection=g):.1f})', ax=axes[0], show=False)
axes[0].legend(); axes[0].set_title('Distributions')
means = [df2.val.mean(selection=g) for g in ugroups]
stds = [df2.val.std(selection=g) for g in ugroups]
axes[1].bar(range(3), means, yerr=stds, color=colors, alpha=0.8, capsize=5)
axes[1].set_xticks(range(3)); axes[1].set_xticklabels(ugroups)
axes[1].set_title('Group Means +/- Std')
plt.tight_layout(); plt.savefig('group_comparison.png', dpi=150, bbox_inches='tight'); plt.close()
```

---

Condensed from machine_learning.md (729 lines) + visualization.md (614 lines) = 1,343 lines. Retained: advanced scalers (MinMaxScaler, MaxAbsScaler, RobustScaler), advanced encoders (FrequencyEncoder, TargetEncoder, WeightOfEvidenceEncoder), CycleTransformer, Discretizer, RandomProjection, KMeans clustering, external library integration (XGBoost, LightGBM, CatBoost, Keras/TensorFlow), cross-validation K-fold pattern, feature selection (correlation-based, variance-based), imbalanced data handling (class weights, undersampling, oversampling), end-to-end classification pipeline, feature engineering pipeline, advanced color scales and resolution control, multiple statistics subplots, faceted plots, interactive Jupyter widgets, contour plots, vector field overlay, batch plotting, Plotly integration, seaborn styling, EDA multi-panel pattern, group comparison, saving figures. Omitted from machine_learning.md: model evaluation metrics section (standard sklearn metrics, not vaex-specific -- use scikit-learn directly); "Related Resources" cross-links (superseded by SKILL.md Related Skills section). Omitted from visualization.md: "Related Resources" cross-links (superseded by SKILL.md Related Skills section). Relocated to SKILL.md: StandardScaler basic usage, LabelEncoder basic usage, OneHotEncoder basic usage, PCA basic usage, scikit-learn Predictor wrapper (vaex.ml.sklearn.Predictor), basic plot1d (1D histogram), basic plot (2D heatmap with f='log', limits, what=), selection-based visualization.
