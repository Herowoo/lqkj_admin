"""irusheng_admin URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from django.conf.urls import url
from admin_app import views
from admin_app import Main
from admin_app import FileApi
from django.views.generic.base import TemplateView
from django.views.generic import RedirectView
from admin_cfg import settings

urlpatterns = [
    url(r'^AdminLogin/.*$', views.AdminLogin),  #微信扫码登陆
    url(r'^admin.*$', views.admin),

    url(r'^api/admin.*$', views.admin),
    url(r'^api/.*$', views.admin),
    url(r'^xyhapi/.*$', views.xyhapi),
    url(r'^favicon.ico.*$', RedirectView.as_view(url=r'static/favicon.ico')),  # 图标

    url(r'^interface.*$', Main.Enter), #新版功能
    url(r'^fileapi/upload.*$', FileApi.upload),  # 新版功能
    url(r'^fileapi/download.*$', FileApi.download),  # 新版功能

    url(r'^.*$', TemplateView.as_view(template_name="index.html")),

]
