#!/usr/bin/env python
"""Check which satellites are currently over India"""
from skyfield.api import load, EarthSatellite
import sqlite3

# Get all satellites from database
conn = sqlite3.connect('db.sqlite3')
cursor = conn.cursor()
cursor.execute('SELECT norad_id, name, tle_now FROM satTrack_satellite')
satellites = cursor.fetchall()
conn.close()

ts = load.timescale()
now = ts.now()

print('🌏 Checking which satellites are currently over India...')
print(f'📍 India region: Lat 6-37°, Lon 68-97°\n')

satellites_over_india = []

for norad_id, name, tle in satellites:
    if not tle or len(tle.strip().split('\n')) < 2:
        continue
    
    try:
        tle_lines = tle.strip().split('\n')
        sat = EarthSatellite(tle_lines[0], tle_lines[1], name, ts)
        geocentric = sat.at(now)
        subpoint = geocentric.subpoint()
        
        lat = subpoint.latitude.degrees
        lon = subpoint.longitude.degrees
        height = subpoint.elevation.km
        
        # Check if over India
        if 6 <= lat <= 37 and 68 <= lon <= 97:
            satellites_over_india.append({
                'norad_id': norad_id,
                'name': name,
                'lat': lat,
                'lon': lon,
                'height': height
            })
    except Exception as e:
        continue

if satellites_over_india:
    print(f'✅ Found {len(satellites_over_india)} satellite(s) currently over India:\n')
    for i, sat in enumerate(satellites_over_india, 1):
        print(f'{i}. {sat["name"]} (NORAD ID: {sat["norad_id"]})')
        print(f'   📍 Position: Lat {sat["lat"]:.4f}°, Lon {sat["lon"]:.4f}°')
        print(f'   🛰️  Height: {sat["height"]:.2f} km')
        print(f'   🔗 Imagery URL: http://127.0.0.1:8000/sat/{sat["norad_id"]}/imagery')
        print()
else:
    print('❌ No satellites currently over India')
    print('💡 Use manual location or wait for next pass')
