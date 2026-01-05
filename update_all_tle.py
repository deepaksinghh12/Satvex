import os
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from satTrack.models import Satellite
from datetime import datetime

def update_all_satellites():
    """Update TLE data for all satellites"""
    satellites = Satellite.objects.all()
    
    print(f"Found {satellites.count()} satellites to update")
    print("="*60)
    
    for sat in satellites:
        print(f"\nUpdating: {sat.name} (NORAD ID: {sat.norad_id})")
        print(f"Last TLE Update: {sat.last_tle_update}")
        
        try:
            # Save will trigger TLE update via save_new_tle()
            sat.save()
            print(f"✓ Successfully updated {sat.name}")
            
            # Show current position info
            if sat.tle_now:
                lines = sat.tle_now.strip().split('\n')
                if len(lines) >= 2:
                    # Extract epoch from TLE
                    epoch_str = lines[0][18:32]
                    print(f"  TLE Epoch: {epoch_str}")
                    
        except Exception as e:
            print(f"✗ Error updating {sat.name}: {str(e)}")
    
    print("\n" + "="*60)
    print("TLE update completed!")
    
    # Show summary
    print("\nCurrent satellite status:")
    for sat in Satellite.objects.all():
        print(f"{sat.name:20s} | Last Update: {sat.last_tle_update} | Status: {sat.status}")

if __name__ == "__main__":
    update_all_satellites()
