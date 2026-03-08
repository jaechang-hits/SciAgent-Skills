---
name: "scientific-manuscript-writing"
description: "Scientific manuscript writing knowledge: IMRAD structure, citation styles (APA/AMA/Vancouver/IEEE), figures and tables best practices, reporting guidelines (CONSORT/STROBE/PRISMA/ARRIVE), writing principles (clarity/conciseness/accuracy), field-specific terminology, venue-specific style adaptation. For LaTeX report formatting see companion assets."
license: "CC-BY-4.0"
---

# Scientific Manuscript Writing

## Overview

Scientific manuscript writing is the discipline of communicating research findings with precision, clarity, and reproducibility. This knowhow covers the complete lifecycle of manuscript preparation: from planning and structuring a paper using IMRAD format, through applying correct citation styles and designing effective figures, to ensuring compliance with study-specific reporting guidelines. It applies across biomedical, social science, engineering, and computational fields.

This entry consolidates writing principles, manuscript structure, citation systems, figure/table design, and reporting standards into a unified reference for producing publication-ready scientific documents.

## Key Concepts

### Writing Principles: Clarity, Conciseness, Accuracy

The three pillars of scientific writing govern all manuscript text:

- **Clarity**: Use precise, unambiguous language. Define technical terms at first use. Maintain logical flow within and between paragraphs. Use active voice when it improves understanding; passive voice is acceptable in Methods when the action matters more than the actor.
- **Conciseness**: Express ideas in the fewest words necessary. Eliminate redundant phrases ("due to the fact that" becomes "because"; "in order to" becomes "to"). Favor shorter sentences (15-20 words average). Use strong verbs instead of noun-verb combinations ("analyze" not "perform an analysis").
- **Accuracy**: Report exact values with appropriate precision matched to measurement capability. Use consistent terminology throughout. Distinguish observations from interpretations. Verify that numbers in text match tables and figures.

Additional principles include **objectivity** (present results without bias, acknowledge conflicting evidence), **consistency** (same term for same concept, uniform notation), and **logical organization** (clear "red thread" connecting sections). See `references/writing_principles_style.md` for detailed guidance with examples.

### IMRAD Structure

IMRAD (Introduction, Methods, Results, And Discussion) is the standard organizational structure for original research articles, adopted across most scientific disciplines since the 1970s. It mirrors the scientific method:

| Section | Question Answered | Primary Tense | Typical Length |
|---------|-------------------|---------------|----------------|
| **Title** | What is this about? | N/A | 10-15 words |
| **Abstract** | Complete summary | Mixed | 100-250 words |
| **Introduction** | Why did you study this? | Present/past | 4-5 paragraphs |
| **Methods** | How did you do it? | Past | 2-4 pages |
| **Results** | What did you find? | Past | 2-4 pages |
| **Discussion** | What does it mean? | Past/present | 3-5 pages |
| **Conclusion** | Take-home message | Present | 1-2 paragraphs |

The Introduction follows a funnel structure: broad context, narrowing literature review, gap identification, and study objectives. Methods must provide sufficient detail for replication. Results present findings objectively without interpretation. Discussion interprets findings, compares with prior work, acknowledges limitations, and proposes future directions.

**Venue variations**: Nature/Science use modified IMRAD with methods in supplement. ML conferences (NeurIPS/ICML) use Introduction-Method-Experiments-Conclusion with numbered contributions and ablation studies. See `references/manuscript_structure.md` for section-by-section guidance.

### Citation Systems

Five major citation styles serve different disciplines:

| Style | Format | Primary Disciplines |
|-------|--------|---------------------|
| **AMA** | Superscript numbers | Medicine, health sciences |
| **Vancouver** | Numbers in brackets [1] | Biomedical sciences |
| **APA** | Author-date (Smith, 2023) | Psychology, social sciences |
| **Chicago** | Notes-bibliography or author-date | Humanities, some sciences |
| **IEEE** | Numbers in brackets [1] | Engineering, computer science |

**Best practices across all styles**: Cite primary sources when possible. Include recent literature (within 5-10 years for active fields, 2-3 years for ML). Balance citation distribution across Introduction and Discussion. Verify all citations against original sources. Keep self-citations below 20%. Always check the target journal's author guidelines for the required style.

