# SHAP Theoretical Foundations

## Shapley Values from Game Theory

SHAP is grounded in Shapley values (Lloyd Shapley, 1951), originally from cooperative game theory. In the ML context: features are "players" and the model prediction is the "game payoff." Each feature's Shapley value is its fair contribution to the prediction.

**Shapley Value Formula**:

$$\phi_i = \sum_{S \subseteq F \setminus \{i\}} \frac{|S|!(|F|-|S|-1)!}{|F|!} [f(S \cup \{i\}) - f(S)]$$

Where F is the set of all features, S is a subset not including feature i, and f(S) is the expected model output given only features in S.

**Key Properties**:

1. **Efficiency (Additivity)**: SHAP values sum to the difference between prediction and baseline: `sum(φ_i) = f(x) - E[f(X)]`
2. **Symmetry**: Features with identical contributions receive identical attribution
3. **Dummy**: Irrelevant features receive zero attribution
4. **Monotonicity**: If a feature's marginal contribution increases, its Shapley value increases

## SHAP as Unified Framework

SHAP proves that Shapley values are the **unique** attribution method satisfying three desirable properties:

- **Local Accuracy**: `f(x) = φ_0 + sum(φ_i)` — explanation exactly matches prediction
- **Missingness**: Absent features have zero attribution
- **Consistency**: If a feature becomes more important in the model, its attribution doesn't decrease

This unifies several existing explanation methods as special cases:

| Method | Relationship to SHAP |
|--------|---------------------|
| **LIME** | Approximates Shapley values with suboptimal sample weighting; doesn't guarantee consistency |
| **DeepLIFT** | DeepExplainer averages DeepLIFT over multiple references to approximate Shapley values |
| **LRP** | Special case of SHAP with specific propagation rules |
| **Integrated Gradients** | Approximates SHAP for smooth models with single reference point |

## Computation Algorithms

Exact Shapley value computation is O(2^n) — intractable for many features. SHAP provides specialized algorithms:

### Tree SHAP (TreeExplainer)

Exploits tree structure for exact polynomial-time computation.

- **Complexity**: O(TLD²) where T = trees, L = max leaves, D = max depth
- **Algorithm**: Traverses each tree path, computes feature contributions using splits and weights
- **Advantage**: Exact Shapley values efficiently for all tree ensembles
- **Supports**: interventional and tree-path-dependent perturbation modes

### Kernel SHAP (KernelExplainer)

Weighted linear regression to estimate Shapley values for any model.

- **Complexity**: O(n × 2^M) but approximates with fewer samples
- **Algorithm**: Samples feature coalitions with Shapley kernel weights, fits weighted linear model
- **Advantage**: Model-agnostic — works with any prediction function
- **Trade-off**: Slower, approximate; increase `nsamples` for better accuracy

### Deep SHAP (DeepExplainer)

Combines DeepLIFT backpropagation with Shapley value sampling.

- **Complexity**: O(n × m) where m = reference samples
- **Algorithm**: Computes DeepLIFT attributions per reference, averages across references
- **Advantage**: Efficient for deep neural networks (TensorFlow, PyTorch)

### Linear SHAP (LinearExplainer)

Closed-form Shapley values for linear models.

- **Formula**: `φ_i = w_i × (x_i - E[x_i])` (independent features)
- **Complexity**: O(n) — nearly instantaneous
- **For correlated features**: Adjusts using feature covariance matrix

## Conditional Expectations

Computing f(S) — model output given only features in S — requires handling missing features:

**Interventional (Marginal) Approach**:
- Replace missing features with values from background dataset
- Assumes feature independence (may create unrealistic combinations)
- Matches causal interpretation: "what if we didn't know feature X?"

**Observational (Conditional) Approach**:
- Use conditional distribution E[f(x) | x_S = x_S*]
- Accounts for feature correlations
- More accurate for correlated features but harder to compute

TreeExplainer supports both via `feature_perturbation` parameter. KernelExplainer uses interventional by default.

## Interpreting SHAP Values

**Units**: SHAP values have the same units as model output (regression: target units; classification: log-odds or probability depending on `model_output`).

**Local vs Global**:
- Local (instance): φ_i(x) — "why did the model predict f(x) for this instance?"
- Global (dataset): E[|φ_i|] — "which features are most important overall?"
- Global importance is the aggregation of local importances, maintaining consistency

## Interaction Values

Standard SHAP captures main effects. Interaction values capture pairwise effects:

$$\phi_{i,j} = \sum_{S \subseteq F \setminus \{i,j\}} \frac{|S|!(|F|-|S|-2)!}{2(|F|-1)!} \Delta_{ij}(S)$$

- φ_{i,i}: Main effect of feature i
- φ_{i,j} (i≠j): Interaction effect between features i and j
- Relationship: φ_i = φ_{i,i} + sum_{j≠i}(φ_{i,j})
- Only practical for TreeExplainer (exponential for other explainers)

## Theoretical Limitations

1. **Computational complexity**: Exact computation is O(2^n); specialized algorithms are approximate for non-tree models
2. **Feature independence assumption**: Interventional approach creates unrealistic feature combinations for correlated features (e.g., Age=5, Has_PhD=Yes)
3. **Out-of-distribution samples**: Feature coalitions may be outside training distribution, making model behavior unreliable
4. **Causality**: SHAP measures association, not causation. "Hospital stay increases mortality prediction" ≠ "hospital stays cause mortality"
5. **Approximation quality**: Non-tree methods (Kernel, Deep, Gradient) are approximations with varying accuracy

## References

- Shapley, L. S. (1951). "A value for n-person games"
- Lundberg, S. M., & Lee, S. I. (2017). "A Unified Approach to Interpreting Model Predictions" (NeurIPS)
- Lundberg, S. M., et al. (2020). "From local explanations to global understanding with explainable AI for trees" (Nature Machine Intelligence)

Condensed from original: references/theory.md (450 lines). Omitted: full mathematical proofs, functional ANOVA decomposition, detailed sensitivity analysis connection, extended comparison with all alternative methods. Consult original or Lundberg & Lee (2017) for complete theoretical treatment.
