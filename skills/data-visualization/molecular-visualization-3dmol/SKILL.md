---
name: "molecular-visualization-3dmol"
description: "3Dmol.js WebGL molecular visualization emitted as self-contained HTML. Render structures (PDB/SDF/XYZ/MOL2/cube) with stick, sphere, cartoon, line, and surface styles; animate trajectories with a frame-delay (interval, ms) control; and animate vibrational normal modes via vibrate() from per-atom dx/dy/dz displacements or from precomputed frames. Output standalone HTML that loads 3Dmol from a CDN, with optional play/pause and speed controls. Use for transition-state imaginary-mode animations, MD or reaction-path playback, docking poses, and orbital/density isosurfaces. For static 2D chemical structure drawings use rdkit-chemdraw-cdxml; for 2D statistical plots use matplotlib or plotly."
license: "BSD-3-Clause"
---

# 3Dmol.js molecular visualization

## Overview

3Dmol.js is a WebGL molecular viewer that runs entirely in the browser. This skill emits
**self-contained HTML** files that load 3Dmol from a CDN and render a structure, a trajectory,
or a vibrational mode — no server, no build step, no Python runtime to view. The bundled
`scripts/mol_viewer.py` generates that HTML from any `.xyz/.trj/.pdb/.sdf/.mol2/.cube` file;
the Core API below shows the underlying 3Dmol.js calls so you can hand-write or customize a
viewer.

## When to Use

- Animate a transition-state imaginary vibrational mode (from a mode trajectory or dx/dy/dz vectors)
- Play back a reaction path (IRC/NEB) or an MD trajectory with a speed control
- Show a protein–ligand docking pose with cartoon + ligand sticks + a binding-site surface
- Display an orbital or electron-density isosurface from a Gaussian `.cube` file
- Hand a colleague one HTML file that opens in any browser, no install
- Use **py3Dmol** instead for inline viewers inside a Jupyter notebook (same engine, Python API)
- Use **PyMOL/ChimeraX** instead for publication ray-traced stills or heavy structural editing
- Use **rdkit-chemdraw-cdxml** for 2D chemical structures, **plotly/matplotlib** for 2D plots

## Prerequisites

- **Viewing**: any modern browser with network access (the HTML pulls 3Dmol.js from a CDN)
- **Generator script**: `scripts/mol_viewer.py` — Python 3 standard library only, no install
- **Optional**: `pip install py3Dmol` for notebook use (wraps the same library)

No package is needed to produce or open the HTML. The generator lives in this skill's `scripts/`
folder (next to this SKILL.md). It can't be run in place from the skill directory, so use your
file tools to read `scripts/mol_viewer.py` and save it into your working directory before running.

## Quick Start

```bash
# animate a mode/trajectory file with play/pause + speed slider, in one call
python3 mol_viewer.py ts_imaginary_mode_000.trj --mode trajectory \
    --title "TS mode" --subtitle "-621.8 cm-1" --out ts_mode.html
# static structure:  python3 mol_viewer.py mol.xyz --out mol.html
```

## Core API

All snippets assume `<script src="https://3Dmol.org/build/3Dmol-min.js"></script>` is loaded
and a `<div id="v"></div>` exists.

### Create a viewer and load a structure

`createViewer` binds to a div; `addModel(data, format)` loads coordinates. Always `zoomTo()`
then `render()`. Supported `format`: `xyz`, `pdb`, `sdf`, `mol2`, `cube`, `cif`.

```javascript
const viewer = $3Dmol.createViewer("v", {backgroundColor: "white"});
viewer.addModel(xyzString, "xyz");         // coordinates as a string, not a URL
viewer.setStyle({}, {stick: {radius: 0.15}, sphere: {scale: 0.28}});
viewer.zoomTo();
viewer.render();
```

### Styles and coloring

`setStyle(selection, styleSpec)` — empty selection `{}` targets all atoms. Styles: `stick`,
`sphere`, `line`, `cross`, `cartoon`. Color by element (default), a scheme, or a fixed color.

```javascript
viewer.setStyle({}, {stick: {}, sphere: {scale: 0.25}});          // ball-and-stick
viewer.setStyle({elem: "C"}, {stick: {color: "gray"}});           // per-element override
viewer.setStyle({chain: "A"}, {cartoon: {color: "spectrum"}});    // protein ribbon
viewer.render();
```

### Animate a trajectory

Load every frame with `addModelsAsFrames`, then `animate`. **`interval` is the delay between
frames in milliseconds (larger = slower)** — do not use `step`, which skips frames and looks
jumpy. `loop: "backAndForth"` makes a one-way path oscillate; `reps: 0` loops forever.

