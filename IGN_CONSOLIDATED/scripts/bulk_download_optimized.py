#!/usr/bin/env python3
"""
Optimized IGN Bulk Download using Téléchargement API
Based on official IGN documentation for efficient large dataset downloads
"""

import requests
import time
import os
from pathlib import Path
import json
from typing import List, Dict, Optional
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class IGNBulkDownloader:
    """Efficient bulk downloader using IGN Téléchargement service"""
    
    def __init__(self, output_dir: str = "bulk_downloads"):
        self.base_url = "https://data.geopf.fr/telechargement"
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Rate limiting: Be conservative - 2 requests per second
        self.min_request_interval = 0.5  # 500ms between requests
        self.last_request_time = 0
        self.retry_count = 0
        self.max_retries = 3
        
        # Session for connection pooling
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'IGN-Bulk-Downloader/1.0'
        })
        
    def _rate_limit(self):
        """Ensure we don't exceed rate limits"""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.min_request_interval:
            time.sleep(self.min_request_interval - elapsed)
        self.last_request_time = time.time()
    
    def _handle_429(self, retry_num: int):
        """Handle rate limit errors with exponential backoff"""
        wait_time = (2 ** retry_num) * 2  # 2, 4, 8 seconds
        logger.warning(f"Rate limited (429). Waiting {wait_time} seconds...")
        time.sleep(wait_time)
        
    def get_capabilities(self, zone: str = "FRA", format: str = None, 
                        polygon: str = None, limit: int = 50) -> Dict:
        """
        Get available resources with filtering
        
        Args:
            zone: Geographic zone (e.g., "FRA", "D031" for department)
            format: File format filter (e.g., "SHP", "GPKG")
            polygon: WKT polygon for spatial filtering
            limit: Results per page (max 50)
        """
        self._rate_limit()
        
        params = {
            'zone': zone,
            'limit': limit
        }
        
        if format:
            params['format'] = format
        if polygon:
            params['polygon'] = polygon
            
        url = f"{self.base_url}/capabilities"
        
        try:
            response = self.session.get(url, params=params)
            response.raise_for_status()
            
            # Parse XML response
            import xml.etree.ElementTree as ET
            root = ET.fromstring(response.text)
            
            # Extract resources from Atom feed
            ns = {
                'atom': 'http://www.w3.org/2005/Atom',
                'gpf_dl': 'https://data.geopf.fr/annexes/ressources/xsd/gpf_dl.xsd'
            }
            
            resources = []
            for entry in root.findall('atom:entry', ns):
                title = entry.find('atom:title', ns)
                link = entry.find('atom:link[@rel="alternate"]', ns)
                if title is not None and link is not None:
                    resources.append({
                        'name': title.text,
                        'url': link.get('href')
                    })
            
            return {'resources': resources}
        except Exception as e:
            logger.error(f"Failed to get capabilities: {e}")
            return {}
            
    def get_resource_list(self, resource_name: str, page: int = 1, 
                         limit: int = 50) -> List[Dict]:
        """
        Get list of dataset folders for a resource
        
        Args:
            resource_name: Name of the resource
            page: Page number for pagination
            limit: Results per page
        """
        self._rate_limit()
        
        url = f"{self.base_url}/resource/{resource_name}"
        params = {
            'page': page,
            'limit': limit
        }
        
        try:
            response = self.session.get(url, params=params)
            response.raise_for_status()
            
            # Parse XML response
            import xml.etree.ElementTree as ET
            root = ET.fromstring(response.text)
            
            ns = {
                'atom': 'http://www.w3.org/2005/Atom',
                'gpf_dl': 'https://data.geopf.fr/annexes/ressources/xsd/gpf_dl.xsd'
            }
            
            items = []
            for entry in root.findall('atom:entry', ns):
                title = entry.find('atom:title', ns)
                link = entry.find('atom:link[@rel="alternate"]', ns)
                if title is not None and link is not None:
                    # Extract name from URL
                    url_parts = link.get('href').split('/')
                    sub_resource_name = url_parts[-1] if url_parts else title.text
                    items.append({
                        'name': sub_resource_name,
                        'title': title.text,
                        'url': link.get('href')
                    })
            
            return items
        except Exception as e:
            logger.error(f"Failed to get resource list: {e}")
            return []
            
    def get_files_list(self, resource_name: str, sub_resource: str) -> List[Dict]:
        """
        Get list of files in a specific dataset folder
        
        Args:
            resource_name: Main resource name
            sub_resource: Sub-resource/folder name
        """
        self._rate_limit()
        
        url = f"{self.base_url}/resource/{resource_name}/{sub_resource}"
        
        for retry in range(self.max_retries):
            try:
                response = self.session.get(url)
                
                if response.status_code == 429:
                    self._handle_429(retry)
                    continue
                    
                response.raise_for_status()
                
                # Parse XML response
                import xml.etree.ElementTree as ET
                root = ET.fromstring(response.text)
                
                ns = {
                    'atom': 'http://www.w3.org/2005/Atom',
                    'gpf_dl': 'https://data.geopf.fr/annexes/ressources/xsd/gpf_dl.xsd'
                }
                
                files = []
                for entry in root.findall('atom:entry', ns):
                    title = entry.find('atom:title', ns)
                    link = entry.find('atom:link[@rel="alternate"]', ns)
                    size_elem = entry.find('atom:content[@type="text"]', ns)
                    
                    if title is not None and link is not None:
                        file_info = {
                            'name': title.text,
                            'url': link.get('href'),
                            'size': 0
                        }
                        
                        # Try to extract size from content
                        if size_elem is not None and size_elem.text:
                            try:
                                # Parse size from text like "123456789 bytes"
                                size_text = size_elem.text.strip()
                                if 'bytes' in size_text:
                                    file_info['size'] = int(size_text.replace('bytes', '').strip())
                            except:
                                pass
                        
                        files.append(file_info)
                
                return files
            except Exception as e:
                if retry < self.max_retries - 1:
                    logger.warning(f"Retry {retry+1}/{self.max_retries} after error: {e}")
                    time.sleep(2 ** retry)
                    continue
                else:
                    logger.error(f"Failed to get files list: {e}")
                    return []
            
    def download_file(self, resource_name: str, sub_resource: str, 
                     file_name: str, output_path: Optional[Path] = None) -> bool:
        """
        Download a specific file
        
        Args:
            resource_name: Main resource name
            sub_resource: Sub-resource/folder name
            file_name: Name of the file to download
            output_path: Custom output path (optional)
        """
        self._rate_limit()
        
        url = f"{self.base_url}/download/{resource_name}/{sub_resource}/{file_name}"
        
        if not output_path:
            output_path = self.output_dir / resource_name / sub_resource / file_name
            
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            response = self.session.get(url, stream=True)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            
            with open(output_path, 'wb') as f:
                downloaded = 0
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        
                        if total_size > 0:
                            progress = (downloaded / total_size) * 100
                            if downloaded % (1024 * 1024 * 10) == 0:  # Log every 10MB
                                logger.info(f"Downloading {file_name}: {progress:.1f}%")
                                
            logger.info(f"✅ Downloaded: {file_name} ({downloaded / (1024*1024):.1f} MB)")
            return True
            
        except Exception as e:
            logger.error(f"Failed to download {file_name}: {e}")
            return False
            
    def bulk_download_dataset(self, resource_name: str, 
                            target_size_gb: float = 1.0,
                            file_filter: Optional[str] = None) -> Dict:
        """
        Download entire dataset up to target size
        
        Args:
            resource_name: Resource to download
            target_size_gb: Target download size in GB
            file_filter: Optional filter for file extensions
        """
        target_bytes = target_size_gb * 1024 * 1024 * 1024
        downloaded_bytes = 0
        downloaded_files = []
        failed_files = []
        
        logger.info(f"🚀 Starting bulk download of {resource_name} (target: {target_size_gb} GB)")
        
        # Get all sub-resources
        page = 1
        while downloaded_bytes < target_bytes:
            sub_resources = self.get_resource_list(resource_name, page=page)
            
            if not sub_resources:
                break
                
            for sub_resource in sub_resources:
                sub_name = sub_resource.get('name')
                if not sub_name:
                    continue
                    
                # Get files in this sub-resource
                files = self.get_files_list(resource_name, sub_name)
                
                for file_info in files:
                    file_name = file_info.get('name')
                    file_size = file_info.get('size', 0)
                    
                    if not file_name:
                        continue
                        
                    # Apply filter if specified
                    if file_filter and not file_name.endswith(file_filter):
                        continue
                        
                    # Check if we've reached target
                    if downloaded_bytes >= target_bytes:
                        logger.info(f"📊 Reached target size: {downloaded_bytes / (1024*1024*1024):.2f} GB")
                        break
                        
                    # Download file
                    if self.download_file(resource_name, sub_name, file_name):
                        downloaded_files.append(file_name)
                        downloaded_bytes += file_size
                    else:
                        failed_files.append(file_name)
                        
                if downloaded_bytes >= target_bytes:
                    break
                    
            page += 1
            
        # Summary
        return {
            'downloaded_files': downloaded_files,
            'failed_files': failed_files,
            'total_size_gb': downloaded_bytes / (1024*1024*1024),
            'files_count': len(downloaded_files)
        }

