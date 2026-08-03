#!/usr/bin/env python3
"""Verify a pysisyphus reaction-path run before its barrier is reported.

Applies three gates:
  1. The transition state Hessian has exactly one imaginary frequency.
  2. The IRC endpoints relax to two distinct species matching reactant and product.
  3. The NEB profile has a single maximum (the step is elementary).

Exit code 0 if every gate passes, 1 otherwise.

Usage:  python3 check_result.py pipeline.log [--trj final_geometries.trj]
"""
import argparse
import re
import sys
from pathlib import Path

HARTREE_KJ = 2625.4996


def imaginary_frequencies(log):
    """Return the list of imaginary wavenumbers reported for the optimized TS."""
    hits = re.findall(r"Imaginary frequencies:\s*\[([^\]]*)\]", log)
    if not hits:
        return None
    return [float(x) for x in re.findall(r"-?\d+\.?\d*", hits[-1])]


def irc_endpoint_matches(log):
    """Return the set of end-geometry indices that matched an input structure."""
    block = re.split(r"RMSDS AFTER END OPTIMIZATIONS", log)
    if len(block) < 2:
        return None
    return {
        int(i)
        for i, line in re.findall(r"end geom\s+(\d+)\s*\(([^\n]*)", block[-1])
        if "bond matrices match" in line
    }


def profile_maxima(trj, prominence_kj=2.0):
    """Locate intervening minima (i.e. intermediates) in the .trj comment-line energies.

    Counting local maxima directly is unreliable: a single barrier whose top falls
    between two images gives a flat two-point summit that neighbour comparison misses.
    An elementary step is better defined by the absence of any interior minimum that
    sits below a real peak on both sides.
    """
    energies = [
        float(m)
        for m in re.findall(r"^\s*(-?\d+\.\d+)\s*,?\s*$", trj, re.M)
    ]
    if len(energies) < 3:
        return None, energies
    thr = prominence_kj / HARTREE_KJ
    wells = [
        i
        for i in range(1, len(energies) - 1)
        if energies[i] <= energies[i - 1]
        and energies[i] <= energies[i + 1]
        and max(energies[:i]) - energies[i] > thr
        and max(energies[i + 1:]) - energies[i] > thr
    ]
    return wells, energies


def barrier_kj(log):
    """Fallback: barrier of the TS above the first COS image (not endpoint-referenced)."""
    m = re.findall(r"Barrier between TS and first COS image:\s*(-?\d+\.?\d*)", log)
    return float(m[-1]) if m else None


def endpoint_barriers_kj(log):
    """Parse pysisyphus's final BARRIERS block (Left / TS / Right, relative to the
    global minimum). Returns (dE_forward, dE_reaction) in kJ/mol, both referenced to
    the reactant endpoint — the numbers to actually report. None if the block is absent.

    Preferred over barrier_kj(): "TS vs first COS image" ignores the endpoint
    reoptimization and typically understates the true dE-double-dagger.
    """
    def _val(label):
        m = re.findall(rf"\b{label}:\s*(-?\d+\.\d+)\s*kJ", log)
        return float(m[-1]) if m else None

    left, ts, right = _val("Left"), _val("TS"), _val("Right")
    if left is None or ts is None:
        return None
    d_fwd = ts - left
    d_rxn = (right - left) if right is not None else None
    return d_fwd, d_rxn


def main():
    p = argparse.ArgumentParser()
    p.add_argument("log")
    p.add_argument("--trj", default=None, help="NEB path .trj (default: sibling final_geometries.trj)")
    a = p.parse_args()

    logpath = Path(a.log)
    log = logpath.read_text(errors="ignore")

    # pysisyphus writes energies into the comment line of the NEB path .trj, but
    # final_geometries.trj only carries the first one. Take the first candidate
    # that actually has a full profile.
    candidates = [Path(a.trj)] if a.trj else [
        logpath.parent / n for n in ("current_geometries.trj", "final_geometries.trj", "cos_hei.trj")
    ]
    trjpath = next(
        (c for c in candidates if c.exists() and len(profile_maxima(c.read_text(errors="ignore"))[1]) >= 3),
        next((c for c in candidates if c.exists()), candidates[0]),
    )

    rows, ok = [], True

    freqs = imaginary_frequencies(log)
    if freqs is None:
        rows.append(("FAIL", "imaginary frequencies", "no Hessian output found; did tsopt run with do_hess?"))
        ok = False
    elif len(freqs) == 1:
        rows.append(("PASS", "imaginary frequencies", f"exactly 1 at {freqs[0]:.1f} cm-1"))
    elif len(freqs) == 0:
        rows.append(("FAIL", "imaginary frequencies", "0 found; optimizer landed on a minimum"))
        ok = False
    else:
        rows.append(("FAIL", "imaginary frequencies", f"{len(freqs)} found {freqs}; higher-order saddle"))
        ok = False

    matched = irc_endpoint_matches(log)
    if matched is None:
        rows.append(("FAIL", "IRC endpoints", "no endopt comparison found; did endopt run?"))
        ok = False
    elif len(matched) >= 2:
        rows.append(("PASS", "IRC endpoints", "forward and backward matched distinct inputs"))
    else:
        rows.append(("FAIL", "IRC endpoints", f"only {len(matched)} distinct match(es); TS may connect other species"))
        ok = False

    if trjpath.exists():
        wells, energies = profile_maxima(trjpath.read_text(errors="ignore"))
        if wells is None:
            rows.append(("WARN", "NEB profile", "too few images to assess"))
        elif not wells:
            span = (max(energies) - min(energies)) * HARTREE_KJ
            rows.append(("PASS", "NEB profile", f"elementary, single barrier, span {span:.1f} kJ/mol"))
        else:
            rows.append(("FAIL", "NEB profile",
                         f"{len(wells)} intermediate(s) at image(s) {wells}; split into elementary steps"))
            ok = False
    else:
        rows.append(("WARN", "NEB profile", f"{trjpath.name} not found; skipped"))

    width = max(len(r[1]) for r in rows)
    print()
    for status, name, detail in rows:
        print(f"  [{status}] {name:<{width}}  {detail}")

    eb = endpoint_barriers_kj(log)
    if eb is not None:
        d_fwd, d_rxn = eb
        print(f"\n  electronic barrier dE‡ (GFN2-xTB): {d_fwd:.1f} kJ/mol = {d_fwd / 4.184:.2f} kcal/mol")
        if d_rxn is not None:
            print(f"  reaction energy dE_rxn:            {d_rxn:.1f} kJ/mol = {d_rxn / 4.184:.2f} kcal/mol")
        print("  (referenced to the reactant endpoint; add Hessian thermal corrections for dG‡)")
    else:
        b = barrier_kj(log)
        if b is not None:
            print(f"\n  barrier vs first COS image (GFN2-xTB): {b:.1f} kJ/mol = {b / 4.184:.2f} kcal/mol")
            print("  (no endpoint BARRIERS block found; this understates dE‡ if endopt ran)")
    print(f"\n  => {'all gates passed' if ok else 'VERIFICATION FAILED, do not report this barrier'}\n")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
