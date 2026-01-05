# Satellite Data API Integration - Usage Guide

## Overview
This integration provides access to Indian satellite data including DEM (Digital Elevation Model), orthoimages, and various thematic layers from Bhuvan (ISRO/NRSC) and other sources.

## Features Implemented

### 1. API Module (`satTrack/satellite_data_api.py`)
- **BhuvanAPI**: Access to ISRO's Bhuvan geoportal
- **MOSDACApi**: Meteorological satellite data (requires registration)
- **VEDASApi**: Earth observation data (requires registration)
- **SatelliteDataManager**: Unified interface for all APIs

### 2. New Django Views
- `satellite_imagery_view`: Main page for viewing satellite imagery
- `get_satellite_dem`: Fetch DEM data for satellite's current position
- `get_satellite_imagery`: Fetch optical imagery
- `get_location_imagery`: Fetch imagery for any location
- `bhuvan_capabilities`: Get available WMS layers

### 3. API Endpoints

```
GET /sat/<norad_id>/imagery              - Satellite imagery page
GET /api/sat/<norad_id>/dem              - Get DEM data (AJAX)
GET /api/sat/<norad_id>/imagery          - Get optical imagery (AJAX)
GET /api/location/imagery                - Get imagery for any location (AJAX)
GET /api/bhuvan/capabilities             - List available layers
```

## Usage Examples

### 1. View Satellite Imagery Page
Navigate to: `http://localhost:8000/sat/<norad_id>/imagery`

Example: `http://localhost:8000/sat/43013/imagery` (for Cartosat-3)

### 2. API Usage in Python

```python
from satTrack.satellite_data_api import SatelliteDataManager

# Initialize the manager
manager = SatelliteDataManager()

# Get DEM data for a location
dem_data = manager.get_imagery_for_satellite_position(
    lat=28.6139,  # New Delhi
    lon=77.2090,
    radius_km=50,
    data_type='dem'
)

# Get optical imagery
imagery = manager.get_imagery_for_satellite_position(
    lat=28.6139,
    lon=77.2090,
    radius_km=50,
    data_type='optical'
)
```

### 3. AJAX Requests from Frontend

```javascript
// Fetch DEM data
$.ajax({
    url: '/api/sat/43013/dem',
    method: 'GET',
    data: { radius: 50 },
    headers: {'X-Requested-With': 'XMLHttpRequest'},
    success: function(response) {
        if (response.success) {
            // Display image: data:image/png;base64,{response.dem_data.image_data}
            $('#image').attr('src', 'data:image/png;base64,' + response.dem_data.image_data);
        }
    }
});

// Fetch imagery for any location
$.ajax({
    url: '/api/location/imagery',
    method: 'GET',
    data: {
        lat: 28.6139,
        lon: 77.2090,
        radius: 50,
        type: 'optical',
        layer: 'resourcesat2'
    },
    headers: {'X-Requested-With': 'XMLHttpRequest'},
    success: function(response) {
        // Handle response
    }
});
```

## Available Data Sources

### 1. Bhuvan (ISRO/NRSC) - Free Access
**URL**: https://bhuvan.nrsc.gov.in/

**Available Layers**:
- `india3` - India satellite imagery composite
- `resourcesat2` - Resourcesat-2 imagery
- `cartosat1` - Cartosat-1 high resolution
- `dem` - Digital Elevation Model
- `lulc` - Land Use Land Cover
- `forest` - Forest cover
- `water` - Water bodies

**Registration**: Not required for WMS access
**Usage**: Integrated and ready to use

### 2. MOSDAC - Meteorological Data
**URL**: https://www.mosdac.gov.in/

**Available Satellites**:
- INSAT-3D, INSAT-3DR (Weather)
- SCATSAT-1 (Ocean scatterometer)
- Oceansat-2, Oceansat-3
- Megha-Tropiques

**Registration**: Required
**Status**: Placeholder implementation (needs credentials)

### 3. VEDAS - Earth Observation
**URL**: https://vedas.sac.gov.in/

**Registration**: Required
**Status**: Placeholder implementation (needs credentials)

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run migrations (if needed):
```bash
python manage.py migrate
```

