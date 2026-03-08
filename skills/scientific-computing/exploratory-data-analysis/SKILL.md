---
name: exploratory-data-analysis
description: >-
  Methodology for performing exploratory data analysis on scientific data files.
  Covers decision frameworks for choosing analysis approaches based on data type
  (tabular, sequence, image, spectral, structural, omics), quality assessment,
  report generation, and format detection across 200+ scientific file formats.
  Use when a user provides a data file for initial exploration or asks what
  analysis is appropriate before running a pipeline.
license: CC-BY-4.0
---

# Exploratory Data Analysis for Scientific Data

## Overview

Exploratory data analysis (EDA) is the systematic examination of scientific data files to understand their structure, content, quality, and characteristics before formal analysis. This knowhow covers methodology for detecting file types, selecting appropriate analysis approaches, assessing data quality, and generating comprehensive reports across all major scientific data domains.

## Key Concepts

### Scientific Data Type Categories

| Category | Common Formats | Typical Analysis | Key Libraries |
|----------|---------------|-----------------|---------------|
| **Tabular** | CSV, TSV, XLSX, Parquet | Summary statistics, distributions, correlations, missing values | pandas, polars |
| **Sequence** | FASTA, FASTQ, SAM/BAM | Length distribution, quality scores, GC content, alignment stats | BioPython, pysam |
| **Image/Microscopy** | TIFF, ND2, CZI, DICOM | Dimensions (XYZCT), intensity stats, metadata, calibration | tifffile, aicsimageio, nd2reader |
| **Spectral** | mzML, SPC, JCAMP, FID | Peak detection, baseline, S/N ratio, resolution | pymzml, nmrglue, pyteomics |
| **Structural** | PDB, CIF, MOL, SDF | Atom counts, bond validation, B-factors, completeness | BioPython, RDKit, MDAnalysis |
| **Array/Tensor** | NPY, HDF5, Zarr, NetCDF | Shape, dtype, value range, NaN/Inf check, chunk structure | numpy, h5py, zarr, xarray |
| **Omics** | H5AD, MTX, VCF, BED | Feature/sample counts, sparsity, annotation completeness | scanpy, pyranges, cyvcf2 |

### Format Detection Strategy

1. **Extension-based**: Map file extension to category (primary method)
2. **Magic bytes**: Check file header for binary format identification (HDF5: `\x89HDF`, GZIP: `\x1f\x8b`)
3. **Content sniffing**: For ambiguous extensions (.txt, .dat, .csv), inspect first lines for delimiters, headers, or format markers
4. **Compound extensions**: Handle `.ome.tiff`, `.nii.gz`, `.tar.gz` by checking from the rightmost extension inward

### Data Quality Dimensions

- **Completeness**: Missing values, empty fields, truncated records
- **Consistency**: Matching dimensions, compatible dtypes, cross-field validation
- **Validity**: Values within expected ranges, proper encoding, format compliance
- **Provenance**: Instrument metadata, software versions, processing history
- **Uniqueness**: Duplicate records, redundant features

## Decision Framework

```
Data file received
├── What is the file type?
│   ├── Known extension → Look up in format reference
│   ├── Unknown extension → Magic bytes / content sniffing
│   └── Directory (e.g., .d, .zarr) → Check internal structure
│
├── What category does it belong to?
│   ├── Tabular → Summary stats, distributions, correlations
│   ├── Sequence → Length/quality distributions, composition
│   ├── Image → Dimensions, channels, intensity, metadata
│   ├── Spectral → Peaks, baseline, resolution, S/N
│   ├── Structural → Atom/bond validation, geometry checks
│   ├── Array → Shape, dtype, value range, sparsity
│   └── Omics → Feature counts, sample QC, annotation check
│
├── How large is the file?
│   ├── Small (<100 MB) → Load fully, comprehensive analysis
│   ├── Medium (100 MB–1 GB) → Sample or lazy evaluation
│   └── Large (>1 GB) → Stream/chunk, representative sampling
│
└── What is the analysis goal?
    ├── Pre-pipeline QC → Focus on completeness, format compliance
    ├── Data understanding → Statistics, distributions, patterns
    ├── Troubleshooting → Compare against expected format/values
    └── Documentation → Full report with recommendations
```

