---
name: hypothesis-generation
description: "Structured hypothesis formulation: turn observations into testable hypotheses with predictions, propose mechanisms, design experiments. Follows the scientific method. Use scientific-brainstorming for open ideation; hypogenic for automated LLM hypothesis testing on datasets."
license: CC-BY-4.0
---

# Scientific Hypothesis Generation

## Overview

Hypothesis generation is a systematic process for developing testable mechanistic explanations from observations. This knowhow covers the full cycle: from understanding a phenomenon through literature synthesis, generating competing hypotheses, evaluating hypothesis quality, designing experimental tests, and formulating testable predictions.

## Key Concepts

### 1. Hypothesis vs Observation vs Prediction

- **Observation**: A factual statement about what was measured or seen (e.g., "Drug X reduces tumor size in mice")
- **Hypothesis**: A proposed mechanistic explanation for the observation (e.g., "Drug X inhibits angiogenesis via VEGF pathway blockade, reducing tumor nutrient supply")
- **Prediction**: A testable consequence of the hypothesis (e.g., "VEGF levels should decrease after Drug X treatment; tumors in VEGF-knockout mice should show no additional effect")

Good hypotheses are mechanistic (explain HOW/WHY), not descriptive (restate WHAT).

### 2. Hypothesis Quality Criteria

| Criterion | Definition | Example of Strong | Example of Weak |
|-----------|-----------|-------------------|-----------------|
| **Testability** | Can be empirically investigated | "Protein X binds to receptor Y" (can test with co-IP) | "Life force drives cellular growth" (untestable) |
| **Falsifiability** | Specific observations would disprove it | "If X is absent, effect disappears" | "X contributes to the effect somehow" |
| **Parsimony** | Simplest explanation fitting the evidence | Single mechanism | Multi-step chain without evidence |
| **Explanatory Power** | Accounts for observed patterns | Explains dose-response and tissue specificity | Explains only one observation |
| **Scope** | Range of phenomena covered | Applies across related systems | Limited to single dataset |
| **Consistency** | Aligns with established knowledge | Consistent with known pathway biology | Contradicts thermodynamics |
| **Novelty** | Offers new insight | Proposes unexplored mechanism | Restates established knowledge |

### 3. Levels of Mechanistic Explanation

Hypotheses can operate at different scales. Strong hypothesis sets include explanations at multiple levels:
- **Molecular**: Protein interactions, gene regulation, enzymatic activity
- **Cellular**: Signaling pathways, cell fate decisions, metabolic changes
- **Tissue/Organ**: Microenvironment, cell-cell communication, organ function
- **Organismal**: Systemic responses, physiological adaptation
- **Population**: Evolutionary pressures, epidemiological patterns

## Decision Framework

```
What is your starting point?
├── Specific observation / data → Follow the full 8-step Workflow below
├── Broad research question → Start with Step 2 (literature search) to narrow scope
├── Existing hypothesis to refine → Start at Step 5 (evaluate quality) and iterate
└── Need creative ideation first → Use scientific-brainstorming skill, then return here
```

| Starting Situation | Approach | Key Steps |
|-------------------|----------|-----------|
| Unexpected experimental result | Phenomenon-driven | Steps 1→2→3→4 (focus on competing explanations) |
| Literature gap identified | Gap-driven | Steps 2→3→4→5 (focus on novelty criterion) |
| Cross-domain analogy noticed | Analogy-driven | Steps 1→4→5→6 (focus on translating mechanism) |
| Contradictory findings in literature | Conflict-driven | Steps 2→3→4→7 (focus on discriminating predictions) |
| Large dataset patterns | Data-driven | Use hypogenic first, then Steps 5→6→7 here |

## Best Practices

1. **Always generate competing hypotheses (3–5)**: A single hypothesis is a confirmation trap. Multiple competing explanations force you to design experiments that discriminate between alternatives, not just confirm your favorite.

2. **Start with mechanism, not correlation**: "X is associated with Y" is not a hypothesis. "X causes Y via mechanism Z" is. Always include the mechanistic link (HOW the cause produces the effect).

3. **Make predictions that differ between hypotheses**: The most valuable predictions are those where Hypothesis A predicts outcome X and Hypothesis B predicts outcome Y. This is called a "crucial experiment" — design your tests around these discriminating predictions.

4. **Ground every hypothesis in evidence**: Cite existing literature for each hypothesis. "It is known that pathway X can regulate process Y [Author, 2023]; therefore, we hypothesize that..." Unsupported hypotheses are speculation, not science.

5. **State falsification criteria explicitly**: For each hypothesis, write "This hypothesis would be falsified if..." before designing experiments. If you cannot state falsification criteria, the hypothesis is untestable.

