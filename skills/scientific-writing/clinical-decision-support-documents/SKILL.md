---
name: clinical-decision-support-documents
description: "Guidelines for clinical decision support (CDS) documents: biomarker-stratified cohort analyses and GRADE-graded treatment reports. Covers structure, executive summaries, evidence grading (1A–2C), stats (HR, CI, survival), and biomarker integration. Use for pharma research docs, clinical guidelines, regulatory submissions."
license: CC-BY-4.0
---

# Clinical Decision Support Documents

## Overview

Clinical decision support (CDS) documents are analytical reports for pharmaceutical research, guideline development, and regulatory submissions. This knowhow covers two main document types: Patient Cohort Analyses (biomarker-stratified group outcomes) and Treatment Recommendation Reports (evidence-graded clinical guidelines). For individual patient-level treatment plans, use the `treatment-plans` skill instead.

## Key Concepts

### 1. Document Types

**Patient Cohort Analysis** — Group-level statistical comparison of patient subgroups stratified by biomarkers, molecular subtypes, or clinical characteristics.
- Typical content: demographics, biomarker stratification, outcome metrics (OS, PFS, ORR), Kaplan-Meier curves, forest plots
- Audience: pharmaceutical companies, clinical researchers, regulatory bodies
- Length: 5–15 pages (1-page executive summary + detailed sections)

**Treatment Recommendation Report** — Evidence-based clinical guidelines with GRADE-graded recommendations for disease management.
- Typical content: evidence review, recommendations by line of therapy, decision algorithm flowcharts, monitoring protocols
- Audience: guideline committees, medical affairs, KOLs
- Length: 5–20 pages

### 2. GRADE Evidence Grading System

The Grading of Recommendations, Assessment, Development and Evaluations (GRADE) system classifies recommendations by strength and evidence quality:

| Grade | Strength | Evidence Quality | Meaning |
|-------|----------|-----------------|---------|
| **1A** | Strong | High | Benefits clearly outweigh risks; consistent RCT data |
| **1B** | Strong | Moderate | Benefits likely outweigh risks; limited RCT data |
| **2A** | Weak | High | Trade-offs exist; high-quality evidence but patient values matter |
| **2B** | Weak | Moderate | Uncertain trade-offs; limited evidence |
| **2C** | Weak | Low | Very uncertain; expert opinion or observational data only |

### 3. Outcome Metrics

| Metric | Abbreviation | Definition |
|--------|-------------|------------|
| Overall Survival | OS | Time from treatment start to death from any cause |
| Progression-Free Survival | PFS | Time to disease progression or death |
| Objective Response Rate | ORR | Proportion with CR + PR per RECIST 1.1 |
| Duration of Response | DOR | Time from first response to progression |
| Disease Control Rate | DCR | Proportion with CR + PR + SD |

### 4. Statistical Reporting Standards

- **Hazard ratios**: Report with 95% CI (e.g., HR 0.65, 95% CI 0.48–0.89, p=0.007)
- **Survival data**: Median OS/PFS with 95% CI + landmark rates (6-mo, 12-mo, 24-mo)
- **Response rates**: Point estimate with 95% CI
- **Kaplan-Meier curves**: Include number-at-risk tables below, censoring markers, log-rank p-value
- **Subgroup analyses**: Forest plots with interaction p-values; clearly label pre-specified vs exploratory

## Decision Framework

Use this framework to select the appropriate document type:

```
Is this about a POPULATION or an INDIVIDUAL patient?
├── POPULATION (group-level analysis)
│   ├── Comparing outcomes between subgroups? → Patient Cohort Analysis
│   ├── Developing treatment guidelines? → Treatment Recommendation Report
│   └── Both analysis and recommendations? → Combined (cohort analysis + recommendations chapter)
└── INDIVIDUAL (single patient)
    └── Use treatment-plans skill instead
```

| Scenario | Document Type | Key Sections |
|----------|--------------|-------------|
| Phase 2/3 trial subgroup analysis | Cohort Analysis | Biomarker stratification, survival curves, forest plots |
| Clinical practice guideline | Treatment Recommendations | GRADE-graded recs, decision algorithm, evidence tables |
| Companion diagnostic development | Cohort Analysis | Biomarker-response correlation, sensitivity/specificity |
| Medical affairs strategy | Treatment Recommendations | Competitive landscape, positioning, KOL education |
| Real-world evidence study | Cohort Analysis | EMR cohort definition, outcomes by treatment arm |

## Best Practices

1. **Always start with a full-page executive summary**: Page 1 should contain 3–5 colored summary boxes (findings, biomarkers, implications, statistics, safety) that are scannable in 60 seconds. No table of contents on page 1. This is the single most impactful formatting decision for CDS documents.

2. **Use GRADE consistently**: Every treatment recommendation must have a GRADE rating (1A–2C) with documented rationale. Do not mix GRADE with other rating systems within the same document.

3. **Report effect sizes, not just p-values**: Always include hazard ratios or odds ratios with 95% confidence intervals. A p-value alone does not convey clinical significance or effect magnitude.

4. **Specify biomarker assay details**: Name the platform (e.g., FoundationOne CDx, Ventana PD-L1 SP263), cut-points, and validation status. Biomarker results are only actionable when the assay is known.

5. **Use RECIST 1.1 for response assessment**: For immunotherapy cohorts, note iRECIST criteria and pseudoprogression handling. Clearly state which criteria were used.

6. **Include number-at-risk tables**: Below every Kaplan-Meier curve, show the number of patients at risk at each time point. This is mandatory for credible survival analysis.

7. **Declare data completeness and follow-up**: Report median follow-up time, data maturity (% events), and how missing data was handled (complete case, imputation method).

