---
name: kegg-pathway-analysis
description: "Best practices for KEGG pathway over-representation analysis (ORA) and gene set enrichment. Covers mandatory directionality splitting, KEGG API failure handling, offline fallbacks, and common pitfalls."
license: CC-BY-4.0
compatibility: Python 3.10+, R 4.0+
metadata:
  authors: HITS
  version: "1.0"
---

# KEGG Pathway Enrichment Analysis Guide

## Overview

This guide covers KEGG pathway enrichment analysis for differential expression results. It addresses two recurring failure modes: (1) incorrect pathway counts due to ignoring gene directionality, and (2) analysis failures caused by KEGG REST API timeouts.

---

## Rule 1 (MANDATORY): Split Enrichment by Gene Direction

**CRITICAL: You MUST run KEGG enrichment SEPARATELY for up-regulated and down-regulated genes. NEVER combine them into a single gene list.** This is the single most common error in pathway enrichment analysis.

Running enrichment on a combined (up + down) gene list produces WRONG pathway counts because:
- Pathways with genes regulated in opposite directions cancel out
- The inflated gene list dilutes the enrichment signal
- Pathways significant in one direction get masked by noise from the other

**MANDATORY WORKFLOW -- follow this EXACTLY:**

### Step 1: Split genes by direction FIRST

```r
library(clusterProfiler)

# Filter significant DEGs
sig_genes <- subset(res, padj < 0.05 & abs(log2FoldChange) > 1.5)

# MANDATORY: Split by direction BEFORE running enrichment
up_genes <- rownames(subset(sig_genes, log2FoldChange > 0))
dn_genes <- rownames(subset(sig_genes, log2FoldChange < 0))

cat("Up-regulated genes:", length(up_genes), "\n")
cat("Down-regulated genes:", length(dn_genes), "\n")
```

### Step 2: Run enrichKEGG TWICE (once per direction)

```r
# Run enrichment SEPARATELY for each direction
ekegg_up <- enrichKEGG(gene = up_genes, organism = organism_code,
                       universe = rownames(res), pvalueCutoff = 0.05)
ekegg_dn <- enrichKEGG(gene = dn_genes, organism = organism_code,
                       universe = rownames(res), pvalueCutoff = 0.05)

# Extract significant pathways from EACH direction
up_pathways <- subset(as.data.frame(ekegg_up), p.adjust < 0.05)$ID
dn_pathways <- subset(as.data.frame(ekegg_dn), p.adjust < 0.05)$ID

# Total significant pathways = union of both directions
all_sig_pathways <- union(up_pathways, dn_pathways)
cat("Significant pathways (up):", length(up_pathways), "\n")
cat("Significant pathways (down):", length(dn_pathways), "\n")
cat("Total unique significant pathways:", length(all_sig_pathways), "\n")
```

### Step 2 alternative: Python with gseapy

```python
import gseapy as gp

# MANDATORY: Split by direction
up_genes = sig_genes[sig_genes['log2FoldChange'] > 0].index.tolist()
dn_genes = sig_genes[sig_genes['log2FoldChange'] < 0].index.tolist()

# Run enrichment SEPARATELY for each direction
enr_up = gp.enrichr(gene_list=up_genes, gene_sets='KEGG_2021_Human',
                     organism='human', outdir=None)
enr_dn = gp.enrichr(gene_list=dn_genes, gene_sets='KEGG_2021_Human',
                     organism='human', outdir=None)
```

### When Comparing Enrichment Across Conditions

When asked "how many pathways are enriched in condition A but not condition B":
1. Run separate up/down enrichment for BOTH conditions (4 enrichKEGG calls total)
2. Compare pathway sets WITHIN the same direction (up_A vs up_B, down_A vs down_B)
3. Report the union of unique pathways across both directions

```r
# Step 1: Get pathways per direction for EACH condition
# Condition A (e.g., iron-depleted)
up_pathways_A <- subset(as.data.frame(ekegg_up_A), p.adjust < 0.05)$ID
dn_pathways_A <- subset(as.data.frame(ekegg_dn_A), p.adjust < 0.05)$ID

# Condition B (e.g., innate media)
up_pathways_B <- subset(as.data.frame(ekegg_up_B), p.adjust < 0.05)$ID
dn_pathways_B <- subset(as.data.frame(ekegg_dn_B), p.adjust < 0.05)$ID

# Step 2: Find pathways unique to condition A in each direction
unique_up <- setdiff(up_pathways_A, up_pathways_B)
unique_dn <- setdiff(dn_pathways_A, dn_pathways_B)

# Step 3: Union
unique_to_A <- union(unique_up, unique_dn)
cat("Pathways in A but not B:", length(unique_to_A), "\n")
cat("  From up-regulated:", length(unique_up), "-", paste(unique_up, collapse=", "), "\n")
cat("  From down-regulated:", length(unique_dn), "-", paste(unique_dn, collapse=", "), "\n")
```

