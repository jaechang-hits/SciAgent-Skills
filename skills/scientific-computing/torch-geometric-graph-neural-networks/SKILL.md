---
name: torch-geometric-graph-neural-networks
description: "PyTorch Geometric (PyG) for graph neural networks. Node classification, graph classification, link prediction with GCN, GAT, GraphSAGE, GIN layers. Message passing framework, mini-batch processing, heterogeneous graphs, neighbor sampling for large-scale learning, model explainability. Supports molecular property prediction (QM9, MoleculeNet), social networks, knowledge graphs, 3D point clouds. For non-graph deep learning use PyTorch directly; for traditional graph algorithms use NetworkX."
license: MIT
---

# PyTorch Geometric (PyG) — Graph Neural Networks

## Overview

PyTorch Geometric is a library built on PyTorch for developing and training Graph Neural Networks (GNNs). It provides 40+ convolutional layers, mini-batch processing via block-diagonal adjacency matrices, neighbor sampling for large-scale graphs, and heterogeneous graph support for multi-type node/edge networks.

## When to Use

- Node classification on citation, social, or biological networks
- Graph-level classification (molecular activity, protein function)
- Link prediction (knowledge graphs, recommendation systems)
- Molecular property prediction (drug discovery, quantum chemistry)
- 3D point cloud processing and mesh analysis
- Large-scale graph learning with neighbor sampling (>100K nodes)
- Heterogeneous graphs with multiple node/edge types
- **For non-graph deep learning** → use PyTorch directly
- **For traditional graph algorithms (shortest path, centrality)** → use NetworkX

## Prerequisites

```bash
pip install torch torch_geometric
# Optional sparse operations (recommended):
# pip install pyg_lib torch_scatter torch_sparse torch_cluster
```

```python
import torch
import torch.nn.functional as F
from torch_geometric.data import Data
from torch_geometric.nn import GCNConv
```

## Quick Start

```python
from torch_geometric.datasets import Planetoid
from torch_geometric.nn import GCNConv
import torch, torch.nn.functional as F

dataset = Planetoid(root='/tmp/Cora', name='Cora')
data = dataset[0]

class GCN(torch.nn.Module):
    def __init__(self):
        super().__init__()
        self.conv1 = GCNConv(dataset.num_features, 16)
        self.conv2 = GCNConv(16, dataset.num_classes)
    def forward(self, data):
        x = F.relu(self.conv1(data.x, data.edge_index))
        return self.conv2(x, data.edge_index)

model = GCN()
optimizer = torch.optim.Adam(model.parameters(), lr=0.01, weight_decay=5e-4)
for epoch in range(200):
    model.train(); optimizer.zero_grad()
    F.cross_entropy(model(data)[data.train_mask], data.y[data.train_mask]).backward()
    optimizer.step()

model.eval()
pred = model(data).argmax(dim=1)
acc = (pred[data.test_mask] == data.y[data.test_mask]).float().mean()
print(f'Test Accuracy: {acc:.4f}')  # ~0.81
```

## Core API

### 1. Data Representation

```python
import torch
from torch_geometric.data import Data

# Create a graph: 3 nodes, 4 edges (undirected)
edge_index = torch.tensor([[0, 1, 1, 2],
                           [1, 0, 2, 1]], dtype=torch.long)
x = torch.randn(3, 16)  # Node features [num_nodes, features]
y = torch.tensor([0, 1, 0])  # Node labels

data = Data(x=x, edge_index=edge_index, y=y)
print(f'Nodes: {data.num_nodes}, Edges: {data.num_edges}')
print(f'Features: {data.num_node_features}')
print(f'Has self-loops: {data.has_self_loops()}')
print(f'Is undirected: {data.is_undirected()}')

# Optional attributes
data.edge_attr = torch.randn(4, 8)   # Edge features [num_edges, features]
data.pos = torch.randn(3, 3)          # Node positions (3D)
data.train_mask = torch.tensor([True, True, False])  # Custom masks
```

```python
# Mini-batch processing — graphs concatenated as block-diagonal
from torch_geometric.loader import DataLoader

loader = DataLoader(dataset, batch_size=32, shuffle=True)
for batch in loader:
    print(f'Graphs: {batch.num_graphs}, Nodes: {batch.num_nodes}')
    # batch.batch maps each node → its source graph index
    # No padding needed — computationally efficient
```

### 2. Convolutional Layers

