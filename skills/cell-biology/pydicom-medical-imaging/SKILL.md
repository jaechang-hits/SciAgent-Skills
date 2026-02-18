---
name: "pydicom-medical-imaging"
description: "Pure Python DICOM library for medical imaging (CT, MRI, X-ray, ultrasound). Read/write DICOM files, extract pixel data as NumPy arrays, access/modify metadata tags, apply windowing (VOI LUT), anonymize PHI, build DICOM from scratch, process series into 3D volumes. For whole-slide pathology images use histolab; for NIfTI neuroimaging use nibabel."
license: MIT
---

# Pydicom Medical Imaging

## Overview

Pydicom is a pure Python library for reading, writing, and modifying DICOM (Digital Imaging and Communications in Medicine) files. It provides access to DICOM metadata tags and pixel data as NumPy arrays, supporting CT, MRI, X-ray, ultrasound, and other medical imaging modalities. The library handles compressed and uncompressed transfer syntaxes with optional codec plugins.

## When to Use

- Reading DICOM files and extracting metadata (patient info, study parameters, imaging settings)
- Extracting pixel data from DICOM images for analysis or visualization
- Converting DICOM images to standard formats (PNG, JPEG, TIFF)
- Anonymizing DICOM files by removing Protected Health Information (PHI)
- Modifying DICOM metadata tags for relabeling or correction
- Creating DICOM files from scratch (e.g., wrapping NumPy arrays as DICOM)
- Processing CT/MRI series into 3D volumetric arrays for reconstruction
- Extracting frames from multi-frame DICOM (cine/video)
- For whole-slide pathology images (SVS, NDPI), use `histolab-wsi-processing` instead
- For NIfTI neuroimaging volumes (.nii/.nii.gz), use `nibabel` instead

## Prerequisites

- **Python packages**: `pydicom`, `numpy`, `pillow`
- **Optional codecs**: `pylibjpeg` + `pylibjpeg-libjpeg` (JPEG), `pylibjpeg-openjpeg` (JPEG 2000), `python-gdcm` (most formats)
- **Data format**: DICOM files (.dcm, .ima, or extensionless) per NEMA PS3.10

```bash
pip install pydicom numpy pillow

# Optional: compression codec handlers (install as needed)
pip install pylibjpeg pylibjpeg-libjpeg   # JPEG Baseline/Lossless
pip install pylibjpeg-openjpeg             # JPEG 2000
pip install python-gdcm                    # Comprehensive codec support
```

## Quick Start

```python
import pydicom
import numpy as np

# Read a DICOM file
ds = pydicom.dcmread("scan.dcm")

# Access metadata
print(f"Patient: {ds.PatientName}, Modality: {ds.Modality}")
print(f"Size: {ds.Rows}x{ds.Columns}, Bits: {ds.BitsAllocated}")

# Extract pixel data as NumPy array
pixels = ds.pixel_array
print(f"Pixel array shape: {pixels.shape}, dtype: {pixels.dtype}")

# Apply windowing for display (CT/MR)
from pydicom.pixel_data_handlers.util import apply_voi_lut
display = apply_voi_lut(pixels, ds)
print(f"Windowed range: [{display.min()}, {display.max()}]")
```

## Core API

### Module 1: Reading and Metadata Access

Read DICOM files and access metadata using attribute names or tag notation.

```python
import pydicom

# Read DICOM file (defer_size delays loading large elements)
ds = pydicom.dcmread("scan.dcm")
ds_lazy = pydicom.dcmread("large.dcm", defer_size="1 KB")

# Access by attribute name (standard DICOM keywords)
print(f"Patient Name: {ds.PatientName}")
print(f"Study Date: {ds.StudyDate}")
print(f"Modality: {ds.Modality}")
print(f"Image Size: {ds.Rows} x {ds.Columns}")

# Access by tag number (group, element)
print(f"Patient ID: {ds[0x0010, 0x0020].value}")

# Safe access with getattr (avoids AttributeError)
slice_thick = getattr(ds, 'SliceThickness', 'N/A')
print(f"Slice Thickness: {slice_thick}")

# Iterate all elements
for elem in ds:
    if elem.VR != 'SQ':  # Skip sequences
        print(f"  {elem.tag} {elem.keyword}: {elem.value}")
```

