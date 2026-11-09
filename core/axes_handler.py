from django.conf import settings
from axes.handlers.database import AxesDatabaseHandler


class SitewrightAxesHandler(AxesDatabaseHandler):
    """
    Database handler that ensures AXES_ONLY_ADMIN_SITE is respected during
    user_login_failed signal processing, so custom portal logins are not tracked by Axes.
    """
    def user_login_failed(self, sender, credentials, request=None, **kwargs):
        if getattr(settings, 'AXES_ONLY_ADMIN_SITE', False):
            if request is not None and not self.is_admin_request(request):
                return
        return super().user_login_failed(sender, credentials, request=request, **kwargs)

