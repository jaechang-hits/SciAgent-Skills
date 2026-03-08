---
name: opentrons-integration
description: "Opentrons Protocol API v2 for OT-2 and Flex liquid handling robots. Write Python protocols for automated pipetting, serial dilutions, PCR setup, plate replication. Control hardware modules (thermocycler, heater-shaker, magnetic, temperature). For multi-vendor lab automation use pylabrobot."
license: Apache-2.0
---

# Opentrons Integration — Lab Automation

## Overview

Opentrons provides a Python-based Protocol API (v2) for programming OT-2 and Flex liquid handling robots. Protocols are structured Python files with metadata and a `run()` function that controls pipettes, labware, and hardware modules. All protocols can be simulated locally before running on physical hardware.

## When to Use

- Automating liquid handling workflows (pipetting, mixing, distributing)
- Writing PCR setup protocols with thermocycler control
- Performing serial dilutions across plates
- Replicating plates or reformatting between plate types
- Controlling hardware modules (temperature, magnetic, heater-shaker, thermocycler)
- Setting up multi-channel pipetting for 96-well plate operations
- Simulating protocols before running on the robot
- For **multi-vendor automation** (Hamilton, Beckman, etc.), use pylabrobot instead
- For **flow cytometry analysis** of automated experiment results, use flowio/flowkit

## Prerequisites

```bash
pip install opentrons
# Simulate protocols locally (no robot needed)
opentrons_simulate my_protocol.py
```

**Protocol API Version**: Always use the latest stable API level (currently `2.19`). Set `apiLevel` in protocol metadata. Protocols are forward-compatible within major versions.

**Robot Types**: Flex (newer, larger deck, 96-channel pipette) vs OT-2 (smaller, 8-channel max). Key differences: deck slot naming (Flex: A1-D3, OT-2: 1-11), available pipettes, and module support.

## Quick Start

```python
from opentrons import protocol_api

metadata = {"protocolName": "Quick Transfer", "apiLevel": "2.19"}

def run(protocol: protocol_api.ProtocolContext):
    tips = protocol.load_labware("opentrons_96_tiprack_300ul", "1")
    source = protocol.load_labware("nest_12_reservoir_15ml", "2")
    plate = protocol.load_labware("corning_96_wellplate_360ul_flat", "3")
    pipette = protocol.load_instrument("p300_single_gen2", "left", tip_racks=[tips])

    pipette.distribute(50, source["A1"], plate.wells()[:12], new_tip="once")
```

## Core API

### 1. Protocol Structure

Every Opentrons protocol follows a required structure: metadata dict + `run()` function.

```python
from opentrons import protocol_api

metadata = {
    "protocolName": "My Protocol",
    "author": "Name <email>",
    "description": "Protocol description",
    "apiLevel": "2.19",
}

# Optional: specify robot type
requirements = {"robotType": "Flex", "apiLevel": "2.19"}

def run(protocol: protocol_api.ProtocolContext):
    # All protocol logic goes here
    protocol.comment("Protocol started")
```

### 2. Labware and Deck Layout

Load labware (plates, reservoirs, tip racks) onto deck slots and optionally onto adapters.

```python
def run(protocol: protocol_api.ProtocolContext):
    # Tip racks
    tips_300 = protocol.load_labware("opentrons_96_tiprack_300ul", "1")
    tips_20 = protocol.load_labware("opentrons_96_tiprack_20ul", "4")

    # Plates and reservoirs
    plate = protocol.load_labware("corning_96_wellplate_360ul_flat", "2", label="Sample Plate")
    reservoir = protocol.load_labware("nest_12_reservoir_15ml", "3")

    # Labware on adapter (Flex)
    adapter = protocol.load_adapter("opentrons_flex_96_tiprack_adapter", "B1")
    tips_on_adapter = adapter.load_labware("opentrons_flex_96_tiprack_200ul")

    # Pipettes
    p300 = protocol.load_instrument("p300_single_gen2", "left", tip_racks=[tips_300])
    p20 = protocol.load_instrument("p20_single_gen2", "right", tip_racks=[tips_20])
```

**Common pipette names**:
- OT-2: `p20_single_gen2`, `p300_single_gen2`, `p1000_single_gen2`, `p20_multi_gen2`, `p300_multi_gen2`
- Flex: `p50_single_flex`, `p1000_single_flex`, `p50_multi_flex`, `p1000_multi_flex`

### 3. Pipette Operations

Basic, compound, and advanced liquid handling operations.

