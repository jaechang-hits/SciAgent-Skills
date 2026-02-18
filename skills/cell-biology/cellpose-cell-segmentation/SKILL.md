---
name: "cellpose-cell-segmentation"
description: "Deep learning cell and nucleus segmentation from fluorescence and brightfield microscopy images. Uses pre-trained models (cyto3, nuclei, tissuenet) and a generalist flow-based algorithm that segments cells without requiring retraining on new image types. Outputs label masks for downstream morphology measurement and tracking. Use scikit-image watershed for rule-based segmentation; use Cellpose when deep learning generalization across staining conditions is needed."
license: "BSD-3-Clause"
---

# Cellpose — Deep Learning Cell Segmentation

## Overview

Cellpose uses a flow-based neural network to segment individual cells or nuclei in fluorescence microscopy images without manual parameter tuning. Pre-trained models (`cyto3`, `nuclei`, `tissuenet`) generalize across cell types, magnifications, and staining conditions — eliminating the need for manual threshold selection or watershed parameter optimization. Cellpose outputs integer label masks (each cell = unique integer) compatible with scikit-image `regionprops` for morphology measurement and with TrackPy for tracking. A built-in diameter estimator removes the need to specify cell size, though providing an approximate diameter improves accuracy.

## When to Use

- Segmenting cells or nuclei in fluorescence microscopy images where rule-based thresholding fails due to varying intensity or cell touching
- Processing large microscopy datasets in batch without per-image parameter tuning
- Segmenting diverse cell types (adherent cells, blood cells, bacteria, organoids) with a single model
- Producing label masks for downstream region property measurement (area, intensity, shape) with scikit-image
- 3D volumetric segmentation of z-stack microscopy data with `do_3D=True`
- Use **scikit-image watershed** when cells are well-separated and rule-based thresholding is sufficient
- Use **StarDist** as an alternative deep learning segmenter optimized for star-convex cells (neurons, nuclei)

## Prerequisites

- **Python packages**: `cellpose`, `numpy`, `matplotlib`
- **Optional**: GPU with CUDA for 10-50× speedup (`pip install cellpose[gui]` for GUI)
- **Input**: grayscale or multichannel TIFF/PNG images (2D or 3D arrays)

```bash
# Install Cellpose
pip install cellpose

# Install with GUI support
pip install cellpose[gui]

# Install with GPU (PyTorch CUDA)
pip install cellpose torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

# Verify
python -c "from cellpose import models; print('Cellpose ready')"
```

## Quick Start

```python
from cellpose import models
import numpy as np
from skimage import io

# Load image (grayscale or 2D array)
img = io.imread("cells.tif")  # shape: (H, W) or (H, W, C)

# Initialize model and segment
model = models.Cellpose(model_type="cyto3", gpu=False)
masks, flows, styles, diams = model.eval(img, diameter=0, channels=[0, 0])

print(f"Cells segmented: {masks.max()}")  # number of cells
print(f"Estimated diameter: {diams:.1f} px")
print(f"Mask shape: {masks.shape}")
```

## Workflow

### Step 1: Load and Inspect Images

Load microscopy images and inspect channel layout before segmentation.

```python
import numpy as np
from skimage import io
import matplotlib.pyplot as plt

# Load single-channel fluorescence image
img_gray = io.imread("nucleus_dapi.tif")           # shape: (H, W)
img_rgb = io.imread("cells_multichannel.tif")      # shape: (H, W, C)

print(f"Grayscale shape: {img_gray.shape}, dtype: {img_gray.dtype}")
print(f"Multichannel shape: {img_rgb.shape}")

# Preview
fig, axes = plt.subplots(1, 2, figsize=(12, 5))
axes[0].imshow(img_gray, cmap="gray")
axes[0].set_title("DAPI (nuclei)")
axes[1].imshow(img_rgb[..., 0], cmap="green")
axes[1].set_title("GFP channel")
plt.tight_layout()
plt.savefig("image_preview.png", dpi=100)
print("Saved: image_preview.png")
```

### Step 2: Segment Cells with a Pre-trained Model

Run Cellpose with the appropriate pre-trained model.

```python
from cellpose import models
import numpy as np
from skimage import io

# Available models: 'cyto3' (cells), 'nuclei', 'tissuenet', 'cyto2', 'CP'
model = models.Cellpose(model_type="cyto3", gpu=False)

img = io.imread("cells.tif")

# channels=[cytoplasm_channel, nucleus_channel]
# Use [0, 0] for grayscale; [1, 3] for green cytoplasm + blue nucleus (1-indexed)
masks, flows, styles, diams = model.eval(
    img,
    diameter=0,          # 0 = auto-estimate; or provide px estimate
    channels=[0, 0],     # grayscale
    flow_threshold=0.4,  # lower = fewer false positives; range 0.1-1.0
    cellprob_threshold=0.0,  # lower = more cells detected; range -6 to 6
)

print(f"Cells found: {masks.max()}")
print(f"Estimated cell diameter: {diams:.1f} pixels")
np.save("masks.npy", masks)
```

### Step 3: Segment Nuclei from DAPI Channel

Use the `nuclei` model for DAPI-stained nuclei.

