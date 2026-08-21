---
name: "aizynthfinder-retrosynthesis"
description: "AiZynthFinder retrosynthetic route planning (CASP) from AstraZeneca Molecular AI. Monte Carlo tree search guided by a template-based neural expansion policy recursively disconnects a target SMILES until precursors are found in a purchasable stock. Covers config.yml (v4 format), aizynthcli batch screening, the AiZynthFinder/AiZynthExpander Python API, one-step disconnections, custom stocks via smiles2stock, scorers, Retro*/breadth-first/DFPN search alternatives, and reading output.json.gz / trees.json. Use for synthesis route planning, synthesizability screening, and building-block/precursor search. For reaction barriers use neb-irc-activation-energy; for 2D reaction scheme drawing use rdkit-chemdraw-cdxml."
license: "MIT"
---

# AiZynthFinder Retrosynthesis

## Overview

AiZynthFinder performs computer-aided synthesis planning (CASP): a search algorithm — Monte Carlo tree search by default — recursively disconnects a target molecule into precursors, guided by a neural expansion policy that ranks known reaction templates. The search terminates when all precursors are found in a *stock* (a set of purchasable building blocks) or the maximum depth is reached. Output is a ranked set of reaction trees plus per-target statistics (`is_solved`, step count, precursors in/out of stock).

Version covered: **4.4.1** (Python 3.10–3.12). The v4 config format differs substantially from v2/v3 as described in the 2020 paper — never copy a config from an old blog post without translating it.

## When to Use

- Planning a synthesis route for a designed or purchased target molecule
- Screening a compound library for synthesizability before committing to make-on-demand
- Finding purchasable precursors or building blocks that lead to a scaffold
- Ranking design ideas by route length and by how many precursors fall outside a catalogue
- Enumerating the first retro step only — plausible disconnections without a full tree
- Testing whether a specific bond can be made disconnection-aware (`break_bonds`) in a route
- Comparing solve rate across two building-block catalogues for the same target set
- Use `torchdrug` instead when training a retrosynthesis model rather than running route search
- For forward reaction barriers and transition states use `neb-irc-activation-energy`; for drawing the resulting scheme use `rdkit-chemdraw-cdxml`

## Prerequisites

- **Python packages**: `aizynthfinder` (4.4.x), `rdkit`, `pandas`
- **Data requirements**: a stock file (InChIKeys), a trained expansion policy (ONNX model + template CSV), optionally a filter policy
- **Environment**: Python 3.10–3.12. Default runtime is `onnxruntime`; TensorFlow is not needed unless serving remote models or loading legacy `.hdf5` Keras models.

Check before installing — `aizynthcli`, `download_public_data`, and `smiles2stock` ship with the package and may already be on PATH inside a pixi/conda env. Inside a pixi project, invoke them as `pixi run aizynthcli ...`.

```bash
command -v aizynthcli || {
  conda create "python>=3.10,<3.13" -n aizynth-env -y
  conda activate aizynth-env
  python -m pip install "aizynthfinder[all]"
}
```

`[all]` adds molbloom (bloom-filter stocks), pymongo, route-distances (route clustering), scipy, and timeout-decorator. Drop it for a lighter install; add `[tf]` only for TF-serving or `.hdf5` models.

## Quick Start

```python
from aizynthfinder.aizynthfinder import AiZynthFinder

finder = AiZynthFinder(configfile="config.yml")
finder.stock.select("zinc")
finder.expansion_policy.select("uspto")

finder.target_smiles = "Cc1cccc(c1N(CC(=O)Nc2ccc(cc2)c3ncon3)C(=O)C4CCS(=O)(=O)CC4)C"
finder.tree_search()
finder.build_routes()                    # required before touching finder.routes

stats = finder.extract_statistics()
print(f"solved={stats['is_solved']} steps={stats['number_of_steps']} "
      f"routes={stats['number_of_routes']} time={stats['search_time']:.1f}s")
finder.routes[0]["image"].save("route_top.png")
```

## Workflow

