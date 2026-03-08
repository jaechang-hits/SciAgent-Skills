# Scientific File Format Quick Reference

Consolidated reference of the most commonly encountered scientific file formats, organized by domain. For each format: extension, description, recommended Python library, and key EDA approach.

## Bioinformatics & Genomics

| Extension | Description | Python Library | Key EDA Approach |
|-----------|------------|---------------|------------------|
| `.fasta` / `.fa` | Nucleotide/protein sequences | `BioPython (Bio.SeqIO)` | Sequence count, length distribution, composition (GC%) |
| `.fastq` / `.fq` | Sequences with quality scores | `BioPython`, `pysam` | Read count, length dist., Phred quality, GC content |
| `.sam` | Sequence Alignment/Map (text) | `pysam` | Alignment stats, mapping quality, CIGAR operations |
| `.bam` | Binary Alignment/Map | `pysam` | Same as SAM; check index (.bai), coverage depth |
| `.vcf` | Variant Call Format | `cyvcf2`, `pyvcf3` | Variant count, type dist. (SNP/indel), quality, allele freq. |
| `.bed` | Browser Extensible Data | `pyranges`, `pybedtools` | Region count, size distribution, chromosome coverage |
| `.gff` / `.gtf` | Gene annotations | `gffutils`, `pyranges` | Feature types, gene count, transcript structure |
| `.bigWig` / `.bw` | Continuous signal track | `pyBigWig` | Signal range, chromosome coverage, bin statistics |
| `.h5ad` | AnnData (single-cell) | `scanpy`, `anndata` | Genes × cells, sparsity, obs/var annotations |
| `.mtx` | Matrix Market (sparse) | `scipy.io.mmread` | Dimensions, sparsity, value distribution |

## Chemistry & Molecular

| Extension | Description | Python Library | Key EDA Approach |
|-----------|------------|---------------|------------------|
| `.pdb` | Protein Data Bank | `BioPython (Bio.PDB)`, `MDAnalysis` | Atom/residue count, B-factors, missing residues, Ramachandran |
| `.cif` (structure) | Macromolecular CIF | `gemmi`, `BioPython` | Unit cell, space group, resolution, R-factors |
| `.mol` / `.mol2` | MDL Molfile / Tripos | `RDKit`, `datamol` | Atom count, bond types, charges, 2D/3D coords |
| `.sdf` | Structure-Data File | `RDKit`, `datamol` | Multi-molecule: count, MW distribution, property fields |
| `.xyz` | XYZ coordinates | `ase`, `cclib` | Atom count, element types, geometry (bond lengths) |
| `.smi` | SMILES strings | `RDKit`, `datamol` | Parse success rate, MW dist., ring count, validity |
| `.gro` | GROMACS coordinate | `MDAnalysis` | Atom count, box dimensions, residue types |
| `.dcd` / `.xtc` | MD trajectories | `MDAnalysis`, `mdtraj` | Frame count, time range, RMSD, dimensions |
| `.log` (Gaussian) | QM calculation output | `cclib` | Convergence, energy, orbital info, frequencies |
| `.cube` | Gaussian cube | `cclib`, `numpy` | Grid dimensions, orbital/density values, atom positions |

## Microscopy & Imaging

| Extension | Description | Python Library | Key EDA Approach |
|-----------|------------|---------------|------------------|
| `.tif` / `.tiff` | Tagged Image File | `tifffile`, `PIL` | Dimensions, bit depth, pages, metadata tags |
| `.ome.tiff` | OME-TIFF (standardized) | `tifffile`, `aicsimageio` | XYZCT dimensions, channel info, pixel size |
| `.nd2` | Nikon NIS-Elements | `nd2reader`, `aicsimageio` | Channels, Z-stacks, timepoints, calibration |
| `.czi` | Carl Zeiss Image | `aicspylibczi`, `aicsimageio` | Scenes, channels, tiles, pixel size |
| `.lif` | Leica Image File | `readlif`, `aicsimageio` | Series count, dimensions, channel wavelengths |
| `.ims` | Imaris format | `h5py` (HDF5-based) | Resolution levels, time points, channel info |
| `.dcm` | DICOM medical imaging | `pydicom` | Patient/study metadata, modality, pixel data shape |
| `.nii` / `.nii.gz` | NIfTI neuroimaging | `nibabel` | Voxel dimensions, affine transform, data shape |
| `.mrc` | MRC (cryo-EM) | `mrcfile` | Grid size, pixel spacing, map statistics |
| `.svs` | Aperio whole-slide | `openslide` | Magnification levels, dimensions, tile structure |

## Spectroscopy & Analytical

