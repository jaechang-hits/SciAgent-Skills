---
name: "libsbml-network-modeling"
description: "Build, read, validate, and modify SBML biological network models using libSBML Python API. Supports all SBML Levels (1–3), reactions with kinetic laws, species/compartments, rules (assignment/rate/algebraic), the FBC extension for flux balance analysis models, and model conversion utilities. Integrates with COBRApy, Tellurium/RoadRunner, and COPASI for simulation. Use when programmatically constructing ODE-based or constraint-based metabolic/signaling models in the standard SBML format."
license: "LGPL-2.1"
---

# libsbml-network-modeling

## Overview

libSBML is the reference library for reading, writing, creating, and validating SBML (Systems Biology Markup Language) models. SBML is the community standard for encoding biochemical reaction networks — ODE models, signaling cascades, and genome-scale metabolic models all use it. The Python API (`python-libsbml`) exposes a full object model covering compartments, species, reactions, kinetic laws, rules, constraints, and every SBML extension. Models saved as SBML `.xml` files are interoperable with COPASI, Tellurium, RoadRunner, COBRApy, and BioModels Database.

## When to Use

- Building a new ODE-based biochemical model (enzyme kinetics, signaling pathway) from scratch in SBML format for simulation in COPASI or Tellurium
- Reading and programmatically modifying an existing BioModels Database model — changing kinetic parameters, adding species, or patching reaction stoichiometry
- Validating an SBML file against the specification before submitting to BioModels or sharing with collaborators
- Converting SBML models between Level 1/2/3 for compatibility with older simulation tools
- Constructing genome-scale metabolic models with flux bounds and objective functions via the FBC (Flux Balance Constraints) extension for use with COBRApy
- Parsing an SBML model to extract the stoichiometry matrix, species list, or reaction network as NumPy/pandas data structures for custom analysis
- Use `cobrapy-metabolic-modeling` instead when you need to run FBA, FVA, or gene knockouts on an already-built metabolic model — libSBML is for constructing and editing the SBML file itself
- Use `tellurium` directly when you want an integrated Python environment for both SBML authoring (Antimony syntax) and ODE simulation without low-level XML manipulation

## Prerequisites

- **Python packages**: `python-libsbml`, `numpy`, `pandas` (optional, for matrix extraction)
- **Optional packages**: `cobra` (COBRApy, for FBA after SBML load), `tellurium` (for SBML↔Antimony conversion and simulation)
- **Data requirements**: SBML files (`.xml`), or built from scratch in Python; BioModels Database SBML files are freely available at https://www.ebi.ac.uk/biomodels/

```bash
pip install python-libsbml numpy pandas
# Optional simulation/FBA integrations:
pip install cobra tellurium
```

## Quick Start

Load an SBML file, inspect its content, and modify a parameter value:

```python
import libsbml

# Read an SBML model file
reader = libsbml.SBMLReader()
doc = reader.readSBMLFromFile("BIOMD0000000012.xml")

# Check for errors
if doc.getNumErrors() > 0:
    doc.printErrors()

model = doc.getModel()
print(f"Model: {model.getId()}")
print(f"  Compartments: {model.getNumCompartments()}")
print(f"  Species:      {model.getNumSpecies()}")
print(f"  Reactions:    {model.getNumReactions()}")

# Modify a global parameter
param = model.getParameter("Km")
if param:
    old_val = param.getValue()
    param.setValue(0.05)
    print(f"Updated Km: {old_val} → {param.getValue()}")

# Write modified model back to file
writer = libsbml.SBMLWriter()
writer.writeSBMLToFile(doc, "BIOMD0000000012_modified.xml")
print("Saved modified model.")
```

## Core API

### Module 1: Reading and Validating SBML

Load SBML files from disk or strings, check parse errors, and run full SBML spec validation.

```python
import libsbml

# Read from file
reader = libsbml.SBMLReader()
doc = reader.readSBMLFromFile("model.xml")

# Check for fatal parse errors
n_errors = doc.getNumErrors()
print(f"Parse errors: {n_errors}")
for i in range(n_errors):
    err = doc.getError(i)
    severity = err.getSeverityAsString()
    print(f"  [{severity}] line {err.getLine()}: {err.getMessage()}")

# Check the SBML Level and Version
print(f"SBML Level {doc.getLevel()} Version {doc.getVersion()}")

# Read from in-memory XML string
xml_string = open("model.xml").read()
doc2 = reader.readSBMLFromString(xml_string)
model = doc2.getModel()
print(f"Model id: {model.getId()}, name: {model.getName()}")
```

