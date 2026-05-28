# PubMed Common Query Templates

Ready-to-use query templates organized by research domain. Adapt terms and date ranges for your specific search.

## Disease-Specific Queries

### Cancer Research

```
# General cancer research (recent)
neoplasms[mh] AND (immunotherapy[tiab] OR checkpoint inhibitor[tiab]) AND 2023:2024[dp]

# Specific cancer type with treatment
breast neoplasms[mh] AND (HER2[tiab] OR trastuzumab[nm]) AND randomized controlled trial[pt]

# Cancer biomarkers
(tumor markers, biological[mh] OR biomarkers[tiab]) AND cancer[tiab] AND liquid biopsy[tiab]

# Cancer genomics
(genomics[mh] OR whole genome sequencing[tiab]) AND neoplasms[mh] AND precision medicine[tiab]
```

### Cardiovascular Disease

```
# Heart failure treatment
heart failure[mh] AND (SGLT2 inhibitors[tiab] OR empagliflozin[nm]) AND clinical trial[pt]

# Hypertension management
hypertension[mh]/drug therapy AND (guideline[pt] OR meta-analysis[pt]) AND 2023:2024[dp]

# Atrial fibrillation
atrial fibrillation[mh] AND (anticoagulants[mh] OR ablation[tiab]) AND systematic review[pt]
```

### Diabetes

```
# Type 2 diabetes treatment
diabetes mellitus, type 2[mh]/drug therapy AND (GLP-1[tiab] OR semaglutide[nm]) AND 2023:2024[dp]

# Diabetes complications
diabetes mellitus[mh] AND (diabetic nephropathy[mh] OR diabetic retinopathy[mh]) AND prevention[tiab]

# Diabetes + obesity
diabetes mellitus, type 2[mh] AND obesity[mh] AND (weight loss[tiab] OR bariatric[tiab])
```

### Infectious Diseases

```
# Antibiotic resistance
drug resistance, microbial[mh] AND (MRSA[tiab] OR carbapenem[tiab]) AND 2023:2024[dp]

# COVID-19 long-term effects
COVID-19[mh] AND (long COVID[tiab] OR post-acute[tiab]) AND systematic review[pt]

# Tuberculosis
tuberculosis[mh] AND (drug therapy[sh] OR treatment outcome[mh]) AND 2022:2024[dp]

# Emerging infections
(disease outbreaks[mh] OR emerging infectious diseases[tiab]) AND surveillance[tiab]
```

### Neurological Disorders

```
# Alzheimer's disease
alzheimer disease[mh] AND (amyloid[tiab] OR tau[tiab] OR biomarkers[mh]) AND clinical trial[pt]

# Parkinson's disease
parkinson disease[mh] AND (gene therapy[tiab] OR neuroprotection[tiab]) AND 2023:2024[dp]

# Depression treatment
depressive disorder, major[mh] AND (psychotherapy[mh] OR antidepressive agents[mh]) AND meta-analysis[pt]
```

## Population-Specific Queries

```
# Pediatric
child[mh] AND asthma[mh] AND (treatment[tiab] OR management[tiab]) AND guideline[pt]

# Geriatric
aged[mh] AND (polypharmacy[tiab] OR drug interactions[mh]) AND systematic review[pt]

# Pregnancy
pregnancy[mh] AND (gestational diabetes[tiab] OR preeclampsia[mh]) AND 2023:2024[dp]

# Sex-specific
(sex factors[mh] OR sex differences[tiab]) AND cardiovascular diseases[mh] AND 2023:2024[dp]
```

## Methodology Queries

```
# Machine learning in medicine
(machine learning[tiab] OR deep learning[tiab] OR artificial intelligence[mh]) AND
(diagnosis[sh] OR prognosis[sh]) AND 2023:2024[dp]

# GWAS studies
genome-wide association study[pt] AND (diabetes[tiab] OR obesity[tiab])

# Gene expression / transcriptomics
(gene expression profiling[mh] OR RNA-seq[tiab] OR transcriptome[tiab]) AND cancer[tiab]

# CRISPR / gene editing
(CRISPR[tiab] OR gene editing[tiab]) AND (therapeutic[tiab] OR clinical[tiab]) AND 2023:2024[dp]

# Proteomics
proteomics[mh] AND (mass spectrometry[mh] OR LC-MS[tiab]) AND biomarkers[tiab]

# Cohort studies
cohort studies[mh] AND cardiovascular diseases[mh] AND risk factors[mh] AND 2020:2024[dp]

# Randomized controlled trials
randomized controlled trial[pt] AND (diabetes mellitus[mh] OR hypertension[mh]) AND 2024[dp]
```