```python
# Read DICOM directory (DICOMDIR)
from pydicom.filereader import dcmread

dicomdir = pydicom.dcmread("DICOMDIR")
for record in dicomdir.DirectoryRecordSequence:
    if record.DirectoryRecordType == "IMAGE":
        ref_file = record.ReferencedFileID
        # ref_file is a list of path components
        print(f"Image file: {'/'.join(ref_file)}")
```

### Module 2: Pixel Data Extraction

Extract pixel data as NumPy arrays with support for grayscale, color, windowing, and multi-frame.

```python
import pydicom
import numpy as np
from pydicom.pixel_data_handlers.util import apply_voi_lut, apply_modality_lut

ds = pydicom.dcmread("ct_scan.dcm")

# Basic pixel extraction
pixels = ds.pixel_array  # NumPy ndarray
print(f"Shape: {pixels.shape}, dtype: {pixels.dtype}")

# Apply Modality LUT (rescale to Hounsfield Units for CT)
hu_pixels = apply_modality_lut(pixels, ds)
print(f"HU range: [{hu_pixels.min()}, {hu_pixels.max()}]")

# Apply VOI LUT (windowing for display contrast)
display = apply_voi_lut(hu_pixels, ds)
print(f"Display range: [{display.min()}, {display.max()}]")

# Manual windowing (when VOI LUT metadata is absent)
center, width = 40, 400  # Soft tissue window
lower = center - width / 2
upper = center + width / 2
windowed = np.clip(hu_pixels, lower, upper)
print(f"Manual window [{lower}, {upper}]")
```

```python
# Color images (ultrasound, photos) — handle YBR color space
import pydicom

ds = pydicom.dcmread("ultrasound.dcm")
pixels = ds.pixel_array
print(f"Color shape: {pixels.shape}")  # (rows, cols, 3)

# Convert YBR to RGB if needed
photo_interp = ds.PhotometricInterpretation
if "YBR" in photo_interp:
    from pydicom.pixel_data_handlers.util import convert_color_space
    rgb = convert_color_space(pixels, photo_interp, "RGB")
    print(f"Converted {photo_interp} -> RGB")

# Multi-frame (cine/video DICOM)
ds_multi = pydicom.dcmread("cine.dcm")
frames = ds_multi.pixel_array  # Shape: (num_frames, rows, cols)
print(f"Frames: {frames.shape[0]}, Frame size: {frames.shape[1:]}")
```

### Module 3: Image Conversion

Convert DICOM pixel data to standard image formats for visualization and export.

```python
import pydicom
import numpy as np
from PIL import Image
from pydicom.pixel_data_handlers.util import apply_voi_lut

ds = pydicom.dcmread("scan.dcm")
pixels = ds.pixel_array

# Apply windowing
display = apply_voi_lut(pixels, ds)

# Normalize to 8-bit for standard image formats
if display.dtype != np.uint8:
    dmin, dmax = display.min(), display.max()
    if dmax > dmin:
        normalized = ((display - dmin) / (dmax - dmin) * 255).astype(np.uint8)
    else:
        normalized = np.zeros_like(display, dtype=np.uint8)
else:
    normalized = display

# Save as PNG
img = Image.fromarray(normalized)
img.save("output.png")
print(f"Saved output.png ({img.size[0]}x{img.size[1]})")

# Save as JPEG with quality control
img.save("output.jpg", quality=95)
```

```python
# Batch conversion: directory of DICOM files to PNG
import pydicom
import numpy as np
from PIL import Image
from pathlib import Path
from pydicom.pixel_data_handlers.util import apply_voi_lut

def dicom_to_image(dcm_path, out_path, fmt="PNG"):
    """Convert a single DICOM file to standard image format."""
    ds = pydicom.dcmread(str(dcm_path))
    pixels = apply_voi_lut(ds.pixel_array, ds)
    dmin, dmax = float(pixels.min()), float(pixels.max())
    if dmax > dmin:
        norm = ((pixels - dmin) / (dmax - dmin) * 255).astype(np.uint8)
    else:
        norm = np.zeros_like(pixels, dtype=np.uint8)
    Image.fromarray(norm).save(str(out_path))

dcm_dir = Path("dicom_files/")
out_dir = Path("images/")
out_dir.mkdir(exist_ok=True)

for dcm_file in sorted(dcm_dir.glob("*.dcm")):
    out_file = out_dir / f"{dcm_file.stem}.png"
    dicom_to_image(dcm_file, out_file)
    print(f"Converted: {dcm_file.name} -> {out_file.name}")
```