```python
import libsbml

# Full consistency / validation check (more thorough than parse error check)
doc = libsbml.readSBMLFromFile("model.xml")

# Enable all consistency checks
doc.setConsistencyChecks(libsbml.LIBSBML_CAT_GENERAL_CONSISTENCY, True)
doc.setConsistencyChecks(libsbml.LIBSBML_CAT_IDENTIFIER_CONSISTENCY, True)
doc.setConsistencyChecks(libsbml.LIBSBML_CAT_UNITS_CONSISTENCY, True)
doc.setConsistencyChecks(libsbml.LIBSBML_CAT_MATHML_CONSISTENCY, True)
doc.setConsistencyChecks(libsbml.LIBSBML_CAT_SBO_CONSISTENCY, True)
doc.setConsistencyChecks(libsbml.LIBSBML_CAT_OVERDETERMINED_MODEL, True)
doc.setConsistencyChecks(libsbml.LIBSBML_CAT_MODELING_PRACTICE, True)

n_errors = doc.checkConsistency()
print(f"Consistency check: {n_errors} issue(s)")
for i in range(n_errors):
    err = doc.getError(i)
    print(f"  [{err.getSeverityAsString()}] {err.getShortMessage()}: {err.getMessage()[:120]}")
```

### Module 2: Creating Models from Scratch

Build a complete SBML document by adding compartments, species, and reactions programmatically.

```python
import libsbml

# Create a new SBML Level 3 Version 2 document
doc = libsbml.SBMLDocument(3, 2)
model = doc.createModel()
model.setId("simple_enzymatic_model")
model.setName("Simple Enzymatic Reaction Model")
model.setTimeUnits("second")
model.setSubstanceUnits("mole")
model.setVolumeUnits("litre")
model.setExtentUnits("mole")

# Add a compartment (cytoplasm)
comp = model.createCompartment()
comp.setId("cytoplasm")
comp.setName("Cytoplasm")
comp.setConstant(True)
comp.setSize(1.0)          # 1 litre
comp.setSpatialDimensions(3)
comp.setUnits("litre")

# Add species: substrate S, enzyme E, complex ES, product P
species_data = [
    ("S",  "Substrate",           0.01, True),   # (id, name, initialConc, boundaryCondition)
    ("E",  "Enzyme",              0.001, False),
    ("ES", "Enzyme-Substrate",    0.0,  False),
    ("P",  "Product",             0.0,  True),
]
for sp_id, sp_name, init_conc, boundary in species_data:
    sp = model.createSpecies()
    sp.setId(sp_id)
    sp.setName(sp_name)
    sp.setCompartment("cytoplasm")
    sp.setInitialConcentration(init_conc)
    sp.setBoundaryCondition(boundary)
    sp.setHasOnlySubstanceUnits(False)
    sp.setConstant(False)
    print(f"Added species: {sp_id} (init={init_conc} M, boundary={boundary})")

print(f"Model has {model.getNumSpecies()} species and {model.getNumCompartments()} compartment(s)")
```

### Module 3: Editing Reactions and Kinetic Laws

Add reactions with stoichiometry and MathML kinetic law formulas.

```python
import libsbml

# Continuing from Module 2: add Michaelis-Menten kinetics reactions
# Forward: S + E -> ES (association)
# Reverse: ES -> S + E (dissociation)
# Catalytic: ES -> P + E (product release)

# First, add kinetic parameters as global parameters
params = [
    ("kf", 1e6,  "litre per mole per second"),   # forward rate constant
    ("kr", 1e-3, "per second"),                   # reverse rate constant
    ("kcat", 0.1, "per second"),                  # catalytic rate constant
]
for p_id, p_val, p_units in params:
    param = model.createParameter()
    param.setId(p_id)
    param.setValue(p_val)
    param.setConstant(True)
    # Units are for documentation — libSBML stores them as unit definitions
    print(f"Added parameter: {p_id} = {p_val}")

def add_reaction(model, rxn_id, rxn_name, reactants, products, formula):
    """Helper: create a reaction with MathML kinetic law."""
    rxn = model.createReaction()
    rxn.setId(rxn_id)
    rxn.setName(rxn_name)
    rxn.setReversible(False)
    for sp_id, stoich in reactants:
        sr = rxn.createReactant()
        sr.setSpecies(sp_id)
        sr.setStoichiometry(stoich)
        sr.setConstant(True)
    for sp_id, stoich in products:
        sr = rxn.createProduct()
        sr.setSpecies(sp_id)
        sr.setStoichiometry(stoich)
        sr.setConstant(True)
    kl = rxn.createKineticLaw()
    math_ast = libsbml.parseL3Formula(formula)
    if math_ast is None:
        raise ValueError(f"Could not parse formula: {formula}")
    kl.setMath(math_ast)
    return rxn

add_reaction(model, "v1", "Association",  [("S",1),("E",1)], [("ES",1)], "kf * S * E * cytoplasm")
add_reaction(model, "v2", "Dissociation", [("ES",1)], [("S",1),("E",1)], "kr * ES * cytoplasm")
add_reaction(model, "v3", "Catalysis",    [("ES",1)], [("P",1),("E",1)], "kcat * ES * cytoplasm")

print(f"Model has {model.getNumReactions()} reactions")
writer = libsbml.SBMLWriter()
writer.writeSBMLToFile(doc, "michaelis_menten.xml")
print("Saved michaelis_menten.xml")
```

