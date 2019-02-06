# This file will contain all necessary functionality to
# Produce interactive visualizations of data

from mining_scripts.mining import *
from nvd3 import multiBarHorizontalChart
import random 
import datetime



# TODO: Write the code to generate the visualizations we need and
#       return raw HTML representing the visualization 


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
    landing_page = find_repo_main_page(repo_name)
    print(landing_page["description"])

    description = landing_page['description']
    created_at = landing_page['created_at']
    updated_at = landing_page['updated_at']
    clone_url = landing_page['clone_url']
    homepage = landing_page['homepage']
    stargazers_count = landing_page['stargazers_count']
    language = landing_page['language']
    has_wiki = landing_page['has_wiki']
    license_key = landing_page['license']
    open_issues = landing_page['open_issues']
    network_count = landing_page['network_count']
    subscribers_count = landing_page['subscribers_count']

    return {
        "landing_page":str(landing_page),
        "description":str(description),
        "created_at":datetime.datetime.strptime(str(created_at), "%Y-%m-%dT%H:%M:%SZ"),
        "updated_at":datetime.datetime.strptime(str(updated_at), "%Y-%m-%dT%H:%M:%SZ"),
        "clone_url":str(clone_url),
        "homepage":str(homepage),
        "stargazers_count":int(stargazers_count),
        "language":str(language),
        "has_wiki":bool(has_wiki),
        "license_key":str(license_key),
        "open_issues":int(open_issues),
        "network_count":int(network_count),
        "subscribers_count":int(subscribers_count)
    }

         