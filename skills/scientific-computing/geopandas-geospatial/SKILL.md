---
name: geopandas-geospatial
description: >-
  Geospatial vector analysis extending pandas. Read/write spatial formats
  (Shapefile, GeoJSON, GeoPackage, Parquet, PostGIS), CRS handling, geometric
  ops (buffer, simplify, centroid, affine), spatial analysis (joins, overlays,
  dissolve, clipping, distance), visualization (choropleth, interactive maps,
  basemaps). Use for spatial joins, overlays, CRS transforms, area/distance, maps.
license: BSD-3-Clause
---

# GeoPandas Geospatial Analysis

## Overview

GeoPandas extends pandas with spatial operations on geometric types, combining pandas DataFrames with Shapely geometries and Fiona for file I/O. It enables reading, writing, manipulating, and visualizing geospatial vector data (points, lines, polygons) with a familiar pandas-like API.

## When to Use

- Reading and writing spatial file formats (Shapefile, GeoJSON, GeoPackage, Parquet)
- Performing spatial joins between geographic datasets (points in polygons, nearest neighbors)
- Running overlay operations (intersection, union, difference, clipping)
- Computing geometric properties (area, distance, buffer, centroid)
- Creating choropleth maps and interactive web maps
- Reprojecting data between coordinate reference systems
- Aggregating spatial features by attribute (dissolve)
- For raster data analysis, use rasterio/xarray instead
- For large-scale distributed geospatial, consider Dask-GeoPandas or Apache Sedona

## Prerequisites

```bash
pip install geopandas matplotlib
# Optional:
# pip install folium       — interactive maps
# pip install mapclassify  — classification schemes for choropleth
# pip install contextily   — basemaps
# pip install pyarrow      — faster I/O (2-4x speedup)
# pip install psycopg2 geoalchemy2  — PostGIS support
```

## Quick Start

```python
import geopandas as gpd

# Read spatial data
gdf = gpd.read_file("data.geojson")
print(f"Shape: {gdf.shape}, CRS: {gdf.crs}")
print(f"Geometry types: {gdf.geometry.geom_type.unique()}")

# Reproject, compute area, save
gdf_proj = gdf.to_crs("EPSG:3857")
gdf_proj['area_m2'] = gdf_proj.geometry.area
gdf_proj.to_file("output.gpkg")

# Quick map
gdf.plot(column='population', legend=True, figsize=(10, 8))
```

## Core API

### 1. Data I/O

```python
import geopandas as gpd

# Read various formats
gdf = gpd.read_file("data.shp")           # Shapefile
gdf = gpd.read_file("data.geojson")       # GeoJSON
gdf = gpd.read_file("data.gpkg")          # GeoPackage
gdf = gpd.read_file("data.gpkg", layer="roads")  # Specific layer

# Filtered reading (load only needed data)
gdf = gpd.read_file("data.gpkg", bbox=(xmin, ymin, xmax, ymax))
gdf = gpd.read_file("data.gpkg", columns=["name", "geometry"])
gdf = gpd.read_file("data.gpkg", where="population > 10000")

# Arrow acceleration (2-4x faster)
gdf = gpd.read_file("data.gpkg", use_arrow=True)

# Parquet/Feather (columnar, fast, preserves CRS)
gdf = gpd.read_parquet("data.parquet")
gdf.to_parquet("output.parquet")

# PostGIS database
from sqlalchemy import create_engine
engine = create_engine("postgresql://user:pass@host/db")
gdf = gpd.read_postgis("SELECT * FROM parcels", con=engine, geom_col='geom')
gdf.to_postgis("output_table", con=engine)

# Write
gdf.to_file("output.gpkg")             # GeoPackage (recommended)
gdf.to_file("output.shp")              # Shapefile
gdf.to_file("output.geojson", driver="GeoJSON")
```

### 2. CRS Management

```python
# Check current CRS
print(gdf.crs)                  # e.g., EPSG:4326
print(gdf.crs.is_geographic)    # True for lat/lon
print(gdf.crs.is_projected)     # True for meters

# Reproject (transforms coordinates)
gdf_proj = gdf.to_crs("EPSG:3857")       # Web Mercator
gdf_proj = gdf.to_crs(epsg=32633)        # UTM zone 33N

# Set CRS (only when metadata missing, does NOT transform coordinates)
gdf = gdf.set_crs("EPSG:4326")

# Estimate appropriate UTM zone
utm_crs = gdf.estimate_utm_crs()
gdf_utm = gdf.to_crs(utm_crs)
```

