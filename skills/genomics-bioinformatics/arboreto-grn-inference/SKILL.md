---
name: "arboreto-grn-inference"
description: "GRN inference from expression via GRNBoost2 (gradient boosting) or GENIE3 (Random Forest). Load matrix, filter by TFs, infer TF-target-importance links, save network. Dask-parallelized to single-cell scale. Core SCENIC component."
license: "BSD-3-Clause"
---

# Arboreto GRN Inference

## Overview

Arboreto infers gene regulatory networks (GRNs) from gene expression data using parallelized tree-based regression. For each target gene, it trains a regression model with all other genes (or a specified TF list) as features and emits TF-target-importance triplets. It provides two interchangeable algorithms -- GRNBoost2 (gradient boosting, fast) and GENIE3 (Random Forest, classic) -- sharing identical input/output formats. Computation is Dask-parallelized, scaling from laptop cores to HPC clusters.

## When to Use

- Inferring transcription factor-to-target gene regulatory relationships from bulk RNA-seq expression data
- Building gene regulatory networks from single-cell RNA-seq count matrices (cells as rows, genes as columns)
- Generating the adjacency matrix (Step 1) of the pySCENIC regulatory analysis pipeline
- Comparing regulatory network structure across experimental conditions (e.g., control vs treatment)
- Producing consensus regulatory networks by running inference across multiple random seeds
- Validating GRN results by comparing GRNBoost2 and GENIE3 outputs on the same dataset
- For downstream regulon identification and activity scoring, use arboreto output with pySCENIC
- For single-cell preprocessing (QC, normalization, clustering) before GRN inference, use **scanpy-scrna-seq**

## Prerequisites

- **Python packages**: `arboreto`, `pandas`, `numpy`, `dask`, `distributed`, `scikit-learn`, `scipy`
- **Data requirements**: Gene expression matrix (genes as columns, observations as rows) in TSV/CSV; optionally a TF list file (one gene name per line)
- **Environment**: Python 3.8+; optional `networkx`, `matplotlib` for visualization

```bash
pip install arboreto distributed networkx matplotlib
```

## Quick Start

Complete GRN inference in a single block. The `if __name__ == '__main__':` guard is required because Dask spawns worker processes via multiprocessing.

```python
import pandas as pd
from arboreto.algo import grnboost2
from arboreto.utils import load_tf_names

if __name__ == '__main__':
    # Load expression matrix (observations x genes)
    expression_matrix = pd.read_csv('expression_data.tsv', sep='\t')
    tf_names = load_tf_names('tf_list.txt')  # optional TF filter

    # Infer GRN (uses all local cores by default)
    network = grnboost2(expression_data=expression_matrix,
                        tf_names=tf_names, seed=777)

    # Filter top links and save
    top_network = network[network['importance'] > 1.0]
    top_network.to_csv('grn_output.tsv', sep='\t', index=False, header=False)
    print(f"Inferred {len(network)} links, kept {len(top_network)} above threshold")
    # Example: Inferred 185432 links, kept 12876 above threshold
```

## Workflow

### Step 1: Load Expression Data

Arboreto accepts a pandas DataFrame (recommended) or NumPy array. Rows are observations (cells or samples), columns are genes. Gene names must be column headers.

```python
import pandas as pd

# From TSV (genes as columns, observations as rows)
expression_matrix = pd.read_csv('expression_data.tsv', sep='\t')
print(f"Shape: {expression_matrix.shape}  "
      f"({expression_matrix.shape[0]} observations x {expression_matrix.shape[1]} genes)")
# Example: Shape: (5000, 18654)  (5000 observations x 18654 genes)

# From AnnData (e.g., after scanpy preprocessing)
import anndata as ad
adata = ad.read_h5ad('preprocessed.h5ad')
expression_matrix = pd.DataFrame(
    adata.X.toarray() if hasattr(adata.X, 'toarray') else adata.X,
    columns=adata.var_names.tolist()
)
print(f"Converted AnnData: {expression_matrix.shape}")
# Example: Converted AnnData: (5000, 18654)
```

