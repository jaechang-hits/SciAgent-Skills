---
name: "nnunet-segmentation"
description: "Train and deploy automated medical image segmentation models using nnU-Net's self-configuring framework that auto-selects optimal architecture, preprocessing, and training for any modality. Supports CT, MRI, microscopy, and ultrasound with 2D, 3D full-res, 3D low-res, and cascade configurations. Pipeline: convert dataset → plan and preprocess → train (5-fold cross-validation) → find best configuration → predict → ensemble. Use when classical segmentation fails and annotated training data is available."
license: "Apache-2.0"
---

# nnU-Net Automated Medical Image Segmentation

## Overview

nnU-Net (no-new-Net) is a self-configuring deep learning framework for biomedical image segmentation. Given a labeled training dataset, nnU-Net automatically determines the optimal network architecture (2D, 3D full-resolution, or 3D cascade), preprocessing steps (resampling, normalization, patch size), training schedule, and post-processing. It consistently achieves state-of-the-art performance across diverse imaging modalities and anatomical structures without manual hyperparameter tuning. nnU-Net v2 (`nnunetv2`) is the current release with a Python API for inference alongside the standard CLI.

## When to Use

- Segmenting anatomical structures in CT or MRI scans (organs, tumors, lesions) when you have 20+ annotated training cases
- Automating cell or nucleus segmentation in 3D fluorescence or electron microscopy volumes
- Establishing a strong baseline for any new segmentation challenge without manually tuning a U-Net
- Running inference on new images using a pretrained nnU-Net model from a published challenge
- Comparing segmentation methods: nnU-Net's auto-configured ensembles serve as a rigorous baseline
- Building production segmentation pipelines where training is done once and inference is repeated on many new cases
- Use **Cellpose** (`cellpose-cell-segmentation`) instead for 2D fluorescence cell segmentation without labeled training data; nnU-Net requires annotated training cases
- Use **SimpleITK** (`simpleitk-image-registration`) instead for rule-based segmentation with classical thresholding and region growing on images where deep learning training data is unavailable

## Prerequisites

- **Python packages**: `nnunetv2>=2.2`, `torch>=2.0` (with CUDA for GPU training)
- **Data requirements**: Images in NIfTI format (`.nii.gz`); binary or multi-class label masks; minimum 20 training cases recommended (50+ for best performance)
- **Environment variables**: `nnUNet_raw`, `nnUNet_preprocessed`, `nnUNet_results` must be set
- **Hardware**: GPU with 8+ GB VRAM recommended for training; CPU inference is supported but slow
- **Environment**: Python 3.9+; Linux or macOS (Windows supported but not officially recommended)

```bash
pip install nnunetv2

# Verify installation
nnUNetv2_train --help

# Set required environment variables (add to ~/.bashrc or ~/.zshrc)
export nnUNet_raw=/data/nnUNet_raw
export nnUNet_preprocessed=/data/nnUNet_preprocessed
export nnUNet_results=/data/nnUNet_results

mkdir -p $nnUNet_raw $nnUNet_preprocessed $nnUNet_results
```

## Quick Start

```bash
# Minimal end-to-end pipeline: convert dataset → preprocess → train → predict
# Assumes dataset is in Medical Segmentation Decathlon format

# 1. Set environment
export nnUNet_raw=/data/nnUNet_raw
export nnUNet_preprocessed=/data/nnUNet_preprocessed
export nnUNet_results=/data/nnUNet_results

# 2. Convert Medical Segmentation Decathlon dataset (dataset ID 7 = Pancreas)
nnUNetv2_convert_MSD_dataset -i /data/Task07_Pancreas -overwrite_id 7

# 3. Plan preprocessing and verify dataset integrity
nnUNetv2_plan_and_preprocess -d 7 --verify_dataset_integrity

# 4. Train 3D full-res model, fold 0 (of 5-fold cross-validation)
nnUNetv2_train 7 3d_fullres 0 --npz

# 5. Predict on new images
nnUNetv2_predict -i /data/test_images/ -o /data/predictions/ -d 7 -c 3d_fullres -f 0
echo "Segmentation predictions saved to /data/predictions/"
```

## Workflow

### Step 1: Prepare Dataset in nnU-Net Format

nnU-Net requires images in NIfTI format organized in a specific directory structure with a `dataset.json` descriptor.

