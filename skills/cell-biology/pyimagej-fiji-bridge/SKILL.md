---
name: "pyimagej-fiji-bridge"
description: "Python bridge to ImageJ2/Fiji for macros, plugins (Bio-Formats, TrackMate, Analyze Particles), NumPy↔ImagePlus/ImgLib2 exchange, and ImageJ Ops. Automates Fiji headlessly from Python. Use scikit-image for pure Python without Fiji plugins; napari for visualization."
license: "Apache-2.0"
---

# PyImageJ — Python Bridge to ImageJ/Fiji

## Overview

PyImageJ provides a Python interface to ImageJ2 and Fiji through PyJNIus and scyjava, embedding a full Java Virtual Machine inside a Python process. It enables bidirectional data exchange between NumPy arrays and ImageJ's ImagePlus/ImgLib2 data structures, so you can preprocess images in Python, pass them into Fiji plugins (Bio-Formats, TrackMate, Analyze Particles, Weka segmentation), and return results back to pandas DataFrames. The library supports headless operation for scripting and batch processing, as well as GUI mode for interactive Fiji sessions.

## When to Use

- Running Fiji-specific plugins from Python: Bio-Formats multi-format I/O, TrackMate particle tracking, CLIJ2 GPU processing, or community Fiji update site plugins
- Automating ImageJ macro pipelines headlessly without opening the Fiji GUI, e.g., batch processing an entire experiment overnight
- Applying the ImageJ Ops framework (150+ image processing operations) with the full ImageJ type system
- Converting between NumPy arrays (SciPy ecosystem) and ImageJ hyperstacks (TZCYX channel order) for round-trip processing
- Parsing ImageJ Results tables and ROI Manager measurements into pandas DataFrames for downstream statistical analysis
- Executing existing `.ijm` macro files as part of a Python workflow without rewriting them
- Use `scikit-image` instead when you need pure Python processing without Fiji plugins — scikit-image is faster to install and avoids JVM overhead
- Use `napari` instead for interactive multi-dimensional image visualization and annotation; PyImageJ does not replace a viewer

## Prerequisites

- **Python packages**: `pyimagej`, `scyjava`, `numpy`, `pandas`
- **Java**: Java 8 or Java 11 (Java 17 is not supported); use conda for reliable Java management
- **Fiji/ImageJ2**: Downloaded automatically on first init, or specify a local Fiji installation path
- **Environment**: conda environment strongly recommended; pip-only installs often have JVM path issues

```bash
# Recommended: conda installation
conda create -n pyimagej -c conda-forge pyimagej openjdk=11
conda activate pyimagej

# Install additional dependencies
pip install pandas tifffile

# Verify
python -c "import imagej; ij = imagej.init('sc.fiji:fiji', mode='headless'); print(ij.getVersion())"
```

## Quick Start

```python
import imagej
import numpy as np

# Initialize Fiji in headless mode (downloads on first run, ~500 MB)
ij = imagej.init("sc.fiji:fiji", mode="headless")
print(f"ImageJ version: {ij.getVersion()}")

# Create a test image, process with Gaussian blur via Ops, convert back
arr = np.random.randint(0, 1000, (256, 256), dtype=np.uint16)
imp = ij.py.to_imageplus(arr)
blurred = ij.op().filter().gauss(imp.getProcessor(), 2.0)
result = ij.py.from_imageplus(imp)
print(f"Processed array shape: {result.shape}, dtype: {result.dtype}")
```

## Core API

### Module 1: Initialization

PyImageJ must be initialized once per Python session. The `mode` and endpoint determine which ImageJ distribution and GUI behavior to use.

```python
import imagej

# Headless Fiji — most common for scripts and batch jobs
ij = imagej.init("sc.fiji:fiji", mode="headless")

# GUI mode — opens the Fiji window (requires a display)
ij = imagej.init("sc.fiji:fiji", mode="gui")

# Local Fiji installation — faster startup, no download
ij = imagej.init("/path/to/Fiji.app", mode="headless")

# Specific Fiji version
ij = imagej.init("sc.fiji:fiji:2.14.0", mode="headless")

# Bare ImageJ2 without Fiji plugins
ij = imagej.init("net.imagej:imagej", mode="headless")

print(f"ImageJ version: {ij.getVersion()}")
print(f"Headless: {ij.ui().isHeadless()}")
```

### Module 2: Image I/O

Open and save images using ImageJ's I/O layer (which includes Bio-Formats for proprietary formats) and convert between ImageJ and NumPy representations.

