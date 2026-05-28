# GWAS Catalog REST API — Endpoint Reference

Base URL: `https://www.ebi.ac.uk/gwas/rest/api`

All endpoints return HAL+JSON. Paginated endpoints accept `size` (default 20, max 500) and `page` (0-indexed).

---

## 1. Study Endpoints

| Endpoint | Method | Parameters | Description |
|----------|--------|------------|-------------|
| `/studies` | GET | `size`, `page` | List all studies |
| `/studies/{accessionId}` | GET | -- | Get study by GCST accession |
| `/studies/search/findByDiseaseTrait` | GET | `diseaseTrait` | Search studies by trait keyword |
| `/studies/search/findByPubmedId` | GET | `pubmedId` | Search studies by PubMed ID |
| `/studies/search/findByFullPvalueSet` | GET | `fullPvalueSet` (bool) | Filter studies with summary statistics |
| `/studies/search/findByEfoTrait` | GET | `efoTrait` (EFO URI) | Studies for a specific EFO trait |
| `/studies/search/findByEfoUri` | GET | `efoUri` | Studies by full EFO URI |

### Study Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `accessionId` | string | GCST accession (e.g., `GCST000392`) |
| `title` | string | Study title |
| `diseaseTrait.trait` | string | Reported disease/trait |
| `publicationInfo.pubmedId` | string | PubMed identifier |
| `publicationInfo.author.fullname` | string | First author name |
| `publicationInfo.publication` | string | Journal name |
| `publicationInfo.publicationDate` | string | Publication date (YYYY-MM-DD) |
| `initialSampleSize` | string | Discovery sample description |
| `replicationSampleSize` | string | Replication sample description |
| `genotypingTechnologies` | array | Genotyping platform(s) used |
| `fullPvalueSet` | boolean | Whether summary statistics are available |
| `lastUpdateDate` | string | Last catalog update for this study |

---

## 2. Association Endpoints

| Endpoint | Method | Parameters | Description |
|----------|--------|------------|-------------|
| `/associations` | GET | `size`, `page` | List all associations |
| `/associations/{associationId}` | GET | -- | Get association by ID |
| `/efoTraits/{efoId}/associations` | GET | `size`, `page` | Associations for a trait |
| `/singleNucleotidePolymorphisms/{rsId}/associations` | GET | `size`, `page` | Associations for a variant |
| `/studies/{accessionId}/associations` | GET | `size`, `page` | Associations from a study |

### Association Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `pvalue` | float | Association p-value |
| `pvalueMantissa` | float | P-value mantissa |
| `pvalueExponent` | int | P-value exponent |
| `orPerCopyNum` | float | Odds ratio per copy of risk allele |
| `betaNum` | float | Beta coefficient (for quantitative traits) |
| `betaUnit` | string | Unit for beta (e.g., "mg/dl") |
| `betaDirection` | string | Direction of effect ("increase"/"decrease") |
| `range` | string | Confidence interval text (e.g., "[1.2-1.5]") |
| `standardError` | float | Standard error of effect estimate |
| `riskFrequency` | string | Risk allele frequency |
| `loci[].strongestRiskAlleles[].riskAlleleName` | string | Risk allele (e.g., "rs7903146-T") |
| `loci[].strongestRiskAlleles[].snps[].rsId` | string | Variant rs ID |
| `loci[].authorReportedGenes[].geneName` | string | Author-reported gene name |
| `efoTraits[].shortForm` | string | EFO short form (e.g., `EFO_0001360`) |
| `efoTraits[].trait` | string | Trait description |

---

## 3. Variant (SNP) Endpoints

| Endpoint | Method | Parameters | Description |
|----------|--------|------------|-------------|
| `/singleNucleotidePolymorphisms` | GET | `size`, `page` | List all variants |
| `/singleNucleotidePolymorphisms/{rsId}` | GET | -- | Get variant by rs ID |
| `/singleNucleotidePolymorphisms/search/findByChromBpLocationRange` | GET | `chrom`, `bpStart`, `bpEnd` | Variants in a chromosomal region |
| `/singleNucleotidePolymorphisms/search/findByCytogeneticBand` | GET | `cytogeneticBand` | Variants by cytoband |
| `/singleNucleotidePolymorphisms/search/findByGene` | GET | `geneName` | Variants near a gene |

