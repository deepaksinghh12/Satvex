import requests

# Try to find Aditya-L1 in Celestrak supplemental data
def search_aditya_l1():
    print("Searching for Aditya-L1...")
    
    # Aditya-L1 is in a halo orbit around L1, might be in special category
    celestrak_groups = [
        'supplemental',
        'geo',
        'science',
        'weather'
    ]
    
    for group in celestrak_groups:
        try:
            url = f"https://celestrak.org/NORAD/elements/gp.php?GROUP={group}&FORMAT=TLE"
            response = requests.get(url, timeout=10)
            
            if 'ADITYA' in response.text.upper():
                print(f"\n✓ Found in {group} group!")
                lines = response.text.split('\n')
                for i, line in enumerate(lines):
                    if 'ADITYA' in line.upper():
                        print(f"Line {i}: {line}")
                        if i + 2 < len(lines):
                            print(f"TLE Line 1: {lines[i+1]}")
                            print(f"TLE Line 2: {lines[i+2]}")
                        break
        except Exception as e:
            print(f"Error checking {group}: {e}")
    
    # Manual check - Aditya-L1 NORAD ID from launch records
    print("\n" + "="*70)
    print("Aditya-L1 Launch Info:")
    print("  Launch Date: September 2, 2023")
    print("  Launch Vehicle: PSLV-C57")
    print("  Mission: Solar observation at L1 point")
    print("\n  Possible NORAD IDs to try:")
    print("  - 57608 (tried, is Starlink)")
    print("  - 57802 (tried, no TLE)")
    print("  - 57693 (PSLV DEB)")
    print("  - Let's try 57693...")
    
    # Try 57693
    try:
        params = {'CATNR': 57693, 'FORMAT': 'TLE'}
        response = requests.get("https://celestrak.org/NORAD/elements/gp.php", params=params)
        if response.status_code == 200 and len(response.text) > 50:
            print(f"\n  ✓ Found TLE for NORAD 57693:")
            print(response.text)
    except:
        pass

if __name__ == "__main__":
    search_aditya_l1()
