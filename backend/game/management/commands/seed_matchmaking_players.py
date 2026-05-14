from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from game.models import PlayerProfile


DEFAULT_PASSWORD = 'TestPass123!'
DEFAULT_PLAYERS = [
    ('mm_1000_a', 1000),
    ('mm_1080_a', 1080),
    ('mm_1090_a', 1090),
    ('mm_1095_a', 1095),
    ('mm_1150_a', 1150),
    ('mm_1160_a', 1160),
    ('mm_1170_a', 1170),
    ('mm_1250_a', 1250),
    ('mm_1260_a', 1260),
    ('mm_1270_a', 1270),
    ('mm_1400_a', 1400),
]


class Command(BaseCommand):
    help = 'Creates test users with trophy counts for matchmaking tests.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--password',
            default=DEFAULT_PASSWORD,
            help='Password assigned to all seeded users.',
        )

    def handle(self, *args, **options):
        User = get_user_model()
        password = options['password']

        for username, trophies in DEFAULT_PLAYERS:
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'email': f'{username}@example.com',
                    'is_active': True,
                },
            )
            if created:
                user.set_password(password)
                user.save(update_fields=['password'])
            elif not user.is_active:
                user.is_active = True
                user.save(update_fields=['is_active'])

            profile, _ = PlayerProfile.objects.get_or_create(
                user=user,
                defaults={'nickname': username},
            )
            profile.nickname = username
            profile.total_score = trophies
            profile.save(update_fields=['nickname', 'total_score'])

            action = 'created' if created else 'updated'
            self.stdout.write(f'{action}: {username} ({trophies} trophies)')

        self.stdout.write(self.style.SUCCESS(
            f'Seeded {len(DEFAULT_PLAYERS)} matchmaking players. Password: {password}'
        ))