See `references/citation_guide.md` for complete format specifications, journal-specific requirements, and DOI formatting rules.

### Figure and Table Design Principles

Figures and tables are the backbone of a scientific paper; many readers examine them before reading the text.

**Decision rule**: Can the information be conveyed in 1-2 sentences? If yes, use text only. If no and precise values are needed, use a table. If no and patterns/trends matter most, use a figure.

**Core design principles**:
1. **Self-explanatory**: Each display item must stand alone with a complete caption defining all abbreviations, units, sample sizes, and statistical annotations
2. **No redundancy**: Text highlights key findings from displays; it does not repeat all data
3. **Consistency**: Uniform formatting, color schemes, and terminology across all display items
4. **Optimal quantity**: Approximately one display item per 1,000 words of manuscript
5. **Accessibility**: Color-blind safe palettes (blue-orange, viridis); designs that work in grayscale

**Error bar rule**: Always state which measure is shown (SD for data spread, SEM for measurement precision, 95% CI for significance assessment). 95% CI is generally preferred because non-overlapping CIs indicate significant differences.

See `references/figures_tables_guide.md` for figure type selection, table formatting, statistical presentation, and journal-specific requirements.

## Decision Framework

```
What type of scientific document are you writing?
|
+-- Original research article
|   |
|   +-- Clinical trial --> IMRAD + CONSORT reporting guideline
|   +-- Observational study --> IMRAD + STROBE reporting guideline
|   +-- Animal study --> IMRAD + ARRIVE reporting guideline
|   +-- Diagnostic accuracy --> IMRAD + STARD reporting guideline
|   +-- Prediction model --> IMRAD + TRIPOD reporting guideline
|   +-- ML/CS research --> Intro-Method-Experiments-Conclusion
|
+-- Review / synthesis
|   +-- Systematic review --> PRISMA reporting guideline
|   +-- Narrative review --> Thematic structure
|   +-- Meta-analysis --> PRISMA + forest plots
|
+-- Case report --> CARE guideline
|
+-- Study protocol --> SPIRIT guideline
|
+-- Quality improvement --> SQUIRE guideline
|
+-- Economic evaluation --> CHEERS guideline
|
+-- Professional report / white paper --> scientific_report.sty (see assets/)
```

| Venue Type | Structure | Citation Style | Key Adaptation |
|-----------|-----------|---------------|----------------|
| Nature/Science | Modified IMRAD, methods in supplement | Numbered superscript | Accessible language, broad significance, story-driven |
| Medical journals (NEJM, JAMA) | Strict IMRAD | Vancouver/AMA | Structured abstracts, clinical focus, CONSORT/STROBE |
| Field-specific journals | Standard IMRAD | Varies by field | Full technical detail, field terminology |
| ML conferences (NeurIPS, ICML) | Intro-Method-Experiments-Conclusion | Numbered or author-year | Numbered contributions, ablations, pseudocode |
| Professional reports | Chapter-based | N/A | Use scientific_report.sty for formatting |

## Best Practices

1. **Write the abstract last**: After completing all sections, synthesize the key message into 100-250 words. Include quantitative results with statistical measures.
2. **Plan figures before writing**: Design figures and tables as the data story backbone. Write Methods first, then Results describing the displays, then Discussion interpreting them, then Introduction framing the question.
3. **One idea per paragraph**: Start with a topic sentence, develop with supporting evidence, end with a transition to the next idea. Target 3-7 sentences per paragraph.
4. **Define abbreviations strategically**: Define at first use in both abstract and main text. Only abbreviate terms used 3+ times. Limit to 3-4 new abbreviations per paper. Standard abbreviations (DNA, RNA, PCR) need no definition.
5. **Use verb tense correctly**: Past tense for completed actions (Methods, Results, prior studies). Present tense for established facts and your interpretations. Present perfect for recent developments with current relevance ("Recent studies have demonstrated...").
6. **Report statistics completely**: For each comparison, include point estimate, variability measure (SD/SEM/CI), sample size, test statistic, exact p-value (not just "p < 0.05"), and effect size with confidence interval.
7. **Follow reporting guidelines from the start**: Identify the appropriate guideline during study design, not after manuscript completion. Use the checklist during drafting to ensure all required elements are captured.
8. **Match writing style to venue**: Review 3-5 recent papers from your target journal. Adapt sentence length, vocabulary level, hedging style, and section proportions to match venue expectations.
9. **Verify citation-reference correspondence**: Every in-text citation must have a reference list entry and vice versa. Check author names, years, titles, and DOIs before submission.
10. **Design for accessibility**: Use color-blind safe palettes. Ensure figures work in grayscale. Maintain minimum 8-10 pt font at final print size. Use vector formats (PDF, EPS) for graphs.