```python
import imagej
import numpy as np

ij = imagej.init("sc.fiji:fiji", mode="headless")

# Open any format Bio-Formats supports: CZI, LIF, ND2, ICS, TIFF, etc.
imp = ij.io().open("/data/experiment.czi")
print(f"Dimensions: {imp.getDimensions()}")   # [W, H, C, Z, T]
print(f"nSlices: {imp.getNSlices()}, nFrames: {imp.getNFrames()}")

# Save image
ij.io().save(imp, "/data/output.tif")
print("Saved output.tif")
```

```python
# NumPy ↔ ImageJ conversion
arr = np.zeros((100, 100), dtype=np.uint16)
arr[30:70, 30:70] = 1000   # bright square

# NumPy → ImagePlus
imp = ij.py.to_imageplus(arr)
print(f"ImagePlus: {imp.getWidth()}×{imp.getHeight()}, type={imp.getType()}")

# ImagePlus → NumPy (returns a view where possible)
arr_back = ij.py.from_imageplus(imp)
print(f"NumPy array: shape={arr_back.shape}, dtype={arr_back.dtype}")

# Multi-channel array: shape (C, H, W)
rgb = np.random.randint(0, 255, (3, 256, 256), dtype=np.uint8)
imp_rgb = ij.py.to_imageplus(rgb)
print(f"Channels: {imp_rgb.getNChannels()}")
```

### Module 3: Macro Execution

Run ImageJ macro language (IJM) snippets or macro files. Macros execute inside the ImageJ environment and can call any built-in ImageJ command.

```python
import imagej

ij = imagej.init("sc.fiji:fiji", mode="headless")

# Run an inline macro string
ij.macro.run("print('Hello from ImageJ macro');")

# Run a macro with options string (key=value pairs)
# Options string mirrors the dialog parameters of ImageJ commands
macro_code = """
run("Gaussian Blur...", "sigma=2");
run("Auto Threshold", "method=Otsu white");
"""
ij.macro.run(macro_code)

# Run a macro file from disk
ij.macro.runMacroFile("/scripts/my_analysis.ijm")

# Run macro that returns a value via getResult or output string
result = ij.macro.run("""
x = 42 * 2;
return x;
""")
print(f"Macro returned: {result}")
```

```python
# Macro with current image: open → process → measure
ij.io().open("/data/cells.tif")   # sets current active image

measure_macro = """
run("Set Measurements...", "area mean min integrated redirect=None decimal=3");
run("Analyze Particles...", "size=50-Infinity display clear summarize");
"""
ij.macro.run(measure_macro)
print("Analyze Particles complete; results in Results table")
```

### Module 4: ImageJ Ops

ImageJ Ops is a framework of 150+ image processing operations with type-safe dispatch. Ops work on ImgLib2 `Img` objects and are the preferred way to call image processing algorithms programmatically.

```python
import imagej
import numpy as np

ij = imagej.init("sc.fiji:fiji", mode="headless")

arr = np.random.randint(100, 900, (512, 512), dtype=np.uint16)
img = ij.py.to_java(arr)   # converts to ImgLib2 RandomAccessibleInterval

# Gaussian blur
blurred = ij.op().filter().gauss(img, 2.0)
blurred_np = ij.py.from_java(blurred)
print(f"Blurred: {blurred_np.shape}")

# Otsu threshold → binary image
binary = ij.op().threshold().otsu(img)
binary_np = ij.py.from_java(binary)
print(f"Binary unique values: {np.unique(binary_np)}")

# Morphological operations
from jnius import autoclass
BitType = autoclass("net.imglib2.type.logic.BitType")
opened = ij.op().morphology().open(binary, [3, 3])
opened_np = ij.py.from_java(opened)
print(f"After opening: {opened_np.shape}")
```

```python
# Statistics ops
mean_val = ij.op().stats().mean(img)
std_val  = ij.op().stats().stdDev(img)
print(f"Mean intensity: {mean_val:.1f}, StdDev: {std_val:.1f}")

# Math ops: multiply image by scalar
scaled = ij.op().math().multiply(img, ij.py.to_java(2.0))
print(f"Scaled max: {ij.py.from_java(scaled).max()}")
```

### Module 5: Plugin and Command Calls

SciJava commands are the primary way to invoke Fiji plugins programmatically. Commands accept a dict of named parameters mirroring the plugin dialog.