**Common EPSG codes**:

| Code | Name | Use |
|------|------|-----|
| 4326 | WGS 84 | GPS coordinates, web data |
| 3857 | Web Mercator | Web mapping (Google/OSM tiles) |
| 326xx | UTM zones (N) | Area/distance calculations |
| 5070 | Albers Equal Area (US) | Area-preserving US maps |

### 3. Geometric Operations

```python
# Buffer (expand/erode geometry by distance)
buffered = gdf.geometry.buffer(100)      # 100 units (meters if projected)
eroded = gdf.geometry.buffer(-50)        # Negative = erosion

# Simplify (reduce complexity)
simplified = gdf.geometry.simplify(tolerance=10, preserve_topology=True)

# Centroid, convex hull, envelope
centroids = gdf.geometry.centroid
hulls = gdf.geometry.convex_hull
bounds = gdf.geometry.envelope

# Union all geometries
unified = gdf.geometry.union_all()

# Affine transformations
rotated = gdf.geometry.rotate(angle=45, origin='center')
scaled = gdf.geometry.scale(xfact=2.0, yfact=2.0)
translated = gdf.geometry.translate(xoff=100, yoff=50)

# Geometric properties
areas = gdf.geometry.area           # Use projected CRS for accuracy
lengths = gdf.geometry.length       # Perimeter for polygons
is_valid = gdf.geometry.is_valid    # Validate geometry
total = gdf.geometry.total_bounds   # [minx, miny, maxx, maxy]
```

### 4. Spatial Analysis

```python
# Spatial join (combine datasets by spatial relationship)
joined = gpd.sjoin(points_gdf, polygons_gdf, predicate='intersects')
joined = gpd.sjoin(gdf1, gdf2, predicate='within')
joined = gpd.sjoin(gdf1, gdf2, predicate='contains', how='left')

# Nearest neighbor join
nearest = gpd.sjoin_nearest(gdf1, gdf2, max_distance=1000, distance_col='dist')

# Overlay operations (set-theoretic)
intersection = gpd.overlay(gdf1, gdf2, how='intersection')
union = gpd.overlay(gdf1, gdf2, how='union')
difference = gpd.overlay(gdf1, gdf2, how='difference')
sym_diff = gpd.overlay(gdf1, gdf2, how='symmetric_difference')

# Dissolve (aggregate by attribute)
dissolved = gdf.dissolve(by='region', aggfunc='sum')
dissolved = gdf.dissolve(by='region', aggfunc={'population': 'sum', 'area': 'mean'})

# Clip to boundary
clipped = gpd.clip(gdf, boundary_gdf)

# Distance calculations (use projected CRS)
distances = gdf.geometry.distance(single_point)

# Spatial predicates
within_mask = gdf1.geometry.within(gdf2.geometry)
intersects_mask = gdf1.geometry.intersects(gdf2.geometry)
```

### 5. Visualization

```python
import matplotlib.pyplot as plt

# Basic plot
gdf.plot(figsize=(10, 8))

# Choropleth map
gdf.plot(column='population', cmap='YlOrRd', legend=True, figsize=(12, 8))

# Classification schemes (requires mapclassify)
gdf.plot(column='population', scheme='quantiles', k=5, legend=True)
gdf.plot(column='population', scheme='fisher_jenks', k=5, legend=True)

# Multi-layer map
fig, ax = plt.subplots(figsize=(12, 10))
polygons_gdf.plot(ax=ax, color='lightblue', edgecolor='black')
points_gdf.plot(ax=ax, color='red', markersize=10)
roads_gdf.plot(ax=ax, color='gray', linewidth=0.5)
ax.set_title('Multi-layer Map')
ax.set_axis_off()

# Interactive map (requires folium)
m = gdf.explore(column='population', cmap='YlOrRd', legend=True,
                tooltip=['name', 'population'])
m.save('map.html')

# Multi-layer interactive
m = gdf1.explore(color='blue', name='Layer 1')
gdf2.explore(m=m, color='red', name='Layer 2')
import folium
folium.LayerControl().add_to(m)

# Basemap (requires contextily)
import contextily as ctx
gdf_wm = gdf.to_crs(epsg=3857)
ax = gdf_wm.plot(alpha=0.5, figsize=(10, 10))
ctx.add_basemap(ax)
```