## Common Pitfalls

1. **Overstating conclusions beyond the evidence**: Claiming causation from observational data or generalizing beyond the study population.
   - *How to avoid*: Use appropriate hedging language ("suggests," "is associated with"). Match claim strength to study design.

2. **Inconsistent terminology**: Using different words for the same concept (switching between "medication," "drug," and "pharmaceutical").
   - *How to avoid*: Choose one term per concept and use it throughout. Create a terminology list before drafting.

3. **Mixing verb tenses inappropriately**: Using present tense for your specific results or past tense for established facts.
   - *How to avoid*: Follow the section-specific tense rules. Review each section for tense consistency during revision.

4. **Insufficient methods detail for reproducibility**: Omitting sample sizes, software versions, statistical test justifications, or ethical approval.
   - *How to avoid*: Use the relevant reporting guideline checklist. Have a colleague assess whether they could replicate the study from your Methods section alone.

5. **Redundant data presentation**: Repeating all table values in the text, or duplicating information between figures and tables.
   - *How to avoid*: Text should highlight and interpret key findings from displays, not restate all numbers. Each data point appears in only one format.

6. **Missing or poorly designed error bars**: Omitting error bars entirely, or not specifying whether they represent SD, SEM, or CI.
   - *How to avoid*: Include error bars on all quantitative figures. Define the measure in every caption ("Error bars represent 95% CI").

7. **Abbreviation overload**: Defining too many abbreviations, or abbreviating terms used only once or twice.
   - *How to avoid*: Only abbreviate terms used 3+ times. Limit new abbreviations to 3-4 per paper. Never abbreviate in the title.

8. **Ignoring journal-specific requirements**: Submitting with wrong citation style, exceeding word limits, or using incorrect figure formats.
   - *How to avoid*: Read author guidelines before starting the manuscript. Create a checklist of journal requirements and verify compliance before submission.

## Workflow

1. **Planning Phase**
   - Identify target journal and review author guidelines (word limits, citation style, figure specs)
   - Determine the applicable reporting guideline (CONSORT, STROBE, PRISMA, etc.)
   - Download the reporting checklist and review items that require prospective planning
   - Outline manuscript structure (usually IMRAD unless venue dictates otherwise)

2. **Literature Review**
   - Search for relevant prior work using systematic database queries
   - Organize references in a reference manager (Zotero, Mendeley, EndNote)
   - Identify the knowledge gap your study addresses
   - Note key studies for Introduction and Discussion contexts

3. **Outline Construction**
   - Create section outlines with bullet points noting main arguments, key citations, data points, and logical flow
   - Plan figures and tables as the core data story
   - Map reporting checklist items to manuscript sections

4. **Drafting (section order: Methods, Results, Discussion, Introduction, Abstract, Title)**
   - Convert each outline section into flowing prose paragraphs
   - Methods: describe what was done with sufficient detail for replication
   - Results: present findings objectively, referencing figures and tables
   - Discussion: interpret findings, compare with literature, acknowledge limitations
   - Introduction: establish context, identify gap, state objectives
   - Abstract: synthesize the complete story in 100-250 words
   - Decision point: If writing for a specific venue, consult venue-specific style guides

5. **Figure and Table Finalization**
   - Create publication-quality figures at final size and resolution (300+ dpi)
   - Write self-explanatory captions with all abbreviations, units, sample sizes, and statistical annotations
   - Number displays consecutively in order of first mention
   - Verify that no data is duplicated between text, figures, and tables

6. **Revision and Quality Control**
   - Check logical flow and the "red thread" throughout the manuscript
   - Verify terminology and notation consistency
   - Walk through the reporting guideline checklist item by item
   - Confirm all citations are accurate and properly formatted
   - Proofread for grammar, spelling, and clarity
   - Check word/page counts against journal limits

