---
name: "pylabrobot"
description: "PyLabRobot is a hardware-agnostic Python library for liquid handling robots. Use it to write portable automation scripts that run on Hamilton STAR, Tecan Freedom EVO, Opentrons OT-2, or a simulation backend — without vendor lock-in. Ideal for protocol automation, method development, plate reformatting, serial dilutions, and integrating liquid handlers into larger Python-based lab workflows."
license: "MIT"
---

# pylabrobot

## Overview

PyLabRobot is an open-source Python library that abstracts liquid handling robot hardware behind a unified API. Write a protocol once and run it on any supported robot — Hamilton STAR, Tecan Freedom EVO, Opentrons OT-2, or a simulated backend — without changing the protocol code. PyLabRobot handles deck layout, resource management, and aspirate/dispense operations through a clean, async-first interface.

## When to Use

- **Writing portable liquid handling protocols**: You want a single Python script that works across Hamilton, Tecan, Opentrons, and a simulator without code changes.
- **Developing and testing protocols before robot time**: Use the simulation backend to validate logic, volumes, and deck layouts without occupying physical hardware.
- **Automating plate reformatting and cherry-picking**: Transfer specific wells between plates based on upstream data (e.g., hit compounds from a screen).
- **Building serial dilution curves**: Systematically aspirate and dispense across a plate with precise volume steps.
- **Integrating liquid handling into Python data pipelines**: Trigger robot actions from analysis code, LIMS queries, or machine learning models.
- **Rapid method development**: Iterate quickly in Python rather than in vendor-specific scripting environments.
- For Opentrons-specific features (module temperature control via the Opentrons app), the `opentrons` SDK may be more appropriate.

## Prerequisites

- **Python packages**: `pylabrobot`
- **Optional backends**: `pylabrobot[hamilton]` for Hamilton STAR, `pylabrobot[opentrons]` for OT-2
- **Data requirements**: None — deck resources are defined in Python
- **Environment**: Python 3.9+; physical robot drivers installed separately per vendor docs

```bash
pip install pylabrobot
pip install "pylabrobot[hamilton]"   # add Hamilton USB driver
pip install "pylabrobot[opentrons]"  # add Opentrons REST driver
```

## Quick Start

```python
import asyncio
from pylabrobot.liquid_handling import LiquidHandler
from pylabrobot.liquid_handling.backends import SimulatorBackend
from pylabrobot.resources import Deck, Cos_96_Rd, HTF_L

async def main():
    backend = SimulatorBackend(open_browser=False)
    lh = LiquidHandler(backend=backend, deck=Deck())
    await lh.setup()

    plate = Cos_96_Rd(name="plate")
    tips  = HTF_L(name="tips")
    lh.deck.assign_child_resource(plate, rails=2)
    lh.deck.assign_child_resource(tips,  rails=5)

    await lh.pick_up_tips(tips["A1"])
    await lh.aspirate(plate["A1"], vols=50)
    await lh.dispense(plate["B1"], vols=50)
    await lh.drop_tips(tips["A1"])
    await lh.stop()
    print("Transfer complete: 50 uL from A1 -> B1")

asyncio.run(main())
```

## Core API

### Module 1: LiquidHandler — Setup and Teardown

The `LiquidHandler` class is the central controller. It wraps a backend and a `Deck`.

```python
import asyncio
from pylabrobot.liquid_handling import LiquidHandler
from pylabrobot.liquid_handling.backends import SimulatorBackend
from pylabrobot.resources import Deck

async def main():
    backend = SimulatorBackend(open_browser=False)
    lh = LiquidHandler(backend=backend, deck=Deck())
    await lh.setup()      # connect to hardware / start simulator
    print("LiquidHandler ready:", lh)
    await lh.stop()       # disconnect cleanly

asyncio.run(main())
```

```python
# Connecting to a real Hamilton STAR
from pylabrobot.liquid_handling.backends.hamilton import STAR

async def main():
    backend = STAR()
    lh = LiquidHandler(backend=backend, deck=Deck())
    await lh.setup()
    # lh is now connected to physical hardware
    await lh.stop()
```

### Module 2: Deck and Resource Assignment

Resources (plates, tip racks, reservoirs) are placed on the deck by rail position.

