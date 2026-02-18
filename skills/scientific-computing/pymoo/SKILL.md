---
name: "pymoo"
description: "pymoo is a Python framework for single- and multi-objective optimization using evolutionary algorithms. Define problems as vectorized objective functions and constraints, then solve with NSGA-II, NSGA-III, MOEA/D, genetic algorithms, or differential evolution. Analyze Pareto fronts, visualize trade-off surfaces, and customize operators and callbacks. Ideal for engineering design, hyperparameter search, process optimization, and any problem with multiple conflicting objectives. Alternatives: scipy.optimize (single-objective, gradient-based), platypus (fewer algorithms), jMetalPy (Java-based, more algorithms)."
license: "Apache-2.0"
---

# pymoo

## Overview

pymoo provides a unified API for multi-objective optimization via population-based evolutionary algorithms. Users define a problem by subclassing `Problem` or `ElementwiseProblem`, specifying objectives (`n_obj`), decision variables (`n_var`), and optional constraints (`n_ieq_constr`). Algorithms like NSGA-II and NSGA-III return a `Result` object containing the Pareto-optimal population, objective values, and decision variable values. pymoo separates problem definition, algorithm configuration, operator selection, and analysis — each component is independently replaceable.

## When to Use

- Optimizing a design with two or more conflicting objectives (e.g., minimizing cost while maximizing performance)
- Running evolutionary algorithms (GA, DE, PSO) as black-box optimizers when gradients are unavailable
- Performing multi-objective hyperparameter search for ML models where accuracy and inference time trade off
- Computing Pareto fronts for portfolio optimization or multi-criteria decision analysis
- Customizing crossover/mutation operators for domain-specific solution encodings (binary, permutation, real-valued)
- Benchmarking optimization algorithms on standard test problems (ZDT, DTLZ, CTP)
- Use `scipy.optimize` instead for single-objective, gradient-available, smooth optimization

## Prerequisites

- **Python packages**: `pymoo`, `numpy`, `matplotlib`
- **Data requirements**: objective function(s) and optional constraint functions; variable bounds
- **Environment**: CPU sufficient for most problems; GPU not used by pymoo core

```bash
pip install pymoo numpy matplotlib
```

## Quick Start

```python
import numpy as np
from pymoo.core.problem import Problem
from pymoo.algorithms.moo.nsga2 import NSGA2
from pymoo.optimize import minimize

class SimpleBiObjective(Problem):
    def __init__(self):
        super().__init__(n_var=2, n_obj=2, xl=np.array([-2, -2]), xu=np.array([2, 2]))

    def _evaluate(self, X, out, *args, **kwargs):
        f1 = X[:, 0] ** 2 + X[:, 1] ** 2
        f2 = (X[:, 0] - 1) ** 2 + X[:, 1] ** 2
        out["F"] = np.column_stack([f1, f2])

algorithm = NSGA2(pop_size=100)
res = minimize(SimpleBiObjective(), algorithm, ("n_gen", 200), seed=1, verbose=False)
print(f"Pareto front size: {len(res.F)}")
print(f"Objective range: F1=[{res.F[:,0].min():.3f}, {res.F[:,0].max():.3f}]")
```

## Core API

### Module 1: Problem Definition

Define optimization problems via subclassing. Use `Problem` for vectorized evaluation (faster), `ElementwiseProblem` for scalar evaluation (simpler to write).

```python
import numpy as np
from pymoo.core.problem import Problem, ElementwiseProblem

# Vectorized problem (preferred for performance)
class ZDT1(Problem):
    """ZDT1 benchmark: 30 variables, 2 objectives, known Pareto front."""
    def __init__(self):
        super().__init__(n_var=30, n_obj=2, xl=0.0, xu=1.0)

    def _evaluate(self, X, out, *args, **kwargs):
        f1 = X[:, 0]
        g = 1 + 9 * X[:, 1:].mean(axis=1)
        f2 = g * (1 - np.sqrt(f1 / g))
        out["F"] = np.column_stack([f1, f2])

# Elementwise problem with inequality constraints
class ConstrainedProblem(ElementwiseProblem):
    def __init__(self):
        super().__init__(n_var=2, n_obj=1, n_ieq_constr=2,
                         xl=np.array([-5, -5]), xu=np.array([5, 5]))

    def _evaluate(self, x, out, *args, **kwargs):
        out["F"] = (x[0] - 1) ** 2 + (x[1] - 2) ** 2  # objective
        out["G"] = np.array([
            x[0] + x[1] - 2,   # g1 <= 0
            x[0] ** 2 - x[1],  # g2 <= 0
        ])

print(f"ZDT1: {ZDT1().n_var} vars, {ZDT1().n_obj} objectives")
```

