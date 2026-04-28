---
name: astropy-astronomy
description: "Core Python library for astronomy/astrophysics: units with dimensional analysis, celestial coordinate transforms (ICRS/Galactic/AltAz/FK5), FITS I/O, tables (FITS/HDF5/VOTable/CSV), cosmology (Planck18, distance/age), precise time (UTC/TAI/TT/TDB, Julian, barycentric), WCS pixel-world mapping, model fitting. For general tables use pandas/polars; for radio interferometry use CASA."
license: BSD-3-Clause
---

# Astropy — Astronomy & Astrophysics Toolkit

## Overview

Astropy is the core Python package for astronomy, providing essential functionality for astronomical research: unit-aware calculations, celestial coordinate transformations, FITS file I/O, cosmological calculations, precise time handling, tabular data operations, and WCS image coordinate mapping.

## When to Use

- Converting between celestial coordinate systems (ICRS, Galactic, FK5, AltAz)
- Working with physical quantities and units (Jy→mJy, parsec→km, spectral equivalencies)
- Reading, writing, or manipulating FITS files (images and tables)
- Cosmological calculations (luminosity distance, lookback time, comoving volume)
- Precise time handling with multiple scales (UTC, TAI, TT, TDB) and formats (JD, MJD, ISO)
- Cross-matching astronomical catalogs by sky position
- WCS transformations between pixel and world coordinates
- For **general tabular data**: use pandas or polars instead
- For **radio interferometry**: use CASA instead

## Prerequisites

```bash
pip install astropy           # Core package
pip install astropy[all]      # With optional dependencies (regions, photutils, etc.)
pip install pytz              # For timezone conversions
```

## Quick Start

```python
import astropy.units as u
from astropy.coordinates import SkyCoord
from astropy.time import Time
from astropy.io import fits
from astropy.table import Table
from astropy.cosmology import Planck18

# Units and quantities
distance = 100 * u.pc
print(f"{distance.to(u.km):.3e}")  # 3.086e+15 km

# Coordinates
coord = SkyCoord(ra=10.5*u.degree, dec=41.2*u.degree, frame='icrs')
print(f"Galactic: l={coord.galactic.l:.2f}, b={coord.galactic.b:.2f}")

# Cosmology
d_L = Planck18.luminosity_distance(z=1.0)
print(f"Luminosity distance at z=1: {d_L:.1f}")  # ~6780 Mpc

# Time
t = Time('2023-01-15 12:30:00')
print(f"JD: {t.jd:.6f}, MJD: {t.mjd:.6f}")
```

## Core API

### 1. Units & Quantities (`astropy.units`)

```python
import astropy.units as u
import numpy as np

# Create quantities
distance = 10 * u.kpc
flux = 3.5e-15 * u.erg / u.s / u.cm**2
wavelength = 6563 * u.Angstrom

# Unit conversions
distance_ly = distance.to(u.lyr)
flux_jy = flux.to(u.Jy, equivalencies=u.spectral_density(wavelength))
print(f"Distance: {distance_ly:.2f}")

# Arithmetic with automatic unit tracking
velocity = 300 * u.km / u.s
time = 1 * u.Gyr
distance_traveled = (velocity * time).to(u.Mpc)
print(f"Distance traveled: {distance_traveled:.2f}")

# Equivalencies for domain-specific conversions
freq = wavelength.to(u.Hz, equivalencies=u.spectral())
energy = wavelength.to(u.eV, equivalencies=u.spectral())
parallax_dist = (0.1 * u.arcsec).to(u.pc, equivalencies=u.parallax())
print(f"Frequency: {freq:.3e}, Parallax distance: {parallax_dist:.1f}")
```

```python
# Logarithmic units (magnitudes)
mag = -2.5 * u.mag
flux_ratio = mag.to(u.dimensionless_unscaled)

# Performance: pre-compute composite units
flux_unit = u.erg / u.s / u.cm**2 / u.Angstrom
fluxes = np.array([1e-15, 2e-15, 3e-15]) * flux_unit

# Custom units
bbl = u.def_unit('bbl', 158.987 * u.liter)
```

### 2. Coordinate Systems (`astropy.coordinates`)

