"""
Script to add Aditya-L1 satellite to the database
Run this with: python add_aditya_l1.py
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from satTrack.models import Satellite, Sensor
from datetime import datetime
import requests

print("Adding Aditya-L1 to database...")
print("=" * 60)

# Aditya-L1 satellite data
aditya_data = {
    'norad_id': 57608,  # NORAD ID for Aditya-L1
    'name': 'ADITYA-L1',
    'satellite_type': 'Solar Observatory',
    'description': 'India\'s first solar mission to study the Sun. Positioned at L1 Lagrange point to continuously observe solar activities, corona, solar wind, and space weather.',
    'launch_date': datetime(2023, 9, 2),
    'launch_site': 'SDSC SHAR, Sriharikota',
    'swath': 0,  # Not applicable for solar observatory
    'status': 'active',
    'orbit': 'Halo Orbit (L1)',
    'orbital_period': 0,  # In halo orbit around L1 point
    'orbit_revisit': 0,  # Continuous observation
    'orbit_distance': 0,
    'orbits_per_day': 0,
    'inclination': 0,  # Not in Earth orbit
    'perigee': 0,
    'apogee': 0,
}

# Check if Aditya-L1 already exists
if Satellite.objects.filter(norad_id=57608).exists():
    print("Aditya-L1 already exists in database!")
    sat = Satellite.objects.get(norad_id=57608)
    print(f"Found: {sat.name} (NORAD ID: {sat.norad_id})")
else:
    # Create the satellite
    satellite = Satellite(**aditya_data)
    
    # Fetch real TLE data
    api_key = 'M8PZCZ-5ELM7M-DE5LRK-531A'
    API_URL = 'https://api.n2yo.com/rest/v1/satellite/'
    
    try:
        print(f"\nFetching TLE data for Aditya-L1 (NORAD ID: 57608)...")
        params = {'apiKey': api_key}
        response = requests.get(f'{API_URL}tle/57608', params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        tle_data = data.get('tle')
        
        if tle_data:
            satellite.tle_now = tle_data
            satellite.last_tle_update = datetime.now()
            print(f"✓ Successfully fetched TLE data")
            print(f"  TLE Preview: {tle_data[:50]}...")
        else:
            print("⚠ No TLE data available, using placeholder")
            satellite.tle_now = "1 00000U 00000    00001.00000000  .00000000  00000-0  00000-0 0    00\n2 00000  00.0000 000.0000 0000000  00.0000 000.0000 00.00000000    00"
            satellite.last_tle_update = datetime.now()
    except Exception as e:
        print(f"⚠ Error fetching TLE: {str(e)}")
        print("  Using placeholder TLE data")
        satellite.tle_now = "1 00000U 00000    00001.00000000  .00000000  00000-0  00000-0 0    00\n2 00000  00.0000 000.0000 0000000  00.0000 000.0000 00.00000000    00"
        satellite.last_tle_update = datetime.now()
    
    # Save using parent class save to avoid triggering custom save method
    super(Satellite, satellite).save()
    
    print(f"\n✓ Successfully added {satellite.name} to database!")
    print(f"  NORAD ID: {satellite.norad_id}")
    print(f"  Launch Date: {satellite.launch_date.strftime('%B %d, %Y')}")
    print(f"  Mission Type: {satellite.satellite_type}")

print("\n" + "=" * 60)
print("Database update complete!")
print(f"\nTotal satellites in database: {Satellite.objects.count()}")

print("\n=== All Available Satellites ===")
for sat in Satellite.objects.all().order_by('name'):
    print(f"  - {sat.name} (NORAD ID: {sat.norad_id})")
