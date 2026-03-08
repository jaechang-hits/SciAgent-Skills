# Slide Design Principles for Scientific Presentations

## Core Design Principles

### 1. Simplicity and Clarity

Each slide should communicate ONE main idea. Audiences process limited information at once — complexity causes cognitive overload. Simple slides are remembered; busy slides are forgotten.

### 2. Visual Hierarchy

Guide attention through size, color, and position:

| Level | Purpose | Size | Contrast |
|-------|---------|------|----------|
| Primary | Main message or key data | Largest (36–54 pt) | Highest |
| Secondary | Supporting information | Medium (24–32 pt) | Medium |
| Tertiary | Details and labels | Smallest (14–18 pt) | Lower |

**Position**: Top-left or top-center for primary content (Western reading pattern). Center for focal visuals. Bottom or sides for supporting details.

### 3. Consistency

Keep consistent throughout: fonts (1–2 families), colors (3–5 palette), layouts (similar slides use same structure), spacing, and style. Create 3–5 layout variants (title, content, figure, section divider) and apply consistently.

## Typography

### Font Selection

**Recommended Sans-Serif Fonts**: Arial, Helvetica, Calibri, Gill Sans, Futura, Avenir

**Avoid**: Script/handwriting fonts (illegible), decorative fonts (distracting), condensed fonts (hard to read), >2 font families

### Font Sizes

| Element | Size Range | Notes |
|---------|-----------|-------|
| Title slide title | 44–54 pt | Largest element |
| Section headers | 36–44 pt | Section dividers |
| Slide titles | 32–40 pt | Every content slide |
| Body text | 24–28 pt | Absolute minimum 18 pt |
| Figure labels | 18–24 pt | Must be readable from back |
| Captions/citations | 14–16 pt | Use sparingly |

**Room Test**: Body text should be readable at 6× screen height distance. View slides at 50% zoom — if you can't read it, the audience can't either.

### Text Formatting

- **Line length**: Maximum 50–60 characters per line
- **Line spacing**: 1.2–1.5× line height
- **Alignment**: Left-aligned for body (natural reading), center for titles/key messages. Avoid justified (awkward spacing)
- **Emphasis**: Bold for key terms (sparingly). Color for emphasis (consistent meaning). Avoid italics (hard from distance), underline (confused with links), ALL CAPS for body

### The 6×6 Rule

Maximum 6 bullets per slide, maximum 6 words per bullet. Better: 3–4 bullets, 4–8 words each. Use fragments, not sentences — you provide explanation verbally.

## Color Theory

### Color Palettes for Scientific Presentations