```python
from astropy.coordinates import SkyCoord, EarthLocation, AltAz
from astropy.time import Time
import astropy.units as u

# Create coordinates (multiple formats)
c = SkyCoord(ra='05h23m34.5s', dec='-69d45m22s', frame='icrs')
c = SkyCoord(ra=10.5*u.degree, dec=41.2*u.degree)
c = SkyCoord(l=280*u.degree, b=-30*u.degree, frame='galactic')

# Transform between frames
c_gal = c.galactic
c_fk5 = c.fk5
print(f"Galactic: l={c_gal.l:.4f}, b={c_gal.b:.4f}")

# Observer-dependent AltAz (requires time + location)
location = EarthLocation(lat=40*u.deg, lon=-120*u.deg, height=1000*u.m)
obstime = Time('2023-06-15 23:00:00')
altaz = c.transform_to(AltAz(obstime=obstime, location=location))
print(f"Alt={altaz.alt:.2f}, Az={altaz.az:.2f}")
```

```python
# Angular separation and matching
c1 = SkyCoord(ra=10*u.deg, dec=20*u.deg)
c2 = SkyCoord(ra=10.1*u.deg, dec=20.05*u.deg)
sep = c1.separation(c2)
print(f"Separation: {sep.arcsec:.2f} arcsec")

# Catalog matching
from astropy.coordinates import match_coordinates_sky
idx, sep, _ = coords1.match_to_catalog_sky(coords2)
matches = sep < 1 * u.arcsec

# Named object lookup
m31 = SkyCoord.from_name('M31')

# 3D coordinates with distance
c3d = SkyCoord(ra=10*u.deg, dec=20*u.deg, distance=50*u.kpc)
print(f"Cartesian: {c3d.cartesian}")

# Velocity information
c_vel = SkyCoord(ra=10*u.deg, dec=20*u.deg,
                 pm_ra_cosdec=5*u.mas/u.yr, pm_dec=-3*u.mas/u.yr,
                 radial_velocity=100*u.km/u.s)
```

### 3. FITS File Handling (`astropy.io.fits`)

```python
from astropy.io import fits
import numpy as np

# Read FITS file
with fits.open('observation.fits') as hdul:
    hdul.info()                    # Show HDU structure
    data = hdul[0].data            # Image data as NumPy array
    header = hdul[0].header        # Header as dict-like object

# Access header values
exptime = header['EXPTIME']
header['OBSERVER'] = 'Smith'       # Modify
header.add_history('Processed with astropy')

# Convenience functions
data = fits.getdata('image.fits')
header = fits.getheader('image.fits')
value = fits.getval('image.fits', 'EXPTIME')
```

```python
# Create new FITS file
hdu_primary = fits.PrimaryHDU(data=np.zeros((100, 100)))
hdu_primary.header['OBJECT'] = 'M31'

# Multi-extension file
hdu_image = fits.ImageHDU(data=np.random.random((256, 256)), name='SCI')
hdu_table = fits.BinTableHDU.from_columns([
    fits.Column(name='ID', format='J', array=np.arange(100)),
    fits.Column(name='FLUX', format='E', array=np.random.random(100)),
    fits.Column(name='NAME', format='20A', array=['star']*100)
])
hdul = fits.HDUList([hdu_primary, hdu_image, hdu_table])
hdul.writeto('output.fits', overwrite=True)

# Large file handling with memory mapping
hdul = fits.open('huge.fits', memmap=True)
cutout = hdul[0].section[100:200, 100:200]  # Read only a slice
```

### 4. Table Operations (`astropy.table`)

```python
from astropy.table import Table, QTable
import astropy.units as u
import numpy as np

# Create tables
t = Table({'ra': [10.0, 20.0, 30.0], 'dec': [41.0, 42.0, 43.0],
           'mag': [15.2, 16.1, 14.8]})

# Read from file (auto-detect format)
t = Table.read('catalog.fits')
t = Table.read('data.csv', format='csv')
t = Table.read('catalog.vot', format='votable')

# Unit-aware QTable
qt = QTable({'distance': [10, 20, 30] * u.kpc,
             'flux': [1e-15, 2e-15, 3e-15] * u.erg / u.s / u.cm**2})

# Filter, sort, column operations
bright = t[t['mag'] < 15.5]
t.sort('mag')
t['abs_mag'] = t['mag'] - 5 * np.log10(100)
print(f"Rows: {len(t)}, Columns: {t.colnames}")
```