### Variant Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `rsId` | string | dbSNP reference ID (e.g., `rs7903146`) |
| `functionalClass` | string | Functional annotation (e.g., "intron_variant") |
| `merged` | int | Merged SNP status (0 = not merged) |
| `lastUpdateDate` | string | Last update date |
| `locations[].chromosomeName` | string | Chromosome number |
| `locations[].chromosomePosition` | int | Base pair position (GRCh38) |
| `locations[].region.name` | string | Cytogenetic band |
| `genomicContexts[].gene.geneName` | string | Nearby gene name |
| `genomicContexts[].distance` | int | Distance to gene (bp) |
| `genomicContexts[].isClosestGene` | boolean | Whether this is the closest gene |
| `genomicContexts[].isIntergenic` | boolean | Whether variant is intergenic |

---

## 4. Trait Endpoints

| Endpoint | Method | Parameters | Description |
|----------|--------|------------|-------------|
| `/efoTraits` | GET | `size`, `page` | List all EFO traits |
| `/efoTraits/{efoId}` | GET | -- | Get trait by EFO short form |
| `/efoTraits/search/findByDescription` | GET | `description` | Search traits by keyword |
| `/efoTraits/search/findByEfoUri` | GET | `efoUri` | Search by full EFO URI |

### Trait Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `shortForm` | string | EFO short form (e.g., `EFO_0001360`) |
| `trait` | string | Trait description (e.g., "type II diabetes mellitus") |
| `uri` | string | Full EFO URI |

---

## 5. Gene Endpoints

| Endpoint | Method | Parameters | Description |
|----------|--------|------------|-------------|
| `/genes/search/findByGeneName` | GET | `geneName` | Find gene by name |
| `/genes/{geneName}` | GET | -- | Get gene details |

Gene data is also accessible through variant genomic contexts (see Variant Response Fields).

---

## 6. Summary Statistics Endpoints

Summary statistics are accessed through study endpoints and the GWAS Catalog FTP:

| Access Method | URL Pattern | Description |
|---------------|-------------|-------------|
| REST: studies with stats | `/studies/search/findByFullPvalueSet?fullPvalueSet=True` | Find studies that deposited summary stats |
| REST: study metadata | `/studies/{accessionId}` | Check `fullPvalueSet` field |
| FTP download | `ftp.ebi.ac.uk/pub/databases/gwas/summary_statistics/{GCSTID}/` | Download full summary statistics files |

Summary statistics files are typically tab-separated (.tsv or .tsv.gz) with columns: `variant_id`, `p_value`, `chromosome`, `base_pair_location`, `effect_allele`, `other_allele`, `effect_allele_frequency`, `beta`, `standard_error`, `odds_ratio`, `ci_lower`, `ci_upper`.

---

## Error Handling

| HTTP Status | Meaning | Action |
|-------------|---------|--------|
| `200` | Success | Parse response JSON |
| `400` | Bad request (invalid parameters) | Check parameter names/values |
| `404` | Resource not found | Verify identifier exists |
| `500` | Server error | Retry after delay |
| `503` | Service unavailable | EBI maintenance; retry later |

Error responses return JSON:
```json
{
  "error": "Not Found",
  "message": "Study with accession GCST999999 not found",
  "status": 404
}
```

---

## Pagination Pattern

```python
def gwas_get_all(endpoint, params=None):
    """Fetch all pages from a paginated GWAS endpoint."""
    params = params or {}
    params["size"] = 500
    params["page"] = 0
    all_items = []
    while True:
        data = gwas_get(endpoint, params)
        key = list(data.get("_embedded", {}).keys())[0]
        all_items.extend(data["_embedded"][key])
        if params["page"] >= data["page"]["totalPages"] - 1:
            break
        params["page"] += 1
    return all_items
```

---

Condensed from original: api_reference.md (794 lines). Retained: all 6 endpoint groups with parameters, association/study/variant/trait response field tables, error handling, pagination pattern, summary statistics access. Omitted: child/parent trait hierarchy traversal details, advanced multi-parameter query composition examples, changelog and versioning notes, detailed HAL link-following patterns -- these are specialized and covered by EBI's official API documentation.
