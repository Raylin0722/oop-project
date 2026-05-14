import time

from django.core.management.base import BaseCommand
from django.db import close_old_connections

from game.models import MatchmakingTicket
from game.views import _try_complete_matchmaking


class Command(BaseCommand):
    help = 'Runs the matchmaking queue worker.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--interval',
            default=1.0,
            type=float,
            help='Seconds between matchmaking scans.',
        )
        parser.add_argument(
            '--once',
            action='store_true',
            help='Run one scan and exit.',
        )

    def handle(self, *args, **options):
        interval = options['interval']
        once = options['once']
        self.stdout.write(self.style.SUCCESS('Matchmaking worker started.'))

        while True:
            close_old_connections()
            processed = self.process_once()
            close_old_connections()

            if once:
                self.stdout.write(f'Matchmaking worker processed {processed} scan(s).')
                return

            time.sleep(interval)

    def process_once(self):
        ticket = (
            MatchmakingTicket.objects
            .select_related('user')
            .filter(status=MatchmakingTicket.Status.WAITING)
            .order_by('created_at', 'id')
            .first()
        )
        if ticket is None:
            return 0

        _try_complete_matchmaking(ticket.user)
        return 1
