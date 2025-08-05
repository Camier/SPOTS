# Real Instagram Scraper for Occitanie Spots

This is a **REAL** Instagram scraper that fetches **ACTUAL DATA** from Instagram. No simulations, no mock data - only real Instagram posts.

## Features

- ✅ **Real Authentication** - Uses Instagram credentials to login
- ✅ **Location-based scraping** - Search posts from specific Occitanie locations
- ✅ **Hashtag-based scraping** - Find posts with Occitanie-related hashtags
- ✅ **French Geocoding** - Integrates with BAN/IGN for address and elevation data
- ✅ **Occitanie filtering** - Only keeps spots within Occitanie region
- ✅ **Activity extraction** - Detects activities mentioned in posts
- ✅ **Spot type detection** - Identifies cascades, lakes, caves, etc.

## Installation

```bash
pip install instagrapi
```

## Setup

1. Create a `.env` file with your Instagram credentials:
```env
INSTAGRAM_USERNAME=your_username
INSTAGRAM_PASSWORD=your_password
```

2. Or set environment variables:
```bash
export INSTAGRAM_USERNAME='your_username'
export INSTAGRAM_PASSWORD='your_password'
```

## Usage

### Command Line
```bash
python instagram_real_scraper.py --username YOUR_USERNAME --password YOUR_PASSWORD --method location --limit 50
```

### In Code
```python
from backend.scrapers.instagram_real_scraper import RealInstagramScraper

# Create scraper
scraper = RealInstagramScraper(
    username="your_username",
    password="your_password"
)

# Scrape by location
spots = scraper.scrape(limit=50, method="location")

# Scrape by hashtag
spots = scraper.scrape(limit=50, method="hashtag")

# Search specific location
results = scraper.search_location_by_name("Lac de Salagou")

# Get posts from outdoor account
posts = scraper.get_user_posts("randonnee_pyrenees", limit=10)
```

## Scraping Methods

### 1. Location-based Scraping
Searches for posts from popular Occitanie locations:
- Lac de Salagou
- Gorges du Tarn
- Pic du Midi
- Pont du Gard
- Carcassonne
- And more...

### 2. Hashtag-based Scraping
Monitors Occitanie-specific hashtags:
- #occitaniesecrete
- #toulousesecret
- #pyrenéescachées
- #gorgesdutarn
- Department-specific tags
- Activity-specific tags

## Data Structure

Each scraped spot contains:
```json
{
    "source": "instagram:#hashtag",
    "source_url": "https://instagram.com/p/CODE",
    "raw_text": "Original caption",
    "name": "Cascade de Cauterets",
    "latitude": 42.9023,
    "longitude": -0.1033,
    "address_hint": "Cauterets, 65 Hautes-Pyrénées",
    "department": "65",
    "type": "cascade",
    "activities": ["baignade", "randonnée"],
    "is_hidden": 1,
    "metadata": {
        "instagram_id": "123456789",
        "user": "username",
        "likes": 245,
        "comments": 12,
        "is_real_data": true
    }
}
```

## Important Notes

1. **Rate Limiting** - Instagram has strict rate limits. The scraper includes delays.
2. **Authentication** - Use a dedicated account, not your personal one.
3. **Session Persistence** - Sessions are saved to avoid repeated logins.
4. **Privacy** - Respects private accounts (doesn't scrape them).
5. **Real Data Only** - This scraper NEVER generates fake data.

## Troubleshooting

- **Login Failed**: Check credentials, ensure account isn't blocked
- **No Posts Found**: Location might not have recent posts, try different locations
- **Rate Limited**: Wait a few hours before trying again
- **Session Expired**: Delete session file and re-authenticate

## Compliance

This scraper is for educational/research purposes. Always respect:
- Instagram's Terms of Service
- User privacy
- Rate limits
- Copyright of content