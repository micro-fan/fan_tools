from datetime import date
from unittest import mock

import pytest
from tipsi_tools.django import call_once_on_commit

from django.db import connection, models, transaction
from django.test import TestCase
from rest_framework.test import APIClient
from sampleapp.models import Article, ArticleType, Author, Review


class MainTest(TestCase):
    def setUp(self):
        self.client = APIClient()

        self.author1 = Author.objects.create(name='author 1', birth_date=date(1985, 1, 31))

        self.author2 = Author.objects.create(name='author 2', birth_date=date(1986, 2, 20))

        self.articles = []

        for i in range(5):
            article_type = i % 3 + 1
            for author in [self.author1, self.author2]:
                article = Article.objects.create(
                    title='article {} by {}'.format(i, author.name),
                    content='article content {}'.format(i),
                    author=author,
                    type=article_type,
                )
                self.articles.append(article)
        Article.objects.create(
            title='null article', content='null content', author=author, type=None
        )

    def test_get_articles_of_review_type(self):
        url = '/article/'.format(self.articles[0].id)
        query = 'type=review'

        response = self.client.get('{}?{}'.format(url, query))

        assert response.status_code == 200, response.status_code

        response_json = response.json()
        expected = len([a for a in response_json if a['type'] == 'review'])
        assert len(response_json) == expected, response_json

    def test_get_articles_of_ads_and_review_types(self):
        url = '/article/'.format(self.articles[0].id)
        query = 'type=ads,review'

        response = self.client.get('{}?{}'.format(url, query))

        assert response.status_code == 200, response.status_code

        response_json = response.json()
        assert len(response_json) == 6, response_json

    def test_null(self):
        url = '/article/'.format(self.articles[0].id)
        query = 'type=null'
        response = self.client.get('{}?{}'.format(url, query))

        assert response.status_code == 200, response.status_code

        response_json = response.json()
        assert len(response_json) == 1, response_json


class ReviewTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.author = Author.objects.create(name='author 1', birth_date=date(1985, 1, 31))
        self.article = Article.objects.create(
            title='article by {}'.format(self.author.name),
            content='article content',
            author=self.author,
            type=ArticleType.article,
        )
        self.ads = Article.objects.create(
            title='ads by {}'.format(self.author.name),
            content='ads content',
            author=self.author,
            type=ArticleType.ads,
        )

        self.reviews = []
        for a in [self.article, self.ads]:
            for i in range(5):
                r = Review.objects.create(article=a, summary='summary', content='content', stars=5)
                self.reviews.append(r)

    def test_reviews(self):
        url = '/review/'

        response = self.client.get('{}?{}'.format(url, ''))

        assert response.status_code == 200, response.status_code

        response_json = response.json()
        assert len(response_json) == 10

    def test_reviews_article_type(self):
        response = self.client.get('/review/?article_type=ads')

        assert response.status_code == 200, response.status_code

        response_json = response.json()
        assert len(response_json) == 5, len(response_json)


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
    with mock.patch('tipsi_tools.django._get_request_unique_cache', side_effect=lambda: req_cache):
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
