#!/usr/bin/env python3
"""Generate the two standard deliverables from a finished pysisyphus reaction-path run:

  1. irc_energy_profile.png    — IRC step vs relative energy, TS marked
  2. ts_imaginary_mode.html    — 3Dmol.js animation of the TS imaginary vibrational mode

Run it in the same directory as the pipeline output, after `pysis pipeline.yaml` and
`check_result.py` have passed. The gfn/charge/mult/solvent are read from pipeline.yaml so the
IRC single-point energies are recomputed at exactly the pipeline's level of theory (override
with flags if needed).

Why recompute the IRC energies: pysisyphus writes forward_irc.trj / backward_irc.trj with
plain "step N" comment lines that carry no energy, so the energies must come from single-point
xtb calls on each frame. This is level-consistent and independent of log formatting.

Usage:
  python3 make_visuals.py                         # auto-detect pipeline.yaml in cwd
  python3 make_visuals.py --pipeline pipeline.yaml --outdir plots
  python3 make_visuals.py --charge -1 --alpb water   # override detected settings
  python3 make_visuals.py --irc-only | --mode-only
"""
import argparse
import glob
import re
import subprocess
import sys
import tempfile
from pathlib import Path

HARTREE_KCAL = 627.5094740631
HARTREE_KJ = 2625.4996
CDN = "https://3Dmol.org/build/3Dmol-min.js"


# ---------------------------------------------------------------- pipeline settings

def load_calc(pipeline_yaml):
    """Read gfn/charge/mult/alpb from the `calc:` block of pipeline.yaml (minimal parser,
    no yaml dependency needed)."""
    calc = {"gfn": 2, "charge": 0, "mult": 1, "alpb": None}
    p = Path(pipeline_yaml)
    if not p.exists():
        return calc
    in_calc = False
    for line in p.read_text().splitlines():
        stripped = line.strip()
        if re.match(r"^\w[\w ]*:\s*$", line) and not line[0].isspace():
            in_calc = stripped.startswith("calc")
            continue
        if not in_calc or stripped.startswith("#") or ":" not in stripped:
            continue
        key, _, val = stripped.partition(":")
        key, val = key.strip(), val.split("#")[0].strip()
        if key in ("gfn", "charge", "mult") and re.match(r"-?\d+$", val):
            calc[key] = int(val)
        elif key == "alpb" and val:
            calc["alpb"] = val
    return calc


# ---------------------------------------------------------------- xyz / xtb helpers

def read_frames(path):
    """Return [(comment, [(sym, x, y, z), ...]), ...] for a (multi-frame) xyz/trj file."""
    lines = Path(path).read_text().splitlines()
    frames, i = [], 0
    while i < len(lines):
        if not lines[i].strip():
            i += 1
            continue
        n = int(lines[i].split()[0])
        comment = lines[i + 1] if i + 1 < len(lines) else ""
        atoms = [tuple(lines[i + 2 + k].split()[:4]) for k in range(n)]
        frames.append((comment, atoms))
        i += n + 2
    return frames


def frame_to_xyz(comment, atoms):
    body = "\n".join(f"{s} {x} {y} {z}" for s, x, y, z in atoms)
    return f"{len(atoms)}\n{comment}\n{body}\n"


def xtb_energy(comment, atoms, calc):
    """Single-point energy (Hartree) at the pipeline's level of theory."""
    cmd = ["xtb", "frame.xyz", "--gfn", str(calc["gfn"]),
           "--chrg", str(calc["charge"]), "--uhf", str(calc["mult"] - 1)]
    if calc["alpb"]:
        cmd += ["--alpb", calc["alpb"]]
    with tempfile.TemporaryDirectory() as d:
        (Path(d) / "frame.xyz").write_text(frame_to_xyz(comment, atoms))
        out = subprocess.run(cmd, cwd=d, capture_output=True, text=True,
                             env={"OMP_NUM_THREADS": "1", "PATH": _path()}).stdout
    m = re.findall(r"TOTAL ENERGY\s+(-?\d+\.\d+)", out)
    if not m:
        raise RuntimeError("xtb single point produced no TOTAL ENERGY; is xtb on PATH "
                           "and the env sourced? Check charge/mult.")
    return float(m[-1])


