# Matchms Filter Functions Catalog

Complete catalog of 50+ matchms filter functions for mass spectrometry data processing.

## Metadata Processing Filters

### Compound & Chemical Information

| Function | Description |
|----------|-------------|
| `add_compound_name(spectrum)` | Adds/standardizes compound name to correct metadata field |
| `clean_compound_name(spectrum)` | Removes unwanted additions and formatting inconsistencies |
| `derive_adduct_from_name(spectrum)` | Extracts adduct information from compound names |
| `derive_formula_from_name(spectrum)` | Detects and relocates chemical formulas from compound names |
| `derive_annotation_from_compound_name(spectrum)` | Retrieves SMILES/InChI from PubChem using compound name |

### Chemical Structure Conversions

| Function | Description |
|----------|-------------|
| `derive_inchi_from_smiles(spectrum)` | Generates InChI from SMILES (requires rdkit) |
| `derive_inchikey_from_inchi(spectrum)` | Computes 27-character InChIKey from InChI |
| `derive_smiles_from_inchi(spectrum)` | Creates SMILES from InChI (requires rdkit) |
| `repair_inchi_inchikey_smiles(spectrum)` | Corrects misplaced chemical identifiers between fields |
| `repair_not_matching_annotation(spectrum)` | Ensures consistency between SMILES, InChI, and InChIKey |
| `add_fingerprint(spectrum, fingerprint_type="daylight", nbits=2048, radius=2)` | Generates molecular fingerprints; types: "daylight", "morgan1"/"morgan2"/"morgan3" |

### Mass & Charge Information

| Function | Description |
|----------|-------------|
| `add_precursor_mz(spectrum)` | Normalizes and standardizes precursor m/z metadata |
| `add_parent_mass(spectrum, estimate_from_adduct=True)` | Calculates neutral parent mass from precursor m/z and adduct |
| `correct_charge(spectrum)` | Aligns charge sign with ionization mode |
| `make_charge_int(spectrum)` | Converts charge to integer format |
| `clean_adduct(spectrum)` | Standardizes adduct notation and corrects formatting |
| `interpret_pepmass(spectrum)` | Parses pepmass field into precursor m/z and intensity components |

### Ion Mode & Validation

| Function | Description |
|----------|-------------|
| `derive_ionmode(spectrum)` | Determines ionmode from adduct information |
| `require_correct_ionmode(spectrum, ion_mode)` | Returns None if ionmode does not match specified mode |
| `require_precursor_mz(spectrum, minimum_accepted_mz=0.0)` | Returns None if precursor m/z missing or below threshold |
| `require_precursor_below_mz(spectrum, maximum_accepted_mz=1000.0)` | Returns None if precursor exceeds maximum m/z |

### Retention Information

| Function | Description |
|----------|-------------|
| `add_retention_time(spectrum)` | Harmonizes retention time as float values |
| `add_retention_index(spectrum)` | Stores retention index in standardized field |

### Data Harmonization

| Function | Description |
|----------|-------------|
| `harmonize_undefined_inchi(spectrum, undefined="", aliases=None)` | Standardizes undefined/empty InChI entries |
| `harmonize_undefined_inchikey(spectrum, undefined="", aliases=None)` | Standardizes undefined/empty InChIKey entries |
| `harmonize_undefined_smiles(spectrum, undefined="", aliases=None)` | Standardizes undefined/empty SMILES entries |

### Repair & Quality

| Function | Description |
|----------|-------------|
| `repair_adduct_based_on_smiles(spectrum, mass_tolerance=0.1)` | Corrects adduct using SMILES and mass matching |
| `repair_parent_mass_is_mol_wt(spectrum, mass_tolerance=0.1)` | Converts molecular weight to monoisotopic mass |
| `repair_precursor_is_parent_mass(spectrum)` | Fixes swapped precursor/parent mass values |
| `repair_smiles_of_salts(spectrum, mass_tolerance=0.1)` | Removes salt components to match parent mass |
| `require_parent_mass_match_smiles(spectrum, mass_tolerance=0.1)` | Returns None if parent mass does not match SMILES-calculated mass |
| `require_valid_annotation(spectrum)` | Validates SMILES, InChI, and InChIKey presence and consistency |

## Peak Processing Filters

