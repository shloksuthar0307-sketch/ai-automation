import csv
import json
import logging
import re
from datetime import datetime
from urllib.parse import quote

from django.conf import settings
from django.core.cache import cache
from django.core.mail import send_mail
from django.core.paginator import Paginator
from django.db.models import Q, Count, Sum, Case, When, IntegerField
from django.http import JsonResponse, HttpResponse, HttpResponseForbidden, StreamingHttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_http_methods
from django.contrib.auth import authenticate, login, logout

from .models import QuoteRequest, PortfolioProject, Testimonial, FAQ, PLAN_PRICES
from .forms import QuoteForm

logger = logging.getLogger(__name__)


# ==============================================================================
# SECURITY UTILITIES
# ==============================================================================

def get_client_ip(request):
    """
    Extracts the client's real IP address from proxy headers or remote address.
    Only trusts HTTP_X_FORWARDED_FOR if settings.TRUSTED_PROXY_COUNT > 0.
    If X-Forwarded-For has fewer entries than TRUSTED_PROXY_COUNT, falls back
    to REMOTE_ADDR rather than trusting ips[0].
    """
    remote_addr = request.META.get('REMOTE_ADDR', '127.0.0.1')
    trusted_proxy_count = getattr(settings, 'TRUSTED_PROXY_COUNT', 0)

    if trusted_proxy_count > 0:
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ips = [ip.strip() for ip in x_forwarded_for.split(',') if ip.strip()]
            if len(ips) >= trusted_proxy_count:
                return ips[-trusted_proxy_count]
    return remote_addr


def is_rate_limited(key, limit, window_seconds):
    """
    Lightweight, atomic cache-based rate limiter using cache.add and cache.incr.
    Returns True if request exceeds limit within the sliding window, False otherwise.
    """
    try:
        cache.add(key, 0, timeout=window_seconds)
        count = cache.incr(key)
    except Exception:
        current = cache.get(key)
        if current is None:
            cache.set(key, 1, timeout=window_seconds)
            return False
        count = current + 1
        cache.set(key, count, timeout=window_seconds)
    return count > limit


def sanitize_csv_cell(value):
    """
    Neutralizes CSV / Spreadsheet Formula Injection (CWE-1236).
    If a string starts with =, +, -, @, tab, or carriage return, prepend an apostrophe
    so spreadsheet software (Excel, Google Sheets, LibreOffice) treats it purely as text.
    """
    if value is None:
        return ""
    val_str = str(value)
    if val_str.startswith(('=', '+', '-', '@', '\t', '\r', '%')):
        return f"'{val_str}"
    return val_str


def is_admin_authorized(user):
    """
    Strict authorization check: User must be authenticated, active, and staff/superuser.
    """
    return user.is_authenticated and user.is_active and user.is_staff and user.is_superuser


# ==============================================================================
# PUBLIC CLIENT VIEWS
# ==============================================================================

@ensure_csrf_cookie
def index(request):
    form = QuoteForm()
    projects = PortfolioProject.objects.filter(is_published=True)
    testimonials = Testimonial.objects.filter(is_published=True)
    faqs = FAQ.objects.filter(is_published=True)
    return render(request, 'core/index.html', {
        'form': form,
        'projects': projects,
        'testimonials': testimonials,
        'faqs': faqs,
    })


@require_http_methods(["POST"])
def submit_quote(request):
    # 1. Rate Limiting Defense (10 quote requests per 60 seconds per IP)
    client_ip = get_client_ip(request)
    rate_limit_key = f"quote_rate_{client_ip}"
    if is_rate_limited(rate_limit_key, limit=10, window_seconds=60):
        return JsonResponse({
            'success': False,
            'error': 'Too many requests. Please wait a minute before submitting another quote.'
        }, status=429)

    # 2. Parse Form Data
    if request.content_type == 'application/json':
        try:
            data = json.loads(request.body.decode('utf-8'))
        except (json.JSONDecodeError, UnicodeDecodeError):
            return JsonResponse({'success': False, 'error': 'Invalid JSON format'}, status=400)
        if not isinstance(data, dict):
            return JsonResponse({'success': False, 'error': 'Invalid JSON format'}, status=400)
        form = QuoteForm(data)
    else:
        form = QuoteForm(request.POST)

    # 3. Form Validation
    if form.is_valid():
        # Anti-Bot Honeypot check: If either honeypot field is filled, silently discard
        if form.cleaned_data.get('contact_ref_url') or form.cleaned_data.get('website_trap'):
            # Return success to trick bot into thinking it succeeded, but persist nothing
            return JsonResponse({
                'success': True,
                'message': 'Thank you! We have received your idea and will send a free first-draft and fixed quote.',
                'quote_id': 0,
                'email': form.cleaned_data.get('email', ''),
            })

        quote = form.save()

        # Send notification to email (sanitizing subject against CRLF header injection)
        raw_subject = f"New Website Quote Request: {quote.business_name or quote.name} ({quote.plan})"
        clean_subject = re.sub(r'[\r\n]+', ' ', raw_subject)

        message = (
            f"=== NEW WEBSITE ENQUIRY ===\n"
            f"Name: {quote.name}\n"
            f"Email: {quote.email}\n"
            f"Phone: {quote.phone or 'Not provided'}\n"
            f"Business: {quote.business_name or 'Not provided'}\n"
            f"Plan: {quote.plan}\n\n"
            f"Project Details:\n{quote.brief or 'No details provided'}\n"
            f"==========================="
        )

        admin_email = getattr(settings, 'ADMIN_NOTIFICATION_EMAIL', 'admin@sitewright.ai')
        from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'no-reply@sitewright.ai')

        try:
            send_mail(
                clean_subject,
                message,
                from_email,
                [admin_email],
                fail_silently=False,
            )
        except Exception:
            logger.exception("Failed to send quote notification email for quote ID %s", quote.id)

        return JsonResponse({
            'success': True,
            'message': 'Thank you! We have received your idea and will send a free first-draft and fixed quote.',
            'quote_id': quote.id,
            'email': quote.email,
        })
    else:
        errors = {field: [str(e) for e in errs] for field, errs in form.errors.items()}
        return JsonResponse({'success': False, 'errors': errors}, status=400)


