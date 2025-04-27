from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/chat/(?P<case_id>\d+)/$', consumers.ChatConsumer.as_asgi()),
    re_path(r'ws/video/(?P<case_id>\d+)/$', consumers.VideoCallConsumer.as_asgi()),
]