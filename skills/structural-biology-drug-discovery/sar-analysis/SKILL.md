---
name: sar-analysis
description: "Structure-Activity Relationship (SAR) analysis with RDKit: scaffold detection via MCS, R-group decomposition, aligned visualization, activity heatmaps, interpretive SAR output. For general cheminformatics see rdkit-cheminformatics; for bioactivity see chembl-database-bioactivity."
license: CC-BY-4.0
---

# SAR Analysis

## Overview

Structure-Activity Relationship (SAR) analysis is a foundational technique in medicinal chemistry that systematically relates chemical modifications to changes in biological activity. By identifying a common scaffold across a compound series and decomposing each molecule into its core and variable substituents (R-groups), SAR analysis reveals which structural features drive potency, selectivity, and other pharmacological properties. This guide covers the complete computational SAR workflow using RDKit: from automatic core identification through MCS, to R-group decomposition, aligned molecular visualization, interactive HTML report generation with activity heatmaps, and interpretive SAR text output.

## Key Concepts

### Maximum Common Substructure (MCS)

The Maximum Common Substructure is the largest substructure shared by all (or a threshold fraction of) molecules in a dataset. In SAR analysis, MCS serves as the automatic scaffold detection method. RDKit provides `rdFMCS.FindMCS` which accepts parameters controlling match stringency: `threshold` (fraction of molecules that must contain the substructure), `ringMatchesRingOnly` (ring atoms match only ring atoms), `completeRingsOnly` (partial ring matches are disallowed), and atom/bond comparison modes. The MCS result is returned as a SMARTS string that can be converted to a molecule object for downstream use.

```python
from rdkit.Chem import rdFMCS, AllChem, Chem

mols_for_mcs = [Chem.AddHs(m) for m in mols]
mcs_res = rdFMCS.FindMCS(
    mols_for_mcs,
    threshold=0.8,
    ringMatchesRingOnly=True,
    completeRingsOnly=True,
    atomCompare=rdFMCS.AtomCompare.CompareElements,
    bondCompare=rdFMCS.BondCompare.CompareOrder
)
core_mol = Chem.MolFromSmarts(mcs_res.smartsString)
AllChem.Compute2DCoords(core_mol)
```

### R-Group Decomposition

R-group decomposition breaks each molecule into the common core scaffold and its variable substituents at defined attachment points. RDKit's `rdRGroupDecomposition.RGroupDecompose` takes the core molecule and a list of target molecules, returning a dictionary mapping each R-group position (R1, R2, etc.) to its fragment for each compound. After decomposition, constant R-groups (identical across all molecules) should be excluded from the analysis since they carry no SAR information. These constant positions should also be visually merged back into the core representation.

```python
from rdkit.Chem import rdRGroupDecomposition

matches, unmatched_indices = rdRGroupDecomposition.RGroupDecompose(
    [core_mol], mols, asSmiles=False, asRows=False
)
```

### Molecular Alignment and Visualization

Proper molecular alignment ensures that the core scaffold and R-group fragments are visually superimposed on the parent molecule, making structural comparisons intuitive. RDKit's `GenerateDepictionMatching2DStructure` aligns a molecule's 2D coordinates to match a template (the core). For fragments, coordinate extraction from the parent molecule guarantees pixel-perfect overlay. SVG output is preferred over raster formats for resolution independence and scalability in HTML reports.

```python
from rdkit.Chem.Draw import rdMolDraw2D

drawer = rdMolDraw2D.MolDraw2DSVG(-1, -1)
rdMolDraw2D.DrawMoleculeACS1996(drawer, mol)
drawer.FinishDrawing()
svg = drawer.GetDrawingText()

svg = svg.replace("width='", "width='100%' data-original-width='")
svg = svg.replace("height='", "height='100%' data-original-height='")
```

### Activity Heatmaps

Activity heatmaps apply color gradients to activity values in a tabular report, providing an immediate visual summary of potency trends across the compound series. A logarithmic scale is typically used because biological activity values (IC50, EC50, Ki) often span several orders of magnitude. The conventional color scheme maps green to high potency (low IC50 values) and red to low potency (high IC50 values), aligning with the medicinal chemistry convention that lower values indicate more active compounds.

## Decision Framework

When setting up a SAR analysis, the first decision is how to define the core scaffold:

```
Question: How do you define the common scaffold?
|-- Compound series is congeneric (shared ring system)
|   |-- >80% share the same core -> MCS with threshold=0.8
|   |-- 60-80% share the same core -> MCS with threshold=0.6
|   +-- <60% share a core -> Manual scaffold or cluster first
|-- You have a known pharmacophore scaffold
|   +-- Use manual SMARTS definition
+-- Highly diverse set with no obvious shared core
    +-- Cluster by fingerprint similarity first, then MCS per cluster
```

