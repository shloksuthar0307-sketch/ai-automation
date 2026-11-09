import os
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.sitemaps.views import sitemap
from django.urls import path, include

from core.sitemaps import StaticViewSitemap
from core.views import robots_txt_view

sitemaps = {
    'static': StaticViewSitemap,
}

admin.site.site_header = "Sitewright Administration"
admin.site.site_title = "Sitewright Admin Portal"
admin.site.index_title = "Agency Dashboard & Leads"

admin_url_path = getattr(settings, 'DJANGO_ADMIN_URL', 'admin/').strip('/')
admin_url = f"{admin_url_path}/" if admin_url_path else "admin/"

urlpatterns = [
    path(admin_url, admin.site.urls),
    path('robots.txt', robots_txt_view, name='robots_txt'),
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, name='django.contrib.sitemaps.views.sitemap'),
    path('', include('core.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
