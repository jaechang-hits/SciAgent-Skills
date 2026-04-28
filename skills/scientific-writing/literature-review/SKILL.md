---
name: "literature-review"
description: "Conducting systematic, scoping, and narrative literature reviews. Covers PRISMA/PRISMA-ScR protocols, search strategy (Boolean, MeSH), database selection (PubMed, Scopus, Web of Science, Embase), screening, data extraction, evidence synthesis (narrative, meta-analysis, thematic), and reporting. Use when planning or executing a formal literature review."
license: "CC-BY-4.0"
---

# Conducting a Literature Review

## Overview

A literature review systematically identifies, appraises, and synthesizes published evidence on a defined research question. The method ranges from informal narrative reviews to highly structured systematic reviews with meta-analysis. Choosing the correct review type, building a reproducible search strategy, and applying transparent inclusion/exclusion criteria are the foundational decisions that determine whether a review can be trusted and published in a high-impact journal. This guide covers the full workflow from question formulation to synthesis and reporting.

## Key Concepts

### 1. Review Type Taxonomy

| Review Type | Definition | When to Use | Time Required |
|-------------|-----------|-------------|--------------|
| **Narrative review** | Selective, expert-curated synthesis; no protocol; no PRISMA | Introducing a topic; describing mechanistic background | Days to weeks |
| **Scoping review** | Comprehensive mapping of evidence landscape; PRISMA-ScR; no quality appraisal | Understand what evidence exists before committing to systematic review | Weeks to months |
| **Systematic review** | Exhaustive search; predefined protocol (PROSPERO); quality appraisal; PRISMA | Answer a specific clinical/scientific question with highest rigor | Months to years |
| **Meta-analysis** | Systematic review + quantitative pooling of effect estimates | Quantify pooled effect size and heterogeneity across studies | Months to years |
| **Umbrella review** | Systematic review of existing systematic reviews | Synthesize evidence from multiple reviews on one topic | Months |
| **Rapid review** | Streamlined systematic review with time-limited methods | Time-sensitive policy or clinical decisions | Weeks |

**Peer reviewer expectations**: Journals in the biomedical domain expect systematic and scoping reviews to follow PRISMA or PRISMA-ScR reporting standards and to be pre-registered in PROSPERO (systematic reviews only). Narrative reviews are typically invited by editors rather than submitted unsolicited.

### 2. PICO / PICOS Framework for Question Formulation

Systematic reviews require a precisely defined research question. The PICO framework structures the question into searchable, operationalizable components:

| Component | Meaning | Example (for a clinical question) |
|-----------|---------|----------------------------------|
| **P** | Population | Adults with type 2 diabetes aged ≥ 40 |
| **I** | Intervention | SGLT2 inhibitors (empagliflozin, dapagliflozin) |
| **C** | Comparison | Placebo or standard care |
| **O** | Outcome | Cardiovascular mortality, HbA1c, eGFR decline |
| **S** | Study design (PICOS) | Randomized controlled trials only |

For basic science questions, adapt to PECO (Population, Exposure, Comparator, Outcome) or a custom framework. A well-formed PICO directly maps to search terms for each database.

### 3. Evidence Hierarchy

Different study designs provide different levels of certainty about causal effects. Standard hierarchy for intervention questions (highest to lowest):

```
Systematic reviews and meta-analyses of RCTs (highest certainty)
    ↓
Individual randomized controlled trials (RCTs)
    ↓
Non-randomized controlled trials / quasi-experiments
    ↓
Prospective cohort studies
    ↓
Retrospective cohort / case-control studies
    ↓
Cross-sectional studies
    ↓
Case series and case reports
    ↓
Expert opinion / narrative review / editorials (lowest certainty)
```

For diagnostic accuracy, prognosis, and etiology questions, the hierarchy differs. The GRADE framework (Grading of Recommendations Assessment, Development and Evaluation) formalizes evidence quality across four domains: risk of bias, inconsistency, indirectness, and imprecision.

### 4. Database Coverage

No single database covers all literature. Major databases and their coverage:

| Database | Coverage | Strength | Access |
|----------|----------|----------|--------|
| **PubMed / MEDLINE** | >35M biomedical records; 1946+ | Free; MeSH controlled vocabulary; high precision | Free |
| **Embase** | >34M records; European + drug focus; 1947+ | Best for pharmacology and European journals | Subscription |
| **Web of Science** | ~90M records across science and humanities | Citation analysis; interdisciplinary | Subscription |
| **Scopus** | ~90M records; broad | Largest abstract database; good non-English | Subscription |
| **CINAHL** | Nursing and allied health | Best for nursing/PT/OT research | Subscription |
| **PsycINFO** | Psychology and behavioral science | Deep coverage of behavioral literature | Subscription |
| **Cochrane CENTRAL** | Controlled trials only; curated | Highest precision for RCTs | Free/subscription |
| **ClinicalTrials.gov** | US-registered clinical trials | Includes unpublished/ongoing trials | Free |
| **Grey literature** | Reports, theses, guidelines | Reduces publication bias | Various |

