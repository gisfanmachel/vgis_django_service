from django.urls import re_path
from my_project.ws import ws_comsumers

websocket_urlpatterns = [
    #re_path("^alert/(?P<group>\w+)", alert_info_comsumers.AlertConsumer.as_asgi()),
    re_path("ws/msg", ws_comsumers.AlertConsumer.as_asgi()),
]


