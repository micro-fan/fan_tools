from django.urls import include, re_path
from rest_framework.routers import DefaultRouter

from .views import ArticleViewSet, ReviewViewSet


router = DefaultRouter()
router.register('article', ArticleViewSet)
router.register('review', ReviewViewSet)

urlpatterns = [
    re_path(r'^', include(router.urls)),
]
