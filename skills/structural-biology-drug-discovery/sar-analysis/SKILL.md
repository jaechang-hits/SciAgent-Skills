---
name: sar-analysis
description: "Comprehensive guide for performing Structure-Activity Relationship (SAR) analysis using RDKit. Covers core identification via MCS, R-group decomposition, molecular alignment, HTML report generation with heatmaps, and SAR text analysis."
license: CC-BY-4.0
compatibility: Python 3.10+
metadata:
  authors: Biomni Team
  version: "1.0"
---

# SAR Analysis

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
            * CRITICAL REQUIREMENT: You MUST justify ALL claims about substituent impact **by explicitly contrasting with other substituents at the SAME position that resulted in different activity**. Every activity trend you describe MUST be supported by direct comparisons between the compounds. Unsupported generalizations are not acceptable.

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

        The SAR analysis of the provided compounds indicates that a small, electron-withdrawing group at the R1 position is crucial for antibacterial activity. For instance, analogue **7** (R1=F, IC50 = 0.5 uM) showed a 10-fold improvement over the parent compound **1** (R1=Me, IC50 = 5.2 uM), suggesting a key interaction within a sterically confined space. In contrast, bulky substituents at R1, such as the phenyl group in analogue **12**, abolished activity entirely.

        ### Suggestions for Further Study

        To validate the hypothesis that steric bulk at R1 is detrimental, synthesizing an analogue with a simple hydrogen at that position (the des-methyl version of compound 1) is recommended. This would establish a baseline activity for the unsubstituted scaffold and confirm the size constraints of the binding pocket.

        **Would you like me to design a synthesis pathway for the proposed des-methyl analogue?**

**Output:**
*   Provide the final `sar_analysis_report.html` file.
*   Print the Analysis Text in the chat.
