---
name: cobrapy-metabolic-modeling
description: "Constraint-based reconstruction and analysis (COBRA) of genome-scale metabolic models. FBA, FVA, gene/reaction knockouts, flux sampling, production envelopes, gapfilling, and media optimization. Use for metabolic engineering strain design, essential gene identification, and flux distribution analysis. For kinetic modeling use tellurium; for pathway visualization use Escher."
license: GPL-2.0
---

# COBRApy — Constraint-Based Metabolic Modeling

## Overview

COBRApy is a Python package for constraint-based reconstruction and analysis (COBRA) of genome-scale metabolic models. It provides flux balance analysis (FBA), flux variability analysis (FVA), gene and reaction knockout screens, flux sampling, production envelopes, gapfilling, and media optimization on SBML-format metabolic networks.

## When to Use

- Predicting microbial growth rates under different nutrient conditions (FBA)
- Identifying essential genes or reactions via single and double knockout screens
- Determining flux ranges and alternative optimal solutions (FVA)
- Sampling feasible flux distributions to characterize metabolic flexibility
- Designing minimal growth media or optimizing carbon sources
- Computing production envelopes for metabolic engineering targets
- Gapfilling incomplete draft models using a universal reaction database
- For **kinetic modeling** or **dynamic ODE-based models**, use Tellurium instead
- For **pathway visualization** on metabolic maps, use Escher instead

## Prerequisites

- **Python packages**: `cobra` (includes GLPK solver), `numpy`, `pandas`
- **Optional solvers**: CPLEX or Gurobi (faster for large models, require license)
- **Data**: SBML (.xml), JSON, or YAML metabolic model files; available from BiGG Models, AGORA, or ModelSEED

```bash
pip install cobra
```

## Quick Start

```python
from cobra.io import load_model

model = load_model("textbook")  # E. coli core model
print(f"Model: {model.id} — {len(model.reactions)} rxns, {len(model.metabolites)} mets, {len(model.genes)} genes")

solution = model.optimize()
print(f"Growth rate: {solution.objective_value:.4f} /h")
print(f"Status: {solution.status}")
# Model: e_coli_core — 95 rxns, 72 mets, 137 genes
# Growth rate: 0.8739 /h
# Status: optimal
```

## Core API

### 1. Model I/O

Load bundled models and read/write standard formats.

```python
from cobra.io import load_model, read_sbml_model, write_sbml_model, load_json_model, save_json_model

# Bundled: "textbook" (95 rxns), "ecoli" (2583 rxns), "salmonella"
model = load_model("textbook")
# model = read_sbml_model("my_model.xml")   # from SBML file
# model = load_json_model("my_model.json")  # from JSON file

write_sbml_model(model, "output_model.xml")
save_json_model(model, "output_model.json")
print(f"Saved model: {model.id}")
```

### 2. Model Structure and Components

Access reactions, metabolites, and genes via DictList containers.

```python
from cobra.io import load_model
model = load_model("textbook")

# Inspect a reaction
rxn = model.reactions.get_by_id("PFK")
print(f"Reaction: {rxn.id} — {rxn.name}")
print(f"Equation: {rxn.reaction}")
print(f"Bounds: {rxn.bounds}, GPR: {rxn.gene_reaction_rule}")

# Inspect a metabolite
met = model.metabolites.get_by_id("atp_c")
print(f"Metabolite: {met.id}, Formula: {met.formula}, Compartment: {met.compartment}")

# Query and list exchange reactions
atp_rxns = model.reactions.query("atp", attribute="name")
print(f"ATP-related reactions: {len(atp_rxns)}, Exchange reactions: {len(model.exchanges)}")
```

### 3. Flux Balance Analysis (FBA)

Predict optimal flux distributions by maximizing an objective.

```python
from cobra.io import load_model
from cobra.flux_analysis import pfba

model = load_model("textbook")

# Standard FBA
solution = model.optimize()
print(f"Growth: {solution.objective_value:.4f} /h, Active fluxes: {(solution.fluxes.abs() > 1e-6).sum()}")

# Parsimonious FBA — same growth, minimal total flux
pfba_sol = pfba(model)
print(f"pFBA total flux: {pfba_sol.fluxes.abs().sum():.1f} vs standard: {solution.fluxes.abs().sum():.1f}")
```

```python
# Change objective; slim_optimize for speed
from cobra.io import load_model
model = load_model("textbook")

with model:
    model.objective = "ATPM"
    print(f"Max ATPM flux: {model.optimize().objective_value:.2f}")

print(f"Growth (slim): {model.slim_optimize():.4f}")  # no flux vector, faster
```

