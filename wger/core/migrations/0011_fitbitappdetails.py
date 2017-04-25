# -*- coding: utf-8 -*-
# Generated by Django 1.9.12 on 2017-04-25 13:03
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0010_auto_20170330_1116'),
    ]

    operations = [
        migrations.CreateModel(
            name='FitBitAppDetails',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('client_id', models.CharField(editable=False, max_length=300, verbose_name='OAuth 2.0 ClientID')),
                ('client_secret', models.CharField(editable=False, max_length=300, verbose_name='Client Secret')),
            ],
        ),
    ]
