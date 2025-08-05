# 🇫🇷 French Geocoding Integration

## Overview

We've replaced the India-focused Ola Maps with **free French government services** that are perfectly suited for the Occitanie region:

- **BAN (Base Adresse Nationale)** - French national address database for geocoding
- **IGN (Institut National de l'Information Géographique et Forestière)** - French geographic institute for elevation data
- **Open-Elevation** - Fallback service for elevation when IGN is unavailable

## ✅ Advantages over Ola Maps

1. **No API Key Required** - Completely free government services
2. **French-Specific** - Optimized for French addresses and locations
3. **Official Data** - Government-maintained, high-quality data
4. **Occitanie Focus** - Built-in validation for Occitanie departments
5. **Better Accuracy** - Native understanding of French address formats

## 🎯 What Was Implemented

### 1. **French Geocoding Service** (`geocoding_france.py`)
- Forward geocoding using BAN API
- Reverse geocoding for coordinates → addresses
- IGN elevation service integration
- Occitanie region validation
- Department detection and validation

### 2. **Enhanced API Endpoints** (`mapping_france.py`)
- `/api/mapping/geocode` - French address geocoding
- `/api/mapping/reverse-geocode` - Get French addresses from coordinates
- `/api/mapping/elevation` - IGN elevation data (with Open-Elevation fallback)
- `/api/mapping/search-places` - Search French places with Occitanie filtering
- `/api/mapping/departments` - List all Occitanie departments
- `/api/mapping/validate-location` - Check if coordinates are in Occitanie

### 3. **Database Enhancements**
- Added `department` column for French department codes
- Existing columns: `elevation`, `address`, `geocoding_confidence`
- Ready for enrichment with French data

### 4. **French Reddit Scraper** (`reddit_scraper_french.py`)
- Occitanie-specific location detection
- French place name patterns
- Automatic geocoding with Occitanie context
- Department validation

### 5. **Enrichment Script** (`enrich_spots_french.py`)
- Batch processing for all 3,226 spots
- IGN elevation lookup
- French address resolution
- Department assignment

## 📊 API Usage Examples

### Geocode a French Address
```bash
curl -X POST http://localhost:8000/api/mapping/geocode \
  -H "Content-Type: application/json" \
  -d '{"address": "Place du Capitole, Toulouse"}'
```

Response:
```json
{
  "latitude": 43.6044,
  "longitude": 1.4431,
  "formatted_address": "Place du Capitole 31000 Toulouse",
  "confidence": 0.98,
  "city": "Toulouse",
  "postcode": "31000",
  "department": "31"
}
```

### Get Elevation
```bash
curl -X POST http://localhost:8000/api/mapping/elevation \
  -H "Content-Type: application/json" \
  -d '{"latitude": 42.9369, "longitude": 0.1412}'
```

Response:
```json
{
  "latitude": 42.9369,
  "longitude": 0.1412,
  "elevation": 2877.0,
  "source": "IGN"
}
```

### Validate Occitanie Location
```bash
curl -X GET "http://localhost:8000/api/mapping/validate-location?lat=43.6047&lon=1.4442"
```

Response:
```json
{
  "coordinates": {"latitude": 43.6047, "longitude": 1.4442},
  "in_occitanie": true,
  "department_code": "31",
  "department_name": "Haute-Garonne",
  "address": "5 Rue Lafayette 31000 Toulouse"
}
```

## 🗺️ Occitanie Departments

The system recognizes all 13 departments of Occitanie:

| Code | Department | Major City |
|------|------------|------------|
| 09 | Ariège | Foix |
| 11 | Aude | Carcassonne |
| 12 | Aveyron | Rodez |
| 30 | Gard | Nîmes |
| 31 | Haute-Garonne | Toulouse |
| 32 | Gers | Auch |
| 34 | Hérault | Montpellier |
| 46 | Lot | Cahors |
| 48 | Lozère | Mende |
| 65 | Hautes-Pyrénées | Tarbes |
| 66 | Pyrénées-Orientales | Perpignan |
| 81 | Tarn | Albi |
| 82 | Tarn-et-Garonne | Montauban |

## 🚀 Running the Enrichment

```bash
# Check current statistics
python scripts/enrich_spots_french.py --stats

# Test with first 10 spots
python scripts/enrich_spots_french.py --test

# Run full enrichment (all 3,226 spots)
python scripts/enrich_spots_french.py
```

## 📈 Performance

- **BAN API**: 50 requests/second limit
- **IGN Elevation**: No specified limit, we use 2 req/sec
- **No API Key**: Zero cost, government service
- **Caching**: Built-in to reduce duplicate requests

## 🔧 Technical Details

### BAN API Endpoints
- **New (IGN)**: `https://data.geopf.fr/geocodage/search`
- **Legacy**: `https://api-adresse.data.gouv.fr/search` (until 2026)
- Both currently work, code tries new first, falls back to legacy

### Data Quality
- **Geocoding Confidence**: 0.0 to 1.0 score
- **Address Format**: Standard French postal format
- **Elevation Accuracy**: ~1m precision from IGN
- **Department Detection**: Based on official boundaries

## 🎉 Benefits

1. **Free Forever** - Government service, no pricing tiers
2. **High Quality** - Official French geographic data
3. **Fast** - Low latency to French servers
4. **Reliable** - Government infrastructure
5. **Privacy** - No API keys to leak or manage
6. **Accurate** - Native French address understanding

## 📝 Next Steps

1. **Run Enrichment**: Add French addresses and elevation to all spots
2. **Monitor Coverage**: Check which spots get enriched
3. **Validate Departments**: Ensure all spots are correctly assigned
4. **Frontend Integration**: Update UI to show French address data

---

**Migration Complete!** The spots project now uses proper French geocoding services. 🇫🇷