```python
from torch_geometric.nn import GCNConv, GATConv, SAGEConv, GINConv
import torch.nn as nn

# GCNConv — spectral graph convolution (baseline)
conv = GCNConv(in_channels=16, out_channels=32)
# Supports: edge_weight, SparseTensor, Bipartite, Lazy init

# GATConv — attention-based neighbor weighting
conv = GATConv(16, 32, heads=8, dropout=0.6)
# Output: [N, heads * out_channels] (concat) or [N, out_channels] (concat=False)

# SAGEConv — inductive learning via sampling
conv = SAGEConv(16, 32, aggr='mean')  # 'mean', 'max', 'lstm'

# GINConv — maximally powerful for graph isomorphism
nn_module = nn.Sequential(nn.Linear(16, 32), nn.ReLU(), nn.Linear(32, 32))
conv = GINConv(nn_module)

# TransformerConv — graph transformer
from torch_geometric.nn import TransformerConv
conv = TransformerConv(16, 32, heads=8, beta=True)

# All layers: x_out = conv(x, edge_index)
x_out = conv(x, edge_index)
print(f'Output shape: {x_out.shape}')  # [num_nodes, out_channels]
```

### 3. Custom Message Passing

```python
from torch_geometric.nn import MessagePassing
from torch_geometric.utils import add_self_loops, degree

class CustomConv(MessagePassing):
    def __init__(self, in_channels, out_channels):
        super().__init__(aggr='add')  # 'add', 'mean', 'max'
        self.lin = torch.nn.Linear(in_channels, out_channels)

    def forward(self, x, edge_index):
        edge_index, _ = add_self_loops(edge_index, num_nodes=x.size(0))
        x = self.lin(x)

        # Degree-based normalization
        row, col = edge_index
        deg = degree(col, x.size(0), dtype=x.dtype)
        norm = deg.pow(-0.5)
        norm = norm[row] * norm[col]

        return self.propagate(edge_index, x=x, norm=norm)

    def message(self, x_j, norm):
        # x_j: source node features (automatic via _j suffix)
        return norm.view(-1, 1) * x_j

# Key methods: forward(), message(), aggregate(), update()
# _i suffix → target node, _j suffix → source node
```

### 4. Pooling & Graph-Level Readout

```python
from torch_geometric.nn import (
    global_mean_pool, global_max_pool, global_add_pool,
    TopKPooling, SAGPooling
)

# Global pooling: node features → graph-level representation
x_graph = global_mean_pool(x, batch)  # [num_graphs, features]

# Hierarchical pooling: coarsen graph
pool = TopKPooling(64, ratio=0.8)  # Keep top 80% nodes
x, edge_index, _, batch, _, _ = pool(x, edge_index, None, batch)

# Graph classification model
class GraphClassifier(torch.nn.Module):
    def __init__(self, num_features, num_classes):
        super().__init__()
        self.conv1 = GCNConv(num_features, 64)
        self.conv2 = GCNConv(64, 64)
        self.pool = TopKPooling(64, ratio=0.8)
        self.lin = torch.nn.Linear(64, num_classes)

    def forward(self, data):
        x, edge_index, batch = data.x, data.edge_index, data.batch
        x = F.relu(self.conv1(x, edge_index))
        x, edge_index, _, batch, _, _ = self.pool(x, edge_index, None, batch)
        x = F.relu(self.conv2(x, edge_index))
        x = global_mean_pool(x, batch)
        return self.lin(x)
```

### 5. Heterogeneous Graphs

```python
from torch_geometric.data import HeteroData
from torch_geometric.nn import HeteroConv, GCNConv, SAGEConv, to_hetero

# Create heterogeneous graph
data = HeteroData()
data['paper'].x = torch.randn(100, 128)
data['author'].x = torch.randn(200, 64)
data['author', 'writes', 'paper'].edge_index = torch.randint(0, 200, (2, 500))
data['paper', 'cites', 'paper'].edge_index = torch.randint(0, 100, (2, 300))
print(data)  # Shows all node/edge types

# Method 1: Auto-convert homogeneous model
model = GCN(...)
model = to_hetero(model, data.metadata(), aggr='sum')
out = model(data.x_dict, data.edge_index_dict)
```

```python
# Method 2: Custom per-edge-type convolutions
class HeteroGNN(torch.nn.Module):
    def __init__(self):
        super().__init__()
        self.conv1 = HeteroConv({
            ('paper', 'cites', 'paper'): GCNConv(-1, 64),
            ('author', 'writes', 'paper'): SAGEConv((-1, -1), 64),
        }, aggr='sum')

    def forward(self, x_dict, edge_index_dict):
        x_dict = self.conv1(x_dict, edge_index_dict)
        return {k: F.relu(v) for k, v in x_dict.items()}
```