### Module 4: Metadata Modification and Anonymization

Modify DICOM attributes and remove Protected Health Information for de-identification.

```python
import pydicom
from pydicom.uid import generate_uid

ds = pydicom.dcmread("original.dcm")

# Modify attributes
ds.PatientName = "Anonymous"
ds.PatientID = "ANON001"
ds.InstitutionName = "Research Lab"

# Add new attribute
ds.add_new(0x00081030, 'LO', 'Research Study')  # Study Description

# Delete attribute
if 'PatientBirthDate' in ds:
    del ds.PatientBirthDate

# Generate new UIDs for de-identification
ds.StudyInstanceUID = generate_uid()
ds.SeriesInstanceUID = generate_uid()
ds.SOPInstanceUID = generate_uid()

# Save modified file (preserves original)
ds.save_as("modified.dcm")
print(f"Saved modified.dcm with new UIDs")
```

```python
# PHI anonymization: remove patient-identifying tags (DICOM PS3.15 Annex E)
import pydicom
from pydicom.uid import generate_uid

PHI_TAGS = [  # Core set — extend per institutional policy
    'PatientName', 'PatientID', 'PatientBirthDate', 'PatientSex',
    'PatientAge', 'PatientWeight', 'PatientAddress',
    'OtherPatientIDs', 'OtherPatientNames',
    'InstitutionName', 'InstitutionAddress',
    'ReferringPhysicianName', 'PerformingPhysicianName',
    'OperatorsName', 'StudyID', 'AccessionNumber',
]

def anonymize_dicom(ds, prefix="ANON"):
    """Remove PHI tags and assign anonymous identifiers."""
    for tag in PHI_TAGS:
        if hasattr(ds, tag): delattr(ds, tag)
    ds.PatientName, ds.PatientID = f"{prefix}_Patient", f"{prefix}_ID"
    ds.StudyInstanceUID = generate_uid()
    ds.SeriesInstanceUID = generate_uid()
    ds.SOPInstanceUID = generate_uid()
    return ds

ds = pydicom.dcmread("patient_scan.dcm")
anonymize_dicom(ds, prefix="STUDY001").save_as("anonymized.dcm")
print("Anonymized: PHI tags removed, UIDs replaced")
```

### Module 5: Writing DICOM from Scratch

Create new DICOM files from NumPy arrays with proper metadata.

```python
import pydicom, numpy as np, datetime
from pydicom.dataset import FileDataset, FileMetaDataset
from pydicom.uid import ExplicitVRLittleEndian, generate_uid

# File meta header
file_meta = FileMetaDataset()
file_meta.MediaStorageSOPClassUID = '1.2.840.10008.5.1.4.1.1.2'  # CT Image Storage
file_meta.MediaStorageSOPInstanceUID = generate_uid()
file_meta.TransferSyntaxUID = ExplicitVRLittleEndian

# Dataset with required attributes
ds = FileDataset("new.dcm", {}, file_meta=file_meta, preamble=b"\x00" * 128)
ds.SOPClassUID = file_meta.MediaStorageSOPClassUID
ds.SOPInstanceUID = file_meta.MediaStorageSOPInstanceUID
ds.StudyInstanceUID, ds.SeriesInstanceUID = generate_uid(), generate_uid()
ds.Modality, ds.Manufacturer = 'CT', 'Research'
ds.is_little_endian, ds.is_implicit_VR = True, False
dt = datetime.datetime.now()
ds.ContentDate, ds.ContentTime = dt.strftime('%Y%m%d'), dt.strftime('%H%M%S.%f')

# Pixel data from NumPy array
pixels = np.random.randint(0, 4096, (512, 512), dtype=np.uint16)
ds.Rows, ds.Columns = pixels.shape
ds.BitsAllocated, ds.BitsStored, ds.HighBit = 16, 12, 11
ds.PixelRepresentation = 0  # Unsigned
ds.SamplesPerPixel, ds.PhotometricInterpretation = 1, 'MONOCHROME2'
ds.PixelData = pixels.tobytes()

ds.save_as("new.dcm")
print(f"Created DICOM: {ds.Rows}x{ds.Columns}, {ds.BitsStored}-bit")
```

### Module 6: Series Processing and 3D Volumes

