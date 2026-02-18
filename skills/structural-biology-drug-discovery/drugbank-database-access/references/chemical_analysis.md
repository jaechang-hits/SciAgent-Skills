# Chemical Properties & Similarity Analysis

All examples assume the standard setup from SKILL.md Quick Start:
```python
import xml.etree.ElementTree as ET
NS = {'db': 'http://www.drugbank.ca'}
tree = ET.parse('drugbank_all_full_database.xml')
root = tree.getroot()
# find_drug(), get_property(), get_all_properties() as defined in SKILL.md Core API 5
```

## Full Property Extraction (Calculated + Experimental)

```python
drug = find_drug('Imatinib')
props = get_all_properties(drug)  # from SKILL.md Core API 5
for k, v in props.items():
    section = 'experimental' if k.startswith('experimental_') else 'calculated'
    label = k.replace('experimental_', '') if section == 'experimental' else k
    print(f"  [{section}] {label}: {v}")
```

## Veber's Rules for Oral Bioavailability

```python
def check_veber(drug_element):
    """Veber's rules: PSA <= 140 A^2 and rotatable bonds <= 10."""
    psa_str = get_property(drug_element, 'Polar Surface Area (PSA)')
    rot_str = get_property(drug_element, 'Rotatable Bond Count')
    if not psa_str or not rot_str:
        return None
    try:
        psa, rot = float(psa_str), int(rot_str)
    except (ValueError, TypeError):
        return None
    return {'PSA': psa, 'rotatable_bonds': rot, 'passes': psa <= 140 and rot <= 10}

for name in ['Aspirin', 'Imatinib', 'Cyclosporine']:
    drug = find_drug(name)
    r = check_veber(drug) if drug else None
    if r:
        print(f"{name}: PSA={r['PSA']:.1f}, RotBonds={r['rotatable_bonds']} -> "
              f"{'PASS' if r['passes'] else 'FAIL'}")
```

## Find Structurally Similar Drugs

```python
from rdkit import Chem
from rdkit.Chem import AllChem, DataStructs

def find_similar_drugs(query_drug, root, threshold=0.3, radius=2, nbits=2048):
    """Iterate all drugs, return those above Tanimoto threshold."""
    smi = get_property(query_drug, 'SMILES')
    mol = Chem.MolFromSmiles(smi) if smi else None
    if mol is None: return []
    qfp = AllChem.GetMorganFingerprintAsBitVect(mol, radius, nBits=nbits)
    qid = query_drug.find('db:drugbank-id[@primary="true"]', NS).text
    hits = []
    for d in root.findall('db:drug', NS):
        did = d.find('db:drugbank-id[@primary="true"]', NS)
        if did is None or did.text == qid: continue
        s = get_property(d, 'SMILES')
        m = Chem.MolFromSmiles(s) if s else None
        if m is None: continue
        sim = DataStructs.TanimotoSimilarity(qfp,
            AllChem.GetMorganFingerprintAsBitVect(m, radius, nBits=nbits))
        if sim >= threshold:
            nm = d.find('db:name', NS)
            hits.append({'drugbank_id': did.text,
                         'name': nm.text if nm is not None else 'N/A', 'similarity': sim})
    return sorted(hits, key=lambda x: x['similarity'], reverse=True)

for h in find_similar_drugs(find_drug('Ibuprofen'), root, threshold=0.4)[:5]:
    print(f"  {h['name']} ({h['drugbank_id']}): {h['similarity']:.3f}")
```

## Batch Similarity Matrix

```python
import numpy as np, pandas as pd
from rdkit import Chem
from rdkit.Chem import AllChem, DataStructs

def build_similarity_matrix(drug_names, radius=2, nbits=2048):
    fps, names = [], []
    for nm in drug_names:
        d = find_drug(nm)
        smi = get_property(d, 'SMILES') if d else None
        mol = Chem.MolFromSmiles(smi) if smi else None
        if mol is None:
            continue
        fps.append(AllChem.GetMorganFingerprintAsBitVect(mol, radius, nBits=nbits))
        names.append(nm)
    n = len(fps)
    mat = np.ones((n, n))
    for i in range(n):
        for j in range(i + 1, n):
            mat[i, j] = mat[j, i] = DataStructs.TanimotoSimilarity(fps[i], fps[j])
    return pd.DataFrame(mat, index=names, columns=names)

print(build_similarity_matrix(['Aspirin', 'Ibuprofen', 'Naproxen', 'Diclofenac']).round(3))
```