### 6. Transforms & Preprocessing

```python
from torch_geometric.transforms import (
    NormalizeFeatures, AddSelfLoops, ToUndirected,
    RandomNodeSplit, RandomLinkSplit, Compose,
    KNNGraph, RadiusGraph, AddLaplacianEigenvectorPE
)

# Single transform
dataset = Planetoid(root='/tmp/Cora', name='Cora', transform=NormalizeFeatures())

# Compose multiple transforms
transform = Compose([
    ToUndirected(),
    AddSelfLoops(),
    NormalizeFeatures(),
])

# Data splitting
node_split = RandomNodeSplit(num_val=0.1, num_test=0.2)
link_split = RandomLinkSplit(num_val=0.1, num_test=0.2, is_undirected=True)

# Point cloud → graph
pc_transform = Compose([KNNGraph(k=6), NormalizeFeatures()])

# Positional encodings (for Graph Transformers)
pe_transform = AddLaplacianEigenvectorPE(k=10)
```

## Key Concepts

### Layer Selection Guide

| Task | Layer | Key Feature |
|------|-------|-------------|
| Baseline / general | `GCNConv` | Spectral, cached, edge_weight |
| Variable neighbor importance | `GATConv` / `GATv2Conv` | Multi-head attention |
| Large-scale inductive | `SAGEConv` | Sampling-friendly, mean/max/lstm aggr |
| Graph classification | `GINConv` | Maximally powerful WL-test |
| Long-range dependencies | `TransformerConv` | Graph transformer |
| Spectral filtering | `ChebConv` | Chebyshev polynomials, K hops |
| Rich edge features | `NNConv` | Edge NN processes edge_attr |
| Molecular / 3D structures | `SchNet`, `DimeNet` | Continuous filters, angles |
| Heterogeneous / multi-relation | `RGCNConv`, `HGTConv` | Multiple edge types |
| Point clouds | `EdgeConv`, `PointNetConv` | Dynamic graphs, local features |
| Deep GNNs (avoid oversmoothing) | `APPNP` + `PairNorm` | Separated propagation |

### Data Flow Architecture

- **edge_index**: `[2, num_edges]` COO format. Row 0 = source, Row 1 = target
- **Mini-batch**: Block-diagonal adjacency + `batch` vector mapping nodes → graphs. No padding
- **Neighbor sampling**: `NeighborLoader` samples K-hop subgraphs per seed node. Output is directed, relabeled
- **Heterogeneous**: `x_dict` (per-type features), `edge_index_dict` (per-relation edges), `metadata()` for schema

### Aggregation Options

| Aggregation | Class | Use Case |
|-------------|-------|----------|
| Sum | `SumAggregation` | Counting-sensitive tasks |
| Mean | `MeanAggregation` | Degree-invariant |
| Max | `MaxAggregation` | Salient feature detection |
| Softmax | `SoftmaxAggregation(learn=True)` | Learnable attention |
| Multi | `MultiAggregation(['mean','max','std'])` | Combined signals |

## Common Workflows

### 1. Node Classification (Full Graph)

```python
import torch
import torch.nn.functional as F
from torch_geometric.datasets import Planetoid
from torch_geometric.nn import GCNConv

dataset = Planetoid(root='/tmp/Cora', name='Cora')
data = dataset[0]

class GCN(torch.nn.Module):
    def __init__(self):
        super().__init__()
        self.conv1 = GCNConv(dataset.num_features, 16)
        self.conv2 = GCNConv(16, dataset.num_classes)
    def forward(self, data):
        x = F.dropout(F.relu(self.conv1(data.x, data.edge_index)), p=0.5, training=self.training)
        return self.conv2(x, data.edge_index)

model = GCN()
optimizer = torch.optim.Adam(model.parameters(), lr=0.01, weight_decay=5e-4)

# Training
for epoch in range(200):
    model.train(); optimizer.zero_grad()
    out = model(data)
    F.cross_entropy(out[data.train_mask], data.y[data.train_mask]).backward()
    optimizer.step()

# Evaluation
model.eval()
pred = model(data).argmax(dim=1)
acc = (pred[data.test_mask] == data.y[data.test_mask]).float().mean()
print(f'Test Accuracy: {acc:.4f}')
```

### 2. Graph Classification (Mini-Batch)

