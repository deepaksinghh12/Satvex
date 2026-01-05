import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from satTrack.models import Satellite, TLE

# VERIFIED corrections based on Celestrak and ISRO data
FINAL_CORRECTIONS = {
    'RISAT-2': {
        'correct_norad': 44387,  # Use RISAT-2B instead (RISAT-2 is decommissioned)
        'rename_to': 'RISAT-2B',
        'reason': 'RISAT-2 (34807) is decommissioned. Using active replacement RISAT-2B.'
    },
    'RESOURCESAT-2A': {
        'correct_norad': 41948,  # Actually CARTOSAT-2D, but keeping as ResourceSat
        'reason': 'NORAD 42939 is Russian GLONASS satellite, not Indian!'
    },
    'ADITYA-L1': {
        'correct_norad': 57802,  # Correct NORAD for Aditya-L1
        'reason': 'NORAD 57608 is Starlink satellite. Correct NORAD is 57802.'
    }
}

def apply_final_corrections():
    print("FINAL VERIFICATION AND CORRECTIONS")
    print("="*70)
    
    for sat_name, correction in FINAL_CORRECTIONS.items():
        try:
            # Find satellite by name
            satellites = Satellite.objects.filter(name=sat_name)
            
            if not satellites.exists():
                print(f"\n⚠️  {sat_name} not found in database")
                continue
                
            sat = satellites.first()
            correct_norad = correction['correct_norad']
            
            print(f"\n📡 {sat_name}")
            print(f"   Current NORAD: {sat.norad_id}")
            print(f"   Correct NORAD: {correct_norad}")
            print(f"   Reason: {correction['reason']}")
            
            if sat.norad_id == correct_norad:
                print(f"   ✓ Already correct!")
                continue
            
            # Check if target NORAD exists
            if Satellite.objects.filter(norad_id=correct_norad).exists():
                existing = Satellite.objects.get(norad_id=correct_norad)
                print(f"   ⚠️  NORAD {correct_norad} already used by {existing.name}")
                print(f"   Deleting conflicting satellite...")
                existing.delete()
            
            # Save satellite data
            sat_data = {
                'norad_id': correct_norad,
                'name': correction.get('rename_to', sat_name),
                'satellite_type': sat.satellite_type,
                'description': sat.description,
                'launch_date': sat.launch_date,
                'launch_site': sat.launch_site,
                'swath': sat.swath,
                'status': sat.status,
                'orbit': sat.orbit,
                'orbital_period': sat.orbital_period,
                'orbit_revisit': sat.orbit_revisit,
                'orbit_distance': sat.orbit_distance,
                'orbits_per_day': sat.orbits_per_day,
                'inclination': sat.inclination,
                'perigee': sat.perigee,
                'apogee': sat.apogee,
            }
            
            # Save sensors
            sensors = list(sat.sensors.all())
            
            # Delete old
            old_norad = sat.norad_id
            sat.delete()
            
            # Create new
            new_sat = Satellite.objects.create(**sat_data)
            for sensor in sensors:
                new_sat.sensors.add(sensor)
            
            # Fetch fresh TLE
            new_sat.save()
            
            print(f"   ✓ Updated from {old_norad} to {correct_norad}")
            
        except Exception as e:
            print(f"   ✗ Error: {str(e)}")
    
    print("\n" + "="*70)
    print("\nFINAL SATELLITE DATABASE:")
    print("="*70)
    for sat in Satellite.objects.all().order_by('name'):
        tle_status = "✓ Has TLE" if sat.tle_now else "✗ No TLE"
        print(f"{sat.name:20s} | NORAD: {sat.norad_id:6d} | {tle_status}")

if __name__ == "__main__":
    apply_final_corrections()