```python
from cellpose import models
from skimage import io
import numpy as np

model = models.Cellpose(model_type="nuclei", gpu=False)
dapi = io.imread("dapi.tif")

# Nucleus-only segmentation: channels=[0, 0] (single channel)
masks, flows, styles, diams = model.eval(
    dapi,
    diameter=30,         # approximate nucleus diameter in pixels
    channels=[0, 0],
    flow_threshold=0.4,
    cellprob_threshold=0.0,
)

print(f"Nuclei segmented: {masks.max()}")
# Save label mask as TIFF for ImageJ/FIJI compatibility
from skimage import io as skio
skio.imsave("nuclei_masks.tif", masks.astype(np.uint16))
print("Saved: nuclei_masks.tif")
```

### Step 4: Visualize Segmentation Results

Overlay masks on original images for quality control.

```python
from cellpose import plot as cpplot
import matplotlib.pyplot as plt
import numpy as np
from skimage import io

img = io.imread("cells.tif")
masks = np.load("masks.npy")
flows_data = None  # load if you saved them: flows = np.load("flows.npy", allow_pickle=True)

# Cellpose built-in visualization
fig, axes = plt.subplots(1, 3, figsize=(15, 5))

# Original image
axes[0].imshow(img, cmap="gray")
axes[0].set_title(f"Original image")

# Label mask (each cell = unique color)
axes[1].imshow(masks, cmap="tab20")
axes[1].set_title(f"Segmentation masks ({masks.max()} cells)")

# Overlay: outline on original
from skimage.segmentation import find_boundaries
boundaries = find_boundaries(masks, mode="inner")
overlay = np.stack([img / img.max()] * 3, axis=-1)
overlay[boundaries] = [1, 0, 0]  # red outlines
axes[2].imshow(overlay)
axes[2].set_title("Outlines overlay")

plt.tight_layout()
plt.savefig("segmentation_result.png", dpi=150)
print("Saved: segmentation_result.png")
```

### Step 5: Measure Cell Properties from Masks

Extract morphology and intensity measurements using scikit-image regionprops.

```python
import numpy as np
import pandas as pd
from skimage.measure import regionprops_table
from skimage import io

masks = np.load("masks.npy")
img = io.imread("cells.tif")

# Measure morphology and intensity per cell
props = regionprops_table(
    masks, intensity_image=img,
    properties=["label", "area", "centroid", "eccentricity",
                 "mean_intensity", "max_intensity", "perimeter",
                 "equivalent_diameter_area"]
)
df = pd.DataFrame(props)
df.columns = ["cell_id", "area_px", "centroid_y", "centroid_x",
              "eccentricity", "mean_intensity", "max_intensity",
              "perimeter", "diameter_px"]

print(f"Cells measured: {len(df)}")
print(f"Median area: {df['area_px'].median():.0f} px²")
print(f"Median diameter: {df['diameter_px'].median():.1f} px")
print(df.head())

df.to_csv("cell_measurements.csv", index=False)
```

### Step 6: Batch Segment Multiple Images

Process a directory of images and aggregate results.

```python
from cellpose import models
from skimage import io
from skimage.measure import regionprops_table
import pandas as pd
import numpy as np
from pathlib import Path

model = models.Cellpose(model_type="cyto3", gpu=False)
image_dir = Path("images/")
output_dir = Path("results/")
output_dir.mkdir(exist_ok=True)

all_stats = []
for img_path in sorted(image_dir.glob("*.tif")):
    img = io.imread(img_path)
    masks, _, _, diams = model.eval(img, diameter=0, channels=[0, 0])
    
    # Save mask
    np.save(output_dir / f"{img_path.stem}_masks.npy", masks)
    
    # Measure
    if masks.max() > 0:
        props = regionprops_table(masks, intensity_image=img,
                                  properties=["label", "area", "mean_intensity"])
        df = pd.DataFrame(props)
        df["image"] = img_path.name
        df["est_diameter"] = diams
        all_stats.append(df)
    
    print(f"{img_path.name}: {masks.max()} cells, diameter={diams:.0f}px")

summary = pd.concat(all_stats, ignore_index=True)
summary.to_csv(output_dir / "all_cells.csv", index=False)
print(f"\nTotal cells: {len(summary)} across {summary['image'].nunique()} images")
```

## Key Parameters

| Parameter | Default | Range/Options | Effect |
|-----------|---------|---------------|--------|
| `model_type` | `"cyto3"` | `"cyto3"`, `"cyto2"`, `"nuclei"`, `"tissuenet"`, `"CP"`, custom path | Pre-trained model; `cyto3` is most general; `nuclei` for DAPI-only |
| `diameter` | `30` | 0–500 px | Approximate cell diameter in pixels; `0` = auto-estimate from image |
| `channels` | `[0, 0]` | `[cyto, nucleus]` (0=gray, 1=R, 2=G, 3=B) | Channel indices for cytoplasm and nuclear stain |
| `flow_threshold` | `0.4` | 0.1–1.0 | Cell probability threshold from flow field; lower = stricter |
| `cellprob_threshold` | `0.0` | −6 to 6 | Cell probability cutoff; increase to find more cells |
| `gpu` | `False` | `True`, `False` | Enable GPU inference (requires CUDA PyTorch) |
| `do_3D` | `False` | `True`, `False` | Enable 3D volumetric segmentation of z-stacks |
| `min_size` | `15` | integer px² | Minimum object size in pixels²; smaller objects discarded |
| `batch_size` | `8` | integer | Number of image tiles processed per GPU batch |
| `normalize` | `True` | `True`, `False` | Normalize image intensity before segmentation |