```python
# Joins and grouping
from astropy.table import join, vstack, hstack

# Database-style join
merged = join(t1, t2, keys='id', join_type='inner')

# Stack tables
combined = vstack([t1, t2, t3])       # Vertical (row-append)
combined = hstack([t_coords, t_phot])  # Horizontal (column-append)

# Group and aggregate
grouped = t.group_by('field')
stats = grouped.groups.aggregate(np.mean)

# Write
t.write('output.fits', format='fits', overwrite=True)
t.write('output.ecsv', format='ascii.ecsv')  # Preserves units + metadata
```

### 5. Time Handling (`astropy.time`)

```python
from astropy.time import Time, TimeDelta
import astropy.units as u
import numpy as np

# Create from various formats
t = Time('2023-01-15 12:30:45', format='iso', scale='utc')
t = Time(2460000.0, format='jd')
t = Time(59945.0, format='mjd')
t = Time(1673785845.0, format='unix')

# Convert between formats and scales
print(f"ISO: {t.iso}")
print(f"JD: {t.jd}, MJD: {t.mjd}")
print(f"TAI: {t.tai.iso}")      # UTC → TAI (includes leap seconds)
print(f"TDB: {t.tdb.iso}")      # UTC → Barycentric Dynamical Time

# Time arithmetic
dt = TimeDelta(7, format='jd')
t_future = t + dt
t_future = t + 1 * u.hour
duration = Time('2024-01-01') - Time('2023-01-01')
print(f"Duration: {duration.jd:.1f} days")

# Array of times
times = Time('2023-01-01') + np.arange(365) * u.day
```

```python
# Observing features
from astropy.coordinates import SkyCoord, EarthLocation

location = EarthLocation.of_site('Keck Observatory')
t = Time('2023-06-15 23:00:00', location=location)

# Sidereal time
lst = t.sidereal_time('apparent')
print(f"LST: {lst}")

# Barycentric correction
target = SkyCoord(ra='23h23m08.55s', dec='+18d24m59.3s')
ltt = t.light_travel_time(target, kind='barycentric')
t_bary = t.tdb + ltt
print(f"Barycentric correction: {ltt.sec:.3f} seconds")
```

### 6. Cosmological Calculations (`astropy.cosmology`)

```python
from astropy.cosmology import Planck18, FlatLambdaCDM
import astropy.units as u
import numpy as np

# Built-in cosmologies: Planck18, Planck15, Planck13, WMAP9, WMAP7
z = 1.5

# Distance calculations
d_L = Planck18.luminosity_distance(z)
d_A = Planck18.angular_diameter_distance(z)
d_C = Planck18.comoving_distance(z)
dm = Planck18.distmod(z)  # Distance modulus
print(f"d_L={d_L:.1f}, d_A={d_A:.1f}, d_C={d_C:.1f}")

# Time calculations
age = Planck18.age(z)
lookback = Planck18.lookback_time(z)
print(f"Age at z={z}: {age.to(u.Gyr):.2f}")
print(f"Lookback time: {lookback.to(u.Gyr):.2f}")

# Scale and volume
scale = Planck18.kpc_proper_per_arcmin(z)
vol = Planck18.comoving_volume(z)
print(f"Scale: {scale:.2f}")
```

```python
# Inverse calculations — find z for given property
from astropy.cosmology import z_at_value

z_10gyr = z_at_value(Planck18.lookback_time, 10 * u.Gyr)
z_1gpc = z_at_value(Planck18.comoving_distance, 1 * u.Gpc)
print(f"z at lookback 10 Gyr: {z_10gyr:.4f}")

# Custom cosmology
cosmo = FlatLambdaCDM(H0=70, Om0=0.3, Tcmb0=2.725)
d_L_custom = cosmo.luminosity_distance(z=1.0)

# Array operations (all methods accept arrays)
z_array = np.linspace(0.1, 3.0, 100)
distances = Planck18.luminosity_distance(z_array)
print(f"Distance array shape: {distances.shape}")  # (100,)
```

### 7. WCS & Image Processing