```javascript
viewer.addModelsAsFrames(trjString, "xyz");   // multi-frame .trj or multi-model .xyz/.pdb
viewer.setStyle({}, {stick: {radius: 0.14}, sphere: {scale: 0.28}});
viewer.zoomTo();
viewer.render();
viewer.animate({loop: "backAndForth", interval: 120, reps: 0});
```

### Animate a vibrational normal mode

If a model's atoms carry displacement vectors (`dx, dy, dz` — extra columns on each XYZ line:
`elem x y z dx dy dz`), `model.vibrate(numFrames, amplitude, bothWays, arrowSpec)` builds the
oscillation frames. `bothWays: true` swings symmetrically about equilibrium; `arrowSpec` draws
motion arrows.

```javascript
const m = viewer.addModel(modeXyz, "xyz");        // each atom line: elem x y z dx dy dz
m.vibrate(10, 1.0, true, {radius: 0.08, color: "black"});   // 10 frames, full amplitude, arrows
viewer.setStyle({}, {stick: {radius: 0.14}, sphere: {scale: 0.28}});
viewer.zoomTo();
viewer.render();
viewer.animate({loop: "backAndForth", interval: 120, reps: 0});
```

If you only have a precomputed frame trajectory (e.g. pysisyphus `ts_imaginary_mode_000.trj`),
use the trajectory path above instead — no `dx/dy/dz` needed.

### Surfaces and volumetric isosurfaces

`addSurface(type, style, atomsel)` builds a molecular surface (`VDW`, `SAS`, `SES`, `MS`).
For an orbital/density isosurface, load the `.cube` and call `addVolumetricData`.

```javascript
viewer.addSurface($3Dmol.SurfaceType.VDW, {opacity: 0.75, color: "lightblue"}, {chain: "A"});
// isosurface from a Gaussian cube (positive and negative lobes):
viewer.addVolumetricData(cubeString, "cube", {isoval:  0.02, color: "blue", opacity: 0.85});
viewer.addVolumetricData(cubeString, "cube", {isoval: -0.02, color: "red",  opacity: 0.85});
viewer.render();
```

### Labels and interactive speed control

`addLabel(text, spec)` annotates. For animations, a slider bound to `interval` (restarting via
`stopAnimate()` + `animate()`) lets the viewer set the speed — the fix for "sometimes too fast".

```javascript
viewer.addLabel("TS", {position: {x: 0, y: 0, z: 0}, backgroundColor: "black", fontSize: 14});
let interval = 140;
const play = () => viewer.animate({loop: "backAndForth", interval});
document.getElementById("spd").oninput = e => { interval = +e.target.value; viewer.stopAnimate(); play(); };
play();
```

## Key Concepts

**`interval` vs `step`.** `interval` (ms) sets playback speed; every frame is shown. `step`
plays every Nth frame — it skips motion and is the usual cause of a "too fast"/jumpy animation.
Control speed with `interval`, never `step`.

**Coordinates are strings, not URLs.** `addModel`/`addModelsAsFrames` take the file *contents*.
Embed them in the HTML as a JSON-encoded string so quotes and newlines survive
(`scripts/mol_viewer.py` uses `json.dumps`; a raw backtick template breaks on backticks in data).

**CDN and CSP.** The page fetches 3Dmol.js from a CDN, so it needs network access when opened,
and a strict Content-Security-Policy (e.g. inside some artifact sandboxes) will blank it. Open
it as a normal local/hosted file.

## Common Workflows

### TS imaginary-mode animation (quantum-chemistry)

End-to-end HTML from a precomputed mode trajectory, with play/pause and a speed slider — the
deliverable the `neb-irc-activation-energy` skill hands off.

```bash
python3 mol_viewer.py ts_imaginary_mode_000.trj --mode trajectory \
    --title "Transition-state mode" --subtitle "-621.8 cm-1" --out ts_mode.html
# open ts_mode.html; drag the slider if the oscillation is too fast
```

### Reaction-path / MD playback

```bash
python3 mol_viewer.py trajectory.pdb --mode trajectory --style ballstick --out md.html
# any multi-model .xyz/.pdb works; backAndForth loop + interval control are built in
```

### Docking pose: protein ribbon + ligand sticks + pocket surface

```javascript
const viewer = $3Dmol.createViewer("v", {backgroundColor: "white"});
viewer.addModel(complexPdb, "pdb");
viewer.setStyle({}, {cartoon: {color: "spectrum"}});                 // protein
viewer.setStyle({resn: "LIG"}, {stick: {radius: 0.2}});             // ligand
viewer.addSurface($3Dmol.SurfaceType.VDW, {opacity: 0.6}, {resn: "LIG", byres: true, expand: 5});
viewer.zoomTo({resn: "LIG"});
viewer.render();
```

## Key Parameters

