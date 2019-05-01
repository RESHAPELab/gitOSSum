# Import necessary django libraries
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseNotFound
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import EmailMessage
from django.db import IntegrityError
from django.views.generic import TemplateView
from django.shortcuts import render
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes, force_text
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.forms import ValidationError


# Import all handwritten libraries
from permissions.permissions import login_forbidden
from .forms import MiningRequestForm, LoginForm, FeedbackForm, Filter, SignupForm
from mining_scripts.mining import *
from .models import *
from .tokens import account_activation_token
from .visualizations import *
from .filters import *


# Import external libraries
from nvd3 import multiBarHorizontalChart
import random 
import json
from io import BytesIO
from PIL import Image



# Begin views

class HomeView(TemplateView):
    template_name = 'home.html'

def about_us(request):
    template_name = 'about_us.html'
    return render(request, template_name, {})

@login_forbidden
def signup(request):
    if request.method == 'POST':
        form = SignupForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False
            user.save()
            current_site = get_current_site(request)
            mail_subject = 'Activate your Git-OSS-um account.'
            message = render_to_string('registration/acc_active_email.html', {
                'user': user,
                'domain': current_site.domain,
                'uid':urlsafe_base64_encode(force_bytes(user.pk)),
                'token':account_activation_token.make_token(user),
            })
            to_email = form.cleaned_data.get('email')
            email = EmailMessage(
                        mail_subject, message, to=[to_email]
            )
            email.send()
            return HttpResponse('Please  confirm your email address to complete the registration')
    else:
        form = SignupForm()
    return render(request, 'signup.html', {'form': form})


