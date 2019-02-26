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
from django.conf.urls import include
from django.contrib import admin
from django.views.generic import TemplateView
from user_app.views import ( HomeView, about_us, mining_request_form_view, 
                            get_repo_data, mined_repos, signup, activate
                             )

urlpatterns = [
    url(r'^admin/', admin.site.urls), # allow access to the admin portal
    url(r'^$', HomeView.as_view()),   # The home page 
    url(r'^about_us/$', about_us, name="about_us"),
    url(r'^accounts/', include('django.contrib.auth.urls')), # Login/Logout controls
    url(r'^signup/$', signup, name='signup'), # The signup page 
    url(r'^activate/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$',
        activate, name='activate'),
    url(r'^mining_requests_form/$', mining_request_form_view, name="mining_form"), # The mining request form 
    url(r'^repos/$', mined_repos, name="repos"), # The list of all mined repos 
    url(r'^repos/(?P<repo_owner>((\w+)[-]*))+/+(?P<repo_name>((\w+)[-]*)+\w+)/$', get_repo_data, name="visualization"), # Visualizations
]
