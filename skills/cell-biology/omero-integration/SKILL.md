---
name: "omero-integration"
description: "OMERO is an open-source platform for biological image data management. Use the omero-py Python client to connect to an OMERO server, search and retrieve images as numpy arrays, annotate images with tags and key-value pairs, manage ROIs, and integrate OMERO image data into downstream analysis pipelines — all programmatically without the OMERO desktop GUI."
license: "GPL-2.0"
---

# omero-integration

## Overview

OMERO is an open-source image data management system widely used in microscopy facilities and core labs. The `omero-py` library provides a Python client (`BlitzGateway`) that connects to an OMERO server, allowing programmatic access to images, datasets, projects, tags, annotations, and ROIs. Use it to build automated analysis workflows that pull images from OMERO, process them in Python, and write results back as annotations.

## When to Use

- **Programmatic image retrieval from OMERO**: Downloading microscopy images as numpy arrays for downstream analysis without using the OMERO Insight GUI.
- **Bulk annotation and tagging**: Applying tags, key-value pair annotations, or comments to large numbers of images/datasets based on analysis results.
- **ROI access and management**: Reading segmentation ROIs (shapes) stored in OMERO for downstream quantification or export.
- **Integrating OMERO into Python analysis pipelines**: Connecting OMERO image data to scikit-image, OpenCV, CellPose, or other image analysis tools.
- **Automated QC workflows**: Querying images by metadata (channel, acquisition date, experimenter) and flagging those that fail quality criteria.
- **Data provenance tracking**: Attaching analysis provenance (parameters, tool versions) as structured key-value annotations to images.
- For local image analysis without an OMERO server, use `tifffile`, `aicsimageio`, or `imageio` directly.

## Prerequisites

- **Python packages**: `omero-py`, `numpy`, `Pillow`
- **System**: Java 8+ (required by `omero-py` internals), Ice 3.6 (installed automatically via conda)
- **Data requirements**: Access credentials to a running OMERO server (host, port, username, password)
- **Environment**: Conda is strongly recommended; `omero-py` has complex dependencies

```bash
conda create -n omero python=3.9
conda activate omero
conda install -c ome -c conda-forge omero-py
pip install numpy Pillow
```

## Quick Start

```python
import omero
from omero.gateway import BlitzGateway

# Connect to OMERO server
conn = BlitzGateway("username", "password", host="omero.example.org", port=4064)
conn.connect()
print(f"Connected: {conn.isConnected()}, user: {conn.getUser().getName()}")

# Get an image by ID and download as numpy array
image = conn.getObject("Image", 12345)
pixels = image.getPrimaryPixels()
plane = pixels.getPlane(0, 0, 0)   # z=0, c=0, t=0
print(f"Image shape: {plane.shape}, dtype: {plane.dtype}")

conn.close()
```

## Core API

### Module 1: BlitzGateway — Connection Management

`BlitzGateway` is the main entry point for all server interactions.

```python
from omero.gateway import BlitzGateway

# Establish connection
conn = BlitzGateway(
    username="user",
    passwd="password",
    host="omero.example.org",
    port=4064,
    secure=True,
)
success = conn.connect()
print(f"Connected: {success}")
print(f"Server version: {conn.getServerVersion()}")
print(f"Current group: {conn.getGroupFromContext().getName()}")

# Always close when done
conn.close()
```

```python
# Context manager pattern for automatic cleanup
class OmeroConnection:
    def __init__(self, **kwargs):
        self.conn = BlitzGateway(**kwargs)
    def __enter__(self):
        self.conn.connect()
        return self.conn
    def __exit__(self, *args):
        self.conn.close()

with OmeroConnection(username="user", passwd="pass",
                     host="omero.example.org", port=4064) as conn:
    print(f"Connected as: {conn.getUser().getFullName()}")
```

### Module 2: Project, Dataset, and Image Queries

Traverse the OMERO data hierarchy (Project → Dataset → Image).

```python
# List all projects for the current user
for project in conn.listProjects():
    print(f"Project {project.getId()}: {project.getName()}")
    for dataset in project.listChildren():
        print(f"  Dataset {dataset.getId()}: {dataset.getName()}")
        for image in dataset.listChildren():
            print(f"    Image {image.getId()}: {image.getName()}")
```

