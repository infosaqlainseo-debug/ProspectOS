import urllib.request
import json
url = "https://autocomplete.clearbit.com/v1/companies/suggest?query=technology"
req = urllib.request.Request(url, headers={'User-Agent': 'ProspectOS/1.0'})
with urllib.request.urlopen(req) as r:
    data = json.loads(r.read())
    for d in data[:5]:
        print(d['name'], d['domain'])
