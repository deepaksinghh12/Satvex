import csv

with open('satellite_data_20251206_230903.csv', 'r') as f:
    reader = csv.DictReader(f)
    rows = list(reader)

print(f'✅ Total records: {len(rows)}\n')
print('📡 Satellites included:\n')

for i, r in enumerate(rows, 1):
    print(f'{i}. {r["OBJECT_NAME"]} (NORAD {r["NORAD_CAT_ID"]})')
    print(f'   Epoch: {r["EPOCH"][:10]}')
    print(f'   Inclination: {r["INCLINATION"]}° | Period: {r["PERIOD"]} min')
    print(f'   Altitude: {r["PERIAPSIS"]}-{r["APOAPSIS"]} km')
    print()
