from datetime import date
from pprint import pprint

from django.test import TestCase
from rest_framework.test import APIClient

from tests.django_sample.sampleapp.models import Author, Article


class MainTest(TestCase):
    def setUp(self):
        self.client = APIClient()

        self.author1 = Author.objects.create(name='author 1',
                                             birth_date=date(1985, 1, 31))

        self.author2 = Author.objects.create(name='author 2',
                                             birth_date=date(1986, 2, 20))

        self.articles = []

        for i in range(5):
            for author in [self.author1, self.author2]:
                article = Article.objects.create(title='article {} by {}'.format(i, author.name),
                                                 content='article content {}'.format(i),
                                                 author=author)
                self.articles.append(article)

    def test_get_article_with_extended_fields(self):
        url = '/article/'.format(self.articles[0].id)
        query = 'type=review'

        response = self.client.get('{}?{}'.format(url, query))

        assert response.status_code == 200, response.status_code

        response_json = response.json()
        assert len(response_json) == 10, response_json