| Function | Description |
|----------|-------------|
| `normalize_intensities(spectrum)` | Scales peak intensities to unit height (max = 1.0) |
| `select_by_intensity(spectrum, intensity_from=0.0, intensity_to=1.0)` | Retains peaks within absolute intensity range |
| `select_by_relative_intensity(spectrum, intensity_from=0.0, intensity_to=1.0)` | Keeps peaks within relative intensity bounds (fraction of max) |
| `select_by_mz(spectrum, mz_from=0.0, mz_to=1000.0)` | Filters peaks by m/z value range |
| `reduce_to_number_of_peaks(spectrum, n_max=None, ratio_desired=None)` | Removes lowest-intensity peaks when exceeding maximum |
| `remove_peaks_around_precursor_mz(spectrum, mz_tolerance=17)` | Eliminates peaks near precursor (removes precursor/isotope peaks) |
| `remove_peaks_outside_top_k(spectrum, k=10, ratio_desired=None)` | Retains only peaks near k highest-intensity peaks |
| `require_minimum_number_of_peaks(spectrum, n_required=10)` | Returns None if peak count below threshold |
| `require_minimum_number_of_high_peaks(spectrum, n_required=5, intensity_threshold=0.05)` | Returns None if insufficient peaks above intensity threshold |
| `add_losses(spectrum, loss_mz_from=5.0, loss_mz_to=200.0)` | Derives neutral losses (precursor_mz - fragment_mz) for NeutralLossesCosine |

## Pipeline Functions

**`default_filters(spectrum)`** -- Applies nine essential metadata filters sequentially:
make_charge_int, add_precursor_mz, add_retention_time, add_retention_index,
derive_adduct_from_name, derive_formula_from_name, clean_compound_name,
harmonize_undefined_smiles, harmonize_undefined_inchi.

**`SpectrumProcessor(filters)`** -- Orchestrates multi-filter pipelines from a list of filter functions.

## Example Pipelines

### Strict QC Pipeline
```python
from matchms.filtering import (default_filters, normalize_intensities,
    require_precursor_mz, require_minimum_number_of_peaks,
    require_minimum_number_of_high_peaks,
    remove_peaks_around_precursor_mz, select_by_relative_intensity)

def strict_qc(spectrum):
    spectrum = default_filters(spectrum)
    spectrum = require_precursor_mz(spectrum, minimum_accepted_mz=50.0)
    if spectrum is None: return None
    spectrum = require_minimum_number_of_peaks(spectrum, n_required=10)
    if spectrum is None: return None
    spectrum = normalize_intensities(spectrum)
    spectrum = remove_peaks_around_precursor_mz(spectrum, mz_tolerance=17)
    spectrum = select_by_relative_intensity(spectrum, intensity_from=0.01)
    spectrum = require_minimum_number_of_high_peaks(spectrum, n_required=5, intensity_threshold=0.05)
    return spectrum
```

### Chemical Enrichment Pipeline
```python
from matchms.filtering import (default_filters, derive_inchi_from_smiles,
    derive_inchikey_from_inchi, add_fingerprint,
    repair_not_matching_annotation, require_valid_annotation)

def chemical_enrichment(spectrum):
    spectrum = default_filters(spectrum)
    spectrum = derive_inchi_from_smiles(spectrum)
    spectrum = derive_inchikey_from_inchi(spectrum)
    spectrum = repair_not_matching_annotation(spectrum)
    spectrum = add_fingerprint(spectrum, fingerprint_type="morgan2", nbits=2048)
    spectrum = require_valid_annotation(spectrum)
    return spectrum
```

### Minimal Noise Removal + SpectrumProcessor
```python
from matchms import SpectrumProcessor
from matchms.filtering import (default_filters, normalize_intensities,
    select_by_relative_intensity, reduce_to_number_of_peaks)

pipeline = SpectrumProcessor([
    default_filters, normalize_intensities,
    lambda s: select_by_relative_intensity(s, intensity_from=0.01),
    lambda s: reduce_to_number_of_peaks(s, n_max=200)
])
processed = [pipeline(s) for s in spectra if pipeline(s) is not None]
```

## Notes on Filter Usage

1. **Order matters**: Apply filters in logical sequence (normalize before relative intensity selection)
2. **Filters return None**: Many filters return None for invalid spectra; always check before proceeding
3. **Immutability**: Filters return modified copies; reassign results to variables
4. **Pipeline efficiency**: Use SpectrumProcessor for consistent multi-spectrum processing

---

> **Condensation note**: Condensed from original: filtering.md (289 lines). Retained: all 50+ filter functions organized by category with descriptions. Relocated to SKILL.md: key filters (default_filters, normalize_intensities, select_by_relative_intensity, reduce_to_number_of_peaks, remove_peaks_around_precursor_mz, add_fingerprint, add_losses) in Core API Module 2; filter category summary table in Key Concepts. Omitted: individual per-filter code examples -- patterns shown in SKILL.md Core API Module 2 apply to all filters.