```python
def run(protocol: protocol_api.ProtocolContext):
    # ... (labware loaded above)

    # === Basic operations ===
    p300.pick_up_tip()
    p300.aspirate(100, source["A1"])        # Draw 100 µL
    p300.dispense(100, dest["B1"])          # Expel 100 µL
    p300.drop_tip()

    # === Compound operations (auto tip management) ===
    # Transfer: single source → single dest
    p300.transfer(100, source["A1"], dest["B1"], new_tip="always")

    # Distribute: one source → many dests
    p300.distribute(50, reservoir["A1"],
                    [plate["A1"], plate["A2"], plate["A3"]], new_tip="once")

    # Consolidate: many sources → one dest
    p300.consolidate(50, [plate["A1"], plate["A2"]], reservoir["A1"])

    # === Advanced techniques ===
    p300.pick_up_tip()
    p300.mix(repetitions=3, volume=50, location=plate["A1"])  # Mix in place
    p300.aspirate(100, source["A1"])
    p300.air_gap(20)                        # Prevent dripping
    p300.dispense(120, dest["A1"])
    p300.blow_out(dest["A1"].top())          # Expel residual
    p300.touch_tip(plate["A1"])              # Remove exterior drops
    p300.drop_tip()
```

### 4. Well Access and Locations

Navigate wells by name, index, row, or column. Control vertical position within wells.

```python
def run(protocol: protocol_api.ProtocolContext):
    plate = protocol.load_labware("corning_96_wellplate_360ul_flat", "1")

    # Access by name or index
    well = plate["A1"]
    first = plate.wells()[0]           # Same as plate["A1"]

    # Iterate rows/columns
    row_a = plate.rows()[0]            # [A1, A2, ..., A12]
    col_1 = plate.columns()[0]         # [A1, B1, ..., H1]

    # Vertical positions
    pipette.aspirate(100, well.top())          # 1mm below top
    pipette.aspirate(100, well.bottom(z=2))    # 2mm above bottom
    pipette.aspirate(100, well.center())       # Center of well
    pipette.dispense(100, well.top(z=5))       # 5mm above top
```

### 5. Hardware Modules

Control temperature, magnetic, heater-shaker, and thermocycler modules.

```python
def run(protocol: protocol_api.ProtocolContext):
    # Temperature module
    temp_mod = protocol.load_module("temperature module gen2", "3")
    temp_plate = temp_mod.load_labware("corning_96_wellplate_360ul_flat")
    temp_mod.set_temperature(celsius=4)
    # temp_mod.temperature → current temp; temp_mod.deactivate()

    # Magnetic module
    mag_mod = protocol.load_module("magnetic module gen2", "6")
    mag_plate = mag_mod.load_labware("nest_96_wellplate_100ul_pcr_full_skirt")
    mag_mod.engage(height_from_base=10)    # Raise magnets (mm)
    mag_mod.disengage()

    # Heater-Shaker module
    hs_mod = protocol.load_module("heaterShakerModuleV1", "1")
    hs_plate = hs_mod.load_labware("corning_96_wellplate_360ul_flat")
    hs_mod.close_labware_latch()
    hs_mod.set_target_temperature(celsius=37)
    hs_mod.wait_for_temperature()
    hs_mod.set_and_wait_for_shake_speed(rpm=500)
    hs_mod.deactivate_shaker()
    hs_mod.deactivate_heater()
    hs_mod.open_labware_latch()

    # Thermocycler (auto-assigned to slots)
    tc_mod = protocol.load_module("thermocyclerModuleV2")
    tc_plate = tc_mod.load_labware("nest_96_wellplate_100ul_pcr_full_skirt")
    tc_mod.open_lid()
    tc_mod.close_lid()
    tc_mod.set_lid_temperature(celsius=105)
    tc_mod.set_block_temperature(95, hold_time_seconds=180)

    profile = [
        {"temperature": 95, "hold_time_seconds": 15},
        {"temperature": 60, "hold_time_seconds": 30},
        {"temperature": 72, "hold_time_seconds": 60},
    ]
    tc_mod.execute_profile(steps=profile, repetitions=30, block_max_volume=50)
    tc_mod.deactivate_lid()
    tc_mod.deactivate_block()
```

### 6. Protocol Control and Utilities

Pause, delay, comment, liquid tracking, and simulation detection.

```python
def run(protocol: protocol_api.ProtocolContext):
    # Execution control
    protocol.pause(msg="Replace tip box and resume")
    protocol.delay(seconds=60)
    protocol.delay(minutes=5)
    protocol.comment("Starting serial dilution")
    protocol.home()

    # Liquid tracking (visual in Opentrons App)
    water = protocol.define_liquid(name="Water", description="Ultrapure water",
                                    display_color="#0000FF")
    reservoir["A1"].load_liquid(liquid=water, volume=50000)
    plate["B1"].load_empty()

    # Check simulation vs real run
    if protocol.is_simulating():
        protocol.comment("Simulation mode")

    # Flow rate control (µL/s)
    pipette.flow_rate.aspirate = 150
    pipette.flow_rate.dispense = 300
    pipette.flow_rate.blow_out = 400
```

## Key Concepts

