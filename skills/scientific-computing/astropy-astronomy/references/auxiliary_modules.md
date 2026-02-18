# Astropy Auxiliary Modules Reference

WCS operations, NDData, modeling, visualization, constants, convolution, statistics, and utilities.

## World Coordinate System (`astropy.wcs`)

### Reading and Creating WCS

```python
from astropy.wcs import WCS
from astropy.io import fits

# From FITS header
with fits.open('image.fits') as hdul:
    wcs = WCS(hdul[0].header)

# Create new WCS
wcs = WCS(naxis=2)
wcs.wcs.crpix = [512.0, 512.0]
wcs.wcs.crval = [10.5, 41.2]
wcs.wcs.ctype = ['RA---TAN', 'DEC--TAN']
wcs.wcs.cdelt = [-0.0001, 0.0001]  # degrees/pixel
wcs.wcs.cunit = ['deg', 'deg']
```

### Transformations

```python
import numpy as np

# Pixel → world
world = wcs.pixel_to_world(100, 200)  # Returns SkyCoord
x_pix = np.array([100, 200, 300])
y_pix = np.array([150, 250, 350])
world_arr = wcs.pixel_to_world(x_pix, y_pix)

# World → pixel
from astropy.coordinates import SkyCoord
import astropy.units as u
coord = SkyCoord(ra=10.5*u.deg, dec=41.2*u.deg)
x, y = wcs.world_to_pixel(coord)

# Properties
print(wcs.wcs.crpix)  # Reference pixel
print(wcs.wcs.crval)  # Reference value
print(wcs.wcs.cd)     # CD matrix
pixel_scale = wcs.proj_plane_pixel_scales()
footprint = wcs.calc_footprint()
```

## NDData and CCDData (`astropy.nddata`)

```python
from astropy.nddata import NDData, CCDData, StdDevUncertainty
import numpy as np
import astropy.units as u

# NDData with uncertainty and mask
data = np.random.random((100, 100))
uncertainty = StdDevUncertainty(np.sqrt(data))
mask = data < 0.1
ndd = NDData(data, uncertainty=uncertainty, mask=mask, unit=u.electron/u.s)

# CCDData for CCD images
ccd = CCDData(data, unit=u.adu, meta={'OBJECT': 'M31'})
ccd = CCDData.read('image.fits', unit=u.adu)
ccd.write('output.fits', overwrite=True)

# With WCS
ndd = NDData(data, wcs=wcs)
```

## Modeling (`astropy.modeling`)

### Common Models

```python
from astropy.modeling import models, fitting
import numpy as np

# 1D models
gauss = models.Gaussian1D(amplitude=10, mean=5, stddev=1)
poly = models.Polynomial1D(degree=3)
plaw = models.PowerLaw1D(amplitude=10, x_0=1, alpha=2)
lorentz = models.Lorentz1D(amplitude=10, x_0=5, fwhm=1)

# 2D models
gauss2d = models.Gaussian2D(amplitude=10, x_mean=50, y_mean=50,
                              x_stddev=5, y_stddev=3)
const2d = models.Const2D(amplitude=1.0)
```

### Fitting

```python
# Generate data
x = np.linspace(0, 10, 100)
y_true = 10 * np.exp(-0.5 * ((x - 5) / 1.0)**2)
y_noisy = y_true + np.random.normal(0, 0.5, 100)

# Levenberg-Marquardt fitter
fitter = fitting.LevMarLSQFitter()
model = models.Gaussian1D(amplitude=8, mean=4, stddev=1.5)
fitted = fitter(model, x, y_noisy)

print(f"Amplitude: {fitted.amplitude.value:.3f}")
print(f"Mean: {fitted.mean.value:.3f}")
print(f"Stddev: {fitted.stddev.value:.3f}")

# Fit info
print(fitter.fit_info['message'])
```

### Compound Models

```python
# Addition (multiple components)
double_gauss = (models.Gaussian1D(amplitude=5, mean=3, stddev=1) +
                models.Gaussian1D(amplitude=8, mean=7, stddev=1.5))

# Composition (pipeline)
scaled = (models.Gaussian1D(amplitude=10, mean=5, stddev=1) |
          models.Scale(factor=2))

# Fit compound model
fitter = fitting.LevMarLSQFitter()
fitted_compound = fitter(double_gauss, x, y_noisy)
```

## Visualization (`astropy.visualization`)

### Image Normalization

```python
from astropy.visualization import simple_norm, ImageNormalize
from astropy.visualization import (MinMaxInterval, ZScaleInterval,
    PercentileInterval, AsinhStretch, SqrtStretch, LogStretch)
import matplotlib.pyplot as plt

data = fits.getdata('image.fits')

# Simple normalization
norm = simple_norm(data, 'sqrt', percent=99)
plt.imshow(data, norm=norm, cmap='gray', origin='lower')
```

### Stretches and Intervals

