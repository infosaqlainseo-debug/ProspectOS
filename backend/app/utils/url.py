import urllib.parse
import tldextract

def normalize_url(url: str) -> str | None:
    if not url:
        return None
    try:
        lower_url = url.lower()
        if not lower_url.startswith('http://') and not lower_url.startswith('https://'):
            url = 'https://' + url
            
        parsed = urllib.parse.urlparse(url)
        scheme = parsed.scheme.lower()
        netloc = parsed.netloc.lower()
        
        # Remove default ports
        if scheme == 'http' and netloc.endswith(':80'):
            netloc = netloc[:-3]
        elif scheme == 'https' and netloc.endswith(':443'):
            netloc = netloc[:-4]
            
        path = parsed.path
        if not path:
            path = '/'
            
        return f"{scheme}://{netloc}{path}"
    except Exception:
        return None

def extract_canonical_domain(url: str) -> str | None:
    if not url:
        return None
    try:
        extracted = tldextract.extract(url)
        
        if not extracted.domain or not extracted.suffix:
            return None
            
        subdomain = extracted.subdomain.lower()
        if subdomain == 'www':
            subdomain = ''
            
        parts = []
        if subdomain:
            parts.append(subdomain)
        parts.append(extracted.domain.lower())
        parts.append(extracted.suffix.lower())
        
        return '.'.join(parts)
    except Exception:
        return None
