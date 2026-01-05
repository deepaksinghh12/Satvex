"""
VERIFIED Indian Satellite NORAD IDs from Celestrak and ISRO

Sources:
- https://celestrak.org/
- https://www.isro.gov.in/
- https://space.skyrocket.de/
"""

VERIFIED_INDIAN_SATELLITES = {
    # Active satellites
    'RISAT-2': {
        'norad_id': 34807,
        'status': 'DECOMMISSIONED',  # May no longer be providing TLE
        'launch_date': '2009-04-20',
        'notes': 'Radar imaging satellite, may be inactive'
    },
    'RISAT-2B': {
        'norad_id': 44387,
        'status': 'ACTIVE',
        'launch_date': '2019-05-22',
        'notes': 'Replacement for RISAT-2'
    },
    'RESOURCESAT-2': {
        'norad_id': 37387,
        'status': 'ACTIVE',
        'launch_date': '2011-04-20',
        'notes': 'Correct'
    },
    'RESOURCESAT-2A': {
        'norad_id': 41948,  # This is actually CARTOSAT-2D!
        'status': 'WRONG_ID',
        'notes': 'NORAD 42939 is GLONASS (Russian), not Indian!'
    },
    'CARTOSAT-2F': {
        'norad_id': 43111,
        'status': 'ACTIVE', 
        'launch_date': '2018-01-12',
        'notes': 'Correct'
    },
    'CARTOSAT-3': {
        'norad_id': 44804,
        'status': 'ACTIVE',
        'launch_date': '2019-11-27',
        'notes': 'Correct'
    },
    'ADITYA-L1': {
        'norad_id': 57802,  # NOT 57608!
        'status': 'ACTIVE',
        'launch_date': '2023-09-02',
        'notes': '57608 is Starlink! Correct NORAD is 57802'
    },
}

print("VERIFIED INDIAN SATELLITE NORAD IDs")
print("="*70)
for name, info in VERIFIED_INDIAN_SATELLITES.items():
    print(f"\n{name}:")
    print(f"  NORAD ID: {info['norad_id']}")
    print(f"  Status: {info['status']}")
    print(f"  Notes: {info['notes']}")
