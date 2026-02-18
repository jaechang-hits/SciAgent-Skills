---
name: "opentrons-protocol-api"
description: "Python API v2 for programming Opentrons OT-2 and Flex liquid handling robots. Write protocols as Python files with metadata and a run() function; control pipettes, labware, and hardware modules (thermocycler, heater-shaker, magnetic, temperature). Simulate locally with opentrons_simulate, then upload to the robot app. Use PyLabRobot instead for hardware-agnostic scripts that run on Hamilton, Tecan, or other vendors."
license: "Apache-2.0"
---

# Opentrons Python Protocol API

## Overview

The Opentrons Protocol API v2 lets you write liquid handling protocols as plain Python files that run on OT-2 or Flex robots. Every protocol defines a `metadata` dictionary, an optional `requirements` dictionary, and a `run(protocol)` function. The `ProtocolContext` object passed to `run()` exposes all deck setup, pipette operations, module control, and utility methods. Protocols can be simulated on any computer with `opentrons_simulate` before uploading to the robot through the Opentrons App or HTTP API.

## When to Use

- **Setting up PCR reactions**: Distribute master mix from a tube rack into a thermocycler plate, add template DNA from individual tubes, then execute a PCR profile automatically.
- **Running serial dilutions**: Programmatically step a multi-channel pipette across a 96-well plate to create 2-fold or custom dilution curves with defined diluent volumes.
- **Performing ELISA plate layouts**: Add blocking buffer, primary antibody, secondary antibody, and substrate to defined wells with tip changes between each reagent.
- **Automating magnetic bead cleanups**: Engage/disengage the magnetic module, aspirate supernatant, wash with ethanol, and elute — in a fully automated loop.
- **Plate reformatting and stamping**: Transfer an entire 96-well plate to a destination plate with one command; reformat from tubes to plates.
- **Integrating hardware modules**: Coordinate temperature control, shaking, and liquid handling steps in a single protocol with precise timing.
- Use `PyLabRobot` instead when writing protocols that must run on Hamilton STAR, Tecan Freedom EVO, or other vendors without Opentrons-specific hardware; for Opentrons-only workflows the native Protocol API provides tighter integration and module support.
- For retrieving and parsing published protocols before automation, use `protocolsio-integration` to search protocols.io alongside this skill.

## Prerequisites

- **Python packages**: `opentrons`
- **Robot types**: OT-2 (slots 1-11, Gen2 pipettes) or Flex (slots A1-D3, Flex pipettes)
- **Environment**: Python 3.10+; Opentrons App for uploading to physical robot
- **CLI tool**: `opentrons_simulate` ships with the package for local testing

```bash
pip install opentrons
# Verify installation and simulate a protocol locally
opentrons_simulate my_protocol.py
```

## Quick Start

A minimal protocol showing all required elements — metadata, labware, instrument, and a transfer:

```python
from opentrons import protocol_api

metadata = {
    "protocolName": "Simple Reagent Distribution",
    "author": "Lab Automation Team",
    "apiLevel": "2.19",
}

def run(protocol: protocol_api.ProtocolContext):
    # Load labware onto deck slots
    tips    = protocol.load_labware("opentrons_96_tiprack_300ul", "1")
    source  = protocol.load_labware("nest_12_reservoir_15ml", "2")
    plate   = protocol.load_labware("corning_96_wellplate_360ul_flat", "3")

    # Load pipette and attach tip rack
    pipette = protocol.load_instrument("p300_single_gen2", "left", tip_racks=[tips])

    # Distribute 50 µL from reservoir A1 to first 12 wells using one tip
    pipette.distribute(50, source["A1"], plate.wells()[:12], new_tip="once")
    protocol.comment("Distribution complete")
```

```bash
# Simulate locally — no robot needed
opentrons_simulate simple_reagent_distribution.py
```

## Core API

### Module 1: Protocol Metadata and Deck Setup

Every protocol requires a `metadata` dict specifying at minimum `apiLevel`. The optional `requirements` dict sets the target robot type. All labware and instruments are loaded through the `ProtocolContext`.

