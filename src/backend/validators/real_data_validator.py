"""
CRITICAL: Real Data Validation System
This module ensures NO MOCK, FAKE, OR SIMULATED DATA enters the system
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
import re
import hashlib
from src.backend.core.logging_config import logger


class RealDataValidator:
    """
    Strict validator to ensure all data comes from real sources
    NEVER ALLOW MOCK OR SIMULATED DATA
    """
    
    # Patterns that indicate mock/fake data
    MOCK_PATTERNS = [
        r'test[\s_-]?data',
        r'mock[\s_-]?data',
        r'fake[\s_-]?data',
        r'sample[\s_-]?data',
        r'example[\s_-]?data',
        r'demo[\s_-]?data',
        r'dummy[\s_-]?data',
        r'placeholder',
        r'lorem\s*ipsum',
        r'foo[\s_-]?bar',
        r'john[\s_-]?doe',
        r'jane[\s_-]?doe',
        r'test@(test|example|demo|mock)\.com',
        r'123[\s_-]?456[\s_-]?789',
        r'000[\s_-]?000[\s_-]?000',
        r'xxx+',
        r'aaa+bbb+',
        r'default[\s_-]?value',
        r'\[insert[\s_]+here\]',
        r'\{[\s]*placeholder[\s]*\}',
    ]
    
    # Real data source verification
    VALID_SOURCES = {
        'instagram': {
            'url_pattern': r'https?://(www\.)?instagram\.com/',
            'required_fields': ['post_id', 'timestamp', 'user_handle'],
            'api_endpoints': ['graph.instagram.com', 'i.instagram.com']
        },
        'openstreetmap': {
            'url_pattern': r'https?://(www\.|nominatim\.)?openstreetmap\.org/',
            'required_fields': ['osm_id', 'lat', 'lon'],
            'api_endpoints': ['nominatim.openstreetmap.org', 'overpass-api.de']
        },
        'ign': {
            'url_pattern': r'https?://(data\.)?geopf\.fr/',
            'required_fields': ['feature_id', 'geometry'],
            'api_endpoints': ['data.geopf.fr', 'wxs.ign.fr']
        },
        'tourism_office': {
            'url_pattern': r'https?://.*\.(tourisme|tourism|tourist).*\.(fr|com|org)',
            'required_fields': ['source_url', 'last_updated'],
            'api_endpoints': []
        }
    }
    
    def __init__(self):
        self.validation_log = []
        self.blocked_data_hashes = set()  # Track rejected data to prevent re-entry
        
    def validate_data_source(self, data: Dict[str, Any], source_type: str) -> bool:
        """
        Validate that data comes from a legitimate source
        
        Args:
            data: The data to validate
            source_type: The claimed source of the data
            
        Returns:
            bool: True if data is from real source, False if mock/fake
        """
        # Check if source type is valid
        if source_type not in self.VALID_SOURCES:
            logger.error(f"Invalid source type: {source_type}")
            return False
            
        source_config = self.VALID_SOURCES[source_type]
        
        # 1. Check for mock patterns in all string values
        if self._contains_mock_patterns(data):
            logger.error("Mock/fake patterns detected in data")
            self._block_data(data)
            return False
            
        # 2. Verify required fields exist
        for field in source_config['required_fields']:
            if field not in data or not data[field]:
                logger.error(f"Missing required field for {source_type}: {field}")
                return False
                
        # 3. Verify source URL if provided
        if 'source_url' in data:
            if not self._validate_source_url(data['source_url'], source_config['url_pattern']):
                logger.error(f"Invalid source URL: {data['source_url']}")
                return False
                
        # 4. Check data freshness (not too old, not future)
        if not self._validate_timestamps(data):
            logger.error("Invalid timestamps detected")
            return False
            
        # 5. Verify data hasn't been previously rejected
        data_hash = self._hash_data(data)
        if data_hash in self.blocked_data_hashes:
            logger.error("Previously rejected data attempted re-entry")
            return False
            
        return True
    
    def _contains_mock_patterns(self, data: Any, depth: int = 0) -> bool:
        """Recursively check for mock patterns in data"""
        if depth > 10:  # Prevent infinite recursion
            return False
            
        if isinstance(data, str):
            data_lower = data.lower()
            for pattern in self.MOCK_PATTERNS:
                if re.search(pattern, data_lower):
                    logger.warning(f"Mock pattern detected: {pattern} in {data[:50]}...")
                    return True
                    
        elif isinstance(data, dict):
            for key, value in data.items():
                if self._contains_mock_patterns(key, depth + 1) or \
                   self._contains_mock_patterns(value, depth + 1):
                    return True
                    
        elif isinstance(data, list):
            for item in data:
                if self._contains_mock_patterns(item, depth + 1):
                    return True
                    
        return False
    
    def _validate_source_url(self, url: str, pattern: str) -> bool:
        """Validate URL matches expected source pattern"""
        if not url:
            return False
        return bool(re.match(pattern, url))
    
    def _validate_timestamps(self, data: Dict[str, Any]) -> bool:
        """Ensure timestamps are realistic"""
        timestamp_fields = ['timestamp', 'created_at', 'updated_at', 'date', 'last_updated']
        current_time = datetime.now()
        
        for field in timestamp_fields:
            if field in data:
                try:
                    # Parse timestamp
                    if isinstance(data[field], str):
                        ts = datetime.fromisoformat(data[field].replace('Z', '+00:00'))
                    elif isinstance(data[field], (int, float)):
                        ts = datetime.fromtimestamp(data[field])
                    else:
                        continue
                        
                    # Check if timestamp is reasonable (not too old, not in future)
                    years_old = (current_time - ts).days / 365
                    if years_old > 10 or ts > current_time:
                        return False
                        
                except Exception:
                    return False
                    
        return True
    
    def _hash_data(self, data: Dict[str, Any]) -> str:
        """Create hash of data for tracking"""
        data_str = str(sorted(data.items()))
        return hashlib.sha256(data_str.encode()).hexdigest()
    
    def _block_data(self, data: Dict[str, Any]):
        """Block data from re-entering system"""
        data_hash = self._hash_data(data)
        self.blocked_data_hashes.add(data_hash)
        logger.warning(f"Data blocked with hash: {data_hash[:16]}...")
    
    def validate_batch(self, data_list: List[Dict[str, Any]], source_type: str) -> List[Dict[str, Any]]:
        """
        Validate a batch of data items
        
        Returns:
            List of valid data items only
        """
        valid_items = []
        
        for item in data_list:
            if self.validate_data_source(item, source_type):
                valid_items.append(item)
            else:
                logger.warning(f"Rejected item from {source_type}: {item.get('id', 'unknown')}")
                
        logger.info(f"Validated {len(valid_items)}/{len(data_list)} items from {source_type}")
        return valid_items
    
    def generate_validation_report(self) -> Dict[str, Any]:
        """Generate report of validation activities"""
        return {
            'timestamp': datetime.now().isoformat(),
            'blocked_hashes_count': len(self.blocked_data_hashes),
            'validation_log': self.validation_log[-100:],  # Last 100 entries
            'active_sources': list(self.VALID_SOURCES.keys())
        }


# Global validator instance
real_data_validator = RealDataValidator()


def enforce_real_data(func):
    """
    Decorator to enforce real data validation on scraper functions
    """
    def wrapper(*args, **kwargs):
        result = func(*args, **kwargs)
        
        # Determine source type from function name or class
        source_type = 'unknown'
        if hasattr(func, '__self__'):
            class_name = func.__self__.__class__.__name__.lower()
            for source in real_data_validator.VALID_SOURCES:
                if source in class_name:
                    source_type = source
                    break
                    
        # Validate result
        if isinstance(result, list):
            return real_data_validator.validate_batch(result, source_type)
        elif isinstance(result, dict):
            if real_data_validator.validate_data_source(result, source_type):
                return result
            else:
                logger.error(f"Invalid data from {func.__name__}")
                return None
                
        return result
        
    return wrapper