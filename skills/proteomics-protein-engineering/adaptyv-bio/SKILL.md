---
name: "adaptyv-bio"
description: "Adaptyv Bio provides an API and Python SDK for ordering and managing cell-free protein expression and binding assay experiments. Use it to submit protein sequences for expression (scale 10–100 µg), characterize binding affinity (KD) against target proteins, track experiment status, and retrieve results — all programmatically without wet-lab setup. Designed for protein engineers, ML-guided directed evolution, and antibody/nanobody optimization workflows. Requires an Adaptyv Bio account and API key."
license: "MIT"
---

# Adaptyv Bio

## Overview

Adaptyv Bio is a protein expression and characterization platform accessed via a REST API and Python SDK. Users submit protein sequences (antibodies, nanobodies, enzymes, binding proteins) and receive expressed protein along with binding affinity measurements (KD via biolayer interferometry) within days. The platform is designed for high-throughput directed evolution loops: generate candidate sequences (computationally or by library design) → order expression + assay via API → receive affinity data → retrain model or select top candidates → repeat. The SDK handles experiment submission, status polling, and result retrieval in Python.

## When to Use

- Screening computationally designed protein variants for experimental binding affinity validation
- Running ML-guided directed evolution loops where in silico candidate generation alternates with wet-lab characterization
- Ordering cell-free expression of nanobodies, antibodies, or binding domains without maintaining wet-lab infrastructure
- Automating high-throughput protein characterization pipelines using the REST API
- Integrating experimental affinity data (KD values) with computational models for Bayesian optimization of protein sequences
- Validating ESM, AlphaFold, or docking predictions with experimental binding data
- Use `benchling-integration` for LIMS-style sequence and plasmid management; use Adaptyv Bio instead when you need automated cell-free expression and affinity characterization without wet-lab setup

## Prerequisites

- **Python packages**: `adaptyvbio`, `requests`, `pandas`
- **Account**: Adaptyv Bio account required; obtain API key from dashboard
- **Data requirements**: protein sequence(s) in FASTA or plain string format; target protein specification

```bash
pip install adaptyvbio requests pandas
# Set API key as environment variable
export ADAPTYV_API_KEY="your_api_key_here"
```

## Quick Start

```python
import adaptyvbio as ab
import os

# Initialize client
client = ab.Client(api_key=os.environ["ADAPTYV_API_KEY"])

# List available experiment types
experiment_types = client.get_experiment_types()
for et in experiment_types:
    print(f"  {et['name']}: {et['description']}")
```

## Core API

### Module 1: Sequence Submission

Submit protein sequences for cell-free expression and characterization.

```python
import adaptyvbio as ab
import os

client = ab.Client(api_key=os.environ["ADAPTYV_API_KEY"])

# Submit a single protein sequence for expression
sequence = "MAQRITLPSGMKELRLSYNMGEIVYKIEPVGSIVHIEYYDPENKDTLVNKPSDIVELTMPGKLVVENAKTFAEK"

submission = client.submit_experiment(
    experiment_type="expression",   # "expression" or "binding"
    sequences=[sequence],
    metadata={
        "project": "nanobody_optimization_round1",
        "designer": "ESM2_1000_candidates",
    }
)

experiment_id = submission["experiment_id"]
print(f"Submitted experiment: {experiment_id}")
print(f"Status: {submission['status']}")
print(f"Estimated completion: {submission.get('estimated_completion', 'N/A')}")
```

```python
# Submit batch of sequences (up to 96 per experiment)
import pandas as pd

# Load candidate sequences from CSV
candidates = pd.read_csv("esm_candidates.csv")  # columns: name, sequence, score
top_candidates = candidates.nlargest(48, "score")

sequences = top_candidates["sequence"].tolist()
names = top_candidates["name"].tolist()

batch_submission = client.submit_experiment(
    experiment_type="binding",
    sequences=sequences,
    sequence_names=names,
    target="target_protein_name",  # registered target in your Adaptyv account
    metadata={"round": 2, "parent_experiment": experiment_id}
)
print(f"Batch experiment: {batch_submission['experiment_id']}")
print(f"Sequences submitted: {len(sequences)}")
```

### Module 2: Experiment Status Tracking

Poll experiment status and retrieve results when complete.

```python
import adaptyvbio as ab
import os
import time

client = ab.Client(api_key=os.environ["ADAPTYV_API_KEY"])
experiment_id = "exp_abc123"  # from submission step

# Check current status
status = client.get_experiment_status(experiment_id)
print(f"Status: {status['status']}")  # "pending", "running", "complete", "failed"
print(f"Progress: {status.get('progress', 0):.0%}")

# Poll until complete (with timeout)
max_wait_hours = 72
poll_interval_minutes = 30
timeout = max_wait_hours * 3600

start = time.time()
while time.time() - start < timeout:
    status = client.get_experiment_status(experiment_id)
    print(f"[{time.strftime('%H:%M')}] Status: {status['status']}")
    if status["status"] in ("complete", "failed"):
        break
    time.sleep(poll_interval_minutes * 60)

print(f"Final status: {status['status']}")
```

