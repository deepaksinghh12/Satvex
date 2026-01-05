#!/usr/bin/env python
"""
Fetch live TLE data from Celestrak API and update datac.csv
Keeps current and previous TLE for comparison purposes
"""
import django
import os
import sys
import csv
import requests
from datetime import datetime
import time

# Setup Django
sys.path.append('d:/satallite-track')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from satTrack.models import Satellite, TLE

print('🛰️  Live TLE Data Fetcher & datac.csv Updater')
print('='*70)

# Celestrak API endpoints
CELESTRAK_GP_URL = "https://celestrak.org/NORAD/elements/gp.php"
CELESTRAK_GP_HISTORY_URL = "https://celestrak.org/NORAD/elements/gp-history.php"

def fetch_tle_from_celestrak(norad_id):
    """Fetch current TLE from Celestrak API"""
    try:
        params = {
            'CATNR': norad_id,
            'FORMAT': 'TLE'
        }
        response = requests.get(CELESTRAK_GP_URL, params=params, timeout=10)
        
        if response.status_code == 200 and response.text.strip():
            lines = response.text.strip().split('\n')
            if len(lines) >= 2:
                return {
                    'line1': lines[-2].strip(),
                    'line2': lines[-1].strip(),
                    'success': True
                }
        return {'success': False, 'error': 'No TLE data found'}
    except Exception as e:
        return {'success': False, 'error': str(e)}

def fetch_tle_history_from_celestrak(norad_id, limit=2):
    """Fetch TLE history from Celestrak (last 2 records)"""
    try:
        params = {
            'CATNR': norad_id,
            'FORMAT': 'TLE'
        }
        response = requests.get(CELESTRAK_GP_HISTORY_URL, params=params, timeout=15)
        
        if response.status_code == 200 and response.text.strip():
            lines = response.text.strip().split('\n')
            
            # Parse TLE records (every 2 lines is one TLE)
            tle_records = []
            for i in range(0, len(lines), 2):
                if i + 1 < len(lines):
                    line1 = lines[i].strip()
                    line2 = lines[i + 1].strip()
                    
                    if line1.startswith('1 ') and line2.startswith('2 '):
                        # Extract epoch from line 1
                        epoch_year = int(line1[18:20])
                        epoch_day = float(line1[20:32])
                        
                        # Convert to full year
                        if epoch_year < 57:
                            epoch_year += 2000
                        else:
                            epoch_year += 1900
                        
                        tle_records.append({
                            'line1': line1,
                            'line2': line2,
                            'epoch_year': epoch_year,
                            'epoch_day': epoch_day
                        })
            
            # Return last 2 records (most recent)
            return {'success': True, 'records': tle_records[-limit:] if len(tle_records) >= limit else tle_records}
        
        return {'success': False, 'error': 'No history data found'}
    except Exception as e:
        return {'success': False, 'error': str(e)}

def parse_epoch_from_tle(line1):
    """Parse epoch date from TLE line 1"""
    try:
        epoch_year = int(line1[18:20])
        epoch_day = float(line1[20:32])
        
        # Convert to full year
        if epoch_year < 57:
            epoch_year += 2000
        else:
            epoch_year += 1900
        
        # Convert day of year to datetime
        from datetime import datetime, timedelta
        epoch_date = datetime(epoch_year, 1, 1) + timedelta(days=epoch_day - 1)
        
        return epoch_date.strftime('%Y-%m-%dT%H:%M:%S.%f')
    except:
        return None

# Fetch all satellites from database
satellites = Satellite.objects.all().order_by('name')
total_satellites = satellites.count()