```python
from opentrons import protocol_api

# Minimum required metadata
metadata = {
    "protocolName": "My Assay Protocol",
    "author": "Jane Smith <jane@lab.org>",
    "description": "96-well assay setup with temperature control",
    "apiLevel": "2.19",
}

# Optional: target a specific robot type (Flex or OT-2)
requirements = {"robotType": "OT-2", "apiLevel": "2.19"}

def run(protocol: protocol_api.ProtocolContext):
    # OT-2: slots numbered 1-11 in a 3×4 grid
    tips_300 = protocol.load_labware("opentrons_96_tiprack_300ul", "1")
    tips_20  = protocol.load_labware("opentrons_96_tiprack_20ul",  "4")
    source   = protocol.load_labware("nest_12_reservoir_15ml",     "2", label="Buffer Reservoir")
    plate    = protocol.load_labware("corning_96_wellplate_360ul_flat", "3")
    tube_rack = protocol.load_labware("opentrons_24_tuberack_nest_1.5ml_snapcap", "5")

    # Load both pipettes (optional: one or two mounts)
    p300 = protocol.load_instrument("p300_single_gen2", "left",  tip_racks=[tips_300])
    p20  = protocol.load_instrument("p20_single_gen2",  "right", tip_racks=[tips_20])

    print(f"Deck has {len(protocol.deck)} slots; pipettes: {[p300.name, p20.name]}")
```

OT-2 deck layout (3 columns × 4 rows, numbered left-to-right, bottom-to-top):

```
Slot map (OT-2):         Slot map (Flex, A-D rows, 1-3 cols):
 10 | 11 | Trash          D1 | D2 | D3
  7 |  8 |  9             C1 | C2 | C3
  4 |  5 |  6             B1 | B2 | B3
  1 |  2 |  3             A1 | A2 | A3
```

Common OT-2 pipette names: `p20_single_gen2`, `p300_single_gen2`, `p1000_single_gen2`, `p20_multi_gen2`, `p300_multi_gen2`.
Common Flex pipette names: `p50_single_flex`, `p1000_single_flex`, `p50_multi_flex`, `p1000_multi_flex`, `flex_96channel_1000`.

### Module 2: Pipette Operations

Low-level aspirate/dispense/blow-out operations for precise step-by-step control.

```python
def run(protocol: protocol_api.ProtocolContext):
    tips   = protocol.load_labware("opentrons_96_tiprack_300ul", "1")
    source = protocol.load_labware("nest_12_reservoir_15ml", "2")
    dest   = protocol.load_labware("corning_96_wellplate_360ul_flat", "3")
    p300   = protocol.load_instrument("p300_single_gen2", "left", tip_racks=[tips])

    p300.pick_up_tip()

    # Aspirate and dispense — basic liquid movement
    p300.aspirate(100, source["A1"])         # draw 100 µL from reservoir
    p300.dispense(100, dest["A1"])           # expel into plate well

    # Air gap to prevent dripping during transport
    p300.aspirate(80, source["A2"])
    p300.air_gap(20)                         # draw 20 µL air to cap the tip
    p300.dispense(100, dest["A2"])           # dispenses liquid + air

    # Mix in place (repetitions, volume)
    p300.mix(3, 60, dest["A1"])             # mix 60 µL × 3 times

    # Remove exterior droplets / expel residual
    p300.touch_tip(dest["A1"])              # wipe tip on well rim
    p300.blow_out(dest["A1"].top())         # expel last drop at top

    p300.drop_tip()
    protocol.comment("Low-level operations complete")
```

```python
def run(protocol: protocol_api.ProtocolContext):
    tips = protocol.load_labware("opentrons_96_tiprack_300ul", "1")
    p300 = protocol.load_instrument("p300_single_gen2", "left", tip_racks=[tips])

    # Adjust flow rates (µL/s) for viscous or sensitive samples
    p300.flow_rate.aspirate = 50    # slow down for viscous liquids (default ~150)
    p300.flow_rate.dispense = 150   # default dispense speed
    p300.flow_rate.blow_out = 300   # fast blow-out for complete expulsion
    print(f"Aspirate rate: {p300.flow_rate.aspirate} µL/s")
```