### 4. Flux Variability Analysis (FVA)

Determine feasible flux ranges at or near optimality.

```python
from cobra.io import load_model
from cobra.flux_analysis import flux_variability_analysis

model = load_model("textbook")

fva = flux_variability_analysis(model, fraction_of_optimum=1.0)
fva_90 = flux_variability_analysis(model, fraction_of_optimum=0.9)
fva["range"] = fva["maximum"] - fva["minimum"]
fva_90["range"] = fva_90["maximum"] - fva_90["minimum"]
print(f"Mean range at 100%: {fva['range'].mean():.2f}, at 90%: {fva_90['range'].mean():.2f}")
```

```python
# Loopless FVA on specific reactions
from cobra.io import load_model
from cobra.flux_analysis import flux_variability_analysis

model = load_model("textbook")
fva_ll = flux_variability_analysis(
    model, loopless=True, reaction_list=["PFK", "PGI", "FBA", "TPI", "GAPD"],
)
print(fva_ll)
```

### 5. Gene and Reaction Deletions

Screen for essential genes/reactions via knockout simulations.

```python
from cobra.io import load_model
from cobra.flux_analysis import single_gene_deletion, double_gene_deletion

model = load_model("textbook")
wt_growth = model.slim_optimize()

# Single gene deletions
gene_results = single_gene_deletion(model)
gene_results["growth_fraction"] = gene_results["growth"] / wt_growth
essential = gene_results[gene_results["growth_fraction"] < 0.01]
print(f"Essential genes: {len(essential)} / {len(model.genes)}")

# Double deletions (synthetic lethality) — use multiprocessing
double_results = double_gene_deletion(model, processes=4)
print(f"Double deletion results: {double_results.shape}")
```

### 6. Growth Media and Minimal Media

Modify nutrient availability and compute minimal media.

```python
from cobra.io import load_model
from cobra.medium import minimal_medium

model = load_model("textbook")

# View current medium
for rxn_id, flux in sorted(model.medium.items()):
    print(f"  {rxn_id}: {flux}")

# Anaerobic switch via context manager
with model:
    medium = model.medium
    medium["EX_o2_e"] = 0.0
    model.medium = medium
    print(f"Anaerobic growth: {model.slim_optimize():.4f} /h")

# Minimal medium
min_med = minimal_medium(model, minimize_components=True, open_exchanges=True)
print(f"Minimal medium: {len(min_med)} components")
```

### 7. Flux Sampling

Sample feasible flux distributions for variability analysis.

```python
from cobra.io import load_model
from cobra.sampling import sample

model = load_model("textbook")
samples = sample(model, n=500, method="optgp")
print(f"Samples shape: {samples.shape}")  # (500, n_reactions)
print(f"PFK flux: mean={samples['PFK'].mean():.2f}, std={samples['PFK'].std():.2f}")
```

### 8. Production Envelopes and Gapfilling

Compute phenotype phase planes and fill model gaps.

```python
from cobra.io import load_model
from cobra.flux_analysis import production_envelope

model = load_model("textbook")
envelope = production_envelope(
    model,
    reactions=model.reactions.get_by_id("EX_ac_e"),
    carbon_sources=model.reactions.get_by_id("EX_glc__D_e"),
)
print(f"Envelope: {len(envelope)} points")
print(envelope[["flux_minimum", "flux_maximum", "carbon_yield_minimum", "carbon_yield_maximum"]].head())
```

```python
# Gapfilling: restore growth after reaction removal
from cobra.io import load_model
from cobra.flux_analysis.gapfilling import gapfill

model = load_model("textbook")
universal = load_model("textbook")  # In practice, use a universal reaction DB
with model:
    model.remove_reactions([model.reactions.get_by_id("PFK")])
    print(f"Growth after removing PFK: {model.slim_optimize():.4f}")
    for rxn in gapfill(model, universal)[0]:
        print(f"  Gapfill suggests: {rxn.id}")
```

## Key Concepts

### DictList Objects

Reactions, metabolites, and genes are stored in `DictList` — ordered, indexable, and accessible by ID.

```python
rxn = model.reactions[0]                    # by index
rxn = model.reactions.get_by_id("PFK")      # by ID
matches = model.reactions.query("phospho")  # keyword search
```

### Exchange Reactions

`EX_` prefix reactions represent system boundary. Positive flux = secretion; negative = uptake. Managed via `model.medium` dict.

### Gene-Reaction Rules (GPR)