### Step 1: Get the Models and Stock

`download_public_data` fetches the public USPTO models and the ZINC stock subset (several hundred MB, from zenodo.org and figshare.com) and writes a ready-to-use `config.yml`.

```bash
# Skip if the folder already holds the models — this is a large download.
test -f my_folder/config.yml || download_public_data my_folder

ls my_folder
# uspto_model.onnx              uspto_templates.csv.gz
# uspto_ringbreaker_model.onnx  uspto_ringbreaker_templates.csv.gz
# uspto_filter_model.onnx       zinc_stock.hdf5
# config.yml
```

### Step 2: Write or Adjust config.yml

The list short-cut means "template-based strategy, model first, templates second, defaults elsewhere". The same short-cut works for a single `filter` model path and a single `stock` file path.

```yaml
# config.yml — minimal
expansion:
  uspto:
    - uspto_model.onnx
    - uspto_templates.csv.gz
stock:
  zinc: zinc_stock.hdf5
```

```yaml
# config.yml — explicit form, the settings that matter in practice
search:
  algorithm: mcts
  algorithm_config:
    C: 1.4
    use_prior: True
    prune_cycles_in_search: True
    search_rewards: ["state score"]
  max_transforms: 6
  iteration_limit: 100
  time_limit: 120
  return_first: false
  exclude_target_from_stock: True
expansion:
  uspto:
    type: template-based
    model: uspto_model.onnx
    template: uspto_templates.csv.gz
    template_column: retro_template
    cutoff_cumulative: 0.995
    cutoff_number: 50
    use_rdchiral: True
filter:
  uspto:
    type: quick-filter
    model: uspto_filter_model.onnx
    filter_cutoff: 0.05
stock:
  zinc:
    type: inchiset
    path: zinc_stock.hdf5
post_processing:
  min_routes: 5
  max_routes: 25
  all_routes: False
```

Values can be pulled from the environment: `iteration_limit: ${ITERATION_LIMIT}`.

### Step 3: Validate the Target SMILES

An unparseable target burns the whole time limit before failing. Check first.

```python
from rdkit import Chem

smiles = "Cc1cccc(c1N(CC(=O)Nc2ccc(cc2)c3ncon3)C(=O)C4CCS(=O)(=O)CC4)C"
mol = Chem.MolFromSmiles(smiles)
assert mol is not None, f"invalid SMILES: {smiles}"
smiles = Chem.MolToSmiles(mol)           # canonicalize
print(f"{smiles}  heavy_atoms={mol.GetNumHeavyAtoms()}")
```

### Step 4: Run the Tree Search

`select()` picks which loaded policies and stocks are active. `AiZynthFinder` also accepts `configdict=<dict>` instead of a file — the cleanest way to sweep parameters without writing YAML.

```python
from aizynthfinder.aizynthfinder import AiZynthFinder

finder = AiZynthFinder(configfile="config.yml")
finder.stock.select("zinc")
finder.expansion_policy.select("uspto")
finder.filter_policy.select("uspto")     # optional; prunes implausible reactions

finder.target_smiles = smiles
search_time = finder.tree_search()
print(f"search finished in {search_time:.1f}s")
```

### Step 5: Build Routes and Read Statistics

`build_routes()` extracts reaction trees from the search graph. Nothing in `finder.routes` exists until it is called.

```python
finder.build_routes()
stats = finder.extract_statistics()

for key in ("is_solved", "number_of_steps", "number_of_routes",
            "number_of_precursors", "number_of_precursors_in_stock",
            "search_time", "first_solution_time"):
    print(f"{key:32s} {stats[key]}")

print("not in stock:", stats["precursors_not_in_stock"])
```

### Step 6: Inspect and Render Routes

`finder.routes` is a `RouteCollection`. Show two or three distinct routes, not only the top-scored one.