| Scenario | Recommended Approach | Rationale |
|----------|---------------------|-----------|
| Congeneric series (>10 compounds, shared ring system) | MCS with `threshold=0.8`, `completeRingsOnly=True` | Automatic detection avoids manual bias; high threshold ensures meaningful core |
| Small series (<10 compounds) | MCS with `threshold=1.0` or manual scaffold | Every compound must match; manual review is feasible |
| Known target with published scaffold | Manual SMARTS-defined core | Preserves medicinal chemistry knowledge; avoids MCS finding a suboptimal core |
| Mixed scaffolds in one dataset | Cluster by Tanimoto similarity, then per-cluster MCS | Prevents MCS from returning a trivially small common fragment |
| MCS returns a very small fragment (<6 heavy atoms) | Lower threshold or switch to manual scaffold | A tiny MCS lacks SAR interpretive value |
| Ring-open / ring-closed analogue pairs | Set `ringMatchesRingOnly=False` | Allows matching of ring atoms to non-ring atoms across the pair |

## Best Practices

1. **Pre-process molecules with explicit hydrogens before MCS**: Apply `Chem.AddHs` to all molecules before calling `FindMCS`. This ensures hydrogen-bearing positions are correctly identified as substitution points, preventing missed R-groups in the decomposition step.

2. **Remove constant R-groups from the analysis**: After R-group decomposition, identify columns where every molecule has the identical substituent. Exclude these from both the data table and the core visualization. Constant R-groups add visual clutter without contributing SAR insight.

3. **Align all molecules to the core template before generating images**: Use `AllChem.GenerateDepictionMatching2DStructure(mol, core_mol)` for each molecule. Then extract coordinates from the aligned parent molecule to position fragments. This guarantees visual consistency across the entire report.

4. **Use SVG output with DrawMoleculeACS1996 for publication-quality rendering**: SVG scales without pixelation and integrates cleanly into HTML reports. The ACS 1996 drawing style produces structures that conform to American Chemical Society publication standards, with proper bond lengths and atom label sizes.

5. **Apply logarithmic scaling for activity heatmaps**: Biological activity values often span orders of magnitude. Linear color mapping compresses the interesting range; log-scale mapping distributes colors more evenly across the potency spectrum, making subtle differences visible.

6. **Set minimum column widths of 300px for structure images in HTML tables**: Molecular structures become unreadable when compressed into narrow table cells. Enforce `min-width: 300px` on columns containing SVG or image content to maintain legibility.

7. **Validate image generation before embedding**: Check that each SVG or Base64 image string is non-empty and well-formed before inserting it into the HTML table. Use a text placeholder (e.g., "No Image") for any failed rendering to prevent broken layout.

8. **Always include compound identifiers in SAR text analysis**: Reference specific compound IDs when describing activity trends (e.g., "Compound 7, R1=F, IC50=0.5 uM showed 10-fold improvement over Compound 1"). Unnamed claims about substituent effects are not verifiable.

## Common Pitfalls

1. **MCS returns a trivially small fragment (e.g., a single ring or chain)**: This happens when the compound set is too structurally diverse for the chosen threshold, or when `completeRingsOnly` is not set.
   - *How to avoid*: Inspect the MCS result before proceeding. If the core has fewer than 6 heavy atoms, either lower the threshold parameter, pre-cluster the molecules by fingerprint similarity and run MCS per cluster, or define the scaffold manually.

2. **R-group decomposition fails silently for some molecules**: Molecules that do not match the core are returned in `unmatched_indices` but no error is raised, leading to incomplete reports.
   - *How to avoid*: Always check `unmatched_indices` after `RGroupDecompose`. Log which molecules failed to match and report them separately. Consider whether the core definition needs adjustment.

3. **Misaligned structures in the HTML report**: Fragments appear shifted or rotated relative to the parent molecule because independent 2D coordinate generation was used instead of coordinate extraction.
   - *How to avoid*: Use the `align_substructure_to_parent` function (see Workflow Step 4) to copy atom positions from the aligned parent molecule to each fragment. Never call `Compute2DCoords` independently on fragments that should overlay the parent.

4. **Activity heatmap colors are misleading due to linear scaling**: When activity values range from 1 nM to 100 uM, linear color mapping assigns nearly identical colors to 1 nM and 100 nM (both near the green end), obscuring meaningful differences.
   - *How to avoid*: Apply `math.log10` or `numpy.log10` to activity values before mapping to the color gradient. Verify the color scale by checking that the most and least potent compounds receive clearly distinct colors.

5. **Forgetting to handle dummy atoms in substructure matching**: R-group fragments contain dummy atoms (`[*]`, `[#0]`) at attachment points. Standard substructure matching does not recognize these, causing alignment failures.
   - *How to avoid*: Use `Chem.AdjustQueryParameters` with `makeDummiesQueries=True` as a fallback matching strategy. Implement a multi-strategy alignment approach (direct match, then dummy-adjusted match, then chirality-relaxed match).

