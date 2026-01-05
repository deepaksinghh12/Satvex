import os
import django
from datetime import datetime

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from satTrack.models import Satellite
from satTrack.extract_data import convert, get_live_data

def verify_satellite_position(norad_id, expected_data):
    """Verify satellite position matches N2YO data"""
    
    try:
        sat = Satellite.objects.get(norad_id=norad_id)
        print(f"Verifying: {sat.name} (NORAD {norad_id})")
        print("="*70)
        
        if not sat.tle_now:
            print("❌ No TLE data available!")
            return
        
        print(f"\nTLE Data:")
        print(sat.tle_now)
        print()
        
        # Get current position
        position = get_live_data(sat.tle_now, {'lat': 0, 'lon': 0})
        
        print(f"{'Parameter':<20} {'Your System':<25} {'N2YO':<25} {'Match?'}")
        print("-"*70)
        
        # Compare latitude
        your_lat = position['lat']
        n2yo_lat = expected_data['latitude']
        lat_diff = abs(your_lat - n2yo_lat)
        lat_match = "✓" if lat_diff < 0.5 else "✗"
        print(f"{'Latitude':<20} {your_lat:>8.2f}°{'':<15} {n2yo_lat:>8.2f}°{'':<15} {lat_match}")
        
        # Compare longitude
        your_lon = position['lon']
        n2yo_lon = expected_data['longitude']
        lon_diff = abs(your_lon - n2yo_lon)
        lon_match = "✓" if lon_diff < 0.5 else "✗"
        print(f"{'Longitude':<20} {your_lon:>8.2f}°{'':<15} {n2yo_lon:>8.2f}°{'':<15} {lon_match}")
        
        # Compare altitude
        your_alt = position['height']
        n2yo_alt = expected_data['altitude_km']
        alt_diff = abs(your_alt - n2yo_alt)
        alt_match = "✓" if alt_diff < 5 else "✗"
        print(f"{'Altitude (km)':<20} {your_alt:>8.2f}{'':<16} {n2yo_alt:>8.2f}{'':<16} {alt_match}")
        
        # Compare speed
        your_speed = position['speed']
        n2yo_speed = expected_data['speed_kms']
        speed_diff = abs(your_speed - n2yo_speed)
        speed_match = "✓" if speed_diff < 0.2 else "✗"
        print(f"{'Speed (km/s)':<20} {your_speed:>8.2f}{'':<16} {n2yo_speed:>8.2f}{'':<16} {speed_match}")
        
        print()
        print("="*70)
        
        # Overall assessment
        all_match = lat_match == "✓" and lon_match == "✓" and alt_match == "✓" and speed_match == "✓"
        
        if all_match:
            print("✅ SUCCESS! Your data matches N2YO within acceptable tolerances!")
            print("   Note: Small differences are normal due to timing and propagation.")
        else:
            print("⚠️  DIFFERENCES DETECTED")
            print(f"   Latitude difference: {lat_diff:.4f}°")
            print(f"   Longitude difference: {lon_diff:.4f}°")
            print(f"   Altitude difference: {alt_diff:.2f} km")
            print(f"   Speed difference: {speed_diff:.2f} km/s")
            
            if lat_diff > 5 or lon_diff > 5:
                print("\n   ⚠️  LARGE POSITION DIFFERENCE!")
                print("   This could indicate:")
                print("   - TLE data is outdated")
                print("   - Timing difference between measurements")
                print("   - Wrong satellite NORAD ID")
        
        print(f"\nTimestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}")
        
    except Satellite.DoesNotExist:
        print(f"❌ Satellite with NORAD ID {norad_id} not found!")
    except Exception as e:
        print(f"❌ Error: {str(e)}")

# N2YO data for CARTOSAT-2F at 16:54:24 UTC
n2yo_data = {
    'latitude': -2.72,
    'longitude': -111.24,
    'altitude_km': 510.74,
    'speed_kms': 7.61,
}

print("CARTOSAT-2F POSITION VERIFICATION")
print("="*70)
print(f"N2YO Time: 16:54:24 UTC (December 2, 2025)")
print(f"Checking your system at: {datetime.now().strftime('%H:%M:%S UTC')}")
print()

verify_satellite_position(43111, n2yo_data)
