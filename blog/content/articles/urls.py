from django.conf.urls import url

from blog.content.articles.views import article_operate


urlpatterns = [
    url(r'^$', article_operate),
    url(r'^(?P<article_uuid>[a-f0-9]{8}-([a-f0-9]{4}-){3}[a-f0-9]{12})/$', article_operate),
]