```python
# Mixed-variable problem: some integer, some real
from pymoo.core.variable import Real, Integer, Choice

class MixedProblem(ElementwiseProblem):
    def __init__(self):
        vars = {
            "x": Real(bounds=(-2, 2)),
            "n": Integer(bounds=(1, 10)),
        }
        super().__init__(vars=vars, n_obj=1)

    def _evaluate(self, X, out, *args, **kwargs):
        x, n = X["x"], X["n"]
        out["F"] = (x - n) ** 2
```

### Module 2: Algorithm Selection

pymoo provides 20+ algorithms. Key choices by problem type:

```python
from pymoo.algorithms.moo.nsga2 import NSGA2
from pymoo.algorithms.moo.nsga3 import NSGA3
from pymoo.algorithms.moo.moead import MOEAD
from pymoo.algorithms.soo.nonconvex.ga import GA
from pymoo.algorithms.soo.nonconvex.de import DE
from pymoo.util.ref_dirs import get_reference_directions

# NSGA-II: best for 2-3 objectives, most widely used
nsga2 = NSGA2(pop_size=100)

# NSGA-III: designed for 3+ objectives; needs reference directions
ref_dirs = get_reference_directions("das-dennis", 3, n_partitions=12)  # ~91 dirs
nsga3 = NSGA3(pop_size=len(ref_dirs), ref_dirs=ref_dirs)

# MOEA/D: decomposition-based, good for many objectives
moead = MOEAD(ref_dirs=ref_dirs, n_neighbors=15, prob_neighbor_mating=0.7)

# GA: single-objective genetic algorithm
ga = GA(pop_size=100)

# DE: Differential Evolution, good for continuous problems
de = DE(pop_size=100, variant="DE/rand/1/bin", CR=0.9, F=0.8)

print("Algorithms initialized")
```

### Module 3: Operators (Crossover & Mutation)

Operators define how solutions evolve. Replace defaults to match variable type.

```python
from pymoo.operators.crossover.sbx import SBX
from pymoo.operators.mutation.pm import PM
from pymoo.operators.crossover.pntx import TwoPointCrossover
from pymoo.operators.mutation.bitflip import BitflipMutation
from pymoo.operators.sampling.rnd import FloatRandomSampling, BinaryRandomSampling

# Real-valued: Simulated Binary Crossover + Polynomial Mutation (defaults for NSGA-II)
alg_real = NSGA2(
    pop_size=100,
    sampling=FloatRandomSampling(),
    crossover=SBX(prob=0.9, eta=15),     # eta: distribution index (higher = closer to parents)
    mutation=PM(eta=20),                  # eta: higher = smaller perturbation
    eliminate_duplicates=True
)

# Binary encoding
alg_bin = GA(
    pop_size=50,
    sampling=BinaryRandomSampling(),
    crossover=TwoPointCrossover(),
    mutation=BitflipMutation(prob=0.02),
)

print("Custom operators configured")
```

### Module 4: Termination Criteria

Control when the algorithm stops.

```python
from pymoo.termination.default import DefaultMultiObjectiveTermination
from pymoo.termination import get_termination

# Simple: fixed number of generations or evaluations
term_gen = get_termination("n_gen", 500)      # stop after 500 generations
term_eval = get_termination("n_eval", 10000)  # stop after 10,000 function evaluations

# Convergence-based (recommended for multi-objective)
term_conv = DefaultMultiObjectiveTermination(
    xtol=1e-8,      # design space tolerance
    cvtol=1e-6,     # constraint violation tolerance
    ftol=0.0025,    # objective space tolerance
    period=30,      # check every 30 generations
    n_max_gen=500,  # hard limit
    n_max_evals=100_000,
)

print("Termination criteria set")
```

### Module 5: Result Analysis and Pareto Front

