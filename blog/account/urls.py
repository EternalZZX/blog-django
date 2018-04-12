from django.conf.urls import include, url

from blog.account import views


urlpatterns = [
    url(r'^sign_in/$', views.sign_in),
    url(r'^sign_in_guest/$', views.sign_in_guest),
    url(r'^sign_up/$', views.sign_up),
    url(r'^users/', include('blog.account.users.urls')),
    url(r'^roles/', include('blog.account.roles.urls')),
]