## Drug Research Queries

```
# Drug efficacy
drug name[nm] AND (efficacy[tiab] OR effectiveness[tiab]) AND randomized controlled trial[pt]

# Drug safety / adverse effects
drug name[nm] AND (adverse effects[sh] OR drug-related side effects[mh]) AND systematic review[pt]

# Comparative effectiveness
(drug A[nm] OR drug B[nm]) AND comparative study[pt] AND condition[mh]

# Drug repurposing
drug repositioning[tiab] AND (computational[tiab] OR machine learning[tiab]) AND 2023:2024[dp]
```

## Epidemiology Queries

```
# Prevalence / incidence
condition[mh]/epidemiology AND (prevalence[tiab] OR incidence[tiab]) AND global[tiab]

# Risk factors
risk factors[mh] AND disease[mh] AND (prospective[tiab] OR longitudinal[tiab])

# Health disparities
healthcare disparities[mh] AND (racial[tiab] OR ethnic[tiab]) AND United States[mh]

# Global health
global health[mh] AND (developing countries[mh] OR low-income[tiab]) AND 2023:2024[dp]
```

## Systematic Review Templates

### PICO Framework Template

```
# P: Population
(condition_mesh[mh] OR condition_synonym[tiab]) AND

# I: Intervention
(intervention_name[nm] OR intervention_term[tiab]) AND

# C: Comparison (optional)
(comparator[tiab] OR placebo[tiab] OR standard of care[tiab]) AND

# O: Outcome
(outcome_measure[tiab] OR outcome_mesh[mh]) AND

# Study design filter
(randomized controlled trial[pt] OR systematic review[pt] OR meta-analysis[pt])
```

### Comprehensive Search Strategy Template

```
# Concept 1: condition (MeSH + free text synonyms)
(condition_mesh[mh] OR synonym1[tiab] OR synonym2[tiab] OR synonym3[tiab]) AND

# Concept 2: intervention (MeSH + free text + drug names)
(intervention_mesh[mh] OR intervention[tiab] OR drug_name[nm]) AND

# Concept 3: study design
(randomized controlled trial[pt] OR controlled clinical trial[pt] OR
 random*[tiab] OR placebo[tiab] OR blind*[tiab]) AND

# Limits
english[la] AND 2015:2024[dp]

# Exclusions (optional)
NOT (animals[mh] NOT humans[mh])
NOT (comment[pt] OR editorial[pt] OR letter[pt])
```

## Author and Institution Queries

```
# Single author
smith ja[au] AND 2023:2024[dp]

# First author
smith ja[1au] AND cancer[tiab]

# Affiliation
(harvard[affil] OR "harvard university"[affil]) AND 2024[dp]

# Grant-funded research
R01[gr] AND NIH[gr] AND cancer[tiab] AND 2024[dp]
```

## Journal-Specific Queries

```
# High-impact journals
(nature[ta] OR science[ta] OR cell[ta] OR "new england journal of medicine"[ta] OR lancet[ta])
AND topic[tiab] AND 2024[dp]

# By ISSN
0028-0836[issn] AND topic[tiab]  # Nature
```

## Quality Filters

```
# Exclude non-research articles
NOT (comment[pt] OR editorial[pt] OR letter[pt] OR news[pt])

# Only peer-reviewed
NOT (preprint[pt])

# Only English
english[la]

# Humans only
humans[mh] NOT (animals[mh] NOT humans[mh])
```

## Advanced Combination Patterns

```
# Precision medicine
(precision medicine[tiab] OR personalized medicine[tiab] OR pharmacogenomics[mh]) AND
(biomarkers[tiab] OR genetic testing[tiab]) AND
clinical application[tiab] AND 2020:2024[dp]

# Translational research
(translational medical research[mh] OR "bench to bedside"[tiab]) AND
(clinical trial[pt] OR cohort studies[mh]) AND 2023:2024[dp]

# Multi-omics
(multiomics[tiab] OR multi-omics[tiab] OR integrative genomics[tiab]) AND
(machine learning[tiab] OR systems biology[tiab]) AND 2023:2024[dp]
```

Condensed from original: references/common_queries.md (453 lines). Retained: all disease domains, population types, methodology categories, PICO template, quality filters. Omitted: redundant alternative formulations of the same query; diagnostic research templates (use `sensitivity and specificity[mh]` pattern from search_syntax.md clinical filters).
