from django.conf.urls import url
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    url(r'^$', views.model_form_upload, name='model_form_upload'),
    url(r'^signup/$', views.signup, name='signup'),
    url(r'trans/(?P<pk>\d+)/$', views.translation, name='trans'),
    url(r'file/(?P<pk>\d+)/$', views.file_remove, name='file_remove')
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
