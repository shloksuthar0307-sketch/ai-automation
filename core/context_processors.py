import os
import re
from urllib.parse import quote
from django.conf import settings
from .schema import build_schema_graph


def contact_email(request):
    """
    Exposes contact, conversion, WhatsApp, developer profile, canonical URLs,
    and Schema.org JSON-LD structured data across all templates.
    """
    raw_whatsapp = os.environ.get('WHATSAPP_NUMBER', getattr(settings, 'WHATSAPP_NUMBER', '')).strip()
    clean_whatsapp = re.sub(r'[^0-9]', '', str(raw_whatsapp)) if raw_whatsapp else ''
    default_wa_message = "Hi, I'm interested in a website for my business."
    whatsapp_url = f"https://wa.me/{clean_whatsapp}?text={quote(default_wa_message)}" if clean_whatsapp else ''

    booking_url = os.environ.get('BOOKING_URL', getattr(settings, 'BOOKING_URL', '')).strip()
    developer_name = os.environ.get('DEVELOPER_NAME', getattr(settings, 'DEVELOPER_NAME', 'Shlok Suthar')).strip()
    developer_city = os.environ.get('DEVELOPER_CITY', getattr(settings, 'DEVELOPER_CITY', 'Ahmedabad, India')).strip()
    github_url = os.environ.get('GITHUB_URL', getattr(settings, 'GITHUB_URL', 'https://github.com/shloksuthar0307-sketch')).strip()
    linkedin_url = os.environ.get('LINKEDIN_URL', getattr(settings, 'LINKEDIN_URL', 'https://linkedin.com')).strip()
    plausible_domain = os.environ.get('PLAUSIBLE_DOMAIN', getattr(settings, 'PLAUSIBLE_DOMAIN', '')).strip()

    site_url = getattr(settings, 'SITE_URL', 'https://sitewright.in').rstrip('/')
    clean_path = request.path if hasattr(request, 'path') else '/'
    canonical_url = f"{site_url}{clean_path}"

    schema_json_ld = build_schema_graph(request=request)

    return {
        'site_url': site_url,
        'canonical_url': canonical_url,
        'contact_email': getattr(settings, 'ADMIN_NOTIFICATION_EMAIL', 'admin@sitewright.ai'),
        'whatsapp_number': raw_whatsapp,
        'whatsapp_clean_number': clean_whatsapp,
        'whatsapp_url': whatsapp_url,
        'booking_url': booking_url,
        'developer_name': developer_name,
        'developer_city': developer_city,
        'github_url': github_url,
        'linkedin_url': linkedin_url,
        'plausible_domain': plausible_domain,
        'schema_json_ld': schema_json_ld,
    }