8. **De-identify per HIPAA Safe Harbor**: Remove all 18 HIPAA identifiers before including any patient-level data. Add confidentiality headers for proprietary pharmaceutical data.

9. **Color-code consistently**: Blue = data/information, green = biomarkers/positive, orange = clinical implications/caution, red = warnings/safety, gray = statistics/methods.

10. **Date and version all recommendations**: Include analysis date, data cutoff date, and planned update schedule. Treatment guidelines become outdated as new trial data emerges.

## Common Pitfalls

1. **Mixing population-level and individual-level recommendations**: CDS documents analyze cohorts, not individuals. Stating "Patient X should receive..." is inappropriate. *How to avoid*: Use language like "Patients with biomarker X may benefit from..." or "Evidence supports [therapy] for [population] (Grade 1B)."

2. **Over-interpreting subgroup analyses**: Post-hoc subgroup analyses are hypothesis-generating, not confirmatory. *How to avoid*: Always label exploratory vs pre-specified subgroups. Report interaction p-values. State "These findings require prospective validation."

3. **Omitting confidence intervals**: Reporting median PFS = 12.5 months without CI makes the precision invisible. *How to avoid*: Always format as "median PFS 12.5 months (95% CI: 9.8–15.2)."

4. **Ignoring competing risks**: In oncology cohorts, patients may die from non-cancer causes, biasing standard Kaplan-Meier estimates. *How to avoid*: For OS analysis, note competing causes. For PFS, acknowledge censoring for non-disease events.

5. **Inconsistent GRADE application**: Grading one recommendation as 1A but not grading others leaves quality gaps. *How to avoid*: Grade every recommendation. If evidence is insufficient, assign 2C with "insufficient evidence" note.

6. **Executive summary that is too detailed**: A 2-page executive summary defeats the purpose. *How to avoid*: Limit to page 1 only. Use bullet points in colored boxes, not paragraphs. End with `\newpage` before TOC.

7. **Missing regulatory compliance elements**: Omitting confidentiality notices or HIPAA de-identification in pharmaceutical documents. *How to avoid*: Add confidentiality header to every page. Include de-identification statement in methods section.

## Workflow

### Standard CDS Document Development Process

1. **Define scope**: Identify document type (cohort analysis vs treatment recommendations), disease state, target audience, and data sources
2. **Gather evidence**: Collect trial data, biomarker results, published guidelines. For recommendations, perform systematic evidence review
3. **Design document structure**: Select appropriate sections based on document type (see Decision Framework). Plan visual elements (survival curves, forest plots, decision algorithms)
4. **Draft executive summary first**: Write the page-1 summary boxes before detailed sections. This forces clarity about key findings
5. **Author detailed sections**: Write each section with proper statistical reporting. For cohort analyses: demographics → biomarkers → outcomes → subgroup comparisons. For recommendations: evidence review → GRADE assessment → recommendations by line → algorithm
6. **Create visual elements**: Generate Kaplan-Meier curves, forest plots, waterfall plots, TikZ decision algorithms. Include number-at-risk tables below survival curves
7. **Apply GRADE ratings** (recommendations only): Assess each recommendation against evidence quality criteria. Document rationale for each grade
8. **Format in LaTeX/PDF**: Apply document template (0.5-inch margins, colored tcolorbox elements, professional tables). Ensure page 1 is executive summary only
9. **Quality check**: Verify HIPAA compliance, statistical completeness (all CIs reported), GRADE consistency, reference completeness

## Protocol Guidelines

### LaTeX Document Setup

CDS documents use specific LaTeX packages and formatting:
- **Margins**: 0.5-inch all sides (compact, data-dense)
- **Color boxes**: `tcolorbox` package with color-coded environments
- **Tables**: `booktabs` for professional formatting, `longtable` for multi-page tables
- **Figures**: TikZ for decision algorithms, `pgfplots` for survival curves
- **First page**: `\thispagestyle{empty}` + executive summary boxes + `\newpage`

### Executive Summary Box Pattern

Each CDS document's page 1 should have 3–5 `tcolorbox` elements:
- **Report Information** (blue): Document type, date, population, methodology
- **Primary Results** (blue): Main efficacy findings with key statistics
- **Biomarker Insights** (green): Molecular subtype findings or biomarker correlations
- **Clinical Implications** (orange): Actionable recommendations or treatment implications
- **Safety/Warnings** (red, if applicable): Critical adverse events or contraindications

### Biomarker Classification Guide

When stratifying cohorts by biomarkers:
- **Genomic**: Mutations (EGFR, KRAS), CNV (HER2 amplification), fusions (ALK, ROS1)
- **Expression**: IHC scores (PD-L1 TPS/CPS), RNA-seq signatures
- **Molecular subtypes**: Disease-specific (PAM50 breast cancer, GBM clusters)
- Always specify: assay platform, cut-point, validation status, FDA companion diagnostic approval

## Further Reading

- [GRADE Handbook](https://gdt.gradepro.org/app/handbook/handbook.html) — official GRADE methodology documentation
- [RECIST 1.1 Guidelines](https://doi.org/10.1016/j.ejca.2008.10.026) — response evaluation criteria in solid tumors
- [CONSORT Statement](https://www.consort-statement.org/) — reporting standards for randomized trials
- [STROBE Statement](https://www.strobe-statement.org/) — reporting standards for observational studies
- [ICH E9 Guidelines](https://www.ich.org/page/efficacy-guidelines) — statistical principles for clinical trials

## Related Skills

- **treatment-plans** — individual patient-level care plans (complementary to population-level CDS)
- **scientific-writing** — manuscript structure, citation management, reporting guidelines
- **statistical-analysis** — detailed statistical methods (Cox regression, Kaplan-Meier, log-rank tests)
- **matplotlib** / **plotly** — figure generation for survival curves, forest plots, waterfall plots
