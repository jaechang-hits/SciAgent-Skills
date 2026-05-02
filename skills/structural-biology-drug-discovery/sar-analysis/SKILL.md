---
name: sar-analysis
description: Structure-activity relationship (SAR) analysis guide for drug discovery including molecular descriptor analysis, scaffold analysis, and activity cliff detection.
license: open
---

# SAR Analysis

---

## Metadata

**Short Description**: Comprehensive guide for performing Structure-Activity Relationship (SAR) analysis using RDKit.

**Authors**: Ohagent Team

**Version**: 1.0

**Last Updated**: December 2025

**License**: CC BY 4.0

**Commercial Use**: ✅ Allowed

---

## Overview

Structure-Activity Relationship (SAR) analysis is a core medicinal-chemistry workflow that relates systematic structural variations of a chemical series to changes in biological activity. The goal is to (1) identify a common scaffold (Maximum Common Substructure, MCS) shared by a series of analogues, (2) decompose each molecule into the scaffold plus its R-group substituents, (3) align all molecules so substituents at equivalent positions are visually comparable, and (4) connect substituent variation to potency to derive testable design hypotheses.

This guide formalizes a reproducible RDKit-based SAR workflow that produces an interactive HTML report (compound table with aligned core/R-groups and an activity heatmap) and a written SAR narrative that explicitly contrasts substituents at the same R-position. It is intended for use on activity tables containing SMILES, a compound identifier, and a numeric potency value (IC50, Ki, EC50, %inhibition, etc.).

## Key Concepts

### Maximum Common Substructure (MCS)

MCS is the largest connected substructure shared by all (or a configurable threshold of) molecules in a set. RDKit's `rdFMCS.FindMCS` searches for this scaffold under tunable atom/bond comparison rules. For SAR, MCS provides the anchor template against which every analogue is decomposed and aligned. A `threshold=0.8` allows MCS to be defined when only 80% of molecules contain the candidate substructure, which is more robust to outliers than `threshold=1.0`. `ringMatchesRingOnly=True` and `completeRingsOnly=True` prevent partial-ring fragments that look chemically meaningless.

### R-Group Decomposition

R-group decomposition (`rdRGroupDecomposition.RGroupDecompose`) maps each molecule onto the MCS core and assigns the non-core fragments to enumerated R-positions (R1, R2, …). The output is a per-molecule dictionary `{Core, R1, R2, …}`. Constant R-positions (where every molecule carries the same fragment) are uninformative for SAR and should be pruned from the report so attention focuses on the variable positions that actually drive activity.

### Substructure Alignment for Comparable 2D Depiction

For SAR visualization to be interpretable, the core and each R-group must be drawn in the same orientation as the parent molecule. The recommended pattern uses three fall-back strategies in order: (1) a direct `GetSubstructMatch`, (2) a re-match after `AdjustQueryProperties(makeDummiesQueries=True)` so R-group dummy atoms are treated as queries, and (3) a final attempt with `useChirality=False`. Once a match is found, atom coordinates are copied from the parent conformer onto the fragment. Without this, R-group cells are drawn in arbitrary canonical orientations and visual SAR is essentially impossible to read.

### Activity Heatmap and Comparative Analysis

A logarithmic-scale color gradient (green = high potency / low IC50, red = low potency / high IC50) on the activity column lets a reader spot trends across the series at a glance. The accompanying narrative must justify every claim about a substituent's effect by *explicit pairwise contrast at the same R-position* — the unit of SAR evidence is "compound A (R1=X, IC50=…) vs compound B (R1=Y, IC50=…)", never an unsupported generalization.

## Decision Framework

