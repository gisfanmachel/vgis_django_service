"""
ASGI config for my_project project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/3.1/howto/deployment/asgi/
"""

import os
from channels.routing import ProtocolTypeRouter,URLRouter
from . import routings
from channels.security.websocket import AllowedHostsOriginValidator
from my_project.ws.ws_comsumers import TokenAuthMiddleware
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'my_project.settings')


django_asgi_app = get_asgi_application()
application = ProtocolTypeRouter(
    {
        'http': django_asgi_app,
        'websocket':  AllowedHostsOriginValidator(
            TokenAuthMiddleware(
                URLRouter(routings.websocket_urlpatterns)
            )
        )
    }
)