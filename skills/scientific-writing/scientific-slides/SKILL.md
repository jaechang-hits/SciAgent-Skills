---
name: scientific-slides
description: "Scientific presentations for conferences, seminars, thesis defenses, and grant pitches. Slide design, talk structure, timing, data viz for slides, QA. PowerPoint and LaTeX Beamer. For posters use latex-research-posters."
license: CC-BY-4.0
---

# Scientific Slides — Presentation Design and Delivery

## Overview

Scientific presentations are a critical medium for communicating research at conferences, seminars, defenses, and professional talks. This knowhow covers end-to-end presentation development: structure and content planning, visual design principles, data visualization adaptation, timing and pacing, and quality assurance across PowerPoint and LaTeX Beamer formats.

## Key Concepts

### 1. Talk Types and Their Requirements

| Talk Type | Duration | Slides | Focus | Key Finding Count |
|-----------|----------|--------|-------|-------------------|
| Conference talk | 10–20 min | 12–20 | 1–2 key findings | 1–2 |
| Academic seminar | 45–60 min | 40–60 | Comprehensive coverage | 3–6 |
| Thesis defense | 45–60 min | 45–65 | Full dissertation | All studies |
| Grant pitch | 10–20 min | 12–18 | Significance + feasibility | Preliminary data |
| Journal club | 20–45 min | 20–40 | Critical analysis | Paper's findings |

### 2. Visual Design Principles

**Visual-first approach**: Start with visuals (figures, diagrams, images), then add text as support. Target 60–70% visual content, 30–40% text. Every slide should have a strong visual element.

**Typography**:
- Title: 36–44 pt, bold, sans-serif (Arial, Calibri, Helvetica)
- Body: 24–28 pt (not just 18 pt minimum — aim higher for readability)
- Captions/annotations: 18–20 pt
- Maximum 2–3 font families

**Color**:
- Select a modern palette matching your topic (biotech = vibrant, physics = sleek darks, health = warm tones)
- 3–5 colors total with high contrast (7:1 preferred)
- Color-blind safe (avoid red-green combinations)
- Do NOT use default PowerPoint/Beamer themes without customization

**Layout**:
- One main idea per slide
- 40–50% white space
- Vary layouts: full-figure, two-column (text + figure), visual overlay (not all bullet lists)
- Asymmetric compositions (more engaging than centered)
- Rule of thirds for focal points

### 3. Data Visualization for Slides

Key differences from journal figures:
- **Simplify**: fewer panels per slide, split complex figures across slides
- **Enlarge**: 18–24 pt minimum for labels (larger than journal standard)
- **Direct label**: put labels on the data, not in legends
- **Emphasize**: use color and size to highlight key findings
- **Progressive disclosure**: reveal data incrementally for complex figures

| Chart Type | Best For | Slide Adaptation |
|-----------|----------|-----------------|
| Bar chart | Category comparison | Max 6–8 bars, large labels |
| Line graph | Trends over time | Bold lines, 2–3 series max |
| Scatter plot | Correlations | Large points, trend line |
| Heatmap | Matrix patterns | High contrast, annotate key cells |
| Flowchart | Methodology | Build step-by-step with animations |

### 4. Universal Story Arc

Every scientific talk follows this narrative structure:

1. **Hook** — grab attention (30–60 seconds)
2. **Context** — establish importance (5–10% of talk)
3. **Problem/Gap** — identify what's unknown (5–10%)
4. **Approach** — explain your solution (15–25%)
5. **Results** — present key findings (40–50%)
6. **Implications** — discuss meaning (15–20%)
7. **Closure** — memorable conclusion (1–2 minutes)

## Decision Framework

### Implementation Tool Selection

```
Start: What is your priority?
├── Mathematical content, equations, version control?
│   └── YES → LaTeX Beamer (see assets/beamer templates)
├── Editable slides, company templates, animations?
│   └── YES → PowerPoint (programmatic or template-based)
├── Fast creation, non-technical audience, visual impact?
│   └── YES → PowerPoint or image-based PDF
└── Not sure
    └── PowerPoint (most flexible default)
```

### Slide Count Decision Table

| Duration | Simple Topic | Average | Complex Topic |
|----------|-------------|---------|---------------|
| 5 min | 5–6 | 6–8 | 5–7 |
| 10 min | 10–12 | 12–14 | 10–12 |
| 15 min | 14–16 | 16–18 | 14–16 |
| 30 min | 25–30 | 30–35 | 25–30 |
| 45 min | 38–45 | 45–50 | 38–45 |
| 60 min | 50–55 | 55–65 | 50–60 |

