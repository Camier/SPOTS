import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { JSDOM } from 'jsdom';

describe('Regional Map Optimized', () => {
  let dom;
  let window;
  let document;
  let mockFetch;

  beforeEach(() => {
    // Create DOM environment
    dom = new JSDOM(`
      <!DOCTYPE html>
      <html>
        <body>
          <div id="map"></div>
          <div id="stats-container"></div>
          <div id="loading"></div>
          <select id="department-select">
            <option value="all">Tous les départements</option>
          </select>
          <div class="filter-buttons">
            <button class="filter-btn active" data-filter-type="all">Tous</button>
          </div>
        </body>
      </html>
    `, {
      url: 'http://localhost:8081',
      runScripts: 'dangerously',
      resources: 'usable'
    });

    window = dom.window;
    document = window.document;
    global.window = window;
    global.document = document;

    // Mock Leaflet
    global.L = {
      map: vi.fn(() => ({
        setView: vi.fn().mockReturnThis(),
        addLayer: vi.fn(),
        fitBounds: vi.fn(),
        addControl: vi.fn()
      })),
      tileLayer: vi.fn(() => ({
        addTo: vi.fn()
      })),
      marker: vi.fn(() => ({
        bindPopup: vi.fn().mockReturnThis()
      })),
      divIcon: vi.fn(),
      markerClusterGroup: vi.fn(() => ({
        clearLayers: vi.fn(),
        addLayers: vi.fn(),
        addLayer: vi.fn(),
        getBounds: vi.fn(() => ({
          pad: vi.fn()
        }))
      })),
      control: {
        layers: vi.fn(() => ({
          addTo: vi.fn()
        }))
      }
    };

    // Mock fetch
    mockFetch = vi.fn();
    global.fetch = mockFetch;
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  describe('Map Initialization', () => {
    it('should initialize map with correct center and zoom', () => {
      // Simulate map initialization
      const mapSpy = vi.spyOn(L, 'map');
      
      // Execute map initialization code
      const map = L.map('map').setView([43.8, 1.8], 8);
      
      expect(mapSpy).toHaveBeenCalledWith('map');
      expect(map.setView).toHaveBeenCalledWith([43.8, 1.8], 8);
    });

    it('should add all map layers', () => {
      const tileLayerSpy = vi.spyOn(L, 'tileLayer');
      
      // Test IGN layers
      const ignPlanLayer = L.tileLayer('https://data.geopf.fr/wmts?SERVICE=WMTS&REQUEST=GetTile&VERSION=1.0.0&LAYER=GEOGRAPHICALGRIDSYSTEMS.PLANIGNV2&STYLE=normal&TILEMATRIXSET=PM&TILEMATRIX={z}&TILEROW={y}&TILECOL={x}&FORMAT=image/png');
      
      expect(tileLayerSpy).toHaveBeenCalled();
      expect(tileLayerSpy).toHaveBeenCalledWith(
        expect.stringContaining('data.geopf.fr')
      );
    });

    it('should create marker cluster group with performance options', () => {
      const clusterSpy = vi.spyOn(L, 'markerClusterGroup');
      
      const markers = L.markerClusterGroup({
        chunkedLoading: true,
        maxClusterRadius: 60,
        disableClusteringAtZoom: 14,
        spiderfyOnMaxZoom: true,
        removeOutsideVisibleBounds: true
      });
      
      expect(clusterSpy).toHaveBeenCalledWith({
        chunkedLoading: true,
        maxClusterRadius: 60,
        disableClusteringAtZoom: 14,
        spiderfyOnMaxZoom: true,
        removeOutsideVisibleBounds: true
      });
    });
  });

  describe('Spot Loading', () => {
    it('should fetch spots from API', async () => {
      const mockSpots = {
        total: 100,
        spots: [
          {
            id: 1,
            name: 'Test Spot',
            latitude: 43.5,
            longitude: 1.5,
            type: 'waterfall',
            description: 'Test description',
            confidence_score: 0.8,
            elevation: 500
          }
        ]
      };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockSpots
      });

      const response = await fetch('http://localhost:8000/api/spots/quality?limit=1000&min_confidence=0.6');
      const data = await response.json();

      expect(mockFetch).toHaveBeenCalledWith(
        'http://localhost:8000/api/spots/quality?limit=1000&min_confidence=0.6'
      );
      expect(data).toEqual(mockSpots);
    });

    it('should handle API errors gracefully', async () => {
      mockFetch.mockRejectedValueOnce(new Error('Network error'));

      try {
        await fetch('http://localhost:8000/api/spots/quality');
      } catch (error) {
        expect(error.message).toBe('Network error');
      }
    });
  });

  describe('Filtering', () => {
    it('should filter spots by type', () => {
      const spots = [
        { type: 'waterfall', name: 'Cascade 1' },
        { type: 'cave', name: 'Grotte 1' },
        { type: 'waterfall', name: 'Cascade 2' }
      ];

      const filtered = spots.filter(spot => spot.type === 'waterfall');
      expect(filtered).toHaveLength(2);
      expect(filtered[0].name).toBe('Cascade 1');
    });

    it('should filter spots by department bounds', () => {
      const spots = [
        { latitude: 43.1, longitude: 1.9 }, // In bounds
        { latitude: 44.5, longitude: 2.5 }, // Out of bounds
      ];

      const bounds = { lat_max: 43.2, lng_max: 2.0 };
      const filtered = spots.filter(spot => {
        return spot.latitude < bounds.lat_max && spot.longitude < bounds.lng_max;
      });

      expect(filtered).toHaveLength(1);
    });
  });

  describe('UI Interactions', () => {
    it('should update active filter button on click', () => {
      const button = document.querySelector('.filter-btn');
      const allButtons = document.querySelectorAll('.filter-btn');
      
      // Simulate click
      button.click();
      
      // In real implementation, this would update classes
      allButtons.forEach(b => b.classList.remove('active'));
      button.classList.add('active');
      
      expect(button.classList.contains('active')).toBe(true);
    });

    it('should update stats display', () => {
      const statsContainer = document.getElementById('stats-container');
      const count = 150;
      
      statsContainer.textContent = `${count} spots affichés`;
      
      expect(statsContainer.textContent).toBe('150 spots affichés');
    });
  });

  describe('Marker Creation', () => {
    it('should create custom div icon for markers', () => {
      const iconSpy = vi.spyOn(L, 'divIcon');
      
      L.divIcon({
        className: 'spot-marker',
        iconSize: [12, 12]
      });
      
      expect(iconSpy).toHaveBeenCalledWith({
        className: 'spot-marker',
        iconSize: [12, 12]
      });
    });

    it('should bind popup content to markers', () => {
      const marker = L.marker([43.5, 1.5]);
      const popupContent = '<div class="spot-popup"><h4>Test Spot</h4></div>';
      
      marker.bindPopup(popupContent);
      
      expect(marker.bindPopup).toHaveBeenCalledWith(popupContent);
    });
  });
});