### Step 2: Load Transcription Factor List

Providing a TF list restricts regulators to known transcription factors, reducing computation time and improving biological relevance. If omitted, all genes are treated as potential regulators.

```python
from arboreto.utils import load_tf_names

# From file (one TF name per line)
tf_names = load_tf_names('human_tfs.txt')
print(f"Loaded {len(tf_names)} transcription factors")
# Example: Loaded 1639 transcription factors

# Or define directly
tf_names = ['MYC', 'TP53', 'SOX2', 'NANOG', 'POU5F1']

# Verify TFs exist in expression matrix columns
tf_in_data = [tf for tf in tf_names if tf in expression_matrix.columns]
print(f"TFs found in expression data: {len(tf_in_data)}/{len(tf_names)}")
# Example: TFs found in expression data: 1583/1639
```

### Step 3: Configure Dask Client (Optional)

By default arboreto creates an internal Dask client using all local cores. Create an explicit client for resource control, monitoring, or cluster deployment.

```python
from distributed import LocalCluster, Client

# Custom local client with resource limits
local_cluster = LocalCluster(
    n_workers=8,
    threads_per_worker=1,   # avoid GIL contention in scikit-learn
    memory_limit='4GB'       # per worker
)
client = Client(local_cluster)
print(f"Dashboard: {client.dashboard_link}")
# Example: Dashboard: http://127.0.0.1:8787/status
```

### Step 4: Run GRN Inference

Call `grnboost2()` (recommended) or `genie3()`. Both share the same signature and output format.

```python
from arboreto.algo import grnboost2

if __name__ == '__main__':
    network = grnboost2(
        expression_data=expression_matrix,
        tf_names=tf_names,         # 'all' if no TF list
        client_or_address=client,  # omit to use default local scheduler
        seed=777,                  # for reproducibility
        verbose=True               # print progress
    )
    print(f"Inferred {len(network)} regulatory links")
    print(network.head())
    # Example:
    #       TF  target  importance
    # 0   MYC   CDK4       3.214
    # 1   MYC   CCND1      2.871
    # 2  TP53  CDKN1A      2.654
```

### Step 5: Filter Results

Raw output contains links for every TF-target pair with non-zero importance. Filter to retain high-confidence regulatory interactions.

```python
# Strategy 1: Importance threshold
threshold = 1.0
filtered = network[network['importance'] > threshold]
print(f"Threshold {threshold}: {len(filtered)} links "
      f"({len(filtered)/len(network)*100:.1f}% retained)")
# Example: Threshold 1.0: 12876 links (6.9% retained)

# Strategy 2: Top N links per target gene
top_n = 10
top_per_target = (network.groupby('target')
                  .apply(lambda g: g.nlargest(top_n, 'importance'))
                  .reset_index(drop=True))
print(f"Top {top_n} per target: {len(top_per_target)} links")
# Example: Top 10 per target: 186540 links
```

### Step 6: Save Network

Save as a TSV file with three columns: TF, target, importance.

```python
# Save full network
network.to_csv('full_network.tsv', sep='\t', index=False)
print(f"Saved full network: {len(network)} links")

# Save filtered network (without header for pySCENIC compatibility)
filtered.to_csv('filtered_network.tsv', sep='\t', index=False, header=False)
print(f"Saved filtered network: {len(filtered)} links")

# Clean up Dask client if explicitly created
client.close()
local_cluster.close()
```

### Step 7: Visualize Results (Optional)

Plot the top regulatory interactions as a directed network graph.

