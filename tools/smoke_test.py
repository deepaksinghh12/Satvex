import urllib.request
urls = [
    'http://localhost:8000/',
    'http://localhost:8000/sat',
    'http://localhost:8000/about',
    'http://localhost:8000/pass-predictor',
    'http://localhost:8000/comparison',
    'http://localhost:8000/tle-comparison',
    'http://localhost:8000/test-bhuvan',
    'http://localhost:8000/api/satellites/list',
    'http://localhost:8000/static/css/home.css',
    'http://localhost:8000/sat/25544',
]
for u in urls:
    try:
        req = urllib.request.Request(u, headers={'User-Agent':'smoke-test/1.0'})
        with urllib.request.urlopen(req, timeout=10) as r:
            print(f"{u} -> {r.status} {r.getheader('Content-Type')!s} ({r.length if hasattr(r,'length') else 'len=?'})")
    except Exception as e:
        print(f"{u} -> ERROR: {e}")
