from django.core.management.base import BaseCommand
from core.models import PortfolioProject


class Command(BaseCommand):
    help = "Seeds Shlok's real GitHub and production projects with live demos and repository links"

    def handle(self, *args, **options):
        github_projects = [
            {
                'title': 'garege (RepairTrace)',
                'slug': 'garege-repairtrace',
                'category': 'Full-Stack Web App',
                'badge': 'Live App & AI',
                'result_text': 'Gemini Vision AI • 3D Inspection • WebSockets',
                'short_description': 'Automotive repair shop management platform featuring Google Gemini Vision AI damage analysis, interactive 3D vehicle inspection, and real-time WebSocket messaging.',
                'problem': 'Auto repair shops suffer from fragmented communication between car owners, advisors, and mechanics, manual damage logging prone to human error, and delayed repair approvals.',
                'solution': 'Engineered an end-to-end management portal with Gemini Vision AI vehicle damage analysis, 3D inspection module (React Three Fiber), real-time WebSocket status updates (Django Channels), and QR code check-in.',
                'tech_stack': 'Django 5, DRF, React, PostgreSQL, Gemini Vision AI, WebSockets (Channels), Celery, Redis',
                'live_url': 'https://garege-1.onrender.com',
                'github_url': 'https://github.com/shloksuthar0307-sketch/garege',
                'order': 1,
                'is_published': True,
            },
            {
                'title': 'vyse',
                'slug': 'vyse-ai-platform',
                'category': 'Django & AI Platform',
                'badge': 'Live App & AI',
                'result_text': 'Google GenAI SDK • OTP Auth • Publishing',
                'short_description': 'AI-powered creator and publication platform featuring Google Gemini story summarization, Markdown editor, drag-and-drop media uploads, and OTP password recovery.',
                'problem': 'Digital writers and content businesses struggle with bloated publishing software and lack automated tools to generate summaries and engagement tags for time-constrained readers.',
                'solution': 'Architected modern Django publishing platform with Google GenAI SDK for automated 3-bullet article summaries (TL;DR), Markdown content editing, OTP password recovery, and threaded discussions.',
                'tech_stack': 'Django 5, Python, PostgreSQL, Gemini AI, Tailwind CSS, JavaScript',
                'live_url': 'https://vyse-7nj1.onrender.com',
                'github_url': 'https://github.com/shloksuthar0307-sketch/vyse',
                'order': 2,
                'is_published': True,
            },
            {
                'title': 'ecom',
                'slug': 'ecom-affiliate-store',
                'category': 'Django E-Commerce',
                'badge': 'Full-Stack Store',
                'result_text': 'Affiliate Referral Engine • Atomic Transactions',
                'short_description': 'Autonomous Django e-commerce platform with a custom affiliate referral tracking engine, persistent customer carts, and back-office order/inventory management.',
                'problem': 'Online retailers need an autonomous e-commerce store with built-in affiliate referral marketing without paying steep monthly software subscriptions to third-party providers.',
                'solution': 'Built full-featured Django commerce store with custom affiliate tracking middleware, referral links, atomic cart/order transactions, and back-office inventory management.',
                'tech_stack': 'Django 5, Python, PostgreSQL, Affiliate Engine, JavaScript, Tailwind CSS',
                'live_url': 'https://ecom-3atc.onrender.com',
                'github_url': 'https://github.com/shloksuthar0307-sketch/ecom',
                'order': 3,
                'is_published': True,
            },
            {
                'title': 'ReviewX AI',
                'slug': 'reviewx-ai',
                'category': 'Django AI SaaS',
                'badge': 'Universal SaaS',
                'result_text': 'Google Gemini AI • Multi-Tenant • Embed Widget',
                'short_description': 'Production-grade multi-tenant SaaS platform built for businesses to ingest, analyze, monitor, and AI-respond to customer reviews across platforms with an embeddable widget.',
                'problem': 'Businesses struggle with managing online reviews across scattered platforms, detecting customer dissatisfaction quickly, and drafting brand-aligned, policy-safe responses at scale.',
                'solution': 'Built a unified review inbox with Google Gemini sentiment extraction, automated topic tagging, human-in-the-loop brand voice response composer, and lightweight zero-dependency embed widget.',
                'tech_stack': 'Django REST Framework, React 19, Celery, Redis, Google Gemini, PostgreSQL, Docker',
                'live_url': 'https://github.com/shloksuthar0307-sketch',
                'github_url': 'https://github.com/shloksuthar0307-sketch',
                'order': 4,
                'is_published': True,
            },
            {
                'title': 'Fuelfinders',
                'slug': 'fuelfinders',
                'category': 'Full-Stack Web App',
                'badge': 'Open Source',
                'result_text': 'Multi-Fuel Search • Decoupled REST API',
                'short_description': 'Fuel station finder and route navigation platform with decoupled high-performance React + TypeScript frontend consuming Django REST Framework endpoints.',
                'problem': 'Drivers, fleet managers, and long-distance travelers need quick, reliable identification of fuel stations (Petrol, Diesel, CNG) along travel routes without navigating complex maps.',
                'solution': 'Created decoupled full-stack platform with high-speed React + Vite + TypeScript frontend consuming Django REST Framework endpoints with city and fuel type filtering.',
                'tech_stack': 'React, TypeScript, Vite, Django REST Framework, Python, Tailwind CSS',
                'live_url': 'https://github.com/shloksuthar0307-sketch/Fuelfinders',
                'github_url': 'https://github.com/shloksuthar0307-sketch/Fuelfinders',
                'order': 5,
                'is_published': True,
            },
            {
                'title': 'Hospital Management System',
                'slug': 'hospital-management',
                'category': 'Django Healthcare',
                'badge': 'Healthcare CRM',
                'result_text': 'Multi-Role RBAC • Appointment Booking',
                'short_description': 'Comprehensive hospital and multi-department healthcare management system featuring granular role-based access control and patient appointment scheduling.',
                'problem': 'Medical facilities waste hours coordinating appointments and managing records across disconnected communication channels between doctors, staff, and patients.',
                'solution': 'Built unified healthcare portal with role-based access control (Admin, Doctor, Receptionist, Patient), appointment slot reservations, and medical history tracking.',
                'tech_stack': 'Django 5, Python, PostgreSQL, Role-Based Access Control, Dashboards',
                'live_url': 'https://github.com/shloksuthar0307-sketch/hospital',
                'github_url': 'https://github.com/shloksuthar0307-sketch/hospital',
                'order': 6,
                'is_published': True,
            },
        ]

        valid_slugs = [p['slug'] for p in github_projects]
        deleted_count, _ = PortfolioProject.objects.exclude(slug__in=valid_slugs).delete()
        if deleted_count:
            self.stdout.write(self.style.WARNING(f"Purged {deleted_count} older non-GitHub project(s)."))

        created_count = 0
        updated_count = 0
        for data in github_projects:
            slug = data['slug']
            project, created = PortfolioProject.objects.update_or_create(
                slug=slug,
                defaults=data
            )
            if created:
                created_count += 1
            else:
                updated_count += 1

        self.stdout.write(self.style.SUCCESS(
            f"[OK] Seeded {created_count} real GitHub project(s), updated {updated_count} project(s)."
        ))
