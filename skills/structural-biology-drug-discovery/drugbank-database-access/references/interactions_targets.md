# Interactions & Targets — Advanced Patterns

Advanced interaction analysis (networks, mechanism classification, polypharmacy screening,
risk scoring) and target/pathway extraction (polypeptide details, matrices, repurposing,
CYP450/transporter analysis). All blocks assume this preamble:

```python
import xml.etree.ElementTree as ET
from collections import defaultdict, Counter
NS = {'db': 'http://www.drugbank.ca'}
tree = ET.parse('drugbank_all_full_database.xml')
root = tree.getroot()
drug_index, drug_names = {}, {}
for drug in root.findall('db:drug', NS):
    db_id = drug.find('db:drugbank-id[@primary="true"]', NS)
    name = drug.find('db:name', NS)
    if db_id is not None and name is not None:
        drug_index[name.text.lower()] = drug
        drug_index[db_id.text] = drug
        drug_names[db_id.text] = name.text
```

---

## Bidirectional Interaction Network

```python
interaction_net = defaultdict(set)
for drug in root.findall('db:drug', NS):
    db_id = drug.find('db:drugbank-id[@primary="true"]', NS)
    if db_id is None: continue
    for inter in drug.findall('db:drug-interactions/db:drug-interaction', NS):
        pid = inter.find('db:drugbank-id', NS).text
        interaction_net[db_id.text].add(pid)
        interaction_net[pid].add(db_id.text)
print(f"Network: {len(interaction_net)} drugs, "
      f"{sum(len(v) for v in interaction_net.values())//2} edges")
for did, p in sorted(interaction_net.items(), key=lambda x: len(x[1]), reverse=True)[:5]:
    print(f"  {drug_names.get(did,did)}: {len(p)}")

def common_interactors(drug_ids, net):
    """Drugs interacting with ALL drugs in input set (set intersection)."""
    result = net.get(drug_ids[0], set()).copy()
    for did in drug_ids[1:]: result &= net.get(did, set())
    return result
```

## NetworkX Graph with Community Detection

```python
import networkx as nx
G = nx.Graph()
for drug in root.findall('db:drug', NS):
    db_id = drug.find('db:drugbank-id[@primary="true"]', NS)
    nm = drug.find('db:name', NS)
    if db_id is None or nm is None: continue
    G.add_node(db_id.text, name=nm.text)
    for inter in drug.findall('db:drug-interactions/db:drug-interaction', NS):
        pid = inter.find('db:drugbank-id', NS).text
        desc = inter.find('db:description', NS).text or ''
        dl = desc.lower()
        sev = ('major' if any(w in dl for w in ['contraindicated','avoid','fatal'])
               else 'moderate' if any(w in dl for w in ['increase','decrease','enhance'])
               else 'minor')
        G.add_edge(db_id.text, pid, severity=sev)
print(f"Nodes: {G.number_of_nodes()}, Edges: {G.number_of_edges()}")
from community import community_louvain  # pip install python-louvain
print(f"Communities: {max(community_louvain.best_partition(G).values())+1}")
```

## Mechanism Classification

```python
def classify_mechanism(description):
    """Returns: metabolic/absorption/excretion/pharmacodynamic/protein_binding/unknown."""
    if not description: return 'unknown'
    dl = description.lower()
    if any(w in dl for w in ['cyp','metaboli','enzyme inhibit','hepatic','p450']): return 'metabolic'
    if any(w in dl for w in ['absorpt','bioavailab','chelat','gastric']): return 'absorption'
    if any(w in dl for w in ['excret','renal clear','tubular','clearance']): return 'excretion'
    if any(w in dl for w in ['protein bind','plasma protein','albumin']): return 'protein_binding'
    if any(w in dl for w in ['pharmacodynamic','additive','synergis','antagoni',
                              'qt prolong','serotonin','bleeding']): return 'pharmacodynamic'
    return 'unknown'

warfarin = drug_index.get('warfarin')
if warfarin:
    mechs = Counter(classify_mechanism(i.find('db:description', NS).text)
                    for i in warfarin.findall('db:drug-interactions/db:drug-interaction', NS))
    print("Warfarin mechanisms:", dict(mechs.most_common()))
```

## Interaction Matrix and CSV Export

