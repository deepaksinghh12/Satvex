#!/usr/bin/env python
"""Fetch current satellite data and generate CSV in datac.csv format"""
import sqlite3
import csv
import requests
from datetime import datetime

API_KEY = 'M8PZCZ-5ELM7M-DE5LRK-531A'

def fetch_satellite_data(norad_id):
    """Fetch detailed satellite data from Space-Track or N2YO"""
    try:
        # Fetch TLE from N2YO
        url = f'https://api.n2yo.com/rest/v1/satellite/tle/{norad_id}&apiKey={API_KEY}'
        response = requests.get(url, timeout=10)
        data = response.json()
        
        if 'tle' not in data or 'info' not in data:
            return None
        
        info = data['info']
        tle_lines = data['tle'].split('\r\n')
        
        if len(tle_lines) < 2:
            return None
        
        tle_line1 = tle_lines[0].strip()
        tle_line2 = tle_lines[1].strip()
        
        # Parse TLE using fixed-width format (not space-delimited)
        # TLE Line 1: positions are fixed
        satellite_number = int(tle_line1[2:7])
        classification = tle_line1[7]
        epoch_year_str = tle_line1[18:20]
        epoch_day_str = tle_line1[20:32]
        mean_motion_dot_str = tle_line1[33:43]
        mean_motion_ddot_str = tle_line1[44:52]
        bstar_str = tle_line1[53:61]
        element_set_str = tle_line1[64:68]
        
        # TLE Line 2: positions are fixed
        inclination_str = tle_line2[8:16]
        ra_asc_node_str = tle_line2[17:25]
        eccentricity_str = tle_line2[26:33]
        arg_perigee_str = tle_line2[34:42]
        mean_anomaly_str = tle_line2[43:51]
        mean_motion_str = tle_line2[52:63]
        rev_at_epoch_str = tle_line2[63:68]
        
        # Extract values from TLE fixed-width strings
        epoch_year = int(epoch_year_str)
        epoch_day = float(epoch_day_str)
        
        # Convert epoch to datetime
        from datetime import timedelta
        year = 2000 + epoch_year if epoch_year < 57 else 1900 + epoch_year
        epoch_datetime = datetime(year, 1, 1) + timedelta(days=epoch_day - 1)
        
        mean_motion = float(mean_motion_str)
        eccentricity = float('0.' + eccentricity_str)
        inclination = float(inclination_str)
        ra_asc_node = float(ra_asc_node_str)
        arg_perigee = float(arg_perigee_str)
        mean_anomaly = float(mean_anomaly_str)
        element_set = int(element_set_str)
        rev_at_epoch = int(rev_at_epoch_str)
        
        # Calculate orbital parameters
        period = 1440.0 / mean_motion  # minutes
        semimajor_axis = (398600.4418 / ((mean_motion * 2 * 3.14159265359 / 86400) ** 2)) ** (1/3)  # km
        
        # Rough apoapsis/periapsis calculation
        apoapsis = semimajor_axis * (1 + eccentricity) - 6371  # Earth radius
        periapsis = semimajor_axis * (1 - eccentricity) - 6371
        
        # Parse BSTAR, mean motion dot/ddot from TLE format
        # BSTAR format: ±.ddddd±d (decimal point assumed after first digit, last char is exponent)
        try:
            bstar_mantissa = float(bstar_str[:-2]) / 100000.0
            bstar_exp = int(bstar_str[-2:])
            bstar = bstar_mantissa * (10 ** bstar_exp)
        except:
            bstar = 0.0
        
        try:
            mean_motion_dot = float(mean_motion_dot_str.strip())
        except:
            mean_motion_dot = 0.0
            
        try:
            ddot_mantissa = float(mean_motion_ddot_str[:-2]) / 100000.0
            ddot_exp = int(mean_motion_ddot_str[-2:])
            mean_motion_ddot = ddot_mantissa * (10 ** ddot_exp)
        except:
            mean_motion_ddot = 0.0
        
        return {
            'CCSDS_OMM_VERS': '2.0',
            'COMMENT': 'GENERATED VIA N2YO API',
            'CREATION_DATE': datetime.now().strftime('%Y-%m-%dT%H:%M:%S'),
            'ORIGINATOR': 'N2YO',
            'OBJECT_NAME': info['satname'],
            'OBJECT_ID': info.get('satid', norad_id),
            'CENTER_NAME': 'EARTH',
            'REF_FRAME': 'TEME',
            'TIME_SYSTEM': 'UTC',
            'MEAN_ELEMENT_THEORY': 'SGP4',
            'EPOCH': epoch_datetime.strftime('%Y-%m-%dT%H:%M:%S.%f'),
            'MEAN_MOTION': f'{mean_motion:.8f}',
            'ECCENTRICITY': f'{eccentricity:.8f}',
            'INCLINATION': f'{inclination:.4f}',
            'RA_OF_ASC_NODE': f'{ra_asc_node:.4f}',
            'ARG_OF_PERICENTER': f'{arg_perigee:.4f}',
            'MEAN_ANOMALY': f'{mean_anomaly:.4f}',
            'EPHEMERIS_TYPE': '0',
            'CLASSIFICATION_TYPE': 'U',
            'NORAD_CAT_ID': str(norad_id),
            'ELEMENT_SET_NO': str(element_set),
            'REV_AT_EPOCH': str(rev_at_epoch),
            'BSTAR': f'{bstar:.11f}',
            'MEAN_MOTION_DOT': f'{mean_motion_dot:.11f}',
            'MEAN_MOTION_DDOT': f'{mean_motion_ddot:.13f}',
            'SEMIMAJOR_AXIS': f'{semimajor_axis:.3f}',
            'PERIOD': f'{period:.3f}',
            'APOAPSIS': f'{apoapsis:.3f}',
            'PERIAPSIS': f'{periapsis:.3f}',
            'OBJECT_TYPE': 'PAYLOAD',
            'RCS_SIZE': 'LARGE',
            'COUNTRY_CODE': 'IND',
            'LAUNCH_DATE': info.get('launchdate', ''),
            'SITE': '',
            'DECAY_DATE': None,
            'FILE': '',
            'GP_ID': '',
            'TLE_LINE0': f'0 {info["satname"]}',
            'TLE_LINE1': tle_line1,
            'TLE_LINE2': tle_line2
        }
    except Exception as e:
        print(f'Error fetching data for {norad_id}: {e}')
        return None

