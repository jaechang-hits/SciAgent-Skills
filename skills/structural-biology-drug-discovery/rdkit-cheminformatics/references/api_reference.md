# RDKit API Quick Reference

Organized by capability. Use this as a function lookup when writing RDKit code.

## Molecular I/O

| Function | Purpose | Returns |
|----------|---------|---------|
| `Chem.MolFromSmiles(smi)` | Parse SMILES string | `Mol` or `None` |
| `Chem.MolFromMolFile(path)` | Read MOL/SDF file | `Mol` or `None` |
| `Chem.MolFromMolBlock(block)` | Read MOL block string | `Mol` or `None` |
| `Chem.MolFromInchi(inchi)` | Parse InChI string | `Mol` or `None` |
| `Chem.MolToSmiles(mol)` | Canonical SMILES | `str` |
| `Chem.MolToMolBlock(mol)` | MOL block text | `str` |
| `Chem.MolToInchi(mol)` | InChI string | `str` |
| `Chem.SDMolSupplier(path)` | Read multi-mol SDF | Iterator of `Mol` |
| `Chem.ForwardSDMolSupplier(f)` | Streaming SDF reader | Iterator of `Mol` |
| `Chem.SmilesMolSupplier(path)` | Read SMILES file | Iterator of `Mol` |
| `Chem.SDWriter(path)` | Write SDF file | Writer object |
| `Chem.MultithreadedSDMolSupplier(path)` | Parallel SDF reader | Iterator of `Mol` |

## Sanitization & Standardization

| Function | Purpose |
|----------|---------|
| `Chem.SanitizeMol(mol)` | Full sanitization (valence, aromaticity, etc.) |
| `Chem.DetectChemistryProblems(mol)` | List problems without raising |
| `Chem.SanitizeMol(mol, sanitizeOps=ops)` | Partial sanitization |
| `rdMolStandardize.Uncharger().uncharge(mol)` | Remove formal charges |
| `rdMolStandardize.LargestFragmentChooser().choose(mol)` | Keep largest fragment |
| `rdMolStandardize.Cleanup(mol)` | General cleanup |
| `Chem.AddHs(mol)` | Add explicit hydrogens |
| `Chem.RemoveHs(mol)` | Remove explicit hydrogens |
| `Chem.Kekulize(mol)` | Convert aromatic to Kekulé form |
| `Chem.SetAromaticity(mol)` | Perceive aromaticity |

## Molecular Descriptors

| Function | Returns | Typical Range |
|----------|---------|---------------|
| `Descriptors.MolWt(mol)` | Molecular weight (Da) | 100-800 |
| `Descriptors.ExactMolWt(mol)` | Exact mass | 100-800 |
| `Descriptors.MolLogP(mol)` | Wildman-Crippen LogP | -3 to 8 |
| `Descriptors.TPSA(mol)` | Topological polar surface area (Å²) | 0-250 |
| `Descriptors.NumHDonors(mol)` | H-bond donors | 0-15 |
| `Descriptors.NumHAcceptors(mol)` | H-bond acceptors | 0-20 |
| `Descriptors.NumRotatableBonds(mol)` | Rotatable bonds | 0-20 |
| `Descriptors.NumAromaticRings(mol)` | Aromatic ring count | 0-8 |
| `Descriptors.RingCount(mol)` | Total ring count | 0-10 |
| `Descriptors.FractionCSP3(mol)` | sp3 carbon fraction | 0-1 |
| `Descriptors.NumHeteroatoms(mol)` | Heteroatom count | 0-30 |
| `Descriptors.CalcMolDescriptors(mol)` | All descriptors as dict | - |

## Fingerprints

