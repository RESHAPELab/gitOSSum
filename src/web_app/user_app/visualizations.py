# This file will contain all necessary functionality to
# Produce interactive visualizations of data

from mining_scripts.mining import *
from user_app.models import MinedRepo
from nvd3 import multiBarHorizontalChart, discreteBarChart
import random 
import datetime

import plotly.plotly as py
import plotly.offline as opy
import plotly.graph_objs as go
import plotly.tools as tls
import pandas as pd
import numpy as np

# Example using mutli-bar chart 
def multi_bar_chart():
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
    return chart.htmlcontent

def get_repo_table_context(repo_name):
    mined_repo_sql_obj = MinedRepo.objects.get(repo_name=repo_name)
    landing_page = find_repo_main_page(repo_name)
    num_pulls = getattr(mined_repo_sql_obj, 'num_pulls')
    num_closed_merged_pulls = getattr(mined_repo_sql_obj, 'num_closed_merged_pulls')
    num_closed_unmerged_pulls = getattr(mined_repo_sql_obj, 'num_closed_unmerged_pulls')
    num_open_pulls = getattr(mined_repo_sql_obj, 'num_open_pulls')
    description = landing_page['description']
    created_at = landing_page['created_at']
    updated_at = landing_page['updated_at']
    last_mined_date = getattr(mined_repo_sql_obj, "completed_timestamp")
    clone_url = landing_page['clone_url']
    homepage = str(landing_page['homepage'])
    if str(homepage).strip() == "" or str(homepage) == "None" or str(homepage) == "null":
        homepage = False
    stargazers_count = landing_page['stargazers_count']
    language = landing_page['language']
    has_wiki = landing_page['has_wiki']
    try:
        license_key = str(landing_page['license']["key"])
        license_name = str(landing_page['license']['name'])
    except Exception:
        license_key = None
        license_name = None 
    open_issues = landing_page['open_issues']
    network_count = landing_page['network_count']
    subscribers_count = landing_page['subscribers_count']

    return {
        "num_pulls":num_pulls,
        "num_closed_merged_pulls":num_closed_merged_pulls,
        "num_closed_unmerged_pulls":num_closed_unmerged_pulls, 
        "num_open_pulls":num_open_pulls,
        "description":str(description),
        "created_at":datetime.datetime.strptime(str(created_at), "%Y-%m-%dT%H:%M:%SZ"),
        "updated_at":datetime.datetime.strptime(str(updated_at), "%Y-%m-%dT%H:%M:%SZ"),
        "last_mined_date":last_mined_date,
        "clone_url":str(clone_url),
        "homepage":homepage,
        "stargazers_count":int(stargazers_count),
        "language":str(language),
        "has_wiki":bool(has_wiki),
        "license_key":str(license_key),
        "license_name":str(license_name),
        "open_issues":int(open_issues),
        "network_count":int(network_count),
        "subscribers_count":int(subscribers_count)
    }



