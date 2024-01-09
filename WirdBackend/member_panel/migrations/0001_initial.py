# Generated by Django 4.2 on 2024-01-01 15:28

import datetime
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        ('admin_panel', '0002_initial'),
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='PointRecord',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('record_date', models.DateField(default=datetime.date.today)),
                ('units_scored', models.PositiveIntegerField(default=0, help_text='point record help text')),
                ('point_total', models.PositiveIntegerField(default=0)),
                ('contest_criterion', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='admin_panel.contestcriterion')),
                ('person', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='contest_person_points', to='core.contestperson')),
                ('polymorphic_ctype', models.ForeignKey(editable=False, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='polymorphic_%(app_label)s.%(class)s_set+', to='contenttypes.contenttype')),
            ],
            options={
                'ordering': ('-record_date',),
            },
        ),
        migrations.CreateModel(
            name='UserInputPointRecord',
            fields=[
                ('pointrecord_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='member_panel.pointrecord')),
                ('user_input', models.TextField(blank=True, default='', max_length=1024)),
                ('reviewed_by_admin', models.BooleanField(default=False)),
            ],
            options={
                'abstract': False,
                'base_manager_name': 'objects',
            },
            bases=('member_panel.pointrecord',),
        ),
    ]
