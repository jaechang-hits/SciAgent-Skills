# Astropy Coordinates, Time & Cosmology Reference

Complete reference for coordinate transformations, time handling, and cosmological calculations.

## Coordinate Systems

### SkyCoord Creation Formats

```python
from astropy.coordinates import SkyCoord
import astropy.units as u

# Decimal degrees
c = SkyCoord(ra=10.5*u.degree, dec=41.2*u.degree)

# Sexagesimal
c = SkyCoord(ra='05h23m34.5s', dec='-69d45m22s')
c = SkyCoord('05:23:34.5 -69:45:22', unit=(u.hourangle, u.deg))

# Galactic
c = SkyCoord(l=280*u.degree, b=-30*u.degree, frame='galactic')

# Array of coordinates
c = SkyCoord(ra=[10, 20, 30]*u.deg, dec=[41, 42, 43]*u.deg)

# Access components
print(c.ra.deg, c.ra.hms, c.dec.deg, c.dec.dms)
print(c.to_string('hmsdms'))
```

### Frame Transformations

```python
# Standard frames
c_icrs = c.icrs         # Default reference frame
c_fk5 = c.fk5           # Equatorial (J2000)
c_fk4 = c.fk4           # Historical equatorial
c_gal = c.galactic       # Galactic (l, b)
c_sgal = c.supergalactic # Supergalactic

# Ecliptic
from astropy.coordinates import GeocentricMeanEcliptic
c_ecl = c.transform_to(GeocentricMeanEcliptic())

# Galactocentric (3D)
from astropy.coordinates import Galactocentric
c3d = SkyCoord(ra=10*u.deg, dec=20*u.deg, distance=50*u.kpc)
c_gc = c3d.transform_to(Galactocentric())
print(f"x={c_gc.x:.1f}, y={c_gc.y:.1f}, z={c_gc.z:.1f}")
```

### Observer-Dependent Frames

```python
from astropy.coordinates import EarthLocation, AltAz, HADec
from astropy.time import Time

# Observer location
location = EarthLocation(lat=40*u.deg, lon=-120*u.deg, height=1000*u.m)
location = EarthLocation.of_site('Keck Observatory')
location = EarthLocation.of_address('Pasadena, CA')

# AltAz transform
obstime = Time('2023-06-15 23:00:00')
altaz_frame = AltAz(obstime=obstime, location=location)
c_altaz = c.transform_to(altaz_frame)
print(f"Alt={c_altaz.alt:.2f}, Az={c_altaz.az:.2f}")

# Hour Angle / Dec
hadec_frame = HADec(obstime=obstime, location=location)
c_hadec = c.transform_to(hadec_frame)
```

### 3D Coordinates and Velocities

```python
# Distance
c3d = SkyCoord(ra=10*u.deg, dec=20*u.deg, distance=50*u.kpc)
print(f"3D separation: {c3d.separation_3d(c3d_other)}")
print(f"Cartesian: x={c3d.cartesian.x}, y={c3d.cartesian.y}")

# Proper motion and radial velocity
c_vel = SkyCoord(
    ra=10*u.deg, dec=20*u.deg, distance=100*u.pc,
    pm_ra_cosdec=5*u.mas/u.yr, pm_dec=-3*u.mas/u.yr,
    radial_velocity=50*u.km/u.s
)

# Representation types
print(c3d.represent_as('cartesian'))
print(c3d.represent_as('cylindrical'))
```

### Catalog Matching

```python
from astropy.coordinates import match_coordinates_sky

# 1-to-1 nearest match
idx, sep, _ = coords1.match_to_catalog_sky(coords2)
matches = sep < 1 * u.arcsec
matched1 = cat1[matches]
matched2 = cat2[idx[matches]]

# Search around (all matches within radius)
from astropy.coordinates import search_around_sky
idx1, idx2, sep, _ = search_around_sky(coords1, coords2, 5*u.arcsec)

# Named object lookup (requires internet)
m31 = SkyCoord.from_name('M31')
print(f"M31: RA={m31.ra:.4f}, Dec={m31.dec:.4f}")
```

## Time Handling

### Time Formats

```python
from astropy.time import Time

# Supported formats
t = Time('2023-01-15 12:30:45', format='iso')      # ISO 8601
t = Time('2023-01-15T12:30:45', format='isot')      # ISO with T
t = Time(2460000.0, format='jd')                     # Julian Date
t = Time(59945.0, format='mjd')                      # Modified JD
t = Time(2023.5, format='decimalyear')               # Decimal year
t = Time(2023.5, format='jyear')                     # Julian year
t = Time('2023:046', format='yday')                  # Day of year
t = Time(1673785845.0, format='unix')                # Unix epoch
t = Time(1000000000.0, format='gps')                 # GPS seconds

# Convert output format
print(t.jd, t.mjd, t.iso, t.unix, t.decimalyear)
```

### Time Scales

```python
t = Time('2023-01-15 12:00:00', scale='utc')

# Convert between scales
t_tai = t.tai    # +37 leap seconds
t_tt = t.tt      # TAI + 32.184s
t_tdb = t.tdb    # Barycentric dynamical
t_ut1 = t.ut1    # Earth rotation

print(f"UTC-TAI offset: {(t.tai - t.utc).sec:.1f}s")
```

### Time Arithmetic

