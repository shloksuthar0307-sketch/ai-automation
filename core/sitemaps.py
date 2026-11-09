from django.contrib.sitemaps import Sitemap
from django.urls import reverse


class StaticViewSitemap(Sitemap):
    priority = 0.8
    changefreq = 'weekly'

    def items(self):
        return ['core:index', 'core:privacy', 'core:terms']

    def location(self, item):
        return reverse(item)

