# 🚀 Occitanie Spots Data Scraping Infrastructure

## Overview
Complete real data scraping infrastructure for discovering outdoor spots in Occitanie region, France. 

**CRITICAL RULE**: NO MOCK DATA - Only real data from actual sources.

## 📍 Geographic Scope
- **Region**: Occitanie, France
- **Departments**: All 13 departments
  - 09 - Ariège
  - 11 - Aude  
  - 12 - Aveyron
  - 30 - Gard
  - 31 - Haute-Garonne
  - 32 - Gers
  - 34 - Hérault
  - 46 - Lot
  - 48 - Lozère
  - 65 - Hautes-Pyrénées
  - 66 - Pyrénées-Orientales
  - 81 - Tarn
  - 82 - Tarn-et-Garonne

## 🛠️ Implemented Scrapers

### ✅ Instagram Scraper
- **Status**: Fully operational
- **Method**: Puppeteer MCP browser automation
- **Features**:
  - Real post extraction from hashtags/locations
  - Anti-detection measures
  - Manual login support
  - Location and activity extraction
- **Files**:
  - `src/backend/scrapers/instagram_real_scraper.py`
  - `src/backend/scrapers/instagram_playwright_scraper.py`
  - `test_instagram_puppeteer_mcp.py`

### ✅ Facebook Scraper
- **Status**: Infrastructure ready
- **Method**: Playwright browser automation
- **Features**:
  - Public post extraction
  - Group monitoring
  - Location parsing from French text
  - Activity detection
- **Files**:
  - `src/backend/scrapers/facebook_real_scraper.py`
  - `src/backend/scrapers/facebook_playwright_scraper.py`

### ✅ Reddit Integration
- **Status**: MCP available
- **Method**: Reddit MCP server
- **Subreddits**: r/france, r/hiking, r/toulouse, r/montpellier

## 🔐 Data Pipeline

### Privacy & Security
1. **Personal Info Sanitization**:
   - Emails → `[email]`
   - Phone numbers → `[phone]`
   - Usernames → `[user]`
   - URLs → `[url]`

2. **Data Validation**:
   - GPS coordinates within Occitanie bounds
   - Department validation (must be in 13 departments)
   - Spam detection and filtering
   - Activity validation

3. **Secure Storage**:
   - SQLite database with privacy flags
   - Hashed post IDs
   - Privacy compliance tracking

### Pipeline Components
- `src/backend/data_management/data_validator.py` - Validates Occitanie data
- `src/backend/scrapers/instagram_data_handler.py` - Secure storage
- `src/backend/data_management/instagram_data_pipeline.py` - Complete pipeline

## 📊 Data Sources Overview

### Implemented (3)
- ✅ Instagram - 10,000+ posts potential
- ✅ Facebook - 5,000+ posts potential  
- ✅ Reddit - Via MCP integration

### High Priority (6)
- 🎯 Strava - 50,000+ GPS tracks
- 🎯 AllTrails - 2,000+ trail data
- 🎯 Wikiloc - 5,000+ GPS tracks
- 🎯 YouTube - 1,000+ video guides
- 🎯 TikTok - 3,000+ trending spots
- 🎯 Komoot - Route highlights

### Available (4)
- 🔄 Twitter/X - Real-time posts
- 🔄 Pinterest - Travel boards
- 🔄 Flickr - Geotagged photos
- 🔄 Forums - Deep discussions

**Total Potential**: ~86,000 data points

## 🎯 Activity Types Detected
- `baignade` - Swimming
- `randonnée` - Hiking
- `escalade` - Climbing
- `kayak` - Kayaking
- `vtt` - Mountain biking
- `camping` - Camping
- `pêche` - Fishing
- `spéléologie` - Caving
- `canyoning` - Canyoning

## 🗺️ Geocoding Integration
- **Primary**: BAN (Base Adresse Nationale) API
- **Elevation**: IGN API
- **Fallback**: OpenStreetMap Nominatim
- **Department detection**: Automatic from coordinates

## 📁 Key Files Structure
```
src/backend/
├── scrapers/
│   ├── instagram_real_scraper.py      # Instagram API approach
│   ├── instagram_playwright_scraper.py # Browser automation
│   ├── instagram_data_handler.py      # Secure storage
│   ├── facebook_real_scraper.py       # Facebook options
│   ├── facebook_playwright_scraper.py # Facebook browser
│   ├── social_media_sources.py        # All platforms catalog
│   └── geocoding_france.py            # French geocoding
├── data_management/
│   ├── data_validator.py              # Occitanie validation
│   └── instagram_data_pipeline.py     # Complete pipeline
```

## 🚀 Usage Examples

### Process Instagram Data
```python
python process_instagram_data.py
```

### Validate Scrapers
```python
python validate_scrapers.py
```

### Run Data Pipeline
```python
python -m src.backend.data_management.instagram_data_pipeline
```

## 🔒 Security Best Practices
1. **No Mock Data** - Only real data from actual sources
2. **Privacy First** - All personal info sanitized
3. **Anti-Detection** - Human-like behavior, delays
4. **Manual Login** - When automation blocked
5. **Rate Limiting** - Respect platform limits

## 📈 Results So Far
- Successfully scraped real Instagram posts
- Validated Lac de Salagou location
- Attempted Gorges d'Ehujarré (geocoding issue)
- Stored privacy-compliant data
- Exported clean JSON data

## 🎯 Next Steps
1. Fix geocoding for mountain locations
2. Implement Strava API integration
3. Create AllTrails scraper
4. Build unified data aggregator
5. Create spot quality scoring system