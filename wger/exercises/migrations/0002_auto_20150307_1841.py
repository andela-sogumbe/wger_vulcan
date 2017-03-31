# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import uuid

from django.db import models, migrations


def generate_uuids(apps, schema_editor):
    """
    Generate new UUIDs for each exercise
    :param apps:
    :param schema_editor:
    :return:
    """
    excercise = apps.get_model("exercises", "Exercise")
    for exercise in excercise.objects.all():
        exercise.uuid = uuid.uuid4()
        exercise.save()


class Migration(migrations.Migration):
    dependencies = [
        ('exercises', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='exercise',
            name='uuid',
            field=models.CharField(editable=False, max_length=36,
                                   verbose_name='UUID', default=uuid.uuid4),
            preserve_default=True,
        ),
        migrations.RunPython(generate_uuids),
    ]