### Module 4: Species and Compartments

Inspect and modify species properties — initial amounts vs concentrations, boundary conditions, compartment volumes.

```python
import libsbml

doc = libsbml.readSBMLFromFile("model.xml")
model = doc.getModel()

# Iterate species and print their properties
print(f"{'ID':<12} {'Compartment':<15} {'InitConc':>10} {'InitAmt':>10} {'Boundary':>10} {'Constant':>10}")
print("-" * 70)
for i in range(model.getNumSpecies()):
    sp = model.getSpecies(i)
    init_conc = sp.getInitialConcentration() if sp.isSetInitialConcentration() else "—"
    init_amt  = sp.getInitialAmount()        if sp.isSetInitialAmount()        else "—"
    print(f"{sp.getId():<12} {sp.getCompartment():<15} {str(init_conc):>10} {str(init_amt):>10} "
          f"{str(sp.getBoundaryCondition()):>10} {str(sp.getConstant()):>10}")

# Modify compartment volume (e.g. scale to a smaller cell)
comp = model.getCompartment("cytoplasm")
if comp:
    old_size = comp.getSize()
    comp.setSize(old_size * 0.1)
    print(f"\nCytoplasm volume: {old_size} → {comp.getSize()} litre")

# Set a species initial concentration by ID
sp = model.getSpecies("S")
if sp:
    sp.setInitialConcentration(0.005)
    print(f"Updated [S] initial concentration to {sp.getInitialConcentration()} M")
```

### Module 5: Rules and Constraints

Add assignment rules, rate rules, and algebraic rules to model derived quantities or conserved relationships.

```python
import libsbml

doc = libsbml.readSBMLFromFile("model.xml")
model = doc.getModel()

# AssignmentRule: computes a variable algebraically at every time step
# Example: total enzyme E_total = E + ES (conservation relationship, monitoring only)
ar = model.createAssignmentRule()
ar.setVariable("E_total")   # must be an existing parameter or species id
# First add the target as a parameter if needed
if model.getParameter("E_total") is None:
    p = model.createParameter()
    p.setId("E_total")
    p.setConstant(False)     # MUST be False for assignment rule targets
    p.setValue(0.0)
math_ast = libsbml.parseL3Formula("E + ES")
ar.setMath(math_ast)
print(f"Added AssignmentRule: E_total = E + ES")

# RateRule: specifies dX/dt directly, bypassing reaction-based ODE generation
# Useful for custom non-mass-action dynamics
rr = model.createRateRule()
rr.setVariable("P")   # species P already has boundary=True to allow rate rules
math_ast2 = libsbml.parseL3Formula("kcat * ES * cytoplasm")
rr.setMath(math_ast2)
print(f"Added RateRule: dP/dt = kcat * ES * cytoplasm")

# Constraint: model invariant that simulators should monitor (not enforced computationally)
constraint = model.createConstraint()
math_ast3 = libsbml.parseL3Formula("S >= 0")
constraint.setMath(math_ast3)
msg = libsbml.XMLNode.convertStringToXMLNode("<message><p>Substrate cannot be negative</p></message>")
constraint.setMessage(msg)
print(f"Added Constraint: S >= 0")

print(f"Model rules: {model.getNumRules()}, constraints: {model.getNumConstraints()}")
```

### Module 6: FBC Extension (Flux Balance Constraints)

Use the SBML FBC package to encode genome-scale metabolic models with flux bounds and an objective function for use with COBRApy or other FBA solvers.