Boolean expressions linking genes to reactions: `(b0726 and b0727) or b1234`. Gene knockout propagates through GPR logic.

### Context Managers

`with model:` snapshots state and reverts all changes on exit (bounds, objective, medium, knockouts). Nesting supported.

## Common Workflows

### Workflow 1: Gene Knockout Screen

**Goal**: Identify essential, growth-reducing, and neutral genes.

```python
from cobra.io import load_model
from cobra.flux_analysis import single_gene_deletion

model = load_model("textbook")
wt_growth = model.slim_optimize()

results = single_gene_deletion(model)
results["growth_fraction"] = results["growth"] / wt_growth

essential = results[results["growth_fraction"] < 0.01]
reduced = results[(results["growth_fraction"] >= 0.01) & (results["growth_fraction"] < 0.9)]
neutral = results[results["growth_fraction"] >= 0.9]

print(f"Essential: {len(essential)}, Reduced: {len(reduced)}, Neutral: {len(neutral)}")
for idx in essential.index:
    print(f"  Essential gene: {list(idx)[0]}")
```

### Workflow 2: Media Optimization

**Goal**: Find minimal medium at different growth targets; compare aerobic vs anaerobic.

```python
from cobra.io import load_model
from cobra.medium import minimal_medium
import pandas as pd

model = load_model("textbook")
results = []
for frac in [0.1, 0.5, 0.8, 1.0]:
    with model:
        target = model.slim_optimize() * frac
        model.reactions.get_by_id("Biomass_Ecoli_core").lower_bound = target
        try:
            mm = minimal_medium(model, minimize_components=True, open_exchanges=True)
            results.append({"growth_frac": frac, "n_components": len(mm)})
        except Exception:
            results.append({"growth_frac": frac, "n_components": None})
print(pd.DataFrame(results).to_string(index=False))

for label, o2 in [("Aerobic", 1000.0), ("Anaerobic", 0.0)]:
    with model:
        medium = model.medium
        medium["EX_o2_e"] = o2
        model.medium = medium
        print(f"{label} growth: {model.slim_optimize():.4f} /h")
```

### Workflow 3: Production Strain Design

**Goal**: Design a strain with maximized target metabolite production. Combines modules 3, 5, and 8.

1. Load model and compute wild-type production envelope for target metabolite
2. Screen single gene knockouts for overproducers (filter where target secretion increases)
3. Combine top knockouts and validate with FBA under production conditions
4. Gapfill if knockouts create infeasibilities
5. Compute final production envelope and compare to wild-type

## Key Parameters

| Parameter | Module/Function | Default | Range / Options | Effect |
|-----------|----------------|---------|-----------------|--------|
| `fraction_of_optimum` | `flux_variability_analysis` | `1.0` | `0.0`-`1.0` | Fraction of max objective to maintain; lower = wider flux ranges |
| `loopless` | `flux_variability_analysis` | `False` | `True`, `False` | Eliminate thermodynamically infeasible loops; slower |
| `method` | `sample` | `"optgp"` | `"optgp"`, `"achr"` | Sampling algorithm; optgp supports parallelism |
| `n` | `sample` | required | `100`-`10000` | Number of flux samples to draw |
| `processes` | `sample`, `double_gene_deletion` | `1` | `1`-`N_cores` | Parallel worker processes |
| `minimize_components` | `minimal_medium` | `False` | `True`, `False` | True = fewest nutrients (MILP); False = minimize total flux |
| `open_exchanges` | `minimal_medium` | `False` | `True`, `False` | Allow all exchanges as nutrient candidates |
| `carbon_sources` | `production_envelope` | `None` | Reaction object | Compute carbon yield alongside flux envelope |
| `thinning` | `sample` | `100` | `1`-`1000` | Steps between kept samples; higher = less correlated |

## Best Practices

1. **Use context managers for temporary changes**: `with model:` reverts all modifications on exit.
   ```python
   with model:
       model.reactions.PFK.knock_out()
       print(model.slim_optimize())  # modified
   # model is restored here
   ```

2. **Validate with `slim_optimize()` before analysis**: Quick feasibility check before expensive operations (FVA, sampling).

3. **Check `solution.status` after optimization**: Always verify `"optimal"` before interpreting fluxes.

4. **Use loopless FVA when thermodynamic feasibility matters**: Standard FVA can include infeasible internal cycles that inflate flux ranges.

5. **Parallelize expensive operations**: Sampling and double deletions support `processes` parameter.

