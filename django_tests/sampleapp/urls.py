from django.conf.urls import url, include

from rest_framework.routers import DefaultRouter
from .views import ArticleViewSet, ReviewViewSet

router = DefaultRouter()
router.register('article', ArticleViewSet)
router.register('review', ReviewViewSet)

urlpatterns = [
    url(r'^', include(router.urls)),
]
