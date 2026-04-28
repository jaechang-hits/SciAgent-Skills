---
name: "simpleitk-image-registration"
description: "Register, segment, filter, resample 3D medical images (MRI, CT, microscopy) via SimpleITK Python; DICOM, NIfTI, multi-modal. Rigid/affine/deformable registration, threshold/region-growing segmentation, Gaussian/morph filtering, label stats, format conversion. Use to align volumes across timepoints/modalities, segment fluorescence, or convert DICOM→NIfTI."
license: "Apache-2.0"
---

# SimpleITK Image Registration and Analysis

## Overview

SimpleITK is a simplified, high-level interface to the Insight Toolkit (ITK) for medical image processing. It provides Python-native access to registration (rigid, affine, B-spline, Demons), segmentation (thresholding, region growing, watershed, level sets), filtering (smoothing, morphology, gradients), and resampling for 3D/4D images from MRI, CT, ultrasound, and fluorescence microscopy. SimpleITK images carry physical space metadata (spacing, origin, direction cosines) which is critical for correct anatomical interpretation and multi-modal alignment.

## When to Use

- Registering MRI volumes across timepoints (longitudinal studies) or to a standard atlas for normalization
- Segmenting cells or nuclei from fluorescence microscopy using Otsu thresholding with morphological cleanup
- Converting DICOM series (CT, MRI scanner output) to NIfTI format for downstream analysis with FSL or ANTs
- Applying pre-computed transforms to resample images to a common resolution or field of view
- Computing region statistics (volume, mean intensity, surface area) from binary label masks
- Running multi-modal registration (e.g., aligning PET to MRI) using mutual information metrics
- Use **ANTs** (via `antspyx`) instead when you need state-of-the-art diffeomorphic registration with multi-atlas label fusion for neuroimaging research; SimpleITK is better for Python-native scriptable pipelines without native dependencies
- Use **scikit-image** (`scikit-image-processing`) instead for 2D bioimage analysis with `regionprops`, morphological operations, and watershed on non-volumetric fluorescence microscopy data

## Prerequisites

- **Python packages**: `SimpleITK>=2.3`, `numpy`, `matplotlib`
- **Optional**: `SimpleITK-SimpleElastix` for additional registration algorithms (Elastix)
- **Data requirements**: DICOM series (CT/MRI), NIfTI files (.nii or .nii.gz), or any ITK-supported format (MetaImage, NRRD, PNG, TIFF stacks)
- **Environment**: Python 3.8+; no GPU required; 8 GB RAM recommended for typical 3D volumes

```bash
pip install SimpleITK numpy matplotlib

# For additional Elastix-based registration algorithms:
pip install SimpleITK-SimpleElastix
```

## Quick Start

```python
import SimpleITK as sitk

# Read a NIfTI file, apply Gaussian smoothing, and save
image = sitk.ReadImage("brain_t1.nii.gz")
print(f"Size: {image.GetSize()}, Spacing: {image.GetSpacing()}")

smoothed = sitk.SmoothingRecursiveGaussian(image, sigma=1.0)

# Otsu threshold to create a brain mask
mask = sitk.OtsuThreshold(smoothed, 0, 1, 200)
print(f"Voxels in mask: {sitk.GetArrayFromImage(mask).sum()}")

sitk.WriteImage(mask, "brain_mask.nii.gz")
print("Saved brain_mask.nii.gz")
```

## Core API

### Module 1: Image I/O

Reading and writing DICOM series, NIfTI, and other formats with full metadata preservation.

```python
import SimpleITK as sitk

# Read a NIfTI file
image = sitk.ReadImage("subject_t1.nii.gz", sitk.sitkFloat32)
print(f"Size (x,y,z): {image.GetSize()}")
print(f"Spacing (mm): {image.GetSpacing()}")
print(f"Origin:       {image.GetOrigin()}")
print(f"Direction:    {image.GetDirection()}")

# Write as compressed NIfTI
sitk.WriteImage(image, "output.nii.gz")
print("Saved output.nii.gz")
```

```python
import SimpleITK as sitk
import os

# Read a DICOM series from a directory
dicom_dir = "DICOM/series_001/"
series_ids = sitk.ImageSeriesReader.GetGDCMSeriesIDs(dicom_dir)
print(f"Found {len(series_ids)} DICOM series")

reader = sitk.ImageSeriesReader()
reader.SetFileNames(sitk.ImageSeriesReader.GetGDCMSeriesFileNames(dicom_dir, series_ids[0]))
reader.MetaDataDictionaryArrayUpdateOn()
reader.LoadPrivateTagsOn()
volume = reader.Execute()

print(f"DICOM volume size: {volume.GetSize()}")
print(f"Pixel spacing:     {volume.GetSpacing()}")

# Save the 3D volume as NIfTI
sitk.WriteImage(volume, "ct_volume.nii.gz")
print("DICOM series → ct_volume.nii.gz")
```

### Module 2: Image Filtering

Gaussian smoothing, median filtering, gradient magnitude, and edge-preserving filters.