# ==============================================================================
# UNIQUE & SECURE ADMIN PORTAL (ADMIN ONLY)
# ==============================================================================

def admin_login_view(request):
    # If already logged in as authorized admin, redirect straight to dashboard or validated next
    if is_admin_authorized(request.user):
        raw_next = request.GET.get('next', '')
        if raw_next and url_has_allowed_host_and_scheme(
            raw_next,
            allowed_hosts={request.get_host()},
            require_https=request.is_secure()
        ):
            return redirect(raw_next)
        return redirect('core:admin_dashboard')
    elif request.user.is_authenticated:
        # Non-admin user is logged in: log them out to protect the admin portal
        logout(request)

    error_message = None
    client_ip = get_client_ip(request)

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        # Preserve leading/trailing spaces in password
        password = request.POST.get('password', '')

        fail_key = f"login_fails_{client_ip}_{username}"
        lockout_key = f"login_locked_{client_ip}_{username}"

        # Check IP + username lockout status
        if cache.get(lockout_key):
            error_message = "Too many failed attempts. Login locked for 5 minutes for security."
            return render(request, 'core/admin_login.html', {
                'error_message': error_message,
                'next': request.POST.get('next') or request.GET.get('next', '')
            }, status=429)

        user = authenticate(request, username=username, password=password)
        if user is not None:
            if is_admin_authorized(user):
                # Reset failure counter on successful login
                cache.delete(fail_key)
                login(request, user)
                raw_next = request.POST.get('next') or request.GET.get('next') or ''
                if raw_next and url_has_allowed_host_and_scheme(
                    raw_next,
                    allowed_hosts={request.get_host()},
                    require_https=request.is_secure()
                ):
                    return redirect(raw_next)
                return redirect('core:admin_dashboard')
            else:
                error_message = "Access Denied: Only administrators can access this portal."
        else:
            # Atomic increment of failed attempts
            try:
                cache.add(fail_key, 0, timeout=300)
                fails = cache.incr(fail_key)
            except Exception:
                fails = (cache.get(fail_key) or 0) + 1
                cache.set(fail_key, fails, timeout=300)

            if fails >= 5:
                cache.set(lockout_key, True, timeout=300)  # 5 minutes lockout
                cache.delete(fail_key)
                error_message = "Too many failed attempts. Login locked for 5 minutes for security."
                return render(request, 'core/admin_login.html', {
                    'error_message': error_message,
                    'next': request.POST.get('next') or request.GET.get('next', '')
                }, status=429)
            else:
                attempts_left = 5 - fails
                error_message = f"Invalid administrator credentials. ({attempts_left} attempts remaining)"

    return render(request, 'core/admin_login.html', {
        'error_message': error_message,
        'next': request.GET.get('next', '')
    })


@require_http_methods(["POST"])
def admin_logout_view(request):
    logout(request)
    return redirect('core:admin_login')