```python
# Search for images by name
results = conn.searchObjects(["Image"], "GFP_control")
for img in results:
    print(f"  Found: {img.getId()} - {img.getName()}")

# Get a specific object by ID
image   = conn.getObject("Image",   12345)
dataset = conn.getObject("Dataset", 678)
project = conn.getObject("Project", 90)
print(f"Image: {image.getName()}, size: {image.getSizeX()}x{image.getSizeY()}")
print(f"Channels: {image.getSizeC()}, Z-slices: {image.getSizeZ()}, timepoints: {image.getSizeT()}")
```

### Module 3: Image Download as NumPy Arrays

Retrieve pixel data as numpy arrays for processing.

```python
import numpy as np

image  = conn.getObject("Image", 12345)
pixels = image.getPrimaryPixels()

# Get a single 2D plane: getPlane(z_index, channel_index, time_index)
plane = pixels.getPlane(0, 0, 0)
print(f"Plane shape: {plane.shape}, dtype: {plane.dtype}")

# Get all channels at z=0, t=0
planes = [pixels.getPlane(0, c, 0) for c in range(image.getSizeC())]
stack  = np.stack(planes, axis=0)   # shape: (C, Y, X)
print(f"Multi-channel stack: {stack.shape}")
```

```python
# Efficient bulk download using getTiles (for large images)
image  = conn.getObject("Image", 12345)
pixels = image.getPrimaryPixels()

tile_coords = [(0, 0, 0, (0, 0, 512, 512))]  # (z, c, t, (x, y, w, h))
for tile in pixels.getTiles(tile_coords):
    print(f"Tile shape: {tile.shape}")  # (512, 512) numpy array
```

### Module 4: Tag and Annotation Management

Add, retrieve, and update tags and key-value pair annotations on OMERO objects.

```python
import omero

# Add a tag to an image
tag_ann = omero.gateway.TagAnnotationWrapper(conn)
tag_ann.setValue("passed_QC")
tag_ann.setNs("my.analysis.namespace")
tag_ann.save()

image = conn.getObject("Image", 12345)
image.linkAnnotation(tag_ann)
print(f"Tag '{tag_ann.getValue()}' linked to image {image.getId()}")
```

```python
# Add key-value pairs (MapAnnotation) to an image
map_ann = omero.gateway.MapAnnotationWrapper(conn)
map_ann.setNs("openmicroscopy.org/omero/client/mapAnnotation")
kv_pairs = [
    ["analysis_tool",    "CellProfiler 4.2"],
    ["cell_count",       "342"],
    ["mean_intensity",   "1847.3"],
    ["analysis_date",    "2026-02-18"],
]
map_ann.setValue(kv_pairs)
map_ann.save()
image.linkAnnotation(map_ann)
print(f"Key-value annotation attached to image {image.getId()}")

# Read existing annotations
for ann in image.listAnnotations():
    print(f"  {ann.OMERO_TYPE}: {ann.getValue()}")
```

### Module 5: ROI Access

Read segmentation ROIs (shapes) stored in OMERO for downstream quantification.

```python
from omero.model import RoiI

# Get all ROIs for an image
roi_service = conn.getRoiService()
result = roi_service.findByImage(12345, None)

for roi in result.rois:
    for shape in roi.copyShapes():
        shape_type = shape.__class__.__name__
        print(f"  ROI {roi.id.val}: {shape_type}")
        if shape_type == "RectangleI":
            print(f"    x={shape.x.val:.1f}, y={shape.y.val:.1f}, "
                  f"w={shape.width.val:.1f}, h={shape.height.val:.1f}")
        elif shape_type == "EllipseI":
            print(f"    cx={shape.x.val:.1f}, cy={shape.y.val:.1f}, "
                  f"rx={shape.radiusX.val:.1f}, ry={shape.radiusY.val:.1f}")
```