### Module 3: Results Retrieval

Download and parse experiment results.

```python
import adaptyvbio as ab
import pandas as pd
import os

client = ab.Client(api_key=os.environ["ADAPTYV_API_KEY"])
experiment_id = "exp_abc123"

# Get results (only available when status is "complete")
results = client.get_experiment_results(experiment_id)

# Convert to DataFrame
records = []
for result in results["results"]:
    records.append({
        "name": result.get("sequence_name", "unnamed"),
        "sequence": result["sequence"],
        "kd_nM": result.get("kd_nM"),          # binding dissociation constant
        "yield_ug": result.get("yield_ug"),      # expression yield
        "expression_pass": result.get("expression_pass"),
        "binding_pass": result.get("binding_pass"),
    })

df = pd.DataFrame(records)
df = df.sort_values("kd_nM", ascending=True)  # rank by affinity (lower KD = tighter binding)

print(f"Results: {len(df)} sequences")
print(f"Successfully expressed: {df['expression_pass'].sum()}")
print(f"KD range: {df['kd_nM'].min():.2f} – {df['kd_nM'].max():.2f} nM")
print(df[["name", "kd_nM", "yield_ug", "expression_pass"]].head(10).to_string())

df.to_csv(f"{experiment_id}_results.csv", index=False)
```

### Module 4: Experiment History and Project Management

```python
import adaptyvbio as ab
import pandas as pd
import os

client = ab.Client(api_key=os.environ["ADAPTYV_API_KEY"])

# List all experiments
experiments = client.list_experiments(project="nanobody_optimization")
print(f"Total experiments: {len(experiments)}")

for exp in experiments:
    print(f"  {exp['experiment_id']}: {exp['status']} | "
          f"{exp['n_sequences']} seqs | {exp['created_at'][:10]}")

# Retrieve all results across experiments for a project
all_results = []
for exp in experiments:
    if exp["status"] == "complete":
        results = client.get_experiment_results(exp["experiment_id"])
        for r in results["results"]:
            r["experiment_id"] = exp["experiment_id"]
            r["round"] = exp.get("metadata", {}).get("round", "unknown")
            all_results.append(r)

project_df = pd.DataFrame(all_results)
print(f"\nAll results: {len(project_df)} sequences across {len(experiments)} experiments")
print(f"Best KD: {project_df['kd_nM'].min():.3f} nM")
```

### Module 5: Integration with Sequence Design

Integrate Adaptyv Bio results with computational protein design tools.

```python
import adaptyvbio as ab
import pandas as pd
import numpy as np
import os

client = ab.Client(api_key=os.environ["ADAPTYV_API_KEY"])

def run_design_iteration(previous_results_df, n_new_candidates=48):
    """
    Closed-loop protein engineering iteration.
    Input: DataFrame with sequence, kd_nM from previous round
    Output: submitted experiment_id for new round
    """
    # Select top performers as parents for next round
    parents = previous_results_df.nsmallest(5, "kd_nM")["sequence"].tolist()
    print(f"Top parent KDs: {previous_results_df.nsmallest(5, 'kd_nM')['kd_nM'].values}")

    # --- Placeholder for computational design step ---
    # In practice: call ESM, ProteinMPNN, or mutation scanning here
    # new_sequences = design_model.generate(parents, n=n_new_candidates)
    # For demonstration, create random variants:
    new_sequences = [p[:20] + "X" * 10 + p[30:] for p in parents[:3]]  # placeholder

    # Submit new candidates
    submission = client.submit_experiment(
        experiment_type="binding",
        sequences=new_sequences,
        metadata={"round": "auto", "parent_kd_min": parents[0] if parents else None}
    )
    print(f"Round submitted: {submission['experiment_id']}")
    return submission["experiment_id"]

# Example: load round 1 results and start round 2
round1 = pd.read_csv("exp_round1_results.csv")
if not round1.empty:
    next_id = run_design_iteration(round1)
    print(f"Round 2 experiment ID: {next_id}")
```

## Key Concepts

### KD (Dissociation Constant)

KD measures binding affinity between protein and target. Lower KD = tighter binding:
- **µM range (>1000 nM)**: weak binding, typically not useful for therapeutics
- **100–1000 nM**: moderate binding
- **1–100 nM**: good binding, typical antibody range
- **<1 nM**: excellent binding (picomolar antibodies, nanobodies)

Adaptyv Bio reports KD in nM from biolayer interferometry (BLI) steady-state or kinetic measurements.

