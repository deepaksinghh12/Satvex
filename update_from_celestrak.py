import os
import django
import requests

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from satTrack.models import Satellite

# Celestrak TLE API (more reliable than N2YO)
CELESTRAK_API = "https://celestrak.org/NORAD/elements/gp.php"

def fetch_tle_from_celestrak(norad_id):
    """Fetch TLE from Celestrak"""
    try:
        params = {
            'CATNR': norad_id,
            'FORMAT': 'TLE'
        }
        response = requests.get(CELESTRAK_API, params=params, timeout=10)
        
        if response.status_code == 200:
            tle_text = response.text.strip()
            lines = tle_text.split('\n')
            
            if len(lines) >= 2:
                # Remove satellite name line if present
                if not lines[0].startswith('1'):
                    lines = lines[1:]
                
                if len(lines) >= 2:
                    tle = '\n'.join(lines[:2])
                    return tle
        
        return None
    except Exception as e:
        print(f"Error fetching from Celestrak: {e}")
        return None

def update_tle_from_celestrak():
    print("Fetching TLE data from Celestrak (more reliable source)")
    print("="*70)
    
    satellites = Satellite.objects.all()
    
    for sat in satellites:
        print(f"\n📡 {sat.name} (NORAD {sat.norad_id})")
        
        # Try Celestrak
        tle = fetch_tle_from_celestrak(sat.norad_id)
        
        if tle:
            sat.tle_now = tle
            sat.save(update_fields=['tle_now', 'last_tle_update'])
            print(f"   ✓ Updated from Celestrak")
            print(f"   TLE Preview: {tle[:50]}...")
        else:
            print(f"   ✗ No TLE available from Celestrak")
            print(f"   Note: Satellite may be decommissioned or NORAD ID incorrect")
    
    print("\n" + "="*70)
    print("\nFinal Status:")
    for sat in Satellite.objects.all().order_by('name'):
        status = "✓ Has TLE" if sat.tle_now else "✗ No TLE"
        print(f"{sat.name:20s} | NORAD: {sat.norad_id:6d} | {status}")

if __name__ == "__main__":
    update_tle_from_celestrak()
