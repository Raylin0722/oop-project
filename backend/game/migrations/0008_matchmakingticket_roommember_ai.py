import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('game', '0007_rename_password_re_email_token_idx_password_re_email_c29bfe_idx'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='roommember',
            name='ai_name',
            field=models.CharField(blank=True, max_length=50),
        ),
        migrations.AddField(
            model_name='roommember',
            name='is_ai',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='roommember',
            name='user',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='room_memberships', to=settings.AUTH_USER_MODEL),
        ),
        migrations.CreateModel(
            name='MatchmakingTicket',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('score', models.IntegerField(default=0)),
                ('status', models.IntegerField(choices=[(0, 'Waiting'), (1, 'Matched'), (2, 'Cancelled')], default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('matched_room', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='matchmaking_tickets', to='game.room')),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='matchmaking_ticket', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'matchmaking_ticket',
                'indexes': [models.Index(fields=['status', 'score', 'created_at'], name='matchmaking_status_6f9e7d_idx')],
            },
        ),
    ]