```python
import SimpleITK as sitk
import numpy as np

image = sitk.ReadImage("fluorescence_cells.nii.gz", sitk.sitkFloat32)

# Gaussian smoothing — reduces noise before segmentation
smoothed = sitk.SmoothingRecursiveGaussian(image, sigma=1.5)

# Median filter — removes salt-and-pepper noise (preserves edges better than Gaussian)
median_filtered = sitk.Median(image, [3, 3, 3])

# Gradient magnitude — highlights edges/boundaries
gradient = sitk.GradientMagnitude(smoothed)

arr = sitk.GetArrayFromImage(gradient)
print(f"Gradient range: {arr.min():.2f} – {arr.max():.2f}")
print(f"Mean gradient:  {arr.mean():.4f}")

sitk.WriteImage(smoothed, "smoothed.nii.gz")
sitk.WriteImage(gradient, "gradient.nii.gz")
```

```python
import SimpleITK as sitk

image = sitk.ReadImage("ct_volume.nii.gz", sitk.sitkFloat32)

# Normalize intensity to [0, 1] range using RescaleIntensity
rescaled = sitk.RescaleIntensity(image, outputMinimum=0.0, outputMaximum=1.0)

# Histogram equalization — improves contrast for registration
equalized = sitk.AdaptiveHistogramEqualization(rescaled)

# N4 bias field correction for MRI (removes B1 field inhomogeneity)
# Cast to float32 for bias correction
image_f32 = sitk.Cast(image, sitk.sitkFloat32)
mask_otsu = sitk.OtsuThreshold(image_f32, 0, 1, 200)
corrected = sitk.N4BiasFieldCorrection(image_f32, mask_otsu)

print("Applied: rescaling, histogram equalization, N4 bias correction")
sitk.WriteImage(corrected, "bias_corrected.nii.gz")
```

### Module 3: Image Registration

Rigid, affine, and deformable (B-spline, Demons) registration using `ImageRegistrationMethod`.

```python
import SimpleITK as sitk

# Load fixed (reference/atlas) and moving (subject to align) images
fixed = sitk.ReadImage("atlas_t1.nii.gz", sitk.sitkFloat32)
moving = sitk.ReadImage("subject_t1.nii.gz", sitk.sitkFloat32)

# Set up rigid registration
registration_method = sitk.ImageRegistrationMethod()

# Similarity metric: Mattes mutual information (works for same-modality)
registration_method.SetMetricAsMattesMutualInformation(numberOfHistogramBins=50)
registration_method.SetMetricSamplingStrategy(registration_method.RANDOM)
registration_method.SetMetricSamplingPercentage(0.01)

# Optimizer: gradient descent with line search
registration_method.SetOptimizerAsGradientDescent(
    learningRate=1.0, numberOfIterations=100,
    convergenceMinimumValue=1e-6, convergenceWindowSize=10
)
registration_method.SetOptimizerScalesFromPhysicalShift()

# Multi-resolution pyramid: 3 levels → faster convergence
registration_method.SetShrinkFactorsPerLevel(shrinkFactors=[4, 2, 1])
registration_method.SetSmoothingSigmasPerLevel(smoothingSigmas=[2, 1, 0])
registration_method.SmoothingSigmasAreSpecifiedInPhysicalUnitsOn()

# Initialize with center of geometry
initial_transform = sitk.CenteredTransformInitializer(
    fixed, moving,
    sitk.Euler3DTransform(),
    sitk.CenteredTransformInitializerFilter.GEOMETRY
)
registration_method.SetInitialTransform(initial_transform, inPlace=False)
registration_method.SetInterpolator(sitk.sitkLinear)

# Execute registration
final_transform = registration_method.Execute(fixed, moving)
print(f"Optimizer stop: {registration_method.GetOptimizerStopConditionDescription()}")
print(f"Final metric:   {registration_method.GetMetricValue():.4f}")

# Apply transform and save
resampled = sitk.Resample(
    moving, fixed, final_transform,
    sitk.sitkLinear, 0.0, moving.GetPixelID()
)
sitk.WriteImage(resampled, "subject_registered.nii.gz")
sitk.WriteTransform(final_transform, "rigid_transform.tfm")
print("Saved: subject_registered.nii.gz, rigid_transform.tfm")
```