def get_dual_repo_table_context(repo_one_full_name, repo_two_full_name):
    context = dict()
    
    mined_repo_one_sql_obj = MinedRepo.objects.get(repo_name=repo_one_full_name)
    mined_repo_two_sql_obj = MinedRepo.objects.get(repo_name=repo_two_full_name)

    landing_page_repo_one = find_repo_main_page(repo_one_full_name)
    landing_page_repo_two = find_repo_main_page(repo_two_full_name)

    num_pulls_repo_one = getattr(mined_repo_one_sql_obj, 'num_pulls')
    num_pulls_repo_two = getattr(mined_repo_two_sql_obj, 'num_pulls')
    context.update({
        'num_pulls_repo_one':num_pulls_repo_one,
        'num_pulls_repo_two':num_pulls_repo_two
    })

    num_closed_merged_pulls_repo_one = getattr(mined_repo_one_sql_obj, 'num_closed_merged_pulls')
    num_closed_merged_pulls_repo_two = getattr(mined_repo_two_sql_obj, 'num_closed_merged_pulls')
    context.update({
        'num_closed_merged_pulls_repo_one':num_closed_merged_pulls_repo_one,
        'num_closed_merged_pulls_repo_two':num_closed_merged_pulls_repo_two
    })

    num_closed_unmerged_pulls_repo_one = getattr(mined_repo_one_sql_obj, 'num_closed_unmerged_pulls')
    num_closed_unmerged_pulls_repo_two = getattr(mined_repo_two_sql_obj, 'num_closed_unmerged_pulls')
    context.update({
        'num_closed_unmerged_pulls_repo_one':num_closed_unmerged_pulls_repo_one,
        'num_closed_unmerged_pulls_repo_two':num_closed_unmerged_pulls_repo_two
    })

    num_open_pulls_repo_one = getattr(mined_repo_one_sql_obj, 'num_open_pulls')
    num_open_pulls_repo_two = getattr(mined_repo_two_sql_obj, 'num_open_pulls')
    context.update({
        'num_open_pulls_repo_one':num_open_pulls_repo_one,
        'num_open_pulls_repo_two':num_open_pulls_repo_two
    })

    description_repo_one = landing_page_repo_one['description']
    description_repo_two = landing_page_repo_two['description']
    context.update({
        'description_repo_one':description_repo_one,
        'description_repo_two':description_repo_two
    })

    created_at_repo_one = datetime.datetime.strptime(str(landing_page_repo_one['created_at']), "%Y-%m-%dT%H:%M:%SZ")
    created_at_repo_two = datetime.datetime.strptime(str(landing_page_repo_two['created_at']), "%Y-%m-%dT%H:%M:%SZ")
    context.update({
        'created_at_repo_one':created_at_repo_one,
        'created_at_repo_two':created_at_repo_two
    })

    updated_at_repo_one = datetime.datetime.strptime(str(landing_page_repo_one['updated_at']), "%Y-%m-%dT%H:%M:%SZ")
    updated_at_repo_two = datetime.datetime.strptime(str(landing_page_repo_two['updated_at']), "%Y-%m-%dT%H:%M:%SZ")
    context.update({
        'updated_at_repo_one':updated_at_repo_one,
        'updated_at_repo_two':updated_at_repo_two
    })

    last_mined_date_repo_one = getattr(MinedRepo.objects.get(repo_name=repo_one_full_name), "completed_timestamp")
    last_mined_date_repo_two = getattr(MinedRepo.objects.get(repo_name=repo_two_full_name), "completed_timestamp")
    context.update({
        'last_mined_date_repo_one':last_mined_date_repo_one,
        'last_mined_date_repo_two':last_mined_date_repo_two
    })

    clone_url_repo_one = landing_page_repo_one['clone_url']
    clone_url_repo_two = landing_page_repo_two['clone_url']
    context.update({
        'clone_url_repo_one':clone_url_repo_one,
        'clone_url_repo_two':clone_url_repo_two
    })

    homepage_repo_one = str(landing_page_repo_one['homepage'])
    homepage_repo_two = str(landing_page_repo_two['homepage'])

    if homepage_repo_one.strip() == "" or homepage_repo_one.strip() == "None" or homepage_repo_one.strip == "null":
        homepage_repo_one = "None"

    if homepage_repo_two.strip() == "" or homepage_repo_two.strip() == "None" or homepage_repo_two.strip == "null":
        homepage_repo_two = "None"

    context.update({
        'homepage_repo_one':homepage_repo_one,
        'homepage_repo_two':homepage_repo_two
    })

    stargazers_count_repo_one = landing_page_repo_one['stargazers_count']
    stargazers_count_repo_two = landing_page_repo_two['stargazers_count']
    context.update({
        'stargazers_count_repo_one':stargazers_count_repo_one,
        'stargazers_count_repo_two':stargazers_count_repo_two
    })

    language_repo_one = landing_page_repo_one['language']
    language_repo_two = landing_page_repo_two['language']
    context.update({
        'language_repo_one':language_repo_one,
        'language_repo_two':language_repo_two
    })

    has_wiki_repo_one = landing_page_repo_one['has_wiki']
    has_wiki_repo_two = landing_page_repo_two['has_wiki']
    context.update({
        'has_wiki_repo_one':has_wiki_repo_one,
        'has_wiki_repo_two':has_wiki_repo_two
    })

    try:
        license_key_repo_one = landing_page_repo_one['license']["key"]
        license_name_repo_one = landing_page_repo_one['license']['name']
    except Exception:
        license_key_repo_one = "None"
        license_name_repo_one = "None" 

    try:
        license_key_repo_two = landing_page_repo_two['license']["key"]
        license_name_repo_two = landing_page_repo_two['license']['name']
    except Exception:
        license_key_repo_two = "None"
        license_name_repo_two = "None" 

    context.update({
        'license_key_repo_one':license_key_repo_one,
        'license_name_repo_one':license_name_repo_one,
        'license_key_repo_two':license_key_repo_two,
        'license_name_repo_two':license_name_repo_two
    })


    
    open_issues_repo_one = landing_page_repo_one['open_issues']
    open_issues_repo_two = landing_page_repo_two['open_issues']
    context.update({
        'open_issues_repo_one':open_issues_repo_one,
        'open_issues_repo_two':open_issues_repo_two
    })

    network_count_repo_one = landing_page_repo_one['network_count']
    network_count_repo_two =landing_page_repo_two['network_count']
    context.update({
        'network_count_repo_one':network_count_repo_one,
        'network_count_repo_two':network_count_repo_two
    })

    subscribers_count_repo_one = landing_page_repo_one['subscribers_count']
    subscribers_count_repo_two = landing_page_repo_two['subscribers_count']
    context.update({
        'subscribers_count_repo_one':subscribers_count_repo_one,
        'subscribers_count_repo_two':subscribers_count_repo_two
    })

    return context

