from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    # Public routes
    path('', views.index, name='index'),
    path('privacy/', views.privacy_view, name='privacy'),
    path('terms/', views.terms_view, name='terms'),
    path('api/quote/', views.submit_quote, name='submit_quote'),
    path('health/', views.health_check_view, name='health_check'),
    path('healthz', views.health_check_view, name='healthz'),

    # Blog Routes
    path('blog/', views.blog_index, name='blog_index'),
    path('blog/<slug:slug>/', views.blog_detail, name='blog_detail'),

    # Unique & Secure Admin Portal (Strict Admin Only)
    path('portal-hq/dashboard/', views.admin_dashboard_view, name='admin_dashboard'),
    path('portal-hq/login/', views.admin_login_view, name='admin_login'),
    path('portal-hq/logout/', views.admin_logout_view, name='admin_logout'),
    path('portal-hq/quote/<int:quote_id>/update-status/', views.admin_update_status, name='admin_update_status'),
    path('portal-hq/quote/<int:quote_id>/delete/', views.admin_delete_quote, name='admin_delete_quote'),
    path('portal-hq/export-csv/', views.admin_export_csv, name='admin_export_csv'),

    # Phase 2 Keyword Landing Pages (Catch-all slug at root level)
    path('<slug:slug>/', views.landing_page_detail, name='landing_page'),
]
