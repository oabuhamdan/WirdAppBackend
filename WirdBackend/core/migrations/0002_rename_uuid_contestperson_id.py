# Generated by Django 4.2 on 2024-01-15 20:53

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='contestperson',
            old_name='uuid',
            new_name='id',
        ),
    ]