```
SAR analysis pipeline
└── Have SMILES + activity for >= 4 analogues?
    ├── No  -> Insufficient data; collect more analogues first
    └── Yes -> Run rdFMCS.FindMCS(threshold=0.8, ringMatchesRingOnly=True)
        ├── MCS too small (<5 atoms) -> Series is too diverse;
        │                               cluster first, then run SAR per cluster
        └── MCS reasonable -> RGroupDecompose
            └── For each fragment alignment to parent:
                ├── Strategy 1: GetSubstructMatch(direct)  -- works for canonical cases
                │   └── No match -> Strategy 2
                ├── Strategy 2: AdjustQueryProperties(makeDummiesQueries=True)
                │               -- handles dummy R-group atoms
                │   └── No match -> Strategy 3
                ├── Strategy 3: GetSubstructMatch(useChirality=False)
                │               -- handles stereochemistry mismatches
                │   └── No match -> Compute2DCoords as fallback (lose alignment)
                └── Drop constant R-positions, build HTML, draw with DrawMoleculeACS1996
```

| Situation | Recommended choice | Rationale |
|-----------|--------------------|-----------|
| Standard congeneric series with a clear scaffold | MCS `threshold=0.8`, `ringMatchesRingOnly=True`, `completeRingsOnly=True` | Tolerates a small minority of outliers while keeping rings intact |
| Highly diverse set (e.g., HTS hit list) | Cluster (Tanimoto/Murcko) first, then SAR per cluster | A single MCS will be too small to be useful across diverse chemotypes |
| Stereoisomers in the series | Try Strategy 1 first; fall back to Strategy 3 (`useChirality=False`) | Chirality differences should not break depiction alignment |
| Analogues with R-group attachment dummies in queries | Strategy 2 with `AdjustQueryProperties(makeDummiesQueries=True)` | Dummy atoms are treated as queries so they match real heavy atoms |
| One R-position constant across all analogues | Drop from report and from core depiction | Constant positions are uninformative and clutter the table |
| Activity spans many orders of magnitude | Color heatmap on `log10(activity)` | Linear scale collapses the dynamic range visually |
| Drawing for publication or report | `DrawMoleculeACS1996` via `MolDraw2DSVG` | ACS1996 is the de facto standard for medicinal chemistry figures |

## Best Practices

1. **Inspect the dataframe before assuming column names.** Real-world activity tables vary; auto-detect the SMILES, activity, and ID columns from `df.head()` rather than hard-coding names. This avoids silent failures on user data.
2. **Add explicit hydrogens before MCS.** `Chem.AddHs` lets MCS reason correctly about heavy-atom valence and ring closures; without it, otherwise-identical scaffolds can be missed.
3. **Prune constant R-positions.** Any R-position whose fragment is identical across every analogue contributes no SAR information; remove that column from the table and remove the constant attachment point from the core depiction so the variable positions stand out.
4. **Always align fragments to the parent molecule, not the other way around.** Copy coordinates *from the parent* onto each fragment via the matched atom map. Drawing the parent canonically and then re-drawing fragments from scratch loses comparability between rows.
5. **Use a log-scale activity heatmap.** Potency typically spans 2–4 orders of magnitude; a linear color scale collapses the interesting low-IC50 region. Map green to low IC50 (high potency) and red to high IC50 (low potency).
6. **Justify every SAR claim with a pairwise contrast at the same R-position.** Statements like "small electron-withdrawing groups improve activity at R1" must be backed by a direct comparison such as "compound 7 (R1=F, IC50=0.5 µM) vs compound 1 (R1=Me, IC50=5.2 µM)". Unsupported generalizations are not acceptable evidence.
7. **Test 3-4 analogues per design hypothesis.** A single substitution change can be confounded by experimental noise; multiple analogues at the same position give a defensible trend.
8. **Render with `DrawMoleculeACS1996`.** ACS1996 styling produces consistent bond lengths, atom labels, and font choices that match medicinal-chemistry publication norms; avoid mixing styles within a single report.

## Common Pitfalls

- **Pitfall: Hard-coding column names like `"SMILES"` or `"IC50"`.** Different vendors and ELNs export different headers; the script breaks on the first user that uses `Smiles` or `Standard Value`.
  - *How to avoid*: Inspect `df.columns` and `df.head()` and detect the SMILES/activity/ID columns by content (valid SMILES parse rate, numeric values, unique strings).

