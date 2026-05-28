# PubMed Search Syntax Reference

## Boolean Operators

| Operator | Function | Example |
|----------|----------|---------|
| AND | Both terms required (default between words) | `cancer AND treatment` |
| OR | Either term matches | `(metformin OR insulin)` |
| NOT | Exclude term | `cancer NOT review[pt]` |

**Precedence**: Left-to-right; use parentheses for grouping.
```
(diabetes OR obesity) AND (treatment OR therapy) NOT review[pt]
```

## Phrase and Wildcard Searching

| Syntax | Purpose | Example |
|--------|---------|---------|
| `"double quotes"` | Exact phrase match | `"gene expression"` |
| `term*` | Wildcard (min 4 chars before *) | `vaccin*` matches vaccine, vaccination |
| `"term1 term2"[TIAB:~N]` | Proximity (within N words) | `"breast cancer screening"[TIAB:~5]` |

**Note**: Wildcards disable automatic term mapping.

## Complete Field Tag Reference

### Author Tags

| Tag | Field | Example |
|-----|-------|---------|
| `[au]` | Author (any position) | `smith ja[au]` |
| `[1au]` | First author | `smith ja[1au]` |
| `[lastau]` | Last author | `jones b[lastau]` |
| `[fau]` | Full author name | `smith, john a[fau]` |
| `[ir]` | Investigator (grant PI) | `doe j[ir]` |
| `[cois]` | Conflict of interest | — |

### Title and Abstract Tags

| Tag | Field | Example |
|-----|-------|---------|
| `[ti]` | Title only | `CRISPR[ti]` |
| `[ab]` | Abstract only | `biomarker[ab]` |
| `[tiab]` | Title OR abstract | `gene editing[tiab]` |
| `[tw]` | Text word (all text fields) | `mutation[tw]` |
| `[ot]` | Other term (keywords) | `machine learning[ot]` |

### Journal Tags

| Tag | Field | Example |
|-----|-------|---------|
| `[ta]` | Journal abbreviation | `Science[ta]` |
| `[jour]` | Full journal name | `Nature Medicine[jour]` |
| `[issn]` | ISSN | `0028-0836[issn]` |

### Date Tags

| Tag | Field | Example |
|-----|-------|---------|
| `[dp]` | Publication date | `2024[dp]`, `2020:2024[dp]` |
| `[edat]` | Entrez date (added to PubMed) | `2024/01[edat]` |
| `[crdt]` | Create date | `2024[crdt]` |
| `[mhda]` | MeSH date (indexing completed) | `2024[mhda]` |

### MeSH Tags

| Tag | Field | Example |
|-----|-------|---------|
| `[mh]` | MeSH heading (includes narrower) | `diabetes mellitus[mh]` |
| `[majr]` | Major MeSH topic | `neoplasms[majr]` |
| `[mesh]` | MeSH terms (no explosion) | `diabetes mellitus[mesh]` |
| `[sh]` | MeSH subheading | `therapy[sh]` |
| `[nm]` | Substance name | `aspirin[nm]` |

### Publication and Identifier Tags

| Tag | Field | Example |
|-----|-------|---------|
| `[pt]` | Publication type | `systematic review[pt]` |
| `[la]` | Language | `english[la]` |
| `[pmid]` | PubMed ID | `12345678[pmid]` |
| `[doi]` | Digital Object Identifier | `10.1038/s41586[doi]` |
| `[pmc]` | PubMed Central ID | `PMC123456[pmc]` |
| `[affil]` | Author affiliation | `harvard[affil]` |
| `[gr]` | Grant number | `R01CA123456[gr]` |
| `[vi]` | Volume | `456[vi]` |
| `[pg]` | Page | `123-130[pg]` |

## Filter Types

### Article Type Filters

| Filter | Query |
|--------|-------|
| Clinical Trial | `clinical trial[pt]` |
| Randomized Controlled Trial | `randomized controlled trial[pt]` |
| Meta-Analysis | `meta-analysis[pt]` |
| Systematic Review | `systematic review[pt]` |
| Review | `review[pt]` |
| Case Reports | `case reports[pt]` |
| Guideline | `guideline[pt]` |
| Practice Guideline | `practice guideline[pt]` |
| Observational Study | `observational study[pt]` |
| Comparative Study | `comparative study[pt]` |

### Text Availability

| Filter | Query |
|--------|-------|
| Free full text | `free full text[sb]` |
| Full text available | `full text[sb]` |
| Has abstract | `hasabstract[text]` |

### Species Filters

| Filter | Query |
|--------|-------|
| Humans | `humans[mh]` |
| Animals | `animals[mh]` NOT `humans[mh]` |
| Mice | `mice[mh]` |
| Rats | `rats[mh]` |

### Age Group Filters

| Filter | MeSH | Age Range |
|--------|------|-----------|
| Newborn | `infant, newborn[mh]` | Birth–1 month |
| Infant | `infant[mh]` | 1–23 months |
| Child, Preschool | `child, preschool[mh]` | 2–5 years |
| Child | `child[mh]` | 6–12 years |
| Adolescent | `adolescent[mh]` | 13–18 years |
| Young Adult | `young adult[mh]` | 19–24 years |
| Adult | `adult[mh]` | 19–44 years |
| Middle Aged | `middle aged[mh]` | 45–64 years |
| Aged | `aged[mh]` | 65+ years |

### Sex Filters

| Filter | Query |
|--------|-------|
| Female | `female[mh]` |
| Male | `male[mh]` |

## Automatic Term Mapping (ATM)

When no field tag is specified, PubMed maps terms through this cascade:

1. **MeSH Translation Table** → maps to MeSH term if found
2. **Journals Translation Table** → maps to journal if found
3. **Author Index** → maps to author if found
4. **Full Text Search** → searches all fields

**To bypass ATM**:
- Use explicit field tags: `cancer[tiab]`
- Use quoted phrases: `"breast cancer"`
- Use truncation: `cancer*`

**Check ATM behavior**: Use Advanced Search → Search Details to see how PubMed translated your query.

## Clinical Query Filters

PubMed provides validated search filters for clinical questions:

| Category | Narrow (high specificity) | Broad (high sensitivity) |
|----------|--------------------------|-------------------------|
| Therapy | `randomized controlled trial[pt]` | `clinical trial[pt] OR random*[tiab]` |
| Diagnosis | `sensitivity and specificity[mh]` | `(sensitiv*[tiab] OR diagnos*[tiab])` |
| Etiology | `cohort studies[mh] OR risk[tiab]` | `(risk*[tiab] OR cohort*[tiab])` |
| Prognosis | `prognosis[mh] AND cohort[tiab]` | `(prognos*[tiab] OR course[tiab])` |

## Troubleshooting Search Issues

| Problem | Likely Cause | Solution |
|---------|-------------|----------|
| Too many results | Query too broad | Add field tags, MeSH terms, date/type filters |
| Too few results | Over-restrictive terms | Use OR for synonyms, remove filters one at a time |
| No results | Misspelling or wrong syntax | Check ESpell; verify field tag exists |
| Unexpected results | ATM mapping to wrong term | Use explicit field tags; check Search Details |
| MeSH term not found | Term too specific or newly coined | Search MeSH Browser; use `[tiab]` instead |

Condensed from original: references/search_syntax.md (436 lines). Retained: all field tags, all filter types, ATM explanation, clinical query filters. Omitted: verbose prose explanations and repeated examples (covered in SKILL.md Core API).
