# PyG Datasets Catalog

Comprehensive catalog of datasets available in `torch_geometric.datasets`, organized by domain.

## Citation Networks

| Dataset | Class | Nodes | Edges | Classes | Features | Use |
|---------|-------|-------|-------|---------|----------|-----|
| Cora | `Planetoid('Cora')` | 2,708 | 5,429 | 7 | 1,433 | Node classification baseline |
| CiteSeer | `Planetoid('CiteSeer')` | 3,327 | 4,732 | 6 | 3,703 | Node classification |
| PubMed | `Planetoid('PubMed')` | 19,717 | 44,338 | 3 | 500 | Node classification |
| CS | `Coauthor('CS')` | 18,333 | 81,894 | 15 | — | Co-authorship networks |
| Physics | `Coauthor('Physics')` | 34,493 | 247,962 | 5 | — | Co-authorship networks |
| Computers | `Amazon('Computers')` | 13,752 | 245,861 | 10 | — | Product co-purchase |
| Photo | `Amazon('Photo')` | 7,650 | 119,081 | 8 | — | Product co-purchase |

```python
from torch_geometric.datasets import Planetoid, Coauthor, Amazon, CitationFull

dataset = Planetoid(root='/tmp/Cora', name='Cora')
dataset = Coauthor(root='/tmp/CS', name='CS')
dataset = Amazon(root='/tmp/Computers', name='Computers')
dataset = CitationFull(root='/tmp/DBLP', name='DBLP')  # Full, unsampled
```

## Graph Classification (TUDataset)

120+ graph classification benchmarks via `TUDataset`:

| Dataset | Graphs | Classes | Domain | Features |
|---------|--------|---------|--------|----------|
| MUTAG | 188 | 2 | Molecular | Node + edge labels |
| PROTEINS | 1,113 | 2 | Protein structures | Node features |
| ENZYMES | 600 | 6 | Protein enzymes | Node features |
| IMDB-BINARY | 1,000 | 2 | Social | No node features |
| REDDIT-BINARY | 2,000 | 2 | Social | No node features |
| COLLAB | 5,000 | 3 | Scientific | No node features |
| NCI1 | 4,110 | 2 | Chemical | Node labels |
| DD | 1,178 | 2 | Protein | Node labels |

```python
from torch_geometric.datasets import TUDataset
dataset = TUDataset(root='/tmp/ENZYMES', name='ENZYMES')
print(f'{len(dataset)} graphs, {dataset.num_classes} classes')
print(f'Features: {dataset.num_node_features}')
```

## Molecular and Chemical

| Dataset | Class | Size | Task | Properties |
|---------|-------|------|------|------------|
| QM7b | `QM7b` | 7,211 | Regression | Atomization energies, electronic |
| QM8 | `QM8` | ~22K | Regression | Electronic properties |
| QM9 | `QM9` | ~130K | Regression | 19 quantum chemical (HOMO, LUMO, gap) |
| ZINC | `ZINC(subset=True)` | ~250K | Regression | Solubility, molecular weight |
| AQSOL | `AQSOL` | ~10K | Regression | Aqueous solubility |
| MD17 | `MD17(name='benzene')` | Varies | Regression | MD trajectories, forces |
| PCQM4Mv2 | `PCQM4Mv2` | 3.8M | Regression | OGB Large-Scale Challenge |

```python
from torch_geometric.datasets import QM9, ZINC, MoleculeNet

dataset = QM9(root='/tmp/QM9')
print(f'{len(dataset)} molecules, {dataset[0].y.shape[1]} properties')

dataset = ZINC(root='/tmp/ZINC', subset=True)  # 12K subset for fast experiments

# MoleculeNet: 10+ molecular benchmarks
# ESOL, FreeSolv, Lipophilicity (regression)
# BACE, BBBP, HIV, Tox21, ToxCast, SIDER, ClinTox (classification)
dataset = MoleculeNet(root='/tmp/HIV', name='HIV')
```

## Social Networks

