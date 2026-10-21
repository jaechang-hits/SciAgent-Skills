---
name: "database-query"
description: "Gene set membership lookups from public sources: MSigDB GMT files (hallmark, C2 pathways, C5 GO, C6 oncogenic, C7 immunologic/vaccine, mouse MP phenotype), GTRD transcription factor promoter targets, miRDB v6.0 miRNA targets with scores, P-HIPSter virus-host interactions via Enrichr, ClinVar classification of a protein change, and gene cytogenetic band via Ensembl. Answers 'is gene X in set / target of / interacting with Y'. For full ClinVar work use clinvar-database; Ensembl lookups ensembl-database; enrichment analysis gseapy-gene-enrichment; disease-gene associations opentargets-database or monarch-database."
license: "CC-BY-4.0"
---

# Gene Set and Annotation Database Lookups

## Overview

Membership questions ("which of these genes is a GTRD target of TBX3?",
"is UNC5C a miRDB target of hsa-miR-4795-5p?") answered from the public
release files, downloaded once into `ref_cache/`. Output: per-gene yes/no
membership, miRDB scores, ClinVar classifications and cytogenetic bands,
each traceable to a named public release.

## When to Use

- Checking whether genes belong to a named MSigDB set (hallmark, pathway, GO, oncogenic, vaccine, mouse phenotype)
- Asking which genes have a GTRD binding site for a transcription factor in their promoter
- Checking predicted miRNA targets and their miRDB scores
- Listing predicted human partners of a viral protein (P-HIPSter)
- Looking up the ClinVar classification of a protein change, or a gene's cytogenetic band
- Use `gseapy-gene-enrichment` instead when the question is enrichment of a gene list, not membership
- For full ClinVar queries use `clinvar-database`; for disease-gene associations use `opentargets-database`

## Prerequisites

- `pip install requests pandas` if missing
- MSigDB files are free to download; check the MSigDB license page for reuse
  terms of each collection
- NCBI E-utilities: pass your email; without an API key stay under 3
  requests/s (10/s with an `api_key` parameter)

## Workflow

1. Load any MSigDB collection (GMT)
2. TF binding in promoters (GTRD)
3. miRNA targets (miRDB)
4. Virus-host protein interactions (P-HIPSter)
5. Other collections: pathways, GO, oncogenic, vaccine, mouse phenotype
6. ClinVar classification of a protein change
7. Cytogenetic band of a gene

Disease-gene sets from DisGeNET and OMIM are not covered: both need a
licence or API key. Use `opentargets-database` or `monarch-database`.

### Step 1: MSigDB GMT Loader

```python
import os
import requests

MSIGDB_VER = "2026.2"   # latest at writing; list: https://data.broadinstitute.org/gsea-msigdb/msigdb/release/
os.makedirs("ref_cache", exist_ok=True)

def load_gmt(collection, species="Hs"):
    """collection e.g. 'c3.tft.gtrd', 'h.all', 'm5.mpo.mp' (species 'Mm'). Returns {set_name: set(genes)}."""
    fname = f"{collection}.v{MSIGDB_VER}.{species}.symbols.gmt"
    path = f"ref_cache/{fname}"
    if not os.path.exists(path):
        url = f"https://data.broadinstitute.org/gsea-msigdb/msigdb/release/{MSIGDB_VER}.{species}/{fname}"
        r = requests.get(url, timeout=600)
        r.raise_for_status()
        open(path, "w").write(r.text)
    sets = {}
    for line in open(path):
        name, _url, *genes = line.rstrip("\n").split("\t")
        sets[name] = set(genes)
    return sets

def check_membership(sets, set_name, candidates):
    if set_name not in sets:
        close = [s for s in sets if set_name.split("_")[0] in s][:10]
        print(f"'{set_name}' not found; similar: {close}")
        return None
    genes = sets[set_name]
    print(f"{set_name}: {len(genes)} genes")
    return {g: g in genes for g in candidates}
```

Gene sets are plain symbols: human sets uppercase (`TP53`), mouse sets
title case (`Trp53`).

### Step 2: TF Binding Sites in Promoters (GTRD)