```bash
# Dataset directory structure (Dataset007_Pancreas as example):
# $nnUNet_raw/
# └── Dataset007_Pancreas/
#     ├── dataset.json          ← metadata descriptor
#     ├── imagesTr/             ← training images
#     │   ├── pancreas_001_0000.nii.gz   (0000 = channel/modality index)
#     │   └── pancreas_002_0000.nii.gz
#     ├── labelsTr/             ← training segmentation masks
#     │   ├── pancreas_001.nii.gz
#     │   └── pancreas_002.nii.gz
#     └── imagesTs/             ← test images (no labels required)
#         └── pancreas_101_0000.nii.gz

# For Medical Segmentation Decathlon datasets, convert automatically:
nnUNetv2_convert_MSD_dataset -i /data/Task07_Pancreas -overwrite_id 7

echo "Dataset 7 created at $nnUNet_raw/Dataset007_Pancreas/"
```

```python
import json
from pathlib import Path
import shutil

# Create dataset.json for a custom dataset (single CT modality, 2-class segmentation)
dataset_id = 8
dataset_name = f"Dataset{dataset_id:03d}_MyOrgan"
dataset_dir = Path(f"{dataset_name}")
(dataset_dir / "imagesTr").mkdir(parents=True, exist_ok=True)
(dataset_dir / "labelsTr").mkdir(parents=True, exist_ok=True)
(dataset_dir / "imagesTs").mkdir(parents=True, exist_ok=True)

dataset_json = {
    "channel_names": {
        "0": "CT"           # for MRI: "0": "T1", "1": "T2" (multi-modal = multiple channels)
    },
    "labels": {
        "background": 0,
        "organ": 1          # add more classes: "tumor": 2, "vessel": 3
    },
    "numTraining": 50,      # number of training cases
    "file_ending": ".nii.gz"
}

with open(dataset_dir / "dataset.json", "w") as f:
    json.dump(dataset_json, f, indent=2)

print(f"Created dataset.json with {dataset_json['numTraining']} training cases")
print(f"Labels: {dataset_json['labels']}")
print(f"Channels: {dataset_json['channel_names']}")
print(f"\nPlace training images as: imagesTr/case_NNN_0000.nii.gz")
print(f"Place training labels as:  labelsTr/case_NNN.nii.gz")
```

### Step 2: Plan and Preprocess

nnU-Net analyzes the dataset fingerprint (image intensities, spacings, sizes) to automatically configure architectures and preprocessing. This step can take 30–120 minutes for large datasets.

```bash
# Plan preprocessing for dataset 7 with integrity checks
nnUNetv2_plan_and_preprocess -d 7 --verify_dataset_integrity

# This creates:
# $nnUNet_preprocessed/Dataset007_Pancreas/
# ├── nnUNetPlans.json           ← architecture configurations (patch size, batch size, etc.)
# ├── dataset_fingerprint.json   ← image statistics used for auto-configuration
# ├── nnUNetPlans_2d/            ← preprocessed 2D slices
# ├── nnUNetPlans_3d_fullres/    ← preprocessed 3D full-resolution patches
# └── nnUNetPlans_3d_lowres/     ← preprocessed 3D low-resolution patches (if applicable)

echo "Preprocessing complete. Plans stored in $nnUNet_preprocessed/Dataset007_Pancreas/"
```

```python
import json
from pathlib import Path
import os

# Inspect the auto-generated plans to understand what nnU-Net configured
preprocessed_dir = Path(os.environ["nnUNet_preprocessed"])
plans_file = preprocessed_dir / "Dataset007_Pancreas" / "nnUNetPlans.json"

with open(plans_file) as f:
    plans = json.load(f)

print("nnU-Net auto-configuration summary:")
print(f"  Dataset name: {plans['dataset_name']}")
print(f"  Original spacing (mm): {plans['original_median_spacing_after_transp']}")

for config_name, config in plans["configurations"].items():
    print(f"\n  Configuration: {config_name}")
    print(f"    Patch size:     {config.get('patch_size', 'N/A')}")
    print(f"    Batch size:     {config.get('batch_size', 'N/A')}")
    print(f"    Spacing:        {config.get('spacing', 'N/A')}")
    print(f"    Network arch:   {config.get('network_arch_class_name', 'N/A')}")
```

### Step 3: Train (5-Fold Cross-Validation)

