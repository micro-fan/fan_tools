import re
from datetime import date
from unittest import mock

import pytest
from django.db import connection, models, transaction
from rest_framework import status
from rest_framework.reverse import reverse

from fan_tools.django import call_once_on_commit
from fan_tools.django.models import UploadNameGenerator
from pytest_tipsi_django.client_fixtures import UserWrapper

from sampleapp.models import Article, ArticleType, Author, Review


@pytest.fixture
def client(request, module_transaction):
    with module_transaction(request.fixturename):
        return UserWrapper(None)


@pytest.fixture
def author1(request, module_transaction):
    with module_transaction(request.fixturename):
        yield Author.objects.create(name='author 1', birth_date=date(1985, 1, 31))


@pytest.fixture
def author2(request, module_transaction):
    with module_transaction(request.fixturename):
        yield Author.objects.create(name='author 2', birth_date=date(1986, 2, 20))


@pytest.fixture
def articles(request, module_transaction, author1, author2):
    with module_transaction(request.fixturename):
        articles = []
        for i in range(5):
            article_type = i % 3 + 1
            for author in [author1, author2]:
                article = Article.objects.create(
                    title='article {} by {}'.format(i, author.name),
                    content='article content {}'.format(i),
                    author=author,
                    type=article_type,
                )
                articles.append(article)
        Article.objects.create(
            title='null article', content='null content', author=author, type=None
        )
        yield articles


@pytest.fixture
def article_ads(request, module_transaction, author1):
    with module_transaction(request.fixturename):
        yield Article.objects.create(
            title='ads by {}'.format(author1.name),
            content='ads content',
            author=author1,
            type=ArticleType.ads,
        )

@pytest.fixture
def reviews(request, module_transaction, articles, article_ads, author1, author2):
    with module_transaction(request.fixturename):
        reviews = []
        for article in [articles[0], article_ads]:
            for i in range(5):
                review = Review.objects.create(
                    article=article,
                    summary='summary',
                    content='content',
                    stars=5,
                )
                reviews.append(review)
        yield reviews


def test_get_articles_of_review_type(client, articles):
    response = client.get_json(
        reverse('article-list'),
        {'type': 'review'},
        expected=status.HTTP_200_OK,
    )
    data = response['data']
    expected = len([a for a in data if a['type'] == 'review'])
    assert len(data) == expected, data


def test_get_articles_of_ads_and_review_types(client, articles):
    response = client.get_json(
        reverse('article-list'),
        {'type': 'ads,review'},
        expected=status.HTTP_200_OK,
    )
    assert len(response['data']) == 6


def test_null(client, articles):
    response = client.get_json(
        reverse('article-list'),
        {'type': 'null'},
        expected=status.HTTP_200_OK,
        )
    assert len(response['data']) == 1


def test_reviews(client, reviews):
    response = client.get_json(
        reverse('review-list'),
        expected=status.HTTP_200_OK,
    )
    assert len(response['data']) == 10


def test_reviews_empty_filter(client, reviews):
    response = client.get_json(
        reverse('review-list'),
        {'article_type': ''},
        expected=status.HTTP_200_OK,
    )
    assert len(response['data']) == 10


def test_reviews_article_type(client, reviews):
    response = client.get_json(
        reverse('review-list'),
        {'article_type': 'ads'},
        expected=status.HTTP_200_OK,
    )
    assert len(response['data']) == 5


def test_reviews_article_type_err(client, reviews):
    client.get_json(
        reverse('review-list'),
        {'article_type': 'ERROR'},
        expected=400,
    )


def test_reviews_article_type_int(client, articles):
    pk = articles[0].id
    url = reverse('article-detail', [pk])
    assert articles[0].type == ArticleType.article
    data = client.patch_json(
        url,
        {'type': str(ArticleType.ads.value), 'title': 'some title'}
    )['data']
    print(data)
    assert data['type'] == ArticleType.ads.name



@pytest.fixture
def author(db):
    return Author.objects.create(name='author 1', birth_date=date(1985, 1, 31))


@pytest.fixture
def req_cache():
    return {}


@call_once_on_commit
def _test_hook():
    pass


def author_hook(sender, instance, **kwargs):
    _test_hook()


@pytest.fixture
def author_signal(author):
    models.signals.post_save.connect(author_hook, sender=Author)
    yield
    models.signals.post_save.disconnect(author_hook, sender=Author)


def test_once_on_commit(author, req_cache, author_signal):
    with mock.patch(
        'fan_tools.django._get_request_unique_cache',
        side_effect=lambda: req_cache,
    ):
        with transaction.atomic():
            author.birth_date = date(1986, 1, 31)
            author.save()
            author.birth_date = date(1986, 1, 31)
            author.save()

            fn_name = _test_hook.__name__
            call_times = sum(fn_name in str(i[1]) for i in connection.run_on_commit)
            expected_call_times = 1
            assert call_times == expected_call_times

        assert author.birth_date == date(1986, 1, 31)


def test_uploadnamegenerator():
    assert re.match(
        r'static/imageupload/imageupload-image-.*.jpg',
        UploadNameGenerator('imageupload', 'image')(None, 'file.jpg'),
    )
