from app.utils.url import normalize_url, extract_canonical_domain

def test_normalize_url():
    assert normalize_url("example.com") == "https://example.com/"
    assert normalize_url("http://example.com:80/path") == "http://example.com/path"
    assert normalize_url("https://example.com:443") == "https://example.com/"
    assert normalize_url("HTTPS://Example.COM") == "https://example.com/"

def test_extract_canonical_domain():
    assert extract_canonical_domain("https://www.example.com") == "example.com"
    assert extract_canonical_domain("http://shop.example.com/path") == "shop.example.com"
    assert extract_canonical_domain("https://example.co.uk") == "example.co.uk"
    assert extract_canonical_domain("invalid-url") is None