# Utility function taken from https://medium.com/@frfahim/django-registration-with-confirmation-email-bb5da011e4ef
# That will allow a user to activate their account 
def activate(request, uidb64, token):
    try:
        uid = force_text(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except(TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None
    if user is not None and account_activation_token.check_token(user, token):
        user.is_active = True
        user.save()
        # login(request, user)
        return HttpResponse('Thank  you for your email confirmation. Now you can <a href="http://gitossum.com/accounts/login/">login</a> your account.')
    else:
        return HttpResponse('Activation  link is invalid!')


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
                email=request.user.email,
                send_email=form.cleaned_data.get("email"),
                requested_by=request.user.username
            )

            form = MiningRequestForm()
            return render(request, template, {'form': form})
        
        return render(request, template, {'form': form})

    else:
        form = MiningRequestForm()
        return render(request, template, {'form': form}) 

# A page accessible by anyone to see all mined repos (with hyperlinks)
def mined_repos(request):

    template_name = 'repos.html'

    # Obtain all the mining requests 
    mined_repos = sorted(list(MinedRepo.objects.values_list('repo_name', flat=True)))          
    num_repos = len(mined_repos)
    context = dict()
    message = ''
    filter_form = Filter(get_language_list_from_mongo())

    if request.method == 'POST':

        if request.POST.get('compare'):
            if "repo_checkbox" in request.POST:
                checked_repos = request.POST.getlist("repo_checkbox")
                
                if len(checked_repos) < 2 or len(checked_repos) > 3:
                    message = "You can only compare 2-3 repos"

                elif len(checked_repos) == 2:
                    repo_owner1 = checked_repos[0].split('/')[0]
                    repo_owner2 = checked_repos[1].split('/')[0]

                    repo_name1 = checked_repos[0].split('/')[1]
                    repo_name2 = checked_repos[1].split('/')[1]

                    url = f"/repos/compare/{repo_owner1}&{repo_name1}&{repo_owner2}&{repo_name2}/"

                    return HttpResponseRedirect(url)


                else:
                    repo_owner1 = checked_repos[0].split('/')[0]
                    repo_owner2 = checked_repos[1].split('/')[0]
                    repo_owner3 = checked_repos[2].split('/')[0]

                    repo_name1 = checked_repos[0].split('/')[1]
                    repo_name2 = checked_repos[1].split('/')[1]
                    repo_name3 = checked_repos[2].split('/')[1]
                    

                    url = f"/repos/compare/{repo_owner1}&{repo_name1}&{repo_owner2}&{repo_name2}&{repo_owner3}&{repo_name3}/"

                    return HttpResponseRedirect(url)

            else:
                message = "You must choose at least two pages to compare!"

        else:
            filters = list()
            filter_form = Filter(get_language_list_from_mongo(), request.POST)
            
            if filter_form.is_valid():
                if 'search' in request.POST:
                    search_query = filter_form.cleaned_data.get('search')
                    if search_query.strip() != '':
                        repos_filtered_by_search = get_repos_search_query_filter(search_query)
                        filters.append(repos_filtered_by_search)

                if 'languages' in request.POST:
                    languages = filter_form.cleaned_data.get('languages')
                    repos_filtered_by_language = get_repos_list_by_language_filter(languages)
                    filters.append(repos_filtered_by_language)

                lower_bound = filter_form.cleaned_data.get('min_pull_requests')
                upper_bound = filter_form.cleaned_data.get('max_pull_requests')

                if lower_bound != None and upper_bound == None:
                    repos_filtered_by_pulls = get_repos_list_by_pulls_greater_than_filter(lower_bound)
                    filters.append(repos_filtered_by_pulls)

                elif upper_bound != None and lower_bound == None:
                    repos_filtered_by_pulls = get_repos_list_by_pulls_less_than_filter(upper_bound)
                    filters.append(repos_filtered_by_pulls)

                elif lower_bound != None and upper_bound != None:
                    repos_filtered_by_pulls = get_repos_list_by_pulls_bounded_filter(lower_bound, upper_bound)
                    filters.append(repos_filtered_by_pulls)

                if 'has_wiki' in request.POST:
                    repos_that_have_a_wiki = get_repos_list_has_wiki_filter(True)
                    filters.append(repos_that_have_a_wiki)

                if len(filters) != 0:
                    repos_list = get_filtered_repos_list(filters)
                    num_repos = len(repos_list)
                    for item in range(0, len(repos_list)):
                        context.update({
                            f"repo{item}": [repos_list[item], find_repo_main_page(repos_list[item])["owner"]["avatar_url"]]
                        })

                    return render(request, template_name, {"context":context, "filter":filter_form, "num_repos":num_repos})

        
    try:
        for item in range(0, len(mined_repos)):
            context.update({
                f"repo{item}": [mined_repos[item], find_repo_main_page(mined_repos[item])["owner"]["avatar_url"]]
            })
        
        if message == '':
            return render(request, template_name, {"context":context, "filter":filter_form, "num_repos":num_repos})
        else:
            return render(request, template_name, {"context":context, "message":message, 
                                                   "filter":filter_form, "num_repos":num_repos})

    except Exception as e:
        return render(request, template_name, {"error":e})

    


# A function that will be used to generate interactive visualizations of 
# mined JSON data for any repo.
def get_repo_data(request, repo_owner, repo_name):
    template_name = 'mined_repo_display.html'
    original_repo = repo_owner.lower() + "/" + repo_name.lower()
    mined_repos = list(MinedRepo.objects.values_list('repo_name', flat=True)) # Obtain all the mining requests
    
    if original_repo in mined_repos:
        repo = mined_repo_sql_obj = MinedRepo.objects.get(repo_name=original_repo)
        context = get_repo_table_context(original_repo)
        context.update({
            "repo_name":original_repo,
            "repo_img":find_repo_main_page(original_repo)['owner']['avatar_url'],
            "bar_chart_html":getattr(repo, "bar_chart_html"),
            "pull_line_chart_html":getattr(repo, "pull_line_chart_html"), 
            "contribution_line_chart_html": getattr(repo, "contribution_line_chart_html")
        })
        return render(request, template_name, context) 

    else:
        return HttpResponseNotFound('<h1>404 Repo Not Found</h1>')


def compare_two_repos(request, repo_owner1, repo_name1, repo_owner2, repo_name2):
    template_name = 'mined_repo_display_2.html'
    repo_one_full_name = repo_owner1.lower() + "/" + repo_name1.lower()
    repo_two_full_name = repo_owner2.lower() + "/" + repo_name2.lower()

    mined_repos = list(MinedRepo.objects.values_list('repo_name', flat=True)) # Obtain all the mining requests

    if repo_one_full_name in mined_repos and repo_two_full_name in mined_repos:
        context = get_dual_repo_table_context(repo_one_full_name, repo_two_full_name)
        context.update({
            "repo_one_name":repo_one_full_name,
            "repo_one_img":find_repo_main_page(repo_one_full_name)['owner']['avatar_url'],
            "repo_two_name":repo_two_full_name,
            "repo_two_img":find_repo_main_page(repo_two_full_name)['owner']['avatar_url'],
        })
        return render(request, template_name, context) 

    else:
        return HttpResponseNotFound('<h1>404 Repo Not Found</h1>')

def compare_three_repos(request, repo_owner1, repo_name1, repo_owner2, repo_name2, repo_owner3, repo_name3):
    template_name = 'mined_repo_display_3.html'
    repo_one_full_name = repo_owner1.lower() + "/" + repo_name1.lower()
    repo_two_full_name = repo_owner2.lower() + "/" + repo_name2.lower()
    repo_three_full_name = repo_owner3.lower() + "/" + repo_name3.lower()

    mined_repos = list(MinedRepo.objects.values_list('repo_name', flat=True)) # Obtain all the mining requests

    if repo_one_full_name in mined_repos and repo_two_full_name in mined_repos and repo_three_full_name in mined_repos:
        context = get_three_repo_table_context(repo_one_full_name, repo_two_full_name, repo_three_full_name)
        context.update({
            "repo_one_name":repo_one_full_name,
            "repo_one_img":find_repo_main_page(repo_one_full_name)['owner']['avatar_url'],
            "repo_two_name":repo_two_full_name,
            "repo_two_img":find_repo_main_page(repo_two_full_name)['owner']['avatar_url'],
            "repo_three_name":repo_three_full_name,
            "repo_three_img":find_repo_main_page(repo_three_full_name)['owner']['avatar_url'],
        })
        return render(request, template_name, context)

    else:
        return HttpResponseNotFound('<h1>404 Repo Not Found</h1>')
