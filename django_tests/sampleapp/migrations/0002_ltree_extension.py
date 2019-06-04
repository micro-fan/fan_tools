from django.db import migrations
from tipsi_tools.django.contrib.postgres.operations import LTreeExtension


class Migration(migrations.Migration):

    dependencies = [
        ('sampleapp', '0001_initial'),
    ]

    operations = [
        LTreeExtension(),
    ]