### Protocol File Structure

All Opentrons protocols are Python files with this required structure:

```
┌─ metadata dict ──────────────── protocolName, apiLevel, author
├─ requirements dict (optional) ── robotType
└─ def run(protocol): ─────────── All robot commands
```

The `run()` function receives a `ProtocolContext` object — all labware loading, pipette operations, and module control happen through this single entry point. Protocols cannot import arbitrary packages for execution on the robot.

### OT-2 vs Flex Differences

| Feature | OT-2 | Flex |
|---------|------|------|
| Deck slots | 1-11 (numeric) | A1-D3 (grid) |
| Pipettes | Gen2 (`p20`, `p300`, `p1000`) | Flex (`p50`, `p1000`, 96-channel) |
| Max channels | 8-channel multi | 96-channel |
| Modules | Gen1/Gen2 | V2 modules |
| Adapters | Not supported | Supported (tiprack, flat) |

### Multi-Channel Pipette Behavior

When using multi-channel pipettes, referencing a single well accesses the entire column:

```python
multi = protocol.load_instrument("p300_multi_gen2", "left", tip_racks=[tips])
# This transfers from ALL wells in column 1 of source to column 1 of dest
multi.transfer(100, source["A1"], dest["A1"])
```

## Common Workflows

### Workflow: Serial Dilution

```python
from opentrons import protocol_api

metadata = {"protocolName": "Serial Dilution", "apiLevel": "2.19"}

def run(protocol: protocol_api.ProtocolContext):
    tips = protocol.load_labware("opentrons_96_tiprack_300ul", "1")
    reservoir = protocol.load_labware("nest_12_reservoir_15ml", "2")
    plate = protocol.load_labware("corning_96_wellplate_360ul_flat", "3")
    p300 = protocol.load_instrument("p300_single_gen2", "left", tip_racks=[tips])

    # Add diluent to columns 2-12
    p300.transfer(100, reservoir["A1"], plate.rows()[0][1:])

    # Serial dilution across row A
    p300.transfer(
        100,
        plate.rows()[0][:11],
        plate.rows()[0][1:],
        mix_after=(3, 50),
        new_tip="always",
    )
```

### Workflow: PCR Setup with Thermocycler

```python
from opentrons import protocol_api

metadata = {"protocolName": "PCR Setup", "apiLevel": "2.19"}

def run(protocol: protocol_api.ProtocolContext):
    tc_mod = protocol.load_module("thermocyclerModuleV2")
    tc_plate = tc_mod.load_labware("nest_96_wellplate_100ul_pcr_full_skirt")
    tips = protocol.load_labware("opentrons_96_tiprack_300ul", "1")
    reagents = protocol.load_labware("opentrons_24_tuberack_nest_1.5ml_snapcap", "2")
    p300 = protocol.load_instrument("p300_single_gen2", "left", tip_racks=[tips])

    tc_mod.open_lid()
    # Distribute master mix
    p300.distribute(20, reagents["A1"], tc_plate.wells()[:8], new_tip="once")
    # Add samples
    for i in range(8):
        p300.transfer(5, reagents.wells()[i + 1], tc_plate.wells()[i], new_tip="always")

    # Run PCR
    tc_mod.close_lid()
    tc_mod.set_lid_temperature(105)
    tc_mod.set_block_temperature(95, hold_time_seconds=180)  # Initial denaturation
    profile = [
        {"temperature": 95, "hold_time_seconds": 15},
        {"temperature": 60, "hold_time_seconds": 30},
        {"temperature": 72, "hold_time_seconds": 30},
    ]
    tc_mod.execute_profile(steps=profile, repetitions=35, block_max_volume=25)
    tc_mod.set_block_temperature(72, hold_time_minutes=5)  # Final extension
    tc_mod.set_block_temperature(4)  # Hold
    tc_mod.deactivate_lid()
    tc_mod.open_lid()
```

### Workflow: Magnetic Bead Cleanup

1. Load magnetic module with deep-well plate, reservoir with wash buffers
2. Engage magnets → aspirate supernatant → dispense to waste
3. Disengage magnets → add wash buffer → mix → engage → remove wash (repeat 2x)
4. Disengage → add elution buffer → mix → engage → transfer eluate to clean plate

## Key Parameters

