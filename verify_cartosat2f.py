import os
import django
from datetime import datetime

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from satTrack.models import Satellite
from satTrack.extract_data import convert, get_live_data

# Get CARTOSAT-2F
sat = Satellite.objects.get(norad_id=43111)

print("="*70)
print("CARTOSAT-2F VERIFICATION")
print("="*70)
print(f"\nSatellite: {sat.name}")
print(f"NORAD ID: {sat.norad_id}")
print(f"Last TLE Update: {sat.last_tle_update}")
print("\nCurrent TLE:")
print(sat.tle_now)

# Get current position
if sat.tle_now:
    try:
        position = get_live_data(sat.tle_now, {'lat': 0, 'lon': 0})
        
        print("\n" + "="*70)
        print("CURRENT POSITION FROM YOUR APPLICATION:")
        print("="*70)
        print(f"Latitude:    {position['lat']:.2f}°")
        print(f"Longitude:   {position['lon']:.2f}°")
        print(f"Altitude:    {position['height']:.2f} km")
        print(f"Speed:       {position['speed']:.2f} km/s")
        
        print("\n" + "="*70)
        print("N2YO DATA (for comparison):")
        print("="*70)
        print("NORAD ID:    43111")
        print("UTC:         16:54:24")
        print("Latitude:    -2.72°")
        print("Longitude:   -111.24°")
        print("Altitude:    510.74 km")
        print("Speed:       7.61 km/s")
        
        print("\n" + "="*70)
        print("DIFFERENCE:")
        print("="*70)
        lat_diff = abs(position['lat'] - (-2.72))
        lon_diff = abs(position['lon'] - (-111.24))
        alt_diff = abs(position['height'] - 510.74)
        speed_diff = abs(position['speed'] - 7.61)
        
        print(f"Latitude difference:  {lat_diff:.2f}°")
        print(f"Longitude difference: {lon_diff:.2f}°")
        print(f"Altitude difference:  {alt_diff:.2f} km")
        print(f"Speed difference:     {speed_diff:.2f} km/s")
        
        if lat_diff < 5 and lon_diff < 5 and alt_diff < 10:
            print("\n✅ POSITIONS MATCH! Your data is accurate!")
        else:
            print("\n⚠️  Large difference detected. May be due to:")
            print("   - Different observation times")
            print("   - TLE needs updating")
            print("   - Propagation model differences")
        
        print(f"\nCurrent UTC time: {datetime.utcnow().strftime('%H:%M:%S')}")
        
    except Exception as e:
        print(f"\n❌ Error calculating position: {str(e)}")
        import traceback
        traceback.print_exc()
else:
    print("\n❌ No TLE data available!")