```python
from astropy.wcs import WCS
from astropy.io import fits
import astropy.units as u

# Read WCS from FITS
with fits.open('image.fits') as hdul:
    wcs = WCS(hdul[0].header)

# Pixel ↔ world transformations
world = wcs.pixel_to_world(100, 200)  # Returns SkyCoord
print(f"RA: {world.ra:.6f}, Dec: {world.dec:.6f}")

from astropy.coordinates import SkyCoord
coord = SkyCoord(ra=10.5*u.degree, dec=41.2*u.degree)
x, y = wcs.world_to_pixel(coord)

# WCS properties
print(f"Ref pixel: {wcs.wcs.crpix}")
print(f"Ref value: {wcs.wcs.crval}")
print(f"Pixel scale: {wcs.proj_plane_pixel_scales()}")
footprint = wcs.calc_footprint()  # Corner coordinates
```

```python
# Image visualization
from astropy.visualization import simple_norm, ZScaleInterval, AsinhStretch, ImageNormalize
import matplotlib.pyplot as plt

data = fits.getdata('image.fits')
norm = simple_norm(data, 'sqrt', percent=99)
plt.imshow(data, norm=norm, cmap='gray', origin='lower')
plt.colorbar()

# Advanced normalization
interval = ZScaleInterval()
stretch = AsinhStretch()
norm = ImageNormalize(data, interval=interval, stretch=stretch)

# Sigma clipping for robust statistics
from astropy.stats import sigma_clipped_stats
mean, median, std = sigma_clipped_stats(data, sigma=3.0)
print(f"Background: {median:.2f} ± {std:.2f}")
```

## Key Concepts

### Unit Equivalency System

Astropy's `equivalencies` parameter enables domain-specific conversions that are not dimensionally equivalent:

| Equivalency | Converts Between | Example |
|-------------|-----------------|---------|
| `u.spectral()` | Wavelength ↔ frequency ↔ energy | `(500*u.nm).to(u.THz, u.spectral())` |
| `u.spectral_density(wav)` | Flux density (Fλ ↔ Fν ↔ Jy) | `flux.to(u.Jy, u.spectral_density(wav))` |
| `u.parallax()` | Parallax angle ↔ distance | `(10*u.mas).to(u.pc, u.parallax())` |
| `u.doppler_optical(rest)` | Velocity ↔ wavelength (optical) | `vel.to(u.Angstrom, u.doppler_optical(rest))` |
| `u.brightness_temperature(freq)` | Flux ↔ temperature | For radio astronomy |

### Time Scales

| Scale | Description | Use When |
|-------|-------------|----------|
| UTC | Coordinated Universal Time (with leap seconds) | Default; civil time |
| TAI | International Atomic Time (UTC + leap seconds) | Continuous timekeeping |
| TT | Terrestrial Time (TAI + 32.184s) | Geocentric calculations |
| TDB | Barycentric Dynamical Time | Solar system dynamics, ephemerides |
| UT1 | Earth rotation angle | Sidereal time, AltAz transforms |

Access via: `t.utc`, `t.tai`, `t.tt`, `t.tdb`, `t.ut1`

### Coordinate Frame Hierarchy

- **ICRS** — International Celestial Reference System (default, ~J2000)
- **FK5** / **FK4** — Historical equatorial frames (FK4 requires equinox)
- **Galactic** — Galactic coordinates (l, b)
- **AltAz** — Observer-dependent (requires `obstime` + `location`)
- **Ecliptic** — Solar system plane
- **Galactocentric** — Galaxy-centered Cartesian

## Common Workflows

### Workflow 1: Coordinate Conversion Pipeline

```python
from astropy.coordinates import SkyCoord, EarthLocation, AltAz
from astropy.time import Time
import astropy.units as u

# Load catalog of sources
from astropy.table import Table
cat = Table.read('sources.fits')
coords = SkyCoord(ra=cat['RA']*u.degree, dec=cat['DEC']*u.degree)

# Transform to galactic
gal = coords.galactic
print(f"Galactic l range: {gal.l.min():.1f} to {gal.l.max():.1f}")

# Check observability (AltAz)
location = EarthLocation.of_site('Paranal Observatory')
obstime = Time('2023-06-15 23:00:00')
altaz = coords.transform_to(AltAz(obstime=obstime, location=location))
observable = altaz.alt > 30 * u.deg
print(f"Observable (alt>30°): {observable.sum()} of {len(coords)}")
```

### Workflow 2: FITS Image Analysis

