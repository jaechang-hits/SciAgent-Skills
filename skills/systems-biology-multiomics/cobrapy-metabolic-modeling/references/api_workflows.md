# COBRApy — API Reference & Advanced Workflows

## 1. Detailed API Signatures

### flux_variability_analysis

```python
from cobra.flux_analysis import flux_variability_analysis
fva_result = flux_variability_analysis(
    model,                        # cobra.Model
    reaction_list=None,           # list[Reaction|str] — subset (default: all)
    fraction_of_optimum=1.0,      # float — min fraction of optimal objective (0.0-1.0)
    loopless=False,               # bool — eliminate thermodynamically infeasible loops (slower)
    pfba_factor=None,             # float — pFBA constraint: total flux <= pfba_factor * min_total_flux
    processes=1,                  # int — parallel workers
)
# Returns: pd.DataFrame ["minimum", "maximum"], indexed by reaction ID
```

### single_gene_deletion / double_gene_deletion

```python
from cobra.flux_analysis import single_gene_deletion, double_gene_deletion
single_results = single_gene_deletion(
    model,
    gene_list=None,               # list[Gene|str] — genes to test (default: all)
    method="fba",                 # "fba", "moma", or "room"
    processes=1,
)
# Returns: pd.DataFrame ["ids" (frozenset), "growth" (NaN if infeasible), "status"]
double_results = double_gene_deletion(
    model,
    gene_list1=None,              # first gene set (default: all)
    gene_list2=None,              # second gene set (default: gene_list1)
    method="fba", processes=1,    # recommended: 4+ processes for double deletions
)
```

### sample

```python
from cobra.sampling import sample
samples = sample(
    model, n,                     # int — number of samples
    method="optgp",               # "optgp" (parallel, recommended) or "achr" (serial)
    thinning=100,                 # steps between kept samples (higher = less correlated)
    processes=1,                  # parallel workers (optgp only)
    seed=None,                    # random seed for reproducibility
)
# Returns: pd.DataFrame (n, n_reactions)
```

### minimal_medium

```python
from cobra.medium import minimal_medium
min_med = minimal_medium(
    model,
    min_objective_value=None,     # float — minimum growth (default: current objective)
    minimize_components=False,    # True = fewest nutrients (MILP); False = min total flux (LP)
    open_exchanges=False,         # open all exchange bounds as candidates
    exports=False,                # include secretion reactions in result
)
# Returns: pd.Series — exchange reaction IDs -> flux values
```

### production_envelope

```python
from cobra.flux_analysis import production_envelope
envelope = production_envelope(
    model,
    reactions,                    # Reaction | list[Reaction] — target production reaction(s)
    objective=None,               # objective to vary (default: model.objective)
    carbon_sources=None,          # Reaction — for carbon yield calculation
    points=20,                    # grid points along objective axis
    threshold=None,               # minimum objective value fraction
)
# Returns: pd.DataFrame [flux_minimum, flux_maximum, carbon_yield_minimum, carbon_yield_maximum]
```

### gapfill

```python
from cobra.flux_analysis.gapfilling import gapfill
results = gapfill(
    model,                        # incomplete model
    universal=None,               # cobra.Model — universal reaction database
    lower_bound=0.05,             # minimum growth gapfilled model must achieve
    penalties=None,               # dict {reaction_id: cost} for weighted gapfilling
    demand_reactions=True,        # add demand reactions for all metabolites
    exchange_reactions=False,     # add exchange reactions for all metabolites
    iterations=1,                 # number of alternative solutions
)
# Returns: list[list[Reaction]]; iterations > 1 penalizes previous solutions
```

## 2. Solver Configuration

| Solver | License | Speed | MILP | Install |
|--------|---------|-------|------|---------|
| GLPK | Open source | Baseline | Yes (slower) | Bundled with `cobra` |
| CPLEX | Commercial (free academic) | 5-10x | Excellent | `pip install cplex` |
| Gurobi | Commercial (free academic) | 5-10x | Excellent | `pip install gurobipy` |