```python
import SimpleITK as sitk

# Deformable B-spline registration for non-linear alignment
fixed = sitk.ReadImage("atlas_t1.nii.gz", sitk.sitkFloat32)
moving = sitk.ReadImage("subject_t1.nii.gz", sitk.sitkFloat32)

# Start with affine pre-registration
affine_method = sitk.ImageRegistrationMethod()
affine_method.SetMetricAsMattesMutualInformation(numberOfHistogramBins=50)
affine_method.SetMetricSamplingStrategy(affine_method.RANDOM)
affine_method.SetMetricSamplingPercentage(0.01)
affine_method.SetOptimizerAsGradientDescent(
    learningRate=1.0, numberOfIterations=100,
    convergenceMinimumValue=1e-6, convergenceWindowSize=10
)
affine_method.SetShrinkFactorsPerLevel([4, 2, 1])
affine_method.SetSmoothingSigmasPerLevel([2, 1, 0])
affine_method.SmoothingSigmasAreSpecifiedInPhysicalUnitsOn()
affine_init = sitk.CenteredTransformInitializer(
    fixed, moving, sitk.AffineTransform(3),
    sitk.CenteredTransformInitializerFilter.GEOMETRY
)
affine_method.SetInitialTransform(affine_init, inPlace=False)
affine_method.SetInterpolator(sitk.sitkLinear)
affine_transform = affine_method.Execute(fixed, moving)
print(f"Affine complete: metric = {affine_method.GetMetricValue():.4f}")

# B-spline deformable refinement
bspline_method = sitk.ImageRegistrationMethod()
bspline_method.SetMetricAsMattesMutualInformation(numberOfHistogramBins=50)
bspline_method.SetMetricSamplingStrategy(bspline_method.RANDOM)
bspline_method.SetMetricSamplingPercentage(0.01)
bspline_method.SetOptimizerAsGradientDescent(
    learningRate=0.5, numberOfIterations=50,
    convergenceMinimumValue=1e-6, convergenceWindowSize=10
)
bspline_method.SetShrinkFactorsPerLevel([2, 1])
bspline_method.SetSmoothingSigmasPerLevel([1, 0])
bspline_method.SmoothingSigmasAreSpecifiedInPhysicalUnitsOn()

mesh_size = [8] * fixed.GetDimension()
bspline_init = sitk.BSplineTransformInitializer(image1=fixed, transformDomainMeshSize=mesh_size, order=3)
composite = sitk.CompositeTransform(3)
composite.AddTransform(affine_transform)
composite.AddTransform(bspline_init)
bspline_method.SetInitialTransform(composite, inPlace=True)
bspline_method.SetInterpolator(sitk.sitkLinear)

deformable_transform = bspline_method.Execute(fixed, moving)
resampled = sitk.Resample(moving, fixed, deformable_transform, sitk.sitkLinear, 0.0)
sitk.WriteImage(resampled, "subject_deformable_registered.nii.gz")
print("Saved: subject_deformable_registered.nii.gz")
```

### Module 4: Segmentation

Otsu thresholding, region growing, watershed, and morphological post-processing.

```python
import SimpleITK as sitk
import numpy as np

# Read fluorescence microscopy image
image = sitk.ReadImage("cells_gfp.nii.gz", sitk.sitkFloat32)

# Gaussian smoothing before thresholding
smoothed = sitk.SmoothingRecursiveGaussian(image, sigma=1.0)

# Otsu thresholding: automatically finds optimal foreground/background threshold
# Returns binary label image: 1=foreground (cells), 0=background
binary = sitk.OtsuThreshold(smoothed, insideValue=0, outsideValue=1, numberOfHistogramBins=200)

# Count segmented voxels
arr = sitk.GetArrayFromImage(binary)
n_foreground = arr.sum()
total = arr.size
print(f"Foreground: {n_foreground} voxels ({100*n_foreground/total:.1f}%)")

sitk.WriteImage(binary, "cells_binary_otsu.nii.gz")
print("Saved: cells_binary_otsu.nii.gz")
```

```python
import SimpleITK as sitk

image = sitk.ReadImage("mri_brain.nii.gz", sitk.sitkFloat32)
smoothed = sitk.SmoothingRecursiveGaussian(image, sigma=0.5)

# Region growing from a seed point: ConnectedThreshold
# Seeds must be inside the region of interest; lower/upper bound in image intensity units
seed = (128, 128, 64)   # (x, y, z) in image coordinates
lower_threshold = 50.0
upper_threshold = 200.0
region_grown = sitk.ConnectedThreshold(
    smoothed,
    seedList=[seed],
    lower=lower_threshold,
    upper=upper_threshold,
    replaceValue=1
)
print(f"Region growing: {sitk.GetArrayFromImage(region_grown).sum()} voxels segmented")

# ConfidenceConnected: adaptive thresholding based on neighborhood statistics
confidence_seg = sitk.ConfidenceConnected(
    smoothed,
    seedList=[seed],
    numberOfIterations=2,
    multiplier=2.5,       # number of standard deviations from mean
    initialNeighborhoodRadius=2,
    replaceValue=1
)
print(f"Confidence connected: {sitk.GetArrayFromImage(confidence_seg).sum()} voxels")

sitk.WriteImage(region_grown, "region_grown.nii.gz")
sitk.WriteImage(confidence_seg, "confidence_seg.nii.gz")
```

```python
import SimpleITK as sitk

# Morphological operations for binary mask cleanup
binary = sitk.ReadImage("cells_binary_otsu.nii.gz")

# Fill small holes
filled = sitk.BinaryFillhole(binary)

# Erosion: remove thin protrusions and separate touching objects
eroded = sitk.BinaryErode(filled, kernelRadius=(2, 2, 1), kernelType=sitk.sitkBall)

# Dilation: restore true boundary after erosion
dilated = sitk.BinaryDilate(eroded, kernelRadius=(2, 2, 1), kernelType=sitk.sitkBall)

# Opening = erosion + dilation: removes small objects
opened = sitk.BinaryMorphologicalOpening(binary, kernelRadius=(1, 1, 1), kernelType=sitk.sitkBall)

# Connected component labeling: assign unique integer to each object
labeled = sitk.ConnectedComponent(opened)
n_objects = sitk.GetArrayFromImage(labeled).max()
print(f"Connected components (objects): {n_objects}")

# Remove objects smaller than 100 voxels
relabeled = sitk.RelabelComponent(labeled, minimumObjectSize=100)
n_kept = sitk.GetArrayFromImage(relabeled).max()
print(f"Objects remaining after size filter: {n_kept}")

sitk.WriteImage(relabeled, "cells_labeled.nii.gz")
```

