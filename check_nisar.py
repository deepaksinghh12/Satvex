#!/usr/bin/env python
"""Check NISAR position and next pass over India"""
from skyfield.api import load, EarthSatellite
import sqlite3
from datetime import datetime, timedelta

# Get NISAR from database
conn = sqlite3.connect('db.sqlite3')
cursor = conn.cursor()
cursor.execute('SELECT norad_id, name, tle_now FROM satTrack_satellite WHERE norad_id = 65053')
result = cursor.fetchone()
conn.close()

if not result:
    print('❌ NISAR not found in database')
    exit(1)

norad_id, name, tle = result
tle_lines = tle.strip().split('\n')

ts = load.timescale()
sat = EarthSatellite(tle_lines[0], tle_lines[1], name, ts)

print('🛰️  NISAR Satellite Status')
print('='*60)

# Current position
now = ts.now()
geocentric = sat.at(now)
subpoint = geocentric.subpoint()

lat = subpoint.latitude.degrees
lon = subpoint.longitude.degrees
height = subpoint.elevation.km

print(f'\n📍 Current Position:')
print(f'   Latitude:  {lat:.4f}°')
print(f'   Longitude: {lon:.4f}°')
print(f'   Height:    {height:.2f} km')
print(f'   Time:      {now.utc_strftime("%Y-%m-%d %H:%M:%S UTC")}')

# Check if over India
if 6 <= lat <= 37 and 68 <= lon <= 97:
    print(f'\n✅ NISAR IS CURRENTLY OVER INDIA!')
    print(f'🔗 Fetch imagery: http://127.0.0.1:8000/sat/65053/imagery')
else:
    print(f'\n❌ NISAR is NOT over India currently')

# Find next passes over India
print(f'\n🔍 Searching for next NISAR passes over India...')
print(f'   (Checking every 5 minutes for next 24 hours)')

passes = []
check_time = now
end_time = ts.utc(now.utc_datetime() + timedelta(hours=24))

while check_time.tt < end_time.tt and len(passes) < 5:
    geocentric = sat.at(check_time)
    subpoint = geocentric.subpoint()
    
    lat = subpoint.latitude.degrees
    lon = subpoint.longitude.degrees
    
    if 6 <= lat <= 37 and 68 <= lon <= 97:
        time_until = (check_time.utc_datetime() - now.utc_datetime()).total_seconds() / 3600
        passes.append({
            'time': check_time.utc_strftime("%Y-%m-%d %H:%M:%S UTC"),
            'lat': lat,
            'lon': lon,
            'hours_from_now': time_until
        })
        check_time = ts.utc(check_time.utc_datetime() + timedelta(minutes=30))
    else:
        check_time = ts.utc(check_time.utc_datetime() + timedelta(minutes=5))

if passes:
    print(f'\n✅ Found {len(passes)} pass(es) over India in next 24 hours:\n')
    for i, p in enumerate(passes, 1):
        hours = int(p['hours_from_now'])
        minutes = int((p['hours_from_now'] - hours) * 60)
        print(f'{i}. {p["time"]}')
        print(f'   Position: Lat {p["lat"]:.2f}°, Lon {p["lon"]:.2f}°')
        print(f'   In: {hours}h {minutes}m')
        print()
else:
    print('\n❌ No passes over India found in next 24 hours')

print(f'💡 You can also use manual location feature at:')
print(f'   http://127.0.0.1:8000/imagery')