print('🛰️  Fetching Current Satellite Data')
print('='*60)

# Get all satellites from database
conn = sqlite3.connect('db.sqlite3')
cursor = conn.cursor()
cursor.execute('SELECT norad_id, name FROM satTrack_satellite ORDER BY norad_id')
satellites = cursor.fetchall()
conn.close()

print(f'\nFound {len(satellites)} satellites in database\n')

# Prepare CSV
csv_filename = f'satellite_data_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'

# Column headers matching datac.csv format
fieldnames = [
    'CCSDS_OMM_VERS', 'COMMENT', 'CREATION_DATE', 'ORIGINATOR', 'OBJECT_NAME', 'OBJECT_ID',
    'CENTER_NAME', 'REF_FRAME', 'TIME_SYSTEM', 'MEAN_ELEMENT_THEORY', 'EPOCH', 'MEAN_MOTION',
    'ECCENTRICITY', 'INCLINATION', 'RA_OF_ASC_NODE', 'ARG_OF_PERICENTER', 'MEAN_ANOMALY',
    'EPHEMERIS_TYPE', 'CLASSIFICATION_TYPE', 'NORAD_CAT_ID', 'ELEMENT_SET_NO', 'REV_AT_EPOCH',
    'BSTAR', 'MEAN_MOTION_DOT', 'MEAN_MOTION_DDOT', 'SEMIMAJOR_AXIS', 'PERIOD', 'APOAPSIS',
    'PERIAPSIS', 'OBJECT_TYPE', 'RCS_SIZE', 'COUNTRY_CODE', 'LAUNCH_DATE', 'SITE', 'DECAY_DATE',
    'FILE', 'GP_ID', 'TLE_LINE0', 'TLE_LINE1', 'TLE_LINE2'
]

all_data = []
success_count = 0

for norad_id, name in satellites:
    print(f'Fetching {name} (ID: {norad_id})... ', end='')
    data = fetch_satellite_data(norad_id)
    
    if data:
        all_data.append(data)
        success_count += 1
        print('✅')
    else:
        print('❌')

print(f'\n📊 Successfully fetched data for {success_count}/{len(satellites)} satellites')

if all_data:
    with open(csv_filename, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames, quoting=csv.QUOTE_ALL)
        writer.writeheader()
        writer.writerows(all_data)
    
    print(f'\n✅ Data saved to: {csv_filename}')
    print(f'📈 Total records: {len(all_data)}')
else:
    print('\n❌ No data fetched')
