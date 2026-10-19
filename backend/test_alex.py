import urllib.request
import json
url = "https://api.openalex.org/institutions?search=technology+texas&filter=type:company"
req = urllib.request.Request(url, headers={'User-Agent': 'ProspectOS/1.0'})
with urllib.request.urlopen(req) as r:
    data = json.loads(r.read())
    for d in data['results'][:5]:
        print(d['display_name'], d.get('homepage_url'))
