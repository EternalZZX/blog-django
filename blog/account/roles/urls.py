from django.conf.urls import url

from blog.account.roles.views import role_operate


urlpatterns = [
    url(r'^$', role_operate),
    url(r'^(?P<role_id>(\d+))/$', role_operate),
]