```python
import imagej

ij = imagej.init("sc.fiji:fiji", mode="headless")

# Open a file using Bio-Formats opener command
future = ij.command().run(
    "loci.plugins.LociImporter",
    True,
    {"id": "/data/image.lif", "open_files": True, "autoscale": True}
)
module = future.get()
imp = module.getOutput("imp")
print(f"Opened via Bio-Formats: {imp.getDimensions()}")
```

```python
# Run Analyze Particles as a SciJava command
ij.io().open("/data/binary_mask.tif")

future = ij.command().run(
    "ij.plugin.filter.ParticleAnalyzer",
    True,
    {
        "minSize": 50.0,
        "maxSize": float("inf"),
        "options": 0,      # SHOW_NONE
        "measurements": 1,  # AREA
    }
)
future.get()
print("Analyze Particles command complete")

# Alternatively, run via macro string for simpler plugin invocation
ij.macro.run("""
run("Analyze Particles...", "size=50-Infinity display clear summarize");
""")
```

### Module 6: Results Table and ROI Analysis

Retrieve measurement results from ImageJ's Results table and ROI Manager after running Analyze Particles or other measurement commands.

```python
import imagej
import pandas as pd

ij = imagej.init("sc.fiji:fiji", mode="headless")

# After running Analyze Particles, read the Results table
def results_to_dataframe(ij) -> pd.DataFrame:
    """Convert ImageJ Results table to pandas DataFrame."""
    rt = ij.ResultsTable.getResultsTable()
    if rt is None or rt.size() == 0:
        return pd.DataFrame()
    headings = list(rt.getHeadings())
    data = {col: [rt.getValue(col, i) for i in range(rt.size())]
            for col in headings}
    return pd.DataFrame(data)

# Run segmentation + measurement macro
ij.io().open("/data/cells.tif")
ij.macro.run("""
run("Gaussian Blur...", "sigma=1.5");
setAutoThreshold("Otsu dark");
run("Convert to Mask");
run("Analyze Particles...", "size=20-Infinity display clear");
""")

df = results_to_dataframe(ij)
print(f"Found {len(df)} objects")
print(df[["Area", "Mean", "IntDen"]].describe())
df.to_csv("particle_measurements.csv", index=False)
print("Saved particle_measurements.csv")
```

```python
# Access the ROI Manager
def get_roi_manager(ij):
    """Return the ImageJ ROI Manager instance, creating if needed."""
    RoiManager = ij.py.jclass("ij.plugin.frame.RoiManager")
    rm = RoiManager.getInstance()
    if rm is None:
        rm = RoiManager(False)   # headless=False means no GUI window
    return rm

rm = get_roi_manager(ij)
roi_count = rm.getCount()
print(f"ROIs in manager: {roi_count}")

# Extract bounding boxes for all ROIs
rois = []
for i in range(roi_count):
    roi = rm.getRoi(i)
    bounds = roi.getBounds()
    rois.append({"index": i, "x": bounds.x, "y": bounds.y,
                 "width": bounds.width, "height": bounds.height})
roi_df = pd.DataFrame(rois)
print(roi_df.head())
```

## Common Workflows

### Workflow 1: Automated Fluorescence Quantification

**Goal**: Open a multi-channel TIFF stack, apply Gaussian blur, threshold nuclei channel, run Analyze Particles, and export per-cell measurements as CSV.

```python
import imagej
import pandas as pd
import numpy as np
from pathlib import Path

ij = imagej.init("sc.fiji:fiji", mode="headless")

def quantify_nuclei(tiff_path: str, output_csv: str,
                    channel: int = 1, sigma: float = 1.5,
                    min_size: int = 50) -> pd.DataFrame:
    """
    Segment and measure nuclei in a fluorescence TIFF.

    Parameters
    ----------
    tiff_path  : path to single- or multi-channel TIFF
    output_csv : where to save results
    channel    : 1-based channel index for nuclear stain (e.g., DAPI)
    sigma      : Gaussian blur radius in pixels
    min_size   : minimum nucleus area in pixels
    """
    # Step 1: Open image
    imp = ij.io().open(tiff_path)
    print(f"Loaded: {Path(tiff_path).name}  dims={imp.getDimensions()}")

    # Step 2: Extract channel if multi-channel
    if imp.getNChannels() > 1:
        imp.setC(channel)

    # Step 3: Apply Gaussian blur and threshold via macro
    ij.macro.run(f"""
selectWindow("{imp.getTitle()}");
run("Gaussian Blur...", "sigma={sigma}");
setAutoThreshold("Otsu dark");
run("Convert to Mask");
run("Fill Holes");
run("Watershed");
""")

    # Step 4: Measure
    ij.macro.run(f"""
run("Set Measurements...", "area mean min centroid integrated shape redirect=None decimal=3");
run("Analyze Particles...", "size={min_size}-Infinity display clear include summarize");
""")

    # Step 5: Collect results
    rt = ij.ResultsTable.getResultsTable()
    if rt is None or rt.size() == 0:
        print("No objects detected")
        return pd.DataFrame()

    headings = list(rt.getHeadings())
    df = pd.DataFrame(
        {col: [rt.getValue(col, i) for i in range(rt.size())]
         for col in headings}
    )
    df["source_file"] = Path(tiff_path).stem
    df.to_csv(output_csv, index=False)
    print(f"Saved {len(df)} measurements → {output_csv}")
    return df


df = quantify_nuclei(
    tiff_path="/data/experiment_dapi.tif",
    output_csv="nuclei_measurements.csv",
    channel=1,
    sigma=1.5,
    min_size=50
)
print(df[["Area", "Mean", "Circ."]].describe())
```

