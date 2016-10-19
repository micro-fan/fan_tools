from datetime import date
from pprint import pprint

from django.test import TestCase
from rest_framework.test import APIClient

from sampleapp.models import Author, Article


class MainTest(TestCase):
    def setUp(self):
        self.client = APIClient()

        self.author1 = Author.objects.create(name='author 1',
                                             birth_date=date(1985, 1, 31))

        self.author2 = Author.objects.create(name='author 2',
                                             birth_date=date(1986, 2, 20))

        self.articles = []

        for i in range(5):
            article_type = i % 3 + 1
            for author in [self.author1, self.author2]:
                article = Article.objects.create(title='article {} by {}'.format(i, author.name),
                                                 content='article content {}'.format(i),
                                                 author=author,
                                                 type=article_type)
                self.articles.append(article)

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

