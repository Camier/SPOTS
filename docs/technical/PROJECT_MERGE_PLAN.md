# 🗺️ Toulouse Weather Spots - Project Consolidation Plan

## Overview
Merging two related projects into one comprehensive, best-practices compliant application:
1. **secret-toulouse-spots**: Data collection and scraping system
2. **weather-map-app**: Weather integration and PWA visualization

## 🎯 Goals
- Single source of truth for all components
- Clean, maintainable architecture
- No duplicate files or databases
- Production-ready structure
- Comprehensive documentation
- Automated workflows

## 📁 Proposed Structure

```
toulouse-weather-spots/
├── README.md                    # Main project documentation
├── LICENSE                      # MIT License
├── package.json                 # Node.js dependencies
├── requirements.txt             # Python dependencies
├── .env.example                 # Environment variables template
├── .gitignore                   # Git ignore rules
├── docker-compose.yml           # Optional containerization
│
├── /src/                        # Source code
│   ├── /backend/                # Python backend
│   │   ├── __init__.py
│   │   ├── main.py              # Main entry point
│   │   ├── /scrapers/           # Data collection
│   │   │   ├── base_scraper.py
│   │   │   ├── reddit_scraper.py
│   │   │   ├── instagram_scraper.py
│   │   │   ├── osm_scraper.py
│   │   │   └── tourism_scraper.py
│   │   ├── /processors/         # Data processing
│   │   │   ├── coordinate_extractor.py
│   │   │   ├── data_validator.py
│   │   │   └── nlp_analyzer.py
│   │   ├── /api/                # API endpoints
│   │   │   ├── spots.py
│   │   │   └── weather.py
│   │   └── /utils/              # Utilities
│   │       ├── database.py
│   │       ├── geocoding.py
│   │       └── rate_limiter.py
│   │
│   └── /frontend/               # JavaScript frontend
│       ├── index.html           # Main app entry
│       ├── /js/                 # JavaScript modules
│       │   ├── app.js           # Main application
│       │   ├── weather-service.js
│       │   ├── spot-manager.js
│       │   ├── map-controller.js
│       │   └── ui-manager.js
│       ├── /css/                # Styles
│       │   ├── main.css
│       │   └── components.css
│       └── /pwa/                # PWA files
│           ├── manifest.json
│           └── sw.js
│
├── /data/                       # Data storage
│   ├── toulouse_spots.db        # Main database
│   ├── /exports/                # Data exports
│   └── /cache/                  # Temporary files
│
├── /config/                     # Configuration
│   ├── scrapers.yaml           # Scraper settings
│   ├── logging.yaml            # Logging config
│   └── deployment.yaml         # Deployment settings
│
├── /scripts/                    # Automation scripts
│   ├── setup.sh                # Initial setup
│   ├── migrate_data.py         # Data migration
│   ├── run_scrapers.sh         # Scraper automation
│   └── deploy.sh               # Deployment script
│
├── /tests/                      # Test suites
│   ├── /backend/               # Python tests
│   └── /frontend/              # JavaScript tests
│
├── /docs/                       # Documentation
│   ├── API.md                  # API documentation
│   ├── SCRAPERS.md             # Scraper guide
│   ├── DEPLOYMENT.md           # Deployment guide
│   └── /architecture/          # Architecture diagrams
│
└── /workflows/                  # CI/CD workflows
    ├── .github/                # GitHub Actions
    └── monitoring/             # Monitoring scripts
```

## 🔄 Migration Steps

### Phase 1: Setup (Today)
1. Create new project structure
2. Initialize Git repository
3. Setup configuration files

### Phase 2: Backend Migration
1. Merge scraper code from both projects
2. Consolidate databases (deduplicate)
3. Create unified API

### Phase 3: Frontend Migration
1. Merge weather app features
2. Integrate secret spots UI
3. Optimize for production

### Phase 4: Testing & Documentation
1. Write comprehensive tests
2. Update all documentation
3. Create deployment guides

### Phase 5: Cleanup
1. Archive old projects
2. Update all references
3. Final validation

## 🛠️ Technical Decisions

### Database
- Single SQLite database: `toulouse_spots.db`
- Tables: spots, weather_cache, user_spots, spot_metadata

### API Design
- RESTful API with FastAPI (Python)
- Endpoints:
  - `/api/spots` - CRUD operations
  - `/api/weather/{spot_id}` - Weather data
  - `/api/search` - Search functionality
  - `/api/export` - Data export

### Frontend Architecture
- Vanilla JavaScript ES6 modules
- No framework dependencies
- Progressive enhancement
- Mobile-first design

### Deployment
- Docker support for easy deployment
- Environment-based configuration
- Automated backup system
- Monitoring and alerts

## 📋 File Consolidation Map

| Original Location | New Location | Action |
|-------------------|--------------|--------|
| secret-toulouse-spots/scrapers/* | src/backend/scrapers/ | Merge & Refactor |
| weather-map-app/src/* | src/frontend/js/ | Integrate |
| */hidden_spots.db | data/toulouse_spots.db | Merge & Deduplicate |
| weather-map-app/*.html | src/frontend/ | Consolidate |
| */docs/* | docs/ | Organize |
| .claude/commands/workflow-spots.sh | scripts/workflows.sh | Update paths |

## ✅ Benefits
- Single repository to maintain
- Clear separation of concerns
- Easy to deploy and scale
- Comprehensive documentation
- Automated workflows
- Production-ready structure

## 🚀 Next Steps
1. Review and approve this plan
2. Start Phase 1 implementation
3. Migrate data and code incrementally
4. Test thoroughly at each phase
5. Deploy unified application