### Workflow 2: Batch Fiji Macro Processing

**Goal**: Process a folder of images with an existing Fiji `.ijm` macro file, collect the Results table from each image into a single DataFrame.

```python
import imagej
import pandas as pd
from pathlib import Path

ij = imagej.init("sc.fiji:fiji", mode="headless")

def run_macro_on_image(ij, image_path: str, macro_file: str) -> pd.DataFrame:
    """Open one image, run a macro file, return its Results table."""
    ij.io().open(image_path)

    # Clear any previous results before running
    ij.macro.run("run(\"Clear Results\");")

    # Run macro file (macro must operate on the active image)
    ij.macro.runMacroFile(macro_file)

    rt = ij.ResultsTable.getResultsTable()
    if rt is None or rt.size() == 0:
        return pd.DataFrame()
    headings = list(rt.getHeadings())
    return pd.DataFrame(
        {col: [rt.getValue(col, i) for i in range(rt.size())]
         for col in headings}
    )


input_dir  = Path("/data/images")
macro_file = "/scripts/measure_cells.ijm"
output_csv = "batch_results.csv"

all_results = []
image_files = sorted(input_dir.glob("*.tif"))

for img_path in image_files:
    print(f"Processing: {img_path.name}")
    df = run_macro_on_image(ij, str(img_path), macro_file)
    if not df.empty:
        df["filename"] = img_path.name
        all_results.append(df)

    # Close all windows to free memory between images
    ij.macro.run("close('*');")

if all_results:
    combined = pd.concat(all_results, ignore_index=True)
    combined.to_csv(output_csv, index=False)
    print(f"Batch complete: {len(image_files)} images, "
          f"{len(combined)} total measurements → {output_csv}")
else:
    print("No results collected from any image")
```

## Key Parameters

| Parameter | Module | Default | Range / Options | Effect |
|-----------|--------|---------|-----------------|--------|
| `mode` | Initialization | `"headless"` | `"headless"`, `"gui"`, `"interactive"` | Controls whether Fiji GUI window opens; use `"headless"` for scripts |
| `endpoint` | Initialization | `"sc.fiji:fiji"` | Maven coordinate or `/path/to/Fiji.app` | Selects ImageJ2 distribution; `sc.fiji:fiji` includes all Fiji plugins |
| `sigma` (Gaussian blur) | Macro / Ops | `2.0` | `0.5`–`10.0` | Spatial smoothing radius in pixels; higher reduces noise but blurs edges |
| `minSize` (Analyze Particles) | Plugin / Macro | `0` | pixels² or `0`–`Infinity` | Smallest object area to include; eliminates noise particles |
| `method` (Auto Threshold) | Macro / Ops | `"Otsu"` | `"Otsu"`, `"Triangle"`, `"MaxEntropy"`, `"Huang"`, `"Li"` | Threshold algorithm; Otsu works well for bimodal histograms |
| `measurements` bitmask | Results / Macro | varies | OR combination of `AREA=1`, `MEAN=2`, `CENTROID=4`, etc. | Selects which columns appear in the Results table |
| Java heap size | Initialization (env) | JVM default (~25% RAM) | set via `JAVA_TOOL_OPTIONS` | Limits memory for large stacks; set `-Xmx8g` for big images |

## Best Practices

1. **Initialize once per session and reuse `ij`**: Starting a new JVM is expensive (5–15 seconds). Create `ij` at module level or pass it as a parameter rather than calling `imagej.init()` inside a loop.

   ```python
   # At module top level — initialized once
   import imagej
   ij = imagej.init("sc.fiji:fiji", mode="headless")

   def process(path):
       imp = ij.io().open(path)   # reuse ij
       ...
   ```