### Module 5: Resampling and Transform Application

Applying transforms, resampling to a reference grid, and converting between array and image representations.

```python
import SimpleITK as sitk
import numpy as np

# Resample moving image to match reference grid
reference = sitk.ReadImage("reference_volume.nii.gz")
moving = sitk.ReadImage("subject_volume.nii.gz")

# Load a pre-computed transform
transform = sitk.ReadTransform("rigid_transform.tfm")

# Resample with linear interpolation (use nearest neighbor for label images)
resampled = sitk.Resample(
    moving,
    reference,
    transform,
    sitk.sitkLinear,    # interpolator; use sitk.sitkNearestNeighbor for labels
    0.0,                # default pixel value for regions outside the moving image
    moving.GetPixelID()
)
print(f"Resampled size: {resampled.GetSize()} (matches reference: {reference.GetSize()})")
sitk.WriteImage(resampled, "resampled_to_reference.nii.gz")
```

```python
import SimpleITK as sitk
import numpy as np

# Convert between SimpleITK image and NumPy array
image = sitk.ReadImage("ct_volume.nii.gz", sitk.sitkFloat32)

# SimpleITK uses (x, y, z) ordering; NumPy gets (z, y, x) ordering
arr = sitk.GetArrayFromImage(image)
print(f"NumPy array shape (z,y,x): {arr.shape}")
print(f"Value range: {arr.min():.1f} – {arr.max():.1f}")

# Apply NumPy operations
clipped = np.clip(arr, -1000, 3000)   # CT Hounsfield unit clipping
normalized = (clipped - clipped.mean()) / clipped.std()

# Convert back to SimpleITK image (preserving spatial metadata)
out_image = sitk.GetImageFromArray(normalized)
out_image.CopyInformation(image)   # copy spacing, origin, direction from original
print(f"Output size: {out_image.GetSize()}, Spacing: {out_image.GetSpacing()}")

# Resample to isotropic 1mm spacing
new_spacing = [1.0, 1.0, 1.0]
orig_spacing = image.GetSpacing()
orig_size = image.GetSize()
new_size = [
    int(round(orig_size[i] * orig_spacing[i] / new_spacing[i]))
    for i in range(3)
]
resampled_iso = sitk.Resample(
    image,
    new_size,
    sitk.Transform(),         # identity transform
    sitk.sitkLinear,
    image.GetOrigin(),
    new_spacing,
    image.GetDirection(),
    0.0,
    image.GetPixelID()
)
print(f"Isotropic resampled size: {resampled_iso.GetSize()}")
sitk.WriteImage(resampled_iso, "isotropic_1mm.nii.gz")
```

### Module 6: Statistics and Measurement

Label shape statistics (volume, surface area, centroid, bounding box) and intensity statistics per region.

```python
import SimpleITK as sitk
import pandas as pd

# Load intensity image and binary label mask
intensity = sitk.ReadImage("fluorescence_cells.nii.gz", sitk.sitkFloat32)
labels = sitk.ReadImage("cells_labeled.nii.gz", sitk.sitkUInt32)

# Shape statistics: geometric measurements per label
shape_filter = sitk.LabelShapeStatisticsImageFilter()
shape_filter.ComputeOrientedBoundingBoxOn()
shape_filter.Execute(labels)

label_ids = shape_filter.GetLabels()
print(f"Number of labeled objects: {len(label_ids)}")

rows = []
for lbl in label_ids:
    rows.append({
        "label": lbl,
        "volume_voxels": shape_filter.GetNumberOfPixels(lbl),
        "volume_mm3": shape_filter.GetPhysicalSize(lbl),
        "centroid_x": shape_filter.GetCentroid(lbl)[0],
        "centroid_y": shape_filter.GetCentroid(lbl)[1],
        "centroid_z": shape_filter.GetCentroid(lbl)[2],
        "elongation": shape_filter.GetElongation(lbl),
        "roundness": shape_filter.GetRoundness(lbl),
    })

shape_df = pd.DataFrame(rows)
print(shape_df.head())
print(f"\nMean volume: {shape_df['volume_mm3'].mean():.1f} mm³")
shape_df.to_csv("cell_shape_stats.csv", index=False)
print("Saved: cell_shape_stats.csv")
```

```python
import SimpleITK as sitk
import pandas as pd

intensity = sitk.ReadImage("fluorescence_cells.nii.gz", sitk.sitkFloat32)
labels = sitk.ReadImage("cells_labeled.nii.gz", sitk.sitkUInt32)

# Intensity statistics per label
intensity_filter = sitk.LabelIntensityStatisticsImageFilter()
intensity_filter.Execute(labels, intensity)

label_ids = intensity_filter.GetLabels()
rows = []
for lbl in label_ids:
    rows.append({
        "label": lbl,
        "mean_intensity": intensity_filter.GetMean(lbl),
        "std_intensity": intensity_filter.GetSigma(lbl),
        "min_intensity": intensity_filter.GetMinimum(lbl),
        "max_intensity": intensity_filter.GetMaximum(lbl),
        "median_intensity": intensity_filter.GetMedian(lbl),
        "sum_intensity": intensity_filter.GetSum(lbl),
    })

intensity_df = pd.DataFrame(rows)
print(intensity_df.describe().round(2))
intensity_df.to_csv("cell_intensity_stats.csv", index=False)
print(f"\nSaved: cell_intensity_stats.csv ({len(rows)} cells)")
```

