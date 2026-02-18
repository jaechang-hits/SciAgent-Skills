# AutoDock Vina Scoring Functions Comparison

Reference for choosing between Vina, Vinardo, and AD4 scoring functions.

## Available Scoring Functions

| Scoring Function | Speed | Accuracy (general) | Best For |
|-----------------|-------|--------------------|---------|
| **Vina** | Fast | Good | General-purpose docking, virtual screening |
| **Vinardo** | Fast | Better for some targets | Updated parameterization, diverse chemotypes |
| **AD4** (AutoDock 4.2) | Moderate | Good with grid maps | Legacy workflows, metalloprotein targets |

## Vina (Default)

```python
v = Vina(sf_name="vina")
```

- **Energy terms**: Gauss1, Gauss2, Repulsion, Hydrophobic, Hydrogen bonding
- **Strengths**: Fastest, most widely benchmarked, good for standard drug-like molecules
- **Weaknesses**: No explicit metal coordination term, limited handling of halogen bonds
- **Use when**: Default choice for most docking tasks

## Vinardo

```python
v = Vina(sf_name="vinardo")
```

- **Energy terms**: Re-parameterized from Vina with additional training data
- **Strengths**: Better performance on diverse compound sets in some benchmarks
- **Weaknesses**: Less extensively benchmarked than Vina
- **Use when**: Docking structurally diverse libraries, or when Vina gives poor re-docking RMSD

## AD4 (AutoDock 4.2)

```python
v = Vina(sf_name="ad4")
```

- **Energy terms**: van der Waals, hydrogen bonding, electrostatics, desolvation, torsional entropy
- **Strengths**: Explicit electrostatic term, better for charged ligands and metalloproteins
- **Weaknesses**: Requires pre-computed affinity maps, slower than Vina/Vinardo
- **Use when**:
  - Metal-containing binding sites (Zn²⁺, Mg²⁺)
  - Highly charged ligands
  - Reproducing published AD4 results

**Note**: AD4 requires separate map generation:
```python
from vina import Vina
v = Vina(sf_name="ad4")
v.set_receptor(receptor_pdbqt)
v.compute_vina_maps(center=[x, y, z], box_size=[sx, sy, sz])
# This generates .map files automatically
```

## Benchmark Comparison

From published benchmarks (Eberhardt et al. 2021, CASF-2016 dataset):

| Metric | Vina | Vinardo | AD4 |
|--------|------|---------|-----|
| Docking success rate (RMSD <2Å) | ~70% | ~72% | ~68% |
| Scoring power (R²) | 0.56 | 0.54 | 0.53 |
| Screening power (EF1%) | 23.0 | 22.5 | 21.0 |
| Speed (poses/sec) | Fastest | Fast | Moderate |

**Note**: These numbers vary significantly by target class. Always validate with your specific system.

## Consensus Scoring Strategy

For higher confidence, dock with multiple scoring functions and select compounds ranked well by ≥2 functions:

```python
consensus = {}
for sf in ["vina", "vinardo"]:
    v = Vina(sf_name=sf, cpu=2)
    v.set_receptor(receptor_pdbqt)
    v.set_ligand_from_file(ligand_pdbqt)
    v.compute_vina_maps(center=center, box_size=box_size)
    v.dock(exhaustiveness=16, n_poses=1)
    consensus[sf] = v.energies(n_poses=1)[0][0]

avg_score = sum(consensus.values()) / len(consensus)
print(f"Consensus score: {avg_score:.2f} kcal/mol")
```

## Recommendations by Target Class

| Target Class | Recommended SF | Rationale |
|-------------|---------------|-----------|
| Kinases | Vina or Vinardo | Standard drug-like molecules, hinge binding |
| Metalloproteases (Zn²⁺) | AD4 | Explicit electrostatic term for metal coordination |
| GPCRs | Vina + Vinardo consensus | Diverse binding sites, benefit from consensus |
| Nuclear receptors | Vina | Hydrophobic pockets, Vina well-parameterized |
| Proteases (Ser/Cys) | Vina | Standard H-bond interactions |
| Allosteric sites | Vinardo | Often structurally diverse binders |
