# Generated by Django 5.0.6 on 2024-07-12 17:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('navigation', '0003_user_active_user_past_visits'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='step_pointer',
            field=models.IntegerField(default=0),
        ),
    ]