Load a DICOM series, sort by spatial position, and stack into a 3D NumPy array.

```python
import pydicom
import numpy as np
from pathlib import Path

def load_dicom_series(series_dir):
    """Load and sort a DICOM series by slice position."""
    dcm_files = []
    for f in Path(series_dir).iterdir():
        try:
            ds = pydicom.dcmread(str(f))
            dcm_files.append(ds)
        except Exception:
            continue  # Skip non-DICOM files

    if not dcm_files:
        raise ValueError(f"No DICOM files found in {series_dir}")

    # Sort by ImagePositionPatient (z-coordinate) or InstanceNumber
    try:
        dcm_files.sort(key=lambda x: float(x.ImagePositionPatient[2]))
    except (AttributeError, IndexError):
        dcm_files.sort(key=lambda x: int(x.InstanceNumber))

    print(f"Loaded {len(dcm_files)} slices, "
          f"Series: {getattr(dcm_files[0], 'SeriesDescription', 'N/A')}")
    return dcm_files

def series_to_volume(dcm_files):
    """Stack sorted DICOM slices into a 3D NumPy array."""
    from pydicom.pixel_data_handlers.util import apply_modality_lut
    slices = []
    for ds in dcm_files:
        pixels = apply_modality_lut(ds.pixel_array, ds)
        slices.append(pixels)
    volume = np.stack(slices, axis=0)
    # Calculate voxel spacing
    pixel_spacing = dcm_files[0].PixelSpacing
    if len(dcm_files) > 1:
        try:
            z0 = float(dcm_files[0].ImagePositionPatient[2])
            z1 = float(dcm_files[1].ImagePositionPatient[2])
            slice_spacing = abs(z1 - z0)
        except (AttributeError, IndexError):
            slice_spacing = float(getattr(dcm_files[0], 'SliceThickness', 1.0))
    else:
        slice_spacing = float(getattr(dcm_files[0], 'SliceThickness', 1.0))
    spacing = (slice_spacing, float(pixel_spacing[0]), float(pixel_spacing[1]))
    print(f"Volume shape: {volume.shape}, Spacing (z,y,x): {spacing} mm")
    return volume, spacing

# Usage
dcm_files = load_dicom_series("ct_series/")
volume, spacing = series_to_volume(dcm_files)
print(f"HU range: [{volume.min()}, {volume.max()}]")
```

## Key Concepts

### DICOM Data Model

DICOM organizes medical imaging data in a four-level hierarchy:

| Level | Key UID | Description |
|-------|---------|-------------|
| Patient | PatientID | A single individual |
| Study | StudyInstanceUID | One imaging session (may contain multiple modalities) |
| Series | SeriesInstanceUID | One acquisition sequence (e.g., T1-weighted MRI) |
| Instance (Image) | SOPInstanceUID | One image/frame (one DICOM file) |

Each DICOM file contains one Instance with metadata tags organized by group. Tags use `(group, element)` notation (e.g., `(0010,0010)` for PatientName).

### Transfer Syntax and Compression

Transfer Syntax defines how DICOM data is encoded (byte order, VR encoding, pixel compression):

| Transfer Syntax | UID | Compression | Handler Needed |
|----------------|-----|-------------|----------------|
| Implicit VR Little Endian | 1.2.840.10008.1.2 | None | No |
| Explicit VR Little Endian | 1.2.840.10008.1.2.1 | None | No |
| Explicit VR Big Endian | 1.2.840.10008.1.2.2 | None | No |
| JPEG Baseline | 1.2.840.10008.1.2.4.50 | Lossy JPEG | pylibjpeg |
| JPEG Lossless | 1.2.840.10008.1.2.4.70 | Lossless JPEG | pylibjpeg |
| JPEG 2000 Lossless | 1.2.840.10008.1.2.4.90 | Lossless J2K | pylibjpeg-openjpeg |
| JPEG 2000 | 1.2.840.10008.1.2.4.91 | Lossy J2K | pylibjpeg-openjpeg |
| RLE Lossless | 1.2.840.10008.1.2.5 | RLE | pydicom (built-in) |

Check transfer syntax: `ds.file_meta.TransferSyntaxUID`. Install the appropriate handler before accessing `pixel_array` on compressed files.

### Essential DICOM Tags

Most commonly accessed tags (full catalog in references/dicom_standards.md):

