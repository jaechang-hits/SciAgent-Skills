---
name: peer-review-methodology
description: "Structured peer review of scientific manuscripts and grants. 7-stage evaluation: initial assessment, section-by-section review, statistical rigor, reproducibility, figure integrity, ethics, and writing quality. Covers CONSORT/STROBE/PRISMA compliance, review report structure (summary, major/minor comments, questions). For evaluating evidence quality use scientific-critical-thinking; for quantitative scoring use scholar-evaluation."
license: CC-BY-4.0
---

# Scientific Peer Review

## Overview

Peer review is a systematic process for evaluating scientific manuscripts and grant proposals. This knowhow covers the complete review cycle: from initial assessment through detailed section-by-section evaluation, statistical rigor checks, reproducibility assessment, figure integrity verification, ethical considerations, and writing quality — culminating in a structured review report with actionable feedback.

## Key Concepts

### 1. Review Types and Expectations

| Review Type | Scope | Typical Length | Key Focus |
|-------------|-------|---------------|-----------|
| **Original research** | Full evaluation | 1–3 pages | Rigor, novelty, reproducibility |
| **Review/Meta-analysis** | Coverage and bias | 1–2 pages | Completeness, search strategy, systematic approach |
| **Methods paper** | Validation | 1–2 pages | Comparison to existing methods, reproducibility |
| **Short communication** | Proportional | 0.5–1 page | Core findings rigor despite brevity |
| **Grant proposal** | Feasibility + significance | 1–3 pages | Innovation, approach, team, budget justification |

### 2. Comment Severity Levels

- **Major comments**: Issues that significantly impact validity, interpretability, or significance. Must be addressed for publication. Examples: fundamental design flaws, unsupported conclusions, missing controls.
- **Minor comments**: Issues that improve clarity or completeness but don't affect core validity. Examples: unclear labels, missing methods details, grammatical errors.
- **Questions for authors**: Requests for clarification where the reviewer cannot evaluate without additional information.

### 3. Reporting Standards Quick Reference

| Standard | Applies to | Key Check |
|----------|-----------|-----------|
| **CONSORT** | Randomized controlled trials | Flow diagram, randomization, blinding, ITT analysis |
| **STROBE** | Observational studies | Study design, setting, participants, variables, bias |
| **PRISMA** | Systematic reviews / meta-analyses | Search strategy, PICO, risk of bias, forest plots |
| **ARRIVE** | Animal research | Species, sample size, randomization, 3Rs |
| **MIAME** | Microarray experiments | Platform, normalization, data deposit (GEO/ArrayExpress) |
| **MINSEQE** | Sequencing experiments | Read counts, mapping, QC metrics, data deposit (SRA) |

## Decision Framework

```
What are you reviewing?
├── Scientific manuscript
│   ├── Original research → Full 7-stage workflow
│   ├── Review / meta-analysis → Emphasize Stage 2 (Introduction + Methods) + Stage 4
│   ├── Methods paper → Emphasize Stage 3 (rigor) + Stage 4 (reproducibility)
│   └── Short communication → Abbreviated workflow (Stages 1, 2, 3, 7)
├── Grant proposal
│   └── Focus on: significance, innovation, approach feasibility, team qualifications
└── Not a document review
    └── Use scientific-critical-thinking for evidence evaluation
```

| Reviewer Situation | Focus Areas | Time Budget |
|-------------------|-------------|-------------|
| First-round journal review | All 7 stages, full detail | 4–8 hours |
| Revision re-review | Only check if previous concerns addressed | 1–2 hours |
| Internal lab feedback | Stages 1–3, 7 (skip ethics, reporting standards) | 2–4 hours |
| Conference abstract | Stage 1 only + brief methods check | 30 min |
| Grant review | Significance + innovation + approach + team | 3–6 hours |

## Best Practices

1. **Read the whole manuscript once before writing any comments**: Resist the urge to annotate during first reading. Your initial impression informs the summary statement and helps distinguish major from minor issues.

2. **Separate description from judgment**: For each concern, first state what you observed ("The authors report p=0.04 without correction for 12 comparisons"), then state why it's problematic ("This inflates the false positive rate"), then suggest a fix ("Apply Bonferroni or FDR correction and re-evaluate significance").

3. **Number every comment for easy reference**: Both major and minor comments should be sequentially numbered so authors can address each one explicitly in their response letter.

4. **State your confidence level on statistical concerns**: If you are uncertain about a statistical issue, say so explicitly ("I am not certain whether the normality assumption holds here — the authors should verify with a Shapiro-Wilk test or use a non-parametric alternative").

5. **Check reporting standards compliance**: Before writing the review, identify which reporting standard applies (CONSORT, STROBE, PRISMA, etc.) and use its checklist to verify completeness. Missing checklist items are legitimate major comments.

6. **Acknowledge strengths explicitly**: Every review should include 2–3 specific strengths. This is not politeness — it tells editors which aspects are sound and helps authors understand what NOT to change during revision.

7. **Never request experiments beyond the study's scope**: A reviewer should point out limitations, not redesign the study. "This limitation should be acknowledged in the Discussion" is appropriate. "The authors should run a new cohort with 500 patients" is not.