## Key Concepts

### Physical Space vs. Pixel Space

SimpleITK images store spatial metadata (spacing in mm, origin, direction cosines) that defines how pixel coordinates map to physical (world) coordinates. Operations like `Resample` and registration work in physical space, ensuring anatomically correct alignment even when images have different voxel sizes or orientations. Always use `CopyInformation()` when creating output images from NumPy arrays to preserve physical metadata.

```python
import SimpleITK as sitk
import numpy as np

image = sitk.ReadImage("mri.nii.gz")
print(f"Pixel space size:     {image.GetSize()}")       # (x, y, z) in voxels
print(f"Physical spacing mm:  {image.GetSpacing()}")    # mm per voxel
print(f"Physical origin mm:   {image.GetOrigin()}")     # world coords of first voxel
print(f"Direction cosines:    {image.GetDirection()}")  # patient orientation matrix

# Convert pixel index to physical point
pixel_idx = (64, 64, 32)
physical_pt = image.TransformIndexToPhysicalPoint(pixel_idx)
print(f"Pixel {pixel_idx} → physical {physical_pt}")

# NumPy array has REVERSED axis order: (z, y, x)
arr = sitk.GetArrayFromImage(image)
print(f"NumPy shape: {arr.shape}")  # (z, y, x)
```

### Transform Composition

SimpleITK transforms can be composed using `CompositeTransform` to apply a sequence of transformations (e.g., affine pre-alignment followed by deformable B-spline refinement). Transforms are applied in the order they were added when calling `Resample`, enabling modular pipeline construction.

## Common Workflows

### Workflow 1: Fluorescence Microscopy Cell Segmentation

**Goal**: Segment individual cells from a 3D fluorescence microscopy volume, apply morphological cleanup, and extract per-cell measurements.

```python
import SimpleITK as sitk
import pandas as pd
import numpy as np

# 1. Load fluorescence volume
image = sitk.ReadImage("cells_gfp.nii.gz", sitk.sitkFloat32)
print(f"Image size: {image.GetSize()}, Spacing: {image.GetSpacing()}")

# 2. Denoise with Gaussian smoothing
smoothed = sitk.SmoothingRecursiveGaussian(image, sigma=0.8)

# 3. Otsu threshold to get binary foreground mask
binary = sitk.OtsuThreshold(smoothed, insideValue=0, outsideValue=1, numberOfHistogramBins=200)
n_fg = sitk.GetArrayFromImage(binary).sum()
print(f"Foreground voxels after Otsu: {n_fg}")

# 4. Morphological cleanup
filled = sitk.BinaryFillhole(binary)
opened = sitk.BinaryMorphologicalOpening(filled, kernelRadius=(1, 1, 1))

# 5. Label individual connected components (cells)
labeled = sitk.ConnectedComponent(opened)
relabeled = sitk.RelabelComponent(labeled, minimumObjectSize=200)
n_cells = int(sitk.GetArrayFromImage(relabeled).max())
print(f"Detected cells (>200 voxels): {n_cells}")

# 6. Compute shape statistics
shape_filter = sitk.LabelShapeStatisticsImageFilter()
shape_filter.Execute(relabeled)

intensity_filter = sitk.LabelIntensityStatisticsImageFilter()
intensity_filter.Execute(relabeled, image)

rows = []
for lbl in shape_filter.GetLabels():
    rows.append({
        "cell_id": lbl,
        "volume_mm3": shape_filter.GetPhysicalSize(lbl),
        "roundness": shape_filter.GetRoundness(lbl),
        "elongation": shape_filter.GetElongation(lbl),
        "mean_gfp_intensity": intensity_filter.GetMean(lbl),
        "total_gfp_intensity": intensity_filter.GetSum(lbl),
    })

df = pd.DataFrame(rows)
print(df.describe().round(3))

# 7. Save outputs
sitk.WriteImage(relabeled, "cells_labeled.nii.gz")
df.to_csv("cell_measurements.csv", index=False)
print(f"\nSaved: cells_labeled.nii.gz, cell_measurements.csv ({n_cells} cells)")
```

### Workflow 2: MRI Brain Atlas Registration

**Goal**: Register a subject's T1 MRI to a standard brain atlas using rigid + affine registration, then transfer atlas labels to subject space.

