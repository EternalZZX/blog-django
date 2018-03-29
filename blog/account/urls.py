from django.conf.urls import include, url

from blog.account.views import auth


urlpatterns = [
    url(r'^auth/$', auth),
    url(r'^users/', include('blog.account.users.urls')),
    url(r'^roles/', include('blog.account.roles.urls')),
]
