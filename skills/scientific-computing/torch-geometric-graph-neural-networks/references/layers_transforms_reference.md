# PyG Layers, Pooling, Normalization & Transforms Reference

Complete catalog of convolutional layers, aggregation operators, pooling, normalization, pre-built models, and transforms in PyTorch Geometric.

## Convolutional Layers

### Standard Graph Convolutions

| Layer | Key Feature | Supports | Use For |
|-------|-------------|----------|---------|
| **GCNConv** | Spectral, symmetric normalization | SparseTensor, edge_weight, Bipartite, Lazy | General graph learning, citation networks |
| **SAGEConv** | Inductive, neighborhood sampling | SparseTensor, Bipartite, Lazy | Large graphs, inductive learning |
| **GATConv** | Multi-head attention | SparseTensor, edge_attr, Bipartite, Static, Lazy | Variable neighbor importance |
| **GATv2Conv** | Fixed static attention bug in GAT | SparseTensor, edge_attr, Bipartite, Static, Lazy | Better attention than original GAT |
| **GraphConv** | Simple message passing (Morris) | SparseTensor, edge_weight, Bipartite, Lazy | Baseline models |
| **GINConv** | Maximally powerful WL-test | Bipartite | Graph classification, molecular property |
| **TransformerConv** | Graph + transformer attention | SparseTensor, Bipartite, Lazy | Long-range dependencies |
| **ChebConv** | Chebyshev spectral filtering | SparseTensor, edge_weight, Bipartite, Lazy | Spectral learning, K-hop |
| **SGConv** | Pre-computed propagation | SparseTensor, edge_weight, Bipartite, Lazy | Fast training, shallow models |
| **APPNP** | Separated transform/propagation | SparseTensor, edge_weight, Lazy | Deep propagation without oversmoothing |
| **ARMAConv** | ARMA filters | SparseTensor, edge_weight, Bipartite, Lazy | Advanced spectral methods |
| **SuperGATConv** | Self-supervised attention | SparseTensor, edge_attr, Bipartite, Static, Lazy | Self-supervised, limited labels |
| **RGCNConv** | Multiple edge types | SparseTensor, edge_weight, Lazy | Knowledge graphs, heterogeneous |
| **FAConv** | Frequency adaptive filtering | SparseTensor, Lazy | Spectral graph learning |
| **GENConv** | Generalizes multiple GNN variants | SparseTensor, edge_weight, edge_attr, Bipartite, Lazy | Flexible architecture exploration |
| **FiLMConv** | Feature-wise linear modulation | Bipartite, Lazy | Conditional generation, multi-task |
| **PANConv** | Multi-hop path attention | SparseTensor, Lazy | Complex connectivity |
| **ClusterGCNConv** | Graph clustering training | edge_attr, Lazy | Very large graphs |
| **MFConv** | Multi-scale features | SparseTensor, Lazy | Multi-scale patterns |
| **ResGatedGraphConv** | Gating + residual | edge_attr, Bipartite, Lazy | Deep GNNs |

### Edge-Feature & Spatial Convolutions

| Layer | Key Feature | Use For |
|-------|-------------|---------|
| **NNConv** | Edge features via neural network | Rich edge features, molecular graphs |
| **CGConv** | Crystal Graph Convolution | Materials science, crystals |
| **GMMConv** | Gaussian kernels in pseudo-coordinates | Point clouds, spatial data |
| **SplineConv** | B-spline basis functions | Irregular grids, continuous spaces |
| **EdgeConv** | Dynamic graph CNN | Point clouds, dynamic graphs |
| **PointNetConv** | Local + global features | 3D point cloud processing |

### Molecular & 3D Convolutions

| Layer | Key Feature | Use For |
|-------|-------------|---------|
| **SchNet** | Continuous-filter molecular dynamics | Molecular property prediction, 3D |
| **DimeNet** | Directional messages + angles | 3D molecular structures |
| **PointTransformerConv** | Transformer for 3D point clouds | 3D vision, segmentation |

### Hypergraph & Heterogeneous Convolutions

| Layer | Key Feature | Use For |
|-------|-------------|---------|
| **HypergraphConv** | Hyperedges (multi-node) | Multi-way relationships |
| **HGTConv** | Heterogeneous Graph Transformer | Multi-type networks, knowledge graphs |

## Aggregation Operators