nnU-Net uses 5-fold cross-validation by default. Train all 5 folds per configuration for the best ensemble performance, or train fold 0 only for a quick first model.

```bash
# Train 3D full-resolution configuration, fold 0 (on GPU)
# --npz saves softmax predictions for ensembling
nnUNetv2_train 7 3d_fullres 0 --npz

# Train all 5 folds (submit as 5 parallel jobs on a cluster)
for fold in 0 1 2 3 4; do
    nnUNetv2_train 7 3d_fullres $fold --npz
done

# Also train 2D configuration for potential ensemble
nnUNetv2_train 7 2d 0 --npz

echo "Training outputs in $nnUNet_results/Dataset007_Pancreas/"
```

```bash
# Resume training from a checkpoint (if interrupted)
nnUNetv2_train 7 3d_fullres 0 --npz --c

# Training on CPU only (slow — for testing only)
nnUNetv2_train 7 3d_fullres 0 --npz --device cpu

# Monitor GPU memory and training progress
watch -n 10 nvidia-smi

# Check training log for loss curves
tail -f $nnUNet_results/Dataset007_Pancreas/nnUNetTrainer__nnUNetPlans__3d_fullres/fold_0/training_log.txt
```

### Step 4: Find Best Configuration

After training, nnU-Net evaluates all trained configurations and their ensembles to recommend the best single model or ensemble.

```bash
# Determine which configuration or ensemble performs best on validation folds
# Must have trained multiple folds (0-4) for accurate comparison
nnUNetv2_find_best_configuration 7 -c 2d 3d_fullres

# Output example:
# Best configuration: 3d_fullres
# Best ensemble: 2d + 3d_fullres (Dice = 0.823 vs 3d_fullres alone = 0.814)
# Recommended: ensemble of 2d + 3d_fullres

# Also run post-processing determination
# (removes small connected components if it helps validation Dice)
nnUNetv2_apply_postprocessing --help
```

```python
import json
from pathlib import Path
import os

# Parse cross-validation results to see per-fold performance
results_dir = Path(os.environ["nnUNet_results"])
summary_file = results_dir / "Dataset007_Pancreas" / \
    "nnUNetTrainer__nnUNetPlans__3d_fullres" / "fold_0" / "validation" / "summary.json"

if summary_file.exists():
    with open(summary_file) as f:
        summary = json.load(f)

    metrics = summary["foreground_mean"]
    print("3D full-res fold_0 validation metrics:")
    for metric_name, value in metrics.items():
        print(f"  {metric_name}: {value:.4f}")
    # Expected output:
    # Dice: 0.81
    # IoU: 0.68
    # HD95: 12.3 (mm)
else:
    print(f"Summary not found at {summary_file}")
    print("Run nnUNetv2_train first to generate validation metrics")
```

### Step 5: Predict on New Images

Run inference on a folder of new images using the trained model.

```bash
# Predict using the best single configuration (fold 0 only, fast)
nnUNetv2_predict \
    -i /data/test_images/ \
    -o /data/predictions_3d/ \
    -d 7 \
    -c 3d_fullres \
    -f 0 \
    --save_probabilities    # save softmax probabilities for later ensembling

# Predict using all 5 folds (better performance, slower)
nnUNetv2_predict \
    -i /data/test_images/ \
    -o /data/predictions_allfolds/ \
    -d 7 \
    -c 3d_fullres \
    -f 0 1 2 3 4

echo "Predictions saved to /data/predictions_allfolds/"
```

```python
import torch
from nnunetv2.inference.predict_from_raw_data import nnUNetPredictor
from pathlib import Path
import os

# Python API for inference — useful for integration into custom pipelines
results_dir = os.environ["nnUNet_results"]
model_folder = f"{results_dir}/Dataset007_Pancreas/nnUNetTrainer__nnUNetPlans__3d_fullres"

# Initialize predictor
predictor = nnUNetPredictor(
    tile_step_size=0.5,      # overlap fraction between tiles (higher = better quality, slower)
    use_gaussian=True,       # Gaussian weighting at tile edges (reduces boundary artifacts)
    use_mirroring=True,      # test-time augmentation with flips (improves accuracy)
    device=torch.device("cuda", 0),  # use GPU 0; set to torch.device("cpu") for CPU
    verbose=False,
    allow_tqdm=True,
)

predictor.initialize_from_trained_model_folder(
    model_folder,
    use_folds=(0,),          # which folds to use; (0,1,2,3,4) for ensemble of all folds
    checkpoint_name="checkpoint_best.pth",  # or "checkpoint_final.pth"
)

# Predict from files
input_folder = "/data/test_images/"
output_folder = "/data/predictions/"
Path(output_folder).mkdir(exist_ok=True)

predictor.predict_from_files(
    list_of_lists_or_source_folder=input_folder,
    output_folder_or_list_of_truncated_output_files=output_folder,
    save_probabilities=False,
    overwrite=True,
    num_processes_preprocessing=2,
    num_processes_segmentation_export=2,
)
print(f"Python API inference complete → {output_folder}")
```

