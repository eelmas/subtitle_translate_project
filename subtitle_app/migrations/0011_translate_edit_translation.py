# Generated by Django 2.0.6 on 2018-07-22 17:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('subtitle_app', '0010_auto_20180722_1309'),
    ]

    operations = [
        migrations.AddField(
            model_name='translate',
            name='edit_translation',
            field=models.CharField(blank=True, max_length=250, null=True),
        ),
    ]