| Aggregation | Class | Use Case | Example |
|-------------|-------|----------|---------|
| Sum | `SumAggregation` | Counting-sensitive | `SumAggregation()` |
| Mean | `MeanAggregation` | Degree-invariant | `MeanAggregation()` |
| Max | `MaxAggregation` | Salient features | `MaxAggregation()` |
| Softmax | `SoftmaxAggregation` | Learnable attention | `SoftmaxAggregation(learn=True)` |
| Power Mean | `PowerMeanAggregation` | Learnable power | `PowerMeanAggregation(learn=True)` |
| LSTM | `LSTMAggregation` | Sequential neighbors | `LSTMAggregation(in_ch, out_ch)` |
| Set Transformer | `SetTransformerAggregation` | Permutation-invariant | `SetTransformerAggregation(in_ch, out_ch)` |
| Multi | `MultiAggregation` | Combined signals | `MultiAggregation(['mean', 'max', 'std'])` |

## Pooling Layers

### Global Pooling (Node → Graph)

| Function/Class | Description | Example |
|----------------|-------------|---------|
| `global_mean_pool` | Average node features per graph | `global_mean_pool(x, batch)` |
| `global_max_pool` | Max over node features per graph | `global_max_pool(x, batch)` |
| `global_add_pool` | Sum node features per graph | `global_add_pool(x, batch)` |
| `global_sort_pool` | Sort + concat top-k nodes | `global_sort_pool(x, batch, k=30)` |
| `GlobalAttention` | Learnable attention weights | `GlobalAttention(gate_nn)` |
| `Set2Set` | LSTM-based attention | `Set2Set(in_channels, processing_steps=3)` |

### Hierarchical Pooling (Graph Coarsening)

| Class | Method | Example |
|-------|--------|---------|
| `TopKPooling` | Projection score ranking | `TopKPooling(in_channels, ratio=0.5)` |
| `SAGPooling` | Self-attention selection | `SAGPooling(in_channels, ratio=0.5)` |
| `ASAPooling` | Structure-aware selection | `ASAPooling(in_channels, ratio=0.5)` |
| `PANPooling` | Path attention | `PANPooling(in_channels, ratio=0.5)` |
| `EdgePooling` | Edge contraction | `EdgePooling(in_channels)` |
| `MemPooling` | Learnable cluster assignments | `MemPooling(in_ch, out_ch, heads=4, num_clusters=10)` |
| `avg_pool` / `max_pool` | Cluster-based pooling | `avg_pool(cluster, data)` |

## Normalization Layers

| Class | Description | Anti-Oversmoothing | Example |
|-------|-------------|-------------------|---------|
| `BatchNorm` | Across batch | No | `BatchNorm(in_channels)` |
| `LayerNorm` | Per sample | No | `LayerNorm(in_channels)` |
| `InstanceNorm` | Per sample + graph | No | `InstanceNorm(in_channels)` |
| `GraphNorm` | Graph-specific | No | `GraphNorm(in_channels)` |
| `PairNorm` | Pair-wise | **Yes** | `PairNorm(scale_individually=False)` |
| `MessageNorm` | Message normalization | Partially | `MessageNorm(learn_scale=True)` |
| `DiffGroupNorm` | Learnable grouping | No | `DiffGroupNorm(in_channels, groups=10)` |

## Pre-Built Model Architectures

### Complete GNN Models

| Model | Description | Example |
|-------|-------------|---------|
| `GCN` | Multi-layer GCN + dropout | `GCN(in_ch, hidden, num_layers, out_ch)` |
| `GraphSAGE` | Multi-layer SAGE + dropout | `GraphSAGE(in_ch, hidden, num_layers, out_ch)` |
| `GIN` | Graph Isomorphism Network | `GIN(in_ch, hidden, num_layers, out_ch)` |
| `GAT` | Multi-layer GAT + attention | `GAT(in_ch, hidden, num_layers, out_ch, heads=8)` |
| `PNA` | Multiple aggregators + scalers | `PNA(in_ch, hidden, num_layers, out_ch)` |
| `EdgeCNN` | Dynamic graph CNN | `EdgeCNN(out_channels, num_layers=3, k=20)` |

### Auto-Encoders

| Model | Description | Example |
|-------|-------------|---------|
| `GAE` | Graph Auto-Encoder | `GAE(encoder)` |
| `VGAE` | Variational GAE | `VGAE(encoder)` |
| `ARGA` | Adversarial GAE | `ARGA(encoder, discriminator)` |
| `ARGVA` | Adversarial VGAE | `ARGVA(encoder, discriminator)` |

### Knowledge Graph Embeddings

