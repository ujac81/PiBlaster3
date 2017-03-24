from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^wifi$', views.wifi, name='wifi'),
    url(r'^delete$', views.delete, name='delete'),
    url(r'^deleteup$', views.deleteup, name='deleteup'),
]