```python
import libsbml

# Build a minimal FBC-enabled model (3-reaction toy network)
doc = libsbml.SBMLDocument(3, 2)
# Enable FBC package (required)
doc.enablePackage(libsbml.FbcExtension.getXmlnsL3V1V2(), "fbc", True)
doc.setPackageRequired("fbc", False)

model = doc.createModel()
model.setId("toy_fba_model")
fbc_plugin = model.getPlugin("fbc")
fbc_plugin.setStrict(True)

# Add a compartment and species
comp = model.createCompartment()
comp.setId("c")
comp.setConstant(True)
comp.setSize(1.0)

for sp_id in ["A", "B", "C"]:
    sp = model.createSpecies()
    sp.setId(sp_id)
    sp.setCompartment("c")
    sp.setInitialAmount(0.0)
    sp.setBoundaryCondition(False)
    sp.setConstant(False)
    sp.setHasOnlySubstanceUnits(True)
    sp_fbc = sp.getPlugin("fbc")
    sp_fbc.setChemicalFormula("")

# Add flux bound parameters
bounds = {"lb_0": 0.0, "lb_neg1000": -1000.0, "ub_1000": 1000.0}
for b_id, b_val in bounds.items():
    p = model.createParameter()
    p.setId(b_id)
    p.setValue(b_val)
    p.setConstant(True)

def add_fbc_reaction(model, rxn_id, reactants, products, lb_id, ub_id):
    rxn = model.createReaction()
    rxn.setId(rxn_id)
    rxn.setReversible(lb_id == "lb_neg1000")
    rxn.setFast(False)
    for sp_id, stoich in reactants:
        sr = rxn.createReactant(); sr.setSpecies(sp_id); sr.setStoichiometry(stoich); sr.setConstant(True)
    for sp_id, stoich in products:
        sr = rxn.createProduct();  sr.setSpecies(sp_id); sr.setStoichiometry(stoich); sr.setConstant(True)
    rxn_fbc = rxn.getPlugin("fbc")
    rxn_fbc.setLowerFluxBound(lb_id)
    rxn_fbc.setUpperFluxBound(ub_id)
    return rxn

add_fbc_reaction(model, "r1", [("A", 1)], [("B", 1)], "lb_0", "ub_1000")
add_fbc_reaction(model, "r2", [("B", 1)], [("C", 1)], "lb_0", "ub_1000")
add_fbc_reaction(model, "r3", [("A", 1)], [],          "lb_0", "ub_1000")  # exchange

# Add objective function: maximize r2 flux
obj = fbc_plugin.createObjective()
obj.setId("maximize_r2")
obj.setType("maximize")
fbc_plugin.setActiveObjectiveId("maximize_r2")
flux_obj = obj.createFluxObjective()
flux_obj.setReaction("r2")
flux_obj.setCoefficient(1.0)

writer = libsbml.SBMLWriter()
writer.writeSBMLToFile(doc, "toy_fba.xml")
print(f"Saved toy_fba.xml (Level {doc.getLevel()} Version {doc.getVersion()}, FBC enabled)")
print(f"Reactions: {model.getNumReactions()}, Objective: maximize r2")
```

### Module 7: Exporting and Level Conversion

Write models to file or string, convert between SBML levels, and export to Antimony notation via Tellurium.

```python
import libsbml

doc = libsbml.readSBMLFromFile("michaelis_menten.xml")
model = doc.getModel()
print(f"Loaded: Level {doc.getLevel()}, Version {doc.getVersion()}")

# Write to XML string (useful for in-memory transmission)
writer = libsbml.SBMLWriter()
xml_string = writer.writeSBMLToString(doc)
print(f"XML string length: {len(xml_string)} characters")

# Convert Level 3 → Level 2 (for compatibility with older tools)
# SBMLDocument.setLevelAndVersion handles conversion automatically
props = libsbml.ConversionProperties()
props.addOption("setLevelAndVersion", True, "Convert level and version")
props.addOption("targetLevel",   2)
props.addOption("targetVersion", 4)
status = doc.convert(props)
if status == libsbml.LIBSBML_OPERATION_SUCCESS:
    writer.writeSBMLToFile(doc, "michaelis_menten_L2V4.xml")
    print(f"Converted to L2V4 → michaelis_menten_L2V4.xml")
else:
    print(f"Conversion failed with code: {status}")
```

```python
# Export SBML to Antimony (human-readable) via Tellurium (optional)
try:
    import tellurium as te
    antimony_str = te.sbmlToAntimony(open("michaelis_menten.xml").read())
    print("Antimony notation:")
    print(antimony_str[:600])
    with open("michaelis_menten.ant", "w") as f:
        f.write(antimony_str)
    print("Saved michaelis_menten.ant")
except ImportError:
    print("tellurium not installed — skipping Antimony export")
```

## Key Concepts

### SBMLDocument, Model, and the Plugin Architecture

Every libSBML session starts with an `SBMLDocument` that owns exactly one `Model`. Extension packages (FBC, qual, layout, groups, distrib) are accessed as plugins retrieved via `object.getPlugin("fbc")`. Plugins are only available after enabling the package on the document with `doc.enablePackage(...)`. Calling `getPlugin` on a document that has not enabled the package returns `None`.

```python
import libsbml

doc = libsbml.readSBMLFromFile("iJO1366.xml")
model = doc.getModel()

# Check which packages are active
for i in range(doc.getNumPlugins()):
    pkg = doc.getPlugin(i)
    print(f"Package: {pkg.getPackageName()} (level {pkg.getLevel()})")

# Access FBC plugin
fbc_plugin = model.getPlugin("fbc")
if fbc_plugin:
    print(f"FBC strict mode: {fbc_plugin.getStrict()}")
    print(f"Objectives: {fbc_plugin.getNumObjectives()}")
```

### MathML Formulas and the AST