8. **Be concrete about figure quality**: Instead of "figures need improvement," say "Figure 3A: y-axis label missing units; error bars are not defined in the legend (SD vs SEM?); color coding is not colorblind-accessible."

9. **Maintain anonymity and professionalism**: In single/double-blind review, avoid self-referential comments ("In our previous work..."). Never use dismissive or condescending language. Frame all criticism constructively.

10. **Match recommendation to evidence**: If your comments are all minor, don't recommend rejection. If you have unresolvable major concerns about study design, don't recommend minor revision. The recommendation must be consistent with the severity of identified issues.

## Common Pitfalls

1. **Reviewing what the paper should be instead of what it is**: Judging the paper against your preferred experimental approach rather than evaluating whether the authors' approach is valid. *How to avoid*: Focus on whether the methods answer the stated research question, not on whether you would have used different methods.

2. **Conflating statistical significance with scientific importance**: A paper with p=0.001 can be trivial; a paper with p=0.06 can be groundbreaking. *How to avoid*: Evaluate effect sizes and practical significance separately from p-values. Ask "Does this matter?" not just "Is this significant?"

3. **Scope creep in revision requests**: Requesting additional experiments that constitute a new study rather than validation of the current one. *How to avoid*: Before writing a revision request, ask "Is this necessary to support the paper's current conclusions?" If it addresses a new question, suggest it as future work instead.

4. **Overlooking positive controls**: Checking for negative controls while ignoring whether the experiment demonstrates it CAN detect the claimed effect. *How to avoid*: For every experiment, check both "What would happen if the effect doesn't exist?" (negative control) AND "What demonstrates the assay actually works?" (positive control).

5. **Copy-paste reviewing**: Using the same boilerplate concerns across different manuscripts without engaging with the specific content. *How to avoid*: Every comment should reference a specific section, figure, or claim in THIS manuscript. Generic advice ("improve writing quality") is unhelpful.

6. **Ignoring supplementary materials**: Many critical methods details and validation data are in supplements. *How to avoid*: Always read supplementary materials, especially methods and figures referenced from the main text.

7. **Asymmetric skepticism**: Being more critical of findings that contradict your expectations while accepting confirmatory findings uncritically. *How to avoid*: Apply the same methodological scrutiny to all results regardless of whether you agree with the conclusions.

## Workflow

### 7-Stage Peer Review Process

1. **Initial assessment** (read full manuscript without annotation): Identify central question, main findings, overall soundness, venue appropriateness. Write 2-3 sentence summary capturing the manuscript's essence

2. **Section-by-section review**: Evaluate each section (Abstract, Introduction, Methods, Results, Discussion, References) against specific criteria:
   - Abstract: accuracy, completeness, clarity
   - Introduction: context, rationale, novelty, literature coverage
   - Methods: reproducibility, rigor, detail, statistical justification
   - Results: presentation logic, completeness, objectivity
   - Discussion: interpretation support, limitations, context, speculation

3. **Statistical and methodological rigor**: Check statistical assumptions, effect sizes, multiple testing correction, sample size justification, appropriate test selection, control adequacy, randomization, blinding

4. **Reproducibility and transparency**: Verify data availability (repositories, accession numbers), code availability, reporting standards compliance (CONSORT/STROBE/PRISMA/ARRIVE), protocol detail

5. **Figure and data integrity**: Check resolution, labeling, error bar definitions, color accessibility, signs of image manipulation, scale bars, data type appropriateness

6. **Ethical considerations**: Verify IRB/IACUC approval, informed consent, 3Rs compliance, conflicts of interest disclosure, funding disclosure, data privacy

7. **Writing quality**: Assess organization, language clarity, jargon use, narrative flow, accessibility to broad audience

### Review Report Structure

After completing all stages, organize feedback into:
- **Summary statement** (1-2 paragraphs): Synopsis, overall recommendation, 2-3 strengths, 2-3 weaknesses
- **Major comments** (numbered): Critical validity/interpretability issues with specific suggestions
- **Minor comments** (numbered): Clarity/completeness improvements with locations
- **Questions for authors**: Specific clarification requests
- **Recommendation**: Accept / Minor revision / Major revision / Reject (consistent with comments)

## Further Reading

- [COPE Ethical Guidelines for Peer Reviewers](https://publicationethics.org/resources/guidelines-new/cope-ethical-guidelines-peer-reviewers) — Committee on Publication Ethics
- [EQUATOR Network](https://www.equator-network.org/) — reporting guidelines for all study types
- Stahel & Moore (2014) "Peer review for biomedical publications: we can improve the system" — *BMC Medicine* 12:179
- Lovejoy et al. (2011) "An introduction to systematic reviewing" — *BMJ Open*
- [How to peer review](https://authorservices.wiley.com/Reviewers/journal-reviewers/how-to-perform-a-peer-review/index.html) — Wiley reviewer guide

## Related Skills

- **scientific-critical-thinking** — evaluating evidence quality and logical reasoning (broader than manuscript review)
- **scientific-writing** — manuscript authoring; understanding the author's perspective helps write better reviews
- **literature-review** — systematic evidence gathering; complements Stage 4 (reproducibility) assessment
- **scholar-evaluation** — quantitative scoring frameworks for automated manuscript assessment
