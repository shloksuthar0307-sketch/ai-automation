from django.conf import settings
from axes.backends import AxesStandaloneBackend
from axes.handlers.proxy import AxesProxyHandler


class SitewrightAxesBackend(AxesStandaloneBackend):
    """
    Axes standalone backend that gracefully handles test clients where request is None,
    and respects AXES_ONLY_ADMIN_SITE by delegating non-admin site requests to subsequent backends.
    """
    def authenticate(self, request=None, username=None, password=None, **kwargs):
        if request is None:
            return None
        if getattr(settings, 'AXES_ONLY_ADMIN_SITE', False):
            handler = AxesProxyHandler.get_implementation()
            if not handler.is_admin_request(request):
                return None
        return super().authenticate(request, username=username, password=password, **kwargs)