```python
from cobra.io import load_model
model = load_model("textbook")
print(f"Solver: {model.solver.interface.__name__}")  # e.g., "optlang.glpk_interface"

model.solver = "glpk"  # or "cplex", "gurobi" (requires package + license)
model.solver.configuration.tolerances.feasibility = 1e-9
model.solver.configuration.tolerances.optimality = 1e-9
model.solver.configuration.timeout = 300  # seconds
model.solver.configuration.verbosity = 0  # 0=silent, 1=errors, 2=normal, 3=verbose
# For MILP (loopless FVA, minimize_components, gapfilling): CPLEX/Gurobi recommended
```

## 3. Advanced Analysis Functions

### find_blocked_reactions

```python
from cobra.io import load_model
from cobra.flux_analysis import find_blocked_reactions
model = load_model("textbook")
blocked = find_blocked_reactions(model, reaction_list=None, zero_cutoff=1e-9,
                                 open_exchanges=False, processes=1)
print(f"Blocked: {len(blocked)} / {len(model.reactions)}")
# open_exchanges=True: checks if reactions CAN carry flux with unlimited nutrients
blocked_open = find_blocked_reactions(model, open_exchanges=True)
print(f"Blocked (open exchanges): {len(blocked_open)}")
```

### find_essential_genes / find_essential_reactions

```python
from cobra.io import load_model
from cobra.flux_analysis import find_essential_genes, find_essential_reactions
model = load_model("textbook")
ess_genes = find_essential_genes(model, threshold=None)  # default: model.tolerance
ess_rxns = find_essential_reactions(model, threshold=None)
print(f"Essential genes: {len(ess_genes)}/{len(model.genes)}, reactions: {len(ess_rxns)}/{len(model.reactions)}")
```

### Model Summary Methods

```python
from cobra.io import load_model
model = load_model("textbook")
model.optimize()
print(model.summary())                                    # uptake/secretion fluxes
print(model.metabolites.get_by_id("atp_c").summary())     # production/consumption
print(model.reactions.get_by_id("PFK").summary())          # flux and reduced cost
```

## 4. Model Building from Scratch

```python
import cobra
model = cobra.Model("custom_model")

A_c = cobra.Metabolite("A_c", name="Metabolite A", compartment="c", formula="C6H12O6")
B_c = cobra.Metabolite("B_c", name="Metabolite B", compartment="c", formula="C3H6O3")
A_e = cobra.Metabolite("A_e", name="Metabolite A (extracellular)", compartment="e")

rxn1 = cobra.Reaction("R1")
rxn1.name = "A to B conversion"
rxn1.bounds = (0.0, 1000.0)
rxn1.add_metabolites({A_c: -1.0, B_c: 2.0})  # negative = consumed, positive = produced
rxn1.gene_reaction_rule = "(gene1 and gene2) or gene3"

transport = cobra.Reaction("T_A")
transport.add_metabolites({A_e: -1.0, A_c: 1.0})
transport.bounds = (0.0, 1000.0)

exchange = cobra.Reaction("EX_A_e")
exchange.add_metabolites({A_e: -1.0})
exchange.bounds = (-10.0, 1000.0)  # uptake up to 10

model.add_reactions([rxn1, transport, exchange])
model.objective = "R1"
print(f"{len(model.reactions)} rxns, {len(model.metabolites)} mets, {len(model.genes)} genes")
sol = model.optimize()
print(f"Objective: {sol.objective_value:.4f}, Status: {sol.status}")
```

## 5. Flux Sample Validation

```python
from cobra.io import load_model
from cobra.sampling import OptGPSampler
model = load_model("textbook")
sampler = OptGPSampler(model, processes=1, seed=42)
samples = sampler.sample(500, fluxes=True)
validity = sampler.validate(samples)  # boolean array, one per sample
n_valid = validity.sum() if hasattr(validity, 'sum') else sum(validity)
print(f"Valid: {n_valid}/{len(samples)}")
if n_valid < len(samples):
    valid_samples = samples[validity]  # filter; increase thinning if many invalid
```

