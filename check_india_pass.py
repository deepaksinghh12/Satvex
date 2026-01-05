#!/usr/bin/env python
"""
Check when Cartosat-3 will next pass over India
"""
from skyfield.api import load, EarthSatellite
from datetime import timedelta
import sqlite3

# Get satellite TLE
conn = sqlite3.connect('db.sqlite3')
cursor = conn.cursor()
cursor.execute('SELECT name, tle_now FROM satTrack_satellite WHERE norad_id = 44804')
result = cursor.fetchone()
conn.close()

if not result:
    print('Satellite not found in database')
    exit(1)

name, tle = result
tle_lines = tle.strip().split('\n')

ts = load.timescale()
sat = EarthSatellite(tle_lines[0], tle_lines[1], name, ts)

# Check positions for next 24 hours, every 5 minutes
print(f'🛰️  Satellite: {name}')
print(f'📍 India region: Lat 6-37°, Lon 68-97°')
print(f'\nSearching next 24 hours for passes over India...\n')

now = ts.now()
found_pass = False
pass_count = 0

for minutes in range(0, 24 * 60, 5):  # Check every 5 minutes
    t = ts.utc(now.utc_datetime() + timedelta(minutes=minutes))
    geocentric = sat.at(t)
    subpoint = geocentric.subpoint()
    lat = subpoint.latitude.degrees
    lon = subpoint.longitude.degrees
    
    # Check if over India
    is_over_india = (6 <= lat <= 37) and (68 <= lon <= 97)
    
    if is_over_india and not found_pass:
        found_pass = True
        pass_count += 1
        hours = minutes // 60
        mins = minutes % 60
        print(f'✅ Pass #{pass_count}:')
        print(f'   Time: {t.utc_datetime().strftime("%Y-%m-%d %H:%M:%S")} UTC')
        print(f'   In: {hours}h {mins}m from now')
        print(f'   Position: Lat {lat:.2f}°, Lon {lon:.2f}°')
        print()
    elif not is_over_india and found_pass:
        # Just exited India, reset flag to look for next pass
        found_pass = False

if pass_count == 0:
    print('❌ No passes over India found in next 24 hours')
    print('\nCurrent position:')
    geocentric = sat.at(now)
    subpoint = geocentric.subpoint()
    print(f'   Lat: {subpoint.latitude.degrees:.2f}°')
    print(f'   Lon: {subpoint.longitude.degrees:.2f}°')
else:
    print(f'Found {pass_count} pass(es) over India in next 24 hours')