2. **Use conda for Java management**: pip-only installs frequently fail because `JAVA_HOME` is not set or the wrong JDK version is on `PATH`. A conda environment with `openjdk=11` avoids 90% of JVM-not-found errors.

3. **Clear Results and ROI Manager between images in batch loops**: ImageJ accumulates results across calls in the same session. Always call `run("Clear Results")` and `rm.reset()` before each image to prevent row contamination.

   ```python
   ij.macro.run("run('Clear Results');")
   rm = get_roi_manager(ij)
   rm.reset()
   ```

4. **Prefer `ij.macro.run()` for simple commands over `ij.command().run()`**: Macro strings are shorter, easier to read, and use the same syntax as the Fiji Macro Recorder. Use `ij.command().run()` only when you need programmatic access to command outputs (module return values).

5. **Convert to NumPy as late as possible**: `ij.py.from_imageplus()` copies data from the JVM to Python. For multi-step processing inside ImageJ, keep data in ImagePlus or ImgLib2 form and convert only at the end to minimize memory-copy overhead.

6. **Use `ij.py.to_java()` / `ij.py.from_java()` for ImgLib2 Ops**: The `to_imageplus()` / `from_imageplus()` pair works with the classic ImageProcessor; `to_java()` / `from_java()` target the modern ImgLib2 type system required by `ij.op()`.

7. **Set a Fiji update site plugins list during init for reproducibility**: Specify a pinned Fiji version (`sc.fiji:fiji:2.14.0`) rather than `sc.fiji:fiji` (latest) so your pipeline behavior does not change when Fiji releases new plugin updates.

## Common Recipes

### Recipe: TrackMate Headless Spot Detection

When to use: Run TrackMate particle tracking programmatically and retrieve detected spots as a DataFrame without opening the TrackMate GUI.

```python
import imagej
import pandas as pd

ij = imagej.init("sc.fiji:fiji", mode="headless")

# TrackMate headless via macro (scripting interface)
trackmate_macro = """
run("TrackMate", "");
// For fully scripted TrackMate, use the Scripting Interface
// documented at https://imagej.net/plugins/trackmate/scripting
"""

# Scripted TrackMate via Jython-style Java interop
def run_trackmate_headless(ij, imp, radius=3.0, threshold=100.0):
    """Detect spots with LoG detector; return DataFrame of spot coordinates."""
    from jnius import autoclass

    # Import TrackMate classes
    Model          = autoclass("fiji.plugin.trackmate.Model")
    Settings       = autoclass("fiji.plugin.trackmate.Settings")
    TrackMate      = autoclass("fiji.plugin.trackmate.TrackMate")
    LogDetectorFactory = autoclass(
        "fiji.plugin.trackmate.detection.LogDetectorFactory")

    model    = Model()
    settings = Settings(imp)

    # Configure LoG spot detector
    settings.detectorFactory = LogDetectorFactory()
    settings.detectorSettings = {
        "DO_SUBPIXEL_LOCALIZATION": True,
        "RADIUS": radius,
        "TARGET_CHANNEL": 1,
        "THRESHOLD": threshold,
        "DO_MEDIAN_FILTERING": False,
    }

    tm = TrackMate(model, settings)
    tm.process()

    # Extract spot table
    spots = model.getSpots()
    spots.setVisible(True)
    records = []
    for spot in spots.iterable(True):
        records.append({
            "id":       spot.ID(),
            "x":        spot.getDoublePosition(0),
            "y":        spot.getDoublePosition(1),
            "z":        spot.getDoublePosition(2),
            "frame":    spot.getFeature("FRAME"),
            "quality":  spot.getFeature("QUALITY"),
        })
    return pd.DataFrame(records)


imp = ij.io().open("/data/timelapse.tif")
df  = run_trackmate_headless(ij, imp, radius=3.0, threshold=50.0)
print(f"Detected {len(df)} spots across {df['frame'].nunique()} frames")
df.to_csv("spots.csv", index=False)
print(df.head())
```

### Recipe: Convert ImageJ Hyperstack to NumPy 5D Array (TZCYX)

When to use: Import a multi-dimensional Fiji hyperstack into Python as a 5D NumPy array with the standard TZCYX axis order used by most scientific image analysis libraries.

