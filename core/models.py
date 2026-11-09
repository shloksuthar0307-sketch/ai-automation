from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator

PLAN_PRICES = {
    'Starter': 7000,
    'Business': 25000,
    'Store': 35000,
    'Custom': 45000,
}


class PortfolioProject(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    category = models.CharField(max_length=100)
    badge = models.CharField(max_length=50, default="Open Source", help_text="e.g. Open Source, Full-Stack App, Live Demo")
    result_text = models.CharField(max_length=200, help_text="Highlight or milestone (e.g. Full-Stack Web App • Live Demo)")
    short_description = models.TextField()
    problem = models.TextField(blank=True, help_text="Problem addressed")
    solution = models.TextField(blank=True, help_text="Technical and design solution")
    tech_stack = models.CharField(max_length=255, blank=True, help_text="e.g. Django 5, Vanilla JS, SQLite")
    image = models.ImageField(upload_to='portfolio/', blank=True, null=True)
    live_url = models.URLField(blank=True, help_text="Link to live website or demo")
    github_url = models.URLField(blank=True, help_text="Link to GitHub repository")
    is_published = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', '-created_at']
        verbose_name = 'Portfolio Project'
        verbose_name_plural = 'Portfolio Projects'

    def __str__(self):
        return self.title


class Testimonial(models.Model):
    client_name = models.CharField(max_length=150)
    business = models.CharField(max_length=150)
    quote = models.TextField()
    photo = models.ImageField(upload_to='testimonials/', blank=True, null=True)
    rating = models.PositiveSmallIntegerField(
        default=5,
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    is_published = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Testimonial'
        verbose_name_plural = 'Testimonials'

    def __str__(self):
        return f"{self.client_name} ({self.business})"


class FAQ(models.Model):
    question = models.CharField(max_length=255)
    answer = models.TextField()
    order = models.PositiveIntegerField(default=0)
    is_published = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', 'id']
        verbose_name = 'FAQ'
        verbose_name_plural = 'FAQs'

    def __str__(self):
        return self.question


class QuoteRequest(models.Model):
    PLAN_CHOICES = [
        ('Starter', 'Starter (₹7,000)'),
        ('Business', 'Business (₹25,000)'),
        ('Store', 'Store (₹35,000)'),
        ('Custom', 'Custom / Automation (from ₹45,000)'),
    ]

    STATUS_CHOICES = [
        ('new', 'New Lead'),
        ('contacted', 'Contacted'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('archived', 'Archived'),
    ]

    name = models.CharField(max_length=150)
    email = models.EmailField(blank=True)
    business_name = models.CharField(max_length=200, blank=True)
    phone = models.CharField(max_length=50, blank=True)
    plan = models.CharField(max_length=50, choices=PLAN_CHOICES, default='Business')
    brief = models.TextField(blank=True, help_text="Client business description / requirements")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Quote Request'
        verbose_name_plural = 'Quote Requests'

    def __str__(self):
        biz = f" ({self.business_name})" if self.business_name else ""
        return f"{self.name}{biz} - {self.plan} [{self.created_at.strftime('%d %b %Y')}]"
