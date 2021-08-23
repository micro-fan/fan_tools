from django.conf.urls import re_path, include

from rest_framework.routers import DefaultRouter
from .views import ArticleViewSet, ReviewViewSet

router = DefaultRouter()
router.register('article', ArticleViewSet)
router.register('review', ReviewViewSet)

urlpatterns = [
    re_path(r'^', include(router.urls)),
]
