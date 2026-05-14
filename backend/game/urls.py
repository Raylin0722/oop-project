from django.urls import path

from . import views

urlpatterns = [
    path('auth/register/', views.register, name='register'),
    path('auth/verify-email/', views.verify_email, name='verify_email'),
    path('auth/resend-verification/', views.resend_verification, name='resend_verification'),
    path('auth/request-password-reset/', views.request_password_reset, name='request_password_reset'),
    path('auth/reset-password/', views.reset_password, name='reset_password'),
    path('auth/login/', views.login_view, name='login'),
    path('auth/logout/', views.logout_view, name='logout'),
    path('auth/me/', views.me, name='me'),
    path('rooms/create/', views.create_room, name='create_room'),
    path('rooms/join/', views.join_room, name='join_room'),
    path('rooms/current/', views.current_room, name='current_room'),
    path('rooms/<str:code>/ready/', views.set_room_ready, name='set_room_ready'),
    path('rooms/<str:code>/leave/', views.leave_room, name='leave_room'),
    path('rooms/<str:code>/kick/', views.kick_room_member, name='kick_room_member'),
    path('rooms/<str:code>/transfer-host/', views.transfer_room_host, name='transfer_room_host'),
    path('rooms/<str:code>/start/', views.start_room, name='start_room'),
    path('rooms/<str:code>/end/', views.end_room, name='end_room'),
    path('matchmaking/join/', views.join_matchmaking, name='join_matchmaking'),
    path('matchmaking/cancel/', views.cancel_matchmaking, name='cancel_matchmaking'),
    path('matchmaking/status/', views.matchmaking_status, name='matchmaking_status'),
]
