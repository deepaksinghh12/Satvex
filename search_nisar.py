#!/usr/bin/env python
"""Search for NISAR satellite in various TLE sources"""
import requests
import sqlite3

def search_celestrak():
    """Search Celestrak for NISAR"""
    print("🔍 Searching Celestrak for NISAR...")
    try:
        url = 'https://celestrak.org/NORAD/elements/gp.php?GROUP=active&FORMAT=tle'
        response = requests.get(url, timeout=15)
        lines = response.text.strip().split('\n')
        
        i = 0
        while i < len(lines) - 2:
            name = lines[i].strip()
            tle1 = lines[i+1].strip()
            tle2 = lines[i+2].strip()
            
            if 'NISAR' in name.upper():
                print(f"✅ Found in Celestrak: {name}")
                norad_id = tle1.split()[1][:5]
                return name, tle1, tle2, norad_id
            i += 3
        
        print("❌ NISAR not found in Celestrak active satellites")
        return None
    except Exception as e:
        print(f"⚠️ Error searching Celestrak: {e}")
        return None

def search_n2yo(api_key='M8PZCZ-5ELM7M-DE5LRK-531A'):
    """Search N2YO for NISAR-related satellites"""
    print("\n🔍 Searching N2YO for Indian satellites (NISAR may be listed)...")
    try:
        # Search for recently launched satellites
        url = f'https://api.n2yo.com/rest/v1/satellite/above/20/77/0/90/0/&apiKey={api_key}'
        response = requests.get(url, timeout=10)
        data = response.json()
        
        if 'above' in data:
            for sat in data['above']:
                if 'NISAR' in sat.get('satname', '').upper():
                    print(f"✅ Found: {sat['satname']} (NORAD ID: {sat['satid']})")
                    return sat['satid'], sat['satname']
        
        print("❌ NISAR not found in N2YO visible satellites")
        return None
    except Exception as e:
        print(f"⚠️ Error searching N2YO: {e}")
        return None

def add_nisar_to_db(norad_id, name, tle1, tle2):
    """Add NISAR to the database"""
    print(f"\n➕ Adding {name} to database...")
    try:
        conn = sqlite3.connect('db.sqlite3')
        cursor = conn.cursor()
        
        tle_text = f"{tle1}\n{tle2}"
        
        # Extract orbital parameters from TLE
        inclination = float(tle2.split()[2])
        period = 1440.0 / float(tle2.split()[7][:11])  # Minutes per orbit
        
        from datetime import datetime
        today = datetime.now().strftime('%Y-%m-%d')
        
        orbits_per_day = int(float(tle2.split()[7][:11]))
        
        cursor.execute('''
            INSERT INTO satTrack_satellite 
            (norad_id, name, satellite_type, description, tle_now, launch_date, 
             launch_site, last_tle_update, swath, status, orbit, orbital_period, 
             orbit_revisit, orbit_distance, orbits_per_day, inclination, perigee, apogee)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            norad_id, 
            name, 
            'Earth Observation',
            'NASA-ISRO SAR mission for Earth observation with L-band and S-band SAR',
            tle_text, 
            '2025-06-12',  # Approximate launch date
            'Satish Dhawan Space Centre, India',
            today,
            240.0,  # NISAR swath width ~240 km
            'Active',
            'Sun-Synchronous',
            round(period, 2),
            12,  # NISAR orbit revisit in days
            747.0,  # Approximate orbit altitude in km
            orbits_per_day,
            round(inclination, 2),
            730.0,  # Approximate perigee in km
            765.0   # Approximate apogee in km
        ))
        
        conn.commit()
        conn.close()
        
        print(f"✅ Successfully added {name} (NORAD ID: {norad_id}) to database!")
        return True
    except Exception as e:
        print(f"⚠️ Error adding to database: {e}")
        return False

if __name__ == '__main__':
    print("🛰️  NISAR Satellite Search\n" + "="*50 + "\n")
    
    result = search_celestrak()
    
    if result:
        name, tle1, tle2, norad_id = result
        print(f"\n📡 NISAR Details:")
        print(f"   Name: {name}")
        print(f"   NORAD ID: {norad_id}")
        print(f"   TLE Line 1: {tle1}")
        print(f"   TLE Line 2: {tle2}")
        
        add_nisar_to_db(norad_id, name, tle1, tle2)
    else:
        print("\n📋 NISAR Status:")
        print("   Launch: Scheduled for 2025 (exact date TBD)")
        print("   Status: Not yet in orbit")
        print("   Note: NISAR will be added to tracking databases after launch")
        print("\n💡 Alternative: Use manual location feature to fetch imagery from Indian coordinates")
