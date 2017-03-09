import django_filters
from rest_framework import serializers, viewsets
from rest_framework.filters import DjangoFilterBackend

from tipsi_tools.drf.filters import EnumFilter
from tipsi_tools.drf.serializers import EnumSerializer

from sampleapp.models import Article, ArticleType, Review


class ArticleSerializer(serializers.ModelSerializer):
    type = EnumSerializer(ArticleType)

    class Meta:
        model = Article
        fields = ['id', 'title', 'type']


class ArticleFilter(django_filters.FilterSet):
    type = EnumFilter(ArticleType)

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
    article_type = EnumFilter(ArticleType, name='article__type')

    class Meta:
        model = Review
        fields = ['article_type']


class ReviewViewSet(viewsets.ModelViewSet):
    queryset = Review.objects.all()
    serializer_class = ReviewSerializer
    filter_backends = [DjangoFilterBackend]
    filter_class = ReviewFilter
