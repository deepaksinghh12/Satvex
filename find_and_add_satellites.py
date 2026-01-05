#!/usr/bin/env python
"""Find satellites currently over India from live tracking data"""
import requests
import sqlite3
from skyfield.api import load, EarthSatellite
from datetime import datetime

# N2YO API key
API_KEY = 'M8PZCZ-5ELM7M-DE5LRK-531A'

# India center coordinates
INDIA_LAT = 20.5937
INDIA_LON = 78.9629

print('🌏 Searching for satellites currently over India...')
print('='*60)

# Get satellites currently above India region
url = f'https://api.n2yo.com/rest/v1/satellite/above/{INDIA_LAT}/{INDIA_LON}/0/90/18/&apiKey={API_KEY}'

try:
    response = requests.get(url, timeout=15)
    data = response.json()
    
    if 'above' not in data:
        print(f'⚠️ API Response: {data}')
        exit(1)
    
    satellites_above = data['above']
    print(f'\n✅ Found {len(satellites_above)} satellites above India region\n')
    
    # Connect to database
    conn = sqlite3.connect('db.sqlite3')
    cursor = conn.cursor()
    
    # Get existing satellites in database
    cursor.execute('SELECT norad_id FROM satTrack_satellite')
    existing_ids = {row[0] for row in cursor.fetchall()}
    
    satellites_over_india = []
    
    for sat in satellites_above[:20]:  # Check first 20 satellites
        norad_id = sat['satid']
        name = sat['satname']
        
        # Get detailed TLE for this satellite
        tle_url = f'https://api.n2yo.com/rest/v1/satellite/tle/{norad_id}&apiKey={API_KEY}'
        try:
            tle_response = requests.get(tle_url, timeout=10)
            tle_data = tle_response.json()
            
            if 'tle' in tle_data:
                tle1 = tle_data['tle'].split('\r\n')[0]
                tle2 = tle_data['tle'].split('\r\n')[1]
                
                # Calculate precise position
                ts = load.timescale()
                satellite = EarthSatellite(tle1, tle2, name, ts)
                now = ts.now()
                geocentric = satellite.at(now)
                subpoint = geocentric.subpoint()
                
                lat = subpoint.latitude.degrees
                lon = subpoint.longitude.degrees
                height = subpoint.elevation.km
                
                # Check if precisely over India (Lat 6-37°, Lon 68-97°)
                if 6 <= lat <= 37 and 68 <= lon <= 97:
                    satellites_over_india.append({
                        'norad_id': norad_id,
                        'name': name,
                        'lat': lat,
                        'lon': lon,
                        'height': height,
                        'tle1': tle1,
                        'tle2': tle2,
                        'in_db': norad_id in existing_ids
                    })
                    
                    print(f'✅ {name} (ID: {norad_id})')
                    print(f'   Position: Lat {lat:.4f}°, Lon {lon:.4f}°, Height {height:.2f} km')
                    print(f'   In database: {"Yes" if norad_id in existing_ids else "No - will add"}')
                    print()
        except Exception as e:
            continue
    
    conn.close()
    
    if not satellites_over_india:
        print('\n❌ No satellites are precisely over India right now')
        print('💡 Try manual location: http://127.0.0.1:8000/imagery')
        exit(0)
    
    # Add missing satellites to database
    print(f'\n📊 Summary: {len(satellites_over_india)} satellite(s) over India')
    
    new_satellites = [s for s in satellites_over_india if not s['in_db']]
    
    if new_satellites:
        print(f'\n➕ Adding {len(new_satellites)} new satellite(s) to database...\n')
        
        conn = sqlite3.connect('db.sqlite3')
        cursor = conn.cursor()
        
        for sat in new_satellites:
            try:
                tle_text = f"{sat['tle1']}\n{sat['tle2']}"
                today = datetime.now().strftime('%Y-%m-%d')
                
                # Extract orbital parameters
                inclination = float(sat['tle2'].split()[2])
                mean_motion = float(sat['tle2'].split()[7][:11])
                period = 1440.0 / mean_motion
                orbits_per_day = int(mean_motion)
                
                cursor.execute('''
                    INSERT INTO satTrack_satellite 
                    (norad_id, name, satellite_type, description, tle_now, launch_date, 
                     launch_site, last_tle_update, swath, status, orbit, orbital_period, 
                     orbit_revisit, orbit_distance, orbits_per_day, inclination, perigee, apogee)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    sat['norad_id'],
                    sat['name'][:20],  # Truncate to fit varchar(20)
                    'Earth Observation',
                    f"Auto-added satellite tracked over India",
                    tle_text,
                    '2020-01-01',  # Default date
                    'Unknown',
                    today,
                    100.0,  # Default swath
                    'Active',
                    'LEO',
                    round(period, 2),
                    1,  # Default revisit
                    sat['height'],
                    orbits_per_day,
                    round(inclination, 2),
                    sat['height'] - 20,  # Approximate
                    sat['height'] + 20   # Approximate
                ))
                
                print(f'   ✅ Added {sat["name"]} (ID: {sat["norad_id"]})')
            except Exception as e:
                print(f'   ⚠️ Failed to add {sat["name"]}: {e}')
        
        conn.commit()
        conn.close()
    
    # Show imagery URLs
    print(f'\n🔗 Fetch imagery from these satellites:\n')
    for i, sat in enumerate(satellites_over_india, 1):
        print(f'{i}. {sat["name"]} (NORAD ID: {sat["norad_id"]})')
        print(f'   📍 Lat {sat["lat"]:.4f}°, Lon {sat["lon"]:.4f}°')
        print(f'   🔗 http://127.0.0.1:8000/sat/{sat["norad_id"]}/imagery')
        print()

except Exception as e:
    print(f'❌ Error: {e}')
    print('\n💡 Alternative: Use manual location at http://127.0.0.1:8000/imagery')