## Key Concepts

### Data Structures

- **GeoSeries**: Pandas Series of Shapely geometries with spatial methods (area, distance, buffer, etc.)
- **GeoDataFrame**: Pandas DataFrame with one or more geometry columns. One column is the "active geometry" used by spatial methods

```python
from shapely.geometry import Point

# Create from coordinates
gdf = gpd.GeoDataFrame(
    {'name': ['A', 'B'], 'value': [10, 20]},
    geometry=[Point(0, 0), Point(1, 1)],
    crs="EPSG:4326"
)

# Multiple geometry columns
gdf['centroid'] = gdf.geometry.centroid
gdf = gdf.set_geometry('centroid')  # Switch active geometry
```

### CRS Rules for Spatial Operations

- **Always check CRS** before any spatial operation: `print(gdf.crs)`
- **Match CRS** before spatial joins, overlays, or distance calculations
- **Use projected CRS** (meters) for area/distance — geographic CRS (degrees) gives wrong results
- **set_crs()** only adds metadata; **to_crs()** transforms coordinates

### Spatial Indexing

GeoPandas automatically creates spatial indexes (R-tree) for sjoin, overlay, and other spatial operations. For manual queries:

```python
sindex = gdf.sindex
possible_idx = list(sindex.intersection((xmin, ymin, xmax, ymax)))
```

## Common Workflows

### Workflow 1: Load → Transform → Analyze → Export

```python
import geopandas as gpd

# Load
gdf = gpd.read_file("parcels.shp")
print(f"CRS: {gdf.crs}, Rows: {len(gdf)}")

# Transform to projected CRS for measurements
gdf = gdf.to_crs(gdf.estimate_utm_crs())

# Analyze
gdf['area_ha'] = gdf.geometry.area / 10000  # hectares
gdf['perimeter_m'] = gdf.geometry.length
print(f"Total area: {gdf['area_ha'].sum():.1f} ha")

# Export
gdf.to_file("parcels_analyzed.gpkg")
```

### Workflow 2: Spatial Join and Aggregate

```python
# Count points per polygon
points_in_poly = gpd.sjoin(points_gdf, polygons_gdf, predicate='within')
counts = points_in_poly.groupby('index_right').agg(
    point_count=('geometry', 'size'),
    total_value=('value', 'sum')
)
result = polygons_gdf.merge(counts, left_index=True, right_index=True, how='left')
result['point_count'] = result['point_count'].fillna(0)
print(f"Polygons with points: {(result['point_count'] > 0).sum()}/{len(result)}")
```

### Workflow 3: Multi-Source Integration

```python
# Read from different sources, ensure matching CRS
roads = gpd.read_file("roads.shp")
buildings = gpd.read_file("buildings.geojson")
parcels = gpd.read_postgis("SELECT * FROM parcels", con=engine, geom_col='geom')

target_crs = roads.crs
buildings = buildings.to_crs(target_crs)
parcels = parcels.to_crs(target_crs)

# Find buildings within 50m of roads
buildings_near_roads = gpd.sjoin_nearest(
    buildings, roads, max_distance=50, distance_col='road_dist'
)
print(f"Buildings near roads: {len(buildings_near_roads)}/{len(buildings)}")
```

## Key Parameters

| Parameter | Function | Default | Effect |
|-----------|----------|---------|--------|
| `predicate` | sjoin | `'intersects'` | Spatial relationship: intersects, within, contains, touches, crosses |
| `how` | sjoin, overlay | `'inner'` | Join type: inner, left, right |
| `max_distance` | sjoin_nearest | None | Search radius limit (improves performance) |
| `k` | sjoin_nearest | 1 | Number of nearest neighbors to find |
| `tolerance` | simplify | Required | Douglas-Peucker tolerance (in CRS units) |
| `preserve_topology` | simplify | True | Prevents self-intersections |
| `resolution` | buffer | 16 | Number of segments for buffer curves |
| `aggfunc` | dissolve | 'first' | Aggregation function for non-geometry columns |
| `use_arrow` | read_file | False | Enable Arrow acceleration (2-4x faster) |
| `scheme` | plot | None | Classification: quantiles, equal_interval, fisher_jenks |
| `k` | plot (with scheme) | 5 | Number of classification bins |

