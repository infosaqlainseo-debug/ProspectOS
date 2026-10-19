import urllib.request
import urllib.parse
import json

query = """
SELECT DISTINCT ?company ?companyLabel ?website ?locationLabel ?industryLabel WHERE {
  ?company wdt:P31/wdt:P279* wd:Q783794.
  ?company wdt:P856 ?website.
  ?company wdt:P159 ?location.
  ?location wdt:P131* wd:Q1612. # in Texas
  ?company wdt:P452 ?industry.
  ?industry wdt:P279* wd:Q11661. # technology industry
  SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
} LIMIT 5
"""

url = "https://query.wikidata.org/sparql?query=" + urllib.parse.quote(query)
req = urllib.request.Request(url, headers={'User-Agent': 'ProspectOS/1.0', 'Accept': 'application/sparql-results+json'})
with urllib.request.urlopen(req) as response:
    data = json.loads(response.read())
    print(json.dumps(data['results']['bindings'], indent=2))