Systematic reviews should search at minimum: PubMed + Embase + one domain-specific database + Cochrane CENTRAL (for clinical topics). Searching only PubMed biases toward US/English publications and misses up to 30% of relevant trials.

## Decision Framework

```
What is your literature review goal?
│
├── "Understand the topic background for my paper's Introduction"
│   └── → Narrative review: select key papers; no protocol needed
│
├── "Map what evidence exists before designing a study"
│   └── → Scoping review (PRISMA-ScR): comprehensive but no quality appraisal
│
├── "Answer a specific clinical or scientific question rigorously"
│   ├── Quantitative data poolable across studies?
│   │   ├── Yes → Systematic review + meta-analysis (PRISMA + PROSPERO)
│   │   └── No → Systematic review with narrative synthesis only
│   └── Time-constrained (policy deadline)?
│       └── → Rapid review (document scope limitations)
│
└── "Synthesize existing systematic reviews"
    └── → Umbrella review
```

| Review type | Pre-registration required? | Quality appraisal? | Reporting standard | Minimum databases |
|-------------|---------------------------|-------------------|--------------------|------------------|
| Narrative | No | No | None formal | Author's choice |
| Scoping | No (recommended) | No | PRISMA-ScR | ≥2 major databases |
| Systematic | Yes (PROSPERO) | Yes (RoB 2, ROBINS-I, etc.) | PRISMA 2020 | ≥3 databases |
| Meta-analysis | Yes (PROSPERO) | Yes | PRISMA 2020 | ≥3 databases |
| Umbrella | Recommended | Yes (AMSTAR-2) | PRISMA | ≥2 databases |

## Best Practices

1. **Register systematic reviews in PROSPERO before screening begins**: Registration after screening introduces risk of outcome reporting bias (selectively reporting favorable results). PROSPERO registration is free, takes 2–3 days for approval, and is required by most high-impact journals publishing systematic reviews. Include a draft protocol with primary and secondary outcomes, eligibility criteria, and analysis plan.

2. **Build search strategies with a medical librarian, then peer-review the search**: Systematic review search strategies are technically complex — balancing sensitivity (comprehensive recall) and specificity (manageable results). Most university libraries offer free search consultation. The PRESS (Peer Review of Electronic Search Strategies) checklist provides a structured framework for a second librarian to validate the search.

3. **Screen in two stages with at least two independent reviewers at each stage**: Stage 1 (title/abstract): 2 reviewers independently assess each record; disagreements resolved by a third reviewer or consensus. Stage 2 (full-text): same process. Single-reviewer screening at either stage is not acceptable for a systematic review published in a peer-reviewed journal.

