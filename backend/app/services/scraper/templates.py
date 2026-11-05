from typing import Dict, Any, List

SCRAPER_TEMPLATES: List[Dict[str, Any]] = [
    {
        "id": "business-directory-extractor",
        "name": "Business Directory Extractor",
        "description": "Extract structured business profiles, company names, contact phone, website URLs, and physical addresses from commercial directory listings.",
        "category": "Lead Generation",
        "data_source": "Public Commercial Directories & Listing Catalogs",
        "required_credentials": "None (operates on publicly accessible directory catalogs)",
        "limitations": "Subject to directory rate limits. Respects robots.txt directives.",
        "input_parameters": [
            {"key": "directory_url", "label": "Directory URL", "type": "url", "default": "https://www.yellowpages.com/search?search_terms=ecommerce&geo_location_terms=Mexico", "required": True},
            {"key": "category", "label": "Industry Category", "type": "text", "default": "E-commerce & Retail", "required": False},
            {"key": "max_records", "label": "Max Records", "type": "number", "default": 50, "required": True}
        ],
        "output_fields": ["company_name", "website", "phone", "address", "category", "source_url"],
        "example_output": {
            "_sample_notice": "SAMPLE PREVIEW ONLY",
            "company_name": "Kavak Mexico",
            "website": "https://www.kavak.com/mx",
            "phone": "+52 55 5000 0000",
            "address": "Av. Vasco de Quiroga 3900, Santa Fe, Mexico City",
            "category": "E-commerce / Automotive",
            "source_url": "https://www.yellowpages.com/search?search_terms=ecommerce"
        },
        "workflow_config": {
            "container_selector": ".result, .business-card, .listing-item",
            "fields": [
                {"name": "company_name", "selector": "h2.business-name, .title, h3", "type": "text", "attribute": "text"},
                {"name": "website", "selector": "a.track-visit-website, a[href*='http']", "type": "link", "attribute": "href"},
                {"name": "phone", "selector": ".phone, a[href^='tel:']", "type": "text", "attribute": "text"},
                {"name": "address", "selector": ".street-address, .address, .adr", "type": "text", "attribute": "text"},
                {"name": "category", "selector": ".categories, .category", "type": "text", "attribute": "text"}
            ],
            "pagination": {"type": "NEXT_BUTTON", "selector": "a.next, .pagination .next", "max_pages": 5}
        }
    },
    {
        "id": "google-search-results-extractor",
        "name": "Google Search Results Extractor",
        "description": "Extract organic search results, company domains, titles, and meta snippets from public search queries.",
        "category": "Search & Maps",
        "data_source": "Public Search Engine Results (SERP / Authorized Search API)",
        "required_credentials": "None for standard queries or configure SerpAPI / Google Custom Search in Settings",
        "limitations": "Direct scraping of commercial search engines is subject to bot verification; configured search API is recommended for high volume.",
        "input_parameters": [
            {"key": "search_query", "label": "Search Query", "type": "text", "default": "ecommerce companies in Mexico online store", "required": True},
            {"key": "num_results", "label": "Target Results", "type": "number", "default": 50, "required": True}
        ],
        "output_fields": ["company_name", "website", "domain", "description", "source_url"],
        "example_output": {
            "_sample_notice": "SAMPLE PREVIEW ONLY",
            "company_name": "Gaia Design - Muebles y Decoración",
            "website": "https://www.gaiadesign.com.mx",
            "domain": "gaiadesign.com.mx",
            "description": "Tienda en línea de muebles de diseño moderno para el hogar y oficina en México.",
            "source_url": "https://www.google.com/search?q=ecommerce+companies+in+mexico"
        },
        "workflow_config": {
            "container_selector": "div.g, div[data-hveid], .result",
            "fields": [
                {"name": "company_name", "selector": "h3", "type": "text", "attribute": "text"},
                {"name": "website", "selector": "a[href^='http']", "type": "link", "attribute": "href"},
                {"name": "description", "selector": "div[style*='-webkit-line-clamp'], .VwiC3b, .snippet", "type": "text", "attribute": "text"}
            ],
            "pagination": {"type": "NEXT_BUTTON", "selector": "#pnnext, a[aria-label='Next page']", "max_pages": 5}
        }
    },
    {
        "id": "google-maps-lead-extractor",
        "name": "Google Maps Business Lead Extractor",
        "description": "Extract local business listings, company name, address, phone numbers, rating, and website links for regional prospect discovery.",
        "category": "Search & Maps",
        "data_source": "Authorized Places / Public Maps Local Listings",
        "required_credentials": "Google Maps Platform API key recommended in Settings for high volume",
        "limitations": "Browser automation extracts available public cards with bounded concurrency.",
        "input_parameters": [
            {"key": "search_location", "label": "Location & Industry", "type": "text", "default": "Digital marketing agencies in Dubai", "required": True},
            {"key": "max_records", "label": "Max Listings", "type": "number", "default": 40, "required": True}
        ],
        "output_fields": ["company_name", "website", "phone", "address", "city", "country"],
        "example_output": {
            "_sample_notice": "SAMPLE PREVIEW ONLY",
            "company_name": "Gulf Digital Marketing Group",
            "website": "https://www.gulfdigital.ae",
            "phone": "+971 4 300 0000",
            "address": "Business Bay, Tower 1, Dubai",
            "city": "Dubai",
            "country": "United Arab Emirates"
        },
        "workflow_config": {
            "container_selector": "div[role='article'], .Nv2PK, .maps-card",
            "fields": [
                {"name": "company_name", "selector": ".qBF1Pd, .fontHeadlineSmall", "type": "text", "attribute": "text"},
                {"name": "website", "selector": "a[data-value='Website'], a.lcr4fd", "type": "link", "attribute": "href"},
                {"name": "phone", "selector": ".UsdlK, [data-tooltip*='Phone']", "type": "text", "attribute": "text"},
                {"name": "address", "selector": ".W4Efsd:last-child", "type": "text", "attribute": "text"}
            ]
        }
    },
    {
        "id": "ecommerce-product-extractor",
        "name": "E-commerce Product Extractor",
        "description": "Extract products, prices, SKUs, inventory status, descriptions, and product image links from online stores.",
        "category": "E-commerce",
        "data_source": "Public E-commerce Storefronts (Shopify, WooCommerce, Magento)",
        "required_credentials": "None",
        "limitations": "Respects store rate limits and terms of service.",
        "input_parameters": [
            {"key": "catalog_url", "label": "Catalog / Collection URL", "type": "url", "default": "https://example-shop.com/collections/all", "required": True},
            {"key": "max_items", "label": "Max Items", "type": "number", "default": 100, "required": True}
        ],
        "output_fields": ["title", "price", "product_url", "image_url", "description", "availability"],
        "example_output": {
            "_sample_notice": "SAMPLE PREVIEW ONLY",
            "title": "Ergonomic Office Chair - Model X",
            "price": "$299.00 USD",
            "product_url": "https://example-shop.com/products/chair-x",
            "image_url": "https://example-shop.com/cdn/chair.jpg",
            "description": "High-back breathable mesh chair with lumbar support.",
            "availability": "In Stock"
        },
        "workflow_config": {
            "container_selector": ".product-card, .grid-product, .product-item",
            "fields": [
                {"name": "title", "selector": ".product-title, h3, .card__heading", "type": "text", "attribute": "text"},
                {"name": "price", "selector": ".price, .money, .price-item", "type": "text", "attribute": "text"},
                {"name": "product_url", "selector": "a[href*='/products/']", "type": "link", "attribute": "href"},
                {"name": "image_url", "selector": "img", "type": "image", "attribute": "src"}
            ],
            "pagination": {"type": "NEXT_BUTTON", "selector": "a.pagination__next, .next-page", "max_pages": 4}
        }
    },
    {
        "id": "company-website-info-extractor",
        "name": "Company Website Information Extractor",
        "description": "Deep crawl of a target company homepage to extract brand title, meta descriptions, headings, company contacts, and canonical domain.",
        "category": "Company Intelligence",
        "data_source": "Target Company Web Properties",
        "required_credentials": "None",
        "limitations": "Does not bypass anti-bot protections; records status if access restricted.",
        "input_parameters": [
            {"key": "target_url", "label": "Company Website URL", "type": "url", "default": "https://luuna.mx", "required": True}
        ],
        "output_fields": ["company_name", "website", "domain", "description", "phone", "email", "address"],
        "example_output": {
            "_sample_notice": "SAMPLE PREVIEW ONLY",
            "company_name": "Luuna Colchones y Almohadas",
            "website": "https://luuna.mx",
            "domain": "luuna.mx",
            "description": "Colchones de alta densidad, almohadas y blancos con entrega a todo México.",
            "phone": "+52 55 4164 0533",
            "email": "hola@luuna.mx",
            "address": "Ciudad de México, México"
        },
        "workflow_config": {
            "container_selector": "body",
            "fields": [
                {"name": "company_name", "selector": "h1, .navbar-brand, title", "type": "text", "attribute": "text"},
                {"name": "description", "selector": "meta[name='description']", "type": "text", "attribute": "content"},
                {"name": "phone", "selector": "a[href^='tel:']", "type": "text", "attribute": "text"},
                {"name": "email", "selector": "a[href^='mailto:']", "type": "text", "attribute": "text"}
            ]
        }
    },
    {
        "id": "contact-page-extractor",
        "name": "Contact Page Extractor",
        "description": "Targeted extractor for '/contact', '/about-us', and '/contact-us' pages to extract public email, direct phone, and physical office locations.",
        "category": "Company Intelligence",
        "data_source": "Public Company Contact Pages",
        "required_credentials": "None",
        "limitations": "Operates on public contact pages only. Does not solve CAPTCHAs or contact forms.",
        "input_parameters": [
            {"key": "contact_url", "label": "Contact Page URL", "type": "url", "default": "https://example.com/contact-us", "required": True}
        ],
        "output_fields": ["company_name", "email", "phone", "address", "source_url"],
        "example_output": {
            "_sample_notice": "SAMPLE PREVIEW ONLY",
            "company_name": "Acme Global Solutions",
            "email": "info@acmeglobal.com",
            "phone": "+1 (800) 555-0199",
            "address": "100 Innovation Way, Suite 400, Austin, TX",
            "source_url": "https://example.com/contact-us"
        },
        "workflow_config": {
            "container_selector": "main, .contact-content, body",
            "fields": [
                {"name": "email", "selector": "a[href^='mailto:'], [class*='email']", "type": "text", "attribute": "text"},
                {"name": "phone", "selector": "a[href^='tel:'], [class*='phone']", "type": "text", "attribute": "text"},
                {"name": "address", "selector": "address, [class*='address']", "type": "text", "attribute": "text"}
            ]
        }
    },
    {
        "id": "public-business-social-links-extractor",
        "name": "Public Business Social Links Extractor",
        "description": "Inspects website headers, footers, and contact sections to discover official LinkedIn, Instagram, Facebook, X/Twitter, and WhatsApp channels.",
        "category": "Company Intelligence",
        "data_source": "Company Website Public DOM",
        "required_credentials": "None",
        "limitations": "Only discovers public links embedded on the website.",
        "input_parameters": [
            {"key": "website_url", "label": "Website URL", "type": "url", "default": "https://benandfrank.com", "required": True}
        ],
        "output_fields": ["website", "linkedin_url", "instagram_url", "facebook_url", "twitter_url", "whatsapp_url"],
        "example_output": {
            "_sample_notice": "SAMPLE PREVIEW ONLY",
            "website": "https://benandfrank.com",
            "linkedin_url": "https://www.linkedin.com/company/ben-and-frank",
            "instagram_url": "https://www.instagram.com/benandfrank.mx",
            "facebook_url": "https://www.facebook.com/benandfrankmx",
            "twitter_url": "https://twitter.com/benandfrank",
            "whatsapp_url": "https://wa.me/525500000000"
        },
        "workflow_config": {
            "container_selector": "footer, header, body",
            "fields": [
                {"name": "linkedin_url", "selector": "a[href*='linkedin.com']", "type": "link", "attribute": "href"},
                {"name": "instagram_url", "selector": "a[href*='instagram.com']", "type": "link", "attribute": "href"},
                {"name": "facebook_url", "selector": "a[href*='facebook.com']", "type": "link", "attribute": "href"},
                {"name": "twitter_url", "selector": "a[href*='twitter.com'], a[href*='x.com']", "type": "link", "attribute": "href"},
                {"name": "whatsapp_url", "selector": "a[href*='wa.me'], a[href*='whatsapp.com']", "type": "link", "attribute": "href"}
            ]
        }
    },
    {
        "id": "job-listing-extractor",
        "name": "Job Listing Extractor",
        "description": "Extract open job positions, hiring companies, employment locations, salary mentions, and application URLs from career boards.",
        "category": "Real Estate & Jobs",
        "data_source": "Public Company Careers & Job Board Portals",
        "required_credentials": "None",
        "limitations": "Extracts publicly listed postings.",
        "input_parameters": [
            {"key": "careers_url", "label": "Careers URL", "type": "url", "default": "https://boards.greenhouse.io/example", "required": True},
            {"key": "max_jobs", "label": "Max Job Listings", "type": "number", "default": 50, "required": True}
        ],
        "output_fields": ["job_title", "company_name", "location", "department", "apply_url"],
        "example_output": {
            "_sample_notice": "SAMPLE PREVIEW ONLY",
            "job_title": "Senior SEO Strategist",
            "company_name": "Apex Digital",
            "location": "Remote / New York, NY",
            "department": "Growth Marketing",
            "apply_url": "https://boards.greenhouse.io/apex/jobs/12345"
        },
        "workflow_config": {
            "container_selector": ".opening, .job-listing, .career-item",
            "fields": [
                {"name": "job_title", "selector": "a[data-mapped='true'], h4, .title", "type": "text", "attribute": "text"},
                {"name": "location", "selector": ".location", "type": "text", "attribute": "text"},
                {"name": "department", "selector": ".department", "type": "text", "attribute": "text"},
                {"name": "apply_url", "selector": "a", "type": "link", "attribute": "href"}
            ]
        }
    },
    {
        "id": "real-estate-listing-extractor",
        "name": "Real Estate Listing Extractor",
        "description": "Extract property listings, prices, square footage, bedroom counts, broker contacts, and listing URLs from real estate portals.",
        "category": "Real Estate & Jobs",
        "data_source": "Public Real Estate Listings & Broker Portals",
        "required_credentials": "None",
        "limitations": "Bounded crawling of public listings.",
        "input_parameters": [
            {"key": "listings_url", "label": "Real Estate Listings URL", "type": "url", "default": "https://www.inmuebles24.com/casas-en-venta-en-cdmx.html", "required": True},
            {"key": "max_properties", "label": "Max Properties", "type": "number", "default": 40, "required": True}
        ],
        "output_fields": ["title", "price", "location", "property_type", "listing_url"],
        "example_output": {
            "_sample_notice": "SAMPLE PREVIEW ONLY",
            "title": "Casa en Venta en Polanco con Terraza",
            "price": "$14,500,000 MXN",
            "location": "Polanco, Miguel Hidalgo, CDMX",
            "property_type": "Casa Residencial",
            "listing_url": "https://www.inmuebles24.com/propiedades/casa-polanco-123.html"
        },
        "workflow_config": {
            "container_selector": ".posting-card, .property-card, article",
            "fields": [
                {"name": "title", "selector": ".posting-title, h2, h3", "type": "text", "attribute": "text"},
                {"name": "price", "selector": ".first-price, .price", "type": "text", "attribute": "text"},
                {"name": "location", "selector": ".posting-location, .location", "type": "text", "attribute": "text"},
                {"name": "listing_url", "selector": "a", "type": "link", "attribute": "href"}
            ]
        }
    },
    {
        "id": "news-and-article-extractor",
        "name": "News and Article Extractor",
        "description": "Extract headlines, author names, publication timestamps, article summaries, and full story URLs from media publications.",
        "category": "Content & News",
        "data_source": "Public News Sites, Blogs, and Industry Media",
        "required_credentials": "None",
        "limitations": "Does not bypass paywalls.",
        "input_parameters": [
            {"key": "news_url", "label": "News Section URL", "type": "url", "default": "https://techcrunch.com/category/startups/", "required": True},
            {"key": "max_articles", "label": "Max Articles", "type": "number", "default": 30, "required": True}
        ],
        "output_fields": ["headline", "author", "published_date", "summary", "article_url"],
        "example_output": {
            "_sample_notice": "SAMPLE PREVIEW ONLY",
            "headline": "Latin American E-Commerce Infrastructure Reaches Record Valuation",
            "author": "Elena Ramirez",
            "published_date": "2026-10-28",
            "summary": "Cross-border logistics and payments startups expand presence across Mexico and Brazil.",
            "article_url": "https://techcrunch.com/startups/latam-ecommerce-record"
        },
        "workflow_config": {
            "container_selector": "article, .post-block, .news-card",
            "fields": [
                {"name": "headline", "selector": "h2, h3, .post-title", "type": "text", "attribute": "text"},
                {"name": "author", "selector": ".author, .byline", "type": "text", "attribute": "text"},
                {"name": "published_date", "selector": "time, .date", "type": "text", "attribute": "text"},
                {"name": "summary", "selector": "p, .excerpt", "type": "text", "attribute": "text"},
                {"name": "article_url", "selector": "a", "type": "link", "attribute": "href"}
            ]
        }
    },
    {
        "id": "business-listing-pagination-extractor",
        "name": "Business Listing Pagination Extractor",
        "description": "Configured specifically to handle multi-page catalogs with next-page links or numerical pagination loops.",
        "category": "Lead Generation",
        "data_source": "Multi-page Catalogs & Search Directories",
        "required_credentials": "None",
        "limitations": "Bounded to maximum page limit (default 5 pages) to prevent infinite loops.",
        "input_parameters": [
            {"key": "start_url", "label": "Start Page URL", "type": "url", "default": "https://example-directory.com/browse?page=1", "required": True},
            {"key": "max_pages", "label": "Max Pages to Crawl", "type": "number", "default": 5, "required": True}
        ],
        "output_fields": ["company_name", "website", "phone", "city", "country", "source_url"],
        "example_output": {
            "_sample_notice": "SAMPLE PREVIEW ONLY",
            "company_name": "Monterrey Steel & Industrial",
            "website": "https://www.monterreysteel.mx",
            "phone": "+52 81 8000 0000",
            "city": "Monterrey",
            "country": "Mexico",
            "source_url": "https://example-directory.com/browse?page=2"
        },
        "workflow_config": {
            "container_selector": ".directory-card, .vendor-item, tr.company-row",
            "fields": [
                {"name": "company_name", "selector": ".company-title, td.name, h3", "type": "text", "attribute": "text"},
                {"name": "website", "selector": "a.website-link, td.website a", "type": "link", "attribute": "href"},
                {"name": "phone", "selector": ".telephone, td.phone", "type": "text", "attribute": "text"}
            ],
            "pagination": {"type": "NEXT_BUTTON", "selector": "a[rel='next'], .pagination .next, a:-soup-contains('Next')", "max_pages": 5}
        }
    },
    {
        "id": "custom-website-url-extractor",
        "name": "Custom Website URL Extractor",
        "description": "A universal template that accepts any accessible URL, executes automatic structure detection, and extracts all identified fields.",
        "category": "Lead Generation",
        "data_source": "Any Permitted Public Website",
        "required_credentials": "None",
        "limitations": "Works best on semantic HTML pages and structured layouts.",
        "input_parameters": [
            {"key": "target_url", "label": "Website URL to Extract", "type": "url", "default": "https://justo.mx", "required": True},
            {"key": "extract_depth", "label": "Extraction Depth", "type": "text", "default": "Single Page with Repeated Elements", "required": False}
        ],
        "output_fields": ["company_name", "website", "description", "phone", "email", "address"],
        "example_output": {
            "_sample_notice": "SAMPLE PREVIEW ONLY",
            "company_name": "Jüsto Supermercado Online",
            "website": "https://justo.mx",
            "description": "Supermercado 100% digital en México con frutas, verduras y despensa fresca.",
            "phone": "+52 55 7988 3878",
            "email": "hola@justo.mx",
            "address": "Mexico City, Mexico"
        },
        "workflow_config": {
            "auto_detect_on_run": True,
            "container_selector": "auto",
            "fields": []
        }
    }
]

def get_all_templates() -> List[Dict[str, Any]]:
    return SCRAPER_TEMPLATES

def get_template_by_id(template_id: str) -> Dict[str, Any] | None:
    for t in SCRAPER_TEMPLATES:
        if t["id"] == template_id:
            return t
    return None