def _path():
    import os
    return os.environ.get("PATH", "")


def centered_rmsd(a, b):
    import statistics
    ca = [[float(r[k]) for r in a] for k in (1, 2, 3)]
    cb = [[float(r[k]) for r in b] for k in (1, 2, 3)]
    for c in (ca, cb):
        for axis in c:
            m = statistics.fmean(axis)
            axis[:] = [v - m for v in axis]
    return sum((ca[k][i] - cb[k][i]) ** 2 for k in range(3) for i in range(len(a))) ** 0.5


# ---------------------------------------------------------------- deliverable 1: IRC profile

def build_irc_profile(calc, outdir):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fwd = _first(["forward_irc.trj", "*forward*irc*.trj"])
    bwd = _first(["backward_irc.trj", "*backward*irc*.trj"])
    ts = _first(["ts_final_geometry.xyz", "*ts_final*.xyz"])
    if not (fwd and bwd and ts):
        combined = _first(["finished_irc.trj", "*finished*irc*.trj"])
        if not combined:
            raise FileNotFoundError("No IRC trajectories found (forward_irc.trj / "
                                    "backward_irc.trj or finished_irc.trj).")
        frames = read_frames(combined)
    else:
        # reverse(backward) + TS + forward -> a continuous endpoint -> TS -> endpoint path
        frames = read_frames(bwd)[::-1] + read_frames(ts) + read_frames(fwd)

    # Orient so the reactant-matching endpoint is at index 0 (label only; energies unaffected).
    react = _first(["reactant.xyz"])
    reactant_left = True
    if react:
        r0 = read_frames(react)[0][1]
        if centered_rmsd(frames[0][1], r0) > centered_rmsd(frames[-1][1], r0):
            frames = frames[::-1]
            reactant_left = True
    print(f"recomputing {len(frames)} single-point energies "
          f"(gfn{calc['gfn']}, chrg {calc['charge']}, uhf {calc['mult']-1}, "
          f"alpb {calc['alpb'] or 'none'}) ...")
    e = [xtb_energy(c, a, calc) for c, a in frames]

    ref = e[0]                                   # reactant endpoint = 0
    rel_kcal = [(x - ref) * HARTREE_KCAL for x in e]
    rel_kj = [(x - ref) * HARTREE_KJ for x in e]
    ts_i = max(range(len(e)), key=lambda i: e[i])
    barrier = rel_kcal[ts_i]
    rxn = rel_kcal[-1]

    fig, ax = plt.subplots(figsize=(7, 5))
    x = list(range(len(e)))
    ax.plot(x, rel_kcal, marker="o", ms=4, lw=2)
    ax.scatter([ts_i], [barrier], color="C3", s=90, zorder=5, label="TS")
    ax.annotate(f"{barrier:.1f} kcal/mol", (ts_i, barrier),
                xytext=(0, 12), textcoords="offset points", ha="center", color="C3")
    lo, hi = min(rel_kcal), max(rel_kcal)
    ax.set_ylim(lo - 0.06 * (hi - lo), hi + 0.16 * (hi - lo))   # headroom for the TS label
    ax.set_xlabel("IRC step" + ("  (reactant → product)" if reactant_left else ""))
    ax.set_ylabel("relative energy (kcal/mol)")
    ax.set_title("Energy profile along the IRC")
    sec = ax.secondary_yaxis(
        "right", functions=(lambda v: v * 4.184, lambda v: v / 4.184))
    sec.set_ylabel("relative energy (kJ/mol)")
    ax.legend()
    fig.tight_layout()
    out = Path(outdir) / "irc_energy_profile.png"
    fig.savefig(out, dpi=200)
    plt.close(fig)
    print(f"wrote {out}  (dE‡ = {barrier:.1f} kcal/mol = {barrier*4.184:.1f} kJ/mol, "
          f"dE_rxn = {rxn:.1f} kcal/mol)")
    return out