- **Pitfall: Skipping `Chem.AddHs` before MCS.** Implicit-H molecules can yield a smaller-than-expected MCS because valence and ring perception differ.
  - *How to avoid*: Always preprocess with `mols_for_mcs = [Chem.AddHs(m) for m in mols]` before calling `rdFMCS.FindMCS`.

- **Pitfall: Setting `threshold=1.0` on a noisy series.** A single outlier with an unusual scaffold collapses the MCS to a tiny fragment and ruins R-group decomposition for everyone else.
  - *How to avoid*: Use `threshold=0.8` (or lower) so the MCS is defined when 80% of the series contains it; review the outlier(s) separately.

- **Pitfall: Drawing each fragment with `Compute2DCoords` independently.** Each fragment receives its own canonical 2D layout, so equivalent atoms appear in different positions across rows and visual SAR becomes unreadable.
  - *How to avoid*: Match each fragment to the parent (with the 3-strategy fallback) and copy coordinates from the parent's conformer onto the fragment's conformer.

- **Pitfall: Failing on dummy R-group atoms.** `GetSubstructMatch` returns no match when the fragment contains R-group dummy atoms (`*`) because dummies are not treated as queries by default.
  - *How to avoid*: Apply `AdjustQueryProperties(params)` with `makeDummiesQueries=True` before retrying the match (Strategy 2).

- **Pitfall: Reporting only a single error metric (e.g., mean only).** A trend reported without dispersion is not interpretable; equally, claims about substituent effects without same-position contrasts are not SAR.
  - *How to avoid*: For every R-position, list each unique substituent and the activities of the compounds carrying it; derive every claim from a pairwise comparison.

- **Pitfall: Using a linear-scale heatmap on IC50 in nM.** Most of the interesting potency range collapses into one or two color bins.
  - *How to avoid*: Color by `log10(IC50)` or `pIC50 = -log10(IC50_in_M)`; this gives uniform color separation across orders of magnitude.

- **Pitfall: Treating every column of the R-group decomposition as a SAR axis.** Constant R-positions (every analogue has the same fragment) and the core itself are not SAR variables.
  - *How to avoid*: After decomposition, programmatically drop columns where every entry is identical and remove those attachment points from the core image.

## Workflow

You are an expert in Cheminformatics and Python. Perform a SAR (Structure-Activity Relationship) analysis using RDKit.

**Task Requirements:**

1.  **Data Loading:** Load the CSV file. Do not assume fixed column names. Instead, inspect the dataframe (e.g., using `df.head()`) to automatically identify columns for Compound Key (e.g., 'Compound Key', 'ID', 'Name'), Activity (e.g., 'Standard Value', 'IC50', 'Activity'), and SMILES (e.g., 'Smiles', 'SMILES', 'Structure').

2.  **Core Identification (MCS):**
    *   Use `rdFMCS.FindMCS` to find a significant common scaffold.
    *   **Pre-processing:** Apply `Chem.AddHs` to molecules before finding MCS.
    *   **Reference Code:** Use the following parameter settings for robust core identification:
        ```python
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

3.  **R-Group Decomposition & Refinement:**
    *   Perform decomposition based on the Core.
    *   **Refinement:** Exclude any R-group columns that are identical (constant) across all molecules. Remove these constant points from the Core visualization as well.

4.  **Image Generation & Alignment (Strict Coordinate Extraction):**
    *   **Goal:** Ensure Core and R-groups are visually perfectly superimposed on the Original Molecule.
    *   **Drawing Style:** When drawing molecules, always use DrawMoleculeACS1996 for consistent and professional visualization:
        ```python
        from rdkit.Chem.Draw import rdMolDraw2D

        drawer = rdMolDraw2D.MolDraw2DSVG(-1, -1)
        rdMolDraw2D.DrawMoleculeACS1996(drawer, mol)

        drawer.FinishDrawing()
        svg = drawer.GetDrawingText()
        
        svg = svg.replace("width='", "width='100%' data-original-width='")
        svg = svg.replace("height='", "height='100%' data-original-height='")
        ```
    *   **Reference Implementation:** Use this specific alignment logic to guarantee perfect overlay:
        ```python
        matches, unmatched_indices = rdRGroupDecomposition.RGroupDecompose([core_mol], mols, asSmiles=False, asRows=False)
        ```

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

        # Usage in loop:
        # 1. Align Original Molecule to Core template
        try:
            AllChem.GenerateDepictionMatching2DStructure(m, core_mol)
        except:
            AllChem.Compute2DCoords(m)
            
        # 2. Align fragments (Core/R-groups) to Original Molecule
        # Copy coords FROM original molecule TO fragment
        if not align_substructure_to_parent(fragment, m):
             AllChem.Compute2DCoords(fragment)
        ```

        ```python
        match_core = matches['Core'][i]
        align_substructure_to_parent(this_core, mol)
        core_img = mol_to_base64(this_core)
        ```

