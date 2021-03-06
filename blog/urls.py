from django.conf.urls import include, url

from blog.content.photos.views import photo_show


urlpatterns = [
    url(r'^media/', photo_show),
    url(r'^view/', include('blog.render.urls')),
    url(r'^blog/v1/account/', include('blog.account.urls')),
    url(r'^blog/v1/content/albums/', include('blog.content.albums.urls')),
    url(r'^blog/v1/content/articles/', include('blog.content.articles.urls')),
    url(r'^blog/v1/content/comments/', include('blog.content.comments.urls')),
    url(r'^blog/v1/content/photos/', include('blog.content.photos.urls')),
    url(r'^blog/v1/content/sections/', include('blog.content.sections.urls')),
    url(r'^blog/v1/content/marks/', include('blog.content.marks.urls')),
    url(r'^blog/v1/wechat/', include('blog.wechat.urls'))
]