| Model | Method | Example |
|-------|--------|---------|
| `TransE` | Translating embeddings | `TransE(num_nodes, num_relations, hidden)` |
| `RotatE` | Complex rotation | `RotatE(num_nodes, num_relations, hidden)` |
| `ComplEx` | Complex-valued | `ComplEx(num_nodes, num_relations, hidden)` |
| `DistMult` | Bilinear diagonal | `DistMult(num_nodes, num_relations, hidden)` |

## Utility Layers

| Class | Description | Example |
|-------|-------------|---------|
| `Sequential` | Chain layers with named args | `Sequential('x, edge_index', [(GCNConv(16, 64), 'x, edge_index -> x'), ReLU()])` |
| `JumpingKnowledge` | Combine all layer outputs | `JumpingKnowledge(mode='cat')` — modes: cat, max, lstm |
| `DeepGCNLayer` | Deep GNN with skip connections | `DeepGCNLayer(conv, norm, act, block='res+', dropout=0.1)` |
| `MLP` | Multi-layer perceptron | `MLP([in_ch, 64, 64, out_ch], dropout=0.5)` |
| `Linear` | Lazy linear layer | `Linear(in_channels, out_channels, bias=True)` |

### Dense Layers (non-sparse graphs)

`DenseGCNConv`, `DenseSAGEConv`, `DenseGINConv`, `DenseGraphConv` — for small, fully-connected, or densely represented graphs.

---

## Transforms

Apply via `transform=` (each access), `pre_transform=` (once at processing), or inline `transform(data)`.

```python
from torch_geometric.transforms import Compose
transform = Compose([Transform1(), Transform2()])
```

### General Transforms

| Transform | Purpose | Key Parameters |
|-----------|---------|----------------|
| `NormalizeFeatures` | Row-normalize features to sum 1 | — |
| `ToDevice` | Transfer to CPU/GPU | `device` |
| `RandomNodeSplit` | Train/val/test node masks | `num_val`, `num_test`, `split` |
| `RandomLinkSplit` | Train/val/test edge splits | `num_val`, `num_test`, `is_undirected` |
| `IndexToMask` / `MaskToIndex` | Index ↔ boolean mask conversion | — |
| `FixedPoints` | Sample fixed number of points | `num`, `replace` |
| `ToDense` | Dense adjacency matrices | `num_nodes` |
| `ToSparseTensor` | edge_index → SparseTensor | `remove_edge_index` |

### Graph Structure Transforms

| Transform | Purpose | Key Parameters |
|-----------|---------|----------------|
| `ToUndirected` | Directed → undirected | `reduce='add'` |
| `AddSelfLoops` | Self-loops to all nodes | `fill_value` |
| `RemoveSelfLoops` | Remove self-loops | — |
| `RemoveIsolatedNodes` | Remove nodes without edges | — |
| `RemoveDuplicatedEdges` | Deduplicate edges | — |
| `LargestConnectedComponents` | Keep largest component(s) | `num_components` |
| `KNNGraph` | K-nearest neighbor edges | `k`, `loop`, `force_undirected` |
| `RadiusGraph` | Edges within radius | `r`, `loop`, `max_num_neighbors` |
| `Delaunay` | Delaunay triangulation | — |
| `FaceToEdge` | Mesh faces → edges | `remove_faces` |
| `LineGraph` | Graph → line graph | `force_directed` |
| `GDC` | Graph Diffusion Convolution | `diffusion_kwargs(method, alpha)` |
| `SIGN` | Multi-scale preprocessing | `K` (hops) |
| `VirtualNode` | Virtual node → all nodes | — |

### Feature Transforms

| Transform | Purpose | Key Parameters |
|-----------|---------|----------------|
| `OneHotDegree` | One-hot encode degree | `max_degree`, `cat` |
| `LocalDegreeProfile` | Structural node features | — |
| `Constant` | Add constant features | `value`, `cat` |
| `AddRandomWalkPE` | Random walk positional encoding | `walk_length` |
| `AddLaplacianEigenvectorPE` | Laplacian eigenvector PE | `k` (eigenvectors) |
| `AddMetaPaths` | Meta-path induced edges | `metapaths`, `drop_orig_edges` |
| `SVDFeatureReduction` | Dimensionality reduction | `out_channels` |

### Spatial / Vision Transforms

