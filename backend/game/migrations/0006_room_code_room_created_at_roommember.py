from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


def populate_room_codes(apps, schema_editor):
    Room = apps.get_model('game', 'Room')
    used_codes = set(Room.objects.exclude(code__isnull=True).values_list('code', flat=True))
    for room in Room.objects.filter(code__isnull=True).order_by('room_id'):
        base = room.room_id % 1000000
        code = f'{base:06d}'
        while code in used_codes:
            base = (base + 1) % 1000000
            code = f'{base:06d}'
        room.code = code
        room.save(update_fields=['code'])
        used_codes.add(code)


class Migration(migrations.Migration):

    dependencies = [
        ('game', '0005_rename_password_reset_code_token'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='room',
            name='code',
            field=models.CharField(max_length=6, null=True, unique=True),
        ),
        migrations.AddField(
            model_name='room',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.RunPython(populate_room_codes, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='room',
            name='code',
            field=models.CharField(max_length=6, unique=True),
        ),
        migrations.CreateModel(
            name='RoomMember',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('is_ready', models.BooleanField(default=False)),
                ('joined_at', models.DateTimeField(auto_now_add=True)),
                ('room', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='members', to='game.room')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='room_memberships', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'room_member',
                'ordering': ['joined_at', 'id'],
                'constraints': [models.UniqueConstraint(fields=('room', 'user'), name='unique_room_member')],
            },
        ),
    ]
