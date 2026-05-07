import json
import random
import secrets
from datetime import timedelta
from urllib.parse import urlencode

from django.conf import settings
from django.contrib.auth import authenticate, get_user_model, login, logout
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.core.validators import validate_email
from django.db import transaction
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from .models import EmailVerificationCode, PasswordResetCode, PlayerProfile

User = get_user_model()


def _json_body(request):
    try:
        return json.loads(request.body.decode('utf-8') or '{}')
    except json.JSONDecodeError:
        return None


def _error(message, status=400, code='bad_request'):
    return JsonResponse({'error': {'code': code, 'message': message}}, status=status)


def _user_payload(user):
    profile = getattr(user, 'player_profile', None)
    return {
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'email_verified': user.is_active,
        'nickname': profile.nickname if profile else '',
        'total_score': profile.total_score if profile else 0,
        'win_rate': profile.win_rate if profile else 0.0,
    }


def _create_verification_code(user):
    code = f'{random.SystemRandom().randint(0, 999999):06d}'
    verification = EmailVerificationCode.objects.create(
        user=user,
        email=user.email,
        code=code,
        expires_at=timezone.now() + timedelta(minutes=15),
    )
    send_mail(
        subject='Email verification code',
        message=f'Your verification code is {code}. It expires in 15 minutes.',
        from_email=None,
        recipient_list=[user.email],
        fail_silently=False,
    )
    return verification


def _generate_code():
    return f'{random.SystemRandom().randint(0, 999999):06d}'


def _create_password_reset_code(user):
    token = secrets.token_urlsafe(48)
    reset_link = f'{settings.FRONTEND_BASE_URL}/?{urlencode({"reset_email": user.email, "reset_token": token})}'
    send_mail(
        subject='Password reset link',
        message=(
            'Use this link to reset your password. '
            'It expires in 15 minutes and can only be used once.\n\n'
            f'{reset_link}'
        ),
        from_email=None,
        recipient_list=[user.email],
        fail_silently=False,
    )
    PasswordResetCode.objects.filter(
        user=user,
        used_at__isnull=True,
    ).delete()
    reset_code = PasswordResetCode.objects.create(
        user=user,
        email=user.email,
        token=token,
        expires_at=timezone.now() + timedelta(minutes=15),
    )
    return reset_code


@csrf_exempt
@require_http_methods(['POST'])
def register(request):
    data = _json_body(request)
    if data is None:
        return _error('Invalid JSON body.')

    username = str(data.get('username', '')).strip()
    password = str(data.get('password', ''))
    password_confirm = str(data.get('password_confirm', ''))
    email = str(data.get('email', '')).strip().lower()
    nickname = str(data.get('nickname', '')).strip() or username

    if not username or not password or not password_confirm or not email:
        return _error('username, password, password_confirm, and email are required.')
    if len(password) < 8:
        return _error('password must be at least 8 characters.')
    if password != password_confirm:
        return _error('passwords do not match.', code='password_mismatch')

    try:
        validate_email(email)
    except ValidationError:
        return _error('email format is invalid.')

    if User.objects.filter(username=username).exists():
        return _error('username already exists.', code='username_exists')
    if User.objects.filter(email__iexact=email).exists():
        return _error('email already exists.', code='email_exists')

    with transaction.atomic():
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            is_active=False,
        )
        PlayerProfile.objects.create(user=user, nickname=nickname)
        _create_verification_code(user)

    return JsonResponse(
        {
            'user': _user_payload(user),
            'message': 'Registration successful. Please verify your email.',
        },
        status=201,
    )


