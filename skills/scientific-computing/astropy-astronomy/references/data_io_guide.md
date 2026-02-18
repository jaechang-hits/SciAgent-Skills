# Astropy Data I/O Guide — FITS Files & Tables

Detailed reference for FITS file operations and Table manipulation.

## FITS File Operations

### Opening and Navigating

```python
from astropy.io import fits

# Context manager (recommended)
with fits.open('data.fits') as hdul:
    hdul.info()              # Print HDU list
    primary = hdul[0]        # By index
    sci = hdul['SCI']        # By name
    sci_v2 = hdul['SCI', 2]  # By name + version

# Open modes
hdul = fits.open('data.fits', mode='readonly')   # Default
hdul = fits.open('data.fits', mode='update')      # Modify in place
hdul = fits.open('data.fits', mode='append')       # Add HDUs

# Memory mapping for large files
hdul = fits.open('huge.fits', memmap=True)
cutout = hdul[0].section[100:200, 300:400]  # Read only a region

# Remote files
hdul = fits.open('s3://bucket/data.fits', fsspec_kwargs={'anon': True})
```

### Header Operations

```python
header = hdul[0].header

# Read
exptime = header['EXPTIME']
comment = header.comments['EXPTIME']

# Modify
header['EXPTIME'] = 600.0
header['EXPTIME'] = (600.0, 'Integration time in seconds')

# Add/delete
header['NEWKEY'] = ('value', 'description')
header.add_history('Processed on 2023-01-15')
header.add_comment('Calibrated data')
del header['BADKEY']

# Iterate
for key in header:
    print(f"{key} = {header[key]}")
```

### Image Data

```python
import numpy as np

# Access as NumPy array
data = hdul[0].data
print(f"Shape: {data.shape}, Dtype: {data.dtype}")

# Operations
data_float = data.astype(np.float64)
normalized = (data_float - np.median(data_float)) / np.std(data_float)

# Create new image HDU
new_hdu = fits.PrimaryHDU(data=normalized)
new_hdu.header['OBJECT'] = 'M31'
new_hdu.writeto('processed.fits', overwrite=True)
```

### Binary Table HDU

```python
# Create table with typed columns
# Format codes: A=string, L=bool, B=uint8, I=int16, J=int32, K=int64, E=float32, D=float64
cols = [
    fits.Column(name='ID', format='J', array=np.arange(100)),
    fits.Column(name='RA', format='D', array=np.random.uniform(0, 360, 100)),
    fits.Column(name='DEC', format='D', array=np.random.uniform(-90, 90, 100)),
    fits.Column(name='FLUX', format='E', array=np.random.random(100)),
    fits.Column(name='NAME', format='20A', array=['star_%03d' % i for i in range(100)]),
    fits.Column(name='FLAG', format='L', array=np.random.choice([True, False], 100))
]
hdu = fits.BinTableHDU.from_columns(cols, name='CATALOG')
```

### Multi-Extension Files

```python
# Create multi-extension FITS
primary = fits.PrimaryHDU()
primary.header['TELESCOP'] = 'HST'

sci = fits.ImageHDU(data=science_data, name='SCI')
err = fits.ImageHDU(data=error_data, name='ERR')
dq = fits.ImageHDU(data=quality_data, name='DQ')

hdul = fits.HDUList([primary, sci, err, dq])
hdul.writeto('multi_ext.fits', overwrite=True)
```

### Convenience Functions

```python
# Quick read (no context manager needed)
data = fits.getdata('image.fits')
data = fits.getdata('image.fits', ext=1)
header = fits.getheader('image.fits')
value = fits.getval('image.fits', 'EXPTIME')

# Quick write
fits.writeto('output.fits', data, header, overwrite=True)
fits.append('output.fits', new_data, new_header)

# Quick modify
fits.setval('image.fits', 'OBSERVER', value='Smith')

# Compare files
fits.printdiff('file1.fits', 'file2.fits')
diff = fits.FITSDiff('file1.fits', 'file2.fits')
print(diff.report())
```

### Error Handling

```python
# Non-standard FITS files
hdul = fits.open('bad.fits', ignore_missing_end=True)
hdul.verify('fix')  # Auto-fix common issues

# FITS ↔ Table conversion
from astropy.table import Table
t = Table.read('data.fits')
t.write('output.fits', format='fits', overwrite=True)
```

