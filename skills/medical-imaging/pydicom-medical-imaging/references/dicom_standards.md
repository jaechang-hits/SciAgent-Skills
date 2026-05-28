# DICOM Standards Reference

Consolidated tag catalogs and transfer syntax reference for pydicom.
Essential subsets are inlined in the main SKILL.md Key Concepts section; this file provides the complete reference.

> **Condensation note**: Consolidated from common_tags.md (229 lines) and transfer_syntaxes.md (353 lines). Verbose prose descriptions replaced with table format. Handler installation tutorials moved to SKILL.md Prerequisites and Troubleshooting.

---

## Patient Demographics Tags

| Tag | Keyword | VR | Description |
|-----|---------|-----|-------------|
| (0010,0010) | PatientName | PN | Patient's full name (Last^First^Middle) |
| (0010,0020) | PatientID | LO | Primary patient identifier |
| (0010,0030) | PatientBirthDate | DA | Date of birth (YYYYMMDD) |
| (0010,0040) | PatientSex | CS | M, F, or O |
| (0010,1010) | PatientAge | AS | Age string (e.g., "045Y") |
| (0010,1020) | PatientSize | DS | Height in meters |
| (0010,1030) | PatientWeight | DS | Weight in kg |
| (0010,0032) | PatientBirthTime | TM | Time of birth |
| (0010,1000) | OtherPatientIDs | LO | Additional IDs |
| (0010,1001) | OtherPatientNames | PN | Additional names |
| (0010,1040) | PatientAddress | LO | Mailing address |
| (0010,2154) | PatientTelephoneNumbers | SH | Phone numbers |

## Study-Level Tags

| Tag | Keyword | VR | Description |
|-----|---------|-----|-------------|
| (0008,0020) | StudyDate | DA | Date study started |
| (0008,0030) | StudyTime | TM | Time study started |
| (0008,0050) | AccessionNumber | SH | RIS/HIS order number |
| (0008,0090) | ReferringPhysicianName | PN | Ordering physician |
| (0008,1030) | StudyDescription | LO | Study description text |
| (0020,000D) | StudyInstanceUID | UI | Globally unique study ID |
| (0020,0010) | StudyID | SH | Human-readable study ID |
| (0032,1032) | RequestingPhysician | PN | Physician requesting study |
| (0008,1060) | PhysiciansOfRecord | PN | Attending physicians |

## Series-Level Tags

| Tag | Keyword | VR | Description |
|-----|---------|-----|-------------|
| (0008,0060) | Modality | CS | CT, MR, US, CR, DX, PT, NM, XA, RF, MG, IO, PX, SC |
| (0008,0021) | SeriesDate | DA | Date series started |
| (0008,0031) | SeriesTime | TM | Time series started |
| (0008,103E) | SeriesDescription | LO | Series description text |
| (0020,000E) | SeriesInstanceUID | UI | Globally unique series ID |
| (0020,0011) | SeriesNumber | IS | Series number within study |
| (0008,0070) | Manufacturer | LO | Equipment manufacturer |
| (0008,1010) | StationName | SH | Scanner station name |
| (0008,1090) | ManufacturerModelName | LO | Scanner model |
| (0018,1000) | DeviceSerialNumber | LO | Scanner serial number |
| (0018,1020) | SoftwareVersions | LO | Scanner software version |
| (0008,1070) | OperatorsName | PN | Operator performing scan |
| (0008,1050) | PerformingPhysicianName | PN | Physician performing |

## Image Geometry Tags

