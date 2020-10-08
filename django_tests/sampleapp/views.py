from fan_tools.drf.filters import EnumFilter
from fan_tools.drf.serializers import EnumSerializer

import django_filters
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import serializers, viewsets
from sampleapp.models import Article, ArticleType, Review


class ArticleSerializer(serializers.ModelSerializer):
    type = EnumSerializer(ArticleType)

    class Meta:
        model = Article
        fields = ['id', 'title', 'type']


class ArticleFilter(django_filters.FilterSet):
    type = EnumFilter(ArticleType, raise_on_error=True)

    class Meta:
        model = Article
        fields = ['type']


class ArticleViewSet(viewsets.ModelViewSet):
    queryset = Article.objects.all()
    serializer_class = ArticleSerializer
    filter_backends = [DjangoFilterBackend]
    filter_class = ArticleFilter


class ReviewSerializer(serializers.ModelSerializer):
    article = ArticleSerializer()

    class Meta:
        model = Review
        fields = ['id', 'summary', 'content', 'article']


class ReviewFilter(django_filters.FilterSet):
    article_type = EnumFilter(ArticleType, field_name='article__type', raise_on_error=True)

    class Meta:
        model = Review
        fields = ['article_type']


class ReviewViewSet(viewsets.ModelViewSet):
    queryset = Review.objects.all()
    serializer_class = ReviewSerializer
    filter_backends = [DjangoFilterBackend]
    filter_class = ReviewFilter
