import json
from django.conf import settings
from django.templatetags.static import static


def is_real_social_url(url, domain):
    """
    Validates that a URL is a real profile link rather than a placeholder/root domain.
    """
    if not url:
        return False
    clean = url.strip().rstrip('/')
    clean_lower = clean.lower()
    if domain == 'linkedin.com':
        if clean_lower in ('https://linkedin.com', 'http://linkedin.com',
                           'https://www.linkedin.com', 'http://www.linkedin.com'):
            return False
        # Must have an actual profile/company path, e.g. /in/username
        if '/in/' in clean_lower or '/company/' in clean_lower:
            return True
        return False
    elif domain == 'github.com':
        if clean_lower in ('https://github.com', 'http://github.com',
                           'https://www.github.com', 'http://www.github.com'):
            return False
        return True
    return bool(clean)


def build_schema_graph(request=None, page_title=None, extra_entities=None, is_home=False):
    """
    Constructs the Schema.org JSON-LD @graph matching all SEO, AEO, and GEO requirements:
    - WebSite
    - ProfessionalService (with OfferCatalog, geo, areaServed, address, etc.)
    - Person (Founder / Full-Stack Engineer)
    - FAQPage (on home page from published FAQ models)
    - BreadcrumbList (on inner pages)
    - Optional extra entities (e.g. Article)
    Returns a valid JSON string with '<' escaped as '\\u003c'.
    """
    site_url = getattr(settings, 'SITE_URL', 'https://sitewright.in').rstrip('/')
    clean_path = request.path if request and hasattr(request, 'path') else '/'
    canonical_url = f"{site_url}{clean_path}"

    developer_name = getattr(settings, 'DEVELOPER_NAME', 'Shlok Suthar').strip()
    admin_email = getattr(settings, 'ADMIN_NOTIFICATION_EMAIL', 'admin@sitewright.ai').strip()
    raw_whatsapp = getattr(settings, 'WHATSAPP_NUMBER', '').strip()
    github_url = getattr(settings, 'GITHUB_URL', '').strip()
    linkedin_url = getattr(settings, 'LINKEDIN_URL', '').strip()

    same_as = []
    if is_real_social_url(github_url, 'github.com'):
        same_as.append(github_url)
    if is_real_social_url(linkedin_url, 'linkedin.com'):
        same_as.append(linkedin_url)

    try:
        logo_url = f"{site_url}{static('core/img/logo.png')}"
        og_image_url = f"{site_url}{static('core/img/og-image.png')}"
    except Exception:
        logo_url = f"{site_url}/static/core/img/logo.png"
        og_image_url = f"{site_url}/static/core/img/og-image.png"

    # 1. WebSite
    website_entity = {
        "@type": "WebSite",
        "@id": f"{site_url}/#website",
        "url": f"{site_url}/",
        "name": "Sitewright",
        "description": "Solo freelance full-stack website developer in Ahmedabad, India building fast websites, WhatsApp automation, and custom AI tools.",
        "inLanguage": "en-IN",
        "publisher": {
            "@id": f"{site_url}/#professionalservice"
        }
    }

    # 2. ProfessionalService
    professional_service_entity = {
        "@type": "ProfessionalService",
        "@id": f"{site_url}/#professionalservice",
        "name": f"Sitewright – {developer_name}",
        "url": f"{site_url}/",
        "logo": logo_url,
        "image": og_image_url,
        "description": "Solo freelance full-stack website developer in Ahmedabad, Gujarat, India building fast, high-converting websites, custom WhatsApp automation, and AI web tools.",
        "email": admin_email,
        "priceRange": "₹7,000 - ₹45,000+",
        "address": {
            "@type": "PostalAddress",
            "addressLocality": "Ahmedabad",
            "addressRegion": "Gujarat",
            "addressCountry": "IN"
        },
        "geo": {
            "@type": "GeoCoordinates",
            "latitude": 23.0225,
            "longitude": 72.5714
        },
        "areaServed": [
            {
                "@type": "City",
                "name": "Ahmedabad"
            },
            {
                "@type": "State",
                "name": "Gujarat"
            },
            {
                "@type": "Country",
                "name": "India"
            }
        ],
        "founder": {
            "@id": f"{site_url}/#founder"
        },
        "hasOfferCatalog": {
            "@type": "OfferCatalog",
            "name": "Website Development & Automation Services",
            "itemListElement": [
                {
                    "@type": "Offer",
                    "name": "Starter Website Plan",
                    "description": "High-impact single-page website, custom modern layout, mobile responsive, WhatsApp click-to-chat, 14 days launch support.",
                    "price": "7000",
                    "priceCurrency": "INR",
                    "availability": "https://schema.org/InStock",
                    "url": f"{site_url}/#pricing"
                },
                {
                    "@type": "Offer",
                    "name": "Business Website Plan",
                    "description": "Multi-page website up to 6 custom pages, conversion-focused copy, local SEO & schema metadata, fast WhiteNoise performance, 30 days support.",
                    "price": "25000",
                    "priceCurrency": "INR",
                    "availability": "https://schema.org/InStock",
                    "url": f"{site_url}/#pricing"
                },
                {
                    "@type": "Offer",
                    "name": "Custom / Automation Plan",
                    "description": "Custom web platforms, appointment booking systems, automated WhatsApp notifications, custom admin dashboard, 60 days priority support.",
                    "price": "45000",
                    "priceCurrency": "INR",
                    "availability": "https://schema.org/InStock",
                    "url": f"{site_url}/#pricing"
                }
            ]
        }
    }

    if raw_whatsapp:
        professional_service_entity["telephone"] = raw_whatsapp
    if same_as:
        professional_service_entity["sameAs"] = same_as

    # 3. Person (Founder)
    person_entity = {
        "@type": "Person",
        "@id": f"{site_url}/#founder",
        "name": developer_name,
        "jobTitle": "Website Developer & Full-Stack Engineer",
        "worksFor": {
            "@id": f"{site_url}/#professionalservice"
        },
        "address": {
            "@type": "PostalAddress",
            "addressLocality": "Ahmedabad",
            "addressRegion": "Gujarat",
            "addressCountry": "IN"
        },
        "knowsAbout": [
            "Web Development",
            "Website Developer in Ahmedabad",
            "Python",
            "Django",
            "JavaScript",
            "WhatsApp Automation",
            "AI Web Tools",
            "Local SEO",
            "PostgreSQL",
            "REST APIs"
        ]
    }
    if same_as:
        person_entity["sameAs"] = same_as

    graph = [website_entity, professional_service_entity, person_entity]

    # 4. FAQPage on Home Page (from published FAQ models)
    if is_home or clean_path == '/':
        try:
            from core.models import FAQ
            published_faqs = FAQ.objects.filter(is_published=True).order_by('order', 'id')
            if published_faqs.exists():
                faq_elements = []
                for faq in published_faqs:
                    faq_elements.append({
                        "@type": "Question",
                        "name": faq.question,
                        "acceptedAnswer": {
                            "@type": "Answer",
                            "text": faq.answer
                        }
                    })
                graph.append({
                    "@type": "FAQPage",
                    "@id": f"{site_url}/#faqpage",
                    "mainEntity": faq_elements
                })
        except Exception:
            pass

    # 5. BreadcrumbList on Inner Pages
    if not (is_home or clean_path == '/'):
        title = page_title or clean_path.strip('/').replace('-', ' ').title()
        breadcrumb_entity = {
            "@type": "BreadcrumbList",
            "@id": f"{canonical_url}#breadcrumb",
            "itemListElement": [
                {
                    "@type": "ListItem",
                    "position": 1,
                    "name": "Home",
                    "item": f"{site_url}/"
                },
                {
                    "@type": "ListItem",
                    "position": 2,
                    "name": title,
                    "item": canonical_url
                }
            ]
        }
        graph.append(breadcrumb_entity)

    # 6. Extra entities (e.g., Blog Article, custom FAQs)
    if extra_entities:
        for ent in extra_entities:
            graph.append(ent)

    payload = {
        "@context": "https://schema.org",
        "@graph": graph
    }

    # Strict JSON formatting with '<' escaped to prevent script tag injection
    raw_json = json.dumps(payload, ensure_ascii=False, indent=2)
    return raw_json.replace('<', '\\u003c')