### Step 6: Ensemble Predictions

Combine predictions from multiple configurations (e.g., 2D + 3D full-res) or folds to improve segmentation accuracy.

```bash
# Ensemble predictions from two configurations
# Both must have been predicted with --save_probabilities
nnUNetv2_ensemble \
    -i /data/predictions_2d/ /data/predictions_3d/ \
    -o /data/predictions_ensemble/ \
    -np 4

echo "Ensemble predictions saved to /data/predictions_ensemble/"

# Apply post-processing (e.g., remove small connected components)
# Post-processing file generated during nnUNetv2_find_best_configuration
nnUNetv2_apply_postprocessing \
    -i /data/predictions_ensemble/ \
    -o /data/predictions_final/ \
    -pp_pkl_file $nnUNet_results/Dataset007_Pancreas/nnUNetTrainer__nnUNetPlans__3d_fullres/crossval_results_folds_0_1_2_3_4/postprocessing.pkl \
    -np 4 \
    -plans_json $nnUNet_preprocessed/Dataset007_Pancreas/nnUNetPlans.json

echo "Post-processing complete → /data/predictions_final/"
```

### Step 7: Evaluate Segmentation Quality

Compute Dice scores and Hausdorff distances between predicted and ground-truth segmentations.

```python
import SimpleITK as sitk
import numpy as np
import pandas as pd
from pathlib import Path

def compute_dice(pred_path: str, gt_path: str, label_value: int = 1) -> dict:
    """Compute Dice coefficient and Hausdorff distance for a single case."""
    pred = sitk.GetArrayFromImage(sitk.ReadImage(pred_path))
    gt = sitk.GetArrayFromImage(sitk.ReadImage(gt_path))

    pred_bin = (pred == label_value).astype(bool)
    gt_bin = (gt == label_value).astype(bool)

    intersection = (pred_bin & gt_bin).sum()
    dice = 2.0 * intersection / (pred_bin.sum() + gt_bin.sum() + 1e-8)

    # Surface distance for Hausdorff (using SimpleITK)
    pred_sitk = sitk.ReadImage(pred_path)
    gt_sitk = sitk.ReadImage(gt_path)
    pred_label = sitk.BinaryThreshold(pred_sitk, label_value, label_value, 1, 0)
    gt_label = sitk.BinaryThreshold(gt_sitk, label_value, label_value, 1, 0)

    hausdorff_filter = sitk.HausdorffDistanceImageFilter()
    hausdorff_filter.Execute(pred_label, gt_label)
    hd95 = hausdorff_filter.GetAverageHausdorffDistance()

    return {
        "dice": dice,
        "hd_avg_mm": hd95,
        "pred_volume_ml": pred_bin.sum() * np.prod(pred_sitk.GetSpacing()) / 1000,
        "gt_volume_ml": gt_bin.sum() * np.prod(gt_sitk.GetSpacing()) / 1000,
    }

# Evaluate all predictions
pred_dir = Path("/data/predictions_ensemble/")
gt_dir = Path("/data/test_labels/")

rows = []
for pred_file in sorted(pred_dir.glob("*.nii.gz")):
    gt_file = gt_dir / pred_file.name
    if gt_file.exists():
        metrics = compute_dice(str(pred_file), str(gt_file), label_value=1)
        metrics["case"] = pred_file.stem
        rows.append(metrics)

df = pd.DataFrame(rows)
print("Segmentation evaluation summary:")
print(df[["case", "dice", "hd_avg_mm", "pred_volume_ml", "gt_volume_ml"]].to_string(index=False))
print(f"\nMean Dice:      {df['dice'].mean():.3f} ± {df['dice'].std():.3f}")
print(f"Mean Avg HD:    {df['hd_avg_mm'].mean():.1f} ± {df['hd_avg_mm'].std():.1f} mm")
df.to_csv("segmentation_evaluation.csv", index=False)
print("Saved: segmentation_evaluation.csv")
```