```python
import networkx as nx
import matplotlib.pyplot as plt

# Build directed graph from top links
top_links = network.nlargest(50, 'importance')
G = nx.from_pandas_edgelist(
    top_links, source='TF', target='target',
    edge_attr='importance', create_using=nx.DiGraph()
)

# Draw network
fig, ax = plt.subplots(figsize=(12, 10))
pos = nx.spring_layout(G, k=2, seed=42)
nx.draw_networkx_nodes(G, pos, node_size=300, node_color='lightblue', ax=ax)
nx.draw_networkx_labels(G, pos, font_size=7, ax=ax)
edges = nx.draw_networkx_edges(
    G, pos, edge_color=[G[u][v]['importance'] for u, v in G.edges()],
    edge_cmap=plt.cm.Reds, width=1.5, arrows=True, ax=ax
)
plt.colorbar(edges, ax=ax, label='Importance')
ax.set_title('Top 50 Regulatory Interactions')
plt.tight_layout()
plt.savefig('grn_network.png', dpi=300, bbox_inches='tight')
print("Saved grn_network.png")
```

## Key Parameters

| Parameter | Default | Range / Options | Effect |
|-----------|---------|-----------------|--------|
| `expression_data` | (required) | DataFrame or ndarray | Expression matrix, observations x genes |
| `tf_names` | `'all'` | list of str or `'all'` | Restrict regulators to known TFs; `'all'` uses every gene |
| `gene_names` | `None` | list of str | Required when `expression_data` is a NumPy array |
| `client_or_address` | `'local'` | Client, str, or `'local'` | Dask client instance or scheduler address |
| `seed` | `None` | int | Random seed for reproducibility; always set for replicable results |
| `verbose` | `False` | bool | Print progress messages during inference |

## Key Concepts

### Algorithm Selection Guide

Both algorithms follow the same multiple-regression strategy (train one model per target gene, extract feature importances) but differ in the underlying regressor.

| Feature | GRNBoost2 | GENIE3 |
|---------|-----------|--------|
| **Method** | Stochastic gradient boosting with early stopping | Random Forest (or ExtraTrees) |
| **Speed** | Fast -- optimized for large datasets | Slower -- higher per-model cost |
| **Memory** | Lower (early stopping limits tree depth) | Higher (full forests per target) |
| **Best for** | Default choice; 10k+ observations, single-cell scale | Comparison with published GENIE3 results; validation |
| **Import** | `from arboreto.algo import grnboost2` | `from arboreto.algo import genie3` |
| **Output format** | TF, target, importance (identical) | TF, target, importance (identical) |

**Decision rule**: Start with GRNBoost2. Use GENIE3 only when reproducing published GENIE3 analyses or as an independent validation of GRNBoost2 results.

### Output Format

The network DataFrame has three columns, sorted by descending importance:

| Column | Type | Description |
|--------|------|-------------|
| `TF` | str | Transcription factor (regulator) gene name |
| `target` | str | Target gene name |
| `importance` | float | Regulatory importance score (higher = stronger predicted regulation) |

Importance scores are not p-values. They represent feature importance from the tree-based model. Filter by absolute threshold or top-N per target for downstream analysis.

### The `if __name__ == '__main__':` Requirement

Dask uses Python's `multiprocessing` module to spawn worker processes. Without the main guard, each spawned process re-executes the script, leading to infinite process spawning. Always wrap arboreto calls in `if __name__ == '__main__':` when running as a script. This is not needed inside Jupyter notebooks.

## Common Recipes

### Recipe: Distributed Computing on a Cluster

When to use: datasets too large for a single machine (e.g., 50k+ cells, 20k+ genes). Requires a Dask distributed scheduler running on the cluster.

```bash
# On head node: start scheduler
dask-scheduler
# Output: Scheduler at tcp://10.118.224.134:8786

# On each compute node: start workers
dask-worker tcp://10.118.224.134:8786 --nprocs 4 --nthreads 1 --memory-limit 16GB
```

