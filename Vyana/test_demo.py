import requests

r = requests.get('http://127.0.0.1:8001/asha/1/patients', timeout=3)
print(f'Status: {r.status_code}')
if r.status_code == 200:
    data = r.json()
    if 'data' in data and 'patients' in data['data']:
        patients = data['data']['patients']
        print(f'Patients: {len(patients)}')
        for p in patients[:3]:
            print(f"  - {p.get('name', 'Unknown')}")
    else:
        print('Response structure:', list(data.keys()) if isinstance(data, dict) else 'not dict')
else:
    print('Error:', r.text[:200])
