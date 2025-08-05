# 🏗️ SPOTS Refactoring Master Plan
*Generated through sequential analysis with revision branches*

## 🎯 Critical Path Analysis

After analyzing dependencies, the critical path is:
**Logging → Database Consolidation → Data Verification → Frontend → Performance**

## 📊 Risk Assessment

### High Risk Areas
1. **Database Migration**: Data loss potential
2. **Frontend Breaking**: User-facing impact  
3. **API Changes**: External integrations

### Mitigation Strategies
- Feature flags for gradual rollout
- Blue-green deployment for databases
- Comprehensive backups before each phase
- Keep old code until new code is verified

## 🚀 Implementation Phases

### Phase 0: Prerequisites (Day 1-2)
```bash
# Backup everything
./scripts/backup_all_databases.sh

# Create feature branch
git checkout -b refactor/phase-1-foundation

# Document current state
python scripts/document_api_endpoints.py > docs/api_baseline.md
python scripts/analyze_database_schemas.py > docs/db_baseline.md
```

### Phase 1: Logging Foundation (Week 1)

#### Day 1-2: Core Logging
- [x] Create logging configuration ✓
- [ ] Replace prints in API endpoints (main.py)
- [ ] Replace prints in critical scrapers
- [ ] Add structured logging for errors

#### Day 3-4: Scraper Analysis
```python
# Analyze scraper quality
for scraper in ['instagram_best_practices.py', 'unified_instagram_scraper.py', 
                'validated_instagram_scraper.py']:
    - Check last modified date
    - Count functions and complexity
    - Analyze error handling
    - Test with sample data
```

#### Day 5: Consolidation Decision
- [ ] Choose primary Instagram scraper
- [ ] Archive redundant scrapers
- [ ] Update imports in dependent code

### Phase 2: Database Consolidation (Week 2)

#### New Unified Schema
```sql
-- Core tables
CREATE TABLE spots (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    latitude REAL NOT NULL,
    longitude REAL NOT NULL,
    type TEXT,
    description TEXT,
    verification_status TEXT DEFAULT 'unverified',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE spot_sources (
    id INTEGER PRIMARY KEY,
    spot_id INTEGER REFERENCES spots(id),
    source_type TEXT NOT NULL, -- 'osm', 'instagram', 'manual'
    source_url TEXT,
    source_data JSON,
    scraped_at TIMESTAMP,
    confidence_score REAL
);

CREATE TABLE spot_verifications (
    id INTEGER PRIMARY KEY,
    spot_id INTEGER REFERENCES spots(id),
    verified_by TEXT,
    verified_at TIMESTAMP,
    verification_method TEXT,
    evidence JSON,
    notes TEXT
);
```

#### Migration Strategy (Blue-Green)
1. Create new consolidated DB alongside existing
2. Implement dual-write adapter:
```python
class DualWriteAdapter:
    def write_spot(self, spot_data):
        # Write to both old and new databases
        self.write_to_legacy(spot_data)
        self.write_to_unified(spot_data)
```
3. Gradually migrate reads to new DB
4. Verify data integrity
5. Sunset old databases

### Phase 3: Frontend Consolidation (Week 3)

#### Component Architecture
```javascript
// New unified map component
class UnifiedMap {
    constructor(config) {
        this.config = {
            mapType: config.mapType || 'default',
            features: config.features || [],
            dataSource: config.dataSource || 'main',
            layers: config.layers || ['base']
        };
    }
    
    // Single entry point for all map variants
    static create(type) {
        const configs = {
            'full-featured': { features: ['all'], layers: ['base', 'ign', 'overlays'] },
            'optimized': { features: ['core'], layers: ['base'] },
            'admin': { features: ['all', 'edit'], layers: ['base', 'admin'] }
        };
        return new UnifiedMap(configs[type]);
    }
}
```

#### Migration Order
1. regional-map-optimized.html → First (simplest)
2. regional-map-api.html → Second (API integration)
3. regional-map-full-featured.html → Third (complex)
4. Archive old implementations

### Phase 4: Performance & Polish (Week 4)

#### Optimization Targets
- [ ] Implement Redis caching for expensive queries
- [ ] Add database indexes for common queries
- [ ] Bundle JavaScript with Vite
- [ ] Implement lazy loading for map layers
- [ ] Add API rate limiting

#### Monitoring Setup
```python
# Add performance monitoring
from src.monitoring import track_performance

@track_performance
def get_spots_by_region(region):
    # Tracks execution time, memory usage
    pass
```

## 📋 Rollback Procedures

### For Each Phase:
1. **Database**: Keep backups, use transactions
2. **Code**: Git tags for each stable version
3. **Frontend**: Feature flags to toggle old/new
4. **API**: Versioning for backwards compatibility

## 🔍 Success Metrics

### Technical Metrics
- Reduce average file size from 830 to <300 lines
- Improve page load time by 50%
- Achieve 80% test coverage
- Zero hardcoded credentials

### Code Quality Metrics  
- No broad exception handlers
- All prints replaced with logging
- Single source of truth for data
- Clear module boundaries

## 🚨 Decision Points

### After Each Phase:
1. **Continue?** Assess stability
2. **Rollback?** If critical issues
3. **Adjust?** Based on learnings

### Go/No-Go Criteria
- [ ] All tests passing
- [ ] No performance regression
- [ ] No data integrity issues
- [ ] User acceptance (if applicable)

## 📅 Timeline Summary

| Week | Focus | Deliverable | Risk Level |
|------|-------|-------------|------------|
| 1 | Foundation | Logging + Scraper consolidation | Low |
| 2 | Data Layer | Unified database schema | High |
| 3 | Frontend | Component architecture | Medium |
| 4 | Polish | Performance optimization | Low |

## 🎓 Lessons from Analysis

1. **Data First**: Database issues block everything else
2. **Incremental**: Small changes are safer than big bang
3. **Measure**: Can't improve what you don't measure
4. **Document**: Future you will thank current you

---

*This plan emerged from sequential thinking with multiple revision branches. See thought process in PLANNING_THOUGHTS.md*