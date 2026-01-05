import os
import django
import sys
from datetime import datetime, timedelta

# Setup Django
sys.path.append(r'd:\sat-track')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from satTrack.models import Satellite
from sgp4.api import Satrec, jday
from skyfield.api import load, wgs84, EarthSatellite
from skyfield.toposlib import GeographicPosition
import numpy as np

# Alwar, Rajasthan, India coordinates
ALWAR_LAT = 27.5667  # degrees
ALWAR_LON = 76.6167  # degrees
ALWAR_ALT = 268      # meters (approximate elevation)

# Minimum elevation angle for visibility (degrees)
MIN_ELEVATION = 10  # Satellite must be at least 10 degrees above horizon

def calculate_passes(satellite, observer_lat, observer_lon, observer_alt, hours_ahead=48):
    """
    Calculate when a satellite will pass over a given location
    """
    print(f"\n{'='*70}")
    print(f"Satellite: {satellite.name} (NORAD ID: {satellite.norad_id})")
    print(f"{'='*70}")
    
    if not satellite.tle_now:
        print("❌ No TLE data available for this satellite")
        return
    
    try:
        # Parse TLE
        tle_lines = satellite.tle_now.strip().split('\n')
        if len(tle_lines) < 2:
            print("❌ Invalid TLE format")
            return
        
        line1 = tle_lines[0].strip()
        line2 = tle_lines[1].strip()
        
        # Create Skyfield satellite object
        ts = load.timescale()
        sat = EarthSatellite(line1, line2, satellite.name, ts)
        
        # Create observer location
        observer = wgs84.latlon(observer_lat, observer_lon, observer_alt)
        
        # Time range to check
        t0 = ts.now()
        t1 = ts.utc(t0.utc_datetime() + timedelta(hours=hours_ahead))
        
        # Find passes
        t, events = sat.find_events(observer, t0, t1, altitude_degrees=MIN_ELEVATION)
        
        if len(t) == 0:
            print(f"❌ No passes above {MIN_ELEVATION}° elevation in the next {hours_ahead} hours")
            return
        
        print(f"\n📡 Passes over Alwar in the next {hours_ahead} hours:")
        print(f"   (Minimum elevation: {MIN_ELEVATION}°)\n")
        
        pass_count = 0
        i = 0
        while i < len(events):
            if events[i] == 0:  # Rise event
                rise_time = t[i]
                
                # Find corresponding culmination and set
                max_time = None
                max_elevation = 0
                set_time = None
                
                j = i + 1
                while j < len(events):
                    if events[j] == 1:  # Culmination
                        max_time = t[j]
                        # Calculate elevation at culmination
                        difference = sat.at(max_time) - observer.at(max_time)
                        topocentric = difference.position.km
                        alt, az, distance = difference.altaz()
                        max_elevation = alt.degrees
                    elif events[j] == 2:  # Set
                        set_time = t[j]
                        break
                    j += 1
                
                if set_time is not None:
                    pass_count += 1
                    rise_dt = rise_time.utc_datetime()
                    set_dt = set_time.utc_datetime()
                    duration = (set_dt - rise_dt).total_seconds() / 60
                    
                    # Calculate rise/set azimuth
                    rise_diff = sat.at(rise_time) - observer.at(rise_time)
                    rise_alt, rise_az, _ = rise_diff.altaz()
                    
                    set_diff = sat.at(set_time) - observer.at(set_time)
                    set_alt, set_az, _ = set_diff.altaz()
                    
                    print(f"Pass #{pass_count}:")
                    print(f"  🌅 Rise:        {rise_dt.strftime('%Y-%m-%d %H:%M:%S')} UTC")
                    print(f"                 (Azimuth: {rise_az.degrees:.1f}°)")
                    print(f"  🔝 Highest:    {max_time.utc_datetime().strftime('%Y-%m-%d %H:%M:%S')} UTC")
                    print(f"                 (Elevation: {max_elevation:.1f}°)")
                    print(f"  🌇 Set:        {set_dt.strftime('%Y-%m-%d %H:%M:%S')} UTC")
                    print(f"                 (Azimuth: {set_az.degrees:.1f}°)")
                    print(f"  ⏱️  Duration:   {duration:.1f} minutes")
                    print()
                    
                    # Convert to IST for user convenience
                    ist_rise = rise_dt + timedelta(hours=5, minutes=30)
                    ist_max = max_time.utc_datetime() + timedelta(hours=5, minutes=30)
                    ist_set = set_dt + timedelta(hours=5, minutes=30)
                    
                    print(f"  📅 In Indian Standard Time (IST):")
                    print(f"     Rise:    {ist_rise.strftime('%Y-%m-%d %H:%M:%S')} IST")
                    print(f"     Highest: {ist_max.strftime('%Y-%m-%d %H:%M:%S')} IST")
                    print(f"     Set:     {ist_set.strftime('%Y-%m-%d %H:%M:%S')} IST")
                    print()
                
                i = j
            i += 1
        
        if pass_count == 0:
            print(f"❌ No complete passes found in the next {hours_ahead} hours")
        else:
            print(f"✅ Total passes: {pass_count}")
            
    except Exception as e:
        print(f"❌ Error calculating passes: {str(e)}")
        import traceback
        traceback.print_exc()

def main():
    print("=" * 70)
    print("SATELLITE PASS PREDICTOR FOR ALWAR, RAJASTHAN")
    print("=" * 70)
    print(f"\n📍 Observer Location:")
    print(f"   Latitude:  {ALWAR_LAT}°N")
    print(f"   Longitude: {ALWAR_LON}°E")
    print(f"   Altitude:  {ALWAR_ALT}m")
    print(f"\n🕐 Current Time: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC")
    print(f"   ({(datetime.utcnow() + timedelta(hours=5, minutes=30)).strftime('%Y-%m-%d %H:%M:%S')} IST)")
    
    # Get all satellites
    satellites = Satellite.objects.all()
    
    if not satellites:
        print("\n❌ No satellites found in database!")
        return
    
    print(f"\n🛰️  Found {satellites.count()} satellites in database\n")
    
    # Calculate passes for each satellite
    for satellite in satellites:
        calculate_passes(satellite, ALWAR_LAT, ALWAR_LON, ALWAR_ALT, hours_ahead=48)
    
    print("\n" + "=" * 70)
    print("CALCULATION COMPLETE")
    print("=" * 70)
    print("\n💡 Tips:")
    print("   • Higher elevation passes provide better imaging opportunities")
    print("   • Passes above 30° elevation are generally good")
    print("   • Azimuth: N=0°, E=90°, S=180°, W=270°")
    print("   • Check weather conditions before the pass time")

if __name__ == "__main__":
    main()