```python
from distributed import Client
from arboreto.algo import grnboost2
import pandas as pd

if __name__ == '__main__':
    client = Client('tcp://10.118.224.134:8786')
    print(f"Connected to cluster: {client.scheduler_info()['workers'].__len__()} workers")
    # Example: Connected to cluster: 16 workers

    expression_data = pd.read_csv('large_scrna.tsv', sep='\t')
    tf_names = pd.read_csv('tf_list.txt', header=None)[0].tolist()

    network = grnboost2(
        expression_data=expression_data,
        tf_names=tf_names,
        client_or_address=client,
        seed=42, verbose=True
    )
    network.to_csv('cluster_grn.tsv', sep='\t', index=False)
    print(f"Cluster inference complete: {len(network)} links")
    client.close()
```

### Recipe: Consensus Network from Multiple Seeds

When to use: improve robustness by aggregating networks from multiple random seeds. Links appearing consistently across runs are more reliable.

```python
import pandas as pd
from distributed import LocalCluster, Client
from arboreto.algo import grnboost2

if __name__ == '__main__':
    client = Client(LocalCluster(n_workers=8, threads_per_worker=1))
    expression_data = pd.read_csv('expression_data.tsv', sep='\t')
    tf_names = pd.read_csv('tf_list.txt', header=None)[0].tolist()

    seeds = [42, 123, 456, 789, 1001]
    all_networks = []

    for seed in seeds:
        net = grnboost2(expression_data=expression_data,
                        tf_names=tf_names,
                        client_or_address=client, seed=seed)
        net['seed'] = seed
        all_networks.append(net)
        print(f"Seed {seed}: {len(net)} links")

    combined = pd.concat(all_networks, ignore_index=True)

    # Consensus: mean importance across seeds, keep links found in 3+ runs
    consensus = (combined.groupby(['TF', 'target'])
                 .agg(mean_importance=('importance', 'mean'),
                      n_seeds=('seed', 'nunique'))
                 .reset_index())
    consensus = consensus[consensus['n_seeds'] >= 3]
    consensus = consensus.sort_values('mean_importance', ascending=False)
    consensus.to_csv('consensus_network.tsv', sep='\t', index=False)
    print(f"Consensus network: {len(consensus)} links (found in 3+ of {len(seeds)} runs)")
    # Example: Consensus network: 28453 links (found in 3+ of 5 runs)

    client.close()
```

### Recipe: pySCENIC Integration

When to use: downstream regulatory analysis after arboreto GRN inference. Arboreto produces the adjacency matrix (Step 1 of SCENIC); pySCENIC performs regulon identification (Step 2) and activity scoring (Step 3).

```python
from arboreto.algo import grnboost2
from arboreto.utils import load_tf_names
import pandas as pd

if __name__ == '__main__':
    # Step 1 (arboreto): GRN inference
    expression_matrix = pd.read_csv('scrna_expression.tsv', sep='\t')
    tf_names = load_tf_names('allTFs_hg38.txt')

    adjacencies = grnboost2(
        expression_data=expression_matrix,
        tf_names=tf_names, seed=777
    )
    adjacencies.to_csv('adjacencies.tsv', sep='\t', index=False, header=False)
    print(f"SCENIC Step 1 complete: {len(adjacencies)} adjacencies")
    # Example: SCENIC Step 1 complete: 234567 adjacencies

    # Steps 2-3 use pySCENIC CLI (requires pyscenic installation):
    # pyscenic ctx adjacencies.tsv hg38_ranking.feather \
    #     --annotations_fname motifs-v10nr.hgnc-m0.001-o0.0.tbl \
    #     --output regulons.csv
    #
    # pyscenic aucell scrna_expression.tsv regulons.csv \
    #     --output auc_matrix.csv
    print("Next: run pyscenic ctx (Step 2) and pyscenic aucell (Step 3)")
```

## Expected Outputs