4. **Pilot test your eligibility criteria on 50–100 records before full screening**: Before screening the full results set, both reviewers independently screen the same 50–100 records and calculate inter-rater agreement (Cohen's kappa). Kappa < 0.6 indicates the eligibility criteria are ambiguous and must be refined. Refining criteria after full screening introduces bias.

5. **Use structured data extraction forms with pre-defined fields**: Design the extraction form before reading full texts, based on your PICO components and outcomes. Pre-defining fields prevents selective extraction of only favorable data. Tools: Cochrane's RevMan, Covidence, Rayyan, or a structured Excel/Google Sheets template.

6. **Search for grey literature and trial registries to reduce publication bias**: Studies with null or negative results are less likely to be published in peer-reviewed journals (publication bias). Searching ClinicalTrials.gov, WHO ICTRP, OpenGrey, and government reports captures unpublished and ongoing evidence that may shift the pooled estimate.

7. **Report according to PRISMA 2020 and include the PRISMA flow diagram**: The PRISMA 2020 checklist has 27 items across title, abstract, introduction, methods, results, discussion, and other sections. The flow diagram shows records identified, screened, assessed for eligibility, and included at each stage. Most journals require the PRISMA checklist as a supplementary submission item.

## Common Pitfalls

1. **Starting the search before finalizing eligibility criteria**: Running database searches before defining inclusion/exclusion criteria leads to circular logic — researchers unconsciously adjust criteria based on what papers they found.
   - *How to avoid*: Write and finalize the eligibility criteria (including PICO, study design, language, date range, and publication type restrictions) before running any database search. Register in PROSPERO to lock in the protocol.

2. **Searching only PubMed and calling it systematic**: PubMed covers MEDLINE but misses significant literature indexed only in Embase, PsycINFO, CINAHL, or regional databases. A single-database search fails the comprehensiveness criterion for a systematic review.
   - *How to avoid*: Use at least 3 databases for clinical topics; document all databases searched, date of search, and search strings in the Methods section.

3. **Updating search results during screening without documenting the update**: Literature is published continuously; some researchers run updated searches mid-screening and add results without documenting. This invalidates the flow diagram and makes the review non-reproducible.
   - *How to avoid*: Define a database lock date before screening begins. If an update is needed, document it as a separate search with its own date and numbers. Consider running a final "top-up" search immediately before submission.

4. **Applying inclusion criteria inconsistently between screeners**: Without a piloting phase, Screener A may interpret "adult" as ≥18 and Screener B as ≥21, or one screener may include conference abstracts while the other excludes them.
   - *How to avoid*: Pilot screen on 50–100 records, calculate kappa, discuss every disagreement to align interpretations, and update the eligibility criteria document with clarifying examples before full screening.

5. **Conducting meta-analysis when studies are too heterogeneous**: Pooling estimates from studies with very different populations, interventions, outcomes, or follow-up durations produces a misleading "average" that may not apply to any real clinical scenario. I² > 75% typically signals unacceptably high statistical heterogeneity.
   - *How to avoid*: Pre-specify a heterogeneity threshold (e.g., I² < 50% required for pooling) in the PROSPERO protocol. When heterogeneity is high, report a narrative synthesis with subgroup analysis, not a single pooled estimate.

6. **Omitting quality/risk of bias assessment**: Without appraising study quality, a systematic review cannot assess confidence in the evidence. Reviewers routinely reject systematic reviews that compile evidence without evaluating methodological rigor.
   - *How to avoid*: Select the appropriate risk of bias tool before screening: RoB 2 (randomized trials), ROBINS-I (non-randomized interventions), QUADAS-2 (diagnostic accuracy), NOS (cohort/case-control). Apply it to all included studies and include results in the synthesis.

7. **Writing the discussion as if a narrative review**: After conducting a rigorous systematic review, authors sometimes revert to selective, opinion-driven discussion that ignores the quality appraisal results and treats all evidence as equivalent.
   - *How to avoid*: Anchor each discussion paragraph to specific evidence quality assessments. Use GRADE language: "moderate-certainty evidence suggests..."; "low-certainty evidence from a single small RCT...". Distinguish what the evidence shows from what the authors believe.

## Workflow

1. **Question formulation and scoping**
   - Define the research question using PICO/PECS framework
   - Conduct a preliminary search (PubMed, Google Scholar) to confirm the topic is not already covered by a recent systematic review
   - Decide on review type (systematic, scoping, narrative)
   - Write the protocol; register in PROSPERO (systematic reviews)

2. **Search strategy development**
   - Identify index terms (MeSH for PubMed, Emtree for Embase) + free-text synonyms for each PICO component
   - Combine within components using OR; combine components using AND
   - Have search peer-reviewed using PRESS checklist
   - Run searches across all databases; record date, database, and total hits

3. **Deduplication and screening**
   - Import all results into reference manager or screening tool (Rayyan, Covidence)
   - Remove duplicates (automated + manual)
   - Stage 1: title/abstract screening by ≥2 independent reviewers; resolve conflicts
   - Stage 2: full-text screening by ≥2 independent reviewers; document reasons for exclusion
   - Calculate and report inter-rater agreement (Cohen's kappa)

4. **Data extraction and quality appraisal**
   - Extract data using pre-designed structured forms
   - Assess risk of bias using appropriate tool (RoB 2, ROBINS-I, QUADAS-2, NOS)
   - Contact study authors for missing data if needed

5. **Synthesis**
   - Narrative synthesis: tabulate studies, describe patterns, explore heterogeneity qualitatively
   - Meta-analysis (if appropriate): calculate pooled effect estimates (OR, RR, MD, SMD) with 95% CI; test heterogeneity (I², Cochran Q); assess publication bias (funnel plot, Egger's test)
   - Rate certainty of evidence using GRADE

6. **Reporting and submission**
   - Draft manuscript following PRISMA 2020 checklist
   - Create PRISMA flow diagram
   - Submit PRISMA checklist as supplementary material
   - Share search strategies, data extraction forms, and risk of bias assessments as supplementary data or OSF repository

## Further Reading

- [PRISMA 2020 statement and checklist](https://www.prisma-statement.org/) — the standard reporting guideline for systematic reviews and meta-analyses
- [Cochrane Handbook for Systematic Reviews of Interventions](https://training.cochrane.org/handbook) — comprehensive methodological reference; freely available
- [PROSPERO registration](https://www.crd.york.ac.uk/prospero/) — international register for systematic review protocols
- [Rayyan systematic review screening tool](https://www.rayyan.ai/) — free web-based title/abstract screening platform
- [GRADE Working Group](https://www.gradeworkinggroup.org/) — evidence quality assessment framework used in clinical systematic reviews

## Related Skills

- `citation-management` — reference managers for collecting and organizing search results before and during review
- `statistical-analysis` — statistical methods for meta-analysis (pooled effects, heterogeneity, forest plots)
- `scientific-critical-thinking` — evaluating individual study quality and interpreting effect sizes in the context of a review