6. **Unsupported SAR claims in the text analysis**: Stating that a substituent "improves activity" without contrasting it against other substituents at the same position is a common analytical error.
   - *How to avoid*: For every SAR claim, explicitly name at least two compounds being compared, their R-group differences at a single position, and their measured activity values. If no direct comparison exists, flag the gap and suggest an analogue to synthesize.

7. **HTML report breaks with special characters in compound names or SMILES**: Unescaped angle brackets, ampersands, or quotes in data fields corrupt the HTML structure.
   - *How to avoid*: HTML-escape all text content before embedding in the report. Use Python's `html.escape()` on compound names and any text fields inserted into the HTML template.

## Workflow

### Step 1: Data Loading and Column Identification

Load the CSV file and automatically identify the relevant columns. Do not assume fixed column names. Inspect the dataframe (e.g., using `df.head()` and `df.columns`) to detect columns for:

- **Compound Key**: Look for columns named "Compound Key", "ID", "Name", "Compound_ID", or similar.
- **Activity**: Look for columns named "Standard Value", "IC50", "EC50", "Ki", "Activity", or similar.
- **SMILES**: Look for columns named "Smiles", "SMILES", "Structure", "canonical_smiles", or similar.

Processing steps:

- Parse each SMILES string into an RDKit molecule object with `Chem.MolFromSmiles`.
- Drop rows where SMILES parsing fails and log a warning for each dropped compound.
- Verify that activity values are numeric; convert string representations if needed.
- Decision point: If fewer than 3 valid molecules remain, abort with a descriptive error message listing the parsing failures.

### Step 2: Core Identification via MCS

Find the Maximum Common Substructure across the molecule set.

- Add explicit hydrogens to all molecules: `mols_h = [Chem.AddHs(m) for m in mols]`.
- Call `rdFMCS.FindMCS` with appropriate parameters (see Key Concepts for the full parameter set).
- Inspect `mcs_res.numAtoms` and `mcs_res.smartsString` to verify the result is chemically meaningful.
- Convert the SMARTS result to a molecule: `core_mol = Chem.MolFromSmarts(mcs_res.smartsString)`.
- Generate 2D coordinates for the core: `AllChem.Compute2DCoords(core_mol)`.
- Decision point: If `mcs_res.numAtoms < 6`, the core may be too small for meaningful SAR. Consider lowering the threshold, pre-clustering the molecules, or defining the scaffold manually via SMARTS.

### Step 3: R-Group Decomposition and Refinement

Decompose each molecule relative to the identified core.

- Call `rdRGroupDecomposition.RGroupDecompose([core_mol], mols, asSmiles=False, asRows=False)`.
- Check `unmatched_indices` and log any molecules that failed to decompose. Report these separately in the final output.
- Iterate over the R-group columns (R1, R2, R3, etc.) and identify constant columns where all molecules have the identical substituent.
- Remove constant R-group columns from the analysis table.
- Optionally update the core visualization to incorporate the constant substituent positions, producing a "decorated core" that better represents the fixed parts of the scaffold.
- Decision point: If all R-group columns are constant, the compound set may lack meaningful structural variation for SAR analysis.

### Step 4: Molecular Alignment and Image Generation

Align all structures for consistent visual presentation.

- Align each original molecule to the core template:
  ```python
  try:
      AllChem.GenerateDepictionMatching2DStructure(m, core_mol)
  except:
      AllChem.Compute2DCoords(m)
  ```
- For each fragment (core instance, R-groups), extract coordinates from the aligned parent:
  ```python
  def align_substructure_to_parent(sub, parent):
      if not sub or not parent: return False
      try:
          # Strategy 1: Direct match
          match = parent.GetSubstructMatch(sub)

          # Strategy 2: Convert dummies to queries (handle R-group attachment points)
          if not match:
              params = Chem.AdjustQueryParameters()
              params.makeDummiesQueries = True
              params.adjustDegree = False
              params.adjustRingCount = False
              sub_query = Chem.AdjustQueryProperties(sub, params)
              match = parent.GetSubstructMatch(sub_query)

          # Strategy 3: Try without chirality
          if not match:
               match = parent.GetSubstructMatch(sub, useChirality=False)

          if match:
              conf_parent = parent.GetConformer()
              conf_sub = Chem.Conformer(sub.GetNumAtoms())
              for sub_idx, parent_idx in enumerate(match):
                  pos = conf_parent.GetAtomPosition(parent_idx)
                  conf_sub.SetAtomPosition(sub_idx, pos)

              sub.RemoveAllConformers()
              sub.AddConformer(conf_sub)
              return True
      except:
          pass
      return False
  ```