| Parameter | Method | Default | Range / Options | Effect |
|-----------|--------|---------|-----------------|--------|
| `interval` | `animate` | 50 | `40`–`400` ms | Frame delay; larger = slower playback |
| `loop` | `animate` | `forward` | `forward`/`backward`/`backAndForth` | `backAndForth` oscillates a one-way path |
| `reps` | `animate` | `0` | `0`=∞, `n` | Number of loops |
| `radius` | `stick` | `0.3` | `0.1`–`0.3` | Bond cylinder thickness |
| `scale` | `sphere` | `1.0` (vdW) | `0.2`–`0.4` for ball-and-stick | Atom sphere size |
| `amplitude` | `vibrate` | `1.0` | `0.5`–`2.0` | Normal-mode distortion size |
| `numFrames` | `vibrate` | `10` | `8`–`20` | Frames per half-cycle |
| `isoval` | `addVolumetricData` | — | e.g. `±0.02` | Isosurface contour value (sign = lobe) |
| `opacity` | `addSurface` | `1.0` | `0`–`1` | Surface transparency |

## Best Practices

- Control animation speed with `interval` (ms), never `step`.
- Embed coordinates as a JSON-encoded string (`json.dumps`), not a raw backtick template.
- Call `zoomTo()` before `render()`, and again after adding a large model.
- Keep default element colors unless the analysis needs a specific scheme — don't bake a palette.
- For large trajectories (>500 frames or >5k atoms), subsample frames; WebGL redraw is the limit.
- Ship one CDN `<script>` tag; only vendor the ~1 MB `3Dmol-min.js` inline if offline use is required.

## Common Recipes

### Recipe: generate a viewer in one call

```bash
python3 mol_viewer.py mode.xyz --mode vibrate --amplitude 1.2 --title "mode" --out mode.html
python3 mol_viewer.py mol.sdf  --style stick --out mol.html          # static
```

### Recipe: inline viewer in a Jupyter notebook (py3Dmol)

```python
import py3Dmol
view = py3Dmol.view(width=500, height=400)
view.addModel(open("mol.xyz").read(), "xyz")
view.setStyle({}, {"stick": {}, "sphere": {"scale": 0.25}})
view.zoomTo(); view.show()
```

### Recipe: side-by-side viewers

```javascript
const viewer = $3Dmol.createViewerGrid("v", {rows: 1, cols: 2});
viewer[0][0].addModel(reactantXyz, "xyz"); viewer[0][0].setStyle({}, {stick: {}});
viewer[0][1].addModel(productXyz, "xyz");  viewer[0][1].setStyle({}, {stick: {}});
viewer[0][0].zoomTo(); viewer[0][1].zoomTo(); viewer[0][0].render(); viewer[0][1].render();
```

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| Blank white page | 3Dmol.js not loaded (offline / strict CSP) | Open with network access; check the CDN `<script>` resolves |
| Animation too fast / jumpy | Using `step`, or a tiny `interval` | Use `interval` (ms); raise it; never set `step` |
| Vibration shows no motion | Model lacks `dx/dy/dz` vectors | Add mode vectors as extra XYZ columns, or use a precomputed frame `.trj` |
| Nothing rendered | Wrong `format` string or bad data | Match `format` to the file; coordinates must be the file contents, not a path |
| JS syntax error in page | Backtick/quote in embedded data | Embed via `json.dumps` (the generator does this) |
| Structure loads but no bonds | XYZ without connectivity + line style | Use `stick`/`sphere`; 3Dmol infers bonds by distance |
| Surface slow or hangs | Large `SES`/`MS` on a big system | Use `VDW`, restrict the `atomsel`, or lower resolution |

## Bundled Resources

- `scripts/mol_viewer.py` — emit a standalone 3Dmol HTML (static / trajectory / vibrate) from a structure file, with built-in play/pause + speed slider for animations

## Related Skills

- **neb-irc-activation-energy** — produces TS imaginary-mode trajectories and IRC paths that this skill animates
- **rdkit-chemdraw-cdxml** — 2D chemical structure and reaction-scheme drawing
- **plotly-interactive-plots** — interactive 2D scientific plots and dashboards

## References

- [3Dmol.js documentation](https://3dmol.org/doc/index.html) — GLViewer / GLModel API
- Rego & Koes, *Bioinformatics* 2015, 31(8):1322–1324 — 3Dmol.js: molecular visualization with WebGL
- [GLViewer.animate](https://3dmol.org/doc/GLViewer.html) — `interval`, `loop`, `reps`
- [GLModel.vibrate](https://3dmol.org/doc/GLModel.html) — normal-mode animation from `dx/dy/dz`
- [py3Dmol on PyPI](https://pypi.org/project/py3Dmol/) — Python/Jupyter wrapper