| Dataset | Class | Nodes | Edges | Classes |
|---------|-------|-------|-------|---------|
| Reddit | `Reddit` | 232,965 | 11.6M | 41 |
| Reddit2 | `Reddit2` | Updated | — | — |
| Twitch (DE/EN/ES/FR/PT/RU) | `Twitch('DE')` | Varies | — | 2 |
| Facebook | `FacebookPagePage` | — | — | — |
| GitHub | `GitHub` | — | — | — |

```python
from torch_geometric.datasets import Reddit, Twitch
dataset = Reddit(root='/tmp/Reddit')  # Large-scale: use NeighborLoader
dataset = Twitch(root='/tmp/Twitch', name='DE')
```

## Knowledge Graphs

| Dataset | Class | Entities | Relations | Triplets |
|---------|-------|----------|-----------|----------|
| AIFB/MUTAG/BGS/AM | `Entities('AIFB')` | Varies | Typed | RDF graphs |
| WordNet18 | `WordNet18` | 40,943 | 18 | 151,442 |
| WordNet18RR | `WordNet18RR` | — | No inverse | — |
| FB15k-237 | `FB15k_237` | 14,541 | 237 | 310,116 |

```python
from torch_geometric.datasets import Entities, WordNet18RR, FB15k_237
dataset = FB15k_237(root='/tmp/FB15k')
```

## Heterogeneous Graphs

| Dataset | Class | Node Types | Use |
|---------|-------|------------|-----|
| OGB_MAG | `OGB_MAG` | paper, author, institution, field | Node classification |
| MovieLens | `MovieLens('100k')` | user, movie | Recommendation |
| IMDB | `IMDB` | movie, actor, director | Heterogeneous learning |
| DBLP | `DBLP` | author, paper, term, conference | Node classification |
| LastFM | `LastFM` | user, artist, tag | Recommendation |

```python
from torch_geometric.datasets import OGB_MAG, IMDB, DBLP
dataset = DBLP(root='/tmp/DBLP')
print(dataset[0].node_types)   # ['author', 'paper', 'term', 'conference']
print(dataset[0].edge_types)   # List of (src, rel, dst) tuples
```

## Temporal Graphs

| Dataset | Class | Use |
|---------|-------|-----|
| BitcoinOTC | `BitcoinOTC` | Temporal link prediction, trust |
| ICEWS18 | `ICEWS18` | Temporal knowledge graph completion |
| GDELT | `GDELT` | Event forecasting |
| JODIE (Reddit/Wikipedia/MOOC/LastFM) | `JODIEDataset('Reddit')` | Dynamic interaction networks |

```python
from torch_geometric.datasets import JODIEDataset
dataset = JODIEDataset(root='/tmp/JODIE', name='Reddit')
```

## 3D Meshes and Point Clouds

| Dataset | Class | Size | Use |
|---------|-------|------|-----|
| ShapeNet | `ShapeNet(categories=['Airplane'])` | 16,881 models, 16 cats | Shape segmentation |
| ModelNet10/40 | `ModelNet('10')` | 4,899 / 12,311 | 3D classification |
| FAUST | `FAUST` | 100 meshes (10 people x 10 poses) | Shape matching |
| CoMA | `CoMA` | 20,466 face scans | Mesh deformation |
| S3DIS | `S3DIS(test_area=6)` | 271 rooms, 6 areas | 3D semantic segmentation |

```python
from torch_geometric.datasets import ShapeNet, ModelNet
dataset = ShapeNet(root='/tmp/ShapeNet', categories=['Airplane'])
dataset = ModelNet(root='/tmp/ModelNet', name='10')
```

## Image and Vision

```python
from torch_geometric.datasets import MNISTSuperpixels, Flickr, PPI

# MNIST as superpixel graphs (70K graphs)
dataset = MNISTSuperpixels(root='/tmp/MNIST')

# Flickr image network (89K nodes, 900K edges)
dataset = Flickr(root='/tmp/Flickr')

# PPI: protein-protein interaction (24 graphs, multi-label)
dataset = PPI(root='/tmp/PPI', split='train')
```

## Open Graph Benchmark (OGB)

