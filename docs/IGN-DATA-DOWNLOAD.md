# IGN Data Download Guide

## Overview

The IGN Dataset Downloader allows you to programmatically download various geographic datasets from IGN (Institut Géographique National) for use in the SPOTS project.

## Available Datasets

### Administrative Boundaries
- **Communes** (`ADMINEXPRESS-COG-CARTO.LATEST:commune`)
- **Départements** (`ADMINEXPRESS-COG-CARTO.LATEST:departement`)
- **Régions** (`ADMINEXPRESS-COG-CARTO.LATEST:region`)

### Environmental Data
- **Protected Areas** (`PROTECTEDAREAS.ALL`)
- **Natura 2000 Sites** (`PROTECTEDAREAS.NATURA2000`)
- **Forest Inventory** (`LANDCOVER.FORESTINVENTORY.V2`)
- **Geology** (`GEOLOGIE.CARTEGEOLOGIQUE`)

### Infrastructure
- **Roads** (`BDTOPO_V3:troncon_de_route`)
- **Hydrography** (`HYDROGRAPHIE.THEME`)

### Elevation
- **RGE ALTI** (`RGEALTI`) - Digital Elevation Model
- **Slopes** (`ELEVATION.SLOPES`)

## Quick Start

### 1. Import the downloader

```python
from backend.scrapers.ign_downloader import download_ign_dataset, IGNDatasetDownloader
```

### 2. Download data with bbox

```python
# Download Toulouse communes
path = download_ign_dataset(
    dataset_id="ADMINEXPRESS-COG-CARTO.LATEST:commune",
    bbox=[1.2, 43.5, 1.5, 43.7],  # min_lon, min_lat, max_lon, max_lat
    format="geojson"  # or "shp", "gml"
)
```

### 3. Download entire Occitanie region

```python
downloader = IGNDatasetDownloader()
path = downloader.download_occitanie_boundaries(level="departement")
```

## Examples

### Example 1: Download communes around Toulouse

```python
communes = download_ign_dataset(
    dataset_id="ADMINEXPRESS-COG-CARTO.LATEST:commune",
    bbox=[1.2, 43.5, 1.5, 43.7],
    format="geojson",
    output_file="toulouse_communes.geojson"
)
```

### Example 2: Download protected areas in Pyrénées

```python
protected = download_ign_dataset(
    dataset_id="PROTECTEDAREAS.ALL",
    bbox=[0.0, 42.5, 3.0, 43.5],  # Pyrénées
    format="geojson"
)
```

### Example 3: Download forest data

```python
forests = download_ign_dataset(
    dataset_id="LANDCOVER.FORESTINVENTORY.V2",
    bbox=[2.0, 43.3, 2.5, 43.6],  # Montagne Noire
    format="shp"  # Shapefile format
)
```

### Example 4: Batch download for Occitanie

```python
downloader = IGNDatasetDownloader(download_dir="data/occitanie")

datasets = [
    ("ADMINEXPRESS-COG-CARTO.LATEST:region", "regions"),
    ("ADMINEXPRESS-COG-CARTO.LATEST:departement", "departments"),
    ("PROTECTEDAREAS.ALL", "protected_areas"),
    ("HYDROGRAPHIE.THEME", "water"),
]

occitanie_bbox = [-0.5, 42.5, 4.5, 45.0]

for dataset_id, name in datasets:
    path = downloader.download_dataset(
        dataset_id=dataset_id,
        bbox=occitanie_bbox,
        format="geojson",
        output_file=f"occitanie_{name}.geojson"
    )
    print(f"Downloaded {name} to {path}")
```

## Command Line Usage

### List available datasets
```bash
python src/backend/scrapers/ign_downloader.py --list
```

### Download specific dataset
```bash
python src/backend/scrapers/ign_downloader.py \
    --dataset ADMINEXPRESS-COG-CARTO.LATEST:commune \
    --bbox 1.2 43.5 1.5 43.7 \
    --format geojson \
    --output toulouse_communes.geojson
```

### Run examples
```bash
cd examples
python download_ign_data.py --example 1  # Toulouse communes
python download_ign_data.py --example 2  # Occitanie departments
python download_ign_data.py --all        # Download all Occitanie data
```

## Integration with SPOTS

The downloaded data can be used to:

1. **Enrich spot data** with administrative information
   ```python
   # Find which commune each spot belongs to
   communes = load_geojson("toulouse_communes.geojson")
   spot_commune = find_containing_polygon(spot_coords, communes)
   ```

2. **Calculate environmental metrics**
   ```python
   # Find nearby protected areas
   protected_areas = load_geojson("protected_areas.geojson")
   nearby_protected = find_within_distance(spot_coords, protected_areas, 1000)  # 1km
   ```

3. **Improve routing and accessibility**
   ```python
   # Find nearest road
   roads = load_geojson("roads.geojson")
   nearest_road = find_nearest_feature(spot_coords, roads)
   ```

4. **Create thematic maps**
   ```python
   # Color spots by department
   departments = load_geojson("departments.geojson")
   spot_department = find_containing_polygon(spot_coords, departments)
   ```

## Output Formats

- **GeoJSON** (`.geojson`) - Recommended for web applications
- **Shapefile** (`.shp`) - Traditional GIS format (creates a folder with multiple files)
- **GML** (`.gml`) - Geography Markup Language

## Storage

Downloaded files are saved to:
- Default: `data/ign_downloads/`
- Custom: Specify with `download_dir` parameter

## Limitations

- Large datasets (like detailed communes for all of France) may take time
- Some datasets require specific API keys (currently using "essentiels" public key)
- Bbox is required for most downloads to limit data size

## Error Handling

```python
try:
    path = download_ign_dataset(dataset_id, bbox=bbox)
except ValueError as e:
    print(f"Invalid parameters: {e}")
except requests.RequestException as e:
    print(f"Download failed: {e}")
```

## Next Steps

1. Download administrative boundaries for your area of interest
2. Integrate with PostGIS for spatial queries
3. Use with Leaflet for visualization
4. Combine with spot data for enriched analysis