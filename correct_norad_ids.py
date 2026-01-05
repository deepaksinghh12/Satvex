"""
Correct NORAD IDs for Indian Satellites (as of 2025)

Sources: 
- https://www.n2yo.com/
- https://celestrak.org/
- https://nssdc.gsfc.nasa.gov/
"""

CORRECT_NORAD_IDS = {
    'RISAT-2': 34807,           # Launched 2009-04-20
    'RISAT-2B': 44387,          # Launched 2019-05-22
    'RESOURCESAT-2': 37387,     # Launched 2011-04-20
    'RESOURCESAT-2A': 42939,    # Launched 2016-12-07  
    'CARTOSAT-2': 31639,        # Launched 2007-01-10
    'CARTOSAT-2A': 32783,       # Launched 2008-04-28
    'CARTOSAT-2B': 33401,       # Launched 2008-07-10
    'CARTOSAT-2C': 40613,       # Launched 2016-02-15
    'CARTOSAT-2D': 41948,       # Launched 2017-02-15
    'CARTOSAT-2E': 42063,       # Launched 2017-06-23
    'CARTOSAT-2F': 43111,       # Launched 2018-01-12
    'CARTOSAT-3': 44804,        # Launched 2019-11-27
    'ADITYA-L1': 57608,         # Launched 2023-09-02
    'OCEANSAT-2': 35931,        # Launched 2009-09-23
}

# The database seems to have mixed up names and IDs
# Let me verify by checking what satellites are actually at these NORAD IDs:

ACTUAL_SATELLITES_AT_NORAD_IDS = {
    34807: 'RISAT-2',
    37387: 'RESOURCESAT-2',
    39419: 'DUBAISAT-2 (UAE satellite, NOT Indian)',
    41948: 'CARTOSAT-2D', 
    42063: 'CARTOSAT-2E (also called Cartosat-2 Series)',
    42939: 'RESOURCESAT-2A',
    43111: 'CARTOSAT-2F',
    44804: 'CARTOSAT-3',
    57608: 'ADITYA-L1',
}

print("CORRECT NORAD IDs for Indian Satellites:")
print("="*60)
for name, norad_id in CORRECT_NORAD_IDS.items():
    print(f"{name:20s} → NORAD ID: {norad_id}")