| Tag | Keyword | VR | Description |
|-----|---------|-----|-------------|
| (0008,0060) | Modality | CS | CT, MR, US, CR, DX, PT, NM |
| (0010,0010) | PatientName | PN | Patient's full name |
| (0010,0020) | PatientID | LO | Patient identifier |
| (0008,0020) | StudyDate | DA | Date of study (YYYYMMDD) |
| (0020,000D) | StudyInstanceUID | UI | Unique study identifier |
| (0020,0013) | InstanceNumber | IS | Image number in series |
| (0020,0032) | ImagePositionPatient | DS | x,y,z position (mm) |
| (0028,0010) | Rows | US | Image height in pixels |
| (0028,0011) | Columns | US | Image width in pixels |
| (0028,0030) | PixelSpacing | DS | Row,column spacing (mm) |
| (0028,1050) | WindowCenter | DS | Display window center |
| (0028,0004) | PhotometricInterpretation | CS | MONOCHROME1/2, RGB, YBR_FULL |
| (0028,0100) | BitsAllocated | US | 8 or 16 |

### Value Representations (VR)

VR defines the data type for each element. Most common types (full table in references/dicom_standards.md):

| VR | Name | Python Type | Example |
|----|------|-------------|---------|
| CS | Code String | str | "CT", "MR" |
| DA | Date | str | "20240115" |
| DS | Decimal String | DSfloat | "1.5" |
| IS | Integer String | IS | "42" |
| LO | Long String | str | "Study description" |
| PN | Person Name | PersonName | "Doe^John" |
| SQ | Sequence | Sequence | Nested datasets |
| UI | Unique Identifier | UID | "1.2.840..." |
| US | Unsigned Short | int | 512 |

## Common Workflows

### Workflow 1: Batch Metadata Extraction to CSV

**Goal**: Walk a directory of DICOM files, extract key metadata fields, and export to a CSV manifest.

```python
import pydicom
import pandas as pd
from pathlib import Path

FIELDS = ['PatientID', 'Modality', 'StudyDate', 'SeriesDescription',
          'StudyInstanceUID', 'SeriesInstanceUID', 'InstanceNumber',
          'Rows', 'Columns', 'SliceThickness', 'BitsStored']

def extract_metadata(dcm_path):
    """Extract key metadata from a DICOM file."""
    try:
        ds = pydicom.dcmread(str(dcm_path), stop_before_pixels=True)
    except Exception as e:
        return {"file": str(dcm_path), "error": str(e)}
    rec = {"file": str(dcm_path)}
    for f in FIELDS:
        rec[f] = str(getattr(ds, f, ''))
    return rec

# Scan directory recursively
dicom_dir = Path("dicom_archive/")
records = [extract_metadata(f) for f in sorted(dicom_dir.rglob("*")) if f.is_file()]

df = pd.DataFrame(records)
df.to_csv("dicom_manifest.csv", index=False)
print(f"Extracted metadata from {len(df)} files")
print(f"Modalities: {df['Modality'].value_counts().to_dict()}")
print(f"Unique patients: {df['PatientID'].nunique()}")
```

### Workflow 2: CT Series to 3D Volume with Visualization

**Goal**: Load a CT series, build a 3D volume in Hounsfield Units, and display axial/sagittal/coronal views.

```python
import pydicom, numpy as np, matplotlib.pyplot as plt
from pathlib import Path
from pydicom.pixel_data_handlers.util import apply_modality_lut

# Load and sort series by z-position
dcm_files = []
for f in sorted(Path("ct_series/").glob("*")):
    try: dcm_files.append(pydicom.dcmread(str(f)))
    except Exception: continue
dcm_files.sort(key=lambda x: float(x.ImagePositionPatient[2]))

# Stack into 3D volume (Hounsfield Units)
volume = np.stack([apply_modality_lut(ds.pixel_array, ds) for ds in dcm_files])
ps = dcm_files[0].PixelSpacing
z_sp = abs(float(dcm_files[1].ImagePositionPatient[2])
           - float(dcm_files[0].ImagePositionPatient[2]))
print(f"Volume: {volume.shape}, spacing: {z_sp:.2f}x{float(ps[0]):.2f}x{float(ps[1]):.2f} mm")

# Display orthogonal views (soft tissue window)
vmin, vmax = -160, 240  # center=40, width=400
fig, axes = plt.subplots(1, 3, figsize=(18, 6))
mid = [s // 2 for s in volume.shape]
axes[0].imshow(volume[mid[0]], cmap='gray', vmin=vmin, vmax=vmax)
axes[0].set_title(f"Axial (slice {mid[0]})")
axes[1].imshow(volume[:, mid[1], :], cmap='gray', vmin=vmin, vmax=vmax,
               aspect=z_sp/float(ps[1]))
axes[1].set_title(f"Coronal")
axes[2].imshow(volume[:, :, mid[2]], cmap='gray', vmin=vmin, vmax=vmax,
               aspect=z_sp/float(ps[0]))
axes[2].set_title(f"Sagittal")
for ax in axes: ax.axis('off')
plt.tight_layout()
plt.savefig("orthogonal_views.png", dpi=150, bbox_inches='tight')
print("Saved orthogonal_views.png")
```