### Cell-Free Expression

Adaptyv Bio uses cell-free protein synthesis (CFPS) systems (wheat germ or E. coli extract) to express proteins without cloning. This enables high-throughput screening (96-well format, days not weeks) but has limitations: eukaryotic modifications (glycosylation, disulfide bonds in complex proteins) may differ from cell-based expression.

## Common Workflows

### Workflow 1: Closed-Loop Directed Evolution

```python
import adaptyvbio as ab
import pandas as pd
import os
import time

client = ab.Client(api_key=os.environ["ADAPTYV_API_KEY"])

ROUNDS = 3
CANDIDATES_PER_ROUND = 48
TARGET = "your_target_protein"

all_data = pd.DataFrame()

for round_num in range(1, ROUNDS + 1):
    print(f"\n=== Round {round_num} ===")

    # Step 1: Generate candidates (replace with actual design model)
    if round_num == 1:
        sequences = ["MAQRITLPSGMKELRL" + "A" * 20 for _ in range(CANDIDATES_PER_ROUND)]
    else:
        parents = all_data.nsmallest(5, "kd_nM")["sequence"].tolist()
        # In practice: sequences = design_model.generate_variants(parents, n=CANDIDATES_PER_ROUND)
        sequences = parents[:CANDIDATES_PER_ROUND]  # placeholder

    # Step 2: Submit
    submission = client.submit_experiment(
        experiment_type="binding",
        sequences=sequences,
        target=TARGET,
        metadata={"round": round_num}
    )
    exp_id = submission["experiment_id"]
    print(f"Submitted {len(sequences)} sequences: {exp_id}")

    # Step 3: Wait for results (skip in demo; poll in production)
    # time.sleep(72 * 3600)

    # Step 4: Retrieve results
    results = client.get_experiment_results(exp_id)
    round_df = pd.DataFrame(results["results"])
    round_df["round"] = round_num
    all_data = pd.concat([all_data, round_df], ignore_index=True)

    best = round_df.nsmallest(1, "kd_nM").iloc[0]
    print(f"Best KD this round: {best['kd_nM']:.2f} nM")

all_data.to_csv("directed_evolution_all_rounds.csv", index=False)
print(f"\nFinal best KD: {all_data['kd_nM'].min():.3f} nM")
```

### Workflow 2: Batch Screen and Rank

```python
import adaptyvbio as ab
import pandas as pd
import matplotlib.pyplot as plt
import os

client = ab.Client(api_key=os.environ["ADAPTYV_API_KEY"])

# Retrieve completed experiment results and rank
exp_id = "exp_completed_123"
results = client.get_experiment_results(exp_id)
df = pd.DataFrame(results["results"])
df = df.dropna(subset=["kd_nM"]).sort_values("kd_nM")

# Summary statistics
print(f"Sequences tested: {len(df)}")
print(f"Expression success rate: {df['expression_pass'].mean():.0%}")
print(f"Binding positives (KD < 100 nM): {(df['kd_nM'] < 100).sum()}")

# Rank plot
fig, ax = plt.subplots(figsize=(10, 4))
ax.semilogy(range(len(df)), df["kd_nM"].values, 'o', markersize=4)
ax.axhline(100, color='red', linestyle='--', label='100 nM threshold')
ax.set_xlabel("Sequence rank")
ax.set_ylabel("KD (nM)")
ax.set_title(f"Binding Affinity Rank — {exp_id}")
ax.legend()
plt.tight_layout()
plt.savefig(f"{exp_id}_rank_plot.pdf", bbox_inches="tight")

# Export top hits
top_hits = df.head(10)[["sequence_name", "sequence", "kd_nM", "yield_ug"]]
top_hits.to_csv(f"{exp_id}_top_hits.csv", index=False)
print(f"\nTop 10 hits:\n{top_hits.to_string(index=False)}")
```

## Key Parameters

| Parameter | Module/Function | Default | Range / Options | Effect |
|-----------|----------------|---------|-----------------|--------|
| `experiment_type` | `submit_experiment` | — | `"expression"`, `"binding"` | Type of assay: expression only or expression + binding |
| `sequences` | `submit_experiment` | — | list of strings, max 96 | Protein sequences to screen per experiment |
| `target` | `submit_experiment` | — | registered target name | Target protein for binding measurement |
| `metadata` | `submit_experiment` | `{}` | dict | Custom key-value pairs stored with experiment |
| `project` | `list_experiments` | None | string | Filter experiments by project name |
| KD threshold | downstream analysis | — | 1–1000 nM | User-defined cutoff for hit selection |

## Best Practices

1. **Include positive and negative control sequences**: Always include a known binder (positive control) and a scrambled/null sequence (negative control) in each experiment batch. This validates assay performance and flags batch-level failures before drawing conclusions about untested variants.

