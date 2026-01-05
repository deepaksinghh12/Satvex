import os
import django
from datetime import datetime, timedelta

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from satTrack.models import Satellite

def datetime_from_epoch(epoch_str):
    """Convert TLE epoch to datetime"""
    year = int('20' + epoch_str[:2])  # Assuming 20xx
    day_of_year = float(epoch_str[2:])
    date = datetime(year, 1, 1) + timedelta(days=day_of_year - 1)
    return date

print("\n" + "="*80)
print("TLE DATA FRESHNESS CHECK")
print("="*80 + "\n")

satellites = Satellite.objects.all()

for sat in satellites:
    if sat.tle_now:
        lines = sat.tle_now.strip().split('\n')
        if len(lines) >= 2:
            line1 = lines[0]
            # Epoch is at positions 18-32 in line 1
            epoch_str = line1[18:32].strip()
            
            try:
                tle_date = datetime_from_epoch(epoch_str)
                age_days = (datetime.now() - tle_date).days
                
                status = "✅ FRESH" if age_days < 7 else "⚠️ OLD" if age_days < 30 else "❌ VERY OLD"
                
                print(f"{sat.name:20} | TLE Date: {tle_date.strftime('%Y-%m-%d')} | Age: {age_days:3} days | {status}")
            except Exception as e:
                print(f"{sat.name:20} | ERROR parsing TLE: {e}")
    else:
        print(f"{sat.name:20} | ❌ NO TLE DATA")

print("\n" + "="*80)
print("RECOMMENDATION:")
print("  - TLE < 7 days old: Excellent accuracy")
print("  - TLE 7-30 days old: Acceptable, but update recommended")
print("  - TLE > 30 days old: Poor accuracy, UPDATE REQUIRED!")
print("="*80 + "\n")

print("To update TLE data, run: python fetch_tle_data.py")
