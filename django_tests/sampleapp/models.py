from enum import IntEnum

from django.conf import settings
from django.db import models

from fan_tools.django.contrib.postgres.models import LTreeModel


class ArticleType(IntEnum):
    article = 1
    review = 2
    ads = 3


class Author(models.Model):
    name = models.CharField(max_length=50)
    birth_date = models.DateField(blank=True, null=True)


class Article(models.Model):
    title = models.CharField(max_length=255)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    content = models.TextField()
    author = models.ForeignKey(Author, on_delete=models.PROTECT, related_name='articles')
    type = models.IntegerField(null=True, default=ArticleType.article)


class Review(models.Model):
    summary = models.CharField(max_length=255)
    content = models.TextField()
    stars = models.IntegerField()
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.DO_NOTHING, null=True, blank=True
    )
    article = models.ForeignKey(Article, on_delete=models.CASCADE, related_name='reviews')


class LTreeModelTest(LTreeModel):
    ltree_defaut_label_field = 'name'
    name = models.CharField(max_length=255)
