from django.conf.urls import url, include
from django.contrib import admin
from django.contrib.auth import views
from subtitle_translate_project import settings

urlpatterns = [
    url('admin/', admin.site.urls),
    url(r'login', views.login, name='login'),
    url(r'^accounts/logout/$', views.logout, name='logout', kwargs={'next_page': '/'}),
    url(r'', include('subtitle_app.urls')),
]