```python
from pymoo.optimize import minimize
import numpy as np

problem = ZDT1()
algorithm = NSGA2(pop_size=100)
res = minimize(problem, algorithm, ("n_gen", 200), seed=42, verbose=False)

# Access results
print(f"Pareto front solutions: {len(res.F)}")
print(f"Objective values (first 3):\n{res.F[:3]}")
print(f"Decision variables (first 3):\n{res.X[:3]}")
print(f"Algorithm generations: {res.algorithm.n_gen}")

# Filter for feasibility (if constraints exist)
if res.G is not None:
    feasible = (res.G <= 0).all(axis=1)
    print(f"Feasible solutions: {feasible.sum()}/{len(feasible)}")

# Performance indicators
from pymoo.indicators.hv import HV
from pymoo.indicators.igd import IGD

ref_point = np.array([1.1, 1.1])  # reference point for HV (must dominate all solutions)
hv = HV(ref_point=ref_point)
print(f"Hypervolume indicator: {hv(res.F):.4f}")
```

### Module 6: Visualization

```python
import matplotlib.pyplot as plt
from pymoo.visualization.scatter import Scatter

# Scatter plot for 2D/3D Pareto fronts
plot = Scatter(title="ZDT1 Pareto Front")
plot.add(res.F, color="blue", label="NSGA-II result")
plot.show()

# Manual matplotlib plot
fig, ax = plt.subplots(figsize=(6, 5))
ax.scatter(res.F[:, 0], res.F[:, 1], s=10, color="steelblue", alpha=0.8)
ax.set_xlabel("Objective 1 (f₁)")
ax.set_ylabel("Objective 2 (f₂)")
ax.set_title("Pareto Front — ZDT1")
plt.tight_layout()
plt.savefig("pareto_front.pdf", bbox_inches="tight")
print("Saved pareto_front.pdf")
```

```python
# Parallel Coordinate Plot for 3+ objectives
from pymoo.visualization.pcp import PCP

# Generate 3-objective result for visualization
from pymoo.problems import get_problem
dtlz2 = get_problem("dtlz2")
ref_dirs = get_reference_directions("das-dennis", 3, n_partitions=12)
res3 = minimize(dtlz2, NSGA3(pop_size=len(ref_dirs), ref_dirs=ref_dirs),
                ("n_gen", 200), seed=1)

pcp = PCP(title="DTLZ2 — 3 Objectives", labels=["f1", "f2", "f3"])
pcp.add(res3.F)
pcp.show()
```

## Key Concepts

### Pareto Dominance

Solution **a** dominates **b** if **a** is no worse than **b** on all objectives and strictly better on at least one. The Pareto front is the set of non-dominated solutions — there is no single "best" solution, only trade-offs. NSGA-II uses non-dominated sorting + crowding distance to maintain a diverse Pareto approximation.

### Constraint Handling

pymoo uses the constraint violation approach: infeasible solutions are penalized but kept in the population. A solution with constraint violation `G[i] > 0` is dominated by any feasible solution regardless of objective values. This means the algorithm first drives the population toward feasibility, then optimizes objectives.

## Common Workflows

### Workflow 1: Two-Objective Engineering Design

```python
import numpy as np
from pymoo.core.problem import Problem
from pymoo.algorithms.moo.nsga2 import NSGA2
from pymoo.optimize import minimize
import matplotlib.pyplot as plt

# Beam design: minimize weight and minimize deflection
class BeamDesign(Problem):
    """
    Variables: x[0] = width (0.1–5 cm), x[1] = height (0.5–10 cm)
    Obj 1: minimize cross-sectional area (weight proxy)
    Obj 2: minimize deflection (1/I, where I = bh³/12)
    """
    def __init__(self):
        super().__init__(n_var=2, n_obj=2,
                         xl=np.array([0.1, 0.5]),
                         xu=np.array([5.0, 10.0]))

    def _evaluate(self, X, out, *args, **kwargs):
        b, h = X[:, 0], X[:, 1]
        area = b * h                      # objective 1: area (minimize)
        I = b * h**3 / 12
        deflection = 1 / I               # objective 2: deflection (minimize)
        out["F"] = np.column_stack([area, deflection])

res = minimize(BeamDesign(), NSGA2(pop_size=100), ("n_gen", 300), seed=1)

fig, axes = plt.subplots(1, 2, figsize=(12, 5))
axes[0].scatter(res.F[:, 0], res.F[:, 1], s=15, c="steelblue")
axes[0].set_xlabel("Cross-sectional area (weight)")
axes[0].set_ylabel("Deflection (1/I)")
axes[0].set_title("Pareto Front")

axes[1].scatter(res.X[:, 0], res.X[:, 1], s=15, c="coral")
axes[1].set_xlabel("Width b (cm)")
axes[1].set_ylabel("Height h (cm)")
axes[1].set_title("Design Space")

plt.tight_layout()
plt.savefig("beam_design.pdf", bbox_inches="tight")
print(f"Pareto solutions: {len(res.F)}")
```