| Tag | Keyword | VR | Description |
|-----|---------|-----|-------------|
| (0020,0013) | InstanceNumber | IS | Image number in series |
| (0020,0032) | ImagePositionPatient | DS | x,y,z of upper-left corner (mm) |
| (0020,0037) | ImageOrientationPatient | DS | Row/column direction cosines (6 values) |
| (0020,1041) | SliceLocation | DS | Relative slice position (mm) |
| (0028,0010) | Rows | US | Image height in pixels |
| (0028,0011) | Columns | US | Image width in pixels |
| (0028,0030) | PixelSpacing | DS | Row spacing, column spacing (mm) |
| (0018,0050) | SliceThickness | DS | Nominal slice thickness (mm) |
| (0018,0088) | SpacingBetweenSlices | DS | Center-to-center distance (mm) |
| (0028,0008) | NumberOfFrames | IS | Number of frames (multi-frame) |

## Pixel Data Encoding Tags

| Tag | Keyword | VR | Description |
|-----|---------|-----|-------------|
| (0028,0004) | PhotometricInterpretation | CS | MONOCHROME1, MONOCHROME2, RGB, YBR_FULL, YBR_FULL_422, PALETTE COLOR |
| (0028,0002) | SamplesPerPixel | US | 1 (grayscale) or 3 (color) |
| (0028,0006) | PlanarConfiguration | US | 0 (pixel-interleaved RGBRGB) or 1 (plane-separated RR...GG...BB) |
| (0028,0100) | BitsAllocated | US | 8, 16, or 32 |
| (0028,0101) | BitsStored | US | Significant bits (e.g., 12 for CT) |
| (0028,0102) | HighBit | US | BitsStored - 1 |
| (0028,0103) | PixelRepresentation | US | 0 (unsigned) or 1 (two's complement signed) |
| (7FE0,0010) | PixelData | OB/OW | Raw pixel byte stream |

## Windowing and Display Tags

| Tag | Keyword | VR | Description |
|-----|---------|-----|-------------|
| (0028,1050) | WindowCenter | DS | Center of display window (may be multi-valued) |
| (0028,1051) | WindowWidth | DS | Width of display window (may be multi-valued) |
| (0028,1052) | RescaleIntercept | DS | b in output = m*SV + b |
| (0028,1053) | RescaleSlope | DS | m in output = m*SV + b |
| (0028,1054) | RescaleType | LO | Units after rescale (e.g., "HU") |
| (0028,3010) | VOILUTSequence | SQ | VOI lookup table sequence |
| (0028,1055) | WindowCenterWidthExplanation | LO | Named window presets |

### Standard CT Window Presets

| Window Name | Center (HU) | Width (HU) | Use Case |
|-------------|-------------|------------|----------|
| Soft Tissue | 40 | 400 | Abdomen, general |
| Lung | -600 | 1500 | Pulmonary |
| Bone | 400 | 1800 | Skeletal |
| Brain | 40 | 80 | Neurological |
| Liver | 60 | 160 | Hepatic |
| Mediastinum | 40 | 500 | Chest soft tissue |

## CT-Specific Tags

| Tag | Keyword | VR | Description |
|-----|---------|-----|-------------|
| (0018,0060) | KVP | DS | Peak kilovoltage (tube voltage) |
| (0018,1150) | ExposureTime | IS | Exposure time (ms) |
| (0018,1151) | XRayTubeCurrent | IS | Tube current (mA) |
| (0018,1152) | Exposure | IS | Exposure (mAs) |
| (0018,0090) | DataCollectionDiameter | DS | Reconstruction diameter (mm) |
| (0018,1100) | ReconstructionDiameter | DS | Display field of view (mm) |
| (0018,1160) | FilterType | SH | X-ray filter type |
| (0018,9305) | RevolutionTime | FD | Gantry rotation time (s) |
| (0018,9306) | SingleCollimationWidth | FD | Detector element width (mm) |
| (0018,9307) | TotalCollimationWidth | FD | Total beam width (mm) |
| (0018,9311) | SpiralPitchFactor | FD | Helical pitch factor |
| (0018,1210) | ConvolutionKernel | SH | Reconstruction kernel (e.g., "STANDARD", "BONE") |

## MR-Specific Tags

| Tag | Keyword | VR | Description |
|-----|---------|-----|-------------|
| (0018,0020) | ScanningSequence | CS | SE, IR, GR, EP, RM |
| (0018,0021) | SequenceVariant | CS | SK, MTC, SS, TRSS, SP, MP, OSP, NONE |
| (0018,0023) | MRAcquisitionType | CS | 2D or 3D |
| (0018,0080) | RepetitionTime | DS | TR (ms) |
| (0018,0081) | EchoTime | DS | TE (ms) |
| (0018,0082) | InversionTime | DS | TI (ms) |
| (0018,0083) | NumberOfAverages | DS | NEX/NSA |
| (0018,0084) | ImagingFrequency | DS | Larmor frequency (MHz) |
| (0018,0085) | ImagedNucleus | SH | e.g., "1H" |
| (0018,0087) | MagneticFieldStrength | DS | Field strength (T) |
| (0018,0089) | NumberOfPhaseEncodingSteps | IS | Phase encoding steps |
| (0018,0091) | EchoTrainLength | IS | ETL |
| (0018,1314) | FlipAngle | DS | Flip angle (degrees) |
| (0018,0095) | PixelBandwidth | DS | Bandwidth per pixel (Hz) |

## Timing and Acquisition Tags

| Tag | Keyword | VR | Description |
|-----|---------|-----|-------------|
| (0008,0022) | AcquisitionDate | DA | Date image acquired |
| (0008,0032) | AcquisitionTime | TM | Time image acquired |
| (0008,0023) | ContentDate | DA | Date image created |
| (0008,0033) | ContentTime | TM | Time image created |
| (0020,0012) | AcquisitionNumber | IS | Acquisition sequence number |
| (0018,1060) | TriggerTime | DS | Cardiac trigger time (ms) |
| (0020,0100) | TemporalPositionIdentifier | IS | Temporal phase number |
| (0020,0105) | NumberOfTemporalPositions | IS | Total temporal phases |

---

## Transfer Syntax Reference

### Uncompressed Transfer Syntaxes

| Name | UID | VR | Byte Order |
|------|-----|-----|-----------|
| Implicit VR Little Endian | 1.2.840.10008.1.2 | Implicit | Little |
| Explicit VR Little Endian | 1.2.840.10008.1.2.1 | Explicit | Little |
| Explicit VR Big Endian | 1.2.840.10008.1.2.2 | Explicit | Big |

### JPEG Transfer Syntaxes

| Name | UID | Compression | Handler |
|------|-----|-------------|---------|
| JPEG Baseline (Process 1) | 1.2.840.10008.1.2.4.50 | Lossy, 8-bit | pylibjpeg + pylibjpeg-libjpeg |
| JPEG Extended (Process 2 & 4) | 1.2.840.10008.1.2.4.51 | Lossy, 12-bit | pylibjpeg + pylibjpeg-libjpeg |
| JPEG Lossless (Process 14) | 1.2.840.10008.1.2.4.57 | Lossless | pylibjpeg + pylibjpeg-libjpeg |
| JPEG Lossless SV1 (Process 14, SV1) | 1.2.840.10008.1.2.4.70 | Lossless | pylibjpeg + pylibjpeg-libjpeg |

### JPEG 2000 Transfer Syntaxes

| Name | UID | Compression | Handler |
|------|-----|-------------|---------|
| JPEG 2000 Lossless Only | 1.2.840.10008.1.2.4.90 | Lossless | pylibjpeg + pylibjpeg-openjpeg |
| JPEG 2000 | 1.2.840.10008.1.2.4.91 | Lossy or Lossless | pylibjpeg + pylibjpeg-openjpeg |

### JPEG-LS Transfer Syntaxes

| Name | UID | Compression | Handler |
|------|-----|-------------|---------|
| JPEG-LS Lossless | 1.2.840.10008.1.2.4.80 | Lossless | pylibjpeg + pylibjpeg-libjpeg |
| JPEG-LS Near-Lossless | 1.2.840.10008.1.2.4.81 | Near-lossless | pylibjpeg + pylibjpeg-libjpeg |

### Other Transfer Syntaxes

| Name | UID | Compression | Handler |
|------|-----|-------------|---------|
| RLE Lossless | 1.2.840.10008.1.2.5 | RLE encoding | pydicom (built-in) |
| Deflated Explicit VR Little Endian | 1.2.840.10008.1.2.1.99 | zlib deflate (metadata) | pydicom (built-in) |

### Checking and Handling Transfer Syntax

```python
import pydicom

ds = pydicom.dcmread("file.dcm")
ts = ds.file_meta.TransferSyntaxUID

print(f"Transfer Syntax UID: {ts}")
print(f"Name: {ts.name}")
print(f"Is compressed: {ts.is_compressed}")
print(f"Is little endian: {ts.is_little_endian}")
print(f"Is implicit VR: {ts.is_implicit_VR}")
```

### Handler Installation Guide

Install handlers based on which compressed formats you need to read:

| Need to Read | Install Command |
|-------------|----------------|
| JPEG (most common compressed) | `pip install pylibjpeg pylibjpeg-libjpeg` |
| JPEG 2000 | `pip install pylibjpeg pylibjpeg-openjpeg` |
| All JPEG variants + JPEG 2000 | `pip install pylibjpeg pylibjpeg-libjpeg pylibjpeg-openjpeg` |
| All formats (comprehensive) | `pip install python-gdcm` |

`python-gdcm` is the most comprehensive single package but has platform-specific installation requirements. The `pylibjpeg` ecosystem provides pure-Python alternatives.

---

## Value Representation (VR) Complete Reference

| VR | Name | Max Length | Python Type | Format / Notes |
|----|------|-----------|-------------|----------------|
| AE | Application Entity | 16 | str | Leading/trailing spaces significant |
| AS | Age String | 4 | str | nnnD, nnnW, nnnM, nnnY |
| AT | Attribute Tag | 4 | BaseTag | (group, element) pair |
| CS | Code String | 16 | str | Uppercase A-Z, 0-9, space, underscore |
| DA | Date | 8 | str | YYYYMMDD |
| DS | Decimal String | 16 | DSfloat | Numeric string (e.g., "3.14159") |
| DT | Date Time | 26 | str | YYYYMMDDHHMMSS.FFFFFF&ZZXX |
| FL | Floating Point Single | 4 | float | 32-bit IEEE 754 |
| FD | Floating Point Double | 8 | float | 64-bit IEEE 754 |
| IS | Integer String | 12 | IS (int) | Numeric string (e.g., "42") |
| LO | Long String | 64 | str | General text |
| LT | Long Text | 10240 | str | Multi-line text |
| OB | Other Byte | varies | bytes | Byte stream |
| OD | Other Double | varies | bytes | 64-bit float stream |
| OF | Other Float | varies | bytes | 32-bit float stream |
| OW | Other Word | varies | bytes | 16-bit word stream |
| PN | Person Name | 64/component | PersonName | Family^Given^Middle^Prefix^Suffix |
| SH | Short String | 16 | str | Short text |
| SL | Signed Long | 4 | int | 32-bit signed integer |
| SQ | Sequence | varies | Sequence | List of Datasets |
| SS | Signed Short | 2 | int | 16-bit signed integer |
| ST | Short Text | 1024 | str | Single paragraph text |
| TM | Time | 14 | str | HHMMSS.FFFFFF |
| UC | Unlimited Characters | varies | str | Unlimited text |
| UI | Unique Identifier | 64 | UID | Dotted numeric string (e.g., "1.2.840...") |
| UL | Unsigned Long | 4 | int | 32-bit unsigned integer |
| UN | Unknown | varies | bytes | Unknown VR |
| UR | URI/URL | varies | str | Universal Resource Identifier |
| US | Unsigned Short | 2 | int | 16-bit unsigned integer |
| UT | Unlimited Text | varies | str | Unlimited multi-line text |