### Common mistake (DO NOT DO THIS)

```r
# WRONG: combining up and down genes into one list
all_sig_genes <- rownames(subset(res, padj < 0.05 & abs(log2FoldChange) > 1.5))
ekegg <- enrichKEGG(gene = all_sig_genes, ...)  # <-- WRONG, will miss pathways
```

---

## Rule 2: Handle KEGG REST API Failures Gracefully

The KEGG REST API (`rest.kegg.jp`) is rate-limited and frequently times out. Plan for this.

### Preferred Strategy: Use Local/Cached Data First

**R (KEGGREST package):**
```r
# Pre-fetch pathway list at the start of analysis, before enrichment
library(KEGGREST)
pathway_list <- tryCatch(
  keggList("pathway", organism_code),
  error = function(e) NULL
)
```

**Python (bioservices or requests):**
```python
# Pre-fetch and cache KEGG pathway mappings
import requests
import json
import os

cache_file = f"kegg_{organism_code}_pathways.json"
if os.path.exists(cache_file):
    with open(cache_file) as f:
        pathway_map = json.load(f)
else:
    resp = requests.get(f"https://rest.kegg.jp/list/pathway/{organism_code}", timeout=30)
    if resp.ok:
        pathway_map = dict(line.split("\t") for line in resp.text.strip().split("\n"))
        with open(cache_file, 'w') as f:
            json.dump(pathway_map, f)
```

### Fallback: Use gseapy When clusterProfiler Fails

If `clusterProfiler::enrichKEGG` fails due to KEGG API issues, fall back to Python `gseapy` which bundles offline gene set databases:

```python
import gseapy as gp

# gseapy has built-in KEGG gene sets that do not require API access
enr = gp.enrichr(gene_list=gene_list,
                  gene_sets='KEGG_2021_Human',  # offline database
                  organism='human',
                  outdir=None)
```

### Retry with Timeout

If you must use the KEGG API, add a retry with a short timeout:

```r
fetch_kegg_with_retry <- function(organism_code, max_retries = 3, timeout_sec = 30) {
  for (i in seq_len(max_retries)) {
    result <- tryCatch({
      R.utils::withTimeout(
        keggList("pathway", organism_code),
        timeout = timeout_sec
      )
    }, error = function(e) NULL)
    if (!is.null(result)) return(result)
    Sys.sleep(2)
  }
  warning("KEGG API unreachable after retries. Proceeding without pathway names.")
  return(NULL)
}
```

---

## Rule 3: Emit the Answer Before Cosmetic Lookups

Once you have computed the numeric answer (e.g., a count of pathways, a list of pathway IDs), **report it immediately**. Do not delay the solution to resolve pathway IDs to human-readable names via additional API calls.

### Correct Pattern

```
# Good: report the answer, then optionally resolve names
result_ids <- setdiff(pathways_condA, pathways_condB)
count <- length(result_ids)
# --> Emit solution with count and IDs here <--

# Then optionally try to resolve names (non-blocking)
names <- tryCatch(keggGet(result_ids), error = function(e) NULL)
```

### Anti-Pattern

```
# Bad: delay the answer to look up names
result_ids <- setdiff(pathways_condA, pathways_condB)
names <- keggGet(result_ids)  # <-- This can timeout and lose the answer
count <- length(result_ids)
# --> Answer never emitted because keggGet hung
```

---

## Common KEGG Organism Codes

| Organism | Code |
|---|---|
| Human | hsa |
| Mouse | mmu |
| Rat | rno |
| Zebrafish | dre |
| Drosophila | dme |
| C. elegans | cel |
| E. coli K-12 | eco |
| P. aeruginosa PA14 | pau |
| P. aeruginosa PAO1 | pae |
| S. cerevisiae | sce |
| A. thaliana | ath |

---

## Checklist

Before reporting pathway enrichment results, verify:

- [ ] Up-regulated and down-regulated genes were analyzed separately (unless question specifies combined)
- [ ] The correct KEGG organism code was used for the species
- [ ] Gene IDs match the KEGG ID format (locus tags for bacteria, Entrez IDs for eukaryotes)
- [ ] Universe/background gene set was specified (all tested genes, not just significant ones)
- [ ] Multiple testing correction was applied (p.adjust < 0.05, not raw p-value)
- [ ] The numeric answer was reported before attempting pathway name resolution