### Workflow 3: Batch Anonymization Pipeline

**Goal**: Anonymize all DICOM files in a directory, preserving series structure with new UIDs.

```python
import pydicom
from pydicom.uid import generate_uid
from pathlib import Path

PHI_TAGS = [
    'PatientName', 'PatientID', 'PatientBirthDate', 'PatientSex',
    'PatientAge', 'PatientWeight', 'PatientAddress',
    'OtherPatientIDs', 'OtherPatientNames',
    'InstitutionName', 'InstitutionAddress',
    'ReferringPhysicianName', 'PerformingPhysicianName',
    'OperatorsName', 'PhysiciansOfRecord', 'StudyID', 'AccessionNumber',
]

uid_map = {}  # Preserves study/series relationships across files
def get_mapped_uid(uid):
    if uid not in uid_map: uid_map[uid] = generate_uid()
    return uid_map[uid]

input_dir, output_dir = Path("original_dicoms/"), Path("anonymized_dicoms/")
output_dir.mkdir(exist_ok=True)
count, errors = 0, 0

for dcm_path in sorted(input_dir.rglob("*")):
    if not dcm_path.is_file(): continue
    try: ds = pydicom.dcmread(str(dcm_path))
    except Exception: errors += 1; continue

    for tag in PHI_TAGS:
        if hasattr(ds, tag): delattr(ds, tag)
    ds.PatientName, ds.PatientID = "ANONYMOUS", "ANON"
    ds.StudyInstanceUID = get_mapped_uid(ds.StudyInstanceUID)
    ds.SeriesInstanceUID = get_mapped_uid(ds.SeriesInstanceUID)
    ds.SOPInstanceUID = generate_uid()
    ds.save_as(str(output_dir / f"anon_{count:06d}.dcm"))
    count += 1

print(f"Anonymized {count} files, {errors} errors, {len(uid_map)} UIDs mapped")
```

## Key Parameters

| Parameter | Module | Default | Range / Options | Effect |
|-----------|--------|---------|-----------------|--------|
| `defer_size` | dcmread | `None` | `"1 KB"`, `"1 MB"`, int bytes | Defer loading elements larger than size |
| `stop_before_pixels` | dcmread | `False` | `True`/`False` | Skip pixel data loading (metadata only) |
| `force` | dcmread | `False` | `True`/`False` | Force read even if missing DICOM preamble |
| `WindowCenter` | Windowing | from file | Any numeric | Center of display window (HU for CT) |
| `WindowWidth` | Windowing | from file | `> 0` | Width of display window |
| `BitsAllocated` | Writing | `16` | `8`, `16`, `32` | Bits allocated per pixel |
| `BitsStored` | Writing | `12` | `1`-`BitsAllocated` | Actual significant bits |
| `PixelRepresentation` | Writing | `0` | `0` (unsigned), `1` (signed) | Pixel value signedness |
| `PhotometricInterpretation` | Writing | `"MONOCHROME2"` | `MONOCHROME1`, `MONOCHROME2`, `RGB`, `YBR_FULL` | Color space |
| `TransferSyntaxUID` | Writing | Explicit VR LE | See Transfer Syntax table | Encoding format |

## Best Practices

1. **Use `stop_before_pixels=True` for metadata-only operations**: Avoids loading large pixel arrays when only reading tags. Dramatically faster for batch metadata extraction.
   ```python
   ds = pydicom.dcmread("scan.dcm", stop_before_pixels=True)
   ```

