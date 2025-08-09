# Urbex Module for SPOTS Project

## Overview
The Urbex (Urban Exploration) module adds support for discovering and cataloging abandoned places in the Occitanie region. It focuses on safety, responsible exploration, and community-driven documentation.

## Features

### Core Functionality
- **Scraping**: Automated discovery from Instagram and Reddit
- **Validation**: Safety checks and data quality assurance  
- **Database**: Dedicated storage with visit tracking
- **API**: RESTful endpoints for frontend integration
- **Map Layer**: Visual display with safety indicators

### Safety Features
- **Danger Levels**: 4-tier risk assessment (Low/Medium/High/Extreme)
- **Access Difficulty**: 4-tier difficulty rating
- **Hazard Tracking**: Specific risks (asbestos, structural, etc.)
- **Beginner Filter**: Shows only safe spots for newcomers

## Structure

```
urbex/
├── __init__.py           # Module exports
├── data_models.py        # UrbexSpot data model
├── scraper.py           # Social media scraping
├── validator.py         # Safety and quality validation
├── database.py          # SQLite database operations
└── README.md           # This file
```

## Data Model

### UrbexSpot
Primary data structure with fields:
- **Location**: name, coordinates, address, department
- **Category**: abandoned_building, industrial, castle, etc.
- **Safety**: danger_level, access_difficulty, hazards
- **Access**: notes, best_time, security_presence
- **Photography**: best spots, lighting times
- **Legal**: status, owner, permission requirements
- **Community**: popularity, visit count, confirmations

### Categories
- `ABANDONED_BUILDING` - General abandoned structures
- `INDUSTRIAL` - Factories, warehouses
- `CASTLE` - Historical fortifications
- `CHURCH` - Religious buildings
- `HOSPITAL` - Medical facilities
- `SCHOOL` - Educational buildings
- `MILITARY` - Military installations
- `TUNNEL` - Underground passages
- `MINE` - Mining sites
- `QUARRY` - Stone quarries
- `THEME_PARK` - Abandoned attractions
- `HOTEL` - Hospitality buildings
- `RAILWAY` - Train infrastructure
- `BUNKER` - Defensive structures

## API Endpoints

### GET /api/urbex/spots
Get urbex spots with filters:
- `department`: Filter by department code
- `category`: Filter by category
- `max_danger`: Maximum danger level (1-4)
- `beginner_friendly`: Show only safe spots

### GET /api/urbex/spots/{id}
Get specific spot details

### GET /api/urbex/spots/nearby
Find spots near coordinates:
- `lat`: Latitude
- `lng`: Longitude  
- `radius_km`: Search radius

### GET /api/urbex/search
Search spots by text:
- `q`: Search query

### POST /api/urbex/spots/{id}/visit
Record a visit:
- `condition_report`: Current state
- `danger_update`: Updated danger level

### POST /api/urbex/scrape
Trigger scraping:
- `source`: instagram/reddit/all
- `limit`: Max results per source

## Usage Examples

### Python - Add Urbex Spot
```python
from src.backend.urbex import UrbexSpot, UrbexCategory, DangerLevel
from src.backend.urbex.database import UrbexDatabase

# Create spot
spot = UrbexSpot(
    name="Château de Example",
    category=UrbexCategory.CASTLE,
    latitude=43.6047,
    longitude=1.4442,
    department="31",
    danger_level=DangerLevel.MEDIUM,
    year_abandoned=1970,
    hazards=["falling debris", "unstable floors"]
)

# Add to database
db = UrbexDatabase()
spot_id = db.add_spot(spot)
```

### JavaScript - Display on Map
```javascript
import { UrbexLayer } from '/js/modules/urbex-layer.js';

// Initialize layer
const urbexLayer = new UrbexLayer(map);

// Load and display spots
await urbexLayer.loadUrbexSpots();

// Filter for beginners
urbexLayer.setFilter('maxDanger', 2);
```

### API - Search Spots
```bash
# Get beginner-friendly spots
curl "http://localhost:8000/api/urbex/spots?beginner_friendly=true"

# Search by name
curl "http://localhost:8000/api/urbex/search?q=château"

# Get nearby spots
curl "http://localhost:8000/api/urbex/spots/nearby?lat=43.6&lng=1.4&radius_km=50"
```

## Safety Guidelines

### For Developers
1. **Never hide safety information** - Always display danger levels
2. **Validate all spots** - Use the validator before adding to DB
3. **Respect private property** - Flag permission requirements
4. **Update danger levels** - Allow community reporting

### For Users
1. **Check danger level** before visiting
2. **Never go alone** to high-risk spots
3. **Respect property** and local laws
4. **Document changes** to help others
5. **Report hazards** for community safety

## Database Schema

### urbex_spots table
```sql
CREATE TABLE urbex_spots (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    category TEXT NOT NULL,
    latitude REAL NOT NULL,
    longitude REAL NOT NULL,
    danger_level INTEGER CHECK(danger_level BETWEEN 1 AND 4),
    access_difficulty INTEGER CHECK(access_difficulty BETWEEN 1 AND 4),
    -- ... additional fields
);
```

### urbex_visits table
```sql
CREATE TABLE urbex_visits (
    id INTEGER PRIMARY KEY,
    spot_id INTEGER REFERENCES urbex_spots(id),
    visit_date TEXT NOT NULL,
    condition_report TEXT,
    danger_update INTEGER
);
```

## Testing

Run tests:
```bash
python -m pytest tests/test_urbex.py
```

Demo scraping:
```bash
python src/backend/urbex/test_urbex.py
```

## Configuration

Add to main API server:
```python
# src/backend/main.py
from .api.urbex_api import router as urbex_router

app.include_router(urbex_router)
```

## Future Enhancements

1. **Photo Integration**: Store and display exploration photos
2. **Route Planning**: Suggest exploration routes
3. **Weather Integration**: Best times based on weather
4. **Community Features**: User accounts, ratings, comments
5. **Mobile App**: Offline maps and safety checklists
6. **Legal Database**: Track permission requirements
7. **Historical Research**: Link to historical records
8. **3D Mapping**: Interior layouts and floor plans

## Contributing

1. Always prioritize safety features
2. Validate data quality before commits
3. Test with real coordinates in Occitanie
4. Document new categories or fields
5. Consider legal and ethical implications

## License

Part of the SPOTS project - for educational and safety purposes only.