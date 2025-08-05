-- Create performance indexes for SPOTS database
-- Run this script to boost query performance

-- Location-based queries (most common)
CREATE INDEX IF NOT EXISTS idx_spots_location ON spots(latitude, longitude);

-- Type filtering
CREATE INDEX IF NOT EXISTS idx_spots_type ON spots(type);

-- Department queries  
CREATE INDEX IF NOT EXISTS idx_spots_department ON spots(department);

-- Quality filtering
CREATE INDEX IF NOT EXISTS idx_spots_confidence ON spots(confidence_score);

-- Weather sensitive spots
CREATE INDEX IF NOT EXISTS idx_spots_weather ON spots(weather_sensitive);

-- Combined index for common query pattern
CREATE INDEX IF NOT EXISTS idx_spots_type_confidence ON spots(type, confidence_score DESC);

-- Text search optimization
CREATE INDEX IF NOT EXISTS idx_spots_name ON spots(name);

-- Analyze tables to update statistics
ANALYZE spots;

-- Show created indexes
SELECT name, sql FROM sqlite_master WHERE type = 'index' AND tbl_name = 'spots';