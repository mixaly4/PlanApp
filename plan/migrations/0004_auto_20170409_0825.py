# -*- coding: utf-8 -*-
# Generated by Django 1.10.6 on 2017-04-09 08:25
from __future__ import unicode_literals

import datetime
from django.db import migrations, models
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        ('plan', '0003_auto_20170323_2327'),
    ]

    operations = [
        migrations.AddField(
            model_name='project',
            name='update',
            field=models.DateTimeField(default=datetime.datetime(2017, 4, 9, 8, 25, 36, 899248, tzinfo=utc)),
        ),
        migrations.AddField(
            model_name='task',
            name='update',
            field=models.DateTimeField(default=datetime.datetime(2017, 4, 9, 8, 25, 36, 900231, tzinfo=utc)),
        ),
    ]