- Render each molecule and fragment to SVG using `DrawMoleculeACS1996`.
- Validate that each SVG string is non-empty before embedding.

### Step 5: HTML Report Generation

Build an interactive HTML report (`sar_analysis_report.html`).

**Table structure:**
- Columns: Compound Key, Activity, Original Molecule, Core, and one column per variable R-group.
- Each image column should have `min-width: 300px` in CSS so structures remain legible.
- Activity cells receive a background color from the heatmap gradient.

**Activity heatmap:**
- Compute `log10(activity)` for each compound to establish the color scale range.
- Map the log-transformed values to a green-to-red gradient (green = low value = high potency, red = high value = low potency).
- Apply the computed color as an inline `background-color` style on each Activity cell.

**Image embedding:**
- Insert validated SVG strings directly into `<td>` elements.
- For any molecule where SVG generation failed, insert a text placeholder: `<td>No Image</td>`.
- HTML-escape all text content (compound names, SMILES) before embedding.

**Interactive sorting:**
- Add a "Toggle Sort Order" button at the top of the page.
- Implement with client-side JavaScript that cycles through three views: Default View (original CSV order), Activity Ascending (low to high), and Activity Descending (high to low).
- Parse Activity column values as floating-point numbers for correct numeric sorting.

**Styling:**
- Use modern CSS: subtle box shadows on the table, clean sans-serif typography, alternating row colors, responsive layout with horizontal scroll for wide tables.
- Include a brief text summary of observed SAR trends at the top or bottom of the report.

### Step 6: SAR Text Analysis

Generate a concise, interpretive SAR report printed directly in the conversation (do not save to a file).

**Opening statement:**
- Begin with a single sentence summarizing the main structural modifications and the key finding.
- Be direct: do not use conversational openings like "I will analyze..." or "Here is the analysis...".

**Scaffold and substituents:**
- Describe the common core structure identified in Step 2.
- Label variable positions consistently as R1, R2, etc., matching the R-group decomposition output.

**Comparative analysis (critical requirement):**
- For every activity trend claim, explicitly contrast at least two compounds with different substituents at the same position.
- Include compound IDs and measured activity values in every comparison.
- Example format: "Compound 7 (R1=F, IC50=0.5 uM) showed a 10-fold improvement over Compound 1 (R1=Me, IC50=5.2 uM), suggesting steric constraints at the R1 pocket."

**Mechanistic inference:**
- Propose plausible reasons for activity changes, considering steric, electronic, and intermolecular interaction effects (H-bonding, hydrophobic contacts, pi-stacking).
- Use speculative but precise language (e.g., "suggests that...", "likely due to...").

**Data completeness evaluation:**
- Assess whether the dataset has gaps that prevent robust conclusions.
- If a key comparison is missing, propose a specific analogue to synthesize:
  1. Identify the ambiguity (which compound and data point create uncertainty).
  2. State the missing counterpart (what comparison is needed but unavailable).
  3. Propose the solution (the exact analogue that would resolve the ambiguity).

**Conclusion and follow-up:**
- Summarize key SAR findings and identify the most promising analogue(s).
- Include a "Suggestions for Further Study" section. Either propose specific analogues with justification, or state: "The provided analogues offer sufficient comparative data for a robust initial SAR analysis at the explored positions."
- End with a direct question to the user suggesting a concrete next step (e.g., "Would you like me to design a synthesis pathway for the proposed analogue?").

## Further Reading

- [RDKit Documentation](https://www.rdkit.org/docs/) -- Comprehensive reference for all RDKit modules including Chem, AllChem, Draw, and descriptor calculation
- [rdFMCS Module Documentation](https://www.rdkit.org/docs/source/rdkit.Chem.rdFMCS.html) -- Detailed API reference for Maximum Common Substructure finding, including all parameter options and algorithm details
- [R-Group Decomposition in RDKit](https://www.rdkit.org/docs/source/rdkit.Chem.rdRGroupDecomposition.html) -- API reference for the R-group decomposition module with usage examples
- [Matched Molecular Pair Analysis and SAR Transfer (Griffen et al., 2011)](https://doi.org/10.1021/jm200452d) -- Seminal paper on systematic SAR analysis methodologies in drug discovery
- [Getting Started with the RDKit in Python](https://www.rdkit.org/docs/GettingStartedInPython.html) -- Tutorial covering molecule manipulation, substructure searching, and visualization fundamentals

## Related Skills

- `rdkit-cheminformatics` -- General-purpose cheminformatics operations including descriptor calculation, fingerprinting, similarity searching, and molecular file I/O
- `chembl-database-bioactivity` -- Retrieving bioactivity data from ChEMBL for use as input to SAR analysis, including IC50, EC50, and Ki values for compound series
