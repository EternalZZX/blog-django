from django.conf.urls import url

from blog.wechat.views import handle


urlpatterns = [
    url(r'^$', handle)
]