## 6. Extended Workflows

### Workflow A: Production Strain Design with Iteration

```python
from cobra.io import load_model
from cobra.flux_analysis import production_envelope, flux_variability_analysis
import pandas as pd

model = load_model("textbook")
target_rxn, wt_growth = "EX_ac_e", model.slim_optimize()
wt_env = production_envelope(model, reactions=model.reactions.get_by_id(target_rxn),
                              carbon_sources=model.reactions.get_by_id("EX_glc__D_e"))
print(f"WT max acetate: {wt_env['flux_maximum'].max():.4f}")

# Screen knockouts for overproducers
results = []
for gene in model.genes:
    with model:
        gene.knock_out()
        growth = model.slim_optimize()
        if growth > 0.01 * wt_growth:
            model.objective = target_rxn
            results.append({"gene": gene.id, "growth_frac": growth/wt_growth,
                            "target_flux": model.slim_optimize()})
ko_df = pd.DataFrame(results).sort_values("target_flux", ascending=False)
print(ko_df.head(5).to_string(index=False))

# Combine top knockouts and validate
with model:
    for gid in ko_df.head(3)["gene"].tolist():
        model.genes.get_by_id(gid).knock_out()
    growth = model.slim_optimize()
    print(f"Combined KO growth: {growth:.4f} (WT: {wt_growth:.4f})")
    if growth > 0.01:
        ko_env = production_envelope(model, reactions=model.reactions.get_by_id(target_rxn),
                                      carbon_sources=model.reactions.get_by_id("EX_glc__D_e"))
        fva = flux_variability_analysis(model, reaction_list=[target_rxn])
        print(f"KO acetate: max={ko_env['flux_maximum'].max():.4f}, "
              f"FVA=[{fva.loc[target_rxn,'minimum']:.4f}, {fva.loc[target_rxn,'maximum']:.4f}]")
```

### Workflow B: Multi-Condition Flux Comparison

```python
from cobra.io import load_model
from cobra.flux_analysis import flux_variability_analysis
from cobra.sampling import sample
import pandas as pd

model = load_model("textbook")
conditions = {"Aerobic": {"EX_glc__D_e": 10, "EX_o2_e": 1000},
              "Anaerobic": {"EX_glc__D_e": 10, "EX_o2_e": 0},
              "Low_glc": {"EX_glc__D_e": 1, "EX_o2_e": 1000}}
key_rxns = ["PFK", "PYK", "CS", "ATPM", "EX_ac_e", "EX_co2_e"]
rows = []
for cond, overrides in conditions.items():
    with model:
        medium = model.medium
        medium.update(overrides)
        model.medium = medium
        sol = model.optimize()
        fva = flux_variability_analysis(model, reaction_list=key_rxns, fraction_of_optimum=0.95)
        samp = sample(model, n=200, method="optgp", seed=42)
        for rid in key_rxns:
            rows.append({"condition": cond, "reaction": rid, "fba": round(sol.fluxes[rid], 3),
                         "fva_range": f"[{fva.loc[rid,'minimum']:.1f},{fva.loc[rid,'maximum']:.1f}]",
                         "sample_mean": round(samp[rid].mean(), 3)})
print(pd.DataFrame(rows).pivot_table(index="reaction", columns="condition", values="fba").to_string())
```

### Workflow C: Model Debugging and Validation Pipeline