## Multiple Fingerprint Types

```python
from rdkit import Chem
from rdkit.Chem import AllChem, MACCSkeys, DataStructs
from rdkit.Chem.AtomPairs import Pairs as AtomPairs

def compare_fingerprints(smi1, smi2):
    mol1, mol2 = Chem.MolFromSmiles(smi1), Chem.MolFromSmiles(smi2)
    if mol1 is None or mol2 is None:
        return {}
    fp_funcs = {
        'morgan_ecfp4': lambda m: AllChem.GetMorganFingerprintAsBitVect(m, 2, nBits=2048),
        'morgan_ecfp6': lambda m: AllChem.GetMorganFingerprintAsBitVect(m, 3, nBits=2048),
        'maccs':        lambda m: MACCSkeys.GenMACCSKeys(m),
        'topological':  lambda m: Chem.RDKFingerprint(m),
        'atom_pairs':   lambda m: AtomPairs.GetAtomPairFingerprintAsBitVect(m),
    }
    return {k: DataStructs.TanimotoSimilarity(fn(mol1), fn(mol2)) for k, fn in fp_funcs.items()}

results = compare_fingerprints('CC(=O)Oc1ccccc1C(=O)O',            # Aspirin
                              'CC(C)Cc1ccc(cc1)[C@@H](C)C(=O)O')  # Ibuprofen
for fp, sim in results.items():
    print(f"  {fp:20s}: {sim:.3f}")
# MACCS=pharmacophore; Morgan=circular; Topological=linear paths; AtomPairs=distance
```

## Substructure Search with SMARTS

```python
from rdkit import Chem

def substructure_search(smarts, root, max_results=100):
    query = Chem.MolFromSmarts(smarts)
    if query is None:
        return []
    hits = []
    for drug in root.findall('db:drug', NS):
        smi = get_property(drug, 'SMILES')
        mol = Chem.MolFromSmiles(smi) if smi else None
        if mol is not None and mol.HasSubstructMatch(query):
            did = drug.find('db:drugbank-id[@primary="true"]', NS)
            nm = drug.find('db:name', NS)
            hits.append({'id': did.text if did is not None else 'N/A',
                         'name': nm.text if nm is not None else 'N/A'})
            if len(hits) >= max_results:
                break
    return hits

for h in substructure_search('[#16](=[#8])(=[#8])[#7]', root)[:5]:  # sulfonamide
    print(f"  {h['name']} ({h['id']})")
```

## ADMET Prediction Scoring

```python
def _admet_score(drug_element, criteria):
    """Generic scorer. criteria: [(prop_name, test_fn, label), ...]"""
    props = get_all_properties(drug_element)
    try:
        vals = {c[0]: float(props.get(c[0], 9999)) for c in criteria}
    except (ValueError, TypeError):
        return None
    score = sum(1 for c in criteria if c[1](vals[c[0]]))
    return {'score': score, 'max': len(criteria),
            'likelihood': 'high' if score >= 3 else 'moderate' if score >= 2 else 'low'}

def predict_oral_absorption(d):
    """MW<=500, logP [0,5], PSA<=140, HBD<=5."""
    return _admet_score(d, [('Molecular Weight', lambda v: v <= 500, 'MW'),
        ('logP', lambda v: 0 <= v <= 5, 'logP'),
        ('Polar Surface Area (PSA)', lambda v: v <= 140, 'PSA'),
        ('H Bond Donor Count', lambda v: v <= 5, 'HBD')])

def predict_bbb_permeability(d):
    """MW<450, logP [1,3], PSA<90, HBD<=3."""
    return _admet_score(d, [('Molecular Weight', lambda v: v < 450, 'MW'),
        ('logP', lambda v: 1 <= v <= 3, 'logP'),
        ('Polar Surface Area (PSA)', lambda v: v < 90, 'PSA'),
        ('H Bond Donor Count', lambda v: v <= 3, 'HBD')])

for name in ['Aspirin', 'Diazepam', 'Cyclosporine']:
    drug = find_drug(name)
    if not drug: continue
    oral, bbb = predict_oral_absorption(drug), predict_bbb_permeability(drug)
    if oral and bbb:
        print(f"{name}: oral={oral['likelihood']}({oral['score']}/4), "
              f"BBB={bbb['likelihood']}({bbb['score']}/4)")
```

