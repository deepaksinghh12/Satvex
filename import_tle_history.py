#!/usr/bin/env python
"""Import historical TLE data from datac.csv to build TLE history"""
import django
import os
import sys
import csv
from datetime import datetime

# Setup Django
sys.path.append('d:/satallite-track')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from satTrack.models import Satellite, TLE

print('📚 Importing TLE History from datac.csv')
print('='*60)

# Read the CSV file
try:
    with open('datac.csv', 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        
        tle_by_satellite = {}
        
        for row in reader:
            norad_id = int(row['NORAD_CAT_ID'])
            epoch_str = row['EPOCH']
            tle_line1 = row['TLE_LINE1']
            tle_line2 = row['TLE_LINE2']
            
            # Parse epoch date
            try:
                epoch_date = datetime.fromisoformat(epoch_str.replace('T', ' ').split('.')[0])
            except:
                continue
            
            if norad_id not in tle_by_satellite:
                tle_by_satellite[norad_id] = []
            
            tle_by_satellite[norad_id].append({
                'epoch_date': epoch_date,
                'tle': f"{tle_line1}\n{tle_line2}"
            })
        
        print(f'\n✅ Parsed {sum(len(v) for v in tle_by_satellite.values())} TLE records')
        print(f'   For {len(tle_by_satellite)} satellites\n')
        
        # Import into database
        total_added = 0
        for norad_id, tle_list in tle_by_satellite.items():
            try:
                satellite = Satellite.objects.get(norad_id=norad_id)
                
                # Sort by epoch date (oldest first)
                tle_list.sort(key=lambda x: x['epoch_date'])
                
                added_count = 0
                for tle_data in tle_list:
                    # Check if this epoch already exists
                    exists = TLE.objects.filter(
                        satellite=satellite,
                        epoch_date=tle_data['epoch_date']
                    ).exists()
                    
                    if not exists:
                        tle_obj = TLE(
                            satellite=satellite,
                            tle=tle_data['tle'],
                            epoch_date=tle_data['epoch_date']
                        )
                        tle_obj.save()
                        added_count += 1
                
                if added_count > 0:
                    total_added += added_count
                    print(f'✅ {satellite.name} ({norad_id}): Added {added_count} TLE records')
                    
            except Satellite.DoesNotExist:
                continue
        
        print(f'\n📊 Total TLE records added: {total_added}')
        
        # Show satellites with most TLE history
        print('\n🏆 Top satellites by TLE history count:')
        from django.db.models import Count
        top_sats = Satellite.objects.annotate(
            tle_count=Count('tle')
        ).filter(tle_count__gt=0).order_by('-tle_count')[:10]
        
        for sat in top_sats:
            print(f'   {sat.name} ({sat.norad_id}): {sat.tle_count} records')

except FileNotFoundError:
    print('❌ datac.csv not found in current directory')
except Exception as e:
    print(f'❌ Error: {e}')
    import traceback
    traceback.print_exc()