### Module 3: transfer() Shortcut

`transfer()`, `distribute()`, and `consolidate()` handle tip management automatically and accept mix, blow-out, and air-gap options.

```python
def run(protocol: protocol_api.ProtocolContext):
    tips   = protocol.load_labware("opentrons_96_tiprack_300ul", "1")
    source = protocol.load_labware("corning_96_wellplate_360ul_flat", "2")
    dest   = protocol.load_labware("corning_96_wellplate_360ul_flat", "3")
    p300   = protocol.load_instrument("p300_single_gen2", "left", tip_racks=[tips])

    # transfer(): one source → one destination, with optional per-well tip changes
    p300.transfer(
        100,
        source["A1"],
        dest["A1"],
        new_tip="always",       # options: "always", "once", "never"
        mix_after=(3, 50),      # mix 50 µL × 3 reps after each dispense
        blow_out=True,
        touch_tip=True,
    )

    # transfer() with lists: pairwise source-destination mapping
    sources = source.wells()[:8]
    dests   = dest.wells()[:8]
    p300.transfer(75, sources, dests, new_tip="always")

    # distribute(): one source → many destinations (single tip, multi-dispense)
    p300.distribute(
        50,
        source["A1"],
        dest.wells()[:12],
        new_tip="once",         # use one tip for all destinations
        disposal_volume=10,     # extra volume drawn to ensure accuracy
    )

    # consolidate(): many sources → one destination (collect, then dispense)
    p300.consolidate(
        50,
        source.wells()[:8],
        dest["A1"],
        mix_after=(3, 100),
    )
    print("Compound transfer operations complete")
```

### Module 4: Labware, Liquids, and Well Access

Load labware from the library, navigate wells by name/row/column, and define liquids for visual tracking in the Opentrons App.

```python
def run(protocol: protocol_api.ProtocolContext):
    plate  = protocol.load_labware("corning_96_wellplate_360ul_flat", "1")
    p300   = protocol.load_instrument("p300_single_gen2", "left",
                                      tip_racks=[protocol.load_labware("opentrons_96_tiprack_300ul", "2")])

    # Access wells by alphanumeric name
    well_a1 = plate["A1"]

    # Access all wells (column-major order: A1, B1, C1, ..., H1, A2, ...)
    all_wells = plate.wells()
    print(f"Total wells: {len(all_wells)}")   # 96

    # Access by row (8 rows, A-H; each row has 12 wells)
    row_a = plate.rows()[0]    # [A1, A2, ..., A12]
    row_b = plate.rows()[1]    # [B1, B2, ..., B12]

    # Access by column (12 columns, 1-12; each column has 8 wells)
    col_1 = plate.columns()[0]   # [A1, B1, C1, D1, E1, F1, G1, H1]

    # Vertical position control within a well
    p300.pick_up_tip()
    p300.aspirate(80, well_a1.bottom(z=1))   # 1 mm above well bottom
    p300.dispense(80, well_a1.top(z=-2))     # 2 mm below well top
    p300.aspirate(80, well_a1.center())      # geometric center
    p300.drop_tip()
```

```python
def run(protocol: protocol_api.ProtocolContext):
    reservoir = protocol.load_labware("nest_12_reservoir_15ml", "1")
    plate     = protocol.load_labware("corning_96_wellplate_360ul_flat", "2")

    # Define liquids for visual tracking in Opentrons App
    pbs     = protocol.define_liquid(name="1× PBS",    description="Phosphate buffered saline",    display_color="#0077BB")
    sample  = protocol.define_liquid(name="Sample",    description="Cell lysate, 1 mg/mL protein", display_color="#EE7733")

    # Assign liquids to wells with known starting volumes (µL)
    reservoir["A1"].load_liquid(liquid=pbs,    volume=10000)
    reservoir["A2"].load_liquid(liquid=sample, volume=5000)

    # Mark destination wells as empty
    for well in plate.wells():
        well.load_empty()

    print("Liquids defined and assigned")
```

### Module 5: Hardware Modules

