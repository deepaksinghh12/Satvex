"""
Script to add Indian Earth observation satellites to the database
Run this with: python manage.py shell < add_indian_satellites.py
"""

from satTrack.models import Satellite, Sensor
from datetime import datetime

# Create sensors first
sensors_data = [
    {
        'name': 'PAN',
        'resolution_type': 'Panchromatic',
        'resolution_value': 0.25,
        'swath': 10,
        'positive_tilting': 26,
        'negative_tilting': -26
    },
    {
        'name': 'MX',
        'resolution_type': 'Multispectral',
        'resolution_value': 1.0,
        'swath': 10,
        'positive_tilting': 26,
        'negative_tilting': -26
    },
    {
        'name': 'LISS-4',
        'resolution_type': 'Multispectral',
        'resolution_value': 5.8,
        'swath': 70,
        'positive_tilting': 26,
        'negative_tilting': -26
    },
    {
        'name': 'LISS-3',
        'resolution_type': 'Multispectral',
        'resolution_value': 23.5,
        'swath': 141,
        'positive_tilting': 26,
        'negative_tilting': -26
    },
    {
        'name': 'AWiFS',
        'resolution_type': 'Wide Field',
        'resolution_value': 56,
        'swath': 740,
        'positive_tilting': 0,
        'negative_tilting': 0
    }
]

print("Creating sensors...")
sensors = {}
for sensor_data in sensors_data:
    sensor, created = Sensor.objects.get_or_create(
        name=sensor_data['name'],
        defaults=sensor_data
    )
    sensors[sensor_data['name']] = sensor
    print(f"{'Created' if created else 'Found'} sensor: {sensor.name}")

# Indian Earth Observation Satellites with NORAD IDs
satellites_data = [
    {
        'norad_id': 41948,
        'name': 'CARTOSAT-3',
        'satellite_type': 'Earth Observation',
        'description': 'High-resolution earth observation satellite with panchromatic and multispectral cameras. Provides sub-meter resolution imagery.',
        'launch_date': datetime(2019, 11, 27),
        'launch_site': 'SDSC SHAR, Sriharikota',
        'swath': 10,
        'status': 'active',
        'orbit': 'Sun-Synchronous',
        'orbital_period': 97.4,
        'orbit_revisit': 16,
        'orbit_distance': 2800,
        'orbits_per_day': 14,
        'inclination': 97.5,
        'perigee': 505,
        'apogee': 520,
        'sensor_names': ['PAN', 'MX']
    },
    {
        'norad_id': 42063,
        'name': 'CARTOSAT-2F',
        'satellite_type': 'Earth Observation',
        'description': 'Advanced remote sensing satellite providing high-resolution images for cartographic applications.',
        'launch_date': datetime(2017, 1, 12),
        'launch_site': 'SDSC SHAR, Sriharikota',
        'swath': 10,
        'status': 'active',
        'orbit': 'Sun-Synchronous',
        'orbital_period': 97.3,
        'orbit_revisit': 4,
        'orbit_distance': 2800,
        'orbits_per_day': 14,
        'inclination': 97.5,
        'perigee': 505,
        'apogee': 520,
        'sensor_names': ['PAN']
    },
    {
        'norad_id': 39419,
        'name': 'RESOURCESAT-2',
        'satellite_type': 'Earth Observation',
        'description': 'Continuity mission for earth observation with LISS-3, LISS-4 and AWiFS cameras for resource management.',
        'launch_date': datetime(2011, 4, 20),
        'launch_site': 'SDSC SHAR, Sriharikota',
        'swath': 740,
        'status': 'active',
        'orbit': 'Sun-Synchronous',
        'orbital_period': 101.35,
        'orbit_revisit': 5,
        'orbit_distance': 2900,
        'orbits_per_day': 14,
        'inclination': 98.7,
        'perigee': 817,
        'apogee': 827,
        'sensor_names': ['LISS-3', 'LISS-4', 'AWiFS']
    },
    {
        'norad_id': 42939,
        'name': 'RESOURCESAT-2A',
        'satellite_type': 'Earth Observation',
        'description': 'Follow-on mission to RESOURCESAT-2 for natural resource management and monitoring.',
        'launch_date': datetime(2016, 12, 7),
        'launch_site': 'SDSC SHAR, Sriharikota',
        'swath': 740,
        'status': 'active',
        'orbit': 'Sun-Synchronous',
        'orbital_period': 101.35,
        'orbit_revisit': 5,
        'orbit_distance': 2900,
        'orbits_per_day': 14,
        'inclination': 98.7,
        'perigee': 817,
        'apogee': 827,
        'sensor_names': ['LISS-3', 'LISS-4', 'AWiFS']
    },
    {
        'norad_id': 37387,
        'name': 'RISAT-2',
        'satellite_type': 'Radar Imaging',
        'description': 'All-weather Synthetic Aperture Radar (SAR) satellite for surveillance and disaster management.',
        'launch_date': datetime(2009, 4, 20),
        'launch_site': 'SDSC SHAR, Sriharikota',
        'swath': 20,
        'status': 'active',
        'orbit': 'Sun-Synchronous',
        'orbital_period': 94.6,
        'orbit_revisit': 14,
        'orbit_distance': 2700,
        'orbits_per_day': 15,
        'inclination': 97.5,
        'perigee': 550,
        'apogee': 555,
        'sensor_names': []
    }
]

print("\nAdding Indian satellites...")
for sat_data in satellites_data:
    sensor_names = sat_data.pop('sensor_names')
    
    # Check if satellite already exists
    if Satellite.objects.filter(norad_id=sat_data['norad_id']).exists():
        print(f"Satellite {sat_data['name']} already exists, skipping...")
        continue
    
    try:
        # Note: save() will automatically fetch TLE from N2YO API
        # This might fail if API is unavailable or rate-limited
        satellite = Satellite(**sat_data)
        # Temporarily skip the automatic TLE fetch by commenting the save override
        # We'll set a dummy TLE for now
        satellite.tle_now = "1 00000U 00000    00001.00000000  .00000000  00000-0  00000-0 0    00\n2 00000  00.0000 000.0000 0000000  00.0000 000.0000 00.00000000    00"
        satellite.last_tle_update = datetime.now()
        
        # Save without calling the custom save method
        super(Satellite, satellite).save()
        
        # Add sensors
        for sensor_name in sensor_names:
            if sensor_name in sensors:
                satellite.sensors.add(sensors[sensor_name])
        
        print(f"✓ Added {satellite.name} (NORAD: {satellite.norad_id})")
    except Exception as e:
        print(f"✗ Error adding {sat_data['name']}: {str(e)}")

print("\n=== Summary ===")
print(f"Total satellites in database: {Satellite.objects.count()}")
print(f"Total sensors in database: {Sensor.objects.count()}")

print("\n=== Available Satellites ===")
for sat in Satellite.objects.all():
    print(f"  - {sat.name} (NORAD ID: {sat.norad_id})")
