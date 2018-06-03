from django.conf.urls import url

from blog.render import views


urlpatterns = [
    url(r'^albums/(?P<uuid>[a-f0-9]{8}-([a-f0-9]{4}-){3}[a-f0-9]{12})/$', views.album_show)
]
