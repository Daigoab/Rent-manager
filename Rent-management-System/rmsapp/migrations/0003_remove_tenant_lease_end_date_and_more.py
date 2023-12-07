# Generated by Django 4.2.2 on 2023-11-29 23:38

import django.contrib.auth.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('rmsapp', '0002_alter_tenant_options_remove_tenant_lease_end_date_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='tenant',
            name='lease_end_date',
        ),
        migrations.RemoveField(
            model_name='tenant',
            name='lease_start_date',
        ),
        migrations.AddField(
            model_name='tenant',
            name='username',
            field=models.CharField(default=True, error_messages={'unique': 'A user with that username already exists.'}, help_text='Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.', max_length=150, unique=True, validators=[django.contrib.auth.validators.UnicodeUsernameValidator()], verbose_name='username'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='tenant',
            name='password',
            field=models.CharField(max_length=128, verbose_name='password'),
        ),
    ]