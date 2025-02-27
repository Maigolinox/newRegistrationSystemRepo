# Generated by Django 5.1.1 on 2025-01-24 22:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mainApplication', '0020_systemsettings_availabilitydatescientificcomitteediplomas_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='News',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField()),
                ('title', models.CharField(max_length=255)),
                ('type', models.CharField(choices=[('info', 'Info'), ('success', 'Success'), ('danger', 'Danger')], default='info', max_length=50)),
                ('enlace_url', models.URLField(blank=True, null=True)),
            ],
        ),
    ]