@csrf_exempt
@require_http_methods(['POST'])
def verify_email(request):
    data = _json_body(request)
    if data is None:
        return _error('Invalid JSON body.')

    email = str(data.get('email', '')).strip().lower()
    code = str(data.get('code', '')).strip()
    if not email or not code:
        return _error('email and code are required.')

    verification = (
        EmailVerificationCode.objects
        .select_related('user')
        .filter(email__iexact=email, code=code, verified_at__isnull=True)
        .order_by('-created_at')
        .first()
    )
    if verification is None:
        return _error('verification code is invalid.', status=404, code='invalid_code')
    if verification.is_expired:
        return _error('verification code is expired.', code='expired_code')

    user = verification.user
    user.email = verification.email
    user.is_active = True
    verification.verified_at = timezone.now()

    with transaction.atomic():
        user.save(update_fields=['email', 'is_active'])
        verification.save(update_fields=['verified_at'])

    return JsonResponse({'user': _user_payload(user), 'message': 'Email verified.'})


@csrf_exempt
@require_http_methods(['POST'])
def resend_verification(request):
    data = _json_body(request)
    if data is None:
        return _error('Invalid JSON body.')

    email = str(data.get('email', '')).strip().lower()
    user = User.objects.filter(email__iexact=email, is_active=False).first()
    if user is None:
        return _error('pending user not found.', status=404, code='pending_user_not_found')

    _create_verification_code(user)
    return JsonResponse({'message': 'Verification code sent.'})


@csrf_exempt
@require_http_methods(['POST'])
def request_password_reset(request):
    data = _json_body(request)
    if data is None:
        return _error('Invalid JSON body.')

    email = str(data.get('email', '')).strip().lower()
    if not email:
        return _error('email is required.')

    try:
        validate_email(email)
    except ValidationError:
        return _error('email format is invalid.')

    user = User.objects.filter(email__iexact=email, is_active=True).first()
    if user is not None:
        _create_password_reset_code(user)

    return JsonResponse({
        'message': 'If the email is registered, a password reset link has been sent.',
    })


@csrf_exempt
@require_http_methods(['POST'])
def reset_password(request):
    data = _json_body(request)
    if data is None:
        return _error('Invalid JSON body.')

    email = str(data.get('email', '')).strip().lower()
    token = str(data.get('token', '')).strip()
    new_password = str(data.get('new_password', ''))
    new_password_confirm = str(data.get('new_password_confirm', ''))
    if not email or not token or not new_password or not new_password_confirm:
        return _error('email, token, new_password, and new_password_confirm are required.')
    if len(new_password) < 8:
        return _error('new_password must be at least 8 characters.')
    if new_password != new_password_confirm:
        return _error('passwords do not match.', code='password_mismatch')

    reset_code = (
        PasswordResetCode.objects
        .select_related('user')
        .filter(email__iexact=email, token=token, used_at__isnull=True)
        .order_by('-created_at')
        .first()
    )
    if reset_code is None:
        return _error('password reset link is invalid.', status=404, code='invalid_token')
    if reset_code.is_expired:
        return _error('password reset link is expired.', code='expired_token')

    user = reset_code.user
    user.set_password(new_password)
    reset_code.used_at = timezone.now()

    with transaction.atomic():
        user.save(update_fields=['password'])
        reset_code.delete()

    return JsonResponse({'message': 'Password reset successful. You can log in now.'})


@csrf_exempt
@require_http_methods(['POST'])
def login_view(request):
    data = _json_body(request)
    if data is None:
        return _error('Invalid JSON body.')

    identifier = str(data.get('username', data.get('email', ''))).strip()
    password = str(data.get('password', ''))
    if not identifier or not password:
        return _error('username/email and password are required.')

    user = User.objects.filter(email__iexact=identifier).first()
    if user is None:
        user = User.objects.filter(username=identifier).first()
    username = user.username if user else identifier
    user = authenticate(request, username=username, password=password)
    if user is None:
        return _error('login failed.', status=401, code='invalid_credentials')
    if not user.is_active:
        return _error('email is not verified.', status=403, code='email_not_verified')

    login(request, user)
    return JsonResponse({'user': _user_payload(user)})


@csrf_exempt
@require_http_methods(['POST'])
def logout_view(request):
    logout(request)
    return JsonResponse({'message': 'Logged out.'})


@require_http_methods(['GET'])
def me(request):
    if not request.user.is_authenticated:
        return _error('not authenticated.', status=401, code='not_authenticated')
    return JsonResponse({'user': _user_payload(request.user)})