## Common Recipes

### Recipe 1: Segment Multichannel Image (GFP + DAPI)

```python
from cellpose import models
from skimage import io
import numpy as np

model = models.Cellpose(model_type="cyto3", gpu=False)

# Multichannel image: channel 1 = GFP (cytoplasm), channel 3 = DAPI (nucleus)
img_multi = io.imread("cells_gfp_dapi.tif")  # shape: (H, W, 3)

# channels=[cytoplasm_channel, nucleus_channel] (1-indexed for multichannel)
masks, flows, styles, diams = model.eval(
    img_multi,
    diameter=0,
    channels=[2, 3],  # GFP=channel2, DAPI=channel3 (1-indexed)
    flow_threshold=0.4,
)
print(f"Cells segmented: {masks.max()}, diameter: {diams:.0f}px")
np.save("masks_multichannel.npy", masks)
```

### Recipe 2: Use Cellpose CLI for Directory Batch Processing

```bash
# CLI batch segmentation of all TIFFs in a directory
cellpose \
    --image_path images/ \
    --pretrained_model cyto3 \
    --diameter 0 \
    --chan 0 \
    --save_tif \
    --no_npy

# With GPU
cellpose \
    --image_path images/ \
    --pretrained_model nuclei \
    --diameter 30 \
    --chan 0 \
    --use_gpu \
    --save_tif

# Results saved as: images/*_cp_masks.tif
echo "Done. Masks saved in images/ directory."
```

### Recipe 3: Fine-tune Cellpose on Custom Cell Type

```python
from cellpose import models, train
import numpy as np
from skimage import io

# Prepare training data: list of images and corresponding masks
train_images = [io.imread(f"train/img_{i}.tif") for i in range(10)]
train_masks = [np.load(f"train/mask_{i}.npy") for i in range(10)]

# Fine-tune starting from cyto3
model = models.CellposeModel(model_type="cyto3")

# Train: saves model to models/ directory
model_path = train.train_seg(
    model.net,
    train_data=train_images,
    train_labels=train_masks,
    channels=[0, 0],
    save_path="models/",
    n_epochs=100,
    learning_rate=0.2,
    weight_decay=1e-5,
)
print(f"Fine-tuned model saved: {model_path}")
```

## Expected Outputs

| Output | Format | Description |
|--------|--------|-------------|
| `masks` array | numpy int32 | Label mask: 0=background, 1..N=unique cell IDs |
| `flows` list | numpy arrays | Flow field components: [XY flows, cell prob, gradient] |
| `styles` array | numpy float | Style vector embedding (used for model similarity) |
| `diams` float | scalar | Estimated average cell diameter in pixels |
| `*_masks.npy` | NumPy | Saved mask array (from `np.save`) |
| `*_cp_masks.tif` | TIFF uint16 | Mask TIFF (from CLI `--save_tif`); compatible with FIJI/ImageJ |

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| All cells merged into one mask | Diameter too large or cells too close | Reduce `diameter`; increase `flow_threshold` to 0.6–0.8 |
| Very few cells detected | Diameter too small or `cellprob_threshold` too high | Increase `cellprob_threshold` to −2; use `diameter=0` for auto |
| Many false positives (background labeled) | Low `flow_threshold` | Increase `flow_threshold` to 0.6–0.9; increase `min_size` |
| GPU out of memory | Image too large for GPU batch | Process in tiles; reduce `batch_size`; crop image |
| Poor generalization on new cell type | Model not trained on similar cells | Try all pre-trained models; fine-tune with 10-20 annotated images |
| 3D segmentation very slow | Large z-stack on CPU | Enable GPU; reduce z-stack depth; use `anisotropy` parameter |
| Mask values overflow uint8 | More than 255 cells in image | Save with `dtype=np.uint16` or `np.int32` |
| Import error: `No module named 'cellpose'` | Package not installed | `pip install cellpose` or `conda install -c conda-forge cellpose` |

## References

- [Cellpose GitHub: MouseLand/cellpose](https://github.com/MouseLand/cellpose) — source code, documentation, and model zoo
- Stringer C et al. (2021) "Cellpose: a generalist algorithm for cellular segmentation" — *Nature Methods* 18:100-106. [DOI:10.1038/s41592-020-01018-x](https://doi.org/10.1038/s41592-020-01018-x)
- Pachitariu M & Stringer C (2022) "Cellpose 2.0: how to train your own model" — *Nature Methods* 19:1500-1508. [DOI:10.1038/s41592-022-01663-4](https://doi.org/10.1038/s41592-022-01663-4)
- [Cellpose documentation](https://cellpose.readthedocs.io/) — official API reference and training guide