### Workflow 2: Algorithm Comparison with Callback

```python
import numpy as np
from pymoo.core.problem import Problem
from pymoo.algorithms.moo.nsga2 import NSGA2
from pymoo.algorithms.moo.nsga3 import NSGA3
from pymoo.optimize import minimize
from pymoo.core.callback import Callback
from pymoo.indicators.hv import HV
from pymoo.util.ref_dirs import get_reference_directions

class HVCallback(Callback):
    def __init__(self, ref_point):
        super().__init__()
        self.hv_indicator = HV(ref_point=ref_point)
        self.history = []

    def notify(self, algorithm):
        F = algorithm.opt.get("F")
        if F is not None and len(F) > 0:
            self.history.append(self.hv_indicator(F))

problem = ZDT1()
ref_point = np.array([1.1, 1.1])

results = {}
for name, alg in [("NSGA-II", NSGA2(pop_size=100))]:
    cb = HVCallback(ref_point)
    res = minimize(problem, alg, ("n_gen", 200), callback=cb, seed=42)
    results[name] = {"res": res, "hv": cb.history}
    print(f"{name}: final HV = {cb.history[-1]:.4f}")

import matplotlib.pyplot as plt
fig, ax = plt.subplots(figsize=(8, 4))
for name, data in results.items():
    ax.plot(data["hv"], label=name)
ax.set_xlabel("Generation")
ax.set_ylabel("Hypervolume")
ax.legend()
plt.tight_layout()
plt.savefig("hv_convergence.pdf", bbox_inches="tight")
```

## Key Parameters

| Parameter | Module/Class | Default | Range / Options | Effect |
|-----------|-------------|---------|-----------------|--------|
| `pop_size` | All algorithms | 100 | 50–500 | Population per generation; larger = better diversity, slower |
| `n_gen` | Termination | — | 100–5000 | Maximum generations to run |
| `eta` (crossover) | `SBX` | 15 | 5–30 | Distribution index; higher = offspring closer to parents |
| `eta` (mutation) | `PM` | 20 | 5–50 | Perturbation strength; higher = smaller mutation steps |
| `CR` | `DE` | 0.9 | 0–1 | Crossover probability in differential evolution |
| `F` | `DE` | 0.8 | 0.1–2.0 | Scaling factor for differential evolution mutation |
| `n_partitions` | `get_reference_directions` | 12 | 4–20 | Density of reference directions for NSGA-III/MOEA/D |
| `n_neighbors` | `MOEAD` | 15 | 5–30 | Neighborhood size for MOEA/D weight vector selection |
| `prob` | `SBX` | 0.9 | 0.5–1.0 | Probability of applying crossover to a pair |

## Best Practices

1. **Profile your objective function first**: pymoo calls the objective function `pop_size × n_gen` times. If one evaluation takes >1 ms, parallelize using `pymoo.core.problem.StarmapParallelization` or `dask`. Profile before optimizing.

2. **Start with NSGA-II for 2 objectives, NSGA-III for 3+**: NSGA-II is the de facto standard for biobjective problems. For 3+ objectives, crowding distance degrades — use NSGA-III with Das-Dennis reference directions or MOEA/D.

3. **Set termination based on convergence, not fixed generations**: `DefaultMultiObjectiveTermination` detects stagnation automatically. Fixed `n_gen` wastes compute if the Pareto front converges early, or terminates too soon if the problem is hard.

4. **Use vectorized `Problem` not `ElementwiseProblem` for speed**: `ElementwiseProblem` evaluates one solution at a time; `Problem` evaluates the whole population in one NumPy call. For numpy-compatible functions this is 10–100× faster.

5. **Normalize objectives before computing indicators**: Hypervolume and IGD are sensitive to objective scale. If objectives have different units (e.g., mass in kg vs. deflection in m⁻¹), normalize to [0, 1] before comparison.

## Common Recipes

### Recipe: Parallelize Expensive Objective Evaluations

