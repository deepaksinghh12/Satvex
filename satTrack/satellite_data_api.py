"""
Satellite Data API Integration Module
Provides access to Indian satellite imagery, DEM, and ortho images from various sources
"""

import requests
from typing import Dict, Optional, Tuple, List
import json
from datetime import datetime
import base64
from io import BytesIO
from PIL import Image
import numpy as np


class BhuvanAPI:
    """
    API client for Bhuvan (ISRO/NRSC) data services
    Provides access to satellite imagery, DEM, and thematic data
    """
    
    # Base URLs for different services
    WMS_BASE_URL = "https://bhuvan-vec1.nrsc.gov.in/bhuvan/wms"
    WMS_ALTERNATE_URL = "https://bhuvan-app1.nrsc.gov.in/bhuvan/wms"
    THEMATIC_WMS_URL = "https://bhuvan-vec2.nrsc.gov.in/bhuvan/gwc/service/wms"
    
    # Available layers (verified working layers)
    LAYERS = {
        'india3': 'India satellite composite imagery (WORKING)',
        'resourcesat2': 'Resourcesat-2 imagery (may not have coverage)',
        'cartosat1': 'Cartosat-1 high resolution (may not have coverage)',
    }
    
    # Recommended default layer
    DEFAULT_LAYER = 'india3'
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Bhuvan API client
        
        Args:
            api_key: Optional API key for authenticated requests
        """
        self.api_key = api_key
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'SatelliteTrack-Application'
        })
    
    def get_capabilities(self) -> Dict:
        """
        Get WMS capabilities - lists all available layers
        """
        params = {
            'SERVICE': 'WMS',
            'VERSION': '1.1.1',
            'REQUEST': 'GetCapabilities'
        }
        
        try:
            response = self.session.get(self.WMS_BASE_URL, params=params, timeout=30)
            return {
                'success': True,
                'data': response.text,
                'status_code': response.status_code
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_satellite_imagery(self, 
                            bbox: Tuple[float, float, float, float],
                            layer: str = 'india3',
                            width: int = 512, 
                            height: int = 512,
                            format: str = 'image/png',
                            srs: str = 'EPSG:4326') -> Optional[bytes]:
        """
        Get satellite imagery using WMS (Web Map Service)
        
        Args:
            bbox: Bounding box as (minx, miny, maxx, maxy) in WGS84
            layer: Layer name (e.g., 'india3', 'resourcesat2', 'cartosat1')
            width: Image width in pixels
            height: Image height in pixels
            format: Output format (image/png, image/jpeg, image/tiff)
            srs: Spatial Reference System (default: EPSG:4326 for WGS84)
        
        Returns:
            Image bytes or None if request fails
        """
        params = {
            'SERVICE': 'WMS',
            'VERSION': '1.1.1',
            'REQUEST': 'GetMap',
            'LAYERS': layer,
            'BBOX': ','.join(map(str, bbox)),
            'WIDTH': str(width),
            'HEIGHT': str(height),
            'SRS': srs,
            'FORMAT': format,
            'TRANSPARENT': 'TRUE'
        }
        
        try:
            response = self.session.get(self.WMS_BASE_URL, params=params, timeout=10)
            content_type = response.headers.get('Content-Type', '')
            
            # Check if we got an image
            if response.status_code == 200 and 'image' in content_type:
                return response.content
            
            # Check for XML error response
            if 'xml' in content_type:
                print(f"WMS Error Response: {response.text[:500]}")
            else:
                print(f"Error: Status {response.status_code}, Content-Type: {content_type}")
                print(f"Response preview: {response.text[:200]}")
            return None
        except Exception as e:
            print(f"Exception fetching imagery: {e}")
            return None
    
    def get_dem_data(self, 
                    lat: float, 
                    lon: float, 
                    radius: float = 0.1,
                    resolution: int = 512) -> Optional[Dict]:
        """
        Get Digital Elevation Model (DEM) data for a location
        
        Args:
            lat: Latitude in degrees
            lon: Longitude in degrees
            radius: Radius around the point in degrees (default: 0.1° ≈ 11km)
            resolution: Image resolution in pixels
        
        Returns:
            Dictionary with DEM image data and metadata
        """
        bbox = (
            lon - radius,
            lat - radius,
            lon + radius,
            lat + radius
        )
        
        # Note: DEM layer may not be available, using india3 for now
        image_data = self.get_satellite_imagery(
            bbox=bbox,
            layer='india3',  # DEM layer doesn't exist, using composite
            width=resolution,
            height=resolution
        )
        
        if image_data:
            return {
                'success': True,
                'image_data': base64.b64encode(image_data).decode('utf-8'),
                'bbox': bbox,
                'center': {'lat': lat, 'lon': lon},
                'radius_deg': radius,
                'resolution': resolution
            }
        return None
    
    def get_ortho_image(self,
                       bbox: Tuple[float, float, float, float],
                       satellite: str = 'resourcesat2',
                       resolution: int = 1024) -> Optional[Dict]:
        """
        Get orthorectified satellite imagery
        
        Args:
            bbox: Bounding box as (minx, miny, maxx, maxy)
            satellite: Satellite source ('resourcesat2', 'cartosat1')
            resolution: Output resolution in pixels
        
        Returns:
            Dictionary with image data and metadata
        """
        image_data = self.get_satellite_imagery(
            bbox=bbox,
            layer=satellite,
            width=resolution,
            height=resolution
        )
        
        if image_data:
            return {
                'success': True,
                'image_data': base64.b64encode(image_data).decode('utf-8'),
                'bbox': bbox,
                'satellite': satellite,
                'resolution': resolution,
                'format': 'png'
            }
        return None
    
    def get_feature_info(self,
                        lat: float,
                        lon: float,
                        layer: str = 'india3') -> Optional[Dict]:
        """
        Get feature information at a specific point
        
        Args:
            lat: Latitude
            lon: Longitude
            layer: Layer to query
        
        Returns:
            Feature information as dictionary
        """
        bbox = (lon - 0.001, lat - 0.001, lon + 0.001, lat + 0.001)
        
        params = {
            'SERVICE': 'WMS',
            'VERSION': '1.1.1',
            'REQUEST': 'GetFeatureInfo',
            'LAYERS': layer,
            'QUERY_LAYERS': layer,
            'BBOX': ','.join(map(str, bbox)),
            'WIDTH': '101',
            'HEIGHT': '101',
            'X': '50',
            'Y': '50',
            'SRS': 'EPSG:4326',
            'INFO_FORMAT': 'application/json'
        }
        
        try:
            response = self.session.get(self.WMS_BASE_URL, params=params, timeout=30)
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            print(f"Error getting feature info: {e}")
            return None


class MOSDACApi:
    """
    API client for MOSDAC (Meteorological & Oceanographic Satellite Data Archival Centre)
    Provides access to Indian meteorological satellite data
    """
    
    BASE_URL = "https://www.mosdac.gov.in"
    DATA_URL = f"{BASE_URL}/data"
    
    # Supported satellites
    SATELLITES = {
        'INSAT3D': 'INSAT-3D weather satellite',
        'INSAT3DR': 'INSAT-3DR weather satellite',
        'SCATSAT1': 'SCATSAT-1 ocean scatterometer',
        'OCEANSAT2': 'Oceansat-2',
        'OCEANSAT3': 'Oceansat-3',
        'MEGHATROPIQUES': 'Megha-Tropiques'
    }
    
    def __init__(self, username: Optional[str] = None, password: Optional[str] = None):
        """
        Initialize MOSDAC API client
        
        Args:
            username: MOSDAC portal username
            password: MOSDAC portal password
        """
        self.username = username
        self.password = password
        self.session = requests.Session()
        self.authenticated = False
    
    def authenticate(self) -> bool:
        """
        Authenticate with MOSDAC portal
        Note: Requires registration at https://www.mosdac.gov.in/
        """
        if not self.username or not self.password:
            return False
        
        # Authentication implementation would go here
        # This requires actual MOSDAC API documentation
        return False
    
    def get_satellite_data(self,
                          satellite: str,
                          start_date: str,
                          end_date: str,
                          product_type: Optional[str] = None) -> Optional[Dict]:
        """
        Get satellite data from MOSDAC
        
        Args:
            satellite: Satellite name (e.g., 'INSAT3D')
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            product_type: Type of product to fetch
        
        Returns:
            Dictionary with data URLs and metadata
        """
        # Placeholder - actual implementation requires MOSDAC API credentials
        return {
            'success': False,
            'message': 'MOSDAC API requires authentication. Register at https://www.mosdac.gov.in/',
            'satellite': satellite,
            'dates': {'start': start_date, 'end': end_date}
        }


class VEDASApi:
    """
    API client for VEDAS (Visualisation of Earth observation Data and Archival System)
    Provides access to Indian Earth Observation satellite data
    """
    
    BASE_URL = "https://vedas.sac.gov.in"
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize VEDAS API client
        
        Args:
            api_key: VEDAS API key (requires registration)
        """
        self.api_key = api_key
        self.session = requests.Session()
    
    def search_data(self,
                   satellite: str,
                   start_date: str,
                   end_date: str,
                   bbox: Optional[Tuple[float, float, float, float]] = None) -> Dict:
        """
        Search for available satellite data
        
        Args:
            satellite: Satellite name
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            bbox: Optional bounding box filter
        
        Returns:
            Search results with data availability
        """
        return {
            'success': False,
            'message': 'VEDAS API requires registration. Visit https://vedas.sac.gov.in/',
            'satellite': satellite,
            'dates': {'start': start_date, 'end': end_date}
        }


