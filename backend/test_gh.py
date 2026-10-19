import urllib.request
import json
url = "https://api.github.com/search/users?q=type:org+location:Texas+technology"
req = urllib.request.Request(url, headers={'User-Agent': 'ProspectOS/1.0'})
with urllib.request.urlopen(req) as r:
    data = json.loads(r.read())
    for org in data['items'][:5]:
        org_url = org['url']
        req2 = urllib.request.Request(org_url, headers={'User-Agent': 'ProspectOS/1.0'})
        with urllib.request.urlopen(req2) as r2:
            org_data = json.loads(r2.read())
            print(org_data.get('name'), org_data.get('blog'))