MSigDB `c3.tft.gtrd` sets `{TF}_TARGET_GENES` hold genes with one or more
GTRD ChIP-seq binding sites for the TF in the promoter (TSS -1000,+100 bp):

```python
gtrd = load_gmt("c3.tft.gtrd")
print(check_membership(gtrd, "TBX3_TARGET_GENES", ["DGAT2-DT", "CXCL1", "RIMS3", "TMEM79"]))
print(sorted(s for s in gtrd if s.startswith("ZNF28"))[:10])   # browse TF names
```

Mouse: `load_gmt("m3.gtrd", "Mm")`.

### Step 3: miRNA Targets (miRDB v6.0)

MSigDB `c3.mir.mirdb` holds miRDB v6.0 targets with score > 80, named
`MIR4795_5P` for `hsa-miR-4795-5p`:

```python
mirdb_sets = load_gmt("c3.mir.mirdb")
print(check_membership(mirdb_sets, "MIR4795_5P", ["ATP5MGL", "UNC5C", "NTN3", "MACROD1"]))

def mirbase_name(msig, prefix="hsa"):
    """MIR29B_1_5P -> hsa-miR-29b-1-5p; LET_7A_5P -> hsa-let-7a-5p."""
    head, *rest = msig.lower().split("_")
    base = f"{prefix}-miR-{head[3:]}" if head.startswith("mir") else f"{prefix}-{head}"
    return "-".join([base, *rest])

print(mirbase_name("MIR29B_1_5P"))
```

For scores, or targets below 80, use the raw miRDB file (RefSeq accessions,
~60 MB) and map symbols to RefSeq with MyGene.info:

```python
import pandas as pd

RAW = "ref_cache/miRDB_v6.0_prediction_result.txt.gz"
if not os.path.exists(RAW):
    open(RAW, "wb").write(requests.get("https://mirdb.org/download/miRDB_v6.0_prediction_result.txt.gz", timeout=600).content)
mirdb = pd.read_csv(RAW, sep="\t", header=None, names=["miRNA", "refseq", "score"])

def mirdb_scores(mirna, symbols, species="human"):
    hits = requests.post("https://mygene.info/v3/query", timeout=60, data={
        "q": ",".join(symbols), "scopes": "symbol", "species": species, "fields": "refseq.rna"}).json()
    rows = mirdb[mirdb["miRNA"] == mirna]
    out = {}
    for h in hits:
        rna = h.get("refseq", {}).get("rna", [])
        acc = {a.split(".")[0] for a in ([rna] if isinstance(rna, str) else rna)}
        s = rows.loc[rows["refseq"].isin(acc), "score"]
        out[h["query"]] = round(float(s.max()), 1) if len(s) else None
    return out

print(mirdb_scores(mirbase_name("MIR4795_5P"), ["UNC5C", "NTN3", "MACROD1"]))
```

### Step 4: Virus-Host Interactions (P-HIPSter)

P-HIPSter predictions are distributed as the Enrichr library
`Virus-Host_PPI_P-HIPSTer_2020`; set names are viral proteins:

```python
LIB = "ref_cache/Virus-Host_PPI_P-HIPSTer_2020.txt"
if not os.path.exists(LIB):
    url = "https://maayanlab.cloud/Enrichr/geneSetLibrary?mode=text&libraryName=Virus-Host_PPI_P-HIPSTer_2020"
    open(LIB, "w").write(requests.get(url, timeout=600).text)
phipster = {}
for line in open(LIB):
    name, _, *genes = line.rstrip("\n").split("\t")
    phipster[name] = {g.split(",")[0] for g in genes if g}

query = "Hepatitis C virus genotype 5"
matches = [n for n in phipster if query.lower() in n.lower() and " E2" in n]
print(matches)                                  # confirm the right strain/protein first
partners = set().union(*(phipster[n] for n in matches)) if matches else set()
print({g: g in partners for g in ["TRGV3", "SLAIN1", "FOXK2", "GYS2"]})
```

### Step 5: Other Collections

`check_membership(load_gmt(<collection>, <species>), <set_name>, candidates)`
works for all of these:

| Question | Collection | Set name example |
|---|---|---|
| Hallmark processes | `h.all` | `HALLMARK_APOPTOSIS` |
| Curated pathways (KEGG legacy, Reactome, ...) | `c2.cp`, `c2.all` | `KEGG_APOPTOSIS` |
| GO terms | `c5.go.bp`, `c5.go.cc`, `c5.go.mf` | `GOBP_APOPTOTIC_PROCESS` |
| Oncogenic signatures | `c6.all` | `AKT_UP_MTOR_DN.V1_UP` |
| Vaccine response | `c7.vax` | `CAO_BLOOD_FLUMIST_AGE_05_14YO_1DY_DN` |
| Immunologic signatures | `c7.immunesigdb` | |
| Cell type signatures | `c8.all` / mouse `m8.all` | |
| Mouse phenotype (MGI MP) | `m5.mpo.mp`, species `Mm` | `MP_INCREASED_SMALL_INTESTINE_ADENOCARCINOMA_INCIDENCE` |
| Mouse curated pathways | `m2.cp`, species `Mm` | |

```python
mp = load_gmt("m5.mpo.mp", "Mm")
print([s for s in mp if "ADENOCARCINOMA" in s][:10])
print(check_membership(mp, "MP_INCREASED_SMALL_INTESTINE_ADENOCARCINOMA_INCIDENCE",
                       ["Tes", "Tnfrsf1a", "Rnf8", "Smurf2"]))
```

### Step 6: ClinVar Classification of a Protein Change

Find the protein change first (`sequence-analysis` Modules 2 and 7: identify
the protein by BLAST, list substitutions), then look each one up:

```python
import time

EUTILS = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
EMAIL = "you@example.org"          # NCBI asks for a contact email

def clinvar_protein_change(gene, change):
    """change like 'A1326S'. Returns ClinVar records whose protein_change lists it."""
    ids = requests.get(f"{EUTILS}/esearch.fcgi", timeout=30, params={
        "db": "clinvar", "term": f"{gene}[gene] AND {change}[variant name]",
        "retmax": 20, "retmode": "json", "email": EMAIL}).json()["esearchresult"]["idlist"]
    time.sleep(0.4)                  # stay under 3 requests/s without an API key
    if not ids:
        return []
    res = requests.get(f"{EUTILS}/esummary.fcgi", timeout=30, params={
        "db": "clinvar", "id": ",".join(ids), "retmode": "json", "email": EMAIL}).json()["result"]
    out = []
    for uid in res["uids"]:
        d, gc = res[uid], res[uid].get("germline_classification", {})
        out.append({"title": d["title"], "protein_change": d.get("protein_change"),
                    "classification": gc.get("description"), "review_status": gc.get("review_status")})
    return out

for v in ["A1326S", "T455A"]:
    print(v, clinvar_protein_change("SCN5A", v))
```

Residue numbers differ between isoforms (`protein_change` may read
`A1325S, A1326S, A1272S`); match the isoform your sequence came from. Report
the ClinVar classification and review status, never a guess from amino acid
chemistry; "not in ClinVar" is a valid answer.

### Step 7: Cytogenetic Band

```python
def gene_band(symbol, species="homo_sapiens"):
    hdr = {"Content-Type": "application/json"}
    g = requests.get(f"https://rest.ensembl.org/lookup/symbol/{species}/{symbol}", headers=hdr, timeout=30).json()
    if "error" in g:
        return {"gene": symbol, "band": None, "location": None}
    asm = requests.get(f"https://rest.ensembl.org/info/assembly/{species}/{g['seq_region_name']}",
                       params={"bands": 1}, headers=hdr, timeout=30).json()
    band = next((b["id"] for b in asm.get("karyotype_band", []) if b["start"] <= g["start"] <= b["end"]), None)
    return {"gene": symbol, "band": f"{g['seq_region_name']}{band}" if band else None,
            "location": f"chr{g['seq_region_name']}:{g['start']}-{g['end']}"}

for s in ["NUTF2", "BRCA1"]:
    print(gene_band(s))
```

Coordinates are GRCh38. Pseudogenes and readthrough symbols may be missing
from the lookup; try the Ensembl ID instead.

## Key Parameters