```python
import SimpleITK as sitk
import numpy as np

# 1. Load atlas (fixed) and subject (moving) T1 MRI
atlas_t1 = sitk.ReadImage("mni152_t1.nii.gz", sitk.sitkFloat32)
subject_t1 = sitk.ReadImage("subject_t1.nii.gz", sitk.sitkFloat32)
atlas_labels = sitk.ReadImage("mni152_labels.nii.gz", sitk.sitkUInt16)
print(f"Atlas size: {atlas_t1.GetSize()}, Subject size: {subject_t1.GetSize()}")

# 2. Normalize intensities for better registration convergence
atlas_norm = sitk.RescaleIntensity(atlas_t1, 0.0, 1.0)
subject_norm = sitk.RescaleIntensity(subject_t1, 0.0, 1.0)

# 3. Initialize with center-of-geometry alignment
initial_transform = sitk.CenteredTransformInitializer(
    atlas_norm, subject_norm,
    sitk.AffineTransform(3),
    sitk.CenteredTransformInitializerFilter.GEOMETRY
)

# 4. Configure and run affine registration
reg = sitk.ImageRegistrationMethod()
reg.SetMetricAsMattesMutualInformation(numberOfHistogramBins=50)
reg.SetMetricSamplingStrategy(reg.RANDOM)
reg.SetMetricSamplingPercentage(0.01)
reg.SetOptimizerAsGradientDescent(
    learningRate=1.0, numberOfIterations=200,
    convergenceMinimumValue=1e-6, convergenceWindowSize=10
)
reg.SetOptimizerScalesFromPhysicalShift()
reg.SetShrinkFactorsPerLevel([4, 2, 1])
reg.SetSmoothingSigmasPerLevel([2, 1, 0])
reg.SmoothingSigmasAreSpecifiedInPhysicalUnitsOn()
reg.SetInitialTransform(initial_transform, inPlace=False)
reg.SetInterpolator(sitk.sitkLinear)

final_transform = reg.Execute(atlas_norm, subject_norm)
print(f"Registration metric: {reg.GetMetricValue():.4f}")
print(f"Optimizer: {reg.GetOptimizerStopConditionDescription()}")

# 5. Apply transform to subject T1 (aligned to atlas space)
subject_registered = sitk.Resample(
    subject_t1, atlas_t1, final_transform,
    sitk.sitkLinear, 0.0, subject_t1.GetPixelID()
)

# 6. Invert transform to bring atlas labels to subject space
inverse_transform = final_transform.GetInverse()
labels_in_subject_space = sitk.Resample(
    atlas_labels, subject_t1, inverse_transform,
    sitk.sitkNearestNeighbor, 0, atlas_labels.GetPixelID()
)

# 7. Save results
sitk.WriteImage(subject_registered, "subject_in_atlas_space.nii.gz")
sitk.WriteImage(labels_in_subject_space, "atlas_labels_in_subject_space.nii.gz")
sitk.WriteTransform(final_transform, "subject_to_atlas.tfm")

n_labels = int(sitk.GetArrayFromImage(labels_in_subject_space).max())
print(f"Transferred {n_labels} atlas regions to subject space")
print("Saved: subject_in_atlas_space.nii.gz, atlas_labels_in_subject_space.nii.gz")
```

### Workflow 3: DICOM Series to NIfTI Batch Conversion

**Goal**: Convert multiple DICOM series from a scanner directory to NIfTI with isotropic resampling.

```python
import SimpleITK as sitk
from pathlib import Path

def convert_dicom_series(dicom_dir: str, output_path: str, target_spacing_mm: float = 1.0) -> dict:
    """Convert a DICOM series directory to NIfTI with optional isotropic resampling."""
    series_ids = sitk.ImageSeriesReader.GetGDCMSeriesIDs(dicom_dir)
    if not series_ids:
        return {"error": f"No DICOM series in {dicom_dir}"}

    reader = sitk.ImageSeriesReader()
    reader.SetFileNames(sitk.ImageSeriesReader.GetGDCMSeriesFileNames(dicom_dir, series_ids[0]))
    volume = reader.Execute()
    orig_size = volume.GetSize()
    orig_spacing = volume.GetSpacing()

    # Resample to isotropic voxels
    new_spacing = [target_spacing_mm] * 3
    new_size = [int(round(orig_size[i] * orig_spacing[i] / target_spacing_mm)) for i in range(3)]
    resampled = sitk.Resample(
        volume, new_size, sitk.Transform(),
        sitk.sitkLinear, volume.GetOrigin(),
        new_spacing, volume.GetDirection(),
        0.0, volume.GetPixelID()
    )

    sitk.WriteImage(resampled, output_path)
    return {
        "input": dicom_dir, "output": output_path,
        "orig_size": orig_size, "orig_spacing": orig_spacing,
        "new_size": new_size, "n_series": len(series_ids)
    }

# Batch convert all subject directories
input_root = Path("DICOM_data/")
output_root = Path("NIfTI_converted/")
output_root.mkdir(exist_ok=True)

results = []
for subject_dir in sorted(input_root.iterdir()):
    if subject_dir.is_dir():
        out_file = output_root / f"{subject_dir.name}_t1.nii.gz"
        info = convert_dicom_series(str(subject_dir), str(out_file), target_spacing_mm=1.0)
        results.append(info)
        print(f"  {subject_dir.name}: {info.get('orig_size')} → {info.get('new_size')}")

print(f"\nConverted {len(results)} subjects to {output_root}/")
```

## Key Parameters