General rule: ~1 slide per minute. Complex slides (results, methodology) may take 2–3 minutes; simple slides (transitions, section dividers) take 15–30 seconds.

### Time Allocation

| Section | % of Time | 15-min Talk | 45-min Talk |
|---------|-----------|------------|------------|
| Introduction | 15–20% | 2–3 min | 7–9 min |
| Methods | 15–20% | 2–3 min | 7–9 min |
| Results | 40–50% | 6–7 min | 18–22 min |
| Discussion | 15–20% | 2–3 min | 7–9 min |
| Conclusion | 5% | 45 sec | 2 min |

## Best Practices

1. **MANDATORY: Every slide must have a strong visual element** — figure, chart, diagram, image, or icon. Text-only bullet list slides fail to communicate science effectively. Target minimum 2 visual elements per content slide.

2. **MANDATORY: Practice with a timer at least 3 times before presenting.** Set timing checkpoints: for a 15-minute talk, check at 3–4 min (finishing intro), 7–8 min (midway through results), 12–13 min (starting conclusions).

3. **Use minimal text as visual support.** 3–4 bullets per slide, 4–6 words per bullet. Text is the supporting role; visuals are the stars. Never put full paragraphs on slides.

4. **Include proper citations.** Cite 3–5 papers in the introduction (establishing context) and 3–5 in the discussion (comparison). Use author-year format (Smith et al., 2023) for readability.

5. **Design section dividers with visual breaks.** Insert visually distinctive slides between major sections (intro → methods → results → conclusion). These help the audience reset and follow the narrative.

6. **Anti-pattern — using default templates without customization.** Default PowerPoint/Beamer themes signal "minimal effort." Choose a modern color palette, customize fonts, and add visual personality matching your topic.

7. **Simplify journal figures for slides.** Increase all labels to 18–24 pt, remove non-essential panels, use direct labeling instead of legends, emphasize the key finding with color or annotation.

8. **Anti-pattern — cramming full paper content into slides.** A 15-minute talk should cover 1–2 key findings, not the entire paper. Leave details for the written paper and prepare backup slides for Q&A.

9. **Prepare backup slides.** Put additional data, detailed methods, alternative analyses after the "Thank You" slide. Reference them during Q&A without disrupting the main talk flow.

10. **Never skip conclusions.** If running behind, cut earlier content (skip a results slide or compress methods). The conclusion is the audience's take-away message — skipping it wastes the entire talk.

## Common Pitfalls

1. **Text-heavy, visual-poor slides.** Walls of text, no images or graphics, bullet points as the only content. *How to avoid*: Start slide creation with visuals first (which figure/diagram?), then add minimal text as support.

2. **Font sizes too small (under 24pt body text).** Back-row audience can't read, slides look cramped. *How to avoid*: Set body text to 24–28 pt, titles to 36–44 pt. Test by viewing slides at 50% zoom — if you can't read it, the audience can't either.

3. **Too many findings for the time slot.** Trying to present 5 findings in a 15-minute talk rushes everything. *How to avoid*: Conference talks = 1–2 findings. Seminars = 3–5. Choose ruthlessly.

4. **Missing research context (no citations).** Claims without supporting literature undermine credibility. *How to avoid*: Search literature before creating slides. Cite 3–5 papers in intro and 3–5 in discussion.

5. **Inconsistent formatting across slides.** Different fonts, colors, and layouts from slide to slide look unprofessional. *How to avoid*: Use master slides/templates. Define your color palette, fonts, and layout grid before starting content.

6. **Low contrast text on background.** Light gray text on white, or colored text on busy images. *How to avoid*: Ensure text-background contrast ratio ≥ 7:1. Use solid color overlays on image backgrounds.

7. **Not practicing with timer.** First run-through is during the actual presentation, causing time overruns. *How to avoid*: Practice minimum 3 times. Mark timing checkpoints on your notes.

8. **Skipping conclusions when running over time.** Rushing through or omitting the take-away message. *How to avoid*: Cut earlier content (a results slide) rather than the conclusion. Prepare a "Plan B" with marked skip-able slides.

## Workflow

### Stage 1: Planning