```python
from pylabrobot.resources import (
    Deck,
    Cos_96_Rd,                  # Corning 96-well round-bottom plate
    Cos_384_Sq,                 # Corning 384-well plate
    HTF_L,                      # Hamilton tip rack (filtered, large)
    Trough_1_Row_1_Col_4,       # 4-channel reservoir
)

deck = Deck()
plate_96  = Cos_96_Rd(name="sample_plate")
plate_384 = Cos_384_Sq(name="assay_plate")
tips      = HTF_L(name="tip_rack")
reservoir = Trough_1_Row_1_Col_4(name="buffer")

deck.assign_child_resource(plate_96,  rails=1)
deck.assign_child_resource(plate_384, rails=4)
deck.assign_child_resource(tips,      rails=8)
deck.assign_child_resource(reservoir, rails=11)

print("Deck resources:", [r.name for r in deck.children])
```

### Module 3: Tip Operations

Pick up and drop tips before and after liquid operations.

```python
# Pick up tips from the first column of the tip rack
await lh.pick_up_tips(tips["A1:H1"])   # all 8 tips in column 1

# After liquid operations, drop tips back
await lh.drop_tips(tips["A1:H1"])

# Single tip
await lh.pick_up_tips(tips["A1"])
await lh.drop_tips(tips["A1"])
print("Tip operations complete")
```

### Module 4: Aspirate Operations

Aspirate liquid from wells. Accepts single wells, ranges, or lists.

```python
# Aspirate 100 uL from a single well
await lh.aspirate(plate["A1"], vols=100)

# Aspirate different volumes from multiple wells simultaneously
await lh.aspirate(
    plate["A1:A4"],
    vols=[50, 75, 100, 125],
)
print("Aspiration complete")
```

```python
from pylabrobot.resources import Coordinate

# Aspirate with flow rate and liquid height control
await lh.aspirate(
    plate["A1"],
    vols=50,
    flow_rates=100,                    # uL/s
    offsets=Coordinate(0, 0, 1),       # 1 mm above well bottom
)
```

### Module 5: Dispense Operations

Dispense liquid into target wells.

```python
# Dispense 100 uL into a single well
await lh.dispense(plate["B1"], vols=100)

# Multi-well dispense with different volumes
await lh.dispense(
    plate["B1:B4"],
    vols=[50, 75, 100, 125],
)
print("Dispense complete")
```

### Module 6: Transfer — High-Level Convenience

`transfer` combines aspirate and dispense for simple source-to-destination moves.

```python
# Transfer 50 uL from A1 -> B1
await lh.transfer(plate["A1"], plate["B1"], transfer_volume=50)

# Multi-well pairwise transfer
sources      = plate["A1:A8"]
destinations = plate["B1:B8"]
await lh.transfer(sources, destinations, transfer_volume=75)
print("Transfer complete")
```

### Module 7: Simulation Backend

The `SimulatorBackend` runs a browser-based visualizer for protocol debugging.

```python
from pylabrobot.liquid_handling.backends import SimulatorBackend

# With visual browser (default — opens http://localhost:2121)
backend = SimulatorBackend(open_browser=True)

# Headless simulation (CI/testing)
backend = SimulatorBackend(open_browser=False)

# After setup(), liquid movements are visualized in real time
await lh.setup()
# Check browser for visual confirmation before running on real hardware
print("Simulator running at http://localhost:2121")
```

## Key Concepts

### Async-First Design

All robot operations (`setup`, `aspirate`, `dispense`, `transfer`) are Python `async` coroutines. Run them inside an `async def` function using `asyncio.run()` or Jupyter's top-level `await` syntax.

```python
import asyncio

async def run_protocol(lh, plate, tips):
    await lh.pick_up_tips(tips["A1"])
    await lh.aspirate(plate["A1"], vols=50)
    await lh.dispense(plate["B1"], vols=50)
    await lh.drop_tips(tips["A1"])
    print("Protocol complete")

asyncio.run(run_protocol(lh, plate, tips))
```

### Well Addressing

Wells are addressed by alphanumeric position (`"A1"`) or slice notation (`"A1:H1"` for a column, `"A1:A12"` for a row).

```python
well    = plate["A1"]             # single well
col1    = plate["A1:H1"]          # 8 wells in column 1
row_a   = plate["A1:A12"]         # 12 wells in row A
print(f"Single: {well.name}")
print(f"Column: {len(col1)} wells")
print(f"Row:    {len(row_a)} wells")
```

