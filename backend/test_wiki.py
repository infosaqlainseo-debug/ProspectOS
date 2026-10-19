import urllib.request
import json
import urllib.parse
query = urllib.parse.quote("technology companies based in Texas")
url = f"https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch={query}&utf8=&format=json"
req = urllib.request.Request(url, headers={'User-Agent': 'ProspectOS/1.0'})
with urllib.request.urlopen(req) as r:
    print(json.loads(r.read())['query']['search'])