- `full_network.tsv` -- complete TF-target-importance table; columns: TF, target, importance
- `filtered_network.tsv` -- high-confidence subset after threshold or top-N filtering
- `consensus_network.tsv` -- aggregated network from multi-seed runs; columns: TF, target, mean_importance, n_seeds
- `adjacencies.tsv` -- arboreto output formatted for pySCENIC input (no header)
- `grn_network.png` -- directed graph visualization of top regulatory interactions

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| `RuntimeError: freeze_support()` or infinite process spawning | Missing `if __name__ == '__main__':` guard | Wrap all arboreto calls in main guard; not needed in Jupyter |
| `MemoryError` during inference | Expression matrix too large for available RAM | Filter low-variance genes first, reduce to top 5-10k genes, or use distributed cluster |
| Empty or near-empty network | TF names do not match expression matrix column names | Verify TF names overlap with `expression_matrix.columns`; check case sensitivity |
| Very slow inference | Using GENIE3 on large dataset, or too few Dask workers | Switch to GRNBoost2; create explicit Dask client with more workers |
| `ModuleNotFoundError: No module named 'arboreto'` | Package not installed | `pip install arboreto` |
| All importance scores are 0 or identical | Expression matrix has no variance (e.g., all zeros after filtering) | Check data quality; ensure matrix contains non-zero expression values with variance |
| `TypeError` with NumPy array input | Missing `gene_names` parameter | Provide `gene_names=` list matching the column count of the array |

## Bundled Resources

This entry is fully self-contained with no `references/` directory.

**Original reference file dispositions**:

- **references/algorithms.md** (139 lines) -- Algorithm comparison, parameter details, custom regressor kwargs. Consolidated into Key Concepts (Algorithm Selection Guide table) and Key Parameters. Custom regressor kwargs (`regressor_type`, `regressor_kwargs`) omitted: advanced tuning rarely needed; users can pass scikit-learn kwargs directly per the arboreto API docs.
- **references/basic_inference.md** (152 lines) -- Input formats, TF loading, basic workflow, output format. Fully consolidated into Workflow Steps 1-2, Key Concepts (Output Format table), and Quick Start.
- **references/distributed_computing.md** (242 lines) -- Local client, cluster setup, monitoring, performance tips. Consolidated into Workflow Step 3 and Recipe: Distributed Computing. Omitted: Dask dashboard panel descriptions (monitoring UI detail beyond scope), detailed network/storage tuning (cluster-admin concern).
- **scripts/basic_grn_inference.py** (98 lines) -- CLI wrapper with argparse. Core load-infer-save logic absorbed into Workflow Steps 1-6 and Quick Start. Argparse/CLI boilerplate stripped.

**Narrative use-case dispositions** (from original Common Use Cases):

- Single-cell RNA-seq analysis -- absorbed into When to Use bullets and Workflow Steps 1/4
- Bulk RNA-seq with TF filtering -- absorbed into Workflow Step 2 and Quick Start
- Comparative analysis (multiple conditions) -- omitted as standalone recipe: trivial loop over conditions, pattern shown in Consensus Network recipe

## Related Skills

- **scanpy-scrna-seq** -- upstream single-cell preprocessing (QC, normalization, HVG selection) before GRN inference
- **scvi-tools-single-cell** -- deep generative models for batch correction and imputation prior to network inference
- **pyscenic (planned)** -- downstream regulon identification and cellular activity scoring using arboreto adjacencies
- **networkx-graph-analysis** -- graph-theoretic analysis of inferred regulatory networks (centrality, communities)

## References

- [Arboreto GitHub repository](https://github.com/aertslab/arboreto) -- source code, README, examples
- [Arboreto PyPI](https://pypi.org/project/arboreto/) -- installation and version history
- Moerman et al. (2019) "GRNBoost2 and Arboreto: efficient and scalable inference of gene regulatory networks" *Bioinformatics* 35(12):2159-2161 -- algorithm paper
- Aibar et al. (2017) "SCENIC: single-cell regulatory network inference and clustering" *Nature Methods* 14:1083-1086 -- SCENIC pipeline paper
- [Dask distributed documentation](https://distributed.dask.org/) -- Dask client, cluster setup, dashboard
