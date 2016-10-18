from datetime import date
from pprint import pprint

from django.test import TestCase
from rest_framework.test import APIClient


class MainTest(TestCase):
    def test_list_articles(self):
        url = '/article/{}/'.format(self.articles[0].id)
        query = 'article_fields=id,author&author_fields=id,name,birth_date'

        response = self.client.get('{}?{}'.format(url, query))

        assert response.status_code == 200, response.status_code

        response_json = response.json()
        assert 'author' in response_json, response_json

        author = response_json['author']
        assert author == {'id': self.author1.id,
                          'name': 'author 1',
                          'birth_date': '1985-01-31'}, author