### Step 8: Visualize Segmentation Results

Overlay predicted segmentations on input images for visual quality control.

```python
import SimpleITK as sitk
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from pathlib import Path

def visualize_segmentation(image_path: str, pred_path: str, gt_path: str = None,
                            output_path: str = "segmentation_qc.png",
                            n_slices: int = 5, label_value: int = 1):
    """Create a multi-slice overlay figure for visual QC."""
    image = sitk.GetArrayFromImage(sitk.ReadImage(image_path))  # shape: (z, y, x)
    pred = sitk.GetArrayFromImage(sitk.ReadImage(pred_path))

    # Select evenly spaced slices where segmentation is present
    label_slices = np.where((pred == label_value).any(axis=(1, 2)))[0]
    if len(label_slices) == 0:
        print("No foreground voxels found in prediction")
        return
    step = max(1, len(label_slices) // n_slices)
    selected_slices = label_slices[::step][:n_slices]

    n_cols = n_slices
    n_rows = 2 if gt_path is None else 3
    fig, axes = plt.subplots(n_rows, n_cols, figsize=(4 * n_cols, 4 * n_rows))

    # Normalize image for display
    vmin, vmax = np.percentile(image, [1, 99])
    cmap_label = mcolors.ListedColormap(["none", "#FF4500"])   # orange-red for prediction

    for col, z in enumerate(selected_slices):
        ax_img = axes[0, col] if n_rows > 1 else axes[col]
        ax_img.imshow(image[z], cmap="gray", vmin=vmin, vmax=vmax)
        ax_img.imshow((pred[z] == label_value), cmap=cmap_label, alpha=0.5, vmin=0, vmax=1)
        ax_img.set_title(f"Pred z={z}", fontsize=9)
        ax_img.axis("off")

        if gt_path is not None:
            gt = sitk.GetArrayFromImage(sitk.ReadImage(gt_path))
            ax_gt = axes[1, col]
            ax_gt.imshow(image[z], cmap="gray", vmin=vmin, vmax=vmax)
            ax_gt.imshow((gt[z] == label_value), cmap=cmap_label, alpha=0.5, vmin=0, vmax=1)
            ax_gt.set_title(f"GT z={z}", fontsize=9)
            ax_gt.axis("off")

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"QC figure saved: {output_path}")

# Generate QC plots for first 3 test cases
pred_dir = Path("/data/predictions_ensemble/")
image_dir = Path("/data/test_images/")
gt_dir = Path("/data/test_labels/")

for i, pred_file in enumerate(sorted(pred_dir.glob("*.nii.gz"))[:3]):
    case_id = pred_file.stem.replace(".nii", "")
    image_file = image_dir / f"{case_id}_0000.nii.gz"
    gt_file = gt_dir / pred_file.name

    if image_file.exists():
        visualize_segmentation(
            image_path=str(image_file),
            pred_path=str(pred_file),
            gt_path=str(gt_file) if gt_file.exists() else None,
            output_path=f"qc_{case_id}.png",
            n_slices=5
        )
```

## Key Parameters

| Parameter | Default | Range / Options | Effect |
|-----------|---------|-----------------|--------|
| `-c` (configuration) | — | `2d`, `3d_fullres`, `3d_lowres`, `3d_cascade_fullres` | Network architecture; 3d_fullres is the standard starting point |
| `-f` (fold) | — | `0`, `1`, `2`, `3`, `4`, `all` | Cross-validation fold(s) to train or use for inference |
| `--npz` (train) | off | flag | Save softmax probability maps during training; required for ensembling |
| `tile_step_size` (Python API) | `0.5` | `0.3`–`0.9` | Overlap between inference tiles; larger values improve accuracy at cost of speed |
| `use_mirroring` (Python API) | `True` | `True`, `False` | Test-time augmentation with axis flips; disable for 2–4× speedup with slight Dice drop |
| `--num_epochs` (train) | `1000` | `250`–`2000` | Training epochs; default 1000 is suitable for most datasets |
| `checkpoint_name` (Python API) | `"checkpoint_best.pth"` | `"checkpoint_best.pth"`, `"checkpoint_final.pth"` | Which saved checkpoint to load; `_best` is the highest-validation-Dice snapshot |
| `-np` (ensemble/postproc) | `3` | `1`–CPU count | Number of parallel processes for ensemble or post-processing |
| `minimumObjectSize` (postprocessing) | auto | voxel count | Minimum connected component size kept; determined automatically by `find_best_configuration` |
| `--device` (train) | `cuda` | `cuda`, `cpu`, `mps` | Training device; `mps` for Apple Silicon GPU |

