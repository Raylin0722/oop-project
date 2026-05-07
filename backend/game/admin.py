from django.contrib import admin

from .models import (
    EmailVerificationCode,
    MatchParticipant,
    MatchRecord,
    PasswordResetCode,
    PlayerProfile,
    Room,
)


@admin.register(PlayerProfile)
class PlayerProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'nickname', 'total_score', 'win_rate')
    search_fields = ('user__username', 'nickname')


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ('room_id', 'host', 'status')
    list_filter = ('status',)
    search_fields = ('host__username',)


@admin.register(MatchRecord)
class MatchRecordAdmin(admin.ModelAdmin):
    list_display = ('match_id', 'start_time', 'end_time')


@admin.register(MatchParticipant)
class MatchParticipantAdmin(admin.ModelAdmin):
    list_display = ('match', 'user', 'player_rank', 'score_change')
    list_filter = ('player_rank',)
    search_fields = ('user__username',)


@admin.register(EmailVerificationCode)
class EmailVerificationCodeAdmin(admin.ModelAdmin):
    list_display = ('email', 'user', 'code', 'expires_at', 'verified_at')
    list_filter = ('verified_at',)
    search_fields = ('email', 'user__username')


@admin.register(PasswordResetCode)
class PasswordResetCodeAdmin(admin.ModelAdmin):
    list_display = ('email', 'user', 'expires_at', 'used_at')
    list_filter = ('used_at',)
    search_fields = ('email', 'user__username')