Kinetic laws in SBML are stored as MathML. libSBML parses formula strings to an Abstract Syntax Tree (AST) using `libsbml.parseL3Formula(string)` and converts AST back to a string with `libsbml.formulaToL3String(ast)`. Always check that `parseL3Formula` returns non-`None` before assigning to a kinetic law — a `None` return means parsing failed silently.

```python
import libsbml

# Parse and inspect a kinetic formula
formula = "Vmax * S / (Km + S) * cytoplasm"
ast = libsbml.parseL3Formula(formula)
if ast is None:
    print("ERROR: formula could not be parsed")
else:
    print(f"Parsed formula: {libsbml.formulaToL3String(ast)}")
    print(f"AST root type: {ast.getType()}")  # e.g., AST_TIMES

# Retrieve a kinetic law formula from an existing reaction
doc = libsbml.readSBMLFromFile("model.xml")
model = doc.getModel()
rxn = model.getReaction(0)
if rxn and rxn.isSetKineticLaw():
    kl = rxn.getKineticLaw()
    formula_str = libsbml.formulaToL3String(kl.getMath())
    print(f"Reaction '{rxn.getId()}' kinetic law: {formula_str}")
```

## Common Workflows

### Workflow 1: Load BioModels Model, Modify Parameters, and Simulate

**Goal**: Download a BioModels model, adjust kinetic parameters, and run an ODE simulation with Tellurium/RoadRunner.

```python
import libsbml
import urllib.request

# 1. Download SBML from BioModels Database (BIOMD0000000012 = Tyson 1991 cell cycle)
url = "https://www.ebi.ac.uk/biomodels/model/download/BIOMD0000000012?filename=BIOMD0000000012_url.xml"
urllib.request.urlretrieve(url, "BIOMD0000000012.xml")
print("Downloaded BIOMD0000000012.xml")

# 2. Load and inspect the model
doc = libsbml.readSBMLFromFile("BIOMD0000000012.xml")
model = doc.getModel()
print(f"Model: {model.getId()} | Level {doc.getLevel()} Version {doc.getVersion()}")
print(f"Species: {model.getNumSpecies()}, Reactions: {model.getNumReactions()}")

# 3. Print all global parameters and their values
print("\nGlobal parameters:")
for i in range(model.getNumParameters()):
    p = model.getParameter(i)
    print(f"  {p.getId():<20} = {p.getValue()}")

# 4. Modify a parameter (example: increase a rate constant by 2x)
target_param = model.getParameter("k3")   # parameter name varies by model
if target_param:
    old_val = target_param.getValue()
    target_param.setValue(old_val * 2.0)
    print(f"\nModified k3: {old_val} → {target_param.getValue()}")

# 5. Save modified model
writer = libsbml.SBMLWriter()
writer.writeSBMLToFile(doc, "BIOMD0000000012_modified.xml")
print("Saved modified model.")

# 6. Simulate with Tellurium (optional)
try:
    import tellurium as te
    r = te.loadSBMLModel(open("BIOMD0000000012_modified.xml").read())
    result = r.simulate(0, 100, 500)
    print(f"Simulation complete: {result.shape[0]} time points, {result.shape[1]-1} species")
    r.plot(result, title="BIOMD0000000012 modified simulation")
except ImportError:
    print("tellurium not installed — simulation step skipped")
```

### Workflow 2: Build a Michaelis-Menten ODE Model from Scratch

**Goal**: Construct a full Michaelis-Menten enzyme kinetics SBML model and verify it passes validation.

