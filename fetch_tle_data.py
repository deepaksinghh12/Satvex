"""
Script to fetch real TLE data for satellites from N2YO API
Run this with: python fetch_tle_data.py
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from satTrack.models import Satellite
import requests

api_key = 'M8PZCZ-5ELM7M-DE5LRK-531A'
API_URL = 'https://api.n2yo.com/rest/v1/satellite/'

def fetch_tle(norad_id):
    """Fetch TLE data from N2YO API"""
    try:
        params = {'apiKey': api_key}
        response = requests.get(f'{API_URL}tle/{norad_id}', params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        return data.get('tle')
    except Exception as e:
        print(f"Error fetching TLE for NORAD ID {norad_id}: {str(e)}")
        return None

print("Fetching TLE data for satellites...")
print("=" * 60)

satellites = Satellite.objects.all()

for sat in satellites:
    print(f"\nProcessing {sat.name} (NORAD ID: {sat.norad_id})...")
    
    tle_data = fetch_tle(sat.norad_id)
    
    if tle_data:
        # Update the satellite's TLE data directly without triggering save_new_tle
        sat.tle_now = tle_data
        from datetime import datetime
        sat.last_tle_update = datetime.now()
        
        # Use super().save() to avoid calling custom save method
        super(Satellite, sat).save(update_fields=['tle_now', 'last_tle_update'])
        
        print(f"✓ Successfully updated TLE for {sat.name}")
        print(f"  TLE Preview: {tle_data[:50]}...")
    else:
        print(f"✗ Failed to fetch TLE for {sat.name}")

print("\n" + "=" * 60)
print("TLE fetch complete!")
print("\nSummary:")
for sat in Satellite.objects.all():
    has_valid_tle = sat.tle_now and len(sat.tle_now) > 100
    status = "✓" if has_valid_tle else "✗"
    print(f"  {status} {sat.name}: {'Valid TLE' if has_valid_tle else 'Invalid/Missing TLE'}")