2. **Design candidates in batches matching plate format (48 or 96)**: Adaptyv Bio runs experiments in 48-well or 96-well format. Design candidate batches to fill plates — partial plates cost the same as full plates but generate fewer data points per experiment.

3. **Log all metadata at submission time**: Include round number, parent sequences, computational model version, and generation parameters in the `metadata` field. This makes it possible to reconstruct the design-experiment history for publications and reproducibility.

4. **Filter by expression yield before ranking by KD**: Proteins that failed to express or expressed below the detection threshold will have unreliable KD values. Always filter `expression_pass == True` before sorting by KD.

5. **Use the API to automate the poll-retrieve-design loop**: Implement an automated pipeline that polls every 6–12 hours, retrieves results when complete, runs the design model, and submits the next round — removing the manual bottleneck in iterative protein engineering.

## Common Recipes

### Recipe: Export Top Hits as FASTA

```python
import adaptyvbio as ab
import os

client = ab.Client(api_key=os.environ["ADAPTYV_API_KEY"])

def results_to_fasta(exp_id, top_n=10, kd_cutoff_nM=100, output_file="top_hits.fasta"):
    results = client.get_experiment_results(exp_id)
    hits = [r for r in results["results"]
            if r.get("expression_pass") and r.get("kd_nM", float("inf")) < kd_cutoff_nM]
    hits.sort(key=lambda x: x["kd_nM"])

    with open(output_file, "w") as f:
        for r in hits[:top_n]:
            name = r.get("sequence_name", r["sequence"][:8])
            f.write(f">{name}_KD{r['kd_nM']:.1f}nM\n{r['sequence']}\n")

    print(f"Exported {min(top_n, len(hits))} sequences to {output_file}")

results_to_fasta("exp_abc123", top_n=10, kd_cutoff_nM=50)
```

### Recipe: Compare Rounds by KD Distribution

```python
import pandas as pd
import matplotlib.pyplot as plt

# Load all rounds
rounds = {
    1: pd.read_csv("exp_round1_results.csv"),
    2: pd.read_csv("exp_round2_results.csv"),
    3: pd.read_csv("exp_round3_results.csv"),
}

fig, ax = plt.subplots(figsize=(8, 5))
for round_num, df in rounds.items():
    kd_vals = df.dropna(subset=["kd_nM"])["kd_nM"]
    ax.hist(kd_vals, bins=20, alpha=0.6, label=f"Round {round_num} (n={len(kd_vals)})")

ax.set_xlabel("KD (nM)")
ax.set_ylabel("Count")
ax.set_title("KD Distribution Across Directed Evolution Rounds")
ax.legend()
plt.tight_layout()
plt.savefig("kd_distribution_by_round.pdf", bbox_inches="tight")
```

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| `AuthenticationError` | Invalid or missing API key | Set `ADAPTYV_API_KEY` env var; regenerate key in Adaptyv dashboard |
| Experiment status stuck at "pending" | Queue backlog or missing target configuration | Contact Adaptyv support; verify target protein is registered in account |
| All sequences show `expression_pass=False` | Sequences may be too long, contain invalid characters, or have folding issues | Check sequence length (typical limit: <300 aa); verify no non-standard amino acids; run expression screen before binding assay |
| KD values show high variability (>3×) | Low expression yield causes noisy BLI signal | Filter to `yield_ug > 5`; redesign sequences for better expression |
| `results` field empty after "complete" status | API timing issue; results not yet persisted | Wait 10 minutes and retry; check Adaptyv status page |
| Batch limited to <96 sequences | Account tier restriction | Upgrade account; split into multiple experiments of 48 |
| CSV missing KD values for some sequences | BLI fit failed (poor binding kinetics or non-binding) | Sequences with `kd_nM=None` are non-binders; treat as negative result |

## Related Skills

- `esm-protein-language-model` — generate candidate sequences for submission to Adaptyv Bio
- `benchling-integration` — LIMS management of protein engineering sequences alongside Adaptyv Bio experiments
- `pymoo` — multi-objective optimization using Adaptyv Bio KD + yield data as fitness function

## References

- [Adaptyv Bio platform](https://www.adaptyvbio.com/) — service overview and documentation
- [Adaptyv Bio API documentation](https://docs.adaptyvbio.com/) — SDK reference and endpoint descriptions
- [Cell-free protein synthesis review: Pardee et al. (2016), Cell](https://doi.org/10.1016/j.cell.2016.08.018) — cell-free expression technology background
- [Directed evolution review: Arnold (2018), Angewandte Chemie](https://doi.org/10.1002/anie.201708408) — Nobel lecture on directed evolution methodology
- [Biolayer interferometry review: Sultana & Lee (2015), CMS](https://doi.org/10.1002/cmdc.201500316) — BLI measurement methodology for KD determination
