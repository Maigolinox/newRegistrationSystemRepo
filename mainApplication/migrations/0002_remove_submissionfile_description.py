# Generated by Django 5.1.1 on 2025-01-14 18:41

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('mainApplication', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='submissionfile',
            name='description',
        ),
    ]