2. **Always use `getattr()` with defaults for optional tags**: DICOM files vary widely in which tags are present. Direct attribute access raises `AttributeError` on missing tags.
   ```python
   # Good
   thickness = getattr(ds, 'SliceThickness', None)
   # Bad — will crash on files without SliceThickness
   thickness = ds.SliceThickness
   ```

3. **Apply Modality LUT before windowing for CT data**: Raw pixel values are stored values; apply `apply_modality_lut()` first to convert to Hounsfield Units, then `apply_voi_lut()` for display.

4. **Install compression handlers before accessing compressed pixel data**: Check `ds.file_meta.TransferSyntaxUID` and install the appropriate handler. Attempting `pixel_array` without the handler raises `RuntimeError`.

5. **Generate new UIDs for every modified file**: Never reuse original SOPInstanceUID after modifications. Use `pydicom.uid.generate_uid()` to ensure global uniqueness.

6. **Use `save_as()` instead of overwriting originals**: Always save to a new path to preserve original data. DICOM archives may have integrity checks that fail if originals are modified in-place.

7. **Sort series by ImagePositionPatient for 3D reconstruction**: `InstanceNumber` is not always reliable. `ImagePositionPatient[2]` (z-coordinate) gives correct physical ordering for axial CT/MR series.

## Common Recipes

### Recipe: Compression and Decompression Handling

When to use: Read compressed DICOM files or compress uncompressed ones.

```python
import pydicom

ds = pydicom.dcmread("compressed.dcm")
ts = ds.file_meta.TransferSyntaxUID

# Check if compressed
print(f"Transfer Syntax: {ts}")
print(f"Compressed: {ts.is_compressed}")

# Decompress in-place (requires appropriate handler installed)
if ts.is_compressed:
    ds.decompress()
    print(f"Decompressed to {ds.file_meta.TransferSyntaxUID}")

# Access pixel data (works after decompression)
pixels = ds.pixel_array
print(f"Pixel shape: {pixels.shape}")
```

### Recipe: Working with DICOM Sequences

When to use: Access nested data structures like referenced series, procedure codes, or protocol elements.

```python
import pydicom

ds = pydicom.dcmread("structured.dcm")

# Access sequence elements (SQ VR = list of datasets)
if hasattr(ds, 'ReferencedStudySequence'):
    for item in ds.ReferencedStudySequence:
        print(f"  Referenced Study: {item.ReferencedSOPInstanceUID}")

# Access procedure code sequence
if hasattr(ds, 'ProcedureCodeSequence'):
    for code in ds.ProcedureCodeSequence:
        print(f"  Procedure: {code.CodeMeaning} ({code.CodeValue})")

# Create a sequence when writing DICOM
from pydicom.dataset import Dataset
from pydicom.sequence import Sequence

ref_item = Dataset()
ref_item.ReferencedSOPClassUID = '1.2.840.10008.5.1.4.1.1.2'
ref_item.ReferencedSOPInstanceUID = pydicom.uid.generate_uid()
ds.ReferencedImageSequence = Sequence([ref_item])
```

### Recipe: Multi-Frame Extraction

When to use: Extract individual frames from cine, video, or enhanced multi-frame DICOM files.

