from django.urls import re_path

from . import consumers

websocket_urlpatterns = [
    re_path(r'^ws/rooms/(?P<code>\d{6})/$', consumers.RoomConsumer.as_asgi()),
    re_path(r'^ws/matchmaking/$', consumers.MatchmakingConsumer.as_asgi()),
]