### Node Property Prediction
- **ogbn-products** — Amazon products (2.4M nodes)
- **ogbn-proteins** — Protein associations (132K nodes)
- **ogbn-arxiv** — Citation network (169K nodes)
- **ogbn-papers100M** — Large citations (111M nodes)
- **ogbn-mag** — Heterogeneous academic graph

### Link Property Prediction
- **ogbl-ppa** — Protein associations
- **ogbl-collab** — Collaboration networks
- **ogbl-ddi** — Drug-drug interactions
- **ogbl-citation2** — Citation network
- **ogbl-wikikg2** — Wikidata knowledge graph

### Graph Property Prediction
- **ogbg-molhiv** — Molecular HIV activity
- **ogbg-molpcba** — Molecular bioassays (multi-task)
- **ogbg-ppa** — Protein function
- **ogbg-code2** — Code ASTs

```python
# PyG native OGB access
from torch_geometric.datasets import OGB_MAG

# Standard OGB access (pip install ogb)
from ogb.nodeproppred import PygNodePropPredDataset
dataset = PygNodePropPredDataset(name='ogbn-arxiv')
split_idx = dataset.get_idx_split()  # train/valid/test indices
```

## Synthetic and Small Datasets

```python
from torch_geometric.datasets import KarateClub, FakeDataset, StochasticBlockModelDataset

# Zachary's karate club (34 nodes, 78 edges, 2 communities)
dataset = KarateClub()

# Random graphs for testing/debugging
dataset = FakeDataset(num_graphs=100, avg_num_nodes=50)

# Stochastic block model for community detection
dataset = StochasticBlockModelDataset(root='/tmp/SBM', num_graphs=1000)
```

## Dataset Usage Patterns

### Loading with Transforms

```python
from torch_geometric.datasets import Planetoid
from torch_geometric.transforms import NormalizeFeatures
dataset = Planetoid(root='/tmp/Cora', name='Cora', transform=NormalizeFeatures())
```

### Train/Val/Test Splits

```python
# Node classification: use pre-defined masks
data = dataset[0]
train_x = data.x[data.train_mask]

# Graph classification: index-based split
train_dataset = dataset[:int(0.8 * len(dataset))]
test_dataset = dataset[int(0.8 * len(dataset)):]

from torch_geometric.loader import DataLoader
train_loader = DataLoader(train_dataset, batch_size=32, shuffle=True)
```

### Custom Dataset

```python
from torch_geometric.data import Data, InMemoryDataset

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
        # Build Data objects from raw files...
        edge_index = torch.tensor([[0,1],[1,0]], dtype=torch.long)
        data_list.append(Data(x=torch.randn(2,16), edge_index=edge_index, y=torch.tensor([0])))
        if self.pre_filter is not None:
            data_list = [d for d in data_list if self.pre_filter(d)]
        if self.pre_transform is not None:
            data_list = [self.pre_transform(d) for d in data_list]
        self.save(data_list, self.processed_paths[0])
```

## Dataset Selection Guide

| Task | Start With | Scale Up To |
|------|-----------|-------------|
| Node classification (prototype) | Cora, CiteSeer (Planetoid) | Reddit, ogbn-arxiv |
| Graph classification | ENZYMES, MUTAG (TUDataset) | ogbg-molhiv |
| Molecular properties | QM9, ZINC | MoleculeNet, PCQM4Mv2 |
| Knowledge graphs | FB15k-237, WordNet18RR | ogbl-wikikg2 |
| Heterogeneous graphs | DBLP, IMDB | OGB_MAG |
| 3D / point clouds | ModelNet10, ShapeNet | S3DIS |
| Temporal | JODIEDataset('Reddit') | GDELT |
| Link prediction | Cora + RandomLinkSplit | ogbl-collab |

Condensed from original: datasets_reference.md (575 lines). Retained: all dataset categories (citation, graph classification, molecular, social, knowledge graph, heterogeneous, temporal, 3D, image/vision, OGB, synthetic), per-dataset statistics and class names, loading code for every category, train/val/test split patterns, custom dataset template, dataset selection guide. Omitted: STRING dataset (no PyG class, requires custom loading), duplicate PPI listing, redundant import statements per dataset, verbose descriptions already summarized in tables.