## Table Operations

### Creating Tables

```python
from astropy.table import Table, QTable
import astropy.units as u
import numpy as np

# From column arrays
t = Table({'ra': [10.0, 20.0], 'dec': [41.0, 42.0], 'mag': [15.2, 16.1]})

# From rows
t = Table(rows=[(10.0, 41.0, 15.2), (20.0, 42.0, 16.1)],
          names=['ra', 'dec', 'mag'])

# From NumPy array
arr = np.array([(10.0, 41.0), (20.0, 42.0)], dtype=[('ra', 'f8'), ('dec', 'f8')])
t = Table(arr)

# From pandas
t = Table.from_pandas(df)

# QTable with units
qt = QTable({'distance': [10, 20, 30] * u.kpc,
             'flux': [1e-15, 2e-15, 3e-15] * u.erg / u.s / u.cm**2})
```

### File I/O

```python
# Read (format auto-detected or specified)
t = Table.read('catalog.fits')
t = Table.read('data.csv', format='csv')
t = Table.read('catalog.vot', format='votable')
t = Table.read('data.hdf5', path='table1')
t = Table.read('data.parquet')

# Write
t.write('output.fits', format='fits', overwrite=True)
t.write('output.ecsv', format='ascii.ecsv')  # Preserves units + metadata
t.write('output.hdf5', path='results', serialize_meta=True)
t.write('output.tex', format='ascii.latex')
```

### Sorting and Filtering

```python
# Sort
t.sort('mag')                            # Ascending
t.sort('mag', reverse=True)              # Descending
t.sort(['field', 'mag'])                 # Multiple columns

# Boolean filtering
bright = t[t['mag'] < 15.5]
selected = t[(t['mag'] < 16) & (t['dec'] > 40)]

# Unique rows
unique_t = t[np.unique(t['field'], return_index=True)[1]]
```

### Joins and Grouping

```python
from astropy.table import join, vstack, hstack, unique

# Joins
merged = join(t1, t2, keys='id', join_type='inner')
merged = join(t1, t2, keys=['ra', 'dec'], join_type='left')

# Stack
combined = vstack([t1, t2, t3])
wide = hstack([t_coords, t_photometry])

# Group and aggregate
grouped = t.group_by('field')
for key, group in zip(grouped.groups.keys, grouped.groups):
    print(f"Field {key['field']}: {len(group)} sources")

stats = grouped.groups.aggregate(np.mean)

# Unique rows
unique_rows = unique(t, keys='id')
```

### Masked Data

```python
from astropy.table import MaskedColumn

# Create masked column
mc = MaskedColumn(data=[1.0, 2.0, 3.0], mask=[False, True, False], name='flux')
t.add_column(mc)

# Check and fill masks
print(t['flux'].mask)
filled = t['flux'].filled(0)  # Replace masked with 0
```

### Indexing and Performance

```python
# Fast lookup index
t.add_index('id')
row = t.loc[12345]
subset = t.loc[100:200]

# Performance: build from lists (not row-by-row)
# SLOW
t = Table(names=['a', 'b'])
for i in range(1000):
    t.add_row([i, i**2])

# FAST
rows = [(i, i**2) for i in range(1000)]
t = Table(rows=rows, names=['a', 'b'])

# Memory-mapped FITS tables
t = Table.read('huge_catalog.fits', memmap=True)

# View vs copy
t_view = t['ra', 'dec']           # View (shares data)
t_copy = t['ra', 'dec'].copy()    # Independent copy
```

### Table Metadata and Display

```python
# Metadata
t.meta['TELESCOPE'] = 'HST'
t['ra'].description = 'Right Ascension (J2000)'

# Display
print(t)
t.show_in_browser(jsviewer=True)  # Interactive browser
t['flux'].format = '%.3e'

# Convert
arr = np.array(t)
df = t.to_pandas()
```

Condensed from original: fits.md (397 lines) + tables.md (489 lines) = 886 lines total. Retained: all FITS operations (open modes, headers, images, binary tables, multi-extension, convenience functions, error handling, format codes), all Table operations (creation, I/O formats, sorting, filtering, joins, grouping, masked data, indexing, performance, metadata, display, conversion). Omitted: verbose prose introductions, duplicate examples already in SKILL.md Core API sections, FITS-specific remote access details beyond S3 example.
