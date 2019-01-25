"""web_app URL Configuration

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
from django.conf.urls import url
from django.contrib import admin
from django.views.generic import TemplateView
from user_app.views import ( HomeView, ChartView, DatabaseView, CleanDatabaseView,
                               MineView, mining_request_listview, MiningRequestListView,
                               mining_request_create_view, clean_mining_requests, 
                               admin_approve_mining_requests
                             )

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^$', HomeView.as_view()),
    url(r'^chart/$', ChartView.as_view()),
    url(r'^database/$', DatabaseView.as_view()),
    url(r'^mining_requests_form/$', mining_request_create_view),
    url(r'^mining_requests/$', MiningRequestListView.as_view()),
    url(r'^clean_mining_requests/$', clean_mining_requests),
    url(r'^admin_approve_mining_requests/$', admin_approve_mining_requests),
    url(r'^clean_database/$', CleanDatabaseView.as_view()),
    url(r'^mine/$', MineView.as_view()),
]
