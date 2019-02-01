import json
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseNotFound
from django.db import IntegrityError
from django.shortcuts import render
from pymongo import MongoClient
import plotly
import plotly.offline as opy
import plotly.graph_objs as go
from django.views import View 
from django.views.generic import TemplateView, ListView
import mining_scripts.send_email
from mining_scripts.mining import *
from .models import *
from .forms import MiningRequestForm
from django.contrib import messages

# MongoDB information 
client = MongoClient('localhost', 27017)
db = client.test_database
pull_requests = db.pullRequests


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
        
        return render(request, template, {'form': form})

    else:
        form = MiningRequestForm()
        return render(request, template, {'form': form})  
    
   

# function based view. This is the BETTER way of returning an html page
def chart(request):
    # The third parameter specifies something that we want to pass 
    # to the html page page (base.html) 
    bool_item = False # turn to false to not print a rand number 

    pulls = pull_requests.find()
    additions = []
    pull_nums = []
    for pull in pulls:
        additions.append(pull['additions'])
        pull_nums.append(pull['number'])

    if len(pull_nums) != 0:
        trace1 = go.Pie(labels=pull_nums, values=additions, name='Additions Pie Chart')
        data=go.Data([trace1])
        layout=go.Layout(title="Additions Pie Chart")
        figure=go.Figure(data=data,layout=layout)
        div = opy.plot(figure, auto_open=False, output_type='div')
        context = {"graph":div}
    else:
        context = {"noGraph":True}

    # response
    return render(request, "chart.html", context) 


# ANOTHER way of rendering A Page using template views 
class HomeView(TemplateView):
    template_name = 'home.html'

class ChartView(TemplateView):
    template_name = 'chart.html'
    def get_context_data(self, *args, **kwargs):
        context = super(ChartView, self).get_context_data(*args, **kwargs)
        pulls = pull_requests.find()
        additions = []
        pull_nums = []
        for pull in pulls:
            additions.append(pull['additions'])
            pull_nums.append(pull['number'])

        if len(pull_nums) != 0:
            trace1 = go.Pie(labels=pull_nums, values=additions, name='Additions Pie Chart')
            data=go.Data([trace1])
            layout=go.Layout(title="Additions Pie Chart")
            figure=go.Figure(data=data,layout=layout)
            div = opy.plot(figure, auto_open=False, output_type='div')
            context = {"graph":div}
        else:
            context = {"noGraph":True}
        return context


class MinedRepos(TemplateView):
    template_name = 'repos.html'
    def get_context_data(self, *args, **kwargs):
        context = super(MinedRepos, self).get_context_data(*args, **kwargs)
        mined_repos = list(MinedRepo.objects.values_list('repo_name', flat=True)) # Obtain all the mining requests
        context = {"repos":mined_repos}
        return context

def get_repo_data(request, repo_owner, repo_name):
    template_name = 'mined_repo_display.html'
    context = {"repo_owner":repo_owner.lower(), "repo_name":repo_name.lower()}
    original_repo = repo_owner.lower() + "/" + repo_name.lower()
    mined_repos = list(MinedRepo.objects.values_list('repo_name', flat=True)) # Obtain all the mining requests
    
    if original_repo in mined_repos:
        return render(request, template_name, context) 

    else:
        return HttpResponseNotFound('<h1>404 Repo Not Found</h1>')