```python
# Z-scale (DS9-like)
interval = ZScaleInterval()
vmin, vmax = interval.get_limits(data)

# Percentile
interval = PercentileInterval(95)

# Stretches
stretch = AsinhStretch()     # Arcsinh (good for high dynamic range)
stretch = SqrtStretch()      # Square root
stretch = LogStretch(a=1000) # Logarithmic

# Combined normalization
norm = ImageNormalize(data, interval=ZScaleInterval(), stretch=AsinhStretch())
plt.imshow(data, norm=norm, cmap='gray', origin='lower')
plt.colorbar()
```

## Constants (`astropy.constants`)

```python
from astropy import constants as const
import astropy.units as u

# Fundamental
c = const.c           # Speed of light
G = const.G           # Gravitational constant
h = const.h           # Planck constant
hbar = const.hbar     # Reduced Planck
k_B = const.k_B       # Boltzmann constant
e = const.e           # Elementary charge
N_A = const.N_A       # Avogadro

# Astronomical
M_sun = const.M_sun   # Solar mass
R_sun = const.R_sun   # Solar radius
L_sun = const.L_sun   # Solar luminosity
au = const.au         # Astronomical unit
pc = const.pc         # Parsec
M_earth = const.M_earth
R_earth = const.R_earth

# Electron/proton
m_e = const.m_e
m_p = const.m_p

# Usage in calculations
r_s = 2 * G * (10 * M_sun) / c**2  # Schwarzschild radius
v_esc = (2 * G * M_earth / R_earth)**0.5  # Escape velocity
print(f"Schwarzschild radius: {r_s.to(u.km):.2f}")
print(f"Escape velocity: {v_esc.to(u.km/u.s):.2f}")
```

## Unit Equivalencies (Detailed)

```python
import astropy.units as u

# Spectral: wavelength ↔ frequency ↔ energy
wav = 500 * u.nm
freq = wav.to(u.THz, equivalencies=u.spectral())
energy = wav.to(u.eV, equivalencies=u.spectral())

# Spectral density: Fλ ↔ Fν
flux_lam = 1e-17 * u.erg / u.s / u.cm**2 / u.Angstrom
flux_nu = flux_lam.to(u.Jy, equivalencies=u.spectral_density(6563 * u.Angstrom))

# Doppler shifts
rest = 6563 * u.Angstrom
vel = 1000 * u.km / u.s
shifted = vel.to(u.Angstrom, equivalencies=u.doppler_optical(rest))

# Parallax
parallax = 10 * u.mas
dist = parallax.to(u.pc, equivalencies=u.parallax())

# Brightness temperature (radio)
freq = 1.4 * u.GHz
flux = 1 * u.Jy
temp = flux.to(u.K, equivalencies=u.brightness_temperature(freq))

# Mass-energy
mass = 1 * u.kg
energy = mass.to(u.J, equivalencies=u.mass_energy())

# Logarithmic units
mag = -2.5 * u.mag
ratio = mag.to(u.dimensionless_unscaled)

# Custom units
bbl = u.def_unit('bbl', 158.987 * u.liter)
```

## Convolution (`astropy.convolution`)

```python
from astropy.convolution import (Gaussian2DKernel, Box2DKernel,
    Tophat2DKernel, convolve, convolve_fft)

# Gaussian smoothing
kernel = Gaussian2DKernel(x_stddev=2)
smoothed = convolve(data, kernel)

# FFT convolution (faster for large kernels, handles NaN)
smoothed = convolve_fft(data, kernel, nan_treatment='interpolate')

# Box filter
kernel = Box2DKernel(5)
smoothed = convolve(data, kernel)
```

## Statistics (`astropy.stats`)

```python
from astropy.stats import (sigma_clip, sigma_clipped_stats,
    mad_std, biweight_location, biweight_scale)

# Sigma clipping
clipped = sigma_clip(data, sigma=3, maxiters=5)

# Clipped statistics
mean, median, std = sigma_clipped_stats(data, sigma=3.0)

# Robust statistics
robust_std = mad_std(data)
robust_center = biweight_location(data)
robust_scale = biweight_scale(data)
```

## Utilities

```python
# Data downloads with caching
from astropy.utils.data import download_file
local_file = download_file('https://example.com/data.fits', cache=True)

# Progress bar
from astropy.utils.console import ProgressBar
with ProgressBar(1000) as bar:
    for i in range(1000):
        bar.update()

# SAMP (interoperability)
from astropy.samp import SAMPIntegratedClient
client = SAMPIntegratedClient()
client.connect()
# Broadcast tables/images to other tools (DS9, TOPCAT, Aladin)
client.disconnect()
```

Condensed from original: wcs_and_other_modules.md (374 lines) + units.md equivalency details (179 lines) = 553 lines total. Retained: all WCS operations, NDData/CCDData, all model types + fitting + compound models, all visualization stretches/intervals, complete constants catalog, all equivalencies with examples, convolution, robust statistics, SAMP, download utilities. Omitted: verbose prose introductions already in SKILL.md, basic unit creation/arithmetic (covered in SKILL.md Core API Section 1).
