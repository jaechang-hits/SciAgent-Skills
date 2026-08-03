# Activation energy definitions and reporting

Several distinct quantities are all called "the barrier", and they differ by amounts large
enough to change conclusions. Always state which one is reported, at what level of theory, and
relative to which reference state.

## The quantities

| Quantity | Definition | When it is the right one |
|---|---|---|
| ΔE‡ | E(TS) − E(reactant), electronic only | comparing methods, or internal ranking |
| ΔE‡ + ZPE | ΔE‡ + zero-point energy difference | light-atom transfers, kinetic isotope work |
| ΔH‡(T) | ΔE‡ + thermal enthalpy correction | calorimetric comparison |
| ΔG‡(T) | ΔH‡ − TΔS‡ | **comparison against experimental rates** |
| Arrhenius Ea | ΔH‡ + RT (unimolecular gas phase), ΔH‡ + 2RT (bimolecular) | fitting an Arrhenius plot |

ΔG‡ is the default when comparing with measured kinetics. Entropy matters most for bimolecular
reactions, where the loss of translational and rotational freedom on association can shift the
barrier by tens of kJ/mol relative to ΔH‡.

## Getting the corrections

The pipeline's TS Hessian, plus Hessians on the reactant and product, supply everything needed.
With pysisyphus these come from the `do_hess` output; with xtb directly, **using the same
charge, spin, and solvent as the pipeline, on the optimized endpoint geometry**:

```bash
xtb forward_end_final_geometry.xyz --hess --gfn 2 --alpb water --chrg -1 --uhf 0
```

The thermochemistry block reports ZPE, H(T) − H(0), entropy, and G. Take the differences
between TS and reactant.

**Consistency is not optional.** ΔG‡ = G(TS) − G(reactant) is only meaningful if both Hessians
share the level of theory, charge, spin, and solvent used to locate the TS, and if the reactant
Hessian is on the *relaxed* endpoint the barrier is referenced to — not the raw input geometry.
A gas-phase Hessian differenced against a solvated barrier, or a Hessian with the wrong
`--chrg`, is the most common way to produce a physically impossible (often negative) ΔG‡.

Two standard caveats apply to the rigid-rotor harmonic-oscillator treatment every one of these
codes uses. Low-frequency modes below ~50–100 cm⁻¹ contribute spuriously large entropies, so a
quasi-harmonic correction is advisable when such modes are present. And gas-phase entropies
overestimate the association penalty in solution, so a standard-state correction from 1 atm to
1 mol/L is appropriate for solution-phase reactions.

## Reference state for bimolecular reactions

The barrier depends on what the reactant is taken to be:

- **Separated reactants** gives the barrier relevant to the overall bimolecular rate constant.
- **Pre-reaction complex** gives the barrier for the chemical step alone, and is usually the
  smaller number.

Neither is wrong, but they are not interchangeable. Record which was used. NEB converges far
more reliably from the pre-reaction complex, so that is normally what the pipeline produces by
default — which makes the distinction easy to lose track of.

For an ion reacting with a neutral (e.g. anionic SN2, F⁻ + CH₃Cl), the gas-phase ion–dipole
pre-reaction complex is deep enough that the TS lies *below* the separated reactants — a
**submerged barrier**. Against separated reactants ΔE‡ is then negative; against the
pre-reaction complex it is positive. Report the pre-complex-referenced value (what the pipeline
gives), and add implicit solvation, which screens the ion–dipole attraction and lifts the
barrier to a positive, experiment-comparable number. A negative barrier here is a reference-state
artifact, not an error — but a negative barrier *after* solvation usually means the Hessian and
the path used different settings (see the consistency note above).

## Refining the electronic energy

The composite approach separates geometry from energy: optimize and take frequencies at a cheap
level, then recompute only the electronic energy at a better one.

```
ΔG‡ = [E_high(TS) − E_high(R)] + [G_corr,low(TS) − G_corr,low(R)]
```

Realistically the high level here means B3LYP or ωB97X-D with a double-zeta basis on ≤30 atoms,
applied to three structures. See `feasibility.md` for timing.

## Accuracy expectations for GFN2-xTB

GFN2-xTB barriers are semi-quantitative. Absolute errors of tens of kJ/mol against high-level
references are routine, and errors are systematically larger for charged species, transition
metals, and reactions involving substantial charge separation.

What GFN2 is genuinely good for is relative ordering within a series of closely related
reactions, and for producing geometries and thermal corrections good enough to carry into a
higher-level single point. Report accordingly: a GFN2 barrier presented without this
qualification invites the reader to treat it as a predicted rate, which it does not support.
When the user needs quantitative agreement with experiment, say directly that this level cannot
deliver it and that DFT or coupled-cluster refinement is required.

## Suggested reporting format

```
reaction:      <description>
level:         GFN2-xTB / ALPB(solvent)
reference:     pre-reaction complex

dE‡        = xx.x kJ/mol
dE‡ + ZPE  = xx.x kJ/mol
dG‡(298 K) = xx.x kJ/mol

verification: 1 imaginary frequency (-xxxx cm-1, matches reaction coordinate)
              IRC endpoints match reactant/product bond matrices
              NEB profile single maximum

caveat:       GFN2-level semi-quantitative value; DFT re-computation needed for
              experimental comparison.
```