| Extension | Description | Python Library | Key EDA Approach |
|-----------|------------|---------------|------------------|
| `.mzML` | Mass spec standard XML | `pymzml`, `pyteomics` | Scan count, MS levels, RT range, m/z range, TIC |
| `.mgf` | Mascot Generic Format | `pyteomics.mgf` | Spectrum count, charge states, precursor m/z |
| `.raw` (Thermo) | Thermo instrument raw | `pymsfilereader` | Method params, scan functions, calibration |
| `.fid` | NMR free induction decay | `nmrglue` | Time-domain points, sampling rate, S/N estimation |
| `.spc` | Galactic spectroscopy | `spc` | Wavenumber range, data points, multi-spectrum info |
| `.jdx` / `.jcamp` | JCAMP-DX standard | `jcamp` | Spectrum type, metadata, peak table |
| `.cif` (crystal) | Crystallographic info | `gemmi`, `pymatgen` | Unit cell, space group, R-factors, completeness |
| `.xy` / `.xye` | Powder diffraction | `pymatgen`, `pandas` | 2-theta range, peak positions, background |
| `.wdf` | Renishaw Raman | `renishawWiRE` | Laser wavelength, spectral vs map mode, spatial coords |
| `.dta` | Thermal analysis (DSC/TGA) | `pandas` (exported) | Transition temperatures, enthalpy, mass loss steps |

## Proteomics & Metabolomics

| Extension | Description | Python Library | Key EDA Approach |
|-----------|------------|---------------|------------------|
| `.mzML` (proteomics) | Proteomics MS data | `pyteomics.mzml` | MS1/MS2 ratio, precursor distribution, RT coverage |
| `.mzIdentML` | Identification results | `pyteomics.mzid` | PSM count, score dist., FDR, modification types |
| `.pepXML` | TPP peptide results | `pyteomics.pepxml` | Search scores, enzyme specificity, decoy ratio |
| `.mzTab` | Quantitation results | `pyteomics`, `pandas` | Protein/peptide counts, quantitation completeness |
| `.sky` | Skyline targeted MS | Skyline API | Transition count, peak areas, CV across replicates |
| `.cdf` / `.netCDF` | ANDI-MS format | `netCDF4`, `scipy.io` | Scan count, TIC profile, mass range |
| `.nmrML` | NMR standard format | `nmrglue` | Acquisition params, pulse program, dimension info |
| `.featureXML` | OpenMS features | `pyopenms` | Feature count, RT × m/z coverage, intensity range |

## General Scientific

| Extension | Description | Python Library | Key EDA Approach |
|-----------|------------|---------------|------------------|
| `.csv` / `.tsv` | Delimited text | `pandas`, `polars` | Shape, dtypes, nulls, statistics, correlations |
| `.xlsx` | Excel spreadsheet | `openpyxl`, `pandas` | Sheet count, dimensions, merged cells, formulas |
| `.json` | JSON data | `json`, `pandas` | Structure depth, key inventory, array lengths |
| `.hdf5` / `.h5` | Hierarchical Data Format | `h5py` | Groups/datasets tree, shapes, dtypes, compression |
| `.zarr` | Chunked arrays | `zarr` | Chunk layout, compressor, shape, dtype |
| `.npy` / `.npz` | NumPy arrays | `numpy` | Shape, dtype, value range, NaN/Inf count |
| `.parquet` | Columnar binary | `polars`, `pyarrow` | Schema, row groups, statistics, compression |
| `.nc` / `.netcdf` | NetCDF (climate/ocean) | `xarray`, `netCDF4` | Dimensions, variables, coordinates, attributes |
| `.mat` | MATLAB data | `scipy.io.loadmat` | Variable names, shapes, dtypes |
| `.fits` | FITS (astronomy) | `astropy.io.fits` | HDU list, header keywords, data shape, WCS info |

## Format Disambiguation

Some extensions are ambiguous. Use context to disambiguate:

| Extension | Possible Formats | How to Distinguish |
|-----------|-----------------|-------------------|
| `.raw` | Thermo MS, XRD vendor, image | Source instrument; magic bytes |
| `.cif` | Macromolecular (mmCIF) vs crystallographic (small molecule) | Check for `_atom_site` vs `_cell_length_a` blocks |
| `.d` | Agilent data directory vs generic data | Is it a directory? Check internal file structure |
| `.dat` | Binary spectroscopy vs text data | Try text read first; check magic bytes |
| `.log` | Gaussian QM vs generic log | Check for "Gaussian" or "Entering Link" in first lines |
| `.h5` | HDF5 generic vs OME-HDF5 vs AnnData | Check group structure: `/obs`, `/var` = AnnData |
| `.txt` | Spectroscopy export vs generic text | Check for numeric columns with wavelength/wavenumber headers |

Condensed from original: 6 domain-specific catalogs (3,616 lines total covering 200+ formats). This reference covers the ~50 most commonly encountered formats. For rare vendor-specific formats (Shimadzu .lcd, Waters .arw, SCIEX .wiff, etc.), consult the instrument vendor's documentation or specialized reader libraries.