```python
from astropy.io import fits
from astropy.wcs import WCS
from astropy.stats import sigma_clipped_stats
from astropy.visualization import simple_norm
import numpy as np

# Load image and WCS
with fits.open('science_image.fits') as hdul:
    data = hdul[0].data.astype(float)
    wcs = WCS(hdul[0].header)

# Background statistics
mean, median, std = sigma_clipped_stats(data, sigma=3.0)
print(f"Background: {median:.2f} ± {std:.2f}")

# Find bright pixels (simple threshold detection)
threshold = median + 5 * std
sources = np.where(data > threshold)
print(f"Pixels above 5σ: {len(sources[0])}")

# Convert pixel positions to sky coordinates
sky_coords = wcs.pixel_to_world(sources[1], sources[0])
print(f"RA range: {sky_coords.ra.min():.4f} to {sky_coords.ra.max():.4f}")
```

### Workflow 3: Catalog Cross-Matching

```python
from astropy.table import Table
from astropy.coordinates import SkyCoord
import astropy.units as u

# Read two catalogs
cat1 = Table.read('catalog1.fits')
cat2 = Table.read('catalog2.fits')

coords1 = SkyCoord(ra=cat1['RA']*u.degree, dec=cat1['DEC']*u.degree)
coords2 = SkyCoord(ra=cat2['RA']*u.degree, dec=cat2['DEC']*u.degree)

# Match
idx, sep, _ = coords1.match_to_catalog_sky(coords2)
max_sep = 1 * u.arcsec
matches = sep < max_sep

cat1_matched = cat1[matches]
cat2_matched = cat2[idx[matches]]
print(f"Matched: {matches.sum()} of {len(cat1)} (within {max_sep})")
```

## Key Parameters

| Parameter | Module | Default | Description |
|-----------|--------|---------|-------------|
| `frame` | SkyCoord | `'icrs'` | Coordinate reference frame |
| `scale` | Time | `'utc'` | Time scale (utc, tai, tt, tdb, ut1) |
| `format` | Time | auto | Time format (iso, jd, mjd, unix, etc.) |
| `equivalencies` | `.to()` | None | Domain-specific unit conversion rules |
| `memmap` | `fits.open` | True | Memory-map large files |
| `join_type` | `join()` | `'inner'` | Join type (inner, outer, left, right) |
| `sigma` | `sigma_clip` | 3.0 | Clipping threshold in standard deviations |
| `stretch` | `simple_norm` | `'linear'` | Image stretch (linear, sqrt, log, asinh) |
| `percent` | `simple_norm` | 100 | Percentile for normalization limits |

## Best Practices

1. **Always attach units** — Use `Quantity` objects (e.g., `10 * u.kpc`) to prevent dimensional errors. Bare numbers silently produce wrong results.

2. **Use context managers for FITS** — `with fits.open(...) as hdul:` ensures proper file closing and memory map cleanup.

3. **Process arrays, not loops** — All astropy operations accept arrays. Process 10,000 coordinates at once instead of looping.

4. **Be explicit about time scales** — `Time('2023-01-15', scale='utc')` prevents ambiguity. UTC↔TDB differences matter for precision timing.

5. **Use QTable for unit-aware columns** — `QTable` preserves units through I/O; plain `Table` stores units as metadata only.

6. **Use ECSV for round-trip fidelity** — `t.write('file.ecsv')` preserves units, dtypes, and metadata. CSV/FITS lose some metadata.

7. **Anti-pattern — Wrong cosmology model**: Always specify which cosmology you're using. Different models give different distances at the same redshift. Planck18 is current standard.

8. **Anti-pattern — Ignoring WCS origin convention**: astropy uses 0-based pixel coordinates. FITS standard uses 1-based. Use `wcs.pixel_to_world()` (handles this automatically) instead of manual calculations.

## Common Recipes

### Recipe: Custom Cosmology with Neutrinos

```python
from astropy.cosmology import FlatLambdaCDM
import astropy.units as u

cosmo = FlatLambdaCDM(
    H0=67.66, Om0=0.3111, Tcmb0=2.7255,
    Neff=3.046, m_nu=[0, 0, 0.06] * u.eV
)
print(f"Age of universe: {cosmo.age(0).to(u.Gyr):.3f}")
```

### Recipe: Model Fitting