```python
from torch_geometric.datasets import TUDataset
from torch_geometric.loader import DataLoader
from torch_geometric.nn import GCNConv, global_mean_pool

dataset = TUDataset(root='/tmp/ENZYMES', name='ENZYMES')
train_dataset = dataset[:int(0.8 * len(dataset))]
test_dataset = dataset[int(0.8 * len(dataset)):]
train_loader = DataLoader(train_dataset, batch_size=32, shuffle=True)

class GraphNet(torch.nn.Module):
    def __init__(self):
        super().__init__()
        self.conv1 = GCNConv(dataset.num_features, 64)
        self.conv2 = GCNConv(64, 64)
        self.lin = torch.nn.Linear(64, dataset.num_classes)
    def forward(self, data):
        x = F.relu(self.conv1(data.x, data.edge_index))
        x = F.relu(self.conv2(x, data.edge_index))
        x = global_mean_pool(x, data.batch)
        return self.lin(x)

model = GraphNet()
optimizer = torch.optim.Adam(model.parameters(), lr=0.01)
for epoch in range(100):
    model.train()
    for batch in train_loader:
        optimizer.zero_grad()
        F.cross_entropy(model(batch), batch.y).backward()
        optimizer.step()
```

### 3. Large-Scale with Neighbor Sampling

```python
from torch_geometric.loader import NeighborLoader

# Sample 25 1-hop and 10 2-hop neighbors per seed node
train_loader = NeighborLoader(
    data,
    num_neighbors=[25, 10],
    batch_size=128,
    input_nodes=data.train_mask,
)

model.train()
for batch in train_loader:
    optimizer.zero_grad()
    out = model(batch)
    # Only compute loss on seed nodes (first batch_size nodes)
    loss = F.cross_entropy(out[:batch.batch_size], batch.y[:batch.batch_size])
    loss.backward()
    optimizer.step()
# Note: output subgraphs are directed, indices relabeled 0..N-1
```

## Key Parameters

| Parameter | Module | Default | Range | Effect |
|-----------|--------|---------|-------|--------|
| `in_channels` | All Conv layers | — | int | Input feature dimension |
| `out_channels` | All Conv layers | — | int | Output feature dimension |
| `heads` | GATConv | 1 | 1-16 | Number of attention heads |
| `dropout` | GATConv | 0.0 | 0-0.8 | Attention weight dropout |
| `aggr` | MessagePassing | 'add' | add/mean/max | Neighbor aggregation |
| `K` | ChebConv | — | 2-5 | Chebyshev polynomial order |
| `num_neighbors` | NeighborLoader | — | list[int] | Neighbors per hop (e.g., [25,10]) |
| `batch_size` | DataLoader | — | 16-512 | Graphs or seed nodes per batch |
| `ratio` | TopKPooling | 0.5 | 0.1-0.9 | Fraction of nodes to keep |
| `lr` | Adam | — | 1e-4 to 0.01 | Learning rate |
| `weight_decay` | Adam | 0 | 0 to 5e-3 | L2 regularization |

## Best Practices

1. **Start with GCNConv**: Use 2-layer GCN as baseline before trying complex architectures
2. **Use lazy initialization**: Pass `-1` as `in_channels` to infer dimensions automatically: `GCNConv(-1, 64)`
3. **Normalize features**: Apply `NormalizeFeatures()` transform for citation/social networks
4. **Anti-pattern — too many layers**: GNNs typically need only 2-3 layers. Deeper causes oversmoothing. Use `JumpingKnowledge` or `PairNorm` if you need depth
5. **GPU transfer**: Move both model AND data to GPU: `model.to(device)`, `data.to(device)`
6. **Anti-pattern — ignoring batch vector**: In graph classification, always use `global_mean_pool(x, batch)` — forgetting `batch` pools across all graphs

## Common Recipes

### Recipe: Model Explainability (GNNExplainer)

```python
from torch_geometric.explain import Explainer, GNNExplainer

explainer = Explainer(
    model=model,
    algorithm=GNNExplainer(epochs=200),
    explanation_type='model',
    node_mask_type='attributes',
    edge_mask_type='object',
    model_config=dict(mode='multiclass_classification', task_level='node', return_type='log_probs'),
)

explanation = explainer(data.x, data.edge_index, index=10)
print(f'Important edges: {explanation.edge_mask.topk(5).indices}')
print(f'Important features: {explanation.node_mask[10].topk(5).indices}')
```

### Recipe: Custom InMemoryDataset