Control temperature, magnetic, thermocycler, and heater-shaker modules. Each module is loaded by its model name string and occupies specific deck slots.

```python
def run(protocol: protocol_api.ProtocolContext):
    # --- Temperature Module (Gen2) ---
    temp_mod = protocol.load_module("temperature module gen2", "3")
    temp_plate = temp_mod.load_labware("corning_96_wellplate_360ul_flat")
    temp_mod.set_temperature(celsius=4)       # blocks until target reached
    print(f"Temp module: {temp_mod.temperature}°C")
    # temp_mod.deactivate()                   # turn off at end

    # --- Magnetic Module (Gen2) ---
    mag_mod  = protocol.load_module("magnetic module gen2", "6")
    mag_plate = mag_mod.load_labware("nest_96_wellplate_100ul_pcr_full_skirt")
    mag_mod.engage(height_from_base=10)       # raise magnets 10 mm from plate base
    protocol.delay(seconds=300)               # hold beads for 5 min
    mag_mod.disengage()

    # --- Heater-Shaker Module ---
    hs_mod = protocol.load_module("heaterShakerModuleV1", "1")
    hs_plate = hs_mod.load_labware("corning_96_wellplate_360ul_flat")
    hs_mod.close_labware_latch()
    hs_mod.set_target_temperature(celsius=37)
    hs_mod.wait_for_temperature()
    hs_mod.set_and_wait_for_shake_speed(rpm=500)
    protocol.delay(minutes=30)
    hs_mod.deactivate_shaker()
    hs_mod.deactivate_heater()
    hs_mod.open_labware_latch()
    print("Heater-shaker cycle complete")
```

```python
def run(protocol: protocol_api.ProtocolContext):
    # --- Thermocycler Module (Gen2) ---
    # Auto-occupies slots 7-11 on OT-2; no slot argument needed
    tc_mod  = protocol.load_module("thermocyclerModuleV2")
    tc_plate = tc_mod.load_labware("nest_96_wellplate_100ul_pcr_full_skirt")

    tc_mod.open_lid()
    tc_mod.set_lid_temperature(celsius=105)   # pre-heat lid to prevent condensation

    # Initial denaturation
    tc_mod.set_block_temperature(95, hold_time_seconds=180)

    # PCR cycling profile
    profile = [
        {"temperature": 95, "hold_time_seconds": 15},   # denaturation
        {"temperature": 60, "hold_time_seconds": 30},   # annealing
        {"temperature": 72, "hold_time_seconds": 30},   # extension
    ]
    tc_mod.execute_profile(steps=profile, repetitions=35, block_max_volume=25)

    # Final extension and hold
    tc_mod.set_block_temperature(72, hold_time_minutes=5)
    tc_mod.set_block_temperature(4)           # hold at 4°C indefinitely
    tc_mod.deactivate_lid()
    tc_mod.open_lid()
    print("PCR complete; plate held at 4°C")
```

### Module 6: Advanced Protocol Features

Pause for user interaction, log comments visible in the app, control rail lights, and detect simulation mode.

```python
def run(protocol: protocol_api.ProtocolContext):
    # Pause and prompt the user (robot stops, app shows message)
    protocol.pause(msg="Add 10 µL of enzyme to tube A1, then resume")

    # Timed delay (robot waits without user action)
    protocol.delay(seconds=30, msg="Waiting 30s for reaction incubation")
    protocol.delay(minutes=5)

    # Log a comment visible in Opentrons App run log
    protocol.comment("Starting serial dilution — columns 1 to 11")

    # Rail lights for visual status indication
    protocol.set_rail_lights(True)    # lights on
    protocol.set_rail_lights(False)   # lights off

    # Home all axes (useful after an error or before finishing)
    protocol.home()

    # Detect simulation vs. physical run — skip slow waits in simulation
    if protocol.is_simulating():
        protocol.comment("Running in simulation mode — skipping 10-min incubation")
    else:
        protocol.delay(minutes=10)

    # Load waste bin (Flex only — OT-2 uses fixed trash)
    # trash = protocol.load_trash_bin("A3")

    print("Protocol control features demonstrated")
```

## Common Workflows