## Chemical Space PCA

```python
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA

prop_keys = ['Molecular Weight', 'logP', 'logS', 'Polar Surface Area (PSA)',
             'H Bond Donor Count', 'H Bond Acceptor Count', 'Rotatable Bond Count']
records = []
for drug in root.findall('db:drug', NS):
    if drug.get('type') != 'small molecule':
        continue
    name = drug.find('db:name', NS)
    if name is None:
        continue
    try:
        vals = {k: float(get_property(drug, k)) for k in prop_keys}
        vals['name'] = name.text
        records.append(vals)
    except (TypeError, ValueError):
        continue

df = pd.DataFrame(records)
print(f"Drugs with complete vectors: {len(df)}")
X_scaled = StandardScaler().fit_transform(df[prop_keys].values)
pca = PCA(n_components=2).fit(X_scaled)
df[['PC1', 'PC2']] = pca.transform(X_scaled)
print(f"Variance: PC1={pca.explained_variance_ratio_[0]:.1%}, "
      f"PC2={pca.explained_variance_ratio_[1]:.1%}")
```

## Clustering by Chemical Properties

```python
from sklearn.cluster import KMeans
# Reuse df, X_scaled, prop_keys from PCA section above
df['cluster'] = KMeans(n_clusters=5, random_state=42, n_init=10).fit_predict(X_scaled)
for c in range(5):
    sub = df[df['cluster'] == c]
    print(f"Cluster {c} ({len(sub)}): MW={sub['Molecular Weight'].mean():.0f}, "
          f"logP={sub['logP'].mean():.1f} — {', '.join(sub['name'].head(3))}")
```

## Export Full Property Database to CSV

```python
import pandas as pd

records = []
for drug in root.findall('db:drug', NS):
    did = drug.find('db:drugbank-id[@primary="true"]', NS)
    nm = drug.find('db:name', NS)
    if did is None or nm is None:
        continue
    row = {'drugbank_id': did.text, 'name': nm.text, 'type': drug.get('type')}
    for sec, prefix in [('calculated', ''), ('experimental', 'exp_')]:
        for prop in drug.findall(f'db:{sec}-properties/db:property', NS):
            k, v = prop.find('db:kind', NS), prop.find('db:value', NS)
            if k is not None and v is not None:
                row[f'{prefix}{k.text}'] = v.text
    records.append(row)
df = pd.DataFrame(records)
df.to_csv('drugbank_full_properties.csv', index=False)
print(f"Exported {len(df)} drugs, {len(df.columns)} columns")
```

---

Condensed from chemical-analysis.md (591 lines). Retained: full property extraction (calculated + experimental), Veber's rules, similar drug search with threshold iteration, batch pairwise similarity matrix, multiple fingerprint types (MACCS, topological, atom pairs) with comparison, substructure search via SMARTS, ADMET prediction (oral absorption scoring, BBB permeability criteria), chemical space PCA, KMeans clustering, CSV export with experimental properties. Omitted: 3D conformer generation, RDKit descriptor calculator module — use rdkit-cheminformatics skill. Relocated to SKILL.md: basic SMILES/InChI extraction and Tanimoto similarity with Morgan fingerprints (Core API 5), Lipinski Rule of Five filter (Common Recipes).