```python
import libsbml

def build_mm_model() -> libsbml.SBMLDocument:
    """Create a Michaelis-Menten enzyme kinetics SBML L3V2 model."""
    doc = libsbml.SBMLDocument(3, 2)
    model = doc.createModel()
    model.setId("michaelis_menten")
    model.setName("Michaelis-Menten Enzyme Kinetics")
    model.setTimeUnits("second")
    model.setSubstanceUnits("mole")
    model.setVolumeUnits("litre")
    model.setExtentUnits("mole")

    # Compartment
    c = model.createCompartment()
    c.setId("cell"); c.setConstant(True); c.setSize(1e-15); c.setSpatialDimensions(3)

    # Species: S (substrate), E (enzyme), ES (complex), P (product)
    for sp_id, init_conc, boundary in [
        ("S",  1e-3, False), ("E",  1e-6, False),
        ("ES", 0.0,  False), ("P",  0.0,  False)
    ]:
        sp = model.createSpecies()
        sp.setId(sp_id); sp.setCompartment("cell")
        sp.setInitialConcentration(init_conc)
        sp.setBoundaryCondition(boundary); sp.setConstant(False)
        sp.setHasOnlySubstanceUnits(False)

    # Parameters
    for p_id, p_val in [("kf", 1e6), ("kr", 1e-3), ("kcat", 0.1)]:
        p = model.createParameter()
        p.setId(p_id); p.setValue(p_val); p.setConstant(True)

    # Reactions
    def make_rxn(m, rxn_id, reacts, prods, formula):
        rxn = m.createReaction(); rxn.setId(rxn_id); rxn.setReversible(False)
        for sp, s in reacts:
            sr = rxn.createReactant(); sr.setSpecies(sp); sr.setStoichiometry(s); sr.setConstant(True)
        for sp, s in prods:
            sr = rxn.createProduct();  sr.setSpecies(sp); sr.setStoichiometry(s); sr.setConstant(True)
        kl = rxn.createKineticLaw()
        ast = libsbml.parseL3Formula(formula)
        if ast is None: raise ValueError(f"Bad formula: {formula}")
        kl.setMath(ast)

    make_rxn(model, "v_forward",  [("S",1),("E",1)], [("ES",1)], "kf * S * E * cell")
    make_rxn(model, "v_reverse",  [("ES",1)], [("S",1),("E",1)], "kr * ES * cell")
    make_rxn(model, "v_catalysis",[("ES",1)], [("P",1),("E",1)], "kcat * ES * cell")
    return doc

doc = build_mm_model()

# Validate
doc.setConsistencyChecks(libsbml.LIBSBML_CAT_UNITS_CONSISTENCY, False)  # skip units for brevity
n_errors = doc.checkConsistency()
print(f"Validation: {n_errors} issue(s)")
for i in range(n_errors):
    e = doc.getError(i)
    print(f"  [{e.getSeverityAsString()}] {e.getMessage()}")

writer = libsbml.SBMLWriter()
writer.writeSBMLToFile(doc, "michaelis_menten.xml")
print("Saved michaelis_menten.xml")
print(f"Reactions: {doc.getModel().getNumReactions()}, Species: {doc.getModel().getNumSpecies()}")
```

### Workflow 3: Extract Stoichiometry Matrix as NumPy Array

**Goal**: Parse a loaded SBML model and extract the stoichiometry matrix and reaction/species lists for custom linear algebra or FBA analysis.

```python
import libsbml
import numpy as np
import pandas as pd

doc = libsbml.readSBMLFromFile("model.xml")
model = doc.getModel()

n_species   = model.getNumSpecies()
n_reactions = model.getNumReactions()

species_ids  = [model.getSpecies(i).getId()  for i in range(n_species)]
rxn_ids      = [model.getReaction(i).getId() for i in range(n_reactions)]

# Build stoichiometry matrix S: rows=species, cols=reactions
S = np.zeros((n_species, n_reactions), dtype=float)
sp_index = {sp_id: idx for idx, sp_id in enumerate(species_ids)}

for j, rxn_id in enumerate(rxn_ids):
    rxn = model.getReaction(rxn_id)
    # Reactants: negative stoichiometry
    for k in range(rxn.getNumReactants()):
        sr = rxn.getReactant(k)
        sp_id = sr.getSpecies()
        if sp_id in sp_index:
            S[sp_index[sp_id], j] -= sr.getStoichiometry()
    # Products: positive stoichiometry
    for k in range(rxn.getNumProducts()):
        sr = rxn.getProduct(k)
        sp_id = sr.getSpecies()
        if sp_id in sp_index:
            S[sp_index[sp_id], j] += sr.getStoichiometry()

# Create a labeled DataFrame for inspection
S_df = pd.DataFrame(S, index=species_ids, columns=rxn_ids)
print("Stoichiometry matrix (S):")
print(S_df.to_string())
print(f"\nMatrix shape: {S.shape} (species × reactions)")

# Null-space rank as a basic model check
rank = np.linalg.matrix_rank(S)
print(f"Rank of S: {rank}")
print(f"Degrees of freedom (flux modes): {n_reactions - rank}")
```

### Workflow 4: Load SBML FBA Model and Hand Off to COBRApy

**Goal**: Read a genome-scale metabolic model in SBML FBC format and load it into COBRApy for FBA analysis.

```python
import libsbml
import cobra
import cobra.io

# Method A: use COBRApy's built-in SBML reader (wraps libSBML)
model_cobra = cobra.io.read_sbml_model("iJO1366.xml")
print(f"COBRApy model: {model_cobra.id}")
print(f"  Reactions: {len(model_cobra.reactions)}")
print(f"  Metabolites: {len(model_cobra.metabolites)}")
print(f"  Genes: {len(model_cobra.genes)}")

# Run FBA
solution = model_cobra.optimize()
print(f"\nFBA objective value: {solution.objective_value:.4f}")
print(f"Status: {solution.status}")

# Method B: use libSBML to inspect FBC metadata before loading into COBRApy
doc = libsbml.readSBMLFromFile("iJO1366.xml")
model = doc.getModel()
fbc = model.getPlugin("fbc")

if fbc:
    n_obj = fbc.getNumObjectives()
    active_obj_id = fbc.getActiveObjectiveId()
    print(f"\nlibSBML FBC: {n_obj} objective(s), active='{active_obj_id}'")
    obj = fbc.getObjective(active_obj_id)
    if obj:
        print(f"Objective type: {obj.getType()}")
        for i in range(obj.getNumFluxObjectives()):
            fo = obj.getFluxObjective(i)
            print(f"  {fo.getReaction()} (coeff={fo.getCoefficient()})")
```

