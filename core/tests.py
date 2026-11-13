import io
import importlib
import json
import os
import re
from unittest.mock import patch
from django.conf import settings
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.exceptions import ImproperlyConfigured
from django.core.management import call_command
from core.models import QuoteRequest, PortfolioProject, Testimonial, FAQ
from core.views import get_client_ip

User = get_user_model()


class SitewrightPortalTests(TestCase):
    def setUp(self):
        cache.clear()
        self.client = Client()
        self.admin_user = User.objects.create_superuser('admin', 'admin@sitewright.ai', 'adminpassword123')
        self.regular_user = User.objects.create_user('john', 'john@example.com', 'mypassword123')
        self.quote = QuoteRequest.objects.create(
            name='Rohit Verma',
            email='rohit@example.com',
            business_name='Verma Logistics',
            phone='+91 91234 56789',
            plan='Business',
            brief='Fleet tracking portal with customer booking.'
        )

    def test_unique_portal_urls(self):
        self.assertEqual(reverse('core:admin_login'), '/portal-hq/login/')
        self.assertEqual(reverse('core:admin_dashboard'), '/portal-hq/dashboard/')
        self.assertEqual(reverse('core:admin_logout'), '/portal-hq/logout/')
        self.assertEqual(reverse('core:admin_export_csv'), '/portal-hq/export-csv/')
        self.assertEqual(reverse('core:admin_update_status', args=[1]), '/portal-hq/quote/1/update-status/')
        self.assertEqual(reverse('core:admin_delete_quote', args=[1]), '/portal-hq/quote/1/delete/')

    def test_index_page_loads(self):
        response = self.client.get(reverse('core:index'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Sitewright")
        self.assertContains(response, "fast, high-converting websites")

    def test_submit_quote_valid(self):
        payload = {
            'name': 'Priya Patel',
            'email': 'priya@example.com',
            'business_name': 'Patel Organics',
            'phone': '+91 99887 76655',
            'plan': 'Store',
            'brief': 'Online organic grocery store.'
        }
        response = self.client.post(
            reverse('core:submit_quote'),
            data=json.dumps(payload),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(QuoteRequest.objects.filter(email='priya@example.com').count(), 1)

    def test_admin_login_page_renders(self):
        response = self.client.get(reverse('core:admin_login'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "admin portal")
        self.assertContains(response, "Username")
        self.assertContains(response, "Password")
        self.assertContains(response, "Sign in to Dashboard")

    def test_admin_login_successful_for_admin(self):
        response = self.client.post(reverse('core:admin_login'), {
            'username': 'admin',
            'password': 'adminpassword123'
        })
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('core:admin_dashboard'))

    def test_admin_login_denies_regular_user(self):
        response = self.client.post(reverse('core:admin_login'), {
            'username': 'john',
            'password': 'mypassword123'
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Access Denied: Only administrators can access this portal.")

    def test_admin_login_invalid_credentials(self):
        response = self.client.post(reverse('core:admin_login'), {
            'username': 'admin',
            'password': 'wrongpassword'
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Invalid administrator credentials.")

    def test_admin_dashboard_anonymous_redirected(self):
        response = self.client.get(reverse('core:admin_dashboard'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/portal-hq/login/', response.url)

    def test_admin_dashboard_denies_regular_user(self):
        self.client.login(username='john', password='mypassword123')
        response = self.client.get(reverse('core:admin_dashboard'))
        self.assertEqual(response.status_code, 403)

    def test_admin_dashboard_accessible_by_admin(self):
        self.client.login(username='admin', password='adminpassword123')
        response = self.client.get(reverse('core:admin_dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Inquiries & Leads Overview")
        self.assertContains(response, "Rohit Verma")
        self.assertContains(response, "Verma Logistics")

    def test_admin_update_status_authorized(self):
        self.client.login(username='admin', password='adminpassword123')
        response = self.client.post(
            reverse('core:admin_update_status', args=[self.quote.id]),
            data=json.dumps({'status': 'in_progress'}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.quote.refresh_from_db()
        self.assertEqual(self.quote.status, 'in_progress')

    def test_admin_update_status_forbidden_for_regular_user(self):
        self.client.login(username='john', password='mypassword123')
        response = self.client.post(
            reverse('core:admin_update_status', args=[self.quote.id]),
            data=json.dumps({'status': 'in_progress'}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 403)

    def test_admin_delete_quote_authorized(self):
        self.client.login(username='admin', password='adminpassword123')
        quote_to_delete = QuoteRequest.objects.create(
            name='Temp User',
            email='temp@example.com',
            plan='Starter'
        )
        response = self.client.post(
            reverse('core:admin_delete_quote', args=[quote_to_delete.id]),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(QuoteRequest.objects.filter(id=quote_to_delete.id).exists())

    def test_admin_delete_quote_forbidden_for_regular_user(self):
        self.client.login(username='john', password='mypassword123')
        response = self.client.post(
            reverse('core:admin_delete_quote', args=[self.quote.id]),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(response.status_code, 403)

    def test_admin_export_csv_authorized(self):
        self.client.login(username='admin', password='adminpassword123')
        response = self.client.get(reverse('core:admin_export_csv'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/csv')
        self.assertContains(response, "Rohit Verma")
        self.assertContains(response, "rohit@example.com")

    def test_admin_export_csv_forbidden_for_regular_user(self):
        self.client.login(username='john', password='mypassword123')
        response = self.client.get(reverse('core:admin_export_csv'))
        self.assertEqual(response.status_code, 403)

    def test_csv_formula_injection_sanitization(self):
        # Create quote with formula injection payloads
        QuoteRequest.objects.create(
            name='=cmd|"/c calc"!A0',
            email='malicious@example.com',
            business_name='+1234567890',
            phone='-999999999',
            plan='Starter',
            brief='@SUM(1,2)'
        )
        self.client.login(username='admin', password='adminpassword123')
        response = self.client.get(reverse('core:admin_export_csv'))
        self.assertEqual(response.status_code, 200)
        content = response.content.decode('utf-8')
        # All dangerous leading characters must be prefixed with single quote
        self.assertIn("'=cmd", content)
        self.assertIn("'+1234567890", content)
        self.assertIn("'-999999999", content)
        self.assertIn("'@SUM(1,2)", content)

    def test_honeypot_discards_bot_quote_silently(self):
        payload = {
            'name': 'Bot Spammer',
            'email': 'bot@spammer.com',
            'business_name': 'Buy Cheap Crypto',
            'phone': '123456789',
            'plan': 'Starter',
            'brief': 'Visit our scam site',
            'website_trap': 'http://automated-bot-payload.com'  # Bot filled honeypot!
        }
        response = self.client.post(
            reverse('core:submit_quote'),
            data=json.dumps(payload),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        # Crucial security verification: Nothing was saved into QuoteRequest!
        self.assertFalse(QuoteRequest.objects.filter(email='bot@spammer.com').exists())

    def test_quote_rate_limiting(self):
        payload = {
            'name': 'Rapid Submitter',
            'email': 'rapid@example.com',
            'plan': 'Business',
            'brief': 'Need site quickly'
        }
        # First 10 requests should succeed
        for i in range(10):
            res = self.client.post(
                reverse('core:submit_quote'),
                data=json.dumps(payload),
                content_type='application/json'
            )
            self.assertEqual(res.status_code, 200)

        # 11th request from same client must be throttled with 429
        throttled_res = self.client.post(
            reverse('core:submit_quote'),
            data=json.dumps(payload),
            content_type='application/json'
        )
        self.assertEqual(throttled_res.status_code, 429)
        self.assertIn('Too many requests', throttled_res.json()['error'])

    def test_admin_login_lockout_after_failed_attempts(self):
        # 4 failed attempts should yield attempts remaining
        for attempt in range(4):
            res = self.client.post(reverse('core:admin_login'), {
                'username': 'admin',
                'password': f'badpass{attempt}'
            })
            self.assertEqual(res.status_code, 200)
            self.assertContains(res, "attempts remaining")

        # 5th failed attempt triggers 5-minute lockout
        lockout_res = self.client.post(reverse('core:admin_login'), {
            'username': 'admin',
            'password': 'badpass5'
        })
        self.assertEqual(lockout_res.status_code, 429)
        self.assertContains(lockout_res, "Login locked for 5 minutes", status_code=429)

    def test_open_redirect_mitigation_on_login(self):
        # 1. next parameter with evil off-site domain must not redirect off-site
        response = self.client.post(reverse('core:admin_login'), {
            'username': 'admin',
            'password': 'adminpassword123',
            'next': 'https://evil.com/phishing'
        })
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('core:admin_dashboard'))
        self.assertNotIn('evil.com', response.url)

        # 2. Also check GET parameter next when logging in
        response2 = self.client.post(reverse('core:admin_login') + '?next=https://evil.com/attack', {
            'username': 'admin',
            'password': 'adminpassword123'
        })
        self.assertEqual(response2.status_code, 302)
        self.assertRedirects(response2, reverse('core:admin_dashboard'))
        self.assertNotIn('evil.com', response2.url)

    def test_admin_dashboard_redirect_encodes_next(self):
        # Unauthenticated access to dashboard encodes the next redirect path
        res = self.client.get('/portal-hq/dashboard/?status=new&q=test')
        self.assertEqual(res.status_code, 302)
        self.assertIn('%2Fportal-hq%2Fdashboard%2F%3Fstatus%3Dnew%26q%3Dtest', res.url)

    def test_spoofed_x_forwarded_for_rate_limit(self):
        # When TRUSTED_PROXY_COUNT=0, spoofing HTTP_X_FORWARDED_FOR must not bypass quote rate limiting
        payload = {
            'name': 'Spoofer',
            'email': 'spoofer@example.com',
            'plan': 'Business',
            'brief': 'Need site'
        }
        with self.settings(TRUSTED_PROXY_COUNT=0):
            for i in range(10):
                res = self.client.post(
                    reverse('core:submit_quote'),
                    data=json.dumps(payload),
                    content_type='application/json',
                    HTTP_X_FORWARDED_FOR=f"10.0.0.{i}"
                )
                self.assertEqual(res.status_code, 200)

            # 11th request with different spoofed XFF should be throttled
            throttled_res = self.client.post(
                reverse('core:submit_quote'),
                data=json.dumps(payload),
                content_type='application/json',
                HTTP_X_FORWARDED_FOR="192.168.1.99"
            )
            self.assertEqual(throttled_res.status_code, 429)

    def test_spoofed_x_forwarded_for_login_lockout(self):
        # When TRUSTED_PROXY_COUNT=0, spoofing HTTP_X_FORWARDED_FOR must not bypass login lockout
        with self.settings(TRUSTED_PROXY_COUNT=0):
            for i in range(4):
                res = self.client.post(
                    reverse('core:admin_login'),
                    {'username': 'admin', 'password': f'wrong_{i}'},
                    HTTP_X_FORWARDED_FOR=f"10.0.0.{i}"
                )
                self.assertEqual(res.status_code, 200)
                self.assertContains(res, "attempts remaining")

            # 5th attempt triggers lockout despite different spoofed header
            lockout_res = self.client.post(
                reverse('core:admin_login'),
                {'username': 'admin', 'password': 'wrong_final'},
                HTTP_X_FORWARDED_FOR="192.168.1.99"
            )
            self.assertEqual(lockout_res.status_code, 429)
            self.assertContains(lockout_res, "Login locked for 5 minutes", status_code=429)

    def test_trusted_proxy_count_behavior(self):
        req = self.client.get(reverse('core:index'), HTTP_X_FORWARDED_FOR="1.1.1.1, 2.2.2.2, 3.3.3.3").wsgi_request
        with self.settings(TRUSTED_PROXY_COUNT=0):
            self.assertEqual(get_client_ip(req), req.META.get('REMOTE_ADDR'))
        with self.settings(TRUSTED_PROXY_COUNT=1):
            self.assertEqual(get_client_ip(req), "3.3.3.3")
        with self.settings(TRUSTED_PROXY_COUNT=2):
            self.assertEqual(get_client_ip(req), "2.2.2.2")

    def test_password_with_leading_trailing_spaces(self):
        spaced_pw = "  super secret password  "
        User.objects.create_superuser('spaced_admin', 'spaced@sitewright.ai', spaced_pw)
        response = self.client.post(reverse('core:admin_login'), {
            'username': 'spaced_admin',
            'password': spaced_pw
        })
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('core:admin_dashboard'))

    @patch('core.views.send_mail')
    def test_quote_saved_if_send_mail_raises(self, mock_send_mail):
        mock_send_mail.side_effect = Exception("SMTP connection failure")
        payload = {
            'name': 'Test Client',
            'email': 'client@example.com',
            'business_name': 'Test Co',
            'phone': '+91 91234 56789',
            'plan': 'Business',
            'brief': 'Need website'
        }
        response = self.client.post(
            reverse('core:submit_quote'),
            data=json.dumps(payload),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertTrue(QuoteRequest.objects.filter(email='client@example.com').exists())

    def test_setup_admin_does_not_use_known_default_password(self):
        out = io.StringIO()
        test_username = 'new_random_admin'
        User.objects.filter(username=test_username).delete()

        env_patch = {
            'ADMIN_USERNAME': test_username,
            'ADMIN_EMAIL': 'new_random@sitewright.ai',
        }
        with patch.dict(os.environ, env_patch, clear=False):
            if 'ADMIN_PASSWORD' in os.environ:
                del os.environ['ADMIN_PASSWORD']
            call_command('setup_admin', stdout=out)

        user = User.objects.get(username=test_username)
        # Verify it did not use the old default password 'adminpassword123'
        self.assertFalse(user.check_password('adminpassword123'))
        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_staff)
        self.assertIn(f"Created superuser '{test_username}' with generated password:", out.getvalue())

    def test_settings_raise_improperly_configured_when_debug_false_and_no_secret_key(self):
        env_copy = os.environ.copy()
        try:
            os.environ['DJANGO_DEBUG'] = 'False'
            os.environ.pop('DJANGO_SECRET_KEY', None)
            with patch('dotenv.load_dotenv'):
                with self.assertRaises(ImproperlyConfigured):
                    import sitewright.settings
                    importlib.reload(sitewright.settings)
        finally:
            os.environ.clear()
            os.environ.update(env_copy)
            with patch('dotenv.load_dotenv'):
                import sitewright.settings
                importlib.reload(sitewright.settings)

    def test_contact_ref_url_honeypot_discards_bot_quote(self):
        payload = {
            'name': 'Bot Spammer 2',
            'email': 'bot2@spammer.com',
            'plan': 'Starter',
            'brief': 'Visit our scam site',
            'contact_ref_url': 'http://automated-bot-payload.com'
        }
        response = self.client.post(
            reverse('core:submit_quote'),
            data=json.dumps(payload),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['success'])
        self.assertFalse(QuoteRequest.objects.filter(email='bot2@spammer.com').exists())

    def test_contact_email_context_processor(self):
        response = self.client.get(reverse('core:index'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('contact_email', response.context)

    def test_portfolio_projects_rendered_when_published(self):
        PortfolioProject.objects.all().delete()
        pub = PortfolioProject.objects.create(
            title="Dr. Sharma Dental Clinic",
            slug="sharma-dental",
            category="Healthcare",
            short_description="Modern appointment booking portal",
            result_text="Launched in 3 days",
            is_published=True,
            order=1
        )
        unpub = PortfolioProject.objects.create(
            title="Draft Secret Project",
            slug="draft-secret",
            category="Tech",
            short_description="Unpublished internal demo",
            result_text="Pending",
            is_published=False,
            order=2
        )
        response = self.client.get(reverse('core:index'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Dr. Sharma Dental Clinic")
        self.assertNotContains(response, "Draft Secret Project")

    def test_testimonials_section_hidden_when_empty(self):
        Testimonial.objects.all().delete()
        response = self.client.get(reverse('core:index'))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'id="testimonials"')

    def test_testimonials_section_rendered_when_published(self):
        Testimonial.objects.all().delete()
        Testimonial.objects.create(
            client_name="Vikram Mehta",
            business="Mehta Sweets & Bakery",
            quote="Our orders doubled in the first month. Excellent design.",
            rating=5,
            is_published=True
        )
        response = self.client.get(reverse('core:index'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'id="testimonials"')
        self.assertContains(response, "Vikram Mehta")
        self.assertContains(response, "Mehta Sweets &amp; Bakery")

    def test_faqs_rendered_from_database(self):
        FAQ.objects.all().delete()
        FAQ.objects.create(
            question="What is the average turnaround time?",
            answer="Usually 5 to 7 days.",
            order=1,
            is_published=True
        )
        FAQ.objects.create(
            question="Can I upgrade my plan later?",
            answer="Yes, at any time.",
            order=2,
            is_published=True
        )
        response = self.client.get(reverse('core:index'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "What is the average turnaround time?")
        self.assertContains(response, "Usually 5 to 7 days.")
        self.assertContains(response, "Can I upgrade my plan later?")

    def test_submit_quote_with_email_only_succeeds(self):
        payload = {
            'name': 'Aarav Gupta',
            'email': 'aarav@example.com',
            'phone': '',
            'plan': 'Starter',
            'brief': 'Minimal site'
        }
        response = self.client.post(
            reverse('core:submit_quote'),
            data=json.dumps(payload),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['success'])
        self.assertTrue(QuoteRequest.objects.filter(email='aarav@example.com').exists())

    def test_submit_quote_with_phone_only_succeeds(self):
        payload = {
            'name': 'Kavita Singh',
            'email': '',
            'phone': '+91 98765 43210',
            'plan': 'Business',
            'brief': 'WhatsApp contact only'
        }
        response = self.client.post(
            reverse('core:submit_quote'),
            data=json.dumps(payload),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['success'])
        self.assertTrue(QuoteRequest.objects.filter(phone='+91 98765 43210').exists())

    def test_submit_quote_without_email_and_phone_fails(self):
        payload = {
            'name': 'No Contact User',
            'email': '',
            'phone': '',
            'plan': 'Business',
            'brief': 'No contact provided'
        }
        response = self.client.post(
            reverse('core:submit_quote'),
            data=json.dumps(payload),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.json()['success'])
        self.assertIn('errors', response.json())

    def test_whatsapp_floating_button_toggle(self):
        # When WHATSAPP_NUMBER is configured
        with patch.dict(os.environ, {'WHATSAPP_NUMBER': '+91 99887 76655'}, clear=False):
            res = self.client.get(reverse('core:index'))
            self.assertEqual(res.status_code, 200)
            self.assertContains(res, 'id="whatsappFloatBtn"')
            self.assertContains(res, 'https://wa.me/919988776655')

        # When WHATSAPP_NUMBER is empty
        with patch.dict(os.environ, {'WHATSAPP_NUMBER': ''}, clear=False):
            with self.settings(WHATSAPP_NUMBER=''):
                res = self.client.get(reverse('core:index'))
                self.assertEqual(res.status_code, 200)
                self.assertNotContains(res, 'id="whatsappFloatBtn"')

    def test_booking_link_toggle(self):
        # When BOOKING_URL is configured
        with patch.dict(os.environ, {'BOOKING_URL': 'https://cal.com/sitewright'}, clear=False):
            res = self.client.get(reverse('core:index'))
            self.assertEqual(res.status_code, 200)
            self.assertContains(res, 'https://cal.com/sitewright')
            self.assertContains(res, 'Book a free 15-min call')

        # When BOOKING_URL is empty
        with patch.dict(os.environ, {'BOOKING_URL': ''}, clear=False):
            with self.settings(BOOKING_URL=''):
                res = self.client.get(reverse('core:index'))
                self.assertEqual(res.status_code, 200)
                self.assertNotContains(res, 'Book a free 15-min call')

    def test_privacy_page_renders_with_dpdp_act(self):
        res = self.client.get(reverse('core:privacy'))
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, "Privacy Policy")
        self.assertContains(res, "Digital Personal Data Protection")
        self.assertContains(res, "Right to Erasure")

    def test_terms_page_renders_freelance_terms(self):
        res = self.client.get(reverse('core:terms'))
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, "Terms of Service")
        self.assertContains(res, "50% non-refundable deposit")
        self.assertContains(res, "Project Scope & Estimates")

    def test_robots_txt_shielding_and_sitemap(self):
        res = self.client.get('/robots.txt')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res['Content-Type'], 'text/plain')
        content = res.content.decode('utf-8')
        self.assertIn("User-agent: *", content)
        self.assertIn("Disallow: /portal-hq/", content)
        self.assertIn("/sitemap.xml", content)

    def test_sitemap_xml_renders(self):
        res = self.client.get('/sitemap.xml')
        self.assertEqual(res.status_code, 200)
        self.assertIn('xml', res['Content-Type'])
        content = res.content.decode('utf-8')
        self.assertIn('<loc>http://testserver/</loc>', content)
        self.assertIn('<loc>http://testserver/privacy/</loc>', content)
        self.assertIn('<loc>http://testserver/terms/</loc>', content)

    def test_seed_concept_projects_command_and_rendering(self):
        call_command('seed_concept_projects')
        self.assertTrue(PortfolioProject.objects.filter(github_url__icontains="github.com").exists())
        project = PortfolioProject.objects.get(slug="garege-repairtrace")
        self.assertEqual(project.badge, "Live App & AI")
        self.assertTrue(len(project.problem) > 10)
        self.assertTrue(len(project.solution) > 10)

        res = self.client.get(reverse('core:index'))
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, "garege (RepairTrace)")
        self.assertContains(res, "https://github.com/shloksuthar0307-sketch/garege")

    def test_submit_quote_custom_plan(self):
        payload = {
            'name': 'Dr. Rajesh Patel',
            'email': 'rajesh@example.com',
            'phone': '+91 98765 00000',
            'business_name': 'Patel Dental Care',
            'plan': 'Custom',
            'brief': 'Custom patient booking with automated WhatsApp confirmation.'
        }
        res = self.client.post(
            reverse('core:submit_quote'),
            data=json.dumps(payload),
            content_type='application/json'
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data['success'])
        lead = QuoteRequest.objects.get(email='rajesh@example.com')
        self.assertEqual(lead.plan, 'Custom')

    def test_about_section_and_solo_branding(self):
        res = self.client.get(reverse('core:index'))
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, "Who builds your site")
        self.assertContains(res, "Shlok Suthar")
        self.assertContains(res, "Ahmedabad, India")
        self.assertContains(res, "Django 5")
        self.assertContains(res, "Python")

    def test_pricing_tiers_and_transparency_notes(self):
        res = self.client.get(reverse('core:index'))
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, "Starter")
        self.assertContains(res, "Business")
        self.assertContains(res, "Custom / Automation")
        self.assertContains(res, "What is included")
        self.assertContains(res, "What is not included")
        self.assertContains(res, "50% deposit upfront")

    def test_mobile_navigation_accessibility(self):
        res = self.client.get(reverse('core:index'))
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, 'id="mobileNavToggle"')
        self.assertContains(res, 'aria-expanded="false"')
        self.assertContains(res, 'aria-controls="mobileNavMenu"')
        self.assertContains(res, 'id="mobileNavMenu"')
        self.assertContains(res, 'aria-hidden="true"')

    def test_plausible_analytics_script_toggle(self):
        with patch.dict(os.environ, {'PLAUSIBLE_DOMAIN': 'sitewright.ai'}, clear=False):
            res = self.client.get(reverse('core:index'))
            self.assertEqual(res.status_code, 200)
            self.assertContains(res, 'data-domain="sitewright.ai"')

        with patch.dict(os.environ, {'PLAUSIBLE_DOMAIN': ''}, clear=False):
            with self.settings(PLAUSIBLE_DOMAIN=''):
                res = self.client.get(reverse('core:index'))
                self.assertEqual(res.status_code, 200)
                self.assertNotContains(res, 'data-domain="sitewright.ai"')

    # --------------------------------------------------------------------------
    # Security Audit Tasks Tests
    # --------------------------------------------------------------------------

    def test_settings_raise_improperly_configured_when_debug_false_and_no_admin_url(self):
        env_copy = os.environ.copy()
        try:
            os.environ['DJANGO_DEBUG'] = 'False'
            os.environ['DJANGO_SECRET_KEY'] = 'test-secret-key-1234567890'
            os.environ.pop('DJANGO_ADMIN_URL', None)
            with patch('dotenv.load_dotenv'):
                with self.assertRaises(ImproperlyConfigured) as ctx:
                    import sitewright.settings
                    importlib.reload(sitewright.settings)
                self.assertIn("DJANGO_ADMIN_URL", str(ctx.exception))
        finally:
            os.environ.clear()
            os.environ.update(env_copy)
            with patch('dotenv.load_dotenv'):
                import sitewright.settings
                importlib.reload(sitewright.settings)

    def test_django_admin_url_defaults_to_admin_in_debug_true(self):
        env_copy = os.environ.copy()
        try:
            os.environ['DJANGO_DEBUG'] = 'True'
            os.environ.pop('DJANGO_ADMIN_URL', None)
            with patch('dotenv.load_dotenv'):
                import sitewright.settings
                importlib.reload(sitewright.settings)
                self.assertEqual(sitewright.settings.DJANGO_ADMIN_URL, 'admin/')
        finally:
            os.environ.clear()
            os.environ.update(env_copy)
            with patch('dotenv.load_dotenv'):
                import sitewright.settings
                importlib.reload(sitewright.settings)

    def test_django_admin_axes_lockout_after_5_failures(self):
        admin_login_url = reverse('admin:login')
        for i in range(4):
            res = self.client.post(admin_login_url, {
                'username': 'admin',
                'password': f'wrongpass{i}'
            })
            self.assertEqual(res.status_code, 200)

        # 5th attempt should be locked out by Axes
        locked_res = self.client.post(admin_login_url, {
            'username': 'admin',
            'password': 'wrongpass_lockout'
        })
        self.assertIn(locked_res.status_code, [403, 429])

    def test_settings_fail_when_redis_url_set_and_redis_not_installed(self):
        env_copy = os.environ.copy()
        try:
            os.environ['REDIS_URL'] = 'redis://127.0.0.1:6379/1'
            with patch('dotenv.load_dotenv'), patch.dict('sys.modules', {'redis': None}):
                with self.assertRaises(ImproperlyConfigured) as ctx:
                    import sitewright.settings
                    importlib.reload(sitewright.settings)
                self.assertIn("REDIS_URL is configured but the 'redis' package is not installed", str(ctx.exception))
        finally:
            os.environ.clear()
            os.environ.update(env_copy)
            with patch('dotenv.load_dotenv'):
                import sitewright.settings
                importlib.reload(sitewright.settings)

    def test_submit_quote_invalid_json_types(self):
        # [1, 2]
        res1 = self.client.post(
            reverse('core:submit_quote'),
            data='[1, 2]',
            content_type='application/json'
        )
        self.assertEqual(res1.status_code, 400)
        self.assertEqual(res1.json(), {'success': False, 'error': 'Invalid JSON format'})

        # "x"
        res2 = self.client.post(
            reverse('core:submit_quote'),
            data='"x"',
            content_type='application/json'
        )
        self.assertEqual(res2.status_code, 400)
        self.assertEqual(res2.json(), {'success': False, 'error': 'Invalid JSON format'})

        # null
        res3 = self.client.post(
            reverse('core:submit_quote'),
            data='null',
            content_type='application/json'
        )
        self.assertEqual(res3.status_code, 400)
        self.assertEqual(res3.json(), {'success': False, 'error': 'Invalid JSON format'})

        # {}
        res4 = self.client.post(
            reverse('core:submit_quote'),
            data='{}',
            content_type='application/json'
        )
        self.assertEqual(res4.status_code, 400)
        self.assertFalse(res4.json()['success'])
        self.assertIn('errors', res4.json())

        # None / empty body
        res5 = self.client.post(
            reverse('core:submit_quote'),
            data='',
            content_type='application/json'
        )
        self.assertIn(res5.status_code, [400, 500])

    def test_admin_login_lockout_keyed_on_ip_and_username(self):
        # Attacker fails 5 times with 'attacker_user'
        for i in range(5):
            self.client.post(reverse('core:admin_login'), {
                'username': 'attacker_user',
                'password': f'wrong_{i}'
            })

        # 'attacker_user' is locked out from this IP
        res_locked = self.client.post(reverse('core:admin_login'), {
            'username': 'attacker_user',
            'password': 'any_password'
        })
        self.assertEqual(res_locked.status_code, 429)

        # Real admin from same IP with valid credentials is NOT locked out
        res_admin = self.client.post(reverse('core:admin_login'), {
            'username': 'admin',
            'password': 'adminpassword123'
        })
        self.assertEqual(res_admin.status_code, 302)
        self.assertRedirects(res_admin, reverse('core:admin_dashboard'))

    def test_trusted_proxy_count_fewer_entries_fallback_to_remote_addr(self):
        req = self.client.get(
            reverse('core:index'),
            HTTP_X_FORWARDED_FOR="198.51.100.1",
            REMOTE_ADDR="192.0.2.1"
        ).wsgi_request
        with self.settings(TRUSTED_PROXY_COUNT=2):
            self.assertEqual(get_client_ip(req), "192.0.2.1")

    def test_startup_warning_when_debug_false_and_proxy_count_zero_and_no_redis(self):
        from django.apps import apps
        core_config = apps.get_app_config('core')
        with self.settings(DEBUG=False, TRUSTED_PROXY_COUNT=0, REDIS_URL=None):
            with self.assertLogs('core.apps', level='WARNING') as cm:
                core_config.ready()
            self.assertTrue(any("TRUSTED_PROXY_COUNT is 0" in msg for msg in cm.output))

    def test_admin_logout_requires_post(self):
        self.client.login(username='admin', password='adminpassword123')
        # GET should return 405 Method Not Allowed
        get_res = self.client.get(reverse('core:admin_logout'))
        self.assertEqual(get_res.status_code, 405)

        # POST should succeed and redirect to login
        post_res = self.client.post(reverse('core:admin_logout'))
        self.assertEqual(post_res.status_code, 302)
        self.assertRedirects(post_res, reverse('core:admin_login'))

    def test_csp_header_present_and_nonced(self):
        res = self.client.get(reverse('core:index'))
        self.assertEqual(res.status_code, 200)
        self.assertIn('Content-Security-Policy', res.headers)
        csp = res.headers['Content-Security-Policy']
        self.assertIn("default-src 'self'", csp)
        self.assertIn("fonts.googleapis.com", csp)
        self.assertIn("fonts.gstatic.com", csp)
        self.assertIn("plausible.io", csp)
        self.assertIn("nonce-", csp)

    def test_admin_dashboard_csp_and_no_inline_event_handlers(self):
        self.client.login(username='admin', password='adminpassword123')
        res = self.client.get(reverse('core:admin_dashboard'))
        self.assertEqual(res.status_code, 200)
        content = res.content.decode('utf-8')
        self.assertIn('Content-Security-Policy', res.headers)
        self.assertIn('<style nonce="', content)
        self.assertIn('<script nonce="', content)
        self.assertNotIn('onchange=', content)

    def test_admin_dashboard_pagination(self):
        self.client.login(username='admin', password='adminpassword123')
        QuoteRequest.objects.all().delete()
        for i in range(30):
            QuoteRequest.objects.create(
                name=f'Client {i:02d}',
                email=f'client{i:02d}@example.com',
                plan='Starter',
                status='new'
            )

        res_p1 = self.client.get(reverse('core:admin_dashboard') + '?page=1')
        self.assertEqual(res_p1.status_code, 200)
        self.assertEqual(len(res_p1.context['quotes']), 25)
        self.assertContains(res_p1, 'Page 1 of 2')
        self.assertContains(res_p1, 'Next →')

        res_p2 = self.client.get(reverse('core:admin_dashboard') + '?page=2')
        self.assertEqual(res_p2.status_code, 200)
        self.assertEqual(len(res_p2.context['quotes']), 5)
        self.assertContains(res_p2, '← Previous')
        self.assertContains(res_p2, 'Page 2 of 2')

    def test_admin_dashboard_pagination_preserves_filters(self):
        self.client.login(username='admin', password='adminpassword123')
        QuoteRequest.objects.all().delete()
        for i in range(30):
            QuoteRequest.objects.create(
                name=f'SearchTarget {i:02d}',
                email=f'target{i:02d}@example.com',
                plan='Business',
                status='new'
            )

        res = self.client.get(reverse('core:admin_dashboard') + '?q=SearchTarget&plan=Business&status=new&page=1')
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, 'q=SearchTarget')
        self.assertContains(res, 'plan=Business')
        self.assertContains(res, 'status=new')

    def test_secure_ssl_redirect_configurable_via_env(self):
        env_copy = os.environ.copy()
        try:
            os.environ['DJANGO_SSL_REDIRECT'] = 'False'
            os.environ['DJANGO_DEBUG'] = 'False'
            os.environ['DJANGO_SECRET_KEY'] = 'test-secret-key-1234567890'
            os.environ['DJANGO_ADMIN_URL'] = 'secret-admin/'
            with patch('dotenv.load_dotenv'):
                import sitewright.settings
                importlib.reload(sitewright.settings)
                self.assertFalse(sitewright.settings.SECURE_SSL_REDIRECT)

            os.environ['DJANGO_SSL_REDIRECT'] = 'True'
            with patch('dotenv.load_dotenv'):
                import sitewright.settings
                importlib.reload(sitewright.settings)
                self.assertTrue(sitewright.settings.SECURE_SSL_REDIRECT)
        finally:
            os.environ.clear()
            os.environ.update(env_copy)
            with patch('dotenv.load_dotenv'):
                import sitewright.settings
                importlib.reload(sitewright.settings)

    # --------------------------------------------------------------------------
    # Automatic Database Fallback (PostgreSQL -> SQLite) Tests
    # --------------------------------------------------------------------------

    def test_database_defaults_to_sqlite_when_postgres_unconfigured(self):
        from sitewright.settings import get_database_config
        with patch.dict(os.environ, {}, clear=True):
            cfg = get_database_config()
            self.assertEqual(cfg['ENGINE'], 'django.db.backends.sqlite3')
            self.assertTrue(str(cfg['NAME']).endswith('db.sqlite3'))

    def test_database_uses_postgres_when_configured_and_available(self):
        from sitewright.settings import get_database_config
        env = {
            'POSTGRES_DB': 'sitewright_prod',
            'POSTGRES_USER': 'pguser',
            'POSTGRES_PASSWORD': 'secretpassword',
            'POSTGRES_HOST': 'db.internal',
            'POSTGRES_PORT': '5432'
        }
        with patch.dict(os.environ, env, clear=True), patch('psycopg.connect') as mock_conn:
            cfg = get_database_config()
            self.assertEqual(cfg['ENGINE'], 'django.db.backends.postgresql')
            self.assertEqual(cfg['NAME'], 'sitewright_prod')
            self.assertEqual(cfg['USER'], 'pguser')
            self.assertEqual(cfg['HOST'], 'db.internal')
            self.assertEqual(cfg['PORT'], '5432')
            mock_conn.assert_called_once()

    def test_database_database_url_configured_and_available(self):
        from sitewright.settings import get_database_config
        env = {
            'DATABASE_URL': 'postgresql://dbadmin:p@ss@dbhost.local:5433/custom_db'
        }
        with patch.dict(os.environ, env, clear=True), patch('psycopg.connect') as mock_conn:
            cfg = get_database_config()
            self.assertEqual(cfg['ENGINE'], 'django.db.backends.postgresql')
            self.assertEqual(cfg['NAME'], 'custom_db')
            self.assertEqual(cfg['USER'], 'dbadmin')
            self.assertEqual(cfg['PASSWORD'], 'p@ss')
            self.assertEqual(cfg['HOST'], 'dbhost.local')
            self.assertEqual(cfg['PORT'], '5433')

    def test_database_falls_back_to_sqlite_when_postgres_unavailable(self):
        from sitewright.settings import get_database_config
        env = {
            'POSTGRES_DB': 'sitewright_prod',
            'POSTGRES_HOST': '127.0.0.1',
            'POSTGRES_PORT': '5432'
        }
        with patch.dict(os.environ, env, clear=True), patch('psycopg.connect', side_effect=Exception("Connection refused")):
            cfg = get_database_config()
            self.assertEqual(cfg['ENGINE'], 'django.db.backends.sqlite3')
            self.assertTrue(str(cfg['NAME']).endswith('db.sqlite3'))

    def test_database_falls_back_to_sqlite_when_postgres_driver_missing(self):
        from sitewright.settings import get_database_config
        env = {'POSTGRES_DB': 'sitewright_prod'}
        with patch.dict(os.environ, env, clear=True), patch.dict('sys.modules', {'psycopg': None, 'psycopg2': None}):
            cfg = get_database_config()
            self.assertEqual(cfg['ENGINE'], 'django.db.backends.sqlite3')

    # --------------------------------------------------------------------------
    # Production Readiness Tests (Health Checks, Error Pages, Connection Pooling)
    # --------------------------------------------------------------------------

    def test_health_check_endpoint_ok(self):
        response = self.client.get('/health/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data.get('status'), 'ok')
        self.assertEqual(data.get('database'), 'ok')
        self.assertIn('cache', data)

    def test_healthz_alias_endpoint(self):
        response = self.client.get('/healthz')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data.get('status'), 'ok')

    def test_health_check_head_request(self):
        response = self.client.head('/health/')
        self.assertEqual(response.status_code, 200)

    def test_health_check_database_unhealthy_returns_503(self):
        with patch('django.db.connection.cursor', side_effect=Exception("Database connection timeout")):
            response = self.client.get('/health/')
            self.assertEqual(response.status_code, 503)
            data = response.json()
            self.assertEqual(data.get('status'), 'unhealthy')
            self.assertIn('unhealthy', data.get('database'))

    def test_database_conn_max_age_and_health_checks_configured(self):
        from sitewright.settings import get_database_config
        env = {
            'POSTGRES_DB': 'sitewright_prod',
            'DJANGO_DB_CONN_MAX_AGE': '900'
        }
        with patch.dict(os.environ, env, clear=True), patch('psycopg.connect'):
            cfg = get_database_config()
            self.assertEqual(cfg['CONN_MAX_AGE'], 900)
            self.assertTrue(cfg.get('CONN_HEALTH_CHECKS'))

    def test_custom_error_templates_render(self):
        from django.template.loader import render_to_string
        # Verify 404, 500, 403, and 400 error templates exist and render without crashing
        rendered_404 = render_to_string('404.html')
        self.assertIn("404 NOT FOUND", rendered_404)
        self.assertIn("Sitewright", rendered_404)

        rendered_500 = render_to_string('500.html')
        self.assertIn("500 INTERNAL SERVER ERROR", rendered_500)
        self.assertIn("Sitewright", rendered_500)

        rendered_403 = render_to_string('403.html')
        self.assertIn("403 FORBIDDEN", rendered_403)
        self.assertIn("Sitewright", rendered_403)

        rendered_400 = render_to_string('400.html')
        self.assertIn("400 BAD REQUEST", rendered_400)
        self.assertIn("Sitewright", rendered_400)

    # --------------------------------------------------------------------------
    # Render Cloud Deployment Compatibility Tests
    # --------------------------------------------------------------------------

    def test_render_environment_auto_detection(self):
        env = {
            'RENDER': 'true',
            'RENDER_EXTERNAL_HOSTNAME': 'sitewright.onrender.com',
            'DJANGO_DEBUG': 'True',
        }
        with patch.dict(os.environ, env, clear=True), patch('dotenv.load_dotenv'):
            import sitewright.settings
            importlib.reload(sitewright.settings)
            self.assertTrue(sitewright.settings.IS_RENDER)
            self.assertIn('sitewright.onrender.com', sitewright.settings.ALLOWED_HOSTS)
            self.assertIn('https://sitewright.onrender.com', sitewright.settings.CSRF_TRUSTED_ORIGINS)
            self.assertTrue(sitewright.settings.USE_PROXY_SSL_HEADER)
            self.assertEqual(sitewright.settings.TRUSTED_PROXY_COUNT, 1)

    def test_render_database_url_with_sslmode_query_param(self):
        from sitewright.settings import get_database_config
        env = {
            'DATABASE_URL': 'postgresql://render_user:pass123@dpg-abc123-a.oregon-postgres.render.com:5432/sitewright_db?sslmode=require'
        }
        with patch.dict(os.environ, env, clear=True), patch('psycopg.connect') as mock_conn:
            cfg = get_database_config()
            self.assertEqual(cfg['ENGINE'], 'django.db.backends.postgresql')
            self.assertEqual(cfg['NAME'], 'sitewright_db')
            self.assertEqual(cfg['USER'], 'render_user')
            self.assertEqual(cfg['HOST'], 'dpg-abc123-a.oregon-postgres.render.com')
            self.assertEqual(cfg['OPTIONS']['sslmode'], 'require')
            mock_conn.assert_called_once()
            call_kwargs = mock_conn.call_args[1]
            self.assertEqual(call_kwargs.get('sslmode'), 'require')


class SitewrightSEOAEOAndGEOTests(TestCase):
    def setUp(self):
        cache.clear()
        self.client = Client()

    def test_canonical_has_no_query_string_and_uses_site_url(self):
        response = self.client.get('/?ref=twitter&utm_source=google&page=2')
        self.assertEqual(response.status_code, 200)
        html = response.content.decode('utf-8')

        # Check html lang="en-IN"
        self.assertIn('<html lang="en-IN"', html)

        # Check canonical, og:url, and twitter:url
        canonical_match = re.search(r'rel=["\']canonical["\'] href=["\']([^"\']+)["\']', html)
        self.assertTrue(canonical_match)
        self.assertEqual(canonical_match.group(1), 'https://sitewright.in/')
        self.assertNotIn('?', canonical_match.group(1))
        self.assertNotIn('onrender', canonical_match.group(1))

        og_url_match = re.search(r'property=["\']og:url["\'] content=["\']([^"\']+)["\']', html)
        self.assertTrue(og_url_match)
        self.assertEqual(og_url_match.group(1), 'https://sitewright.in/')

        tw_url_match = re.search(r'name=["\']twitter:url["\'] content=["\']([^"\']+)["\']', html)
        self.assertTrue(tw_url_match)
        self.assertEqual(tw_url_match.group(1), 'https://sitewright.in/')

    def test_json_ld_parses_and_has_required_entities(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        html = response.content.decode('utf-8')

        # Check that '<' is escaped as \u003c in JSON-LD script
        scripts = re.findall(r'<script type=["\']application/ld\+json["\'][^>]*>(.*?)</script>', html, re.DOTALL)
        self.assertTrue(len(scripts) >= 1)
        raw_json_script = scripts[0]
        self.assertNotIn('<', raw_json_script)

        # JSON should parse cleanly
        data = json.loads(raw_json_script)
        self.assertIn('@graph', data)
        types = [e.get('@type') for e in data['@graph']]
        self.assertIn('WebSite', types)
        self.assertIn('ProfessionalService', types)
        self.assertIn('Person', types)
        self.assertIn('FAQPage', types)

        # Validate ProfessionalService
        ps = next(e for e in data['@graph'] if e['@type'] == 'ProfessionalService')
        self.assertEqual(ps['address']['addressLocality'], 'Ahmedabad')
        self.assertEqual(ps['address']['addressCountry'], 'IN')
        self.assertTrue(any(a['name'] == 'Ahmedabad' for a in ps['areaServed']))
        self.assertIn('hasOfferCatalog', ps)
        offers = ps['hasOfferCatalog']['itemListElement']
        self.assertEqual(len(offers), 3)
        self.assertTrue(any(o['name'] == 'Starter Website Plan' and o['price'] == '7000' for o in offers))
        self.assertTrue(any(o['name'] == 'Business Website Plan' and o['price'] == '25000' for o in offers))
        self.assertTrue(any(o['name'] == 'Custom / Automation Plan' and o['price'] == '45000' for o in offers))

    def test_faqpage_matches_database(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        html = response.content.decode('utf-8')
        scripts = re.findall(r'<script type=["\']application/ld\+json["\'][^>]*>(.*?)</script>', html, re.DOTALL)
        data = json.loads(scripts[0])
        faq_page = next(e for e in data['@graph'] if e['@type'] == 'FAQPage')
        json_questions = [q['name'] for q in faq_page['mainEntity']]

        db_faqs = list(FAQ.objects.filter(is_published=True).values_list('question', flat=True))
        self.assertEqual(len(json_questions), len(db_faqs))
        self.assertEqual(set(json_questions), set(db_faqs))

    def test_on_page_seo_titles_descriptions_and_h1(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        html = response.content.decode('utf-8')

        # Title check (<= 60 chars and contains 'Website Developer in Ahmedabad')
        title_match = re.search(r'<title>(.*?)</title>', html)
        self.assertTrue(title_match)
        title = title_match.group(1).strip()
        self.assertLessEqual(len(title), 60)
        self.assertIn('Website Developer in Ahmedabad', title)

        # Meta description (150-160 chars and contains 'Website developer in Ahmedabad')
        desc_match = re.search(r'<meta name=["\']description["\'] content=["\']([^"\']+)["\']', html)
        self.assertTrue(desc_match)
        desc = desc_match.group(1).strip()
        self.assertGreaterEqual(len(desc), 150)
        self.assertLessEqual(len(desc), 160)
        self.assertIn('Website developer in Ahmedabad', desc)

        # Strictly ONE H1 containing 'Ahmedabad'
        h1_matches = re.findall(r'<h1[^>]*>(.*?)</h1>', html, re.DOTALL)
        self.assertEqual(len(h1_matches), 1)
        self.assertIn('Ahmedabad', h1_matches[0])

        # Visible 40-60 word answer-first summary
        summary_match = re.search(r'<div class=["\']answer-summary-card["\'][^>]*>(.*?)</div>', html, re.DOTALL)
        self.assertTrue(summary_match)
        summary_clean = re.sub(r'<[^>]+>', ' ', summary_match.group(1))
        # Lead paragraph words
        lead_match = re.search(r'<p class=["\']answer-summary-lead["\'][^>]*>(.*?)</p>', html, re.DOTALL)
        self.assertTrue(lead_match)
        lead_words = len(re.sub(r'<[^>]+>', ' ', lead_match.group(1)).split())
        self.assertGreaterEqual(lead_words, 40)
        self.assertLessEqual(lead_words, 60)

        # Visible Last Updated date
        self.assertIn('Last updated:', summary_match.group(1))

        # Robots meta tag
        self.assertIn('<meta name="robots" content="index,follow,max-image-preview:large,max-snippet:-1">', html)

    def test_llms_txt_returns_200_text_plain(self):
        response = self.client.get('/llms.txt')
        self.assertEqual(response.status_code, 200)
        self.assertIn('text/plain', response['Content-Type'])
        content = response.content.decode('utf-8')
        self.assertIn('# Sitewright', content)
        self.assertIn('## Site Summary', content)
        self.assertIn('## Services', content)
        self.assertIn('## Pricing', content)
        self.assertIn('## Location', content)
        self.assertIn('Ahmedabad', content)
        self.assertIn('## Key URLs', content)

    def test_robots_txt_lists_ai_bots_and_sitemap(self):
        response = self.client.get('/robots.txt')
        self.assertEqual(response.status_code, 200)
        self.assertIn('text/plain', response['Content-Type'])
        content = response.content.decode('utf-8')

        ai_bots = [
            'GPTBot',
            'OAI-SearchBot',
            'ChatGPT-User',
            'ClaudeBot',
            'Claude-SearchBot',
            'PerplexityBot',
            'Google-Extended',
            'Applebot-Extended',
        ]
        for bot in ai_bots:
            self.assertIn(f'User-agent: {bot}', content)

        self.assertIn('Disallow: /portal-hq/', content)
        self.assertIn('Sitemap: https://sitewright.in/sitemap.xml', content)

    def test_landing_pages_exist_and_meet_requirements(self):
        from core.models import LandingPage

        slugs = [
            'website-developer-ahmedabad',
            'whatsapp-automation-for-business',
            'clinic-website-development',
            'restaurant-website-development',
            'coaching-class-website-development',
        ]
        for slug in slugs:
            url = f'/{slug}/'
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200, f'Landing page {url} returned {response.status_code}')
            html = response.content.decode('utf-8')

            # Check title <= 60 chars
            title_match = re.search(r'<title>(.*?)</title>', html)
            self.assertTrue(title_match)
            self.assertLessEqual(len(title_match.group(1).strip()), 60)

            # Check meta description 150-160 chars
            desc_match = re.search(r'<meta name=["\']description["\'] content=["\']([^"\']+)["\']', html)
            self.assertTrue(desc_match)
            desc_len = len(desc_match.group(1).strip())
            self.assertGreaterEqual(desc_len, 150, f'{slug} meta desc too short ({desc_len})')
            self.assertLessEqual(desc_len, 160, f'{slug} meta desc too long ({desc_len})')

            # Check strictly one H1
            h1_matches = re.findall(r'<h1[^>]*>(.*?)</h1>', html, re.DOTALL)
            self.assertEqual(len(h1_matches), 1)

            # Check 600+ words in content
            lp = LandingPage.objects.get(slug=slug)
            clean_content = re.sub(r'<[^>]+>', ' ', lp.content)
            word_count = len(clean_content.split())
            self.assertGreaterEqual(word_count, 600, f'{slug} content has only {word_count} words')

            # Check FAQ block present
            self.assertIn('Frequently Asked Questions', html)

            # Check BreadcrumbList in JSON-LD
            self.assertIn('"@type": "BreadcrumbList"', html)

    def test_blog_pages_exist_and_meet_requirements(self):
        from core.models import BlogPost

        # Test index
        res_idx = self.client.get('/blog/')
        self.assertEqual(res_idx.status_code, 200)

        # Test 3 articles
        posts = BlogPost.objects.filter(is_published=True)
        self.assertEqual(posts.count(), 3)
        for post in posts:
            res = self.client.get(post.get_absolute_url())
            self.assertEqual(res.status_code, 200)
            html = res.content.decode('utf-8')

            # Title <= 60 chars (inside title tag)
            self.assertLessEqual(len(post.title), 60)

            # Meta description 150-160 chars
            desc_len = len(post.meta_description)
            self.assertGreaterEqual(desc_len, 150)
            self.assertLessEqual(desc_len, 160)

            # 600+ words
            clean_content = re.sub(r'<[^>]+>', ' ', post.content)
            word_count = len(clean_content.split())
            self.assertGreaterEqual(word_count, 600)

            # BlogPosting in schema
            self.assertIn('"@type": "BlogPosting"', html)

    def test_sitemap_xml_includes_all_pages_and_lastmod(self):
        response = self.client.get('/sitemap.xml')
        self.assertEqual(response.status_code, 200)
        xml = response.content.decode('utf-8')
        self.assertIn('<lastmod>', xml)

        # Check landing pages
        self.assertIn('/website-developer-ahmedabad/', xml)
        self.assertIn('/whatsapp-automation-for-business/', xml)
        self.assertIn('/clinic-website-development/', xml)
        self.assertIn('/restaurant-website-development/', xml)
        self.assertIn('/coaching-class-website-development/', xml)

        # Check blog
        self.assertIn('/blog/', xml)
        self.assertIn('/blog/website-development-cost-in-ahmedabad/', xml)
        self.assertIn('/blog/why-whatsapp-automation-beats-contact-forms/', xml)
        self.assertIn('/blog/local-seo-guide-for-ahmedabad-businesses/', xml)

    def test_og_image_and_performance_attributes(self):
        # 1. OG Image exists with 1200x630
        from PIL import Image
        og_path = os.path.join(settings.BASE_DIR, 'static', 'core', 'img', 'og-image.png')
        self.assertTrue(os.path.exists(og_path))
        with Image.open(og_path) as img:
            self.assertEqual(img.size, (1200, 630))

        # 2. Image attributes on home page
        response = self.client.get('/')
        html = response.content.decode('utf-8')
        img_tags = re.findall(r'<img[^>]+>', html)
        for tag in img_tags:
            self.assertIn('width=', tag)
            self.assertIn('height=', tag)
            self.assertIn('loading="lazy"', tag)

        # 3. Chatzy is loaded via deferred script
        self.assertNotIn('<link rel="stylesheet" href="https://chatzy-kb-store.s3.amazonaws.com', html)
        self.assertIn('chatzyLoaded', html)






