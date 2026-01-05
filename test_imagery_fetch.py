#!/usr/bin/env python
"""Test fetching imagery from satellite currently over India"""
import requests

# RANGE-A current position over India
lat = 20.6399
lon = 86.8413

print('🛰️  Testing Imagery Fetch from RANGE-A')
print('='*60)
print(f'📍 Position: Lat {lat}°, Lon {lon}° (over Odisha, India)')
print()

# Test location imagery API with proper GET parameters
params = {
    'lat': lat,
    'lon': lon,
    'layer': 'india3'
}
url = 'http://127.0.0.1:8000/api/location/imagery'
print(f'🔗 URL: {url}')
print(f'📝 Params: {params}')
print('⏳ Fetching imagery...\n')

try:
    headers = {'X-Requested-With': 'XMLHttpRequest'}
    response = requests.get(url, params=params, headers=headers, timeout=15)
    
    print(f'📊 Response:')
    print(f'   Status Code: {response.status_code}')
    print(f'   Content-Type: {response.headers.get("Content-Type")}')
    print(f'   Size: {len(response.content):,} bytes ({len(response.content)/1024:.2f} KB)')
    
    if response.status_code == 200:
        print(f'\n✅ SUCCESS! Imagery fetched successfully!')
        print(f'\n🌐 View in browser:')
        print(f'   Satellite page: http://127.0.0.1:8000/sat/43773/imagery')
        print(f'   Manual location: http://127.0.0.1:8000/imagery')
        
        # Save image to verify
        with open('test_imagery.png', 'wb') as f:
            f.write(response.content)
        print(f'\n💾 Saved test image as: test_imagery.png')
    else:
        print(f'\n⚠️ Error Response:')
        print(response.text[:500])
        
except Exception as e:
    print(f'❌ Error: {e}')