def admin_dashboard_view(request):
    # Strict admin check: unauthenticated -> redirect to login; non-admin -> 403 Forbidden
    if not request.user.is_authenticated:
        full_path = request.get_full_path()
        return redirect(f"{reverse('core:admin_login')}?next={quote(full_path, safe='')}")
    if not is_admin_authorized(request.user):
        return HttpResponseForbidden("Access Denied: Administrator privileges required.")

    # Search & Filter
    query = request.GET.get('q', '').strip()
    status_filter = request.GET.get('status', '').strip()
    plan_filter = request.GET.get('plan', '').strip()

    quotes_qs = QuoteRequest.objects.all()

    if query:
        quotes_qs = quotes_qs.filter(
            Q(name__icontains=query) |
            Q(email__icontains=query) |
            Q(business_name__icontains=query) |
            Q(phone__icontains=query) |
            Q(brief__icontains=query)
        )

    if status_filter and status_filter != 'all':
        quotes_qs = quotes_qs.filter(status=status_filter)

    if plan_filter and plan_filter != 'all':
        quotes_qs = quotes_qs.filter(plan=plan_filter)

    quotes_qs = quotes_qs.order_by('-created_at')

    # Paginate results (25 per page)
    paginator = Paginator(quotes_qs, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Build preserved query string for pagination links
    query_params = request.GET.copy()
    query_params.pop('page', None)
    preserved_filters = query_params.urlencode()

    # Compute key stats & metrics in one aggregate DB query
    price_cases = [
        When(plan=plan, then=price)
        for plan, price in PLAN_PRICES.items()
    ]
    stats = QuoteRequest.objects.aggregate(
        total_count=Count('id'),
        new_count=Count('id', filter=Q(status='new')),
        in_progress_count=Count('id', filter=Q(status='in_progress')),
        completed_count=Count('id', filter=Q(status='completed')),
        pipeline_value=Sum(
            Case(*price_cases, default=0, output_field=IntegerField()),
            filter=~Q(status='archived')
        )
    )

    context = {
        'quotes': page_obj,
        'page_obj': page_obj,
        'paginator': paginator,
        'preserved_filters': preserved_filters,
        'quotes_count': paginator.count,
        'total_count': stats['total_count'] or 0,
        'new_count': stats['new_count'] or 0,
        'in_progress_count': stats['in_progress_count'] or 0,
        'completed_count': stats['completed_count'] or 0,
        'pipeline_value': stats['pipeline_value'] or 0,
        'search_query': query,
        'selected_status': status_filter or 'all',
        'selected_plan': plan_filter or 'all',
        'status_choices': QuoteRequest.STATUS_CHOICES,
        'plan_choices': QuoteRequest.PLAN_CHOICES,
    }
    return render(request, 'core/admin_dashboard.html', context)


@require_http_methods(["POST"])
def admin_update_status(request, quote_id):
    if not is_admin_authorized(request.user):
        return JsonResponse({'success': False, 'error': 'Unauthorized admin access required'}, status=403)

    quote = get_object_or_404(QuoteRequest, id=quote_id)
    
    if request.content_type == 'application/json':
        try:
            data = json.loads(request.body.decode('utf-8'))
        except Exception:
            data = request.POST
    else:
        data = request.POST

    new_status = data.get('status', '').strip()
    valid_statuses = [c[0] for c in QuoteRequest.STATUS_CHOICES]

    if new_status in valid_statuses:
        quote.status = new_status
        quote.save(update_fields=['status'])
        return JsonResponse({
            'success': True,
            'quote_id': quote.id,
            'new_status': quote.status,
            'status_display': quote.get_status_display()
        })
    else:
        return JsonResponse({'success': False, 'error': 'Invalid status'}, status=400)


@require_http_methods(["POST"])
def admin_delete_quote(request, quote_id):
    if not is_admin_authorized(request.user):
        return JsonResponse({'success': False, 'error': 'Unauthorized admin access required'}, status=403)

    quote = get_object_or_404(QuoteRequest, id=quote_id)
    quote_id_val = quote.id
    quote.delete()

    if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.content_type == 'application/json':
        return JsonResponse({'success': True, 'deleted_id': quote_id_val})
    return redirect('core:admin_dashboard')


def admin_export_csv(request):
    if not is_admin_authorized(request.user):
        return HttpResponseForbidden("Access Denied: Administrator privileges required.")

    response = HttpResponse(content_type='text/csv')
    filename = f"sitewright_leads_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'

    writer = csv.writer(response)
    writer.writerow([
        'ID', 'Date', 'Client Name', 'Email', 'Phone', 'Business Name', 'Package', 'Status', 'Project Brief'
    ])

    for q in QuoteRequest.objects.all().order_by('-created_at').iterator(chunk_size=1000):
        writer.writerow([
            q.id,
            q.created_at.strftime('%Y-%m-%d %H:%M'),
            sanitize_csv_cell(q.name),
            sanitize_csv_cell(q.email),
            sanitize_csv_cell(q.phone),
            sanitize_csv_cell(q.business_name),
            sanitize_csv_cell(q.plan),
            q.get_status_display(),
            sanitize_csv_cell(q.brief)
        ])

    return response


# ==============================================================================
# LEGAL & SEARCH ENGINE VIEWS
# ==============================================================================

def privacy_view(request):
    """
    Renders the privacy policy tailored to India's DPDP Act 2023.
    """
    return render(request, 'core/privacy.html')


def terms_view(request):
    """
    Renders terms of service for freelance web development clients.
    """
    return render(request, 'core/terms.html')


def robots_txt_view(request):
    """
    Generates dynamic robots.txt pointing to the XML sitemap and shielding admin areas.
    """
    sitemap_url = request.build_absolute_uri(reverse('django.contrib.sitemaps.views.sitemap'))
    lines = [
        "User-agent: *",
        "Allow: /",
        "Disallow: /portal-hq/",
        f"Sitemap: {sitemap_url}"
    ]
    return HttpResponse("\n".join(lines), content_type="text/plain")