1. **Define context**: talk type (conference/seminar/defense), duration, audience (specialist/general/mixed), venue (room size, virtual/in-person)
2. **Develop content outline**: identify 1–3 core messages, select 3–6 key figures, allocate time per section
3. **Search literature**: find 8–15 relevant papers for citations (3–5 for introduction context, 3–5 for discussion comparison)
4. **Choose implementation tool**: PowerPoint (editable, animations, company templates) vs. LaTeX Beamer (equations, version control, mathematical content)
5. **Plan slide-by-slide**: title, key points, visual element for each slide

### Stage 2: Design and Creation

1. **Start from template** (see Companion Assets for Beamer; use master slides for PowerPoint)
2. **Select modern color palette**: match your topic — 3–5 colors with high contrast
3. **Configure typography**: sans-serif, 24–28 pt body, 36–44 pt titles
4. **Create varied layouts**: mix full-figure slides, two-column (text + figure), visual overlays
5. **Add section dividers**: visually distinctive slides between major sections

### Stage 3: Content Development

1. **Visual backbone first**: place all figures, charts, diagrams, images before adding text
2. **Generate figures**: create presentation-appropriate plots using matplotlib, plotly, or seaborn — larger fonts (18–24 pt labels), fewer panels, direct labeling, high contrast
3. **Add minimal text**: bullet points complement visuals, don't replace them
4. **Include citations**: author-year format on relevant slides (small text, bottom or near data)
5. **Add transitions**: control information flow with builds for complex slides
6. **Prepare presentation aids**: for physical presentations, bring backup copies, adapters, handouts

### Stage 4: Validation and Refinement

1. **Visual inspection**: check each slide for text overflow, element overlap, font sizes, contrast
2. **Readability test**: view at 50% zoom — everything should still be readable
3. **Content review**: verify narrative flow, one idea per slide, consistent formatting
4. **Peer review**: ask colleague for 30-second test (can they identify the main message?)
5. **Compilation check** (Beamer): verify no LaTeX warnings, all figures render correctly

### Stage 5: Practice and Delivery

1. **Practice 3–5 times** with timer: run 1 (rough), run 2 (smooth transitions), run 3 (exact timing), run 4+ (polish)
2. **Set timing checkpoints**: mark 3–4 points on notes (e.g., "should be here by 4 min")
3. **Practice transitions**: connecting phrases between sections
4. **Prepare for Q&A**: anticipate questions, prepare backup slides with additional data
5. **Final checks**: multiple copies (laptop, cloud, USB), test on presentation computer, backup PDF

## Protocol Guidelines

### LaTeX Beamer Compilation

```bash
# Basic compilation
pdflatex presentation.tex

# With bibliography
pdflatex presentation.tex && bibtex presentation && pdflatex presentation.tex && pdflatex presentation.tex

# Better font support
lualatex presentation.tex
```

### PowerPoint Quality Control

- Export to PDF and review at 100% zoom
- Check all slides in Slide Sorter view for consistency
- Test animations and builds in Slideshow mode
- Verify file size (< 50 MB for email; compress images if needed)

## Bundled Resources

Detailed reference files in `references/`:

| File | Content |
|------|---------|
| `talk_types_guide.md` | Detailed structure and strategy for each talk type (conference, seminar, defense, grant pitch, journal club) with example outlines |
| `slide_design_guide.md` | Extended design principles: color theory, typography tables, layout patterns, accessibility guidelines, Gestalt principles for visual composition |

## Further Reading

- Edward Tufte, *The Visual Display of Quantitative Information* — foundational principles for data visualization
- [Web AIM Contrast Checker](https://webaim.org/resources/contrastchecker/) — WCAG compliance for slide readability
- Jean-Luc Doumont, *Trees, Maps, and Theorems* — structured scientific communication
- [Coblis Color Blindness Simulator](https://www.color-blindness.com/coblis-color-blindness-simulator/) — test slide accessibility

## Related Skills

- **matplotlib-scientific-plotting** — generate publication-quality figures adapted for slide presentation (larger fonts, simplified panels)
- **plotly-interactive-visualization** — create interactive figures exportable as static images for slides
- **seaborn-statistical-visualization** — statistical plots with automatic aggregation for results slides
- **latex-research-posters** — poster-specific design guidance; shares typography and color principles with slides

## Companion Assets

Templates and guides in `assets/`:

| File | Description |
|------|-------------|
| `beamer_template_conference.tex` | LaTeX Beamer template for 15-minute conference talks |
| `beamer_template_seminar.tex` | LaTeX Beamer template for 45-minute academic seminars |
| `beamer_template_defense.tex` | LaTeX Beamer template for thesis/dissertation defenses |
| `timing_guidelines.md` | Comprehensive timing and pacing strategies for all talk types |