def download_occitanie_datasets():
    """Download key datasets for Occitanie region"""
    
    downloader = IGNBulkDownloader(output_dir="IGN_BULK")
    
    # Priority datasets for offline mapping (reduced for testing)
    datasets = [
        {
            'name': 'SCAN25',  # Topographic maps 1:25000
            'zone': 'D031',  # Haute-Garonne
            'target_gb': 0.5  # 500MB for testing
        },
        {
            'name': 'BDORTHO',  # Orthophotos
            'zone': 'D031',
            'target_gb': 0.5
        }
    ]
    
    total_downloaded = 0
    
    for dataset in datasets:
        logger.info(f"\n{'='*60}")
        logger.info(f"Downloading {dataset['name']} for {dataset['zone']}")
        logger.info(f"{'='*60}")
        
        # Get capabilities first
        capabilities = downloader.get_capabilities(
            zone=dataset['zone'],
            limit=50
        )
        
        if capabilities:
            logger.info(f"Found {len(capabilities.get('resources', []))} resources")
            
        # Download dataset
        result = downloader.bulk_download_dataset(
            resource_name=dataset['name'],
            target_size_gb=dataset['target_gb']
        )
        
        total_downloaded += result['total_size_gb']
        
        logger.info(f"✅ Downloaded {result['files_count']} files")
        logger.info(f"📊 Size: {result['total_size_gb']:.2f} GB")
        
        if result['failed_files']:
            logger.warning(f"⚠️ Failed: {len(result['failed_files'])} files")
            
    logger.info(f"\n{'='*60}")
    logger.info(f"🎯 TOTAL DOWNLOADED: {total_downloaded:.2f} GB")
    logger.info(f"{'='*60}")

if __name__ == "__main__":
    # Test capabilities
    downloader = IGNBulkDownloader()
    
    print("🔍 Testing IGN Téléchargement API...")
    capabilities = downloader.get_capabilities(zone="D031", limit=5)
    
    if capabilities:
        print(f"✅ API is accessible")
        print(f"📊 Found {len(capabilities.get('resources', []))} resources")
        
        # Show first few resources
        for resource in capabilities.get('resources', [])[:3]:
            print(f"  - {resource.get('name')}: {resource.get('description', 'No description')}")
    else:
        print("❌ Could not access API")
        
    # Start bulk download for Occitanie
    print("\n🚀 Starting bulk download for Occitanie datasets...")
    download_occitanie_datasets()