#!/usr/bin/env python3
"""Emit a self-contained 3Dmol.js HTML viewer from a molecular structure or trajectory.

Three modes:
  static      one geometry, no animation
  trajectory  a multi-frame file (.trj / multi-model .xyz / .pdb) played back and forth
  vibrate     one geometry whose atom lines carry mode vectors (elem x y z dx dy dz);
              3Dmol's vibrate() builds the oscillation frames

Animated modes get a play/pause button and a speed slider. Speed is the frame-delay
`interval` in milliseconds (larger = slower) — NOT a frame-skip step.

Usage:
  python3 mol_viewer.py mol.xyz                                  # static
  python3 mol_viewer.py path.trj --mode trajectory --title "IRC" --out irc.html
  python3 mol_viewer.py mode.xyz --mode vibrate --amplitude 1.2 --out ts_mode.html
  python3 mol_viewer.py pose.pdb --style cartoon --out pose.html

The output HTML loads 3Dmol.js from a CDN, so it needs network access when opened
(use --self-contained-note only affects messaging; offline embedding is out of scope).
"""
import argparse
import json
from pathlib import Path

CDN = "https://3Dmol.org/build/3Dmol-min.js"
EXT_FORMAT = {".xyz": "xyz", ".trj": "xyz", ".pdb": "pdb", ".sdf": "sdf",
              ".mol": "sdf", ".mol2": "mol2", ".cube": "cube", ".cif": "cif"}
STYLES = {
    "ballstick": '{stick: {radius: 0.14}, sphere: {scale: 0.28}}',
    "stick":     '{stick: {radius: 0.15}}',
    "sphere":    '{sphere: {}}',
    "line":      '{line: {}}',
    "cartoon":   '{cartoon: {color: "spectrum"}}',
}


def detect_format(path):
    fmt = EXT_FORMAT.get(Path(path).suffix.lower())
    if not fmt:
        raise ValueError(f"unknown extension {Path(path).suffix!r}; "
                         f"supported: {', '.join(sorted(EXT_FORMAT))}")
    return fmt


def build_html(data, fmt, mode, title, subtitle, style_js, amplitude, num_frames):
    """Return a complete standalone HTML document string."""
    data_js = json.dumps(data)                       # safe JS string literal (handles quotes/newlines)
    animated = mode in ("trajectory", "vibrate")

    if mode == "static":
        load = f'viewer.addModel({data_js}, "{fmt}");'
        anim = ""
    elif mode == "trajectory":
        load = f'viewer.addModelsAsFrames({data_js}, "{fmt}");'
        anim = 'const play = () => viewer.animate({loop: "backAndForth", interval: interval});'
    else:  # vibrate
        load = (f'const m = viewer.addModel({data_js}, "{fmt}");\n'
                f'  m.vibrate({num_frames}, {amplitude}, true);')   # needs dx,dy,dz on atoms
        anim = 'const play = () => viewer.animate({loop: "backAndForth", interval: interval});'

    controls = CONTROLS_HTML if animated else ""
    controls_js = CONTROLS_JS if animated else ""
    header = (f'<div id="h"><b>{title}</b>'
              + (f'<br><span>{subtitle}</span>' if subtitle else "") + "</div>") if title else ""

    return HTML_TEMPLATE.format(
        cdn=CDN, title=title or "3Dmol viewer", header=header, controls=controls,
        load=load, style=style_js, anim=anim, controls_js=controls_js)


CONTROLS_HTML = """
 <div id="c">
  <button id="pp">⏸ Pause</button>
  <label>Fast <input id="spd" type="range" min="40" max="400" step="10" value="140"> Slow</label>
 </div>"""

CONTROLS_JS = """
  let interval = 140, playing = true;
  const spd = document.getElementById("spd"), pp = document.getElementById("pp");
  play();
  spd.oninput = e => { interval = +e.target.value; if (playing) { viewer.stopAnimate(); play(); } };
  pp.onclick = () => {
    playing = !playing;
    if (playing) { play(); pp.textContent = "⏸ Pause"; }
    else { viewer.stopAnimate(); pp.textContent = "▶ Play"; }
  };"""

HTML_TEMPLATE = """<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>{title}</title>
<script src="{cdn}"></script>
<style>
 body{{margin:0;font-family:system-ui,sans-serif;background:#fff}}
 #v{{width:100vw;height:100vh;position:relative}}
 #h{{position:absolute;top:12px;left:50%;transform:translateX(-50%);z-index:9;text-align:center;
    background:rgba(255,255,255,.9);padding:8px 16px;border-radius:8px}}
 #h b{{font-size:1rem}}#h span{{color:#c0392b;font-weight:bold}}
 #c{{position:absolute;bottom:16px;left:50%;transform:translateX(-50%);z-index:9;display:flex;gap:12px;
    align-items:center;background:rgba(255,255,255,.92);padding:8px 14px;border-radius:8px;
    box-shadow:0 1px 4px rgba(0,0,0,.15)}}
 #c button{{cursor:pointer;border:1px solid #ccc;border-radius:5px;padding:4px 10px;background:#fff}}
 #c label{{font-size:.85rem;color:#555;display:flex;gap:6px;align-items:center}}
</style></head>
<body>
 {header}
 <div id="v"></div>{controls}
 <script>
  const viewer = $3Dmol.createViewer("v", {{backgroundColor: "white"}});
  {load}
  viewer.setStyle({{}}, {style});
  viewer.zoomTo();
  viewer.render();{anim}{controls_js}
 </script>
</body></html>
"""


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("infile")
    ap.add_argument("--mode", choices=("static", "trajectory", "vibrate"), default="static")
    ap.add_argument("--out", default=None, help="output .html (default: <infile>.html)")
    ap.add_argument("--style", choices=tuple(STYLES), default="ballstick")
    ap.add_argument("--title", default="")
    ap.add_argument("--subtitle", default="")
    ap.add_argument("--amplitude", type=float, default=1.0, help="vibrate distortion amplitude")
    ap.add_argument("--frames", type=int, default=10, help="vibrate frames per half-cycle")
    a = ap.parse_args()

    fmt = detect_format(a.infile)
    data = Path(a.infile).read_text()
    html = build_html(data, fmt, a.mode, a.title, a.subtitle,
                      STYLES[a.style], a.amplitude, a.frames)
    out = Path(a.out) if a.out else Path(a.infile).with_suffix(".html")
    out.write_text(html)
    print(f"wrote {out}  (mode={a.mode}, format={fmt}, style={a.style})")


if __name__ == "__main__":
    main()