print(f'\n📡 Found {total_satellites} satellites in database')
print(f'⏰ Started at: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
print('\nFetching live TLE data from Celestrak...\n')

csv_data = []
success_count = 0
failed_satellites = []

for idx, satellite in enumerate(satellites, 1):
    print(f'[{idx}/{total_satellites}] {satellite.name} ({satellite.norad_id})...', end=' ')
    
    # Try to fetch TLE history first (gives us current + previous)
    history_result = fetch_tle_history_from_celestrak(satellite.norad_id)
    
    if history_result['success'] and len(history_result['records']) >= 2:
        # We have at least 2 TLE records
        records = history_result['records'][-2:]  # Get last 2 (previous and current)
        
        for record in records:
            epoch = parse_epoch_from_tle(record['line1'])
            if epoch:
                csv_data.append({
                    'OBJECT_NAME': satellite.name,
                    'OBJECT_ID': '',
                    'EPOCH': epoch,
                    'MEAN_MOTION': 0.0,
                    'ECCENTRICITY': 0.0,
                    'INCLINATION': satellite.inclination or 0.0,
                    'RA_OF_ASC_NODE': 0.0,
                    'ARG_OF_PERICENTER': 0.0,
                    'MEAN_ANOMALY': 0.0,
                    'EPHEMERIS_TYPE': 0,
                    'CLASSIFICATION_TYPE': 'U',
                    'NORAD_CAT_ID': satellite.norad_id,
                    'ELEMENT_SET_NO': 0,
                    'REV_AT_EPOCH': 0,
                    'BSTAR': 0.0,
                    'MEAN_MOTION_DOT': 0.0,
                    'MEAN_MOTION_DDOT': 0.0,
                    'TLE_LINE1': record['line1'],
                    'TLE_LINE2': record['line2']
                })
        
        print(f'✅ Got {len(records)} TLE records')
        success_count += 1
        
    else:
        # Fallback to current TLE only
        current_tle = fetch_tle_from_celestrak(satellite.norad_id)
        
        if current_tle['success']:
            epoch = parse_epoch_from_tle(current_tle['line1'])
            if epoch:
                csv_data.append({
                    'OBJECT_NAME': satellite.name,
                    'OBJECT_ID': '',
                    'EPOCH': epoch,
                    'MEAN_MOTION': 0.0,
                    'ECCENTRICITY': 0.0,
                    'INCLINATION': satellite.inclination or 0.0,
                    'RA_OF_ASC_NODE': 0.0,
                    'ARG_OF_PERICENTER': 0.0,
                    'MEAN_ANOMALY': 0.0,
                    'EPHEMERIS_TYPE': 0,
                    'CLASSIFICATION_TYPE': 'U',
                    'NORAD_CAT_ID': satellite.norad_id,
                    'ELEMENT_SET_NO': 0,
                    'REV_AT_EPOCH': 0,
                    'BSTAR': 0.0,
                    'MEAN_MOTION_DOT': 0.0,
                    'MEAN_MOTION_DDOT': 0.0,
                    'TLE_LINE1': current_tle['line1'],
                    'TLE_LINE2': current_tle['line2']
                })
                print('✅ Got current TLE')
                success_count += 1
        else:
            print(f'❌ Failed: {current_tle.get("error", "Unknown error")}')
            failed_satellites.append(satellite.name)
    
    # Rate limiting - be nice to Celestrak API
    if idx < total_satellites:
        time.sleep(0.5)  # 500ms delay between requests

# Write to CSV file
if csv_data:
    print(f'\n💾 Writing {len(csv_data)} TLE records to datac.csv...')
    
    fieldnames = [
        'OBJECT_NAME', 'OBJECT_ID', 'EPOCH', 'MEAN_MOTION', 'ECCENTRICITY',
        'INCLINATION', 'RA_OF_ASC_NODE', 'ARG_OF_PERICENTER', 'MEAN_ANOMALY',
        'EPHEMERIS_TYPE', 'CLASSIFICATION_TYPE', 'NORAD_CAT_ID', 'ELEMENT_SET_NO',
        'REV_AT_EPOCH', 'BSTAR', 'MEAN_MOTION_DOT', 'MEAN_MOTION_DDOT',
        'TLE_LINE1', 'TLE_LINE2'
    ]
    
    with open('datac.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(csv_data)
    
    print('✅ datac.csv updated successfully!')

# Summary
print('\n' + '='*70)
print('📊 SUMMARY')
print('='*70)
print(f'Total Satellites Processed: {total_satellites}')
print(f'✅ Successful: {success_count}')
print(f'❌ Failed: {len(failed_satellites)}')
print(f'📝 Total TLE records in CSV: {len(csv_data)}')
print(f'⏰ Completed at: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')

if failed_satellites:
    print(f'\n⚠️  Failed satellites:')
    for sat in failed_satellites[:10]:  # Show first 10
        print(f'   - {sat}')
    if len(failed_satellites) > 10:
        print(f'   ... and {len(failed_satellites) - 10} more')

print(f'\n✨ You can now re-import this data into database using:')
print(f'   python import_tle_history.py')