# ---------------------------------------------------------------- deliverable 2: mode animation

def build_mode_html(outdir):
    trj = _first(["ts_imaginary_mode_000.trj", "*imaginary_mode*.trj", "*imag_mode*.trj"])
    if not trj:
        raise FileNotFoundError("No imaginary-mode trajectory found (expected "
                                "ts_imaginary_mode_000.trj from tsopt do_hess). "
                                "Re-run with `do_hess: True` under tsopt.")
    xyz = Path(trj).read_text()
    freq = _imag_freq("pipeline.log")
    subtitle = f"imaginary mode {freq:.1f} cm⁻¹" if freq else "imaginary mode"
    html = _HTML.replace("__XYZ__", xyz.replace("\\", "\\\\").replace("`", "\\`")) \
                .replace("__SUB__", subtitle).replace("__CDN__", CDN)
    out = Path(outdir) / "ts_imaginary_mode.html"
    out.write_text(html)
    print(f"wrote {out}  ({len(read_frames(trj))} frames, {subtitle})")
    return out


def _imag_freq(logpath):
    p = Path(logpath)
    if not p.exists():
        return None
    m = re.findall(r"Imaginary frequencies:\s*\[([^\]]*)\]", p.read_text(errors="ignore"))
    if not m:
        return None
    vals = re.findall(r"-?\d+\.?\d*", m[-1])
    return float(vals[0]) if vals else None


def _first(patterns):
    for pat in patterns:
        hits = sorted(glob.glob(pat))
        if hits:
            return hits[0]
    return None


_HTML = """<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>TS imaginary mode</title>
<script src="__CDN__"></script>
<style>
 body{margin:0;font-family:system-ui,sans-serif;background:#fff}
 #h{position:absolute;top:12px;left:50%;transform:translateX(-50%);z-index:9;
    text-align:center;background:rgba(255,255,255,.9);padding:8px 16px;border-radius:8px}
 #h b{font-size:1rem}#h span{color:#c0392b;font-weight:bold}
 #v{width:100vw;height:100vh;position:relative}
</style></head>
<body>
 <div id="h"><b>Transition-state vibrational mode</b><br><span>__SUB__</span></div>
 <div id="v"></div>
 <script>
  const xyz = `__XYZ__`;
  const viewer = $3Dmol.createViewer("v", {backgroundColor: "white"});
  viewer.addModelsAsFrames(xyz, "xyz");
  viewer.setStyle({}, {stick: {radius: 0.14}, sphere: {scale: 0.28}});
  viewer.zoomTo();
  viewer.render();
  viewer.animate({loop: "backAndForth", interval: 70});
 </script>
</body></html>
"""


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--pipeline", default="pipeline.yaml")
    ap.add_argument("--outdir", default=".")
    ap.add_argument("--charge", type=int)
    ap.add_argument("--mult", type=int)
    ap.add_argument("--gfn", type=int)
    ap.add_argument("--alpb")
    ap.add_argument("--irc-only", action="store_true")
    ap.add_argument("--mode-only", action="store_true")
    a = ap.parse_args()

    Path(a.outdir).mkdir(parents=True, exist_ok=True)
    calc = load_calc(a.pipeline)
    for k in ("charge", "mult", "gfn", "alpb"):
        if getattr(a, k) is not None:
            calc[k] = getattr(a, k)

    made = []
    if not a.mode_only:
        made.append(build_irc_profile(calc, a.outdir))
    if not a.irc_only:
        made.append(build_mode_html(a.outdir))
    print("\ndeliverables: " + ", ".join(str(m) for m in made))


if __name__ == "__main__":
    sys.exit(main())