def get_three_repo_table_context(repo_one_full_name, repo_two_full_name, repo_three_full_name):
    context = dict()
    
    mined_repo_one_sql_obj = MinedRepo.objects.get(repo_name=repo_one_full_name)
    mined_repo_two_sql_obj = MinedRepo.objects.get(repo_name=repo_two_full_name)
    mined_repo_three_sql_obj = MinedRepo.objects.get(repo_name=repo_three_full_name)

    landing_page_repo_one = find_repo_main_page(repo_one_full_name)
    landing_page_repo_two = find_repo_main_page(repo_two_full_name)
    landing_page_repo_three = find_repo_main_page(repo_three_full_name)

    num_pulls_repo_one = getattr(mined_repo_one_sql_obj, 'num_pulls')
    num_pulls_repo_two = getattr(mined_repo_two_sql_obj, 'num_pulls')
    num_pulls_repo_three = getattr(mined_repo_three_sql_obj, 'num_pulls')
    context.update({
        'num_pulls_repo_one':num_pulls_repo_one,
        'num_pulls_repo_two':num_pulls_repo_two,
        'num_pulls_repo_three':num_pulls_repo_three
    })

    num_closed_merged_pulls_repo_one = getattr(mined_repo_one_sql_obj, 'num_closed_merged_pulls')
    num_closed_merged_pulls_repo_two = getattr(mined_repo_two_sql_obj, 'num_closed_merged_pulls')
    num_closed_merged_pulls_repo_three = getattr(mined_repo_three_sql_obj, 'num_closed_merged_pulls')
    context.update({
        'num_closed_merged_pulls_repo_one':num_closed_merged_pulls_repo_one,
        'num_closed_merged_pulls_repo_two':num_closed_merged_pulls_repo_two,
        'num_closed_merged_pulls_repo_three':num_closed_merged_pulls_repo_three
    })

    num_closed_unmerged_pulls_repo_one = getattr(mined_repo_one_sql_obj, 'num_closed_unmerged_pulls')
    num_closed_unmerged_pulls_repo_two = getattr(mined_repo_two_sql_obj, 'num_closed_unmerged_pulls')
    num_closed_unmerged_pulls_repo_three = getattr(mined_repo_three_sql_obj, 'num_closed_unmerged_pulls')
    context.update({
        'num_closed_unmerged_pulls_repo_one':num_closed_unmerged_pulls_repo_one,
        'num_closed_unmerged_pulls_repo_two':num_closed_unmerged_pulls_repo_two,
        'num_closed_unmerged_pulls_repo_three':num_closed_unmerged_pulls_repo_three
    })

    num_open_pulls_repo_one = getattr(mined_repo_one_sql_obj, 'num_open_pulls')
    num_open_pulls_repo_two = getattr(mined_repo_two_sql_obj, 'num_open_pulls')
    num_open_pulls_repo_three = getattr(mined_repo_three_sql_obj, 'num_open_pulls')
    context.update({
        'num_open_pulls_repo_one':num_open_pulls_repo_one,
        'num_open_pulls_repo_two':num_open_pulls_repo_two,
        'num_open_pulls_repo_three':num_open_pulls_repo_three
    })

    description_repo_one = landing_page_repo_one['description']
    description_repo_two = landing_page_repo_two['description']
    description_repo_three = landing_page_repo_three['description']
    context.update({
        'description_repo_one':description_repo_one,
        'description_repo_two':description_repo_two,
        'description_repo_three':description_repo_three
    })

    created_at_repo_one = datetime.datetime.strptime(str(landing_page_repo_one['created_at']), "%Y-%m-%dT%H:%M:%SZ")
    created_at_repo_two = datetime.datetime.strptime(str(landing_page_repo_two['created_at']), "%Y-%m-%dT%H:%M:%SZ")
    created_at_repo_three = datetime.datetime.strptime(str(landing_page_repo_three['created_at']), "%Y-%m-%dT%H:%M:%SZ")
    context.update({
        'created_at_repo_one':created_at_repo_one,
        'created_at_repo_two':created_at_repo_two,
        'created_at_repo_three':created_at_repo_three
    })

    updated_at_repo_one = datetime.datetime.strptime(str(landing_page_repo_one['updated_at']), "%Y-%m-%dT%H:%M:%SZ")
    updated_at_repo_two = datetime.datetime.strptime(str(landing_page_repo_two['updated_at']), "%Y-%m-%dT%H:%M:%SZ")
    updated_at_repo_three = datetime.datetime.strptime(str(landing_page_repo_three['updated_at']), "%Y-%m-%dT%H:%M:%SZ")
    context.update({
        'updated_at_repo_one':updated_at_repo_one,
        'updated_at_repo_two':updated_at_repo_two,
        'updated_at_repo_three':updated_at_repo_three
    })

    last_mined_date_repo_one = getattr(MinedRepo.objects.get(repo_name=repo_one_full_name), "completed_timestamp")
    last_mined_date_repo_two = getattr(MinedRepo.objects.get(repo_name=repo_two_full_name), "completed_timestamp")
    last_mined_date_repo_three = getattr(MinedRepo.objects.get(repo_name=repo_three_full_name), "completed_timestamp")
    context.update({
        'last_mined_date_repo_one':last_mined_date_repo_one,
        'last_mined_date_repo_two':last_mined_date_repo_two,
        'last_mined_date_repo_three':last_mined_date_repo_three
    })

    clone_url_repo_one = landing_page_repo_one['clone_url']
    clone_url_repo_two = landing_page_repo_two['clone_url']
    clone_url_repo_three = landing_page_repo_three['clone_url']
    context.update({
        'clone_url_repo_one':clone_url_repo_one,
        'clone_url_repo_two':clone_url_repo_two,
        'clone_url_repo_three':clone_url_repo_three
    })

    homepage_repo_one = str(landing_page_repo_one['homepage'])
    homepage_repo_two = str(landing_page_repo_two['homepage'])
    homepage_repo_three = str(landing_page_repo_three['homepage'])

    if str(homepage_repo_one).strip() == "" or str(homepage_repo_one) == "None" or str(homepage_repo_one) == "null":
        homepage_repo_one = "None"

    if str(homepage_repo_two).strip() == "" or str(homepage_repo_two) == "None" or str(homepage_repo_two) == "null":
        homepage_repo_two = "None"

    if str(homepage_repo_three).strip() == "" or str(homepage_repo_three) == "None" or str(homepage_repo_three) == "null":
        homepage_repo_three = "None"

    context.update({
        'homepage_repo_one':homepage_repo_one,
        'homepage_repo_two':homepage_repo_two,
        'homepage_repo_three':homepage_repo_three
    })

    stargazers_count_repo_one = landing_page_repo_one['stargazers_count']
    stargazers_count_repo_two = landing_page_repo_two['stargazers_count']
    stargazers_count_repo_three = landing_page_repo_three['stargazers_count']
    context.update({
        'stargazers_count_repo_one':stargazers_count_repo_one,
        'stargazers_count_repo_two':stargazers_count_repo_two,
        'stargazers_count_repo_three':stargazers_count_repo_three
    })

    language_repo_one = landing_page_repo_one['language']
    language_repo_two = landing_page_repo_two['language']
    language_repo_three = landing_page_repo_three['language']
    context.update({
        'language_repo_one':language_repo_one,
        'language_repo_two':language_repo_two,
        'language_repo_three':language_repo_three
    })

    has_wiki_repo_one = landing_page_repo_one['has_wiki']
    has_wiki_repo_two = landing_page_repo_two['has_wiki']
    has_wiki_repo_three = landing_page_repo_three['has_wiki']
    context.update({
        'has_wiki_repo_one':has_wiki_repo_one,
        'has_wiki_repo_two':has_wiki_repo_two,
        'has_wiki_repo_three':has_wiki_repo_three
    })

    try:
        license_key_repo_one = landing_page_repo_one['license']["key"]
        license_name_repo_one = landing_page_repo_one['license']['name']
    except Exception:
        license_key_repo_one = None
        license_name_repo_one = None 

    try:
        license_key_repo_two = landing_page_repo_two['license']["key"]
        license_name_repo_two = landing_page_repo_two['license']['name']
    except Exception:
        license_key_repo_two = None
        license_name_repo_two = None

    try:
        license_key_repo_three = landing_page_repo_three['license']["key"]
        license_name_repo_three = landing_page_repo_three['license']['name']
    except Exception:
        license_key_repo_three = None
        license_name_repo_three = None

    context.update({
        'license_key_repo_one':license_key_repo_one,
        'license_name_repo_one':license_name_repo_one,
        'license_key_repo_two':license_key_repo_two,
        'license_name_repo_two':license_name_repo_two,
        'license_key_repo_three':license_key_repo_three,
        'license_name_repo_three':license_name_repo_three
    })



    open_issues_repo_one = landing_page_repo_one['open_issues']
    open_issues_repo_two = landing_page_repo_two['open_issues']
    open_issues_repo_three = landing_page_repo_three['open_issues']
    context.update({
        'open_issues_repo_one':open_issues_repo_one,
        'open_issues_repo_two':open_issues_repo_two,
        'open_issues_repo_three':open_issues_repo_three
    })

    network_count_repo_one = landing_page_repo_one['network_count']
    network_count_repo_two =landing_page_repo_two['network_count']
    network_count_repo_three =landing_page_repo_three['network_count']
    context.update({
        'network_count_repo_one':network_count_repo_one,
        'network_count_repo_two':network_count_repo_two,
        'network_count_repo_three':network_count_repo_three
    })

    subscribers_count_repo_one = landing_page_repo_one['subscribers_count']
    subscribers_count_repo_two = landing_page_repo_two['subscribers_count']
    subscribers_count_repo_three = landing_page_repo_three['subscribers_count']
    context.update({
        'subscribers_count_repo_one':subscribers_count_repo_one,
        'subscribers_count_repo_two':subscribers_count_repo_two,
        'subscribers_count_repo_three':subscribers_count_repo_three
    })

    return context