## Key Parameters

| Parameter | Module | Default | Range / Options | Effect |
|-----------|--------|---------|-----------------|--------|
| `level` | SBMLDocument | `3` | `1`, `2`, `3` | SBML Level; use L3 for all new models; L2 for legacy tool compatibility |
| `version` | SBMLDocument | `2` | `1`–`2` (L3); `1`–`4` (L2) | SBML Version within the Level; L3V2 is the current standard |
| `initialConcentration` | Species | `0.0` | any float | Starting molar concentration; mutually exclusive with `initialAmount` |
| `hasOnlySubstanceUnits` | Species | `False` | `True`, `False` | If `True`, kinetic laws reference amount (mol); if `False`, they reference concentration (M) |
| `boundaryCondition` | Species | `False` | `True`, `False` | If `True`, ODE solver does not change this species — use for external inputs |
| `constant` | Species/Parameter | `True` (Param) | `True`, `False` | `False` required for assignment rule targets and mutable parameters |
| `strict` | FBC plugin | `True` | `True`, `False` | FBC strict mode enforces that all flux bounds are defined as parameters |
| `targetLevel` / `targetVersion` | ConversionProperties | — | L/V integers | Target for `doc.convert()` level/version conversion |
| `LIBSBML_CAT_UNITS_CONSISTENCY` | checkConsistency | `True` | `True`, `False` | Enable/disable unit dimension checking during validation |

## Best Practices

1. **Always check `parseL3Formula` return value**: the function returns `None` on malformed input without raising an exception. Assigning `None` to `kl.setMath()` creates a model with a missing kinetic law that passes parsing but fails validation.
   ```python
   ast = libsbml.parseL3Formula("Vmax * S / (Km + S)")
   if ast is None:
       raise ValueError("Formula parse failed")
   kl.setMath(ast)
   ```

2. **Set `constant=False` on assignment rule targets**: any parameter or species that is the target of an `AssignmentRule` or `RateRule` must have `constant` set to `False`. A `True` value creates a constraint violation that fails consistency checking.

3. **Multiply reaction rate by compartment volume in kinetic laws**: SBML extent units are moles (or molecules), so rates must have units of extent/time. For species measured in concentration, multiply by compartment size: `kf * S * E * compartment_volume`. Omitting this factor is the most common kinetic law unit error.

4. **Enable only the packages you use**: calling `doc.enablePackage()` for unnecessary extensions (layout, groups) adds namespace declarations that confuse some downstream tools. Enable FBC only for FBA/FVA models; leave it off for pure ODE models.

5. **Use `readSBMLFromFile` (top-level function) for quick loading**: the convenience function `libsbml.readSBMLFromFile(path)` is equivalent to creating a `SBMLReader` instance and calling `readSBMLFromFile` on it. Both return an `SBMLDocument`; choose whichever is less verbose.

6. **Validate before saving and after converting**: run `doc.checkConsistency()` immediately before any `writeSBMLToFile` call and again after any level/version conversion. Conversion can introduce new warnings, especially for units.

## Common Recipes

### Recipe: List All Reactions with Their Kinetic Formulas

When to use: audit an SBML model to document every reaction and its rate law before modifying parameters.

```python
import libsbml

doc = libsbml.readSBMLFromFile("model.xml")
model = doc.getModel()

print(f"{'Reaction':<20} {'Reversible':<12} {'Kinetic Law'}")
print("-" * 80)
for i in range(model.getNumReactions()):
    rxn = model.getReaction(i)
    if rxn.isSetKineticLaw():
        formula = libsbml.formulaToL3String(rxn.getKineticLaw().getMath())
    else:
        formula = "(no kinetic law)"
    rev = "reversible" if rxn.getReversible() else "irreversible"
    print(f"{rxn.getId():<20} {rev:<12} {formula}")
```

### Recipe: Batch-Update Multiple Parameters

When to use: sensitivity analysis — sweep a set of kinetic constants over a range of values and re-save an SBML model for each.

```python
import libsbml
import copy

doc = libsbml.readSBMLFromFile("model.xml")
writer = libsbml.SBMLWriter()

# Parameter sweep: vary kcat and Km
sweep = [
    {"kcat": 0.05, "Km": 0.01},
    {"kcat": 0.10, "Km": 0.01},
    {"kcat": 0.20, "Km": 0.01},
    {"kcat": 0.10, "Km": 0.05},
]

for idx, params in enumerate(sweep):
    # Re-read fresh copy each iteration to avoid cumulative edits
    doc_i = libsbml.readSBMLFromFile("model.xml")
    model_i = doc_i.getModel()
    for p_id, p_val in params.items():
        p = model_i.getParameter(p_id)
        if p:
            p.setValue(p_val)
    fname = f"model_sweep_{idx:03d}.xml"
    writer.writeSBMLToFile(doc_i, fname)
    print(f"Saved {fname}: {params}")
```