**Professional/Academic** (Conservative):
- Navy (#1C3D5A), gray (#4A5568), white (#FFFFFF)
- Accent: Orange (#E67E22) or green (#27AE60)
- Use: Faculty seminars, grant presentations, institutional talks

**Modern/Engaging** (Energetic):
- Teal (#0A9396), coral (#EE6C4D), cream (#F4F1DE)
- Accent: Burgundy (#780000)
- Use: Conference talks, public engagement

**High Contrast** (Maximum Legibility):
- Black (#000000) on white (#FFFFFF), or dark blue (#003366) on white
- Use: Large venues, virtual presentations, accessibility priority

**Data Visualization** (Color-blind Safe):
- Blue (#0173B2), orange (#DE8F05), green (#029E73), magenta (#CC78BC)
- Based on Wong/IBM palettes

### Color Contrast and Accessibility

**WCAG Standards**:
- Level AA: 4.5:1 contrast ratio minimum
- Level AAA: 7:1 contrast ratio (preferred for presentations)

**High Contrast Combinations**:
- Black on white (21:1)
- Dark blue (#003366) on white (12.6:1)
- White on dark gray (#2D3748) (11.8:1)
- Dark text (#333333) on cream (#F4F1DE) (9.7:1)

**Avoid**: Light gray on white, yellow on white, pastel on white, red on black

### Color Blindness Considerations

~8% of men, ~0.5% of women have color vision deficiency. Most common: red-green (protanopia/deuteranopia).

**Safe Practices**:
- Use blue/orange instead of red/green
- Add patterns or shapes in addition to color
- Test with color blindness simulator (Coblis)
- Label directly on plot rather than color legend only

**Color-Blind Safe Palette**:
```
Primary: Blue (#0173B2)
Contrast: Orange (#DE8F05)
Additional: Magenta (#CC78BC), Teal (#029E73)
```

## Layout and Composition

### The Rule of Thirds

Divide slide into 3×3 grid; place key elements at intersections or along lines. More visually interesting than centered layouts. Natural eye flow.

### White Space

Minimum 5–10% margins on all sides. Clear separation between unrelated items. Don't fill every pixel — empty space is valuable. Projects professionalism and confidence.

### Layout Patterns

**Title + Content**: Standard slide, most common. Content area below title.

**Two Column**: Text on left, figure on right (or vice versa). Use for comparisons or text+figure combinations.

**Full-Slide Figure**: Large visual takes full slide. Use for key results, impactful visuals.

**Text Overlay**: Text box over background image. Use for title slides, section dividers. Add semi-transparent overlay for contrast.

**Grid Layout**: 2×3 or 3×2 grid of related items. Use for multiple comparisons.

### Alignment

Align elements to create visual order. Use edge alignment (left edges of text), center alignment (titles), or grid alignment (snap to invisible grid). Misaligned elements appear careless.

## Background Design

**Light Backgrounds** (Most Common): White (#FFFFFF), off-white (#F8F9FA), light gray (#F5F5F5). Maximum contrast, works in any lighting, easier on projectors.

**Dark Backgrounds**: Dark gray (#2D3748), navy (#1A202C). Modern, sophisticated, good for dark venues. But harder in bright rooms and requires light text.

**Gradients**: Only subtle gradients (light to lighter). Avoid busy or high-contrast gradients.

**Image Backgrounds**: Only for title/section slides. Ensure contrast with text. Add semi-transparent overlay.

## Animation and Builds

### When to Use

**Appropriate**: Progressive disclosure (reveal points one at a time), build complex figures incrementally, show sequential processes, control pacing.

**Inappropriate**: Decoration, every slide transition, multiple effects per slide, spin/bounce/spiral effects.

### Best Practices

- Fast transitions (0.2–0.3 seconds)
- Consistent animation type throughout
- Click to advance (not automatic)
- Use Appear or Fade only (avoid Fly In, Bounce)
- Builds should add clarity, not complexity

## Common Design Mistakes

| Mistake | Problem | Fix |
|---------|---------|-----|
| Too much text | Audience reads instead of listens | Key phrases, not paragraphs |
| Too many concepts per slide | Cognitive overload | One idea per slide, split |
| Inconsistent formatting | Unprofessional, distracting | Use templates, style guide |
| Poor contrast | Illegible from distance | Test at presentation size |
| Tiny fonts (<18 pt body) | Unreadable | Minimum 24 pt body text |
| Cluttered slides | No clear focal point | Embrace white space |
| Low-quality images | Pixelated figures | 300 DPI minimum |
| Overuse of effects | Looks amateurish | Minimal/no shadows, 3D |
| Red-green combinations | Invisible to 8% of men | Use blue-orange + patterns |

## Accessibility Checklist

**Visual Impairments**: High contrast (7:1 preferred), large fonts (24 pt+ body), no color-only meaning

**Color Blindness**: Avoid red-green, add patterns/labels, test with simulator

**Presentation Environment**: Works in various lighting, visible from back of room, readable on different screens, printable in grayscale

## Design Workflow

1. **Define visual identity**: Choose 3–5 colors, 1–2 fonts, overall style
2. **Create master templates**: 4–6 layouts (title, section divider, content, figure, two-column, closing)
3. **Apply consistently**: Choose template per slide, add content, ensure alignment
4. **Review**: Every slide has clear focus, text is minimal, hierarchy is clear, colors accessible, alignment precise

## Design Resources

**Color Tools**: Coolors.co (palette generator), Adobe Color (scheme creator), WebAIM Contrast Checker, Coblis (color blindness simulator)

**Icon Sources**: Font Awesome, Noun Project, BioIcons (science-specific), Flaticon
