import logging
from django.apps import AppConfig
from django.conf import settings

logger = logging.getLogger(__name__)


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'

    def ready(self):
        debug = getattr(settings, 'DEBUG', False)
        trusted_proxy_count = getattr(settings, 'TRUSTED_PROXY_COUNT', 0)
        redis_url = getattr(settings, 'REDIS_URL', None)
        if not debug and trusted_proxy_count == 0 and not redis_url:
            logger.warning(
                "Security & Performance Warning: DEBUG is False, TRUSTED_PROXY_COUNT is 0, "
                "and REDIS_URL is unset. Client IP resolution and rate limiting may not function "
                "properly across multiple workers or reverse proxies."
            )
