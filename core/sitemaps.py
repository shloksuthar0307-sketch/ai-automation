from datetime import datetime, timezone
from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from .models import LandingPage, BlogPost, FAQ, PortfolioProject


class StaticViewSitemap(Sitemap):
    priority = 0.8
    changefreq = 'weekly'

    def items(self):
        return ['core:index', 'core:blog_index', 'core:privacy', 'core:terms']

    def location(self, item):
        return reverse(item)

    def lastmod(self, item):
        if item == 'core:index':
            # Latest modification among projects and faqs
            latest_faq = FAQ.objects.filter(is_published=True).order_by('-created_at').first()
            if latest_faq:
                return latest_faq.created_at
            return datetime(2026, 11, 13, tzinfo=timezone.utc)
        elif item == 'core:blog_index':
            latest_post = BlogPost.objects.filter(is_published=True).order_by('-updated_at').first()
            if latest_post:
                return latest_post.updated_at
            return datetime(2026, 11, 13, tzinfo=timezone.utc)
        elif item in ('core:privacy', 'core:terms'):
            return datetime(2026, 11, 1, tzinfo=timezone.utc)
        return datetime(2026, 11, 13, tzinfo=timezone.utc)


class LandingPageSitemap(Sitemap):
    priority = 0.9
    changefreq = 'weekly'

    def items(self):
        return LandingPage.objects.filter(is_published=True).order_by('slug')

    def lastmod(self, obj):
        return obj.updated_at

    def location(self, obj):
        return obj.get_absolute_url()


class BlogPostSitemap(Sitemap):
    priority = 0.7
    changefreq = 'monthly'

    def items(self):
        return BlogPost.objects.filter(is_published=True).order_by('-published_date')

    def lastmod(self, obj):
        return obj.updated_at

    def location(self, obj):
        return obj.get_absolute_url()