## Common Workflows

### Workflow 1: 96-Well Serial Dilution

**Goal**: Perform a 2-fold serial dilution across a 96-well plate.

```python
import asyncio
from pylabrobot.liquid_handling import LiquidHandler
from pylabrobot.liquid_handling.backends import SimulatorBackend
from pylabrobot.resources import Deck, Cos_96_Rd, HTF_L, Trough_1_Row_1_Col_4

async def serial_dilution():
    backend = SimulatorBackend(open_browser=False)
    lh = LiquidHandler(backend=backend, deck=Deck())
    await lh.setup()

    plate   = Cos_96_Rd(name="plate")
    tips    = HTF_L(name="tips")
    diluent = Trough_1_Row_1_Col_4(name="diluent")
    lh.deck.assign_child_resource(plate,   rails=1)
    lh.deck.assign_child_resource(tips,    rails=5)
    lh.deck.assign_child_resource(diluent, rails=9)

    # Add 100 uL diluent to columns 2-12
    for col in range(2, 13):
        col_label = f"A{col}:H{col}"
        await lh.pick_up_tips(tips[f"A{col}:H{col}"])
        await lh.aspirate(diluent["A1:H1"], vols=100)
        await lh.dispense(plate[col_label], vols=100)
        await lh.drop_tips(tips[f"A{col}:H{col}"])

    # Serial transfer: col 1 -> 2 -> ... -> 11
    for col in range(1, 12):
        src = f"A{col}:H{col}"
        dst = f"A{col+1}:H{col+1}"
        await lh.pick_up_tips(tips[f"A{col}:H{col}"])
        await lh.aspirate(plate[src], vols=100)
        await lh.dispense(plate[dst], vols=100)
        await lh.drop_tips(tips[f"A{col}:H{col}"])

    print("Serial dilution complete: 12 columns, 2-fold steps")
    await lh.stop()

asyncio.run(serial_dilution())
```

### Workflow 2: Cherry-Picking from a Hit List

**Goal**: Transfer compounds from specified source wells to a destination plate based on a CSV hit list.

```python
import asyncio
import pandas as pd
from pylabrobot.liquid_handling import LiquidHandler
from pylabrobot.liquid_handling.backends import SimulatorBackend
from pylabrobot.resources import Deck, Cos_96_Rd, HTF_L

async def cherry_pick(hit_list_csv: str, volume: float = 50.0):
    # CSV must have columns: source_well, dest_well
    hits = pd.read_csv(hit_list_csv)
    print(f"Cherry-picking {len(hits)} hits at {volume} uL each")

    backend = SimulatorBackend(open_browser=False)
    lh = LiquidHandler(backend=backend, deck=Deck())
    await lh.setup()

    src  = Cos_96_Rd(name="source")
    dst  = Cos_96_Rd(name="destination")
    tips = HTF_L(name="tips")
    lh.deck.assign_child_resource(src,  rails=1)
    lh.deck.assign_child_resource(dst,  rails=4)
    lh.deck.assign_child_resource(tips, rails=8)

    # Get all well names from tip rack
    tip_wells = [w.name for w in tips.wells]
    for i, row in hits.iterrows():
        await lh.pick_up_tips(tips[tip_wells[i]])
        await lh.transfer(src[row["source_well"]], dst[row["dest_well"]],
                          transfer_volume=volume)
        await lh.drop_tips(tips[tip_wells[i]])

    print(f"Cherry-pick complete: {len(hits)} transfers done")
    await lh.stop()

# asyncio.run(cherry_pick("hits.csv", volume=50))
```

## Key Parameters

| Parameter | Module | Default | Range / Options | Effect |
|-----------|--------|---------|-----------------|--------|
| `vols` | aspirate / dispense | required | `0` – robot max (µL) | Volume to aspirate or dispense per well |
| `flow_rates` | aspirate / dispense | backend default | `10` – `1000` µL/s | Speed of liquid movement |
| `blow_out_air_volume` | dispense | `0` | `0` – `30` µL | Air volume blown after dispense to empty tip |
| `offsets` | aspirate / dispense | `Coordinate(0,0,0)` | Any `Coordinate` | Positional offset from well center (x, y, z mm) |
| `open_browser` | SimulatorBackend | `True` | `True`, `False` | Open browser-based visual simulator on setup |
| `rails` | deck assignment | required | `1` – max deck rails | Physical slot on the deck for a resource |
| `transfer_volume` | transfer | required | `0` – robot max (µL) | Volume for high-level aspirate+dispense transfer |