### Quick Reference: Analysis Approach by Data Type

| Data Type | First Check | Core Analysis | Visualization |
|-----------|------------|---------------|---------------|
| Tabular | dtypes, shape, nulls | describe(), correlations, outliers | histograms, scatter, heatmap |
| Sequence | record count, format | length dist., quality, composition | quality plots, length histogram |
| Image | dimensions, bit depth | intensity stats, channel info | thumbnail, histogram |
| Spectral | scan count, m/z range | peak detection, TIC, baseline | spectrum plot, TIC chromatogram |
| Structural | atom/residue count | B-factors, missing residues | Ramachandran, contact map |
| Array | shape, dtype | statistics, NaN check | slice visualization |
| Omics | genes × cells matrix | sparsity, QC metrics | violin plots, PCA |

## Best Practices

1. **Always check file integrity first** — verify file is complete (not truncated) and readable before deep analysis. Check file size against expectations
2. **Sample large files before full analysis** — for files with millions of records, analyze a representative sample (first N records, random sample, or stratified sample) to get quick feedback
3. **Use lazy/streaming readers when available** — `pl.scan_parquet()`, `h5py` dataset slicing, `pysam` indexed access prevent memory overflows
4. **Validate metadata against data** — cross-check stated dimensions vs actual data, verify column count matches header, confirm timestamps are monotonic
5. **Report data quality quantitatively** — "5.2% missing values in column X" is more useful than "some missing values". Include completeness percentages, outlier counts, and format compliance scores
6. **Consider data provenance** — note instrument type, software version, processing steps, and any preprocessing already applied. This context affects downstream analysis choices
7. **Generate actionable recommendations** — don't just describe the data; suggest specific preprocessing steps (normalization method, imputation strategy), appropriate analyses, and potential issues to watch for
8. **Preserve analysis reproducibility** — include library versions, parameter choices, and random seeds in reports so EDA can be reproduced
9. **Check for batch effects early** — in multi-sample datasets, compare distributions across batches, plates, or runs before combining
10. **Handle vendor-specific formats carefully** — many instruments produce proprietary formats (.nd2, .czi, .raw). Document which reader library and version was used, as format support varies

## Common Pitfalls

1. **Assuming CSV means clean tabular data** — CSV files can have inconsistent delimiters, mixed encodings, embedded newlines, or malformed quoting. *How to avoid*: Use `pd.read_csv(engine='python')` for robustness; check encoding with `chardet`

2. **Ignoring missing value encoding** — scientific data uses diverse null representations: `NA`, `NaN`, `-999`, empty string, `#N/A`, `.`. *How to avoid*: Specify `na_values` parameter; check for sentinel values in numeric columns

3. **Drawing conclusions from truncated files** — large file transfers can fail silently. *How to avoid*: Check file size, verify record counts against expected values, check for EOF markers

4. **Applying wrong reader to file** — some extensions are ambiguous (.raw = Thermo MS, XRD, or image; .d = Agilent directory or generic data). *How to avoid*: Use magic bytes and context (source instrument) to disambiguate

5. **Memory overflow on large datasets** — loading a 10 GB CSV into a pandas DataFrame will fail. *How to avoid*: Check file size first; use chunked reading, lazy evaluation, or sampling for files >100 MB

6. **Ignoring coordinate systems and units** — microscopy data may use pixels vs microns; spectroscopy data may use wavelength vs wavenumber vs energy. *How to avoid*: Extract and report units from metadata; verify calibration information

7. **Treating all columns as independent** — scientific tabular data often has hierarchical structure (replicates nested within conditions). *How to avoid*: Identify experimental design from column names and metadata before computing correlations