### Workflow 1: PCR Setup with Thermocycler

**Goal**: Transfer master mix from a tube rack into a PCR plate on the thermocycler, add template DNA from individual samples, then run a complete PCR cycling program.

```python
from opentrons import protocol_api

metadata = {
    "protocolName": "PCR Setup and Run",
    "author": "Lab Automation",
    "apiLevel": "2.19",
}

def run(protocol: protocol_api.ProtocolContext):
    # Hardware setup
    tc_mod    = protocol.load_module("thermocyclerModuleV2")
    tc_plate  = tc_mod.load_labware("nest_96_wellplate_100ul_pcr_full_skirt")
    tips_300  = protocol.load_labware("opentrons_96_tiprack_300ul", "1")
    tips_20   = protocol.load_labware("opentrons_96_tiprack_20ul",  "4")
    reagents  = protocol.load_labware("opentrons_24_tuberack_nest_1.5ml_snapcap", "2")
    p300      = protocol.load_instrument("p300_single_gen2", "left",  tip_racks=[tips_300])
    p20       = protocol.load_instrument("p20_single_gen2",  "right", tip_racks=[tips_20])

    # Define liquids
    master_mix = protocol.define_liquid("Master Mix", "2× PCR master mix", "#33BBEE")
    template   = protocol.define_liquid("Template",   "gDNA 10 ng/µL",     "#EE3377")
    reagents["A1"].load_liquid(master_mix, volume=500)
    for i in range(8):
        reagents.wells()[i + 1].load_liquid(template, volume=50)

    # Step 1: Open lid and distribute master mix (20 µL per well, 8 wells)
    tc_mod.open_lid()
    protocol.comment("Distributing master mix")
    p300.distribute(
        20,
        reagents["A1"],
        tc_plate.wells()[:8],
        new_tip="once",
        blow_out=True,
        blowout_location="source well",
    )

    # Step 2: Add template DNA (5 µL per well, fresh tip each time)
    protocol.comment("Adding template DNA")
    for i in range(8):
        p20.transfer(
            5,
            reagents.wells()[i + 1],
            tc_plate.wells()[i],
            new_tip="always",
            mix_after=(2, 10),
        )

    # Step 3: Run PCR
    tc_mod.close_lid()
    tc_mod.set_lid_temperature(105)
    tc_mod.set_block_temperature(95, hold_time_seconds=180)  # initial denaturation

    profile = [
        {"temperature": 95, "hold_time_seconds": 15},
        {"temperature": 60, "hold_time_seconds": 30},
        {"temperature": 72, "hold_time_seconds": 30},
    ]
    tc_mod.execute_profile(steps=profile, repetitions=35, block_max_volume=25)
    tc_mod.set_block_temperature(72, hold_time_minutes=5)    # final extension
    tc_mod.set_block_temperature(4)                          # hold
    tc_mod.deactivate_lid()
    tc_mod.open_lid()
    protocol.comment("PCR complete — 8 reactions in wells A1:H1")
```

### Workflow 2: ELISA Serial Dilution with Multi-Channel Pipette

**Goal**: Use a multi-channel pipette to add diluent to columns 2-12, perform 2-fold serial dilutions across the plate, and add detection reagent to all wells in a single pass.

