import json
from django.http import HttpResponse, HttpResponseRedirect
from django.db import IntegrityError
from django.shortcuts import render
from user_app.mine import make_request
from pymongo import MongoClient
import plotly
import plotly.offline as opy
import plotly.graph_objs as go
from django.views import View 
from django.views.generic import TemplateView, ListView
import re
import mining_scripts.send_email
from mining_scripts.mining import *
from .models import *
from .forms import MiningRequestForm, AdminApprovalForm
from django.contrib import messages

# MongoDB information 
client = MongoClient('localhost', 27017)
db = client.test_database
pull_requests = db.pullRequests


def mining_request_create_view(request):
    context = {}
    requests = MiningRequest.objects.all()
    
    if request.method == 'POST':
        form = MiningRequestForm(request.POST)
        if form.is_valid():
            messages.success(request, 'Your request has been submitted!') 

                # Only create a database object if what is being passed matches our DB form
            obj = MiningRequest.objects.create(
                repo_name=form.cleaned_data.get('repo_name'),
                email=form.cleaned_data.get("email")
            )

        else:
            messages.error(request, 'The form is invalid.')

        
        return render(request, 'mining_requests/form.html', {'form': form})

    else:
        form = MiningRequestForm()
        return render(request, 'mining_requests/form.html', {'form': form})  
    
   

def admin_approve_mining_requests(request):

    if request.method == 'POST':
        if 'approve' in request.POST:
            try:
                form = AdminApprovalForm(request.POST)

                # Only create a database object if what is being passed matches our DB form
                if form.is_valid():
                    print(request.POST)
                    repo_info = [info for info in request.POST][1:-1]
                    print(repo_info)
                    repo_names = [info.split(':')[0] for info in repo_info]
                    repo_nums = [info.split(':')[1] for info in repo_info]
                    print("REPOS:", repo_names)
                    print("PR NUMS:", repo_nums)
                    

                    for item in range(0, len(repo_names)):
                        # Place the item in the database
                        repo_name = repo_names[item]
                        pull_request_number = repo_nums[item]
                        json_file = make_request(repo_name, pull_request_number)

                        pull_requests.insert_one(json_file)

                        # Delete the request, since it has been mined
                        MiningRequest.objects.filter(repo_name=repo_names[item], pull_request_number=repo_nums[item]).delete()
                    
                    
                    
                    # what was passed in was valid, so redirect to the mining requests page 
                    return HttpResponseRedirect("/database")

            
                # if what is passed in is incorrect, log it
                if form.errors:
                    print(form.errors)
            except IntegrityError as e:
                return render(request, "mining_requests/admin_approval.html", {"error": True})
        elif 'disapprove' in request.POST:
            print(request.POST)
            repo_info = [info for info in request.POST][1:-1]
            repo_names = [info.split(':')[0] for info in repo_info]
            repo_nums = [info.split(':')[1] for info in repo_info]
            print("REPOS:", repo_names)
            print("PR NUMS:", repo_nums)
            

            for item in range(0, len(repo_names)):
                # Place the item in the database
                repo_name = repo_names[item]
                pull_request_number = repo_nums[item]

                # Delete the request, since it has been mined
                MiningRequest.objects.filter(repo_name=repo_names[item], pull_request_number=repo_nums[item]).delete()
            
            
            
            # what was passed in was valid, so redirect to the mining requests page 
            return HttpResponseRedirect("/mining_requests")

    
    template_name = 'mining_requests/admin_approval.html'
    objects = MiningRequest.objects.all()
    context = {"objects": objects}
    return render(request, template_name, context  )


# Create your views here.

# function based view. THIS IS THE ORIGINAL (BAD WAY) OF RETURNING HTML
def home_old(request):
    html_var = 'f strings'
    html_ = f"""<!DOCTYPE html>
    <html lang=en>
    <head>
    </head>
    <body>
    <h1>Hello World!</h1>
    <p>This is {html_var} coming through</p>
    </body>
    </html>
    """
    #return HttpResponse("hello") # Another way to return the same thing 
    return HttpResponse(html_)
    #return render(request, "home.html", {})# response

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


# Class-based view. Allows for some extra functionality!
class HomeViewOld(View):
    def get(self, request, *args, **kwargs):
        context = {}
        return render(request, "home.html", context) 

    # def post(self, request, *args, **kwargs):
    #     context = {}
    #     return render(request, "home.html", context) 

    # def put(self, request, *args, **kwargs):
    #     context = {}
    #     return render(request, "home.html", context) 

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

class DatabaseView(TemplateView):
    template_name = 'database.html'
    def get_context_data(self, *args, **kwargs):
        context = super(DatabaseView, self).get_context_data(*args, **kwargs)
        pulls = pull_requests.find()
        if not pulls is None:
            context = {"bool_item":True, "pulls":pulls}
        else: 
            context = {}

        return context 

class CleanDatabaseView(TemplateView):
    template_name = 'clean_database.html'

    def get_context_data(self, *args, **kwargs):
        context = super(CleanDatabaseView, self).get_context_data(*args, **kwargs)
        pulls = pull_requests.find()
        if not pulls is None:
            pull_requests.remove( { } )
            context = {"bool_item":True}
        else:
            context = {}
        return context 


class MineView(TemplateView):
    template_name = 'mine.html'

    def get_context_data(self, *args, **kwargs):
        context = super(MineView, self).get_context_data(*args, **kwargs)
        mined_jsons = [
        download_api_page_json(15).json(),
        download_api_page_json(17).json(),
        download_api_page_json(20).json(),
        download_api_page_json(21).json(),
        download_api_page_json(22).json()
        ]
    
        addition_list = [
            mined_jsons[0]["additions"],
            mined_jsons[1]["additions"],
            mined_jsons[2]["additions"],
            mined_jsons[3]["additions"],
            mined_jsons[4]["additions"]
        ]

        pull_requests.insert_many(mined_jsons)
        context = {"mined_jsons":mined_jsons, "addition_list":addition_list}

        return context 

# Function-based view to see all of the mining requests 
def mining_request_listview(request):
    template_name = 'mining_requests/mining_requests_list.html'
    queryset = MiningRequest.objects.all()
    context = {
        "object_list": queryset
    }
    return render(request, template_name, context)

# Will display the contents of the mining requests database!
class MiningRequestListView(ListView):
    template_name = 'mining_requests/mining_requests_list.html' 
    queryset = MiningRequest.objects.all()


# Will delete the contents of the mining requests database!
def clean_mining_requests(request):
    template_name = 'mining_requests/clean_mining_requests.html'
    context = {} 
    MiningRequest.objects.all().delete()
    return render(request, template_name, context)

