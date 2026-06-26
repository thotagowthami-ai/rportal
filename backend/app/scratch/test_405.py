import urllib.request
import urllib.error
try:
    urllib.request.urlopen("https://recruitcore-production.up.railway.app/api/api/linkedin/callback")
except urllib.error.HTTPError as e:
    print(e.code, e.read().decode())
