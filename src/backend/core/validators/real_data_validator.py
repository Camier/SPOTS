"""
Real Data Validation System
Ensures NO MOCK, FAKE, OR SIMULATED DATA enters the system
"""

import re
import hashlib
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class RealDataValidator:
    """
    Strict validator to ensure all data comes from real sources
    NEVER ALLOW MOCK OR SIMULATED DATA
    """
    
    # Patterns that indicate mock/fake data
    MOCK_PATTERNS = [
        r'test[\s_-]?data', r'mock[\s_-]?data', r'fake[\s_-]?data',
        r'sample[\s_-]?data', r'example[\s_-]?data', r'demo[\s_-]?data',
        r'dummy[\s_-]?data', r'placeholder', r'lorem\s*ipsum', r'foo[\s_-]?bar',
        r'test\d+', r'user\d+', r'spot\d+', r'location\d+', r'example\.com',
        r'generated[\s_-]?by', r'created[\s_-]?by[\s_-]?ai', r'synthetic',
        r'simulated', r'artificial', r'fabricated'
    ]
    
    # Required real data indicators
    REAL_DATA_INDICATORS = {
        'instagram': ['instagram_id', 'username', 'timestamp', 'media_url'],
        'reddit': ['reddit_id', 'author', 'subreddit', 'created_utc'],
        'manual': ['verifier_id', 'verification_date', 'photo_proof'],
        'tourist_office': ['office_id', 'official_url', 'last_updated']
    }

    def __init__(self):
        self.validation_log = []
        self.suspicious_patterns = {}

    def validate_real_data(self, data: Dict[str, Any], source: str) -> tuple[bool, str]:
        """
        Strictly validate that data is from real sources
        Returns (is_real, reason)
        """
        # Check for mock patterns
        if self._contains_mock_patterns(data):
            return False, "Data contains mock/fake patterns"
        
        # Verify source indicators
        if not self._has_real_source_indicators(data, source):
            return False, f"Missing required {source} source indicators"
        
        # Check data authenticity
        if not self._verify_data_authenticity(data, source):
            return False, "Data authenticity verification failed"
        
        # Verify timestamps
        if not self._verify_timestamps(data):
            return False, "Invalid or suspicious timestamps"
        
        # Check for generated content
        if self._appears_generated(data):
            return False, "Content appears to be AI-generated"
        
        return True, "Data validated as real"

    def _contains_mock_patterns(self, data: Dict[str, Any]) -> bool:
        """Deep check for mock data patterns"""
        data_str = str(data).lower()
        
        for pattern in self.MOCK_PATTERNS:
            if re.search(pattern, data_str, re.IGNORECASE):
                self.suspicious_patterns[pattern] = self.suspicious_patterns.get(pattern, 0) + 1
                logger.warning(f"Mock pattern detected: {pattern}")
                return True
        
        # Check for sequential IDs
        if self._has_sequential_ids(data):
            return True
            
        # Check for default values
        if self._has_default_values(data):
            return True
            
        return False

    def _has_real_source_indicators(self, data: Dict[str, Any], source: str) -> bool:
        """Verify data has required real source indicators"""
        required_fields = self.REAL_DATA_INDICATORS.get(source, [])
        return all(field in data and data[field] for field in required_fields)

    def _verify_data_authenticity(self, data: Dict[str, Any], source: str) -> bool:
        """Verify data authenticity based on source"""
        if source == 'instagram':
            # Check Instagram ID format
            ig_id = data.get('instagram_id', '')
            if not re.match(r'^\d{10,}$', str(ig_id)):
                return False
            # Verify media URL is from Instagram CDN
            media_url = data.get('media_url', '')
            if not any(domain in media_url for domain in ['cdninstagram.com', 'fbcdn.net']):
                return False
                
        elif source == 'reddit':
            # Check Reddit ID format
            reddit_id = data.get('reddit_id', '')
            if not re.match(r'^[a-z0-9]{6,}$', str(reddit_id)):
                return False
                
        return True

    def _verify_timestamps(self, data: Dict[str, Any]) -> bool:
        """Verify timestamps are realistic"""
        timestamp_fields = ['created_at', 'updated_at', 'timestamp', 'created_utc']
        current_time = datetime.now()
        
        for field in timestamp_fields:
            if field in data:
                try:
                    if isinstance(data[field], str):
                        ts = datetime.fromisoformat(data[field].replace('Z', '+00:00'))
                    elif isinstance(data[field], (int, float)):
                        ts = datetime.fromtimestamp(data[field])
                    else:
                        ts = data[field]
                    
                    # Check if timestamp is in the future
                    if ts > current_time:
                        return False
                    
                    # Check if timestamp is too old (before social media existed)
                    if ts.year < 2004:  # Facebook founded in 2004
                        return False
                        
                except (ValueError, TypeError):
                    return False
                    
        return True

    def _appears_generated(self, data: Dict[str, Any]) -> bool:
        """Check if content appears to be AI-generated"""
        text_fields = ['description', 'caption', 'text', 'content']
        
        for field in text_fields:
            if field in data and data[field]:
                text = str(data[field])
                
                # Check for AI generation markers
                ai_markers = [
                    'as an ai', 'as a language model', 'i cannot', 'i don\'t have',
                    'generated content', 'this is a generated'
                ]
                
                for marker in ai_markers:
                    if marker in text.lower():
                        return True
                        
                # Check for perfect grammar/punctuation (suspicious for social media)
                if self._has_perfect_grammar(text):
                    return True
                    
        return False

    def _has_sequential_ids(self, data: Dict[str, Any]) -> bool:
        """Check for sequential or patterned IDs"""
        id_fields = ['id', 'spot_id', 'location_id', 'instagram_id', 'reddit_id']
        
        for field in id_fields:
            if field in data:
                id_val = str(data[field])
                # Check for simple sequences like 1, 2, 3 or test1, test2
                if re.match(r'^(test|user|spot|location)?\d{1,4}$', id_val):
                    return True
                    
        return False

    def _has_default_values(self, data: Dict[str, Any]) -> bool:
        """Check for default/placeholder values"""
        default_values = [
            'unnamed', 'untitled', 'default', 'n/a', 'na', 'none',
            'todo', 'tbd', 'xxx', '...', '???', 'change me'
        ]
        
        data_str = str(data).lower()
        return any(default in data_str for default in default_values)

    def _has_perfect_grammar(self, text: str) -> bool:
        """Check if text has suspiciously perfect grammar for social media"""
        # Social media text usually has some imperfections
        if len(text) > 50:
            # Count sentences
            sentences = re.split(r'[.!?]', text)
            if len(sentences) > 2:
                # Check if all sentences start with capital
                all_capitalized = all(s.strip() and s.strip()[0].isupper() 
                                    for s in sentences if s.strip())
                # Check for proper punctuation
                proper_punctuation = text.rstrip()[-1] in '.!?'
                
                if all_capitalized and proper_punctuation and '...' not in text:
                    return True
                    
        return False

    def get_suspicious_patterns(self) -> Dict[str, int]:
        """Get count of suspicious patterns detected"""
        return self.suspicious_patterns.copy()