| Function | Type | Typical Usage |
|----------|------|---------------|
| `AllChem.GetMorganFingerprintAsBitVect(mol, radius, nBits)` | Morgan/ECFP (bit vector) | Similarity search, ML |
| `AllChem.GetMorganFingerprint(mol, radius)` | Morgan (count vector) | Detailed substructure analysis |
| `Chem.RDKFingerprint(mol)` | RDKit topological | General screening |
| `MACCSkeys.GenMACCSKeys(mol)` | MACCS 166-bit | Drug discovery, legacy |
| `Pairs.GetAtomPairFingerprint(mol)` | Atom pair | Scaffold hopping |
| `Torsions.GetTopologicalTorsionFingerprint(mol)` | Topological torsion | Shape-dependent |
| `pyAvalonTools.GetAvalonFP(mol)` | Avalon | Substructure indexing |

## Similarity Metrics

| Function | Metric | Range |
|----------|--------|-------|
| `DataStructs.TanimotoSimilarity(fp1, fp2)` | Tanimoto (Jaccard) | 0-1 |
| `DataStructs.DiceSimilarity(fp1, fp2)` | Dice | 0-1 |
| `DataStructs.CosineSimilarity(fp1, fp2)` | Cosine | 0-1 |
| `DataStructs.BulkTanimotoSimilarity(fp, fps)` | Bulk Tanimoto | List of 0-1 |

## Substructure & SMARTS

| Function | Purpose |
|----------|---------|
| `Chem.MolFromSmarts(smarts)` | Parse SMARTS pattern |
| `mol.HasSubstructMatch(query)` | Check if match exists |
| `mol.GetSubstructMatch(query)` | First match (atom indices) |
| `mol.GetSubstructMatches(query)` | All matches |
| `Chem.ReplaceSubstructs(mol, query, replacement)` | Replace substructure |

## 3D Coordinates & Conformers

| Function | Purpose |
|----------|---------|
| `AllChem.Compute2DCoords(mol)` | Generate 2D layout |
| `AllChem.EmbedMolecule(mol, params)` | Single 3D conformer |
| `AllChem.EmbedMultipleConfs(mol, numConfs, params)` | Multiple conformers |
| `AllChem.ETKDGv3()` | Best ETKDG parameters |
| `AllChem.MMFFOptimizeMolecule(mol, confId)` | MMFF94 optimization |
| `AllChem.UFFOptimizeMolecule(mol, confId)` | UFF optimization |
| `AllChem.GetConformerRMS(mol, id1, id2)` | RMSD between conformers |
| `AllChem.AlignMol(probe, ref)` | Align two molecules |
| `AllChem.ConstrainedEmbed(mol, core)` | Constrained embedding |

## Drawing & Visualization

| Function | Purpose |
|----------|---------|
| `Draw.MolToImage(mol, size)` | PIL image of molecule |
| `Draw.MolToFile(mol, path)` | Save molecule image |
| `Draw.MolsToGridImage(mols, molsPerRow, subImgSize)` | Grid of molecules |
| `rdMolDraw2D.MolDraw2DCairo(w, h)` | Cairo-based drawer |
| `rdMolDraw2D.MolDraw2DSVG(w, h)` | SVG drawer |
| `Draw.DrawMorganBit(mol, bit_id, bit_info)` | Visualize FP bit |

## Reactions

| Function | Purpose |
|----------|---------|
| `AllChem.ReactionFromSmarts(rxn_smarts)` | Parse reaction SMARTS |
| `rxn.RunReactants((reactant1, reactant2))` | Apply reaction |
| `AllChem.CreateDifferenceFingerprintForReaction(rxn)` | Reaction fingerprint |

## Scaffolds & Fragments

| Function | Purpose |
|----------|---------|
| `MurckoScaffold.GetScaffoldForMol(mol)` | Murcko scaffold |
| `MurckoScaffold.MakeScaffoldGeneric(scaffold)` | Generic (carbon) scaffold |
| `Chem.GetMolFrags(mol, asMols=True)` | Disconnected fragments |
| `Chem.FragmentOnBonds(mol, bond_ids)` | Cut specific bonds |

## Pharmacophore

| Function | Purpose |
|----------|---------|
| `ChemicalFeatures.BuildFeatureFactory(fdef)` | Load feature definitions |
| `factory.GetFeaturesForMol(mol)` | Extract pharmacophore features |
