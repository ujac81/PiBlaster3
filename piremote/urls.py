from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^browse/', views.browse, name='browse'),
    url(r'^ajax/browse/$', views.browse_ajax, name='browse_ajax'),
    url(r'^ajax/status/$', views.status_ajax, name='status_ajax'),
]

