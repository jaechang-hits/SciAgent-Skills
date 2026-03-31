---
name: kegg-pathway-analysis
description: "Guide to KEGG pathway enrichment analysis for differential expression results. Covers over-representation analysis (ORA) vs gene set enrichment analysis (GSEA), mandatory directionality splitting, KEGG organism codes, API failure handling with offline fallbacks, cross-condition pathway comparisons, and answer-first reporting. Consult this when running pathway enrichment with clusterProfiler or gseapy on DEG results."
license: CC-BY-4.0
---

# KEGG Pathway Enrichment Analysis Guide

## Overview

KEGG (Kyoto Encyclopedia of Genes and Genomes) pathway enrichment analysis identifies biological pathways that are statistically over-represented among differentially expressed genes. This guide covers the two main enrichment approaches (ORA and GSEA), critical workflow decisions such as splitting genes by directionality, tool selection between R clusterProfiler and Python gseapy, and strategies for handling the notoriously unreliable KEGG REST API. It addresses recurring failure modes that produce incorrect pathway counts or stalled analyses.

The three most common errors in KEGG pathway analysis are: (1) combining up-regulated and down-regulated genes into a single enrichment run, which masks true pathway signals; (2) analysis failures caused by KEGG REST API timeouts with no fallback strategy; and (3) delaying result reporting while attempting cosmetic pathway name lookups that may never complete. This guide provides concrete solutions for each.

## Key Concepts

### ORA vs GSEA

Over-Representation Analysis (ORA) and Gene Set Enrichment Analysis (GSEA) are the two primary methods for pathway enrichment, and they differ in both input and statistical approach.