## Best Practices

1. **Always check CRS** before spatial operations — mismatched CRS gives wrong or empty results
2. **Use projected CRS** for area and distance calculations — geographic CRS (degrees) is meaningless for measurements
3. **Match CRS before joins** — `gdf2 = gdf2.to_crs(gdf1.crs)` before `gpd.sjoin(gdf1, gdf2)`
4. **Validate geometries** with `.is_valid` before complex operations — invalid geometries cause silent errors
5. **Use GeoPackage** over Shapefile — no 10-char column name limit, supports multiple layers, better performance
6. **Filter during read** — use `bbox`, `columns`, `where` to load only needed data for large files
7. **Set max_distance in sjoin_nearest** — unbounded nearest-neighbor search is slow on large datasets
8. **Use `.copy()` when modifying geometry** — avoid unintended side effects on original GeoDataFrame

## Common Recipes

### Recipe: Count Points in Polygons

When to use: Aggregate point observations (sample sites, observations) by region (county, watershed).

```python
import geopandas as gpd

regions = gpd.read_file("regions.geojson")
points = gpd.read_file("observations.geojson").to_crs(regions.crs)

joined = gpd.sjoin(points, regions, how="inner", predicate="within")
counts = joined.groupby("index_right").size().rename("point_count")
regions_with_counts = regions.join(counts).fillna(0)
regions_with_counts["point_count"] = regions_with_counts["point_count"].astype(int)
print(regions_with_counts[["name", "point_count"]].sort_values("point_count", ascending=False).head())
```

### Recipe: Buffer Around Points and Dissolve Overlaps

When to use: Create service areas or catchment zones from point locations.

```python
import geopandas as gpd

facilities = gpd.read_file("facilities.geojson")
utm_crs = facilities.estimate_utm_crs()   # Project to meters
facilities_m = facilities.to_crs(utm_crs)

# 1 km buffer
buffers = facilities_m.copy()
buffers["geometry"] = facilities_m.geometry.buffer(1000)

# Dissolve overlapping buffers into single polygon
service_area = buffers.dissolve()
service_area_wgs84 = service_area.to_crs("EPSG:4326")
service_area_wgs84.to_file("service_area.geojson", driver="GeoJSON")
print(f"Service area: {service_area_wgs84.geometry.area.sum():.0f} sq degrees")
```

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| Empty spatial join result | CRS mismatch between GeoDataFrames | Ensure matching CRS: `gdf2 = gdf2.to_crs(gdf1.crs)` |
| Wrong area/distance values | Using geographic CRS (degrees) | Reproject to projected CRS: `gdf.to_crs(gdf.estimate_utm_crs())` |
| `DriverError` on read | Missing driver or corrupt file | Check file exists; try `driver="GeoJSON"` explicitly |
| Geometry column lost after merge | Called `df.merge(gdf)` instead of `gdf.merge(df)` | Always call merge ON the GeoDataFrame |
| `TopologicalError` on overlay | Invalid geometries | Fix with `gdf.geometry = gdf.geometry.buffer(0)` |
| Slow sjoin_nearest | No distance limit on large dataset | Set `max_distance` parameter |
| Folium map blank | Geometries not in EPSG:4326 | Reproject to WGS84: `gdf.to_crs(epsg=4326).explore()` |
| Shapefile column names truncated | Shapefile 10-char limit | Use GeoPackage instead: `gdf.to_file("out.gpkg")` |

## References

- GeoPandas documentation: https://geopandas.org/
- GeoPandas GitHub: https://github.com/geopandas/geopandas
- Shapely documentation: https://shapely.readthedocs.io/
- EPSG registry: https://epsg.io/

## Related Skills

- **matplotlib-scientific-plotting** — advanced map styling and figure export
- **polars-dataframes** — high-performance tabular analysis before/after spatial operations
- **folium** — advanced interactive web mapping beyond geopandas.explore()