## Best Practices

1. **Always test with the simulator first**: Run your full protocol with `SimulatorBackend(open_browser=True)` before connecting to physical hardware. The browser visualizer shows deck layout and liquid movements in real time.

2. **Use fresh tips for each transfer when contamination matters**: Reusing tips in cherry-picking workflows risks cross-contamination. Track tip consumption against tip rack capacity programmatically.

3. **Wrap protocols in try/finally for cleanup**: If an exception occurs mid-protocol, always call `await lh.stop()` to release hardware connections.
   ```python
   try:
       await run_my_protocol(lh)
   finally:
       await lh.stop()
   ```

4. **Define resources once at the top of your script**: Create resource objects and assign them to the deck once. Reassigning the same resource mid-run can desynchronize the robot's internal state tracking.

5. **Pre-calculate volume and tip requirements**: For high-throughput runs, compute total volume and tip count needed before starting, and assert that resources are sufficient.

## Common Recipes

### Recipe: Dispense with Post-Dispense Mixing

When to use: Reagent addition to cell culture wells requiring homogeneous mixing.

```python
async def dispense_and_mix(lh, src, dst, tips, volume=50, mix_vol=40, mix_reps=3):
    await lh.pick_up_tips(tips["A1"])
    await lh.aspirate(src["A1"], vols=volume)
    await lh.dispense(dst["A1"], vols=volume)
    for _ in range(mix_reps):
        await lh.aspirate(dst["A1"], vols=mix_vol)
        await lh.dispense(dst["A1"], vols=mix_vol)
    await lh.drop_tips(tips["A1"])
    print(f"Dispensed {volume} uL and mixed {mix_reps}x")
```

### Recipe: Full-Plate Stamp

When to use: Replicate an entire 96-well plate to a second plate.

```python
async def stamp_plate(lh, src_plate, dst_plate, tips, volume=100):
    for col in range(1, 13):
        col_label = f"A{col}:H{col}"
        await lh.pick_up_tips(tips[col_label])
        await lh.aspirate(src_plate[col_label], vols=volume)
        await lh.dispense(dst_plate[col_label], vols=volume)
        await lh.drop_tips(tips[col_label])
    print(f"Full plate stamped: {volume} uL per well, 12 columns")
```

## Expected Outputs

- Robot executes liquid handling operations as scripted (physical or simulated)
- Simulator at `http://localhost:2121` shows animated deck with per-well volume tracking
- No file outputs by default; integrate `pandas` / CSV logging in wrapper code as needed

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| `RuntimeError: No backend connected` | `lh.setup()` not awaited before operations | Ensure `await lh.setup()` completes before any liquid handling call |
| `ResourceNotFoundError` | Resource name not assigned to deck | Call `deck.assign_child_resource(resource, rails=N)` before referencing wells |
| `asyncio.InvalidStateError` | Coroutine called outside async context | Wrap top-level calls in `async def main()` and use `asyncio.run(main())` |
| Well address `KeyError` | Incorrect well label format | Use uppercase letter + integer: `"A1"`, `"H12"`, not `"a1"` or `"A01"` |
| `VolumeError`: exceeds tip capacity | Requested volume larger than tip max | Use appropriate tip type; HTF_L holds up to 1000 µL |
| Simulator shows no movement | `open_browser=False` with no viewer | Set `open_browser=True` or open `http://localhost:2121` manually |
| `ImportError: pylabrobot.hamilton` | Backend extras not installed | `pip install "pylabrobot[hamilton]"` |

## References

- [PyLabRobot Documentation](https://docs.pylabrobot.org/) — official docs covering all backends and resources
- [PyLabRobot GitHub](https://github.com/PyLabRobot/pylabrobot) — source code, examples, and issue tracker
- [Azeloglu & Bhatt (2023), Cell Device — PyLabRobot paper](https://www.cell.com/device/fulltext/S2666-9986(23)00100-0) — original publication
- [PyPI: pylabrobot](https://pypi.org/project/pylabrobot/) — installation and version history
