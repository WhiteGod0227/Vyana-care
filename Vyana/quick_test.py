import requests

tests = [
    ('GET', 'http://127.0.0.1:8000/health'),
    ('GET', 'http://127.0.0.1:8000/patient/1'),
    ('GET', 'http://127.0.0.1:8000/asha/1/patients'),
]

for method, url in tests:
    try:
        r = requests.get(url, timeout=3)
        print(f'{method} {url}: {r.status_code}')
    except Exception as e:
        print(f'{method} {url}: ERROR - {str(e)[:50]}')