```python
from opentrons import protocol_api

metadata = {
    "protocolName": "ELISA Serial Dilution",
    "author": "Lab Automation",
    "apiLevel": "2.19",
}

def run(protocol: protocol_api.ProtocolContext):
    # Deck layout
    tips_300  = protocol.load_labware("opentrons_96_tiprack_300ul", "1")
    tips_300b = protocol.load_labware("opentrons_96_tiprack_300ul", "4")  # extra rack
    reservoir = protocol.load_labware("nest_12_reservoir_15ml", "2")
    plate     = protocol.load_labware("corning_96_wellplate_360ul_flat", "3")
    multi     = protocol.load_instrument("p300_multi_gen2", "left",
                                          tip_racks=[tips_300, tips_300b])

    # Define liquids
    diluent = protocol.define_liquid("Diluent", "PBS + 1% BSA", "#0077BB")
    sample  = protocol.define_liquid("Sample",  "Serum 1:10",   "#EE7733")
    reservoir["A1"].load_liquid(diluent, volume=50000)
    reservoir["A2"].load_liquid(sample,  volume=5000)

    # Step 1: Load column 1 with undiluted sample (all 8 rows at once)
    protocol.comment("Loading undiluted sample into column 1")
    multi.transfer(100, reservoir["A2"], plate.columns()[0], new_tip="once")

    # Step 2: Add diluent to columns 2-12
    protocol.comment("Adding diluent to columns 2-12")
    multi.distribute(
        100,
        reservoir["A1"],
        [col[0] for col in plate.columns()[1:]],  # A2 through A12 (multi-channel reads full column)
        new_tip="once",
        disposal_volume=10,
    )

    # Step 3: Serial dilution — transfer 100 µL from each column to the next, mix
    protocol.comment("Performing 2-fold serial dilution across columns 1→11")
    multi.transfer(
        100,
        [col[0] for col in plate.columns()[:11]],   # cols 1-11 as source
        [col[0] for col in plate.columns()[1:]],    # cols 2-12 as destination
        mix_after=(5, 80),                           # mix 80 µL × 5 reps after each dispense
        new_tip="always",                            # fresh tip per column to avoid carry-over
    )

    # Step 4: Remove 100 µL from column 12 to equalize volumes
    multi.pick_up_tip()
    multi.aspirate(100, plate.columns()[11][0])
    multi.drop_tip()

    protocol.comment("ELISA serial dilution complete — 11 dilution steps, 12 columns")
    print("Protocol complete: 2-fold dilution series across 96-well plate")
```

## Key Parameters

| Parameter | Module / Function | Default | Range / Options | Effect |
|-----------|-------------------|---------|-----------------|--------|
| `new_tip` | `transfer`, `distribute`, `consolidate` | `"always"` | `"always"`, `"once"`, `"never"` | Controls tip change strategy; use `"always"` to prevent cross-contamination |
| `mix_after` | `transfer` | `None` | `(repetitions, volume)` tuple | Aspirate/dispense in destination well after each dispense to homogenize |
| `mix_before` | `transfer` | `None` | `(repetitions, volume)` tuple | Aspirate/dispense in source well before each aspirate |
| `blow_out` | `transfer` | `False` | `True`, `False` | Expel residual volume after dispense; set `blowout_location` to control where |
| `air_gap` | `transfer` | `0` | `0`–pipette max µL | Insert air gap after aspirate to prevent dripping during robot moves |
| `disposal_volume` | `distribute` | `0` | `0`–pipette max µL | Extra volume drawn at start to improve dispense accuracy; discarded to trash |
| `flow_rate.aspirate` | pipette property | varies by model | `1`–`1000` µL/s | Aspirate speed; lower for viscous samples (glycerol, proteins > 5 mg/mL) |
| `flow_rate.dispense` | pipette property | varies by model | `1`–`1000` µL/s | Dispense speed; lower for foaming or delicate cell suspensions |
| `height_from_base` | `mag_mod.engage()` | — | `0`–`20` mm | Height of magnet tips above plate base; depends on bead/plate geometry |
| `repetitions` | `tc_mod.execute_profile()` | — | `1`–`99` | Number of PCR thermal cycles |

## Best Practices

1. **Always simulate before running on hardware**: Use `opentrons_simulate protocol.py` to catch labware name errors, tip shortages, volume overflows, and slot conflicts without consuming consumables or robot time.
   ```bash
   opentrons_simulate my_pcr_setup.py
   # Output shows all commands; errors printed with line numbers
   ```

2. **Prefer compound operations over manual pick-up/aspirate/dispense/drop sequences**: `transfer()`, `distribute()`, and `consolidate()` handle tip management, air gaps, and blow-out automatically. Reserve low-level calls for operations not supported by compound methods.

3. **Count tips before running**: Calculate total tip consumptions (each `new_tip="always"` transfer costs one tip per well pair). If tips exceed rack capacity, add additional racks to `tip_racks=[]`.
   ```python
   n_transfers = len(source_wells)   # one tip per transfer
   tips_per_rack = 96
   racks_needed = -(-n_transfers // tips_per_rack)   # ceiling division
   print(f"Need {racks_needed} tip rack(s) for {n_transfers} transfers")
   ```