```python
from cobra.io import load_model
from cobra.flux_analysis import (find_blocked_reactions, find_essential_genes,
                                  find_essential_reactions, flux_variability_analysis)
model = load_model("textbook")
growth = model.slim_optimize()
print(f"=== {model.id} === Growth: {growth:.4f}")

dead_ends = sum(1 for m in model.metabolites if len(m.reactions) == 1)
no_formula = sum(1 for m in model.metabolites if not m.formula)
no_gpr = sum(1 for r in model.reactions if not r.gene_reaction_rule and not r.id.startswith("EX_"))
print(f"Dead-end mets: {dead_ends}, No formula: {no_formula}, No GPR: {no_gpr}")

blocked = find_blocked_reactions(model)
ess_g, ess_r = find_essential_genes(model), find_essential_reactions(model)
print(f"Blocked: {len(blocked)}/{len(model.reactions)}, Essential genes: {len(ess_g)}, rxns: {len(ess_r)}")

fva = flux_variability_analysis(model, fraction_of_optimum=1.0)
fva["range"] = fva["maximum"] - fva["minimum"]
print(f"Fixed-flux: {(fva['range']<1e-6).sum()}, Flexible(>10): {(fva['range']>10).sum()}")

unbalanced = [(r.id, r.check_mass_balance()) for r in model.reactions
              if not r.boundary and r.check_mass_balance()]
print(f"Mass-unbalanced: {len(unbalanced)}")
```

## 7. Advanced Model Manipulation

### Changing GPR Rules

```python
from cobra.io import load_model
model = load_model("textbook")
rxn = model.reactions.get_by_id("PFK")
print(f"Original GPR: {rxn.gene_reaction_rule}")
with model:
    rxn.gene_reaction_rule = "(b0726 and b0727) or b9999"  # b9999 auto-added to model.genes
    print(f"Modified GPR: {rxn.gene_reaction_rule}, Genes: {len(model.genes)}")
```

### Stoichiometry Matrix Access

```python
from cobra.io import load_model
from cobra.util.array import create_stoichiometric_matrix
import numpy as np
model = load_model("textbook")
S = create_stoichiometric_matrix(model, array_type="dense")  # (n_mets, n_rxns)
print(f"Shape: {S.shape}, Sparsity: {1 - np.count_nonzero(S)/S.size:.2%}")
S_sparse = create_stoichiometric_matrix(model, array_type="lil")  # for large models
# Row i -> model.metabolites[i].id, Column j -> model.reactions[j].id
```

### Adding and Removing Compartments

```python
from cobra.io import load_model
import cobra
model = load_model("textbook")
model.compartments["p"] = "periplasm"
X_p = cobra.Metabolite("X_p", name="Metabolite X", compartment="p")
X_c = cobra.Metabolite("X_c", compartment="c")
transport = cobra.Reaction("T_X_cp")
transport.add_metabolites({X_c: -1.0, X_p: 1.0})
transport.bounds = (-1000.0, 1000.0)
model.add_reactions([transport])
print(f"Compartments: {model.compartments}")
model.remove_reactions([transport], remove_orphans=True)  # clean up orphan metabolites
```

*Condensed from api_quick_reference.md (655 lines) and workflows.md (593 lines) — 1,248 total. Retained: detailed function signatures with all parameters (pfba_factor, method="moma"/"room", seed, exports, iterations, penalties), solver configuration (GLPK/CPLEX/Gurobi switching, optlang tolerances/timeout/verbosity), advanced analysis (find_blocked_reactions with open_exchanges, find_essential_genes/reactions, model summaries), model building from scratch, flux sample validation via OptGPSampler.validate(), production strain design with knockout iteration, multi-condition flux comparison (FBA+FVA+sampling), model debugging pipeline (structural+blocked+essential+mass balance), GPR manipulation, stoichiometry matrix access, compartment management. Omitted: geometric FBA internals — specialized algorithm rarely needed; MIP gap configuration — solver-specific advanced tuning, consult solver docs; redundant basic examples already covered in SKILL.md Core API. Relocated to SKILL.md: basic FBA/FVA/deletion/sampling/media/gapfill usage, DictList/GPR/exchange concepts, 3 core workflows, validation checklist.*
