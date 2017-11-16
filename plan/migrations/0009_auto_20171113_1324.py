# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2017-11-13 13:24
from __future__ import unicode_literals

import datetime
from django.db import migrations, models
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        ('plan', '0008_auto_20170902_1252'),
    ]

    operations = [
        migrations.AlterField(
            model_name='holiday',
            name='date',
            field=models.DateField(db_index=True),
        ),
        migrations.AlterField(
            model_name='project',
            name='active',
            field=models.BooleanField(db_index=True, default=True),
        ),
        migrations.AlterField(
            model_name='project',
            name='update',
            field=models.DateTimeField(default=datetime.datetime(2017, 11, 13, 13, 24, 56, 70303, tzinfo=utc)),
        ),
        migrations.AlterField(
            model_name='staff',
            name='active',
            field=models.BooleanField(db_index=True, default=True),
        ),
        migrations.AlterField(
            model_name='task',
            name='active',
            field=models.BooleanField(db_index=True, default=True),
        ),
        migrations.AlterField(
            model_name='task',
            name='end_date',
            field=models.DateField(db_index=True),
        ),
        migrations.AlterField(
            model_name='task',
            name='start_date',
            field=models.DateField(db_index=True),
        ),
        migrations.AlterField(
            model_name='task',
            name='update',
            field=models.DateTimeField(default=datetime.datetime(2017, 11, 13, 13, 24, 56, 71162, tzinfo=utc)),
        ),
    ]