```python
# Convert ROI masks to numpy boolean arrays
import numpy as np
from omero.gateway import BlitzGateway

def roi_to_mask(shape, height, width):
    """Convert a rectangle ROI to a boolean numpy mask."""
    mask = np.zeros((height, width), dtype=bool)
    x  = int(shape.x.val)
    y  = int(shape.y.val)
    w  = int(shape.width.val)
    h  = int(shape.height.val)
    mask[y:y+h, x:x+w] = True
    return mask

image  = conn.getObject("Image", 12345)
height = image.getSizeY()
width  = image.getSizeX()

result = conn.getRoiService().findByImage(12345, None)
for roi in result.rois:
    for shape in roi.copyShapes():
        if shape.__class__.__name__ == "RectangleI":
            mask = roi_to_mask(shape, height, width)
            print(f"ROI mask: {mask.sum()} pixels selected")
```

## Key Concepts

### OMERO Data Hierarchy

OMERO organizes data as Project → Dataset → Image. Images contain pixel data plus metadata (channels, Z-slices, timepoints). Annotations (tags, key-value pairs, comments) can be attached to any level of the hierarchy.

```python
# Hierarchy navigation
project = conn.getObject("Project", 90)
for dataset in project.listChildren():
    imgs = list(dataset.listChildren())
    print(f"Dataset '{dataset.getName()}': {len(imgs)} images")
```

### Pixel Access Patterns

OMERO stores pixels as (Z, C, T) stacks. `getPlane(z, c, t)` returns a single 2D numpy array. For large images, use `getTiles` to download spatial subregions. Pixel type (uint8, uint16, float32) matches the original acquisition format.

```python
image  = conn.getObject("Image", 12345)
pixels = image.getPrimaryPixels()
ptype  = pixels.getPixelsType().getValue()
print(f"Pixel type: {ptype}")  # e.g., "uint16"
print(f"Dimensions: XY={image.getSizeX()}x{image.getSizeY()}, "
      f"Z={image.getSizeZ()}, C={image.getSizeC()}, T={image.getSizeT()}")
```

## Common Workflows

### Workflow 1: Batch Download and Analysis

**Goal**: Download all images from a dataset, apply processing, and store results as key-value annotations.

```python
import numpy as np
from omero.gateway import BlitzGateway, MapAnnotationWrapper

def mean_intensity(plane):
    return float(plane.mean())

conn = BlitzGateway("user", "pass", host="omero.example.org", port=4064)
conn.connect()

dataset = conn.getObject("Dataset", 678)
results = []

for image in dataset.listChildren():
    pixels = image.getPrimaryPixels()
    plane  = pixels.getPlane(0, 0, 0)         # first z, channel 0, t=0
    mi     = mean_intensity(plane)
    results.append((image, mi))

    # Attach mean intensity as key-value annotation
    ann = MapAnnotationWrapper(conn)
    ann.setNs("my.pipeline.v1")
    ann.setValue([["mean_intensity_ch0", f"{mi:.2f}"]])
    ann.save()
    image.linkAnnotation(ann)
    print(f"Image {image.getId()} '{image.getName()}': mean={mi:.2f}")

print(f"\nProcessed {len(results)} images in dataset '{dataset.getName()}'")
conn.close()
```

### Workflow 2: Retrieve Images by Tag and Export

**Goal**: Find all images tagged "screen_hits", download channel 1 as numpy arrays, and save as TIFF files.

```python
import numpy as np
import tifffile
from omero.gateway import BlitzGateway

conn = BlitzGateway("user", "pass", host="omero.example.org", port=4064)
conn.connect()

# Find images with a specific tag
tag_value = "screen_hits"
tagged_images = []
for ann in conn.getObjects("TagAnnotation", attributes={"textValue": tag_value}):
    for image in ann.listLinkedObjects(["Image"]):
        tagged_images.append(image)

print(f"Found {len(tagged_images)} images tagged '{tag_value}'")

for image in tagged_images:
    pixels = image.getPrimaryPixels()
    # Download DAPI channel (index 0) at z=0, t=0
    plane  = pixels.getPlane(0, 0, 0)
    fname  = f"image_{image.getId()}_DAPI.tif"
    tifffile.imwrite(fname, plane)
    print(f"Saved {fname}: shape={plane.shape}, dtype={plane.dtype}")

conn.close()
print("Export complete")
```

## Key Parameters