```python
routes = finder.routes
print(f"{len(routes)} routes, scores: {routes.scores}")

for i in range(min(3, len(routes))):
    tree = routes.reaction_trees[i]
    leafs = [m.smiles for m in tree.leafs()]
    print(f"route {i}: solved={tree.is_solved} "
          f"steps={len(list(tree.reactions()))} branched={tree.is_branched()}")
    print(f"  precursors: {leafs}")
    routes.images[i].save(f"route_{i:02d}.png")

routes.jsons[0]                          # JSON string for the top route
```

### Step 7: Batch Screen with aizynthcli

For hundreds or thousands of targets, use the CLI rather than a Python loop — `--nproc` splits the input across processes.

```bash
# One SMILES per line in smiles.txt
aizynthcli --config config.yml --smiles smiles.txt \
           --policy uspto --stocks zinc \
           --nproc 8 --checkpoint checkpoint.json.gz \
           --output output.json.gz --log_to_file
```

```python
import pandas as pd

data = pd.read_json("output.json.gz", orient="table")
print(f"solve rate: {data.is_solved.mean():.1%}  n={len(data)}")
print(data.loc[data.is_solved, "number_of_steps"].value_counts().sort_index())
print(data.loc[~data.is_solved, ["target", "precursors_not_in_stock"]].head())
```

## Key Parameters

| Parameter | Default | Range / Options | Effect |
|-----------|---------|-----------------|--------|
| `search.time_limit` | `120` | `30`–`1800` (s) | Wall-clock budget per target. Raise this first when nothing solves. |
| `search.iteration_limit` | `100` | `50`–`1000` | MCTS iterations per target; whichever of time/iterations hits first ends the search. |
| `search.max_transforms` | `6` | `3`–`10` | Maximum tree depth (longest route). Deeper searches cost quadratically more. |
| `search.return_first` | `False` | `True`/`False` | Stop at the first solved route — fast synthesizability yes/no, poor route quality. |
| `search.exclude_target_from_stock` | `True` | `True`/`False` | Keep `True` or a purchasable target returns an empty route. |
| `search.algorithm_config.C` | `1.4` | `0.5`–`3.0` | UCB exploration/exploitation balance; higher explores more disconnections. |
| `search.algorithm_config.search_rewards` | `["state score"]` | any scorer names | Scorers driving the search; pair with `search_rewards_weights` for multi-objective. |
| `expansion.cutoff_number` | `50` | `10`–`100` | Templates applied per expansion. Widens branching and slows search — tune after the time limit. |
| `expansion.cutoff_cumulative` | `0.995` | `0.95`–`0.999` | Cumulative policy probability retained before truncating the template list. |
| `expansion.template_column` | `retro_template` | column name | Must match the template file; a mismatch yields silently empty expansions. |
| `filter.filter_cutoff` | `0.05` | `0.0`–`0.5` | Feasibility threshold; raising it prunes harder and can make targets unsolvable. |
| `post_processing.max_routes` | `25` | `5`–`100` | Routes extracted after the search; `all_routes: True` returns every solved route. |

## Key Concepts

### The route score is not a quality score

The state score reflects the fraction of solved precursors and the route length. It was designed to *guide* the tree search and is largely indiscriminate about whether a route is chemically sensible. Solved routes score near 1.0, unsolved ones typically below 0.8. Never present `top_score` as a confidence or feasibility measure.

### Solve rate is set by the stock and the template library, not the algorithm

The public ZINC subset is far smaller than commercial catalogues; in the original comparison, adding Enamine building blocks found routes for 10 more compounds out of 100. Swapping USPTO for a Reaxys-derived policy changed *which* compounds solved rather than uniformly improving them. Findability tracks synthetic complexity — an unsolved target means "not found under this stock, this policy, and this budget", not "unsynthesizable".

Reference performance from the paper (100 random ChEMBL compounds, single CPU + single GPU): 55 solved, mean search time 38.7 s, mean time to first solution 7.1 s, mean 2.4 steps and 2.7 precursors.

### No conditions are predicted

Reagents, solvents, temperatures, and yields are outside scope. A predicted route is a hypothesis for a chemist to evaluate.

### Scorers