6. **Prefer SBML for model exchange**: Community standard supported by all COBRA tools.

7. **Use `slim_optimize()` in loops**: Skips full flux vector construction, significantly faster for screening.

8. **Validate flux samples**: Use `sampler.validate(samples)` to check stoichiometric and bound constraints.

## Common Recipes

### Recipe: Parameter Scan (Glucose Uptake Rate)

```python
from cobra.io import load_model

model = load_model("textbook")
print("Glucose_uptake | Growth_rate")
for glc_uptake in [1, 2, 5, 10, 15, 20]:
    with model:
        model.reactions.get_by_id("EX_glc__D_e").lower_bound = -glc_uptake
        growth = model.slim_optimize()
        print(f"  {glc_uptake:>13} | {growth:.4f}")
```

### Recipe: Batch Condition Analysis

```python
from cobra.io import load_model
import pandas as pd

model = load_model("textbook")
conditions = [
    {"name": "Rich aerobic", "EX_o2_e": 1000, "EX_glc__D_e": 10},
    {"name": "Anaerobic", "EX_o2_e": 0, "EX_glc__D_e": 10},
    {"name": "Low glucose", "EX_o2_e": 1000, "EX_glc__D_e": 1},
]
results = []
for c in conditions:
    with model:
        medium = model.medium
        medium["EX_o2_e"], medium["EX_glc__D_e"] = c["EX_o2_e"], c["EX_glc__D_e"]
        model.medium = medium
        results.append({"condition": c["name"], "growth": round(model.slim_optimize(), 4)})
print(pd.DataFrame(results).to_string(index=False))
```

### Recipe: Model Validation Checklist

```python
from cobra.io import load_model
from cobra.flux_analysis import find_blocked_reactions

model = load_model("textbook")

# Feasibility, mass balance, dead-ends, blocked reactions
print(f"Growth feasible: {model.slim_optimize() > 0}")
print(f"Missing formula: {sum(1 for m in model.metabolites if m.formula is None)}")
print(f"Dead-end metabolites: {sum(1 for m in model.metabolites if len(m.reactions) == 1)}")
print(f"Blocked reactions: {len(find_blocked_reactions(model))} / {len(model.reactions)}")
```

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| `solution.status == "infeasible"` | Constraints cannot be simultaneously satisfied | Check medium has required nutrients; verify reaction bounds; use `model.medium` to restore defaults |
| `solution.status == "unbounded"` | No upper bound on fluxes | Set finite upper bounds on exchange reactions |
| Very slow optimization | Large model + default GLPK solver | Install CPLEX or Gurobi: `model.solver = "cplex"` |
| `ValueError` setting bounds | `lower_bound > upper_bound` temporarily | Set as tuple: `rxn.bounds = (new_lb, new_ub)` |
| Gene deletion returns NaN | Knockout makes model infeasible | Expected for essential genes; classify as essential |
| `IOError` reading SBML | Invalid SBML or missing namespace | Validate at sbml.org; try `cobra.io.sbml.validate_sbml_model(path)` |
| Flux samples fail validation | Numerical solver tolerance | Increase `thinning` parameter; try `method="achr"` |

## Bundled Resources

1 reference file:
- `references/api_workflows.md` — Consolidates API quick reference and advanced workflows. Covers: detailed function signatures, solver configuration (GLPK/CPLEX/Gurobi), advanced analysis (`find_blocked_reactions`, `find_essential_genes`/`find_essential_reactions`), model manipulation (adding reactions/metabolites/genes), flux sample validation, and 5 workflow examples (knockout with visualization, media design, flux space exploration, production strain design, model validation). Relocated inline: basic FBA/FVA/deletion/sampling (Core API modules 3-7). Omitted: geometric FBA internals, MIP gap configuration — consult COBRApy docs.

## Related Skills

- **escher** — interactive metabolic map visualization; use JSON models from COBRApy
- **bioservices** — retrieve models from BiGG, BioModels, or KEGG for import into COBRApy
- **networkx** — metabolic network topology analysis; export stoichiometry matrix as graph

## References

- [COBRApy documentation](https://cobrapy.readthedocs.io/) — official API reference and tutorials
- [BiGG Models](http://bigg.ucsd.edu/) — curated genome-scale metabolic model repository
- [COBRApy GitHub](https://github.com/opencobra/cobrapy) — source code and issue tracker
- Ebrahim et al. (2013) "COBRApy: COnstraints-Based Reconstruction and Analysis for Python" — [BMC Systems Biology](https://doi.org/10.1186/1752-0509-7-74)
