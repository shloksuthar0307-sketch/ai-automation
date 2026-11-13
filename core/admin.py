from django.contrib import admin
from .models import QuoteRequest, PortfolioProject, Testimonial, FAQ, LandingPage, BlogPost


@admin.register(LandingPage)
class LandingPageAdmin(admin.ModelAdmin):
    list_display = ('title', 'slug', 'target_plan', 'is_published', 'updated_at')
    list_editable = ('is_published',)
    list_filter = ('is_published', 'target_plan')
    search_fields = ('title', 'slug', 'h1', 'content')
    prepopulated_fields = {'slug': ('title',)}


@admin.register(BlogPost)
class BlogPostAdmin(admin.ModelAdmin):
    list_display = ('title', 'slug', 'category', 'is_published', 'published_date')
    list_editable = ('is_published',)
    list_filter = ('is_published', 'category')
    search_fields = ('title', 'slug', 'content')
    prepopulated_fields = {'slug': ('title',)}



@admin.register(QuoteRequest)
class QuoteRequestAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'phone', 'business_name', 'plan', 'status', 'created_at')
    list_filter = ('status', 'plan', 'created_at')
    search_fields = ('name', 'email', 'phone', 'business_name', 'brief')
    list_editable = ('status',)
    readonly_fields = ('created_at',)
    date_hierarchy = 'created_at'


@admin.register(PortfolioProject)
class PortfolioProjectAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'badge', 'result_text', 'order', 'is_published', 'created_at')
    list_editable = ('order', 'is_published')
    list_filter = ('is_published', 'category', 'badge')
    search_fields = ('title', 'category', 'short_description', 'problem', 'solution', 'tech_stack')
    prepopulated_fields = {'slug': ('title',)}


@admin.register(Testimonial)
class TestimonialAdmin(admin.ModelAdmin):
    list_display = ('client_name', 'business', 'rating', 'is_published', 'created_at')
    list_editable = ('is_published',)
    list_filter = ('is_published', 'rating')
    search_fields = ('client_name', 'business', 'quote')


@admin.register(FAQ)
class FAQAdmin(admin.ModelAdmin):
    list_display = ('question', 'order', 'is_published')
    list_editable = ('order', 'is_published')
    list_filter = ('is_published',)
    search_fields = ('question', 'answer')