Loaded automatically: `state score`, `number of reactions`, `number of pre-cursors`, `number of pre-cursors in stock`. Also available in `aizynthfinder.context.scoring`: `average template occurrence`, `sum of prices`, `route cost`, `max transform`, `broken bonds`, `fraction in stock`, `fraction in source`, `fraction of intermediates in <stock>`, `stock availability`, `reaction class membership`, `reaction class-rank score`, `delta-SC score`, `route similarity`, plus `CombinedScorer` and `DeepSetScorer`. Scorers are addressed by their string name both in `search.algorithm_config.search_rewards` and in `post_processing.route_scorer` (which falls back to `search_rewards` when unset).

### Search algorithms

Set `search.algorithm` to a class path to replace MCTS: Retro\* (`aizynthfinder.search.retrostar.search_tree.SearchTree`), breadth-first (`aizynthfinder.search.breadth_first.search_tree.SearchTree`), DFPN (`aizynthfinder.search.dfpn.search_tree.SearchTree`).

### Choosing an entry point

| User intent | Use |
|-------------|-----|
| One or a few molecules, wants routes and images | Python API (`AiZynthFinder`) |
| Hundreds or thousands of molecules | `aizynthcli` with a SMILES file and `--nproc` |
| Interactive exploration by a chemist | `aizynthapp` (Jupyter GUI) |
| Only the first retro step | `AiZynthExpander` — far cheaper than a full tree search |

## Common Recipes

### Recipe: One-Step Disconnections Only

When to use: the user wants plausible first disconnections, not a full route to purchasable material.

```python
import pandas as pd
from aizynthfinder.aizynthfinder import AiZynthExpander

expander = AiZynthExpander(configfile="config.yml")
expander.expansion_policy.select("uspto")
expander.filter_policy.select("uspto")   # annotates feasibility only; does not prune

reactions = expander.do_expansion(smiles)

reactants = [[m.smiles for m in tup[0].reactants[0]] for tup in reactions]
metadata = pd.DataFrame([rxn.metadata for tup in reactions for rxn in tup])
print(f"{len(reactions)} disconnections; metadata fields: {list(metadata.columns)}")
print(metadata.head())   # template info, policy probability, filter feasibility
```

### Recipe: Build a Custom Stock from a Catalogue

When to use: the ZINC subset is not the catalogue you actually buy from. Stock files must hold **pre-computed InChIKeys**, not SMILES — `smiles2stock` does the conversion.

```bash
# one SMILES per line
smiles2stock --files enamine_bb.smi inhouse.smi --output my_stock.hdf5
smiles2stock --files enamine_bb.smi --output my_db --target mongo   # MongoDB target
```

```yaml
stock:
  enamine:
    type: inchiset
    path: my_stock.hdf5
  stop_criteria:
    price: 10
    counts:
      C: 10
```

`inchiset` also reads a CSV with an `inchi_key` column or a plain single-column text file. For a rule-based stock, subclass `StockQueryMixin` and implement `__contains__(self, mol)` over a `Molecule`, then point `stock: type:` at the importable class path.

### Recipe: Multiple Expansion Policies and Disconnection-Aware Search

When to use: ring-forming disconnections are being missed (add RingBreaker), or a specific bond must be broken.

```yaml
expansion:
  uspto:
    - uspto_model.onnx
    - uspto_templates.csv.gz
  ringbreaker:
    - uspto_ringbreaker_model.onnx
    - uspto_ringbreaker_templates.csv.gz
  multi_expansion_strategy:
    type: aizynthfinder.context.policy.MultiExpansionStrategy
    expansion_strategies: [uspto, ringbreaker]
    additive_expansion: True
search:
  break_bonds: [[1, 2], [3, 4]]     # atom-index pairs in the target
  break_bonds_operator: and         # "and" = all must break, "or" = any
  algorithm_config:
    search_rewards: ["state score", "broken bonds"]
```

Select it with `aizynthcli --policy multi_expansion_strategy ...`. Bond indices depend on the target's atom ordering — derive them from the canonical SMILES you actually pass in and confirm the atom map with the user.

