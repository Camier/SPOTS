# 🏗️ SPOTS Architecture Refactoring Plan

Based on the comprehensive analysis, here's a prioritized action plan to address the architectural issues.

## 🚨 Phase 1: Critical Issues (Week 1)

### 1.1 Logging Overhaul
- [ ] Replace 319 print statements with proper logging
- [ ] Set up Python logging configuration
- [ ] Create log levels (DEBUG, INFO, WARNING, ERROR)
- [ ] Add rotating file handlers

```python
# Example: src/config/logging_config.py
import logging
import logging.handlers

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.handlers.RotatingFileHandler('logs/spots.log', maxBytes=10485760, backupCount=5),
            logging.StreamHandler()
        ]
    )
```

### 1.2 Exception Handling Fix
- [ ] Find and fix broad exception handlers
- [ ] Implement specific exception types
- [ ] Add proper error messages and context

### 1.3 Security: Environment Variables
- [ ] Create comprehensive .env file
- [ ] Move ALL API keys and secrets
- [ ] Document required environment variables

## 📦 Phase 2: Dependency Cleanup (Week 2)

### 2.1 Remove Redundant Dependencies
- [ ] Choose Playwright OR Selenium (not both)
- [ ] Remove unnecessary scientific libraries
- [ ] Evaluate if SpaCy is really needed

### 2.2 Frontend Consolidation
- [ ] Audit 10+ map HTML files
- [ ] Identify common functionality
- [ ] Create single configurable entry point

```javascript
// Example: src/frontend/js/unified-map.js
class UnifiedMap {
    constructor(config) {
        this.config = {
            mapType: config.mapType || 'default',
            features: config.features || [],
            dataSource: config.dataSource || 'main'
        };
    }
}
```

## 🔧 Phase 3: Code Organization (Week 3)

### 3.1 Frontend Refactoring
- [ ] Break down ign-wfs-client.js (830 lines)
- [ ] Create modular components
- [ ] Implement proper build system (Vite)

### 3.2 Backend Cleanup
- [ ] Remove duplicate scrapers
- [ ] Consolidate Instagram scrapers (4 → 1)
- [ ] Consolidate OSM scrapers (2 → 1)
- [ ] Archive unused code properly

### 3.3 Database Consolidation
- [ ] Define relationships between DBs
- [ ] Consider single database with proper schemas
- [ ] Implement migrations with Alembic

## 🚀 Phase 4: Architecture Improvements (Week 4)

### 4.1 API Layer
- [ ] Implement proper FastAPI structure
- [ ] Add request/response validation
- [ ] Implement rate limiting
- [ ] Add API documentation (OpenAPI)

### 4.2 Caching Strategy
- [ ] Add Redis for caching
- [ ] Cache expensive IGN/OSM queries
- [ ] Implement cache invalidation

### 4.3 Frontend Build System
```json
// Example: vite.config.js
{
  "build": {
    "rollupOptions": {
      "input": {
        "main": "src/frontend/index.html",
        "admin": "src/frontend/admin.html"
      }
    }
  }
}
```

## 📊 Quick Wins (Can do immediately)

1. **Create logs directory**
   ```bash
   mkdir -p logs
   echo "*.log" >> .gitignore
   ```

2. **Simple logging wrapper**
   ```python
   # src/utils/logger.py
   import logging
   logger = logging.getLogger(__name__)
   ```

3. **Environment template**
   ```bash
   # Already created .env.example
   cp .env.example .env
   ```

## 📈 Success Metrics

- **Code Quality**: Reduce file sizes >500 lines by 50%
- **Performance**: Page load time <2s
- **Maintainability**: Clear module boundaries
- **Security**: Zero hardcoded credentials
- **Testing**: >70% code coverage

## 🔄 Migration Strategy

1. **Parallel Development**: Keep existing code working
2. **Feature Flags**: Toggle between old/new implementations
3. **Incremental Migration**: One module at a time
4. **Testing First**: Write tests before refactoring

## ⚡ Priority Order

1. Security (credentials) - **DONE**
2. Logging (observability)
3. Exception handling (reliability)
4. Frontend consolidation (maintainability)
5. Dependency cleanup (performance)
6. Architecture improvements (scalability)

---

Remember: Each phase should maintain backward compatibility until fully migrated.