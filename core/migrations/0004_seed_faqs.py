from django.db import migrations


def seed_faqs_and_placeholders(apps, schema_editor):
    FAQ = apps.get_model('core', 'FAQ')
    PortfolioProject = apps.get_model('core', 'PortfolioProject')

    faqs = [
        {
            'question': "Will my site look like every other AI site?",
            'answer': "No. AI speeds up the first draft, but a designer shapes the layout, colours and words around your brand.",
            'order': 1,
            'is_published': True,
        },
        {
            'question': "Who owns the website?",
            'answer': "You do. The design, content and domain are yours, and you can move them anywhere.",
            'order': 2,
            'is_published': True,
        },
        {
            'question': "How fast can I launch?",
            'answer': "Most sites go live within 5 to 7 working days once we have your details.",
            'order': 3,
            'is_published': True,
        },
        {
            'question': "Can I edit it later?",
            'answer': "Yes. Ask us for changes, or we can set it up so you edit text and images yourself.",
            'order': 4,
            'is_published': True,
        },
    ]

    for item in faqs:
        if not FAQ.objects.filter(question=item['question']).exists():
            FAQ.objects.create(**item)

    projects = [
        {
            'title': "[Placeholder] Organic Farm Direct",
            'slug': "organic-farm-direct",
            'category': "E-Commerce",
            'short_description': "Online storefront for organic farm-to-table groceries with automated WhatsApp ordering, localized inventory, and fast mobile checkout.",
            'result_text': "Launched in 5 days • 2.4x order conversion",
            'live_url': "https://example.com",
            'order': 1,
            'is_published': True,
        },
        {
            'title': "[Placeholder] Apex Freight Logistics",
            'slug': "apex-freight-logistics",
            'category': "B2B Services",
            'short_description': "Modern company profile and instant quote calculation portal for commercial logistics, fleet booking, and client inquiries.",
            'result_text': "Live in 4 days • 85+ corporate inquiries/mo",
            'live_url': "https://example.com",
            'order': 2,
            'is_published': True,
        },
    ]

    for proj in projects:
        if not PortfolioProject.objects.filter(slug=proj['slug']).exists():
            PortfolioProject.objects.create(**proj)


def reverse_seed(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0003_faq_portfolioproject_testimonial_and_more'),
    ]

    operations = [
        migrations.RunPython(seed_faqs_and_placeholders, reverse_seed),
    ]