5.  **HTML Output (`sar_analysis_report.html`):**
    *   **Design:** Create a clean, modern, and visually appealing HTML page using CSS styling. Use modern CSS features (e.g., subtle shadows, smooth transitions, clean typography, proper color schemes, responsive design) to enhance readability and visual appeal. **Crucially, ensure that the table column widths are large enough to display structures clearly. Set a `min-width` of at least 300px (e.g., `min-width: 300px;`) for the columns containing images (Original, Core, R-groups) so that the molecules are not shrunk and remain easily recognizable.**
    *   **Table Structure:** `Compound Key`, `Activity`, `Original Molecule`, `Core`, and variable R-groups.
    *   **Activity Heatmap:** Apply a background color gradient to Activity cells using a logarithmic scale (Green for low values/high potency, Red for high values/low potency).
    *   **Image Handling:**
        *   Convert molecules to **SVG** (preferred) or Base64 PNG strings.
        *   **Validation:** Check if image generation was successful. Only embed valid images; otherwise, use a text placeholder (`<td>No Image</td>`).
    *   **Interactive Sorting:**
        *   Add a "Toggle Sort Order" button to the HTML page.
        *   **Functionality:** Clicking the button cycles through three views: **Default View** (original CSV order), **Activity Ascending View** (sorted by Activity value from low to high), and **Activity Descending View** (sorted by Activity value from high to low).
        *   **Implementation:** Use JavaScript to handle the sorting logic on the client side. Ensure the Activity column values are parsed as numbers for correct sorting.
    *   **Summary:** Include a brief text summary of SAR findings (correlation between R-groups and activity).