```python
from astropy.modeling import models, fitting
import numpy as np

# Generate noisy Gaussian data
x = np.linspace(0, 10, 100)
y = 10 * np.exp(-0.5 * ((x - 5) / 1.0)**2) + np.random.normal(0, 0.5, 100)

# Fit
fitter = fitting.LevMarLSQFitter()
model = models.Gaussian1D(amplitude=8, mean=4, stddev=1.5)
fitted = fitter(model, x, y)
print(f"Amplitude: {fitted.amplitude.value:.2f}")
print(f"Mean: {fitted.mean.value:.2f}")
print(f"Stddev: {fitted.stddev.value:.2f}")
```

### Recipe: NDData and CCDData

```python
from astropy.nddata import CCDData, StdDevUncertainty
import astropy.units as u
import numpy as np

# Create CCDData with uncertainty
data = np.random.random((256, 256))
uncertainty = StdDevUncertainty(np.sqrt(np.abs(data)))
ccd = CCDData(data, unit=u.adu, uncertainty=uncertainty,
              meta={'OBJECT': 'M31', 'EXPTIME': 300.0})

# Read/write
ccd.write('processed.fits', overwrite=True)
ccd2 = CCDData.read('processed.fits', unit=u.adu)
```

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| `UnitConversionError` | Incompatible units without equivalency | Add `equivalencies=u.spectral()` or appropriate equivalency |
| Wrong coordinate frame after transform | Missing `obstime`/`location` for AltAz | Provide both: `AltAz(obstime=t, location=loc)` |
| `ErfaWarning: dubious year` | Time outside 1960–2040 range for UT1 | Use `scale='tt'` or `scale='tdb'` for extreme dates |
| `FileNotFoundError` for IERS data | Leap second table not downloaded | Run `from astropy.utils.iers import IERS_Auto; IERS_Auto.open()` |
| FITS header `VerifyError` | Non-standard FITS keywords | Use `fits.open(f, ignore_missing_end=True)` or `hdul.verify('fix')` |
| Slow coordinate transforms | Looping over single coordinates | Use array SkyCoord: `SkyCoord(ra=ra_array, dec=dec_array)` |
| `QTable` loses units on write | Using CSV format | Use ECSV format: `qt.write('file.ecsv')` |
| `KeyError` accessing FITS extension | Wrong extension index | Use `hdul.info()` to see structure; access by name: `hdul['SCI']` |
| Inaccurate barycentric correction | Wrong time scale or missing location | Use `scale='utc'`, set `location` on Time object |
| `ModelFit` doesn't converge | Bad initial parameters | Provide closer initial guesses; try `SimplexLSQFitter` |

## Bundled Resources

- **`references/data_io_guide.md`** — Detailed FITS operations (headers, multi-extension, binary tables, column format codes, memory mapping, remote access), Table operations (creation, I/O formats, joins, grouping, indexing, QTable, masked data, display, performance), and collection conversion patterns. Consolidated from original `fits.md` and `tables.md`.
- **`references/coordinates_time_cosmology.md`** — Complete coordinate system reference (all frames, 3D coordinates, proper motions, representations, catalog matching), time handling (all formats, all scales, TimeDelta, sidereal time, light travel time, barycentric corrections, precision), and cosmological models (all built-ins, custom models, distances, volumes, inverse calculations, neutrino effects). Consolidated from original `coordinates.md`, `time.md`, and `cosmology.md`.
- **`references/auxiliary_modules.md`** — WCS detailed operations, NDData/CCDData, modeling framework (1D/2D models, fitting, compound models), image visualization (stretches, intervals, normalization), constants catalog, convolution, robust statistics, SAMP interoperability, data download utilities. Consolidated from original `wcs_and_other_modules.md` and `units.md` (equivalency details).

Not migrated as separate files: Original had 7 reference files. Consolidated into 3 topical reference files covering all capabilities. `units.md` equivalency content split between SKILL.md Key Concepts (summary table) and `auxiliary_modules.md` (detailed code).

## Related Skills

- **matplotlib-scientific-plotting** — Visualization library used for astropy image display and plot generation
- **zarr-python** — Chunked array storage; used with astropy for large astronomical datasets

## References

- Official Documentation: https://docs.astropy.org/en/stable/
- Tutorials: https://learn.astropy.org/
- GitHub: https://github.com/astropy/astropy
- Coordinate Frame Reference: https://docs.astropy.org/en/stable/coordinates/