class SatelliteDataManager:
    """
    Unified manager for all satellite data APIs
    Provides a single interface to access data from multiple sources
    """
    
    def __init__(self):
        self.bhuvan = BhuvanAPI()
        self.mosdac = MOSDACApi()
        self.vedas = VEDASApi()
    
    def get_imagery_for_satellite_position(self,
                                          lat: float,
                                          lon: float,
                                          radius_km: float = 50,
                                          data_type: str = 'optical') -> Dict:
        """
        Get satellite imagery for a specific location
        
        Args:
            lat: Latitude
            lon: Longitude
            radius_km: Radius around the point in kilometers
            data_type: Type of data ('optical', 'dem', 'thermal')
        
        Returns:
            Dictionary with imagery data
        """
        # Convert km to degrees (approximate)
        radius_deg = radius_km / 111.0
        
        bbox = (
            lon - radius_deg,
            lat - radius_deg,
            lon + radius_deg,
            lat + radius_deg
        )
        
        if data_type == 'dem':
            return self.bhuvan.get_dem_data(lat, lon, radius_deg)
        elif data_type == 'optical':
            result = self.bhuvan.get_ortho_image(bbox, satellite='resourcesat2')
            return result
        else:
            return {'success': False, 'error': f'Unknown data type: {data_type}'}
    
    def get_available_layers(self) -> Dict:
        """Get list of all available data layers"""
        return {
            'bhuvan_layers': BhuvanAPI.LAYERS,
            'mosdac_satellites': MOSDACApi.SATELLITES,
            'description': 'Available satellite data layers and sources'
        }
    
    def download_tile(self,
                     bbox: Tuple[float, float, float, float],
                     output_path: str,
                     layer: str = 'resourcesat2') -> bool:
        """
        Download a tile and save to file
        
        Args:
            bbox: Bounding box
            output_path: Path to save the image
            layer: Layer to download
        
        Returns:
            True if successful
        """
        image_data = self.bhuvan.get_satellite_imagery(bbox, layer=layer, width=2048, height=2048)
        
        if image_data:
            try:
                with open(output_path, 'wb') as f:
                    f.write(image_data)
                return True
            except Exception as e:
                print(f"Error saving file: {e}")
                return False
        return False