### Recipe: Re-rank Routes and Render from a Saved Batch Run

When to use: the batch already ran, and you want a different ranking or images without re-searching.

```python
import pandas as pd
from aizynthfinder.analysis import RouteSelectionArguments
from aizynthfinder.reactiontree import ReactionTree

# Widen route extraction, then re-rank by a different scorer
finder.build_routes(RouteSelectionArguments(nmin=5, nmax=50, return_all=True))
finder.routes.compute_scores(finder.scorers["number of reactions"])
finder.routes.rescore(finder.scorers["number of pre-cursors in stock"])

# Render routes stored in a batch output file
data = pd.read_json("output.json.gz", orient="table")
for i, tree in enumerate(data.trees.values[0]):
    ReactionTree.from_dict(tree).to_image().save(f"target0_route{i:03d}.png")
```

## Expected Outputs

- `output.json.gz` — batch results, one row per target; read with `pd.read_json(..., orient="table")`. Columns: `target`, `search_time`, `first_solution_time`, `first_solution_iteration`, `number_of_nodes`, `max_transforms`, `max_children`, `number_of_routes`, `number_of_solved_routes`, `top_score`, `is_solved`, `number_of_steps`, `number_of_precursors`, `number_of_precursors_in_stock`, `precursors_in_stock`, `precursors_not_in_stock`, `precursors_availability`, `policy_used_counts`, `profiling`, `stock_info`, `top_scores`, `trees`
- `trees.json` — route trees for a single-SMILES CLI run (statistics go to the terminal)
- `checkpoint.json.gz` — processed targets, so a crashed batch resumes; `cat_aizynth_output` concatenates several output files
- `route_*.png` — rendered reaction trees from `RouteCollection.images` or `ReactionTree.to_image()`

Report `is_solved`, step count, and the precursors that fell outside stock. For a library screen report solve rate and the step-count distribution.

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| `PolicyException: number of templates does not agree with the output dimensions of the model` | Model and template file come from different releases | Re-pair them; the ringbreaker model needs ringbreaker templates |
| Templates load but every expansion is empty | Wrong `template_column` | Default is `retro_template`. CSV templates are read with `sep="\t"`, `index_col=0` — a comma-separated file parses silently wrong |
| Nothing is ever in stock | Stock file holds SMILES, not InChIKeys | Rebuild with `smiles2stock --files x.smi --output stock.hdf5` |
| Target reported solved immediately with an empty route | The target itself is in stock | Set `search.exclude_target_from_stock: True` |
| Every search hits the time limit unsolved | Budget or branching too tight/wide | Raise `time_limit`/`iteration_limit` first; then lower `cutoff_number` or `max_transforms`; `return_first: True` if any solution suffices |
| Config with top-level `policy:` / `properties:` keys fails | Pre-v4 format | Translate to `expansion:` / `filter:` / `search:` |
| `--nproc` produces fewer output files than expected | One shard failed and aborted concatenation | Check the per-process `aizynthcli*.log` files |
| `finder.routes` is empty or raises | `build_routes()` was not called | Always call `build_routes()` after `tree_search()` |
| Clustering or `distance_to` unavailable | `route-distances` missing | Install the `[all]` extra |
| `ImportError` on TensorFlow | Assuming the TF backend | Default runtime is onnxruntime; only `use_remote_models` or `.hdf5` Keras models need `[tf]` |

## References

- [AiZynthFinder documentation](https://molecularai.github.io/aizynthfinder/) — configuration, CLI, Python interface, stocks, scoring, how-to
- [MolecularAI/aizynthfinder on GitHub](https://github.com/MolecularAI/aizynthfinder) — source, releases, `plugins/` (Chemformer, disconnection-aware expansion)
- [Genheden et al. (2020), J Cheminform 12:70](https://doi.org/10.1186/s13321-020-00472-1) — original paper, algorithm and benchmark numbers
- [aizynthfinder on PyPI](https://pypi.org/project/aizynthfinder/) — versions, Python compatibility, extras