| Transform | Purpose | Key Parameters |
|-----------|---------|----------------|
| `Center` | Center node positions | — |
| `NormalizeScale` | Normalize to unit sphere | — |
| `NormalizeRotation` | Align to principal axes | `max_points` |
| `Distance` | Euclidean distance → edge_attr | `norm`, `cat` |
| `Cartesian` | Relative Cartesian → edge_attr | `norm`, `cat` |
| `Polar` | Polar coords → edge_attr | `norm`, `cat` |
| `Spherical` | Spherical coords → edge_attr | `norm`, `cat` |
| `LocalCartesian` | Local coordinate system | `norm`, `cat` |
| `PointPairFeatures` | Point pair features | `cat` |

### Data Augmentation

| Transform | Purpose | Key Parameters |
|-----------|---------|----------------|
| `RandomJitter` | Jitter positions | `translate` |
| `RandomFlip` | Flip along axis | `axis`, `p` |
| `RandomScale` | Scale positions | `scales (min, max)` |
| `RandomRotate` | Rotate positions | `degrees`, `axis` |
| `RandomShear` | Shear positions | `shear` |
| `RandomTranslate` | Translate positions | `translate` |
| `LinearTransformation` | Apply matrix transform | `matrix` |

### Mesh & Sampling

| Transform | Purpose | Key Parameters |
|-----------|---------|----------------|
| `SamplePoints` | Mesh → point cloud | `num`, `include_normals` |
| `GenerateMeshNormals` | Face/vertex normals | — |
| `GridSampling` | Voxel grid clustering | `size` |

### Specialized

| Transform | Purpose | Key Parameters |
|-----------|---------|----------------|
| `ToSLIC` | Image → superpixel graph | `num_segments`, `compactness` |
| `GCNNorm` | GCN-style edge normalization | `add_self_loops` |
| `LaplacianLambdaMax` | Largest Laplacian eigenvalue | `normalization` |

### Custom Transforms

```python
from torch_geometric.transforms import BaseTransform

class MyTransform(BaseTransform):
    def __init__(self, param):
        self.param = param
    def __call__(self, data):
        data.x = data.x * self.param
        return data
```

## Common Transform Combinations

```python
# Node classification
Compose([NormalizeFeatures(), RandomNodeSplit(num_val=0.1, num_test=0.2)])

# Point cloud processing
Compose([Center(), NormalizeScale(), RandomRotate(15, axis=2),
         RandomJitter(0.01), KNNGraph(k=6), Distance(norm=False)])

# Mesh → graph
Compose([FaceToEdge(remove_faces=True), GenerateMeshNormals(), Distance(norm=True)])

# Graph structure enhancement
Compose([ToUndirected(), AddSelfLoops(), RemoveIsolatedNodes(), GCNNorm()])

# Link prediction
Compose([NormalizeFeatures(), RandomLinkSplit(num_val=0.1, num_test=0.2, is_undirected=True)])
```

## Performance: pre_transform vs transform

**Expensive (use `pre_transform` — computed once):**
GDC, SIGN, KNNGraph (large), AddLaplacianEigenvectorPE, SVDFeatureReduction

**Cheap (use `transform` — computed each access):**
NormalizeFeatures, ToUndirected, AddSelfLoops, Random* augmentations, ToDevice

```python
dataset = Planetoid(root='/tmp/Cora', name='Cora',
                    pre_transform=GDC(self_loop_weight=1, normalization_in='sym',
                                      diffusion_kwargs=dict(method='ppr', alpha=0.15)),
                    transform=NormalizeFeatures())
```

## Layer Selection Tips

1. **Start simple**: GCNConv or GATConv for most tasks
2. **Molecular / 3D**: SchNet, DimeNet for 3D structures; NNConv for edge features
3. **Check capabilities**: Match layer flags (edge_weight, edge_attr, Bipartite) to data
4. **Deep networks**: Use PairNorm + JumpingKnowledge (prevents oversmoothing)
5. **Large graphs**: SAGEConv + ClusterGCNConv with NeighborLoader
6. **Heterogeneous**: RGCNConv, HGTConv, or `to_hetero()` conversion
7. **Lazy init**: Pass `-1` as `in_channels` when dimensions are unknown

Condensed from original: layers_reference.md (486 lines) + transforms_reference.md (680 lines) = 1,166 lines total. Retained: all 40+ convolutional layers with capability flags, all 8 aggregation operators, all pooling layers (global + hierarchical), all 7 normalization layers, pre-built models (GNN + auto-encoder + KG embeddings), utility layers (Sequential, JK, DeepGCN, MLP), dense layers, all transforms organized by category (general, structure, feature, spatial, augmentation, mesh, specialized), custom transform pattern, common combinations, performance guidance. Omitted: duplicate code examples (basic GNN, deep GNN patterns — relocated to SKILL.md Core API and Common Recipes), verbose prose introductions.
