# SPOTS Map Validation Framework 🗺️

Automated map validation framework for the SPOTS project using Puppeteer and Leaflet.js. This framework provides comprehensive testing for interactive maps including visual regression testing, feature validation, and performance benchmarking.

## 🚀 Features

### Core Validation
- **Automated Browser Testing**: Full Puppeteer integration for headless and headed testing
- **Visual Regression Testing**: Screenshot comparison and visual validation
- **Map Layer Testing**: Validates IGN, OSM, Satellite, and Terrain layers
- **Control Testing**: Tests all map controls (zoom, search, filters, etc.)
- **Performance Metrics**: Load time and interaction performance tracking

### Advanced Map Features
- **🌲 Forest Overlay**: IGN FORESTINVENTORY.V2 integration
- **🔥 Heatmap Visualization**: Dynamic heat mapping with Leaflet.heat
- **☀️ Sun/Shadow Calculator**: Real-time sun position and shadow analysis
- **📍 Marker Clustering**: Efficient handling of multiple spots
- **🔍 Advanced Search**: Location search with geocoding
- **🌤️ Weather Integration**: Real-time weather data display

## 🛠️ Installation

```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/spots-map-validation.git
cd spots-map-validation

# Install dependencies
npm install

# Start the development server
npm run dev
```

## 🧪 Running Tests

```bash
# Run all validations
npm test

# Validate main map
node tests/map-validation/validate-main-map.js

# Test specific features
node tests/map-validation/test-features.js

# Test advanced features
node tests/map-validation/test-advanced-features.js
```

## 📊 Validation Results

The framework generates comprehensive reports including:
- ✅ Map initialization status
- 🗺️ Layer functionality
- 🎮 Control responsiveness
- 📸 Visual regression results
- ⏱️ Performance metrics
- 🌟 Advanced feature status

## 🔧 Configuration

```javascript
const options = {
    headless: false,              // Run with visible browser
    screenshotDir: './screenshots',
    baseUrl: 'http://localhost:8085',
    viewport: { width: 1920, height: 1080 }
};
```

## 🗺️ Map Providers

- **IGN Plan**: Institut Géographique National base maps
- **OpenStreetMap**: Community-driven map data
- **Satellite**: High-resolution satellite imagery
- **Terrain**: Topographic elevation data
- **Forest Overlay**: IGN forest inventory data

## 🌟 Advanced Features

### Forest Overlay
```javascript
app.toggleForestOverlay(true);  // Enable forest visualization
```

### Heatmap
```javascript
app.toggleHeatmap(true);  // Show spot density heatmap
```

### Sun Calculator
```javascript
app.toggleSunCalculator();  // Activate sun/shadow analysis
```

## 📁 Project Structure

```
tests/map-validation/
├── map-validator.js           # Core validation framework
├── validate-main-map.js       # Main map validation script
├── test-advanced-features.js  # Advanced feature tests
├── test-features.js           # Feature-by-feature testing
├── screenshots/              # Visual regression screenshots
│   ├── advanced/            # Advanced feature screenshots
│   └── *.png               # Validation screenshots
└── validation-report.json    # Latest validation results

src/frontend/
├── main-map.html            # Production-ready map interface
├── js/
│   ├── main-map-app.js     # Main application class
│   └── modules/            # Modular components
├── css/
│   └── main-map.css        # Professional styling
└── test-maps/              # Test map implementations
```

## 📝 API Documentation

### MapValidator Class
```javascript
const validator = new MapValidator(options);
await validator.init();
await validator.loadMap('/main-map.html');
await validator.validateMapInit();
await validator.generateReport();
```

### MainMapApp Class
```javascript
const app = new MainMapApp();
app.initializeMap();
app.loadSpots();
app.toggleHeatmap(true);
```

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 🐛 Known Issues

- Leaflet.heat may require manual plugin loading in some environments
- IGN tiles require proper API keys for production use
- Sun calculator requires location permissions for accurate calculations

## 🚀 Future Enhancements

- [ ] Real-time data integration (weather, conditions)
- [ ] Mobile device optimization
- [ ] Offline map support
- [ ] Advanced routing capabilities
- [ ] Multi-language support
- [ ] PWA functionality

## 🔍 Debugging Failed Tests

1. **Run with visible browser:**
   ```bash
   node run-validation.js --show --devtools
   ```

2. **Check screenshots:**
   - Failed tests save screenshots automatically
   - Located in `screenshots/YYYY-MM-DD/`

3. **View console logs:**
   - Browser errors are captured
   - Check for JavaScript errors

## 📈 Performance Thresholds

| Metric | Threshold | Description |
|--------|-----------|-------------|
| Load Time | < 3s | Total page load |
| Memory | < 100MB | JavaScript heap |
| FPS | > 30 | During map pan |
| Tile Load | < 1s | Average per tile |

## 🚨 Common Issues

### "Map not initialized"
- Ensure backend server is running on port 8000
- Check if frontend server is on port 8085
- Verify map container exists with id="map"

### "No tiles loaded"
- Check IGN API key configuration
- Verify network connectivity
- Ensure CORS headers are set

### "Timeout waiting for selector"
- Increase timeout in map-validator.js
- Check if page structure changed
- Verify JavaScript errors in console

## 🔧 Maintenance

1. **Update reference screenshots:**
   ```bash
   rm -rf screenshots/reference/
   node run-validation.js --screenshots
   ```

2. **Add new test endpoints:**
   - Update test-scenarios.js
   - Create test HTML files
   - Document expected behavior

3. **Adjust performance thresholds:**
   - Edit limits in test-scenarios.js
   - Consider device capabilities
   - Account for network conditions

## 📝 Best Practices

1. **Keep tests focused** - One feature per test
2. **Use meaningful names** - Describe what's being tested
3. **Add error context** - Help debug failures
4. **Clean up state** - Reset between tests
5. **Document changes** - Update this README

## 🤝 Contributing

1. Create feature branch
2. Add/update tests
3. Run full validation suite
4. Submit PR with test results

---

For questions or issues, check the [SPOTS project documentation](../../SPOTS-PROJECT-CLAUDE.md) or open an issue.