```python
import numpy as np, pandas as pd
drug_list = ['Warfarin','Aspirin','Omeprazole','Metformin','Atorvastatin']
sev_w = {'major':3,'moderate':2,'minor':1}
n = len(drug_list)
matrix = np.zeros((n,n), dtype=int)
for i, n1 in enumerate(drug_list):
    d1 = drug_index.get(n1.lower())
    if not d1: continue
    imap = {it.find('db:drugbank-id',NS).text: it.find('db:description',NS).text or ''
            for it in d1.findall('db:drug-interactions/db:drug-interaction', NS)}
    for j, n2 in enumerate(drug_list):
        if i==j: continue
        d2 = drug_index.get(n2.lower())
        if not d2: continue
        desc = imap.get(d2.find('db:drugbank-id[@primary="true"]',NS).text)
        if desc:
            dl = desc.lower()
            sev = ('major' if any(w in dl for w in ['contraindicated','avoid','fatal'])
                   else 'moderate' if any(w in dl for w in ['increase','decrease','enhance'])
                   else 'minor')
            matrix[i][j] = sev_w.get(sev,0)
print(pd.DataFrame(matrix, index=drug_list, columns=drug_list).to_string())
edges = [{'drug_1':drug_list[i],'drug_2':drug_list[j],'weight':matrix[i][j]}
         for i in range(n) for j in range(i+1,n) if matrix[i][j]>0]
pd.DataFrame(edges).to_csv('interaction_edges.csv', index=False)
```

## Polypharmacy Batch Screening with Risk Scoring

```python
from itertools import combinations
# Pre-build: db_id → {partner_id: description}
id_lookup, inter_map = {}, {}
for drug in root.findall('db:drug', NS):
    db_id = drug.find('db:drugbank-id[@primary="true"]', NS)
    nm = drug.find('db:name', NS)
    if db_id is None or nm is None: continue
    id_lookup[nm.text.lower()] = db_id.text
    inter_map[db_id.text] = {i.find('db:drugbank-id',NS).text: i.find('db:description',NS).text
                              for i in drug.findall('db:drug-interactions/db:drug-interaction',NS)}

def screen_polypharmacy(meds, weights=None):
    """Returns (interactions, risk_score). Score = sum severity weights."""
    if weights is None: weights = {'major':10,'moderate':3,'minor':1}
    ids = [(m,id_lookup.get(m.lower())) for m in meds]
    ids = [(n,i) for n,i in ids if i]
    results, score = [], 0
    for (n1,id1),(n2,id2) in combinations(ids, 2):
        desc = inter_map.get(id1,{}).get(id2) or inter_map.get(id2,{}).get(id1)
        if not desc: continue
        dl = desc.lower()
        sev = ('major' if any(w in dl for w in ['contraindicated','avoid','fatal'])
               else 'moderate' if any(w in dl for w in ['increase','decrease','enhance'])
               else 'minor')
        w = weights.get(sev,0); score += w
        results.append({'drug_1':n1,'drug_2':n2,'severity':sev,'weight':w})
    return results, score

ints, risk = screen_polypharmacy(['Warfarin','Aspirin','Omeprazole','Atorvastatin','Metformin'])
print(f"{len(ints)} interactions, risk={risk}")
```

---

## Detailed Polypeptide Extraction

```python
def get_polypeptide_details(drug_element, target_type='targets'):
    """Full polypeptide: function annotations, sequence length, GO terms."""
    results = []
    for target in drug_element.findall(f'db:{target_type}/db:{target_type[:-1]}', NS):
        t = {'name': (target.find('db:name',NS).text if target.find('db:name',NS) is not None else None),
             'actions': [a.text for a in target.findall('db:actions/db:action',NS) if a.text]}
        poly = target.find('db:polypeptide', NS)
        if poly is not None:
            t['uniprot_id'] = poly.get('id')
            for fld in ['gene-name','general-function','specific-function','cellular-location']:
                el = poly.find(f'db:{fld}', NS)
                t[fld.replace('-','_')] = el.text if el is not None and el.text else None
            seq = poly.find('db:amino-acid-sequence', NS)
            t['seq_len'] = len(seq.text.strip()) if seq is not None and seq.text else 0
            t['go_terms'] = [{'category': g.find('db:category',NS).text,
                               'description': g.find('db:description',NS).text}
                              for g in poly.findall('db:go-classifiers/db:go-classifier',NS)
                              if g.find('db:category',NS) is not None]
        results.append(t)
    return results

drug = drug_index.get('imatinib')
if drug:
    for t in get_polypeptide_details(drug)[:2]:
        print(f"{t['name']} ({t.get('uniprot_id','?')}) GO:{len(t.get('go_terms',[]))} {t.get('seq_len',0)}aa")
```

## Drug-Target Matrix

