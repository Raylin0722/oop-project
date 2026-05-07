from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone


class PlayerProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        primary_key=True,
        related_name='player_profile',
    )
    nickname = models.CharField(max_length=50)
    total_score = models.IntegerField(default=0)
    win_rate = models.FloatField(default=0.0)

    class Meta:
        db_table = 'player_profile'

    def __str__(self):
        return self.nickname


class Room(models.Model):
    class Status(models.IntegerChoices):
        WAITING = 0, 'Waiting'
        PLAYING = 1, 'Playing'
        FULL = 2, 'Full'

    room_id = models.BigAutoField(primary_key=True)
    host = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='hosted_rooms',
    )
    status = models.IntegerField(choices=Status.choices, default=Status.WAITING)
    room_password = models.CharField(max_length=128, blank=True)

    class Meta:
        db_table = 'room'

    def __str__(self):
        return f'Room {self.room_id}'


class MatchRecord(models.Model):
    match_id = models.BigAutoField(primary_key=True)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'match_record'

    def __str__(self):
        return f'Match {self.match_id}'


class MatchParticipant(models.Model):
    match = models.ForeignKey(
        MatchRecord,
        on_delete=models.CASCADE,
        related_name='participants',
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='match_participations',
    )
    player_rank = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(4)],
    )
    score_change = models.IntegerField(default=0)

    class Meta:
        db_table = 'match_participant'
        constraints = [
            models.UniqueConstraint(
                fields=['match', 'user'],
                name='unique_match_participant',
            ),
            models.UniqueConstraint(
                fields=['match', 'player_rank'],
                name='unique_match_player_rank',
            ),
        ]

    def __str__(self):
        return f'{self.user} in {self.match}'


class EmailVerificationCode(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='email_verification_codes',
    )
    email = models.EmailField()
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    verified_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'email_verification_code'
        indexes = [
            models.Index(fields=['email', 'code']),
        ]

    @property
    def is_verified(self):
        return self.verified_at is not None

    @property
    def is_expired(self):
        return timezone.now() > self.expires_at

    def __str__(self):
        return f'{self.email} ({self.code})'


class PasswordResetCode(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='password_reset_codes',
    )
    email = models.EmailField()
    token = models.CharField(max_length=128)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    used_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'password_reset_code'
        indexes = [
            models.Index(fields=['email', 'token']),
        ]

    @property
    def is_used(self):
        return self.used_at is not None

    @property
    def is_expired(self):
        return timezone.now() > self.expires_at

    def __str__(self):
        return self.email