```python
import pydicom
import numpy as np
from PIL import Image
from pathlib import Path

ds = pydicom.dcmread("multiframe.dcm")
frames = ds.pixel_array  # Shape: (num_frames, rows, cols) or (num_frames, rows, cols, 3)
num_frames = frames.shape[0]
print(f"Total frames: {num_frames}, Frame size: {frames.shape[1:]}")

# Extract all frames as images
out_dir = Path("frames/")
out_dir.mkdir(exist_ok=True)

for i in range(num_frames):
    frame = frames[i]
    # Normalize to uint8
    if frame.dtype != np.uint8:
        fmin, fmax = frame.min(), frame.max()
        if fmax > fmin:
            frame = ((frame - fmin) / (fmax - fmin) * 255).astype(np.uint8)
        else:
            frame = np.zeros_like(frame, dtype=np.uint8)
    Image.fromarray(frame).save(out_dir / f"frame_{i:04d}.png")

print(f"Extracted {num_frames} frames to {out_dir}/")
```

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| `RuntimeError: No available image handler` | Compressed transfer syntax without codec | Install appropriate handler: `pip install pylibjpeg pylibjpeg-libjpeg` (JPEG), `pip install pylibjpeg-openjpeg` (JPEG 2000), or `pip install python-gdcm` (all formats) |
| `AttributeError: 'Dataset' has no attribute 'X'` | Optional tag not present in file | Use `getattr(ds, 'X', default)` or check `'X' in ds` before access |
| `InvalidDicomError: File is missing DICOM preamble` | Non-standard DICOM file or non-DICOM file | Try `pydicom.dcmread(path, force=True)` to skip preamble check |
| Wrong pixel values (no negative HU) | Missing Modality LUT application | Apply `apply_modality_lut(pixels, ds)` before analysis — raw stored values differ from actual HU |
| Image appears inverted (bright/dark swapped) | MONOCHROME1 photometric interpretation | Check `ds.PhotometricInterpretation`; invert with `np.max(pixels) - pixels` for MONOCHROME1 |
| `MemoryError` loading large series | All slices loaded into memory at once | Process slices in batches; use `stop_before_pixels=True` for metadata scans; use `defer_size` for large elements |
| Inconsistent slice ordering in 3D volume | Sorted by InstanceNumber instead of position | Sort by `ImagePositionPatient[2]` for correct physical ordering |
| Garbled text in PatientName | Character encoding mismatch | Check `SpecificCharacterSet` tag; pydicom auto-decodes but some files have incorrect charset declarations |
| `TypeError` when setting PixelData | Wrong byte format for pixel array | Use `pixel_array.tobytes()` and ensure dtype matches BitsAllocated (uint16 for 16-bit) |

## Bundled Resources

### references/dicom_standards.md

Consolidated DICOM tag catalogs and transfer syntax reference. Complete tag tables for patient demographics, study/series identification, image geometry, pixel data encoding, windowing parameters, and modality-specific tags (CT Hounsfield parameters, MR sequence parameters, equipment identification, timing). Full transfer syntax UID table with compression types and handler installation. Value Representation (VR) type reference.

- **Covers**: All tag categories from common_tags.md (patient, study, series, image, pixel, windowing, CT-specific, MR-specific, equipment, timing); all transfer syntax UIDs from transfer_syntaxes.md with compression formats and handler mapping; VR type catalog
- **Relocated inline**: Essential tags table (20 most common) moved to Key Concepts; transfer syntax summary table (8 most common) moved to Key Concepts; VR summary table moved to Key Concepts
- **Omitted**: Step-by-step handler installation tutorials (covered in Prerequisites and Troubleshooting); verbose prose descriptions of each tag (tables are self-documenting)

### Original file disposition (5 files):

1. **SKILL.md** (434 lines) -- Migrated: overview, workflows, best practices, common issues restructured into new SKILL.md format
2. **references/common_tags.md** (229 lines) -- (b) Consolidated: essential 20-tag table into Key Concepts; full catalog into references/dicom_standards.md
3. **references/transfer_syntaxes.md** (353 lines) -- (b) Consolidated: summary table (8 syntaxes) into Key Concepts; full UID table and handler details into references/dicom_standards.md
4. **scripts/anonymize_dicom.py** (138 lines) -- (c) Absorbed: PHI tag list and anonymize function into Core API Module 4; batch pipeline into Workflow 3
5. **scripts/dicom_to_image.py** (173 lines) -- (c) Absorbed: conversion function into Core API Module 3 (dicom_to_image helper); batch conversion into Module 3 second code block
6. **scripts/extract_metadata.py** (174 lines) -- (c) Absorbed: metadata extraction function into Workflow 1 (batch extraction to CSV)

## Related Skills

- **histolab-wsi-processing** -- whole-slide pathology image processing (SVS, NDPI); use for digital pathology tile extraction
- **nibabel (planned)** -- NIfTI neuroimaging format for brain MRI volumetric analysis
- **matplotlib-scientific-plotting** -- publication-quality visualization of DICOM images and 3D volume slices

## References

- [Pydicom documentation](https://pydicom.github.io/pydicom/stable/) -- official API reference and user guide
- [Pydicom GitHub repository](https://github.com/pydicom/pydicom) -- source code, examples, and issue tracker
- [DICOM Standard Browser](https://dicom.innolitics.com/ciods) -- interactive DICOM tag and IOD reference
- [pylibjpeg documentation](https://github.com/pydicom/pylibjpeg) -- JPEG codec plugin for pydicom