## Common Recipes

### Recipe: Inference with a Pretrained Community Model

When to use: A published challenge model exists for your anatomy (e.g., abdominal organs, brain tumors). Download and apply without retraining.

```python
import torch
from nnunetv2.inference.predict_from_raw_data import nnUNetPredictor
from pathlib import Path

# Use a downloaded pretrained model folder
# Community models: https://zenodo.org/record/7783116 (abdominal organs)
model_folder = "/data/pretrained_models/Dataset003_Liver/nnUNetTrainer__nnUNetPlans__3d_fullres"

predictor = nnUNetPredictor(
    tile_step_size=0.5,
    use_gaussian=True,
    use_mirroring=True,
    device=torch.device("cuda", 0),
    allow_tqdm=True,
)
predictor.initialize_from_trained_model_folder(
    model_folder,
    use_folds=(0, 1, 2, 3, 4),          # ensemble all folds
    checkpoint_name="checkpoint_best.pth",
)

input_dir = "/data/new_ct_scans/"
output_dir = "/data/liver_predictions/"
Path(output_dir).mkdir(exist_ok=True)

predictor.predict_from_files(
    list_of_lists_or_source_folder=input_dir,
    output_folder_or_list_of_truncated_output_files=output_dir,
    save_probabilities=False,
    overwrite=True,
    num_processes_preprocessing=4,
    num_processes_segmentation_export=4,
)
print(f"Inference complete → {output_dir}")
```

### Recipe: Multi-Channel (Multi-Modal) Dataset Setup

When to use: Training with multiple imaging modalities for the same case (e.g., T1+T2+FLAIR for brain tumor segmentation).

```python
import json
from pathlib import Path
import shutil

# Multi-channel dataset: T1 + T2 + FLAIR brain MRI
dataset_dir = Path("Dataset001_BrainTumor")
for subdir in ["imagesTr", "labelsTr", "imagesTs"]:
    (dataset_dir / subdir).mkdir(parents=True, exist_ok=True)

# File naming convention: case_{ID}_{channel_index}.nii.gz
# For case 001: T1=001_0000, T2=001_0001, FLAIR=001_0002
# Rename your files accordingly:
case_id = "001"
modalities = {"T1": "0000", "T2": "0001", "FLAIR": "0002"}
for modality, idx in modalities.items():
    src = Path(f"/data/raw/{case_id}_{modality}.nii.gz")
    dst = dataset_dir / "imagesTr" / f"BrainTumor_{case_id}_{idx}.nii.gz"
    if src.exists():
        shutil.copy(src, dst)
        print(f"Copied {modality} → {dst.name}")

# dataset.json with multiple channels
dataset_json = {
    "channel_names": {"0": "T1", "1": "T2", "2": "FLAIR"},
    "labels": {"background": 0, "edema": 1, "non_enhancing_tumor": 2, "enhancing_tumor": 3},
    "numTraining": 200,
    "file_ending": ".nii.gz"
}
with open(dataset_dir / "dataset.json", "w") as f:
    json.dump(dataset_json, f, indent=2)

print("Multi-channel dataset.json created")
print(f"Channels: {dataset_json['channel_names']}")
print(f"Classes:  {dataset_json['labels']}")
```

### Recipe: Cascade Training for Large Structures

When to use: The structure to segment is very large relative to the image (e.g., whole brain, large organ in low-resolution CT), making 3D full-res training impractical due to memory.