8. **Skipping format-specific quality metrics** — generic statistics miss domain-specific issues (e.g., Phred quality scores in FASTQ, R-factors in crystallography, mass accuracy in MS). *How to avoid*: Consult the format reference for domain-specific QC metrics

9. **Overinterpreting small samples** — EDA on first 1000 rows may not represent the full dataset's distribution. *How to avoid*: Sample from multiple positions in the file; report sample size and sampling method

10. **Not checking for duplicates** — duplicate records are common in merged datasets and database exports. *How to avoid*: Check for exact and near-duplicates early; report the duplication rate

## Workflow

### Step 1: File Identification
- Extract file extension (handle compound extensions: `.ome.tiff`, `.nii.gz`)
- Look up format in reference catalog
- If unknown: check magic bytes, inspect first lines, ask user about source instrument
- Record: format name, category, typical content, recommended libraries

### Step 2: Initial Assessment
- File size, creation date, permissions
- For binary formats: verify file integrity (header/footer checks)
- For text formats: detect encoding, delimiter, line endings
- For directories: enumerate contents and check expected structure

### Step 3: Data Loading
- Install required library if missing (provide `pip install` command)
- Use appropriate reader with explicit parameters (dtype, encoding, columns)
- For large files: load metadata first, then sample data
- Record: dimensions (rows × columns, or X×Y×Z×C×T), dtypes, memory footprint

### Step 4: Quality Assessment
- **Completeness**: count nulls per column/field, check for truncation
- **Validity**: range checks, dtype verification, format compliance
- **Consistency**: cross-field validation, duplicate detection
- **Domain-specific**: Phred scores (FASTQ), B-factors (PDB), mass accuracy (MS), intensity range (microscopy)

### Step 5: Statistical Analysis
- Summary statistics (mean, median, std, min, max, quartiles)
- Distribution characteristics (skewness, modality, outliers)
- Correlation structure (for multi-variable data)
- Domain-specific metrics (GC content, coverage, resolution, S/N ratio)

### Step 6: Report Generation
Generate a structured markdown report containing:
1. **Header**: filename, timestamp, file size
2. **Format Information**: type, description, typical use cases
3. **Data Structure**: dimensions, dtypes, memory usage
4. **Quality Assessment**: completeness scores, validity checks, issues found
5. **Statistical Summary**: key metrics and distributions
6. **Key Findings**: notable patterns, potential issues, anomalies
7. **Recommendations**: preprocessing steps, appropriate analyses, tools to use

Save as `{original_filename}_eda_report.md`.

## Bundled Resources

- `references/file_format_reference.md` — Quick-reference catalog of the most common scientific file formats across all 6 categories (bioinformatics, chemistry, microscopy, spectroscopy, proteomics/metabolomics, general), with extension, description, Python library, and key EDA approach for each format

Not migrated from original: The 6 category-specific format catalog files (3,616 lines total) contained detailed entries for 200+ formats. The bundled reference consolidates the ~50 most commonly encountered formats. For rare or vendor-specific formats, consult official library documentation.

## Further Reading

- McKinney, W. (2017). *Python for Data Analysis* (2nd ed.) — pandas-based EDA methodology
- VanderPlas, J. (2016). *Python Data Science Handbook* — EDA with matplotlib and scikit-learn
- Tukey, J. (1977). *Exploratory Data Analysis* — foundational EDA philosophy
- Bio-Formats documentation: https://www.openmicroscopy.org/bio-formats/ — microscopy format reference
- PSI standard formats: https://www.psidev.info/ — proteomics/MS data standards

## Related Skills

- **matplotlib-scientific-plotting** — visualization for EDA reports
- **polars-dataframes** — efficient tabular data loading and analysis
- **scanpy-scrna-seq** — single-cell omics EDA workflows
- **zarr-python** — chunked array data access for large datasets
- **pysam-genomic-files** — indexed access to BAM/CRAM/VCF files
