import os
import django
from datetime import datetime

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from satTrack.models import Satellite
from satTrack.extract_data import convert, get_live_data

# Get CARTOSAT-3
sat = Satellite.objects.get(norad_id=44804)

print("="*70)
print("CARTOSAT-3 VERIFICATION")
print("="*70)
print(f"\nSatellite: {sat.name}")
print(f"NORAD ID: {sat.norad_id}")
print(f"Last TLE Update: {sat.last_tle_update}")

# Show TLE details
if sat.tle_now:
    lines = sat.tle_now.strip().split('\n')
    if len(lines) >= 2:
        # Extract epoch from TLE
        epoch_str = lines[0][18:32]
        year = int("20" + epoch_str[:2])
        day_of_year = float(epoch_str[2:])
        
        print(f"\nTLE Epoch: Year {year}, Day {day_of_year:.8f}")
        print(f"TLE Age: Check if this is recent")
        
print("\nCurrent TLE:")
print(sat.tle_now)

# Get current position
if sat.tle_now:
    try:
        position = get_live_data(sat.tle_now, {'lat': 0, 'lon': 0})
        
        print("\n" + "="*70)
        print("CURRENT POSITION FROM YOUR APPLICATION:")
        print("="*70)
        current_time = datetime.utcnow()
        print(f"Observation Time: {current_time.strftime('%Y-%m-%d %H:%M:%S')} UTC")
        print(f"Latitude:         {position['lat']:.4f}°")
        print(f"Longitude:        {position['lon']:.4f}°")
        print(f"Altitude:         {position['height']:.2f} km")
        print(f"Speed:            {position['speed']:.2f} km/s")
        
        print("\n" + "="*70)
        print("INSTRUCTIONS:")
        print("="*70)
        print("1. Go to https://www.n2yo.com/satellite/?s=44804")
        print("2. Note the EXACT time shown on N2YO")
        print("3. Compare the latitude/longitude at that EXACT moment")
        print("4. Remember: Satellite moves ~7.6 km/s (27,360 km/h)")
        print("   - In 1 minute: ~456 km")
        print("   - Latitude can change by ~4° per minute")
        print("\nFor accurate comparison:")
        print(f"  Check N2YO at: {current_time.strftime('%H:%M:%S')} UTC")
        print("  Or wait and check your app at N2YO's displayed time")
        
    except Exception as e:
        print(f"\n❌ Error calculating position: {str(e)}")
        import traceback
        traceback.print_exc()
else:
    print("\n❌ No TLE data available!")

print("\n" + "="*70)
print("TLE FRESHNESS CHECK:")
print("="*70)

# Check all satellites TLE age
for s in Satellite.objects.all().order_by('name'):
    if s.tle_now:
        lines = s.tle_now.strip().split('\n')
        if len(lines) >= 1:
            epoch_str = lines[0][18:32]
            print(f"{s.name:20s} | TLE Epoch: Day {epoch_str}")
    else:
        print(f"{s.name:20s} | ❌ NO TLE")
