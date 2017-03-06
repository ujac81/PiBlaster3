from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^browse/', views.browse, name='browse'),
    url(r'^playlist/', views.playlist, name='playlist'),
    url(r'^ajax/browse/$', views.browse_ajax, name='browse_ajax'),
    url(r'^ajax/status/$', views.status_ajax, name='status_ajax'),
    url(r'^ajax/cmd/$', views.cmd_ajax, name='cmd_ajax'),
    url(r'^ajax/plinfo/$', views.plinfo_ajax, name='plinfo_ajax'),
]

