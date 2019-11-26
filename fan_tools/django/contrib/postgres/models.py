from django.db import models
from django.utils.text import slugify
from django.contrib.postgres.indexes import GistIndex, Index

from .fields import LTreeLabelField, LTreeLabelPathField
from .indexes import LTreeIndex


class LTreeModel(models.Model):

    ltree_defaut_label_field = 'name'

    ltree_label = LTreeLabelField()
    ltree_label_path = LTreeLabelPathField()

    parent = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        related_name='children',
        on_delete=models.CASCADE,
    )

    class Meta:
        abstract = True

        indexes = [
            Index(fields=['ltree_label_path']),
            GistIndex(fields=['ltree_label_path']),
            LTreeIndex(fields=['ltree_label_path']),
        ]

    @property
    def depth(self):
        return len(
            self.ltree_label_path.split('.'),
        )

    def save(self, *args, **kwargs):
        if not self.ltree_label:
            self.ltree_label = slugify(
                getattr(
                    self,
                    self.ltree_defaut_label_field
                ),
            ).replace('-', '_')
        super().save(*args, **kwargs)