| Parameter | Module | Default | Range / Options | Effect |
|-----------|--------|---------|-----------------|--------|
| `sigma` | SmoothingRecursiveGaussian | — | `0.5`–`5.0` mm | Gaussian smoothing width; larger values blur more and reduce noise |
| `numberOfHistogramBins` | OtsuThreshold, MutualInfo | `128` | `50`–`256` | Histogram resolution for threshold/metric calculation |
| `numberOfIterations` | ImageRegistrationMethod | `100` | `50`–`500` | Max optimizer steps; increase for complex/fine registration |
| `learningRate` | GradientDescent optimizer | `1.0` | `0.01`–`2.0` | Step size per optimizer iteration; too large causes divergence |
| `shrinkFactors` | Multi-resolution pyramid | `[4,2,1]` | lists of `[8,4,2,1]` | Image downsampling per resolution level; larger = faster but coarser |
| `minimumObjectSize` | RelabelComponent | `0` | `1`–`10000` voxels | Remove connected components smaller than this size in voxels |
| `kernelRadius` | BinaryErode/Dilate | `(1,1,1)` | `(1,1,1)` – `(5,5,5)` | Morphological kernel radius per axis in voxels |
| `interpolator` | Resample | `sitk.sitkLinear` | `sitkLinear`, `sitkNearestNeighbor`, `sitkBSpline` | Interpolation method; use NearestNeighbor for integer label images |
| `multiplier` | ConfidenceConnected | `2.5` | `1.5`–`4.0` | Number of std devs from neighborhood mean to accept a voxel |
| `meshSize` | BSplineTransformInitializer | `[8]*ndim` | `[4]*ndim` – `[20]*ndim` | B-spline control point grid; larger = more deformation degrees of freedom |

## Best Practices

1. **Always cast to float32 before registration or filtering**: Many ITK filters expect float input. Integers from DICOM (typically `sitk.sitkInt16`) can cause silent errors or precision loss.
   ```python
   image = sitk.ReadImage("ct.nii.gz", sitk.sitkFloat32)   # explicit cast at load time
   # Or: image_f32 = sitk.Cast(image, sitk.sitkFloat32)
   ```

2. **Use `CopyInformation()` when creating images from NumPy arrays**: Without this, the output image loses physical spacing and origin, making it impossible to overlay with the source in a viewer.
   ```python
   arr = sitk.GetArrayFromImage(image)
   modified = some_numpy_operation(arr)
   out = sitk.GetImageFromArray(modified)
   out.CopyInformation(image)  # preserve spacing, origin, direction
   ```

3. **Use `sitkNearestNeighbor` for label/mask resampling**: Linear or B-spline interpolation on integer label images creates fractional label values that corrupt the mask. Always use nearest-neighbor for binary masks and multi-label segmentations.

4. **Run multi-resolution registration for speed and robustness**: Set `SetShrinkFactorsPerLevel([4,2,1])` and `SetSmoothingSigmasPerLevel([2,1,0])` to prevent the optimizer from getting trapped in local minima on large 3D volumes.

5. **Validate registration visually with checkerboard comparison**: Before trusting a registration result, verify alignment using `sitk.CheckerBoard` between fixed and registered-moving.
   ```python
   checker = sitk.CheckerBoard(fixed, resampled_moving, [5, 5, 5])
   sitk.WriteImage(checker, "registration_checker.nii.gz")
   ```

## Common Recipes

### Recipe: Multi-Modal Registration (MRI to CT)

When to use: Aligning different imaging modalities (e.g., PET to MRI, CT to MRI) where intensities are incompatible, requiring mutual information as metric.

```python
import SimpleITK as sitk

# Load images from different modalities
ct = sitk.ReadImage("patient_ct.nii.gz", sitk.sitkFloat32)
mri = sitk.ReadImage("patient_mri.nii.gz", sitk.sitkFloat32)

# Mutual information metric handles multi-modal intensity relationships
reg = sitk.ImageRegistrationMethod()
reg.SetMetricAsMattesMutualInformation(numberOfHistogramBins=100)
reg.SetMetricSamplingStrategy(reg.RANDOM)
reg.SetMetricSamplingPercentage(0.05)
reg.SetOptimizerAsGradientDescent(
    learningRate=1.0, numberOfIterations=150,
    convergenceMinimumValue=1e-6, convergenceWindowSize=10
)
reg.SetOptimizerScalesFromPhysicalShift()
reg.SetShrinkFactorsPerLevel([4, 2, 1])
reg.SetSmoothingSigmasPerLevel([2, 1, 0])
reg.SmoothingSigmasAreSpecifiedInPhysicalUnitsOn()
initial = sitk.CenteredTransformInitializer(
    ct, mri, sitk.AffineTransform(3),
    sitk.CenteredTransformInitializerFilter.GEOMETRY
)
reg.SetInitialTransform(initial, inPlace=False)
reg.SetInterpolator(sitk.sitkLinear)

transform = reg.Execute(ct, mri)
mri_aligned = sitk.Resample(mri, ct, transform, sitk.sitkLinear, 0.0)
sitk.WriteImage(mri_aligned, "mri_aligned_to_ct.nii.gz")
print(f"Multi-modal registration complete. Metric: {reg.GetMetricValue():.4f}")
```

### Recipe: Batch Apply Transform to Label Masks

When to use: After registering one image, apply the same transform to segmentation masks or atlas labels (using nearest-neighbor interpolation).