```python
from astropy.time import TimeDelta
import numpy as np

# TimeDelta operations
dt = TimeDelta(7, format='jd')
t_future = t + dt
t_future = t + 1 * u.hour + 30 * u.minute

# Time differences
duration = Time('2024-01-01') - Time('2023-01-01')
print(f"Duration: {duration.to(u.day):.1f}, {duration.to(u.year):.4f}")

# Regular time series
times = Time('2023-01-01') + np.arange(365) * u.day
hourly = Time('2023-01-15') + np.arange(24) * u.hour
```

### Observing Features

```python
from astropy.coordinates import SkyCoord, EarthLocation

location = EarthLocation.of_site('Keck Observatory')
t = Time('2023-06-15 23:00:00', location=location)

# Sidereal time
lst = t.sidereal_time('apparent')
print(f"LST: {lst}")

# Barycentric light travel time correction
target = SkyCoord(ra='23h23m08.55s', dec='+18d24m59.3s')
ltt_bary = t.light_travel_time(target, kind='barycentric')
ltt_helio = t.light_travel_time(target, kind='heliocentric')
t_bary = t.tdb + ltt_bary

# Earth rotation angle
era = t.earth_rotation_angle()
```

### High Precision and Formatting

```python
# Internal dual-float representation (sub-nanosecond)
t = Time('2023-01-15 12:30:45.123456789', scale='utc')
print(t.jd1, t.jd2)  # Integer + fractional parts

# Custom formatting
print(t.strftime('%Y-%m-%d %H:%M:%S'))
print(t.strftime('%B %d, %Y'))

# Masked times
times = Time(['2023-01-01', '2023-06-01', '2023-12-31'])
times[1] = np.ma.masked
filled = times.filled(Time('2000-01-01'))
```

## Cosmological Calculations

### Built-in Cosmologies

```python
from astropy.cosmology import Planck18, Planck15, WMAP9

# Available: Planck18, Planck15, Planck13, WMAP9, WMAP7, WMAP5
print(f"H0: {Planck18.H0}")
print(f"Om0: {Planck18.Om0}")
print(f"Ode0: {Planck18.Ode0}")
```

### Custom Cosmology

```python
from astropy.cosmology import FlatLambdaCDM, LambdaCDM, FlatwCDM

# Flat ΛCDM
cosmo = FlatLambdaCDM(H0=70, Om0=0.3, Tcmb0=2.725)

# Non-flat
cosmo = LambdaCDM(H0=70, Om0=0.3, Ode0=0.65)

# w₀CDM (dark energy equation of state)
cosmo = FlatwCDM(H0=70, Om0=0.3, w0=-1.1)

# With neutrinos
cosmo = FlatLambdaCDM(H0=67.66, Om0=0.3111, Tcmb0=2.7255,
                       Neff=3.046, m_nu=[0, 0, 0.06]*u.eV)
```

### Distance Calculations

```python
import numpy as np

z = np.linspace(0.1, 3.0, 100)

# All distances
d_L = Planck18.luminosity_distance(z)     # For flux → luminosity
d_A = Planck18.angular_diameter_distance(z) # For angle → size
d_C = Planck18.comoving_distance(z)        # Comoving
d_CT = Planck18.comoving_transverse_distance(z)
dm = Planck18.distmod(z)                   # Distance modulus (mag)

# Scale
scale = Planck18.kpc_proper_per_arcmin(z)  # Physical size per angle
```

### Time and Volume Calculations

```python
# Age and lookback time
age = Planck18.age(z)
lookback = Planck18.lookback_time(z)
print(f"Universe age now: {Planck18.age(0).to(u.Gyr):.3f}")

# Volume
vol = Planck18.comoving_volume(z)
dvol = Planck18.differential_comoving_volume(z)

# Hubble parameter evolution
H_z = Planck18.H(z)
E_z = Planck18.efunc(z)  # H(z)/H0

# Density parameters vs redshift
Om_z = Planck18.Om(z)
Ode_z = Planck18.Ode(z)
```

### Inverse Calculations

```python
from astropy.cosmology import z_at_value

# Find redshift for a given property
z_10gyr = z_at_value(Planck18.lookback_time, 10 * u.Gyr)
z_1gpc = z_at_value(Planck18.comoving_distance, 1 * u.Gpc)
z_age5 = z_at_value(Planck18.age, 5 * u.Gyr)

print(f"z at lookback 10 Gyr: {z_10gyr:.4f}")
print(f"z at comoving 1 Gpc: {z_1gpc:.4f}")
```

### Common Calculations

```python
# Absolute magnitude from apparent magnitude
z = 0.5
m_obs = 22.5  # Apparent magnitude
M_abs = m_obs - Planck18.distmod(z).value
print(f"Absolute magnitude: {M_abs:.2f}")

# Physical size from angular size
theta = 10 * u.arcsec
size = (theta * Planck18.angular_diameter_distance(z)).to(u.kpc, u.dimensionless_angles())
print(f"Physical size: {size:.2f}")

# Survey volume between redshifts
vol_shell = Planck18.comoving_volume(1.0) - Planck18.comoving_volume(0.5)
print(f"Shell volume: {vol_shell:.3e}")
```

Condensed from original: coordinates.md (274 lines) + time.md (405 lines) + cosmology.md (308 lines) = 987 lines total. Retained: all coordinate frames and transformations, all SkyCoord creation formats, catalog matching, observer-dependent frames, 3D coordinates + velocities, all time formats and scales, TimeDelta arithmetic, observing features (sidereal time, barycentric corrections), high precision, all cosmology models, all distance/time/volume calculations, inverse calculations, neutrino support. Omitted: verbose prose descriptions of each frame's meaning, duplicate Quick Start examples already in SKILL.md, time zone handling details (simple pytz pattern shown in SKILL.md).