| Parameter | Module | Default | Range / Options | Effect |
|-----------|--------|---------|-----------------|--------|
| `host` | BlitzGateway | required | hostname or IP | OMERO server address |
| `port` | BlitzGateway | `4064` | `1024`–`65535` | OMERO server port (4064 = standard) |
| `secure` | BlitzGateway | `False` | `True`, `False` | Use SSL/TLS encrypted connection |
| `z, c, t` | getPlane | `0, 0, 0` | `0` – size-1 | Z-slice, channel, timepoint indices |
| `tile_coords` | getTiles | — | list of `(z,c,t,(x,y,w,h))` | Spatial subregion download coordinates |
| `Ns` | annotations | `None` | any URI string | Namespace for annotation filtering |

## Best Practices

1. **Always close the connection**: Call `conn.close()` after all operations, or use a context manager. Unclosed connections consume server resources and can cause session timeouts.

2. **Use namespaces on annotations**: Set a unique `Ns` (namespace URI) on every annotation you create so your programmatic annotations can be distinguished from manual ones and other tools.

3. **Download only the planes you need**: For large time-lapse or Z-stack images, use `getPlane(z, c, t)` with specific indices rather than downloading all planes. For spatial subsets, use `getTiles`.

4. **Batch annotation writes to reduce server round-trips**: Collect key-value pairs across multiple images and write them in a loop rather than making individual RPC calls per image per key.

5. **Check image dimensions before processing**: Always read `getSizeX()`, `getSizeY()`, `getSizeC()`, `getSizeZ()`, `getSizeT()` before accessing pixel data to avoid index-out-of-bounds errors on unexpectedly shaped datasets.

## Common Recipes

### Recipe: List All Tags on an Image

When to use: Inspect existing annotations before adding new ones to avoid duplicates.

```python
image = conn.getObject("Image", 12345)
for ann in image.listAnnotations():
    if ann.OMERO_TYPE == "TagAnnotation":
        print(f"  Tag: '{ann.getValue()}' (ns={ann.getNs()})")
    elif ann.OMERO_TYPE == "MapAnnotation":
        for k, v in ann.getValue():
            print(f"  KV: {k} = {v}")
```

### Recipe: Multi-Channel Max Projection

When to use: Create a maximum intensity projection across all Z-slices for a given channel.

```python
import numpy as np

def max_projection(image, channel=0, timepoint=0):
    pixels = image.getPrimaryPixels()
    planes = [pixels.getPlane(z, channel, timepoint)
              for z in range(image.getSizeZ())]
    stack  = np.stack(planes, axis=0)
    return stack.max(axis=0)

image = conn.getObject("Image", 12345)
proj  = max_projection(image, channel=1)
print(f"Max projection shape: {proj.shape}, max value: {proj.max()}")
```

## Expected Outputs

- NumPy arrays from `getPlane()`: shape `(Y, X)`, dtype matching acquisition (uint8, uint16, float32)
- Multi-channel stacks: shape `(C, Y, X)` when stacking planes
- Annotations attached to images visible in OMERO.web and OMERO Insight GUI
- ROI shapes returned as `omero.model` objects with coordinate attributes

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| `Ice.ConnectionRefusedException` | Wrong host/port or server down | Verify `host` and `port=4064`; confirm server is running |
| `omero.SecurityViolation` | Insufficient permissions on object | Check group membership; ask server admin to grant access |
| `ImportError: omero` | omero-py not installed via conda | Use `conda install -c ome -c conda-forge omero-py`; pip install is unreliable |
| `AttributeError: 'NoneType' object` | Object ID not found on server | Verify the object exists with `conn.getObject(type, id)` returns non-None |
| `Ice.MemoryLimitException` | Downloading very large image all at once | Use `getTiles()` for spatial subsets or `getPlane()` per slice |
| Slow download speed | Downloading many small planes sequentially | Use `getTiles()` with a list of all coordinates for batch download |
| Session timeout mid-run | Long-running analysis exceeds server idle timeout | Call `conn.keepAlive()` periodically in long loops |

## References

- [OMERO Python API Documentation](https://omero-py.readthedocs.io/en/stable/) — official omero-py docs
- [OMERO Developer Documentation](https://docs.openmicroscopy.org/omero/5.6/developers/Python.html) — Python client guide
- [OMERO GitHub (ome/omero-py)](https://github.com/ome/omero-py) — source code and issue tracker
- [Linkert et al. (2010), J Cell Biol — OMERO paper](https://doi.org/10.1083/jcb.201004104) — original OMERO publication
