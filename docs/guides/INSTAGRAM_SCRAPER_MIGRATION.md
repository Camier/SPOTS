# Instagram Scraper Migration Guide

## Overview
This guide explains how to migrate from the multiple Instagram scraper implementations to the new unified scraper.

## Migration Steps

### 1. Update Imports

Replace old imports:
```python
# OLD
from src.backend.scrapers.instagram_best_practices import InstagramBestPractices
from src.backend.scrapers.validated_instagram_scraper import ValidatedInstagramScraper

# NEW
from src.backend.scrapers.unified_instagram_scraper import UnifiedInstagramScraper
```

### 2. Update Class Usage

The UnifiedInstagramScraper provides multiple strategies:
- `"playwright"` - Browser automation (most reliable)
- `"api"` - Direct API calls (fastest)
- `"hybrid"` - Combines both approaches
- `"auto"` - Automatically selects best strategy

```python
# OLD
scraper = InstagramBestPractices()
results = scraper.process_posts(posts)

# NEW
scraper = UnifiedInstagramScraper(strategy="auto")
results = await scraper.scrape("toulouse", limit=10)
```

### 3. Compatibility Aliases

For backward compatibility, these aliases are available:
```python
InstagramScraper = UnifiedInstagramScraper
RealInstagramScraper = UnifiedInstagramScraper
PlaywrightInstagramScraper = UnifiedInstagramScraper
```

### 4. Features Consolidated

The unified scraper includes all features from:
- `instagram_best_practices.py` - Location extraction patterns
- `validated_instagram_scraper.py` - Data validation
- `instagram_playwright_scraper.py` - Browser automation
- `instagram_alternative_scraper.py` - API methods

### 5. New Features

- Automatic strategy selection based on rate limits
- Built-in caching to reduce API calls
- Real data validation with `@enforce_real_data` decorator
- Unified error handling and logging
- Performance monitoring

## Files to Remove (After Migration)

Once migration is complete, these files can be archived:
- `src/backend/scrapers/instagram_best_practices.py`
- `src/backend/scrapers/validated_instagram_scraper.py`
- `src/backend/scrapers/archived_scrapers/instagram_*.py`

## Testing

Run the test script:
```bash
python src/backend/scrapers/unified_instagram_scraper.py
```

Or use the validation tools:
```bash
python tools/scraping/test_instagram_simple.py
```