```python
import imagej
import numpy as np

ij = imagej.init("sc.fiji:fiji", mode="headless")

def hyperstack_to_numpy(ij, imp) -> np.ndarray:
    """
    Convert an ImageJ hyperstack to a NumPy array with shape (T, Z, C, Y, X).

    ImageJ internal order is C-Z-T (slowest to fastest in stack index).
    This function reorders to the TZCYX convention used by tifffile, OME, etc.
    """
    nC = imp.getNChannels()
    nZ = imp.getNSlices()
    nT = imp.getNFrames()
    H  = imp.getHeight()
    W  = imp.getWidth()

    arr = np.zeros((nT, nZ, nC, H, W), dtype=np.uint16)

    for t in range(1, nT + 1):
        for z in range(1, nZ + 1):
            for c in range(1, nC + 1):
                idx = imp.getStackIndex(c, z, t)
                imp.setSlice(idx)
                arr[t-1, z-1, c-1] = ij.py.from_imageplus(imp)

    return arr


imp = ij.io().open("/data/4d_experiment.tif")
print(f"ImageJ dims (W,H,C,Z,T): {imp.getDimensions()}")

stack = hyperstack_to_numpy(ij, imp)
print(f"NumPy TZCYX shape: {stack.shape}")  # e.g., (10, 15, 2, 512, 512)
print(f"dtype: {stack.dtype}, max: {stack.max()}")

# Save as OME-TIFF with correct axis metadata
import tifffile
tifffile.imwrite(
    "output_TZCYX.ome.tif",
    stack,
    imagej=True,
    metadata={"axes": "TZCYX"},
    photometric="minisblack"
)
print("Saved output_TZCYX.ome.tif")
```

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| `JVMNotFoundException` on init | `JAVA_HOME` not set or wrong JDK version | Install via conda: `conda install -c conda-forge openjdk=11`; avoid Java 17 |
| `RuntimeError: Fiji download failed` | No internet or corporate proxy | Download Fiji manually from fiji.sc, then use `imagej.init("/path/to/Fiji.app")` |
| `java.lang.OutOfMemoryError` on large stacks | JVM default heap is too small | Set `export JAVA_TOOL_OPTIONS="-Xmx8g"` before importing imagej |
| Macro `run(...)` silently does nothing | No active image when macro expects one | Call `ij.io().open(path)` before running processing macros; check `ij.WindowManager.getImageCount()` |
| Results table empty after Analyze Particles | Threshold not applied, or mask not binary | Verify mask is 8-bit binary (0/255) with `imp.getType() == 0`; run `Convert to Mask` before Analyze Particles |
| `AttributeError: 'NoneType' object` on `ij.ResultsTable.getResultsTable()` | No measurements run yet in this session | Confirm Analyze Particles macro completed; run `ij.macro.run("print(nResults);")` to check count |
| Plugin class not found (`ClassNotFoundException`) | Plugin not in this Fiji installation | Add the Fiji update site (e.g., TrackMate) or use `sc.fiji:fiji` endpoint which includes all default plugins |
| `gui` mode crashes with `HeadlessException` | No display available (SSH/cluster) | Use `mode="headless"` for remote environments; GUI mode requires `DISPLAY` or X11 forwarding |

## Related Skills

- **scikit-image-processing** — pure Python image processing without JVM; use when Fiji plugins are not needed
- **napari-image-viewer** — interactive multi-dimensional image viewer for Python; complement to PyImageJ for visualization
- **trackpy-particle-tracking** — Python-native Crocker-Grier SPT; alternative to TrackMate for simple 2D tracking
- **cellpose-cell-segmentation** — deep learning cell segmentation; can be run standalone or as a Fiji plugin
- **omero-integration** — OMERO server image management; PyImageJ can process images retrieved via omero-py

## References

- [PyImageJ documentation](https://pyimagej.readthedocs.io/) — official API reference, initialization guide, data conversion
- [PyImageJ GitHub repository](https://github.com/imagej/pyimagej) — source, issue tracker, notebooks, examples
- [ImageJ Ops framework](https://imagej.net/libs/imagej-ops/) — Ops namespace reference and algorithm catalog
- [TrackMate scripting guide](https://imagej.net/plugins/trackmate/scripting) — headless TrackMate Java API patterns
- [Bio-Formats supported formats](https://bio-formats.readthedocs.io/en/latest/supported-formats.html) — list of proprietary microscopy formats openable via `ij.io().open()`
- [ImageJ Macro Language reference](https://imagej.nih.gov/ij/developer/macro/macros.html) — built-in functions for `ij.macro.run()` strings
