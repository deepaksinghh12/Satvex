#!/usr/bin/env python
"""Fetch all Indian satellites and add them to the database"""
import requests
import sqlite3
from datetime import datetime

API_KEY = 'M8PZCZ-5ELM7M-DE5LRK-531A'

print('🇮🇳 Fetching All Indian Satellites')
print('='*60)

# Common Indian satellite name patterns
indian_patterns = [
    'CARTOSAT', 'RESOURCESAT', 'RISAT', 'OCEANSAT', 'INSAT', 'GSAT',
    'IRNSS', 'NAVIC', 'MEGHA', 'SCATSAT', 'SARAL', 'ASTROSAT',
    'CHANDRAYAAN', 'MANGALYAAN', 'EMISAT', 'MICROSAT', 'NISAR',
    'GAGAN', 'EOS', 'ADITYA', 'XPoSat'
]

def fetch_all_satellites():
    """Fetch satellites from Celestrak Indian satellites group"""
    satellites = []
    
    try:
        # Try Celestrak Indian satellites
        print('\n📡 Fetching from Celestrak Indian satellites group...')
        url = 'https://celestrak.org/NORAD/elements/gp.php?GROUP=indian&FORMAT=tle'
        response = requests.get(url, timeout=15)
        
        if response.status_code == 200:
            lines = response.text.strip().split('\n')
            i = 0
            while i < len(lines) - 2:
                name = lines[i].strip()
                tle1 = lines[i+1].strip()
                tle2 = lines[i+2].strip()
                
                if tle1.startswith('1 ') and tle2.startswith('2 '):
                    norad_id = int(tle1[2:7])
                    satellites.append({
                        'norad_id': norad_id,
                        'name': name,
                        'tle1': tle1,
                        'tle2': tle2
                    })
                i += 3
            
            print(f'   Found {len(satellites)} satellites')
    except Exception as e:
        print(f'   ⚠️ Error: {e}')
    
    # Also try active satellites and filter by Indian names
    try:
        print('\n📡 Searching active satellites for Indian missions...')
        url = 'https://celestrak.org/NORAD/elements/gp.php?GROUP=active&FORMAT=tle'
        response = requests.get(url, timeout=15)
        
        if response.status_code == 200:
            lines = response.text.strip().split('\n')
            i = 0
            additional = 0
            while i < len(lines) - 2:
                name = lines[i].strip()
                tle1 = lines[i+1].strip()
                tle2 = lines[i+2].strip()
                
                if tle1.startswith('1 ') and tle2.startswith('2 '):
                    # Check if name matches Indian patterns
                    if any(pattern in name.upper() for pattern in indian_patterns):
                        norad_id = int(tle1[2:7])
                        
                        # Check if already in list
                        if not any(s['norad_id'] == norad_id for s in satellites):
                            satellites.append({
                                'norad_id': norad_id,
                                'name': name,
                                'tle1': tle1,
                                'tle2': tle2
                            })
                            additional += 1
                i += 3
            
            print(f'   Found {additional} additional satellites')
    except Exception as e:
        print(f'   ⚠️ Error: {e}')
    
    return satellites

def extract_orbital_params(tle1, tle2):
    """Extract orbital parameters from TLE"""
    try:
        # Parse TLE using fixed-width format
        inclination = float(tle2[8:16].strip())
        ra_asc_node = float(tle2[17:25].strip())
        eccentricity = float('0.' + tle2[26:33].strip())
        arg_perigee = float(tle2[34:42].strip())
        mean_anomaly = float(tle2[43:51].strip())
        mean_motion = float(tle2[52:63].strip())
        
        # Calculate period and altitude
        period = 1440.0 / mean_motion  # minutes
        semimajor_axis = (398600.4418 / ((mean_motion * 2 * 3.14159265359 / 86400) ** 2)) ** (1/3)
        
        apoapsis = semimajor_axis * (1 + eccentricity) - 6371
        periapsis = semimajor_axis * (1 - eccentricity) - 6371
        
        # Orbit type
        if inclination > 80:
            if 98 <= inclination <= 102:
                orbit_type = 'Sun-Synchronous'
            else:
                orbit_type = 'Polar'
        elif inclination < 10:
            orbit_type = 'Equatorial'
        else:
            orbit_type = 'Inclined'
        
        return {
            'inclination': round(inclination, 4),
            'eccentricity': round(eccentricity, 8),
            'period': round(period, 2),
            'apoapsis': round(apoapsis, 2),
            'periapsis': round(periapsis, 2),
            'orbit_type': orbit_type,
            'mean_motion': round(mean_motion, 8)
        }
    except Exception as e:
        print(f'   Error parsing TLE: {e}')
        return None

def add_to_database(satellites):
    """Add satellites to database"""
    conn = sqlite3.connect('db.sqlite3')
    cursor = conn.cursor()
    
    # Get existing satellites
    cursor.execute('SELECT norad_id FROM satTrack_satellite')
    existing_ids = {row[0] for row in cursor.fetchall()}
    
    added = 0
    updated = 0
    today = datetime.now().strftime('%Y-%m-%d')
    
    for sat in satellites:
        norad_id = sat['norad_id']
        name = sat['name'][:20]  # Truncate to fit varchar(20)
        tle_text = f"{sat['tle1']}\n{sat['tle2']}"
        
        params = extract_orbital_params(sat['tle1'], sat['tle2'])
        if not params:
            continue
        
        if norad_id in existing_ids:
            # Update TLE and parameters
            cursor.execute('''
                UPDATE satTrack_satellite 
                SET tle_now = ?, 
                    last_tle_update = ?,
                    inclination = ?,
                    orbital_period = ?,
                    apogee = ?,
                    perigee = ?,
                    orbit = ?
                WHERE norad_id = ?
            ''', (
                tle_text, today,
                params['inclination'],
                params['period'],
                params['apoapsis'],
                params['periapsis'],
                params['orbit_type'],
                norad_id
            ))
            updated += 1
        else:
            # Insert new satellite
            try:
                orbits_per_day = int(params['mean_motion'])
                
                cursor.execute('''
                    INSERT INTO satTrack_satellite 
                    (norad_id, name, satellite_type, description, tle_now, launch_date, 
                     launch_site, last_tle_update, swath, status, orbit, orbital_period, 
                     orbit_revisit, orbit_distance, orbits_per_day, inclination, perigee, apogee)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    norad_id,
                    name,
                    'Earth Observation',
                    'Indian satellite mission',
                    tle_text,
                    '2020-01-01',
                    'India',
                    today,
                    100.0,
                    'Active',
                    params['orbit_type'],
                    params['period'],
                    1,
                    params['periapsis'],
                    orbits_per_day,
                    params['inclination'],
                    params['periapsis'],
                    params['apoapsis']
                ))
                added += 1
                print(f'   ✅ Added: {name} (ID: {norad_id})')
            except Exception as e:
                print(f'   ⚠️ Failed to add {name}: {e}')
    
    conn.commit()
    conn.close()
    
    return added, updated

# Main execution
satellites = fetch_all_satellites()

if satellites:
    print(f'\n📊 Total Indian satellites found: {len(satellites)}')
    print('\n➕ Adding to database...\n')
    
    added, updated = add_to_database(satellites)
    
    print(f'\n✅ Summary:')
    print(f'   New satellites added: {added}')
    print(f'   Existing satellites updated: {updated}')
    print(f'   Total processed: {added + updated}')
else:
    print('\n❌ No satellites found')