```python
from torch_geometric.data import InMemoryDataset, Data

class MyDataset(InMemoryDataset):
    def __init__(self, root, transform=None, pre_transform=None):
        super().__init__(root, transform, pre_transform)
        self.load(self.processed_paths[0])

    @property
    def raw_file_names(self):
        return ['data.csv']

    @property
    def processed_file_names(self):
        return ['data.pt']

    def process(self):
        data_list = []
        # Build Data objects from raw files
        edge_index = torch.tensor([[0, 1], [1, 0]], dtype=torch.long)
        x = torch.randn(2, 16)
        data_list.append(Data(x=x, edge_index=edge_index, y=torch.tensor([0])))

        if self.pre_filter is not None:
            data_list = [d for d in data_list if self.pre_filter(d)]
        if self.pre_transform is not None:
            data_list = [self.pre_transform(d) for d in data_list]
        self.save(data_list, self.processed_paths[0])
```

### Recipe: Deep GNN with JumpingKnowledge

```python
from torch_geometric.nn import GCNConv, JumpingKnowledge, LayerNorm

class DeepGNN(torch.nn.Module):
    def __init__(self, in_ch, hidden, num_layers, out_ch):
        super().__init__()
        self.convs = torch.nn.ModuleList()
        self.norms = torch.nn.ModuleList()
        self.convs.append(GCNConv(in_ch, hidden))
        self.norms.append(LayerNorm(hidden))
        for _ in range(num_layers - 2):
            self.convs.append(GCNConv(hidden, hidden))
            self.norms.append(LayerNorm(hidden))
        self.convs.append(GCNConv(hidden, hidden))
        self.jk = JumpingKnowledge(mode='cat')
        self.lin = torch.nn.Linear(hidden * num_layers, out_ch)

    def forward(self, x, edge_index, batch):
        xs = []
        for conv, norm in zip(self.convs[:-1], self.norms):
            x = F.relu(norm(conv(x, edge_index)))
            xs.append(x)
        xs.append(self.convs[-1](x, edge_index))
        return self.lin(global_mean_pool(self.jk(xs), batch))
```

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|---------|
| `edge_index` shape error | Wrong format (should be [2, E]) | Ensure COO format: `torch.tensor([[src...],[dst...]], dtype=torch.long)` |
| OOM on large graph | Full-graph forward pass | Use `NeighborLoader` for mini-batch training |
| Low accuracy | Oversmoothing (too many layers) | Reduce to 2-3 layers, add `JumpingKnowledge` or `PairNorm` |
| NaN in training | Exploding gradients | Add gradient clipping, reduce learning rate, check feature scale |
| Wrong graph-level output | Missing `batch` in pooling | Pass `batch` tensor to `global_mean_pool(x, batch)` |
| Heterogeneous type error | Mismatched node/edge types | Check `data.metadata()` matches model definition |
| Slow DataLoader | Large graph, no sampling | Use `NeighborLoader` with reasonable `num_neighbors` (e.g., [25,10]) |
| `x` dimension mismatch | Multi-head attention output | For GATConv: output is `heads*out_channels` unless `concat=False` |
| Import error for sparse ops | Missing optional dependencies | Install `torch_scatter`, `torch_sparse` from PyG wheels |
| Pre-transform not applied | Dataset already processed | Delete `processed/` directory and reload |

## Bundled Resources

- **`references/layers_transforms_reference.md`** — Complete catalog of 40+ convolutional layers (GCN, GAT, SAGE, GIN, molecular layers, hypergraph), aggregation operators, pooling (global + hierarchical), normalization layers, pre-built models, auto-encoders, knowledge graph embeddings, utility layers. Transform catalog: structure, feature, spatial, augmentation, mesh, specialized. Consolidated from original layers_reference.md (486 lines) + transforms_reference.md (680 lines). Script functionality (benchmark_model.py, create_gnn_template.py, visualize_graph.py) covered by Core API code blocks and Common Recipes
- **`references/datasets_catalog.md`** — Comprehensive dataset catalog organized by domain: citation networks (Planetoid, Coauthor, Amazon), graph classification (TUDataset 120+ benchmarks), molecular (QM9, ZINC, MoleculeNet), social (Reddit, Twitch), knowledge graphs (WordNet, FB15k), heterogeneous (OGB_MAG, MovieLens, DBLP), temporal (JODIE), 3D meshes (ShapeNet, ModelNet), OGB integration. Consolidated from original datasets_reference.md (575 lines)

## Related Skills

- **matplotlib-scientific-plotting** — Visualize graph structures, training curves, attention weights

## References

- PyTorch Geometric Documentation: https://pytorch-geometric.readthedocs.io/
- PyG GitHub: https://github.com/pyg-team/pytorch_geometric
- Fey & Lenssen (2019), "Fast Graph Representation Learning with PyTorch Geometric", ICLR Workshop
