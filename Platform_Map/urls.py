# -*- coding: utf-8 -*-
"""Platform_Map URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.11/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url, include
from django.contrib import admin
from django.conf import settings
from Display_Platform_Info import views

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^platform/$', views.platform),
    #url(r'^generate/$', views.generate),
    url(r'^physical/$', views.physical),
    url(r'^display/$', views.display),
    url(r'^submit_platform/$', views.submit_platform),
    url(r'^submit_display/$', views.submit_display),
    url(r'^submit_restart_mmi/$', views.submit_restart_mmi),
    url(r'^submit_tty/$', views.submit_tty),
    url(r'^$', views.log_in),
    #url(r'^$', views.platform),
    url(r'^backend/$', views.backend2),
    url(r'^reg/$', views.reg),
    url(r'^login/$', views.log_in),
    url(r'^logout/$', views.log_out),
    url(r'^backend_push/$', views.backend_push),
    url(r'client_connect/$', views.client_connect),
    url(r'passwd/$', views.passwd),
]

if not settings.DEBUG:
    from django.views import static
    urlpatterns.append(url(r'^static/(?P<path>.*)$', static.serve,
        {'document_root': settings.STATIC_ROOT}, name='static'))
