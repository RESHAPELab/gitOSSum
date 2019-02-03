# Import necessary django libraries
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseNotFound
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import IntegrityError
from django.shortcuts import render
from django.views.generic import TemplateView


# Import all handwritten libraries
from permissions.permissions import login_forbidden
import mining_scripts.send_email
from mining_scripts.mining import *
from .models import *
from .forms import MiningRequestForm, SignUpForm, LoginForm


# Import external libraries
from nvd3 import multiBarHorizontalChart
import random 
import json



# Begin views

class HomeView(TemplateView):
    template_name = 'home.html'


# Only allow people that are not signed in to access the signup page
@login_forbidden
def signup(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            raw_password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=raw_password)
            login(request, user)
            obj = OAuthToken.objects.create(
                oauth_token=form.cleaned_data.get('github_oauth'),
                owner=username
            )
            return HttpResponseRedirect('/')
    else:
        form = SignUpForm()
    return render(request, 'signup.html', {'form': form})



# Only allow people that are logged in to access the mining request form 
@login_required
def mining_request_form_view(request):
    context = {}
    requests = MiningRequest.objects.all()
    template = "form.html"
    
    if request.method == 'POST':
        form = MiningRequestForm(request.POST)
        if form.is_valid():
            messages.success(request, 'Your request has been submitted!') 

                # Only create a database object if what is being passed matches our DB form
            obj = MiningRequest.objects.create(
                repo_name=form.cleaned_data.get('repo_name'),
                email=form.cleaned_data.get("email")
            )

            return HttpResponseRedirect("")
        
        return render(request, template, {'form': form})

    else:
        form = MiningRequestForm()
        return render(request, template, {'form': form})  



# A page accessible by anyone to see all mined repos (with hyperlinks)
class MinedRepos(TemplateView):
    template_name = 'repos.html'
    def get_context_data(self, *args, **kwargs):
        context = super(MinedRepos, self).get_context_data(*args, **kwargs)
        mined_repos = list(MinedRepo.objects.values_list('repo_name', flat=True)) # Obtain all the mining requests
        context = {"repos":mined_repos}
        return context



# A function that will be used to generate interactive visualizations of 
# mined JSON data for any repo.
def get_repo_data(request, repo_owner, repo_name):
    template_name = 'mined_repo_display.html'
    original_repo = repo_owner.lower() + "/" + repo_name.lower()
    mined_repos = list(MinedRepo.objects.values_list('repo_name', flat=True)) # Obtain all the mining requests
    
    if original_repo in mined_repos:

        type = "multiBarHorizontalChart"
        chart = multiBarHorizontalChart(name=type, height=350)
        chart.set_containerheader("\n\n<h2>" + type + "</h2>\n\n")
        nb_element = 10
        xdata = list(range(nb_element))
        ydata = [random.randint(-10, 10) for i in range(nb_element)]
        ydata2 = [x * 2 for x in ydata]
        extra_serie = {"tooltip": {"y_start": "", "y_end": " Calls"}}
        chart.add_serie(name="Count", y=ydata, x=xdata, extra=extra_serie)
        extra_serie = {"tooltip": {"y_start": "", "y_end": " Min"}}
        chart.add_serie(name="Duration", y=ydata2, x=xdata, extra=extra_serie)
        chart.buildhtml()
        chart = chart.htmlcontent
        context = {"repo_owner":repo_owner.lower(), "repo_name":repo_name.lower(), "chart":chart}
        return render(request, template_name, context) 

    else:
        return HttpResponseNotFound('<h1>404 Repo Not Found</h1>')