```python
import SimpleITK as sitk
from pathlib import Path

# Load the transform computed during registration
transform = sitk.ReadTransform("subject_to_atlas.tfm")
reference = sitk.ReadImage("atlas_t1.nii.gz")

# Apply to all label files in a directory
label_dir = Path("subject_labels/")
output_dir = Path("atlas_labels/")
output_dir.mkdir(exist_ok=True)

for label_file in sorted(label_dir.glob("*.nii.gz")):
    label = sitk.ReadImage(str(label_file), sitk.sitkUInt16)
    registered_label = sitk.Resample(
        label, reference, transform,
        sitk.sitkNearestNeighbor,    # critical: integer labels need nearest-neighbor
        0, label.GetPixelID()
    )
    out_path = output_dir / label_file.name
    sitk.WriteImage(registered_label, str(out_path))
    n_labels = int(sitk.GetArrayFromImage(registered_label).max())
    print(f"  {label_file.name}: {n_labels} labels → {out_path.name}")

print(f"Batch transform applied to {len(list(label_dir.glob('*.nii.gz')))} files")
```

### Recipe: Demons Deformable Registration

When to use: Fast deformable registration for images of the same modality with small deformations (e.g., longitudinal brain MRI with slight atrophy).

```python
import SimpleITK as sitk

fixed = sitk.ReadImage("baseline_mri.nii.gz", sitk.sitkFloat32)
moving = sitk.ReadImage("followup_mri.nii.gz", sitk.sitkFloat32)

# Normalize intensities
fixed_n = sitk.RescaleIntensity(fixed, 0.0, 1.0)
moving_n = sitk.RescaleIntensity(moving, 0.0, 1.0)

# Demons registration filter
demons = sitk.DemonsRegistrationFilter()
demons.SetNumberOfIterations(50)
demons.SetStandardDeviations(1.0)   # displacement field smoothing

displacement_field = demons.Execute(fixed_n, moving_n)
print(f"Demons complete: RMS change = {demons.GetRMSChange():.6f}")

# Apply displacement field transform
displacement_transform = sitk.DisplacementFieldTransform(displacement_field)
warped = sitk.Resample(moving, fixed, displacement_transform, sitk.sitkLinear, 0.0)

sitk.WriteImage(warped, "followup_registered_demons.nii.gz")
sitk.WriteImage(
    sitk.Cast(sitk.VectorMagnitude(displacement_field), sitk.sitkFloat32),
    "deformation_magnitude.nii.gz"
)
print("Saved: followup_registered_demons.nii.gz, deformation_magnitude.nii.gz")
```

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| `TypeError: in method 'ImageRegistrationMethod_Execute'` | Image pixel type is not float | Cast to float32 before registration: `sitk.Cast(image, sitk.sitkFloat32)` |
| Registration diverges (metric increases) | Learning rate too high or images not pre-aligned | Reduce `learningRate` to 0.1; use `CenteredTransformInitializer` for initial alignment; check that images overlap |
| Label image has fractional values after resample | Wrong interpolator used for mask | Set interpolator to `sitk.sitkNearestNeighbor` when resampling integer label images |
| `RuntimeError: Exception thrown in SimpleITK ReadImage` | Unsupported format or corrupt DICOM | Verify file with `dcmdump`; for DICOM series use `ImageSeriesReader.GetGDCMSeriesFileNames()` |
| N4 bias correction very slow | Large image or too many iterations | Downsample first: resample to 2mm iso before correction, then apply transform to original-resolution image |
| Connected component labels too many or too few | Object size threshold wrong or insufficient preprocessing | Adjust `minimumObjectSize` in `RelabelComponent`; increase Gaussian sigma to merge touching objects |
| NumPy array shape does not match expected (z,y,x) | Axis ordering confusion | SimpleITK images are (x,y,z); `GetArrayFromImage()` returns (z,y,x) NumPy arrays; use `arr.transpose(2,1,0)` to convert |
| Otsu threshold segments too much background | Background is bright (e.g., confocal reflection artifacts) | Use `sitk.OtsuMultipleThresholds` with `numberOfThresholds=2`; or apply a foreground mask before thresholding |

## Related Skills

- **cellpose-cell-segmentation** — deep learning cell segmentation from fluorescence microscopy; use when classical thresholding fails on heterogeneous staining or touching cells
- **scikit-image-processing** — 2D image analysis with `regionprops`, `watershed`, and filters; prefer for non-volumetric 2D microscopy analysis
- **napari-image-viewer** — interactive visualization of 3D volumes and label masks; use alongside SimpleITK for visual inspection of registration and segmentation results
- **pydicom-medical-imaging** — direct DICOM tag access, anonymization, and metadata editing; use alongside SimpleITK which handles volume reconstruction but not PHI management
- **nnunet-segmentation** — automated deep learning segmentation for medical images; use when SimpleITK classical segmentation is insufficient for complex anatomical structures

## References

- [SimpleITK documentation](https://simpleitk.readthedocs.io/en/master/) — complete API reference and Jupyter notebook tutorials
- [SimpleITK GitHub](https://github.com/SimpleITK/SimpleITK) — source code, examples, and issue tracker
- [SimpleITK Notebooks](https://github.com/InsightSoftwareConsortium/SimpleITK-Notebooks) — 50+ Jupyter notebooks covering registration, segmentation, and I/O
- [Lowekamp BC et al. (2013) Front Neuroinform](https://doi.org/10.3389/fninf.2013.00045) — SimpleITK original paper describing design and capabilities
- [Yaniv Z et al. (2018) Frontiers in Neuroinformatics](https://doi.org/10.3389/fninf.2018.00008) — SimpleITK for the biomedical image processing community