### Recipe: Extract All Species Initial Conditions as a Dict

When to use: initializing a custom ODE solver (e.g., scipy.integrate.solve_ivp) using SBML-defined initial conditions.

```python
import libsbml

doc = libsbml.readSBMLFromFile("model.xml")
model = doc.getModel()

initial_conditions = {}
for i in range(model.getNumSpecies()):
    sp = model.getSpecies(i)
    if sp.isSetInitialConcentration():
        initial_conditions[sp.getId()] = sp.getInitialConcentration()
    elif sp.isSetInitialAmount():
        # Convert amount to concentration using compartment volume
        comp = model.getCompartment(sp.getCompartment())
        vol = comp.getSize() if comp and comp.isSetSize() else 1.0
        initial_conditions[sp.getId()] = sp.getInitialAmount() / vol
    else:
        initial_conditions[sp.getId()] = 0.0

print("Initial conditions (concentration in model units):")
for sp_id, val in initial_conditions.items():
    print(f"  {sp_id}: {val:.6g}")
```

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| `ImportError: No module named 'libsbml'` | Package not installed | `pip install python-libsbml`; note the import name is `libsbml`, not `python_libsbml` |
| `parseL3Formula` returns `None` | Malformed formula string (wrong operator, undefined function) | Check formula syntax; use `libsbml.formulaToL3String` on a known-good AST to see expected format; `*` is multiplication, `^` or `pow()` for exponentiation |
| Consistency check reports unit errors | Kinetic law missing compartment volume factor | Multiply rate formula by compartment volume: `kf * S * E * V`; set `substance_units = "mole"` and `volume_units = "litre"` on the model |
| `getPlugin("fbc")` returns `None` | FBC package not enabled on the document | Call `doc.enablePackage(libsbml.FbcExtension.getXmlnsL3V1V2(), "fbc", True)` before reading or building the model |
| Level/version conversion returns non-zero code | Source model has features unsupported in target level | Check `doc.getNumErrors()` after conversion; SBML L1 has severe limitations (no compartments, no units); prefer L2V4 as minimum target |
| Assignment rule target raises "model is overdetermined" | Species or parameter is `constant=True` but targeted by a rule | Set `constant=False` on the rule target; `constant=True` means the value is fixed and cannot be overridden by rules |
| COBRApy `read_sbml_model` fails on custom-built SBML | FBC `strict=True` but flux bounds not defined as parameters | Ensure every reaction's FBC plugin has `setLowerFluxBound` and `setUpperFluxBound` pointing to existing parameter IDs |
| Large model read is slow (>10 seconds) | Very large SBML file (genome-scale model, 10k+ reactions) | Normal — libSBML XML parsing is single-threaded; use `readSBMLFromFile` (not string-based) and avoid re-reading in loops |

## Related Skills

- **cobrapy-metabolic-modeling** — FBA, FVA, gene knockouts, and flux sampling on SBML/JSON metabolic models; use libSBML to build or edit the model, COBRApy to analyze it
- **string-database-ppi** — protein-protein interaction networks; export PPI data to SBML qual extension for logical network models
- **reactome-database** — pathway data source; Reactome provides SBML exports of human pathways that can be loaded and analyzed with libSBML
- **brenda-database** — kinetic parameter source (Km, Vmax, kcat) for populating libSBML kinetic laws with experimentally measured values
- **networkx-graph-analysis** — use after extracting the reaction network from SBML to analyze graph topology (shortest paths, connectivity, centrality)
- **sympy-symbolic-math** — symbolic manipulation of kinetic law expressions parsed from SBML; combine with `formulaToL3String` for analytical steady-state derivation

## References

- [libSBML Python documentation](https://sbml.org/software/libsbml/libsbml-docs/api/python/) — complete Python API reference
- [SBML specification portal](https://sbml.org/documents/specifications/) — official SBML Level 3 core and package specifications
- [libSBML GitHub repository](https://github.com/sbmlteam/libsbml) — source code, issue tracker, and release notes
- [BioModels Database](https://www.ebi.ac.uk/biomodels/) — curated SBML model repository (1,000+ manually curated models)
- [Hucka et al. (2003) Bioinformatics 19(4):524–531](https://doi.org/10.1093/bioinformatics/btg015) — original SBML specification paper
- [Keating et al. (2020) Molecular Systems Biology 16(8):e9110](https://doi.org/10.15252/msb.20199110) — SBML Level 3 and the current extension ecosystem overview