```python
from multiprocessing.pool import Pool
from pymoo.core.problem import StarmapParallelization

# Wrap a slow objective function with parallel evaluation
def expensive_objective(x):
    import time; time.sleep(0.01)  # simulate slow call
    return [x[0]**2 + x[1]**2, (x[0]-1)**2 + x[1]**2]

n_workers = 4
pool = Pool(n_workers)
runner = StarmapParallelization(pool.starmap)

class ParallelProblem(Problem):
    def __init__(self, runner):
        super().__init__(n_var=2, n_obj=2, xl=-2, xu=2, elementwise=True,
                         elementwise_runner=runner)
    def _evaluate(self, x, out, *args, **kwargs):
        out["F"] = expensive_objective(x)

res = minimize(ParallelProblem(runner), NSGA2(pop_size=50), ("n_gen", 50))
pool.close()
print(f"Pareto solutions: {len(res.F)}")
```

### Recipe: Restart from Previous Population

```python
import numpy as np
from pymoo.core.population import Population

# Warm-start: use previous result's population as initial population
# Run initial optimization
res1 = minimize(ZDT1(), NSGA2(pop_size=100), ("n_gen", 100), seed=1)

# Continue from checkpoint
initial_pop = Population.new("X", res1.X)

from pymoo.algorithms.moo.nsga2 import NSGA2
alg_warmstart = NSGA2(pop_size=100, sampling=initial_pop)
res2 = minimize(ZDT1(), alg_warmstart, ("n_gen", 100), seed=1)
print(f"Continued optimization: {len(res2.F)} Pareto solutions")
```

### Recipe: Single-Objective GA with Custom Fitness

```python
from pymoo.algorithms.soo.nonconvex.ga import GA
from pymoo.core.problem import ElementwiseProblem
from pymoo.optimize import minimize

class Sphere(ElementwiseProblem):
    def __init__(self):
        super().__init__(n_var=5, n_obj=1, xl=-5.0, xu=5.0)

    def _evaluate(self, x, out, *args, **kwargs):
        out["F"] = sum(xi**2 for xi in x)

res = minimize(Sphere(), GA(pop_size=100), ("n_gen", 200), seed=42)
print(f"Best solution: f={res.F[0][0]:.6f}")
print(f"Best x: {res.X}")
```

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| Pareto front has only 1–2 solutions | `pop_size` too small or `n_gen` too few | Increase `pop_size` (≥100) and `n_gen` (≥200 for 2 objectives) |
| All solutions infeasible after many generations | Constraints too tight or initial sampling misses feasible region | Add a feasible seed solution via `sampling` parameter; relax constraints for warm-start |
| `NaN` or `inf` in objective values | Numerical instability in problem definition | Add bounds checks in `_evaluate`; use `np.clip` before division |
| `StarmapParallelization` hangs | `Pool` not closed; lambda/closure not picklable | Use `pool.close()` + `pool.join()`; define objective as module-level function |
| NSGA-III performs worse than NSGA-II on 2 objectives | NSGA-III designed for 3+ objectives; fewer selection pressures for 2D | Use NSGA-II for 2 objectives; NSGA-III for 3+ |
| Convergence stalled early | Population converged, no diversity | Increase `eta` in mutation (larger perturbations); increase `pop_size`; use `DE` instead |
| Result changes drastically between runs | High stochasticity; no seed set | Set `seed=42` in `minimize()` for reproducibility |

## Related Skills

- `scipy-optimization` — single-objective, gradient-based optimization for smooth problems
- `pymatgen` — materials property optimization using pymoo for multi-objective crystal structure search
- `scikit-learn-machine-learning` — hyperparameter tuning (use pymoo for multi-objective HPO: accuracy vs. latency)

## References

- [pymoo documentation](https://pymoo.org/) — algorithm catalog, API reference, and tutorials
- [pymoo paper: Blank & Deb (2020), IEEE Access](https://doi.org/10.1109/ACCESS.2020.2990567) — algorithm descriptions and benchmarks
- [NSGA-II paper: Deb et al. (2002), IEEE TEC](https://doi.org/10.1109/4235.996017) — foundational multi-objective EA
- [NSGA-III paper: Deb & Jain (2014), IEEE TEC](https://doi.org/10.1109/TEVC.2013.2281535) — many-objective extension
- [pymoo GitHub](https://github.com/anyoptimization/pymoo) — source, examples, and issue tracker
