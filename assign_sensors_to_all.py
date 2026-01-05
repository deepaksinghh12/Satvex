#!/usr/bin/env python
"""Assign sensors to all satellites based on their type"""
import django
import os
import sys

# Setup Django
sys.path.append('d:/satallite-track')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from satTrack.models import Satellite, Sensor

print('📡 Assigning Sensors to All Satellites')
print('='*60)

# Get or create sensors
sensors = {}
sensor_data = [
    {
        'name': 'PAN',
        'resolution_type': 'Panchromatic',
        'resolution_value': 0.25,
        'swath': 10.0,
        'positive_tilting': 30.0,
        'negative_tilting': -30.0
    },
    {
        'name': 'MX',
        'resolution_type': 'Multispectral',
        'resolution_value': 1.0,
        'swath': 10.0,
        'positive_tilting': 30.0,
        'negative_tilting': -30.0
    },
    {
        'name': 'LISS-4',
        'resolution_type': 'Multispectral',
        'resolution_value': 5.8,
        'swath': 70.0,
        'positive_tilting': 26.0,
        'negative_tilting': -26.0
    },
    {
        'name': 'LISS-3',
        'resolution_type': 'Multispectral',
        'resolution_value': 23.5,
        'swath': 141.0,
        'positive_tilting': 26.0,
        'negative_tilting': -26.0
    },
    {
        'name': 'AWiFS',
        'resolution_type': 'Wide Field',
        'resolution_value': 56.0,
        'swath': 740.0,
        'positive_tilting': 26.0,
        'negative_tilting': -26.0
    },
    {
        'name': 'SAR-C',
        'resolution_type': 'Synthetic Aperture Radar',
        'resolution_value': 1.0,
        'swath': 10.0,
        'positive_tilting': 35.0,
        'negative_tilting': -35.0
    },
    {
        'name': 'OPTICAL-HR',
        'resolution_type': 'High Resolution Optical',
        'resolution_value': 0.5,
        'swath': 15.0,
        'positive_tilting': 45.0,
        'negative_tilting': -45.0
    },
    {
        'name': 'OPTICAL-MR',
        'resolution_type': 'Medium Resolution Optical',
        'resolution_value': 5.0,
        'swath': 50.0,
        'positive_tilting': 30.0,
        'negative_tilting': -30.0
    },
]

# Create or get sensors
for data in sensor_data:
    sensor, created = Sensor.objects.get_or_create(
        name=data['name'],
        defaults=data
    )
    sensors[data['name']] = sensor
    if created:
        print(f'✅ Created sensor: {data["name"]}')
    else:
        print(f'ℹ️  Sensor exists: {data["name"]}')

print(f'\n📊 Total sensors available: {len(sensors)}')

# Assign sensors based on satellite names
print('\n🛰️  Assigning sensors to satellites...\n')

satellite_sensor_mapping = {
    'CARTOSAT': ['PAN', 'MX'],
    'RESOURCESAT': ['LISS-3', 'LISS-4', 'AWiFS'],
    'RISAT': ['SAR-C'],
    'EOS': ['OPTICAL-HR', 'OPTICAL-MR'],
    'IRS': ['LISS-3', 'LISS-4'],
    'NISAR': ['SAR-C'],
    'OCEANSAT': ['OPTICAL-MR'],
    'INSAT': ['OPTICAL-MR'],
    'GSAT': ['OPTICAL-MR'],
}

updated_count = 0
skipped_count = 0

all_satellites = Satellite.objects.all()

for satellite in all_satellites:
    assigned_sensors = []
    
    # Check satellite name against mapping
    for sat_prefix, sensor_names in satellite_sensor_mapping.items():
        if sat_prefix in satellite.name.upper():
            for sensor_name in sensor_names:
                if sensor_name in sensors:
                    assigned_sensors.append(sensors[sensor_name])
    
    # If no specific mapping found, assign default based on satellite type
    if not assigned_sensors:
        if 'RADAR' in satellite.satellite_type.upper():
            assigned_sensors = [sensors['SAR-C']]
        elif 'EARTH OBSERVATION' in satellite.satellite_type.upper():
            assigned_sensors = [sensors['OPTICAL-HR'], sensors['OPTICAL-MR']]
        else:
            # Default sensors for any other satellite
            assigned_sensors = [sensors['OPTICAL-MR']]
    
    # Assign sensors to satellite if it doesn't already have them
    if assigned_sensors:
        current_sensors = set(satellite.sensors.all())
        new_sensors = set(assigned_sensors)
        
        if current_sensors != new_sensors:
            satellite.sensors.set(assigned_sensors)
            sensor_names_str = ', '.join([s.name for s in assigned_sensors])
            print(f'✅ {satellite.name} ({satellite.norad_id}): Assigned {len(assigned_sensors)} sensor(s) - {sensor_names_str}')
            updated_count += 1
        else:
            skipped_count += 1
    else:
        skipped_count += 1

print(f'\n📊 Summary:')
print(f'   ✅ Updated: {updated_count} satellites')
print(f'   ⏭️  Skipped: {skipped_count} satellites (already have sensors)')

# Show final stats
from django.db.models import Count
sats_with_sensors = Satellite.objects.annotate(
    sensor_count=Count('sensors')
).filter(sensor_count__gt=0)

print(f'\n🎉 Total satellites with sensors now: {sats_with_sensors.count()}')
print(f'\nTop 10 satellites with most sensors:')
for sat in sats_with_sensors.order_by('-sensor_count')[:10]:
    print(f'   {sat.name} ({sat.norad_id}): {sat.sensor_count} sensors')
