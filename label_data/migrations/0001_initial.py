# -*- coding: utf-8 -*-
# Generated by Django 1.10.7 on 2017-08-07 10:30
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='LabelData',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_date', models.DateField()),
                ('total_data', models.IntegerField(default=0)),
                ('spend_time', models.FloatField(default=0)),
                ('efficiency', models.FloatField(default=0)),
                ('username', models.CharField(max_length=50)),
                ('label_score', models.FloatField(default=0)),
                ('is_on_duty', models.BooleanField(default=1)),
                ('remark', models.CharField(max_length=50)),
                ('remark_flag', models.IntegerField(default=0)),
            ],
            options={
                'db_table': 'label_data',
            },
        ),
    ]