**ORA** takes a pre-filtered gene list (e.g., genes with padj < 0.05 and |log2FC| > 1.5) and tests whether KEGG pathway members are over-represented in that list relative to a background universe. ORA uses a hypergeometric test (Fisher's exact test). It is straightforward but discards magnitude information and depends heavily on the significance cutoff chosen.

**GSEA** takes a ranked list of all genes (typically ranked by log2 fold change or a signed significance statistic) without any cutoff. It computes a running enrichment score by walking down the ranked list and identifies pathways whose members cluster toward the top or bottom of the ranking. GSEA captures subtle coordinated changes that ORA may miss.

In practice, ORA via `enrichKEGG()` (clusterProfiler) or `gp.enrichr()` (gseapy) is the more common starting point. GSEA via `gseKEGG()` or `gp.prerank()` is preferred when you want to avoid arbitrary cutoffs or when effect sizes are small.

### Directionality in Enrichment

When performing ORA, gene directionality -- whether a gene is up-regulated or down-regulated -- is critical. A single pathway can contain genes regulated in opposite directions. If up-regulated and down-regulated genes are combined into one list, their opposing signals cancel out, diluting the enrichment signal and masking genuinely enriched pathways. Running enrichment separately for up-regulated and down-regulated gene sets produces more accurate and interpretable results. This splitting is mandatory for ORA. GSEA inherently handles directionality through the signed ranking, though interpreting leading-edge genes by direction is still important.

### KEGG Organism Codes

KEGG uses three-letter (or four-letter) organism codes to identify species-specific pathway databases. Using the wrong code silently returns empty results. Common codes:

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

Gene ID format also varies by organism: eukaryotic species typically require Entrez gene IDs, while bacterial species use locus tags. Mismatched ID types are a silent failure mode.

### KEGG API Reliability

The KEGG REST API (`rest.kegg.jp`) is rate-limited, frequently slow, and prone to timeouts. Both `clusterProfiler::enrichKEGG()` and direct HTTP requests to KEGG can fail unpredictably. Planning for API failures is not optional -- it is a necessary part of any KEGG-based workflow. Strategies include pre-fetching and caching pathway data, using offline gene set databases bundled with gseapy, and implementing retry logic with timeouts.

## Decision Framework

```
Question: What enrichment analysis do you need?
|
+-- Have a pre-filtered DEG list (with cutoffs applied)?
|   +-- Yes --> ORA
|   |   +-- Using R? --> clusterProfiler::enrichKEGG()
|   |   +-- Using Python? --> gseapy.enrichr()
|   |   +-- KEGG API failing? --> gseapy with offline gene sets
|   +-- No, want cutoff-free analysis --> GSEA
|       +-- Using R? --> clusterProfiler::gseKEGG()
|       +-- Using Python? --> gseapy.prerank()
|
+-- Need to split by direction?
|   +-- ORA --> YES, always split up/down (mandatory)
|   +-- GSEA --> No split needed (direction encoded in ranking)
|
+-- KEGG API unreliable?
    +-- Try cached/pre-fetched data first
    +-- Fall back to gseapy offline databases
    +-- Use retry logic with short timeouts
```

| Scenario | Recommended Approach | Rationale |
|----------|---------------------|-----------|
| Standard ORA with R | `clusterProfiler::enrichKEGG()`, split by direction | Most widely used, integrates with Bioconductor ecosystem |
| Standard ORA with Python | `gseapy.enrichr()` with KEGG_2021_Human | Offline gene sets avoid API dependency |
| Cutoff-free enrichment | GSEA via `gseKEGG()` or `gp.prerank()` | Captures subtle coordinated changes, no arbitrary threshold |
| KEGG API is down | Switch to gseapy offline databases | gseapy bundles KEGG gene sets locally |
| Comparing conditions | Run separate up/down enrichment per condition | Enables direction-aware set operations across conditions |
| Non-model organism | Verify organism code, use KEGGREST to check availability | Wrong code silently returns empty results |

## Best Practices

1. **Always split ORA by gene direction.** Run `enrichKEGG()` or `gp.enrichr()` separately for up-regulated and down-regulated genes. Combining them inflates the gene list, dilutes enrichment signal, and produces incorrect pathway counts. Report the union of significant pathways from both directions.

2. **Specify the background universe explicitly.** Set the universe to all tested genes (the full set from your differential expression analysis), not just the significant ones. Omitting the universe defaults to all genes in the KEGG database, which inflates significance for well-studied pathways.

3. **Pre-fetch and cache KEGG data before running enrichment.** Download pathway-gene mappings at the start of the analysis and save them locally. This avoids mid-analysis failures when the KEGG API becomes unresponsive and makes the analysis reproducible.

4. **Report the numeric answer before resolving pathway names.** Once you have computed the count or list of significant pathway IDs, emit that result immediately. Resolving IDs to human-readable names via additional KEGG API calls is cosmetic and can timeout, losing the primary result.

5. **Apply multiple testing correction consistently.** Use adjusted p-values (p.adjust < 0.05, typically BH method) rather than raw p-values. Both clusterProfiler and gseapy apply correction by default, but always verify the cutoff is on the adjusted value.

6. **Verify gene ID format matches the organism.** Eukaryotic KEGG pathways expect Entrez gene IDs; bacterial species expect locus tags. A mismatch silently returns zero enriched pathways. Use `bitr()` in clusterProfiler or equivalent ID conversion if your input uses gene symbols.

7. **Use gseapy as a fallback when clusterProfiler fails.** When `enrichKEGG()` fails due to KEGG API issues, gseapy's `enrichr()` function with bundled offline gene sets (e.g., `KEGG_2021_Human`) provides equivalent ORA results without any network dependency.

## Common Pitfalls

1. **Combining up-regulated and down-regulated genes into a single enrichment run.** Pathways with genes regulated in opposite directions cancel out, producing fewer significant pathways than the true count. Results from combined lists are unreliable. Example of the anti-pattern:

   ```r
   # WRONG: combining up and down genes into one list
   all_sig_genes <- rownames(subset(res, padj < 0.05 & abs(log2FoldChange) > 1.5))
   ekegg <- enrichKEGG(gene = all_sig_genes, ...)  # Will miss pathways
   ```

   - *How to avoid*: Always split DEGs by direction before ORA. Run enrichment twice (once for up, once for down) and take the union of significant pathways.

2. **Using the wrong KEGG organism code.** KEGG silently returns empty results for invalid or mismatched organism codes. This is especially common for bacterial species with multiple strain-specific codes (e.g., `pae` for PAO1 vs `pau` for PA14).
   - *How to avoid*: Confirm the organism code from the KEGG organism list before running enrichment. For bacteria, verify the specific strain code.

3. **Gene ID type mismatch.** Providing gene symbols when KEGG expects Entrez IDs (or locus tags for bacteria) silently yields zero enriched pathways with no error message.
   - *How to avoid*: Check the expected ID type for your organism. Use `clusterProfiler::bitr()` or equivalent to convert gene symbols to Entrez IDs before enrichment.

4. **Not handling KEGG API timeouts.** The KEGG REST API frequently times out, causing `enrichKEGG()` to fail mid-analysis. Without error handling, the entire analysis is lost.
   - *How to avoid*: Wrap KEGG API calls in retry logic with short timeouts (30 seconds). Pre-fetch pathway data at the start. Have gseapy as a fallback.

5. **Delaying the answer to resolve pathway names.** Calling `keggGet()` to convert pathway IDs to human-readable names after computing results can timeout, losing the numeric answer entirely. Example of the anti-pattern:

   ```r
   # BAD: answer delayed by name lookup that may hang
   result_ids <- setdiff(pathways_condA, pathways_condB)
   names <- keggGet(result_ids)  # Can timeout -- answer never emitted
   count <- length(result_ids)
   ```

   - *How to avoid*: Report pathway IDs and counts immediately. Resolve names only after the primary result is secured, inside a `tryCatch()` or try/except block.

6. **Omitting the background universe.** Not specifying the universe parameter defaults to the entire KEGG gene database for that organism, inflating statistical significance for pathways containing well-annotated housekeeping genes.
   - *How to avoid*: Always pass `universe = rownames(res)` (all tested genes from the DE analysis) to `enrichKEGG()`.

7. **Using raw p-values instead of adjusted p-values for filtering.** Reporting pathways with p < 0.05 without multiple testing correction dramatically increases false positives.
   - *How to avoid*: Always filter on `p.adjust < 0.05`. Verify that the column you are filtering is the adjusted value, not the raw p-value.

## Workflow

1. **Step 1: Prepare gene lists**
   - Filter significant DEGs from differential expression results (e.g., padj < 0.05, |log2FC| > 1.5)
   - Split into up-regulated and down-regulated gene sets
   - Convert gene IDs to the format expected by KEGG (Entrez IDs or locus tags)

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

2. **Step 2: Pre-fetch KEGG data (recommended)**
   - Cache pathway-gene mappings locally before running enrichment
   - Decision point: If KEGG API is accessible, proceed with live queries. If not, switch to offline gene sets (Step 2b).

   **R (KEGGREST package):**
   ```r
   library(KEGGREST)
   pathway_list <- tryCatch(
     keggList("pathway", organism_code),
     error = function(e) NULL
   )
   ```

   **Python (requests with caching):**
   ```python
   import requests
   import json
   import os

   cache_file = f"kegg_{organism_code}_pathways.json"
   if os.path.exists(cache_file):
       with open(cache_file) as f:
           pathway_map = json.load(f)
   else:
       resp = requests.get(
           f"https://rest.kegg.jp/list/pathway/{organism_code}", timeout=30
       )
       if resp.ok:
           pathway_map = dict(
               line.split("\t") for line in resp.text.strip().split("\n")
           )
           with open(cache_file, 'w') as f:
               json.dump(pathway_map, f)
   ```

3. **Step 3: Run enrichment separately for each direction**
   - Run ORA twice: once for up-regulated genes, once for down-regulated genes
   - Always specify the universe (all tested genes)

   **R (clusterProfiler):**
   ```r
   ekegg_up <- enrichKEGG(gene = up_genes, organism = organism_code,
                          universe = rownames(res), pvalueCutoff = 0.05)
   ekegg_dn <- enrichKEGG(gene = dn_genes, organism = organism_code,
                          universe = rownames(res), pvalueCutoff = 0.05)

   up_pathways <- subset(as.data.frame(ekegg_up), p.adjust < 0.05)$ID
   dn_pathways <- subset(as.data.frame(ekegg_dn), p.adjust < 0.05)$ID

   all_sig_pathways <- union(up_pathways, dn_pathways)
   cat("Significant pathways (up):", length(up_pathways), "\n")
   cat("Significant pathways (down):", length(dn_pathways), "\n")
   cat("Total unique significant pathways:", length(all_sig_pathways), "\n")
   ```

   **Python (gseapy):**
   ```python
   import gseapy as gp

   up_genes = sig_genes[sig_genes['log2FoldChange'] > 0].index.tolist()
   dn_genes = sig_genes[sig_genes['log2FoldChange'] < 0].index.tolist()

   enr_up = gp.enrichr(gene_list=up_genes, gene_sets='KEGG_2021_Human',
                        organism='human', outdir=None)
   enr_dn = gp.enrichr(gene_list=dn_genes, gene_sets='KEGG_2021_Human',
                        organism='human', outdir=None)
   ```

4. **Step 4: Report results immediately**
   - Emit pathway IDs and counts before attempting name resolution
   - Optionally resolve pathway names in a non-blocking manner

   ```r
   result_ids <- setdiff(pathways_condA, pathways_condB)
   count <- length(result_ids)
   cat("Answer:", count, "pathways unique to condition A\n")
   cat("Pathway IDs:", paste(result_ids, collapse = ", "), "\n")

   # Optional: resolve names (non-blocking)
   names <- tryCatch(keggGet(result_ids), error = function(e) NULL)
   ```

5. **Step 5: Cross-condition comparison (if applicable)**
   - Run separate up/down enrichment for each condition (4 enrichKEGG calls total)
   - Compare pathway sets within the same direction
   - Report the union of direction-specific unique pathways

   ```r
   # Condition A
   up_pathways_A <- subset(as.data.frame(ekegg_up_A), p.adjust < 0.05)$ID
   dn_pathways_A <- subset(as.data.frame(ekegg_dn_A), p.adjust < 0.05)$ID

   # Condition B
   up_pathways_B <- subset(as.data.frame(ekegg_up_B), p.adjust < 0.05)$ID
   dn_pathways_B <- subset(as.data.frame(ekegg_dn_B), p.adjust < 0.05)$ID

   # Find pathways unique to condition A in each direction
   unique_up <- setdiff(up_pathways_A, up_pathways_B)
   unique_dn <- setdiff(dn_pathways_A, dn_pathways_B)

   # Union
   unique_to_A <- union(unique_up, unique_dn)
   cat("Pathways in A but not B:", length(unique_to_A), "\n")
   cat("  From up-regulated:", length(unique_up), "-",
       paste(unique_up, collapse = ", "), "\n")
   cat("  From down-regulated:", length(unique_dn), "-",
       paste(unique_dn, collapse = ", "), "\n")
   ```

6. **Step 6: Handle API failures with retry logic**
   - If KEGG API calls fail, retry with timeout before falling back to offline data

   ```r
   fetch_kegg_with_retry <- function(organism_code, max_retries = 3,
                                      timeout_sec = 30) {
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

## Further Reading

- [KEGG: Kyoto Encyclopedia of Genes and Genomes](https://www.kegg.jp/) -- Official KEGG database with pathway maps, organism lists, and REST API documentation
- [clusterProfiler: an R package for comparing biological themes among gene clusters](https://doi.org/10.1089/omi.2011.0118) -- Original publication by Guangchuang Yu describing the enrichKEGG and gseKEGG functions
- [gseapy documentation](https://gseapy.readthedocs.io/) -- Python package for gene set enrichment analysis with offline KEGG gene set support
- [KEGG REST API reference](https://rest.kegg.jp/kegg/rest_api.html) -- Technical documentation for programmatic access to KEGG pathway data

## Related Skills

- `gseapy-gene-enrichment` -- Python-based gene set enrichment analysis; use as a fallback when clusterProfiler KEGG API calls fail, or as the primary tool for Python-based workflows
- `deseq2-differential-expression` / `pydeseq2-differential-expression` -- Upstream differential expression analysis that produces the DEG lists used as input to KEGG pathway enrichment
