import os
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from satTrack.models import Satellite

# Correct NORAD IDs for the satellites in your database
CORRECTIONS = {
    'RISAT-2': 34807,           # Currently wrong: needs correction
    'RESOURCESAT-2': 37387,     # This one is correct
    'CARTOSAT-3': 44804,        # Currently 41948 (which is actually CARTOSAT-2D)
    'CARTOSAT-2F': 43111,       # Currently 42063 (which is actually CARTOSAT-2E)
    'RESOURCESAT-2A': 42939,    # This one is correct
    'ADITYA-L1': 57608,         # This one seems correct based on launch date
}

def fix_norad_ids():
    print("Checking and fixing NORAD IDs...")
    print("="*70)
    
    satellites = Satellite.objects.all()
    
    for sat in satellites:
        if sat.name in CORRECTIONS:
            correct_norad = CORRECTIONS[sat.name]
            
            if sat.norad_id != correct_norad:
                print(f"\n❌ {sat.name}")
                print(f"   Current NORAD ID: {sat.norad_id} (INCORRECT)")
                print(f"   Correct NORAD ID: {correct_norad}")
                
                # Check if the correct NORAD ID already exists
                if Satellite.objects.filter(norad_id=correct_norad).exists():
                    print(f"   ⚠️  WARNING: NORAD ID {correct_norad} already exists!")
                    print(f"   Skipping to avoid conflict...")
                    continue
                
                # Update the NORAD ID
                old_norad = sat.norad_id
                
                # We need to delete and recreate because norad_id is the primary key
                sat_data = {
                    'norad_id': correct_norad,
                    'name': sat.name,
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
                
                # Get sensors before deleting
                sensors = list(sat.sensors.all())
                
                # Delete old satellite
                sat.delete()
                
                # Create new satellite with correct NORAD ID
                new_sat = Satellite.objects.create(**sat_data)
                
                # Re-add sensors
                for sensor in sensors:
                    new_sat.sensors.add(sensor)
                
                # Fetch fresh TLE data
                new_sat.save()
                
                print(f"   ✓ Updated successfully!")
                
            else:
                print(f"\n✓ {sat.name}: NORAD ID {sat.norad_id} is correct")
    
    print("\n" + "="*70)
    print("\nFinal satellite list:")
    for sat in Satellite.objects.all().order_by('name'):
        print(f"{sat.name:20s} | NORAD ID: {sat.norad_id:6d} | Last Update: {sat.last_tle_update}")

if __name__ == "__main__":
    fix_norad_ids()
