# Generated by Django 2.2.1 on 2019-06-03 09:18

from django.conf import settings
import django.contrib.postgres.indexes
from django.db import migrations, models
import django.db.models.deletion
import fan_tools.django.contrib.postgres.fields.ltree
import fan_tools.django.contrib.postgres.indexes


class Migration(migrations.Migration):

    dependencies = [
        ('sampleapp', '0002_ltree_extension'),
    ]

    operations = [
        migrations.AlterField(
            model_name='article',
            name='author',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='articles', to='sampleapp.Author'),
        ),
        migrations.AlterField(
            model_name='review',
            name='user',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, to=settings.AUTH_USER_MODEL),
        ),
        migrations.CreateModel(
            name='LTreeModelTest',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('ltree_label', fan_tools.django.contrib.postgres.fields.ltree.LTreeLabelField()),
                ('ltree_label_path', fan_tools.django.contrib.postgres.fields.ltree.LTreeLabelPathField()),
                ('name', models.CharField(max_length=255)),
                ('parent', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='children', to='sampleapp.LTreeModelTest')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.AddIndex(
            model_name='ltreemodeltest',
            index=django.contrib.postgres.indexes.GistIndex(fields=['ltree_label_path'], name='sampleapp_l_ltree_l_5c8efd_gist'),
        ),
        migrations.AddIndex(
            model_name='ltreemodeltest',
            index=django.contrib.postgres.indexes.Index(fields=['ltree_label_path'], name='sampleapp_l_ltree_l_16ae5a'),
        ),
        migrations.AddIndex(
            model_name='ltreemodeltest',
            index=fan_tools.django.contrib.postgres.indexes.LTreeIndex(fields=['ltree_label_path'], name='sampleapp_l_ltree_l_ca7bc1_idx'),
        ),
    ]
