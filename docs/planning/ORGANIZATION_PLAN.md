# 📁 SPOTS Project Organization Plan

## Current Issues to Address

### 1. Remove Unnecessary Files/Directories
- **htmlcov/** - 56 coverage report files (6.8 MB)
- **venv/** - Virtual environment (should be local only)
- Root directory clutter (multiple loose files)

### 2. Scraper Directory Cleanup (`src/backend/scrapers/`)
**Keep:**
- `unified_instagram_scraper.py` ✅
- `unified_reddit_scraper.py` ✅
- `base_scraper.py` (needed for inheritance)
- `data_validator.py` (needed for quality checks)
- `geocoding_*.py` files (needed for location validation)
- `rate_limiter.py` (needed for API limits)
- `config.py` (configuration)

**Remove:**
- All Facebook scrapers (6 files)
- Tourism/OSM scrapers (4 files)
- Old/duplicate scrapers
- Test/validation scrapers

### 3. Proposed New Structure
```
spots/
├── src/
│   ├── backend/
│   │   ├── api/            # API endpoints
│   │   ├── core/           # Core functionality
│   │   ├── scrapers/       # Only essential scrapers
│   │   │   ├── base/       # Base classes
│   │   │   ├── social/     # Instagram, Reddit
│   │   │   └── utils/      # Geocoding, validators
│   │   └── migrations/     # DB migrations
│   └── frontend/           # UI files
├── data/                   # Data storage
├── docs/                   # All documentation
├── tests/                  # All tests
├── tools/                  # Development tools
├── config/                 # Configuration files
├── .github/               # GitHub specific
├── README.md
├── requirements.txt
└── .gitignore
```

### 4. Root Directory Cleanup
**Move to config/**:
- `pytest.ini`
- `env.example`
- `requirements*.txt`
- `package.json`
- ESLint/Playwright configs

**Move to docs/planning/**:
- All planning/refactoring markdown files
- Architecture documents
- Progress reports

**Remove:**
- Temporary/test files
- Old organization scripts
- Debug files

### 5. Documentation Consolidation
Current: 95 markdown files across multiple subdirectories
Proposed:
```
docs/
├── api/              # API documentation
├── guides/           # How-to guides
├── architecture/     # System design
├── planning/         # Project planning
└── archive/          # Old/historical docs
```

## Execution Steps

### Phase 1: Clean (Immediate)
```bash
# Remove htmlcov
rm -rf htmlcov/

# Remove __pycache__ directories
find . -type d -name "__pycache__" -exec rm -rf {} +

# Remove .pyc files
find . -type f -name "*.pyc" -delete
```

### Phase 2: Reorganize Scrapers
1. Create new subdirectories in scrapers/
2. Move files to appropriate locations
3. Delete Facebook/tourism/OSM scrapers
4. Update imports in affected files

### Phase 3: Root Cleanup
1. Create config/ directory
2. Move configuration files
3. Archive planning documents
4. Update paths in documentation

### Phase 4: Test & Verify
1. Run API tests
2. Verify imports still work
3. Update .gitignore
4. Commit changes

## Benefits
- **Cleaner structure** - Easier navigation
- **Smaller repo** - Remove 6.8 MB of coverage reports
- **Focused codebase** - Only quality-first scrapers
- **Better organization** - Logical grouping

## Safety Measures
- All deletions tracked in git
- Backup already exists in `backups/20250805_083229/`
- Can revert any changes via git