| Parameter | Function | Default | Range | Effect |
|-----------|----------|---------|-------|--------|
| `volume` | `aspirate`, `dispense`, `transfer` | — | 1–1000 µL | Liquid volume |
| `new_tip` | `transfer`, `distribute`, `consolidate` | `"always"` | `"always"`, `"once"`, `"never"` | Tip change strategy |
| `mix_after` | `transfer` | `None` | `(reps, vol)` tuple | Post-dispense mixing |
| `mix_before` | `transfer` | `None` | `(reps, vol)` tuple | Pre-aspirate mixing |
| `blow_out` | `transfer` | `False` | `True`/`False` | Blow out after dispense |
| `touch_tip` | `transfer` | `False` | `True`/`False` | Touch tip after dispense |
| `air_gap` | `transfer` | `0` | 0–pipette max µL | Air gap volume |
| `flow_rate.aspirate` | pipette property | varies | 1–1000 µL/s | Aspirate speed |
| `flow_rate.dispense` | pipette property | varies | 1–1000 µL/s | Dispense speed |
| `height_from_base` | `mag_module.engage` | — | 0–20 mm | Magnet engagement height |

## Best Practices

1. **Always simulate first**: Run `opentrons_simulate my_protocol.py` before uploading to the robot. Catches labware conflicts, volume errors, and tip shortages without wasting consumables.

2. **Use compound operations over basic**: Prefer `transfer()`, `distribute()`, `consolidate()` over manual `pick_up_tip/aspirate/dispense/drop_tip` sequences — they handle tip management automatically.

3. **Anti-pattern — ignoring tip count**: A protocol that runs out of tips will error mid-run. Count total tip uses vs rack capacity before running.

4. **Track liquids for setup validation**: Use `define_liquid()` and `load_liquid()` to enable volume tracking in the Opentrons App.

5. **Anti-pattern — hardcoding deck slots across robot types**: Flex uses grid coordinates (A1-D3), OT-2 uses numbers (1-11). Write separate metadata or use `requirements["robotType"]` to ensure compatibility.

6. **Control flow rates for difficult liquids**: Reduce aspirate speed for viscous solutions (glycerol, PEG), increase for water-like liquids.

7. **Use pauses for manual intervention**: `protocol.pause(msg=...)` is safer than `protocol.delay()` when you need user action (e.g., adding reagent, sealing plate).

## Common Recipes

### Recipe: Plate Replication

```python
from opentrons import protocol_api

metadata = {"protocolName": "Plate Replication", "apiLevel": "2.19"}

def run(protocol: protocol_api.ProtocolContext):
    tips = protocol.load_labware("opentrons_96_tiprack_300ul", "1")
    source = protocol.load_labware("corning_96_wellplate_360ul_flat", "2")
    dest = protocol.load_labware("corning_96_wellplate_360ul_flat", "3")
    p300 = protocol.load_instrument("p300_single_gen2", "left", tip_racks=[tips])
    p300.transfer(100, source.wells(), dest.wells(), new_tip="always")
```

### Recipe: Reagent Distribution with Multi-Channel

```python
from opentrons import protocol_api

metadata = {"protocolName": "Multi-Channel Distribution", "apiLevel": "2.19"}

def run(protocol: protocol_api.ProtocolContext):
    tips = protocol.load_labware("opentrons_96_tiprack_300ul", "1")
    reservoir = protocol.load_labware("nest_12_reservoir_15ml", "2")
    plate = protocol.load_labware("corning_96_wellplate_360ul_flat", "3")
    multi = protocol.load_instrument("p300_multi_gen2", "left", tip_racks=[tips])

    # Fill all 96 wells: 12 columns × 8 rows via multi-channel
    multi.transfer(100, reservoir["A1"], plate.rows()[0], new_tip="once")
```

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| `OutOfTipsError` | Protocol needs more tips than available | Add multiple tip racks to `tip_racks=` list, or reload tips with `pipette.reset_tipracks()` |
| Labware collision on deck | Two items assigned to overlapping slots | Check deck map — thermocycler auto-occupies multiple slots; use `protocol.deck` to inspect |
| Volume exceeds pipette capacity | Attempting to aspirate/dispense > max volume | Use `distribute()` which auto-splits volumes, or switch to a larger pipette |
| `LabwareNotFoundError` | Wrong labware API name | Check names at labware.opentrons.com; use exact API name strings |
| Protocol works in simulation but fails on robot | Hardware-specific timing issue | Add `protocol.delay()` between temperature changes; increase magnet engage time |
| Inaccurate volumes | Pipette calibration or air bubbles | Recalibrate pipette; pre-wet tips with `mix()`; adjust flow rates for viscous liquids |
| `ModuleNotAttachedError` | Module not connected or wrong model string | Verify module serial connection; use exact model strings (`"temperature module gen2"`) |

## Related Skills

- **pylabrobot** — multi-vendor lab automation (Hamilton, Beckman, Tecan) for cross-platform protocols
- **biopython-molecular-biology** — sequence design and primer tools for PCR protocol inputs

## References

- [Opentrons Protocol API v2 docs](https://docs.opentrons.com/v2/) — official API reference
- [Opentrons Labware Library](https://labware.opentrons.com/) — searchable labware definitions
- [Opentrons Python Protocol Tutorial](https://docs.opentrons.com/v2/tutorial.html) — step-by-step getting started guide