4. **Use `define_liquid()` and `load_liquid()` for setup validation**: Liquid tracking in the Opentrons App displays color-coded wells with volumes, making it easy to verify correct reagent placement before pressing Run.

5. **Distinguish OT-2 slots from Flex slots in protocol files**: OT-2 uses numeric strings (`"1"` through `"11"`) while Flex uses grid coordinates (`"A1"` through `"D3"`). Set `requirements = {"robotType": "Flex"}` or `"OT-2"` to catch slot mismatches during simulation.

6. **Adjust flow rates for difficult liquids**: Viscous solutions (≥20% glycerol, PEG, protein > 5 mg/mL) require lower aspirate rates (25-50 µL/s). Reduce dispense speed for foaming samples to avoid bubble formation.

7. **Use `protocol.pause()` for manual steps, not `protocol.delay()`**: `pause()` stops the robot and notifies the operator; the run resumes on demand. `delay()` is for timed waits (incubations, module equilibration) where no human action is needed.

## Common Recipes

### Recipe: Plate Replication (96-Well to 96-Well)

When to use: Duplicate an entire source plate into a destination plate with fresh tips per well.

```python
from opentrons import protocol_api

metadata = {"protocolName": "Plate Replication", "apiLevel": "2.19"}

def run(protocol: protocol_api.ProtocolContext):
    tips   = protocol.load_labware("opentrons_96_tiprack_300ul", "1")
    source = protocol.load_labware("corning_96_wellplate_360ul_flat", "2")
    dest   = protocol.load_labware("corning_96_wellplate_360ul_flat", "3")
    p300   = protocol.load_instrument("p300_single_gen2", "left", tip_racks=[tips])

    # Transfer all 96 wells in one call — pairwise source[i] → dest[i]
    p300.transfer(100, source.wells(), dest.wells(), new_tip="always")
    protocol.comment("Plate replicated: 96 wells transferred")
```

### Recipe: Multi-Channel Column-by-Column Fill

When to use: Fill a 96-well plate column by column with a single reagent using a multi-channel pipette and one tip.

```python
from opentrons import protocol_api

metadata = {"protocolName": "Multi-Channel Fill", "apiLevel": "2.19"}

def run(protocol: protocol_api.ProtocolContext):
    tips      = protocol.load_labware("opentrons_96_tiprack_300ul", "1")
    reservoir = protocol.load_labware("nest_12_reservoir_15ml", "2")
    plate     = protocol.load_labware("corning_96_wellplate_360ul_flat", "3")
    multi     = protocol.load_instrument("p300_multi_gen2", "left", tip_racks=[tips])

    # distribute() with multi-channel: one pick-up, 12 dispenses across all columns
    multi.distribute(
        100,
        reservoir["A1"],
        [plate.columns()[i][0] for i in range(12)],
        new_tip="once",
        disposal_volume=10,
    )
    protocol.comment("96-well plate filled: 100 µL per well, single tip")
```

### Recipe: Magnetic Bead Wash Loop

When to use: Automated bead-based cleanup (DNA extraction, IP assay) with repeating wash steps.

