# -*- coding: utf-8 -*-
# Generated by Django 1.11.8 on 2019-02-01 21:41
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('user_app', '0002_minedrepos'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='MinedRepos',
            new_name='MinedRepo',
        ),
    ]
