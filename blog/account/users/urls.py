from django.conf.urls import url

from blog.account.users.views import user_operate, user_self


urlpatterns = [
    url(r'^$', user_operate),
    url(r'^self/$', user_self),
    url(r'^(?P<uuid>[a-f0-9]{8}-([a-f0-9]{4}-){3}[a-f0-9]{12})/$', user_operate),
]