```python
import pandas as pd
rows = [{'drug': drug.find('db:name',NS).text, 'gene': poly.find('db:gene-name',NS).text}
        for drug in root.findall('db:drug', NS) if drug.find('db:name',NS) is not None
        for t in drug.findall('db:targets/db:target', NS)
        if (poly := t.find('db:polypeptide',NS)) is not None
        and poly.find('db:gene-name',NS) is not None and poly.find('db:gene-name',NS).text]
df = pd.DataFrame(rows)
print(f"Pairs: {len(df)}, drugs: {df['drug'].nunique()}, genes: {df['gene'].nunique()}")
dt_matrix = (pd.crosstab(df['drug'], df['gene']) > 0).astype(int)
print(f"Matrix: {dt_matrix.shape}")
```

## Reverse Lookup and Shared Targets

```python
import pandas as pd
def find_drugs_for_target(root, gene_name=None, uniprot_id=None):
    """All drugs targeting a gene or UniProt ID (searches targets/enzymes/transporters/carriers)."""
    results = []
    for drug in root.findall('db:drug', NS):
        nm = drug.find('db:name', NS)
        if nm is None: continue
        for ttype in ['targets','enzymes','transporters','carriers']:
            for t in drug.findall(f'db:{ttype}/db:{ttype[:-1]}', NS):
                poly = t.find('db:polypeptide', NS)
                if poly is None: continue
                g = poly.find('db:gene-name', NS)
                if ((gene_name and g is not None and g.text == gene_name) or
                    (uniprot_id and poly.get('id') == uniprot_id)):
                    acts = [a.text for a in t.findall('db:actions/db:action',NS) if a.text]
                    results.append({'drug':nm.text,'type':ttype,'actions':', '.join(acts)})
    return pd.DataFrame(results)

print(find_drugs_for_target(root, gene_name='EGFR').to_string(index=False))

def get_target_genes(drug_el):
    """Gene → actions dict across all target types."""
    genes = {}
    for ttype in ['targets','enzymes','transporters','carriers']:
        for t in drug_el.findall(f'db:{ttype}/db:{ttype[:-1]}', NS):
            poly = t.find('db:polypeptide', NS)
            if poly is None: continue
            g = poly.find('db:gene-name', NS)
            if g is not None and g.text:
                genes[g.text] = [a.text for a in t.findall('db:actions/db:action',NS) if a.text]
    return genes

# Shared targets between two drugs
d1, d2 = drug_index.get('imatinib'), drug_index.get('dasatinib')
if d1 and d2:
    g1, g2 = get_target_genes(d1), get_target_genes(d2)
    shared = set(g1) & set(g2)
    print(f"Shared: {len(shared)}/{len(g1)} vs {len(g2)}")
```

## Pathway Extraction and Network

```python
def get_detailed_pathways(drug_element):
    """SMPDB pathways with category, co-pathway drugs, enzymes."""
    def _txt(el, path):
        e = el.find(path, NS)
        return e.text if e is not None else None
    return [{'smpdb_id': _txt(pw,'db:smpdb-id'), 'name': _txt(pw,'db:name'),
             'category': _txt(pw,'db:category'),
             'drugs': [d.find('db:name',NS).text for d in pw.findall('db:drugs/db:drug',NS)
                       if d.find('db:name',NS) is not None],
             'enzymes': [e.text for e in pw.findall('db:enzymes/db:uniprot-id',NS) if e.text]}
            for pw in drug_element.findall('db:pathways/db:pathway', NS)]

# Global pathway-drug network
pw_drugs = defaultdict(set)
for drug in root.findall('db:drug', NS):
    nm = drug.find('db:name', NS)
    if nm is None: continue
    for pw in drug.findall('db:pathways/db:pathway', NS):
        pn = pw.find('db:name', NS)
        if pn is not None and pn.text: pw_drugs[pn.text].add(nm.text)
print(f"Pathways: {len(pw_drugs)}")
for p, ds in sorted(pw_drugs.items(), key=lambda x: len(x[1]), reverse=True)[:5]:
    print(f"  {p}: {len(ds)} drugs")
```

## Target-Based Drug Repurposing

```python
import pandas as pd
drug_targets = {}  # drug_name → set of gene names
for drug in root.findall('db:drug', NS):
    nm = drug.find('db:name', NS)
    if nm is None: continue
    genes = {poly.find('db:gene-name',NS).text
             for t in drug.findall('db:targets/db:target',NS)
             if (poly := t.find('db:polypeptide',NS)) is not None
             and poly.find('db:gene-name',NS) is not None and poly.find('db:gene-name',NS).text}
    if genes: drug_targets[nm.text] = genes

def find_repurposing_candidates(query, dt, min_jacc=0.2, top_n=15):
    """Jaccard similarity on target gene sets."""
    qg = dt.get(query)
    if not qg: return pd.DataFrame()
    cands = [{'drug':o,'shared':', '.join(sorted(qg&og)),
              'jaccard':round(len(qg&og)/len(qg|og),3)}
             for o,og in dt.items() if o!=query and qg&og and len(qg&og)/len(qg|og)>=min_jacc]
    return pd.DataFrame(cands).sort_values('jaccard',ascending=False).head(top_n)

print(find_repurposing_candidates('Imatinib', drug_targets).to_string(index=False))
```

