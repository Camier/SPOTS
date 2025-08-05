# 🚨 CRITICAL: Data Validation Rules for Scrapers

## NEVER CREATE FAKE DATA

All scrapers MUST follow these rules:

### 1. Real Data Sources Only
- ✅ Instagram API: `https://graph.instagram.com/`
- ✅ OpenStreetMap: `https://nominatim.openstreetmap.org/`
- ✅ IGN: `https://data.geopf.fr/`
- ✅ Official tourism sites with verifiable URLs
- ❌ NO generated coordinates
- ❌ NO placeholder text
- ❌ NO test data

### 2. Mandatory Validation
```python
from src.backend.validators.real_data_validator import enforce_real_data

@enforce_real_data
def scrape_data():
    # Your scraping code
    pass
```

### 3. Blocked Patterns
The following will be REJECTED:
- `test`, `mock`, `fake`, `sample`, `example`, `demo`
- `lorem ipsum`, `foo bar`, `john doe`
- `test@example.com`, `123-456-789`
- Any placeholder text

### 4. Required Fields by Source

#### Instagram
- `post_id`: Real Instagram post ID
- `timestamp`: Actual post timestamp
- `user_handle`: Real Instagram username
- `source_url`: Valid Instagram URL

#### OpenStreetMap
- `osm_id`: Real OSM feature ID
- `lat`, `lon`: Actual coordinates from OSM
- `source`: Must be "OpenStreetMap"

#### IGN
- `feature_id`: Real IGN feature ID
- `geometry`: Actual geometry from IGN
- `source_url`: Valid IGN API URL

### 5. Testing with Real Data
When writing tests:
```python
# ✅ GOOD: Real API call
response = requests.get("https://data.geopf.fr/real/endpoint")

# ❌ BAD: Mock data
mock_spots = [{"name": "Test Waterfall", "lat": 43.5}]

# ✅ GOOD: Clearly marked test mock
TEST_ONLY_MOCK_SPOT = {"name": "TEST-ONLY-MOCK-Waterfall"}
```

### 6. Error Handling
If real data cannot be obtained:
```python
# ✅ GOOD: Return empty with explanation
logger.error("Failed to fetch real data from Instagram API")
return []

# ❌ BAD: Generate fake data
return [{"name": "Fake Waterfall", "lat": 43.5}]
```

## Enforcement

The `real_data_validator.py` automatically:
1. Scans all incoming data for mock patterns
2. Verifies source URLs match legitimate endpoints
3. Blocks previously rejected data
4. Logs all validation failures

## Remember

**USERS RELY ON REAL DATA** - Never compromise data integrity with fake information!