6. **Consider the null hypothesis**: The simplest explanation — that there is no novel mechanism and observed effects are due to known processes, artifact, or chance — should always be included as one of the competing hypotheses.

7. **Scale predictions quantitatively when possible**: "Expression should increase" is weaker than "Expression should increase 2–5 fold (based on known pathway kinetics)." Quantitative predictions enable power analysis for experimental design.

## Common Pitfalls

1. **Confirmation bias in hypothesis selection**: Generating one "main" hypothesis and 2-3 weak alternatives to make the main one look good. *How to avoid*: Generate hypotheses independently, then rank them by quality criteria. Have someone else review whether alternatives are genuinely competitive.

2. **Untestable "just-so" stories**: Hypotheses that sound plausible but cannot be empirically tested with current technology. *How to avoid*: For each hypothesis, immediately write the experiment that would test it. If you cannot design an experiment, the hypothesis needs revision.

3. **Confusing correlation-based claims with mechanistic hypotheses**: "Gene X is upregulated in disease Y" is not a hypothesis. *How to avoid*: Always include HOW and WHY in the hypothesis statement. Use the template: "[Mechanism] leads to [effect] because [rationale]."

4. **Ignoring contradictory evidence**: Cherry-picking literature that supports your hypothesis while ignoring opposing data. *How to avoid*: In Step 3 (Synthesize Evidence), explicitly section contradictory findings. Each hypothesis must address how it handles conflicting data.

5. **Scope creep in hypothesis evaluation**: Trying to make one hypothesis explain everything. *How to avoid*: A hypothesis does not need to explain all observations — it needs to explain the specific phenomenon under investigation. State scope boundaries explicitly.

6. **Designing experiments that can only confirm**: If your experiment cannot produce a negative result, it does not test your hypothesis. *How to avoid*: For each experiment, write down what "failure" looks like. Include negative and positive controls.

7. **Neglecting feasibility in experimental design**: Proposing experiments requiring technology, samples, or timelines that are unrealistic. *How to avoid*: Include feasibility assessment (available reagents, equipment, sample access, timeline) alongside each experimental proposal.

## Workflow

### Structured Hypothesis Generation Process (8 Steps)

1. **Understand the phenomenon**: Clarify the core observation, define scope and boundaries, note what is known vs uncertain, identify the relevant scientific domain(s)

2. **Conduct literature search**: Search PubMed (biomedical) and general databases for reviews, primary research, related mechanisms, and analogous systems. Look for gaps, contradictions, and unresolved debates

3. **Synthesize existing evidence**: Summarize current understanding, identify established mechanisms that may apply, note conflicting evidence, recognize knowledge gaps, find cross-domain analogies

4. **Generate 3–5 competing hypotheses**: Each must be mechanistic (explain HOW/WHY), distinguishable from others, evidence-grounded, and consider different levels of explanation (molecular → population)

5. **Evaluate hypothesis quality**: Score each hypothesis against the 7 quality criteria (testability, falsifiability, parsimony, explanatory power, scope, consistency, novelty). Note strengths and weaknesses explicitly

6. **Design experimental tests**: For each viable hypothesis, propose specific experiments with: measurements, controls, methods, sample sizes, statistical approaches, and potential confounds

7. **Formulate testable predictions**: State what should be observed if the hypothesis is correct, specify expected direction and magnitude, identify conditions where predictions hold, distinguish predictions between competing hypotheses

8. **Present structured output**: Organize findings into: executive summary, competing hypotheses with evidence, testable predictions, critical comparisons, and detailed appendices (literature review, experimental protocols, quality assessments)

## Further Reading

- Platt, JR (1964) "Strong Inference" — *Science* 146:347-353. Classic paper on designing experiments to discriminate between competing hypotheses
- Popper, KR (1959) "The Logic of Scientific Discovery" — foundational framework for hypothesis falsification
- Chamberlin, TC (1890) "The Method of Multiple Working Hypotheses" — *Science* 15:92-96. Original argument for generating competing explanations
- [NIH Guide to Hypothesis Development](https://www.niaid.nih.gov/grants-contracts/write-research-plan) — practical guidance for grant-writing hypothesis sections
- Kell, DB & Oliver, SG (2004) "Here is the evidence, now what is the hypothesis?" — *BioEssays* 26:99-105. Data-driven hypothesis generation

## Related Skills

- **scientific-brainstorming** — open-ended creative ideation when you need divergent thinking before structured hypothesis formulation
- **scientific-critical-thinking** — evaluating evidence quality and logical reasoning; complements hypothesis quality assessment
- **literature-review** — systematic evidence gathering; feeds into Steps 2–3 of this workflow
- **statistical-analysis** — power analysis and experimental design statistics for Step 6
- **scientific-writing** — structuring hypothesis-driven manuscripts for publication