3. Start the development server:
```bash
python manage.py runserver
```

## Data Types Explained

### Digital Elevation Model (DEM)
- **What**: Terrain elevation data
- **Use**: Understanding ground elevation, terrain analysis
- **Resolution**: Variable depending on source
- **Format**: Grayscale image (darker = lower, lighter = higher)

### Orthoimage
- **What**: Geometrically corrected satellite imagery
- **Use**: True-to-scale mapping, feature identification
- **Sources**: Resourcesat-2, Cartosat-1
- **Format**: RGB or multispectral image

### Thematic Layers
- **What**: Classified data (land use, forest, water)
- **Use**: Environmental monitoring, planning
- **Format**: Colored classification maps

## Limitations & Notes

1. **Bhuvan WMS**:
   - Free to use
   - No authentication required
   - Subject to service availability
   - Rate limits may apply

Note: This project includes a small WMS proxy at `/proxy/wms` which forwards WMS GetMap/GetCapabilites requests to Bhuvan. Using the proxy avoids CORS issues for client-side Leaflet WMS layers and allows you to add caching or authentication server-side if needed.

2. **MOSDAC & VEDAS**:
   - Require registration
   - Implementation is placeholder
   - Need to add authentication logic

3. **Image Resolution**:
   - Default: 512x512 or 1024x1024 pixels
   - Can be adjusted in API calls
   - Higher resolution = larger file size

4. **Coverage**:
   - Primarily India and surrounding regions
   - Some global coverage available

## Troubleshooting

### Issue: No image displayed
- Check if satellite has valid TLE data
- Verify Bhuvan service is online
- Check browser console for errors
- Try different layer/satellite combination

### Issue: Slow loading
- Reduce radius parameter
- Lower image resolution
- Check network connectivity

### Issue: "Could not fetch data"
- Bhuvan service may be down
- Check if coordinates are within India
- Try different layer

## Future Enhancements

1. **Add Authentication**:
   - Implement MOSDAC login
   - Implement VEDAS authentication

2. **Caching**:
   - Cache frequently accessed tiles
   - Implement local tile storage

3. **Advanced Features**:
   - Multi-temporal analysis
   - Image processing tools
   - Download functionality
   - Custom area selection

4. **Additional Sources**:
   - Integrate with other satellite data providers
   - Add ESA Copernicus data
   - Add NASA GIBS data

## API Reference

### BhuvanAPI Methods

```python
bhuvan = BhuvanAPI()

# Get capabilities
capabilities = bhuvan.get_capabilities()

# Get satellite imagery
image = bhuvan.get_satellite_imagery(
    bbox=(77, 28, 78, 29),
    layer='resourcesat2',
    width=1024,
    height=1024
)

# Get DEM data
dem = bhuvan.get_dem_data(lat=28.6, lon=77.2, radius=0.1)

# Get ortho image
ortho = bhuvan.get_ortho_image(
    bbox=(77, 28, 78, 29),
    satellite='cartosat1'
)

# Get feature info
info = bhuvan.get_feature_info(lat=28.6, lon=77.2, layer='india3')
```

### SatelliteDataManager Methods

```python
manager = SatelliteDataManager()

# Get imagery for satellite position
data = manager.get_imagery_for_satellite_position(
    lat=28.6,
    lon=77.2,
    radius_km=50,
    data_type='optical'  # or 'dem'
)

# Get available layers
layers = manager.get_available_layers()

# Download tile
success = manager.download_tile(
    bbox=(77, 28, 78, 29),
    output_path='tile.png',
    layer='resourcesat2'
)
```

## Links & Resources

- **Bhuvan Portal**: https://bhuvan.nrsc.gov.in/
- **MOSDAC**: https://www.mosdac.gov.in/
- **VEDAS**: https://vedas.sac.gov.in/
- **ISRO**: https://www.isro.gov.in/
- **Bhuvan Open Data**: https://bhuvan-app3.nrsc.gov.in/data/download/index.php

## Support

For issues or questions:
1. Check the troubleshooting section
2. Verify Bhuvan service status
3. Review browser console for errors
4. Check Django logs for server-side errors