6.  **Analysis Text Output:**
    *   Based on the analysis results, generate a concise text analysis of the SAR findings.
    *   **Output Format:** Print this text directly in the conversation (do not save to a file).
    *   **Instructions:** Follow these strict guidelines for the analysis text:

        You are a scientific assistant specializing in Structure-Activity Relationship (SAR) analysis. Your task is to analyze the provided molecular data and generate a concise SAR report. The report MUST contain molecule ids to help the user understand the SAR analysis.

        **Analyze the SAR for the following molecules based on the provided data.**

        **Core Instructions:**

        1.  **Identify the Scaffold and Substituents:**
            * Determine the common core structure and label the variable positions as R1, R2, etc. Use these labels consistently.

        2.  **Perform a Comparative Analysis:**
            * 🚨 CRITICAL REQUIREMENT: You MUST justify ALL claims about substituent impact **by explicitly contrasting with other substituents at the SAME position that resulted in different activity**. Every activity trend you describe MUST be supported by direct comparisons between the compounds. Unsupported generalizations are not acceptable. 🚨

        3.  **Infer Mechanisms:**
            * Propose plausible reasons for activity changes, considering steric, electronic, and potential intermolecular interactions (e.g., H-bonding, hydrophobic).

        4. **Evaluate Data Completeness and Propose Analogues (Mandatory Evaluation Step):**
            * As the final mandatory step of your analysis, you must critically evaluate the completeness of the provided SAR data.

            * If, and only if, you identify a significant ambiguity where a key compound lacks a clear counterpart for a robust SAR conclusion, you must propose a new analogue to resolve it.

            * The justification for any proposal must still follow the specific logic:

                * Identify the Ambiguity: Name the specific compound and its data that leads to uncertainty.

                * State the Missing Counterpart: Explain what comparison is needed but cannot be made.

                * Propose the Solution: Suggest the exact analogue that would resolve the ambiguity.

                * If you conclude that the data is sufficient, you will simply state this in the dedicated section below.

        5.  **Conclude:**
            * Summarize the key SAR findings and identify the most promising analogue(s).

        **Output Formatting and Style:**

        * **Be Direct:** Begin the analysis immediately. Do not use conversational openings like "I will analyze..." or "Here is the analysis...".
        * **Opening Statement:** Start with a single sentence summarizing the main structural modifications and the key finding.
        * **Scientific Tone:** Use precise, speculative language (e.g., "suggests that...", "likely due to...").
        * **Format:** Use Markdown for clarity (e.g., bolding, bullet points).
        * **Dedicated Suggestions Section:** At the end of your analysis, you **must** include a separate section titled `### Suggestions for Further Study`.
            * In this section, present the analogues you propose based on Instruction #4.
            * **If you conclude that the provided data is sufficient and no new analogues are needed**, you must still include the section and state: "The provided analogues offer sufficient comparative data for a robust initial SAR analysis at the explored positions." This ensures the step is never skipped.
        * **Conciseness:** Provide only the requested SAR analysis.
        * **Proactive Follow-up:** At the very end of your response (after the Conclusion), you **must** explicitly suggest a follow-up step or analysis in the form of a direct question to the user (e.g., "Would you like me to...?").

        ---
        **Example Output Structure:**

        The SAR analysis of the provided compounds indicates that a small, electron-withdrawing group at the R1 position is crucial for antibacterial activity. For instance, analogue **7** (R1=F, IC50 = 0.5 µM) showed a 10-fold improvement over the parent compound **1** (R1=Me, IC50 = 5.2 µM), suggesting a key interaction within a sterically confined space. In contrast, bulky substituents at R1, such as the phenyl group in analogue **12**, abolished activity entirely.

        ### Suggestions for Further Study

        To validate the hypothesis that steric bulk at R1 is detrimental, synthesizing an analogue with a simple hydrogen at that position (the des-methyl version of compound 1) is recommended. This would establish a baseline activity for the unsubstituted scaffold and confirm the size constraints of the binding pocket.

        **Would you like me to design a synthesis pathway for the proposed des-methyl analogue?**

**Output:**
*   Provide the final `sar_analysis_report.html` file.
*   Print the Analysis Text in the chat.

## References

- RDKit documentation — Maximum Common Substructure: https://www.rdkit.org/docs/source/rdkit.Chem.rdFMCS.html
- RDKit documentation — R-Group Decomposition: https://www.rdkit.org/docs/source/rdkit.Chem.rdRGroupDecomposition.html
- RDKit documentation — `MolDraw2D` and `DrawMoleculeACS1996`: https://www.rdkit.org/docs/source/rdkit.Chem.Draw.rdMolDraw2D.html
- Dalke A, Hastings J. "FMCS: a novel algorithm for the multiple MCS problem." J Cheminform. 2013;5(Suppl 1):O6. https://doi.org/10.1186/1758-2946-5-S1-O6
- Lewell XQ, Judd DB, Watson SP, Hann MM. "RECAP — Retrosynthetic Combinatorial Analysis Procedure." J Chem Inf Comput Sci. 1998;38(3):511-522. https://doi.org/10.1021/ci970429i
- Stumpfe D, Bajorath J. "Exploring activity cliffs in medicinal chemistry." J Med Chem. 2012;55(7):2932-2942. https://doi.org/10.1021/jm201706b
- Allen FH, Bellard S, Brice MD, et al. ACS document standards (ACS1996 drawing style reference): https://pubs.acs.org/doi/10.1021/ci00027a005