7. **Submission Preparation**
   - Format according to journal requirements (template, citation style, figure formats)
   - Prepare supplementary materials
   - Complete and upload reporting guideline checklists
   - Write cover letter highlighting significance and fit
   - Gather required statements (funding, conflicts of interest, data availability, ethical approval)
   - Final verification: every in-text citation has a reference entry and vice versa

## Bundled Resources

### Reference Files

| File | Content | Original Source |
|------|---------|----------------|
| `references/writing_principles_style.md` | Clarity/conciseness/accuracy strategies, verb tense rules, word choice, paragraph structure, revision checklist, venue-specific writing styles | Condensed from writing_principles.md (825 lines) |
| `references/manuscript_structure.md` | Complete IMRAD guide, section-by-section content and common mistakes, venue variations, ML conference structure | Condensed from imrad_structure.md (659 lines) |
| `references/citation_guide.md` | AMA, Vancouver, APA, Chicago, IEEE format specifications, journal-specific styles, citation best practices, DOI formatting | Condensed from citation_styles.md (721 lines) |
| `references/figures_tables_guide.md` | Figure type selection, table formatting, statistical presentation, accessibility, journal-specific requirements, submission checklist | Condensed from figures_tables.md (807 lines) |
| `references/reporting_guidelines.md` | CONSORT, STROBE, PRISMA, SPIRIT, STARD, TRIPOD, ARRIVE, CARE, SQUIRE, CHEERS checklist summaries and usage workflow | Condensed from reporting_guidelines.md (749 lines) |

**Omitted**: professional_report_formatting.md (665 lines) -- LaTeX-specific formatting details are covered directly by the `scientific_report.sty` template and its companion `REPORT_FORMATTING_GUIDE.md` in the assets/ directory. Key concepts (box environments, scientific notation commands) are noted in the assets section below.

### Asset Files

| File | Description |
|------|-------------|
| `assets/scientific_report.sty` | LaTeX style package for professional reports (not journal manuscripts). Provides Helvetica typography, colored box environments (keyfindings, methodology, limitations, etc.), alternating-row tables, and scientific notation commands (\pvalue, \effectsize, \CI, \meansd). Compile with XeLaTeX or LuaLaTeX. |
| `assets/scientific_report_template.tex` | Complete LaTeX template demonstrating all style features: title page, executive summary, chapters with box environments, statistical tables, figure formatting, appendices. |
| `assets/REPORT_FORMATTING_GUIDE.md` | Quick reference guide for the style package: color palette (hex values), box environment syntax, scientific notation command reference, table/figure formatting patterns, compilation instructions. |

## Further Reading

- [EQUATOR Network](https://www.equator-network.org/) -- Comprehensive library of reporting guidelines for health research
- [ICMJE Recommendations](http://www.icmje.org/) -- Uniform requirements for manuscripts submitted to biomedical journals
- [APA Style Guide](https://apastyle.apa.org/) -- Official APA Publication Manual resources
- [Nature Masterclasses](https://masterclasses.nature.com/) -- Scientific writing courses from Nature
- [Academic Phrasebank](https://www.phrasebank.manchester.ac.uk/) -- Common academic phrases organized by function (University of Manchester)
- Strunk & White, *The Elements of Style* -- Classic guide to clear writing
- Lebrun, *Scientific Writing: A Reader and Writer's Guide* -- Practical guide for scientific authors

## Related Skills

- `matplotlib-scientific-plotting` -- Create publication-quality figures for manuscripts
- `seaborn-statistical-visualization` -- Statistical visualizations with automatic CI and aggregation
- `plotly-interactive-visualization` -- Interactive figures for supplementary materials
- `statsmodels-statistical-modeling` -- Statistical models whose outputs you report in manuscripts
- `pymc-bayesian-modeling` -- Bayesian analysis results for reporting
- `peer-review-methodology` -- Structured peer review of manuscripts (complements this entry)
- `latex-research-posters` -- Poster preparation using LaTeX
- `scientific-slides` -- Conference presentation preparation
- `scientific-brainstorming` -- Ideation methods for framing research questions

## Companion Assets

- `assets/scientific_report.sty` -- LaTeX style package for professional scientific reports
- `assets/scientific_report_template.tex` -- Complete report template with all style features demonstrated
- `assets/REPORT_FORMATTING_GUIDE.md` -- Quick reference card for box environments, color palette, and scientific notation commands