| Parameter | Default | Effect |
|---|---|---|
| `MSIGDB_VER` | `2026.2` | Release; set names and members change between releases |
| `species` | `Hs` | `Mm` for mouse collections (m1-m8, mh) |
| miRDB score cutoff | > 80 in MSigDB sets | Use the raw file for lower-confidence targets |
| ClinVar `retmax` | 20 | Raise for genes with many records per change |
| NCBI `api_key` | none | Raises the E-utilities limit from 3 to 10 requests/s |
| Ensembl `species` | `homo_sapiens` | Species for the band lookup; coordinates follow its current assembly |

## Common Recipes

### Recipe: Which Sets Contain a Gene?

Reverse lookup across a whole collection:

```python
def sets_containing(sets, gene):
    return sorted(name for name, genes in sets.items() if gene in genes)

hallmark = load_gmt("h.all")
print(sets_containing(hallmark, "TP53"))
print(len(sets_containing(gtrd, "CXCL1")), "GTRD TF sets list CXCL1 as a promoter target")
```

### Recipe: Overlap of a Gene List with One Set

A single-set hypergeometric test, for a quick check of whether a list
overlaps a set more than chance (for whole-collection enrichment use
`gseapy-gene-enrichment`):

```python
from scipy.stats import hypergeom

def overlap_test(gene_list, set_genes, universe_size=20000):
    hits = set(gene_list) & set_genes
    p = hypergeom.sf(len(hits) - 1, universe_size, len(set_genes), len(set(gene_list)))
    return {"overlap": len(hits), "set_size": len(set_genes), "list_size": len(set(gene_list)),
            "p_value": p, "genes": sorted(hits)}

my_genes = ["CDKN1A", "MDM2", "BAX", "GADD45A", "ACTB", "GAPDH"]
print(overlap_test(my_genes, hallmark["HALLMARK_P53_PATHWAY"]))
```

`universe_size` should be the number of genes that could have been in the
list (e.g. genes detected in the experiment), not a fixed 20,000.

## Expected Outputs

- `ref_cache/` - downloaded GMT, miRDB and Enrichr library files (reused across runs)

## Troubleshooting

| Problem | Cause | Fix |
|---|---|---|
| Set name not found | Renamed between releases, or wrong collection | Use the similar-names printout; check the MSigDB browser |
| Mouse gene never matches | Case | Mouse symbols are title case (`Smurf2`) |
| miRNA set missing | Arm or paralog suffix, or merged set | List `[s for s in mirdb_sets if "MIR29B" in s]`; miRNAs with identical targets share one set (`LET_7A_5P_LET_7C_5P_...`) - split it before `mirbase_name` |
| `mirdb_scores` returns None | miRDB uses an older RefSeq; gene below cutoff | Treat as not predicted; say so |
| ClinVar returns nothing | Different notation or isoform numbering | Try three-letter form `"p.Ala1326Ser"`, or nearby residue numbers from other isoforms |
| HTTP 429 from NCBI | Rate limit | Keep the `time.sleep(0.4)`; add an NCBI `api_key` param |
| Ensembl 503 | Service busy | Retry after a few seconds |

## Related Skills

- `clinvar-database` - full ClinVar queries, review stars, bulk files
- `ensembl-database` - gene lookup, sequences, VEP, orthologs
- `gseapy-gene-enrichment` - enrichment analysis over these collections
- `opentargets-database`, `monarch-database` - disease-gene associations
- `sequence-analysis` - identify a protein and list its substitutions

## References

- MSigDB: https://www.gsea-msigdb.org/gsea/msigdb/
- Liberzon et al. (2015) MSigDB hallmark collection, Cell Systems: https://doi.org/10.1016/j.cels.2015.12.004
- Chen and Wang (2019) miRDB, Nucleic Acids Research: https://doi.org/10.1093/nar/gkz757
- Lasso et al. (2019) P-HIPSter, Cell: https://doi.org/10.1016/j.cell.2019.08.005
- Landrum et al. (2017) ClinVar, Nucleic Acids Research: https://doi.org/10.1093/nar/gkx1153
- Ensembl REST API: https://rest.ensembl.org/
