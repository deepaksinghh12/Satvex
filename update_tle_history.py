#!/usr/bin/env python
"""Update TLE for selected satellites to create history"""
import django
import os
import sys

# Setup Django
sys.path.append('d:/satallite-track')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from satTrack.models import Satellite, TLE
import requests
from datetime import datetime

API_KEY = 'M8PZCZ-5ELM7M-DE5LRK-531A'

def fetch_and_save_tle(norad_id):
    """Fetch current TLE and save it"""
    try:
        satellite = Satellite.objects.get(norad_id=norad_id)
        
        # Fetch from N2YO
        url = f'https://api.n2yo.com/rest/v1/satellite/tle/{norad_id}&apiKey={API_KEY}'
        response = requests.get(url, timeout=10)
        data = response.json()
        
        if 'tle' not in data:
            print(f'  ⚠️ No TLE data for {satellite.name}')
            return False
        
        tle_text = data['tle']
        
        # Parse epoch from TLE
        tle_lines = tle_text.split('\r\n')
        if len(tle_lines) >= 2:
            tle_line1 = tle_lines[0]
            epoch_year = int(tle_line1[18:20])
            epoch_day = float(tle_line1[20:32])
            
            from datetime import timedelta
            year = 2000 + epoch_year if epoch_year < 57 else 1900 + epoch_year
            epoch_datetime = datetime(year, 1, 1) + timedelta(days=epoch_day - 1)
            
            # Save TLE
            tle_obj = TLE(
                satellite=satellite,
                tle=tle_text,
                epoch_date=epoch_datetime
            )
            tle_obj.save()
            
            # Update satellite current TLE
            satellite.tle_now = tle_text
            satellite.last_tle_update = datetime.now().date()
            satellite.save()
            
            print(f'  ✅ Updated {satellite.name} - Epoch: {epoch_datetime.strftime("%Y-%m-%d")}')
            return True
        
        return False
        
    except Satellite.DoesNotExist:
        print(f'  ❌ Satellite {norad_id} not found')
        return False
    except Exception as e:
        print(f'  ⚠️ Error: {e}')
        return False

# Main satellites to update
satellites_to_update = [
    44804,  # CARTOSAT-3
    65053,  # NISAR
    41948,  # RESOURCESAT-2A (CARTOSAT 2D)
    43111,  # CARTOSAT-2F
    37387,  # RESOURCESAT-2
]

print('🔄 Updating TLE for selected satellites...')
print('='*60)

for norad_id in satellites_to_update:
    print(f'\nFetching TLE for {norad_id}...')
    fetch_and_save_tle(norad_id)

print('\n✅ TLE update complete!')
print('\nChecking TLE history counts...')

for norad_id in satellites_to_update:
    try:
        sat = Satellite.objects.get(norad_id=norad_id)
        tle_count = TLE.objects.filter(satellite=sat).count()
        print(f'{sat.name}: {tle_count} TLE record(s)')
    except:
        pass