## Polypharmacology Analysis

```python
def polypharmacology_profile(drug_el):
    """Split targets into known-action vs unknown-action lists."""
    known, unknown = [], []
    for t in drug_el.findall('db:targets/db:target', NS):
        poly = t.find('db:polypeptide', NS)
        gene = (poly.find('db:gene-name',NS).text if poly is not None
                and poly.find('db:gene-name',NS) is not None else None)
        ka = t.find('db:known-action', NS)
        (known if ka is not None and ka.text == 'yes' else unknown).append(gene)
    return known, unknown

for dname in ['Imatinib','Dasatinib','Sunitinib']:
    d = drug_index.get(dname.lower())
    if not d: continue
    kn, unk = polypharmacology_profile(d)
    print(f"{dname}: known={len(kn)} unknown={len(unk)}")
```

## CYP450 Enzyme Analysis

```python
import pandas as pd
CYP_GENES = {'CYP1A2','CYP2C9','CYP2C19','CYP2D6','CYP3A4','CYP3A5','CYP2B6','CYP2C8','CYP2E1'}
cyp_data = []
for drug in root.findall('db:drug', NS):
    nm = drug.find('db:name', NS)
    if nm is None: continue
    for enz in drug.findall('db:enzymes/db:enzyme', NS):
        poly = enz.find('db:polypeptide', NS)
        if poly is None: continue
        gene = poly.find('db:gene-name', NS)
        if gene is None or gene.text not in CYP_GENES: continue
        acts = [a.text.lower() for a in enz.findall('db:actions/db:action',NS) if a.text]
        role = ('substrate' if 'substrate' in acts else 'inhibitor' if 'inhibitor' in acts
                else 'inducer' if 'inducer' in acts else 'other')
        cyp_data.append({'drug':nm.text,'cyp':gene.text,'role':role})
df = pd.DataFrame(cyp_data)
print(df.groupby(['cyp','role']).size().unstack(fill_value=0).to_string())
```

## Transporter Substrate Classification

```python
import pandas as pd
EFFLUX = {'ABCB1','ABCG2','ABCC1','ABCC2','ABCC3','ABCC4','ABCB11'}  # P-gp, BCRP, MRP1-4
UPTAKE = {'SLC22A1','SLC22A2','SLC22A6','SLC22A8','SLCO1B1','SLCO1B3','SLC47A1','SLC47A2'}
tdata = []
for drug in root.findall('db:drug', NS):
    nm = drug.find('db:name', NS)
    if nm is None: continue
    for tr in drug.findall('db:transporters/db:transporter', NS):
        poly = tr.find('db:polypeptide', NS)
        if poly is None: continue
        gene = poly.find('db:gene-name', NS)
        if gene is None or not gene.text: continue
        gn = gene.text
        cls = 'efflux' if gn in EFFLUX else 'uptake' if gn in UPTAKE else 'other'
        tdata.append({'drug':nm.text,'gene':gn,'class':cls})
df_tr = pd.DataFrame(tdata)
print(f"Drug-transporter: {len(df_tr)}")
print(df_tr.groupby('class')['drug'].nunique().to_string())
print(f"P-gp (ABCB1): {len(df_tr[df_tr['gene']=='ABCB1'])} entries")
```

---

Condensed from interactions.md (426 lines) + targets-pathways.md (519 lines) = 945 lines. Retained: interaction network, common interactors, NetworkX graph, community detection, mechanism classification, interaction matrix, CSV export, polypharmacy screening with risk scoring, polypeptide extraction (function/sequence/GO), drug-target matrix, reverse lookup, shared targets, pathway extraction (SMPDB), pathway-drug network, drug repurposing (Jaccard), polypharmacology analysis, CYP450 analysis, transporter classification. Omitted from interactions.md: basic extraction/severity/pairwise check — relocated to SKILL.md Core API 3; description parsing boilerplate — subsumed by classify_mechanism. Omitted from targets-pathways.md: basic target/pathway extraction — relocated to SKILL.md Core API 4; drug lookup — relocated to Quick Start. Relocated to SKILL.md: interaction extraction + severity + pairwise (Core API 3), target/enzyme/transporter/pathway extraction (Core API 4), drug lookup (Quick Start).