```python
from opentrons import protocol_api

metadata = {"protocolName": "Magnetic Bead Wash", "apiLevel": "2.19"}

def run(protocol: protocol_api.ProtocolContext):
    mag_mod   = protocol.load_module("magnetic module gen2", "4")
    bead_plate = mag_mod.load_labware("nest_96_wellplate_100ul_pcr_full_skirt")
    tips      = protocol.load_labware("opentrons_96_tiprack_300ul", "1")
    reservoir = protocol.load_labware("nest_12_reservoir_15ml", "2")
    waste     = protocol.load_labware("nest_12_reservoir_15ml", "5")
    p300      = protocol.load_instrument("p300_single_gen2", "left", tip_racks=[tips])

    # Engage magnets and remove supernatant
    mag_mod.engage(height_from_base=6)
    protocol.delay(seconds=120, msg="Beads pelleting on magnet")
    p300.transfer(90, bead_plate["A1"].bottom(z=0.5), waste["A1"], new_tip="once")

    # Wash loop (2 washes)
    for wash_num in range(2):
        mag_mod.disengage()
        protocol.comment(f"Wash {wash_num + 1} of 2")
        p300.transfer(100, reservoir["A1"], bead_plate["A1"],
                      mix_after=(5, 80), new_tip="always")
        mag_mod.engage(height_from_base=6)
        protocol.delay(seconds=90)
        p300.transfer(100, bead_plate["A1"].bottom(z=0.5), waste["A2"], new_tip="always")

    # Elute
    mag_mod.disengage()
    elution_plate = protocol.load_labware("corning_96_wellplate_360ul_flat", "3")
    p300.transfer(50, reservoir["A2"], bead_plate["A1"],
                  mix_after=(10, 40), new_tip="always")
    mag_mod.engage(height_from_base=6)
    protocol.delay(seconds=120)
    p300.transfer(45, bead_plate["A1"].bottom(z=0.5), elution_plate["A1"], new_tip="always")
    mag_mod.disengage()
    protocol.comment("Bead cleanup complete: eluate in elution_plate A1")
```

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| `LabwareNotFoundError: [labware name]` | Incorrect labware API name string | Look up exact names at [labware.opentrons.com](https://labware.opentrons.com/); names are case-sensitive (e.g., `"corning_96_wellplate_360ul_flat"`) |
| `OutOfTipsError` during run | Protocol needs more tips than racks provide | Add additional tip racks to `tip_racks=[]`; or call `pipette.reset_tipracks()` if racks have been reloaded |
| Volume exceeds pipette max capacity | Trying to aspirate/dispense more than the pipette can hold | Use `distribute()` which auto-splits large volumes; switch to `p1000_single_gen2` for large volumes (up to 1000 µL) |
| `DeckConflictError` | Labware placed in overlapping slots | Thermocycler auto-occupies slots 7-11; check `protocol.deck` output from simulation before running |
| Simulation passes but robot fails with `ModuleNotAttachedError` | Module not physically connected or wrong model string | Verify USB connection; use exact model strings: `"temperature module gen2"`, `"magnetic module gen2"`, `"thermocyclerModuleV2"`, `"heaterShakerModuleV1"` |
| Inaccurate volumes, especially near pipette minimum | Pipette at edge of calibrated range or viscous liquid | Use a pipette whose optimal range covers your volume; pre-wet tips with `mix()` before critical transfers; reduce flow rates |
| `TypeError` on `transfer()` with well list length mismatch | Source and destination lists different lengths | Ensure source and destination lists are same length for pairwise transfer, or use a single source with a destination list for 1-to-many |
| OT-2 protocol errors on Flex with slot names | Robot type mismatch (numeric vs grid slots) | Set `requirements = {"robotType": "Flex"}` or `"OT-2"` to enforce slot naming; Flex slots are strings like `"A1"`, OT-2 slots are `"1"`-`"11"` |

## Related Skills

- **pylabrobot** — hardware-agnostic Python API for Hamilton, Tecan, Beckman, and other vendors; use when protocols must run on non-Opentrons hardware
- **protocolsio-integration** — search and retrieve published wet-lab protocols from protocols.io to adapt into Opentrons Python protocols
- **benchling-integration** — connect protocol execution to Benchling ELN entries and sample registries

## References

- [Opentrons Protocol API v2 Documentation](https://docs.opentrons.com/v2/) — official API reference covering all context methods, labware, and modules
- [Opentrons Labware Library](https://labware.opentrons.com/) — searchable catalog of all supported labware with API name strings
- [Protocol API Tutorial](https://docs.opentrons.com/v2/tutorial.html) — step-by-step guide from metadata through hardware modules
- [Opentrons GitHub Repository](https://github.com/Opentrons/opentrons) — source code, protocol examples, and issue tracker
- [Opentrons Community Forum](https://discuss.opentrons.com/) — community Q&A for protocol debugging and hardware questions