```bash
# First train the low-res model (predicts a coarse segmentation)
nnUNetv2_train 7 3d_lowres 0 --npz
nnUNetv2_train 7 3d_lowres 1 --npz
nnUNetv2_train 7 3d_lowres 2 --npz
nnUNetv2_train 7 3d_lowres 3 --npz
nnUNetv2_train 7 3d_lowres 4 --npz

# Then train the high-res cascade (refines the low-res prediction)
# The cascade uses the low-res output as additional input
nnUNetv2_train 7 3d_cascade_fullres 0 --npz
nnUNetv2_train 7 3d_cascade_fullres 1 --npz
nnUNetv2_train 7 3d_cascade_fullres 2 --npz
nnUNetv2_train 7 3d_cascade_fullres 3 --npz
nnUNetv2_train 7 3d_cascade_fullres 4 --npz

# Predict with cascade: automatically uses lowres then cascade_fullres
nnUNetv2_predict -i /data/test/ -o /data/cascade_preds/ \
    -d 7 -c 3d_cascade_fullres -f 0 1 2 3 4

echo "Cascade prediction complete"
```

## Expected Outputs

| Output | Location | Description |
|--------|----------|-------------|
| `nnUNetPlans.json` | `$nnUNet_preprocessed/DatasetXXX/` | Auto-configured architecture, patch size, batch size, spacing |
| `dataset_fingerprint.json` | `$nnUNet_preprocessed/DatasetXXX/` | Dataset statistics used for auto-configuration |
| `checkpoint_best.pth` | `$nnUNet_results/.../fold_N/` | Model snapshot with highest validation Dice score |
| `checkpoint_final.pth` | `$nnUNet_results/.../fold_N/` | Final model checkpoint after all training epochs |
| `training_log.txt` | `$nnUNet_results/.../fold_N/` | Per-epoch train/validation loss and Dice scores |
| `summary.json` | `$nnUNet_results/.../fold_N/validation/` | Dice, IoU, Hausdorff distance on validation fold |
| `{case}.nii.gz` | Prediction output folder | Integer label map (0=background, 1,2,...=classes) |
| `{case}.npz` | Prediction folder (if `--save_probabilities`) | Softmax probability map for each class |

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| `RuntimeError: CUDA out of memory` | GPU VRAM insufficient for patch size | Reduce patch size in `nnUNetPlans.json` (edit `patch_size` and `batch_size`); use 2D configuration instead of 3D |
| `FileNotFoundError: nnUNet_raw not set` | Environment variable missing | `export nnUNet_raw=/path/to/raw`; verify with `echo $nnUNet_raw` |
| Dataset integrity check fails | Mismatched image/label sizes or naming | Ensure every `labelsTr/case_NNN.nii.gz` has a matching `imagesTr/case_NNN_0000.nii.gz`; check spacing matches |
| Low Dice after training | Too few training cases or poor labels | Minimum 20 cases; verify label quality visually; check class imbalance in `dataset.json` |
| Training plateau (loss not decreasing after epoch 200) | Learning rate too high or too low | nnU-Net uses auto LR schedule; if plateau persists, increase `numTraining` examples or check data augmentation |
| `ValueError: images contain incorrect pixel type` | Images not in float or uint format | Convert to float32 with SimpleITK: `sitk.Cast(image, sitk.sitkFloat32)` before placing in `imagesTr/` |
| Prediction is all background | Wrong model folder or checkpoint path | Verify `model_folder` path; check that `checkpoint_best.pth` exists; confirm dataset ID matches the trained model |
| Very slow inference (>10 min per case) | CPU inference or large patch with full mirroring | Set `device=torch.device("cuda",0)`; set `use_mirroring=False` for 4× speedup; reduce `tile_step_size` to 0.3 |

## References

- [nnU-Net GitHub](https://github.com/MIC-DKFZ/nnUNet) — official source code, installation instructions, and documentation
- [Isensee F et al. (2021) Nature Methods 18:203–211](https://doi.org/10.1038/s41592-020-01008-z) — original nnU-Net paper: "nnU-Net: a self-configuring method for deep learning-based biomedical image segmentation"
- [nnU-Net v2 documentation](https://github.com/MIC-DKFZ/nnUNet/tree/master/documentation) — migration guide, dataset format, inference API, custom trainers
- [Medical Segmentation Decathlon](http://medicaldecathlon.com/) — 10 benchmark datasets in nnU-Net-compatible format for training and validation
- [Zenodo: pretrained nnU-Net models](https://zenodo.org/record/7783116) — community-shared pretrained models for abdominal organs and other structures
