# SPOTS Project Documentation & Resources

## Project Overview
SPOTS (Secret Spots in Occitanie) is an interactive web application that displays 817 quality outdoor spots across the Occitanie region of France. It features secure map visualization, XSS protection, and IGN OpenData integration.

## Technologies Used

### 1. Leaflet.js 🍃
**Official Documentation**: https://leafletjs.com/
**GitHub**: https://github.com/Leaflet/Leaflet
**Version**: 1.9.4 (production), 2.0.0-alpha (development)
- Open-source JavaScript library for mobile-friendly interactive maps
- Lightweight (~42 KB)
- 43,000+ GitHub stars
- Key Plugins Used:
  - **Leaflet.markercluster**: https://github.com/Leaflet/Leaflet.markercluster - For clustering map markers
  - **Leaflet.draw**: https://github.com/Leaflet/Leaflet.draw - Vector drawing and editing
  - **Leaflet.heat**: https://github.com/Leaflet/Leaflet.heat - Heatmap visualization

### 2. FastAPI ⚡
**Official Documentation**: https://fastapi.tiangolo.com/
**GitHub**: https://github.com/fastapi/fastapi
**Version**: Latest
- Modern, fast Python web framework for building APIs
- 88,000+ GitHub stars
- Built on Starlette and Pydantic
- Automatic API documentation with Swagger UI
- Key Features:
  - Type hints support
  - Async/await
  - High performance (comparable to NodeJS and Go)
  - Used by Microsoft, Uber, Netflix

### 3. IGN Géoportail 🗺️
**Official Website**: https://geoservices.ign.fr
**Main Portal**: https://www.geoportail.gouv.fr
- French National Institute of Geographic and Forestry Information services
- Provides:
  - Web services (OGC standards)
  - Geolocation API
  - Orthophotos and topographic maps
  - Elevation models (including LiDAR HD)
  - Environmental data layers
- SDK available for 2D/3D mapping
- Extensions for Leaflet, OpenLayers, iTowns

### 4. Puppeteer 🎭
**Official Documentation**: https://pptr.dev/
**GitHub**: https://github.com/puppeteer/puppeteer
- Used for E2E testing in the project
- Headless Chrome automation
- Test files include:
  - Security testing (XSS prevention)
  - IGN integration testing
  - Accessibility testing
  - Responsive design testing

## Related GitHub Projects

### Map Visualization Examples
1. **OpenStreetMap + Leaflet Projects**:
   - Interactive map visualizations
   - Examples: Toronto bike share map, earthquake visualization
   - Demonstrate clustering, popups, and custom markers

2. **FastAPI Projects**:
   - **uvicorn-gunicorn-fastapi-docker**: Docker deployment for FastAPI
   - Full-stack templates with FastAPI backend

3. **Testing with Puppeteer**:
   - E2E testing examples
   - Web scraping demonstrations
   - Browser automation patterns

## Key Features Implemented

### Security
- XSS prevention with HTML escaping
- Content Security Policy headers
- Safe DOM manipulation
- Input validation for coordinates

### Map Features
- Marker clustering for 817 spots
- Multiple map styles (satellite, terrain, street)
- Spot filtering by type
- Search functionality
- Weather-sensitive spot indicators
- IGN environmental data overlays

### API Endpoints
- `/api/spots` - Get all spots with pagination
- `/api/spots/quality` - Quality filtered spots
- `/api/spots/{id}` - Individual spot details
- `/api/spots/department/{code}` - Department filtering
- `/api/ign/spots/{id}/environment` - Environmental analysis
- `/api/config` - Frontend configuration

## Development Setup

### Backend (FastAPI)
```bash
cd src
python -m backend.main
# API available at http://localhost:8000
# Docs at http://localhost:8000/docs
```

### Frontend
```bash
python -m http.server 8085
# Maps available at:
# - http://localhost:8085/debug-map.html
# - http://localhost:8085/enhanced-map-secure.html
# - http://localhost:8085/enhanced-map-ign.html
```

### Testing
```bash
cd tests
npm install
npm test  # Run all E2E tests
```

## Best Practices Applied

1. **Security First**: All user inputs sanitized, CSP headers, XSS prevention
2. **Performance**: Marker clustering, lazy loading, efficient queries
3. **Accessibility**: WCAG 2.1 compliance, keyboard navigation, screen reader support
4. **Responsive Design**: Mobile-first approach, touch-friendly interfaces
5. **Code Quality**: Comprehensive E2E tests, modular architecture

## Resources for Learning

- **Leaflet Tutorials**: https://leafletjs.com/examples.html
- **FastAPI Tutorial**: https://fastapi.tiangolo.com/tutorial/
- **IGN Developer Portal**: https://geoservices.ign.fr/documentation
- **Puppeteer Examples**: https://github.com/puppeteer/puppeteer/tree/main/examples

## License & Credits
- Leaflet.js: BSD 2-Clause License
- FastAPI: MIT License
- IGN Data: Various open data licenses
- OpenStreetMap: © OpenStreetMap contributors