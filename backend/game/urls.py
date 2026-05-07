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
]
