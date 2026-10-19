import urllib.request
import json
url = "https://en.wikipedia.org/w/api.php?action=query&prop=extlinks&titles=Texas_Instruments&ellimit=5&format=json"
req = urllib.request.Request(url, headers={'User-Agent': 'ProspectOS/1.0'})
with urllib.request.urlopen(req) as r:
    print(json.loads(r.read())['query']['pages'])
