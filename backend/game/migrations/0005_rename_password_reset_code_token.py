from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('game', '0004_alter_passwordresetcode_code'),
    ]

    operations = [
        migrations.RemoveIndex(
            model_name='passwordresetcode',
            name='password_re_email_2070ca_idx',
        ),
        migrations.RenameField(
            model_name='passwordresetcode',
            old_name='code',
            new_name='token',
        ),
        migrations.AddIndex(
            model_name='passwordresetcode',
            index=models.Index(fields=['email', 'token'], name='password_re_email_token_idx'),
        ),
    ]
