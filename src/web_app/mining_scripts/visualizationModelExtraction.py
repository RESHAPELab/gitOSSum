from pymongo import MongoClient # Import pymongo for interacting with MongoDB
from github import Github # Import PyGithub for mining data
import datetime
import os
import plotly.plotly as py
import plotly.offline as opy
import plotly.graph_objs as go
import plotly.tools as tls
import pandas as pd
import numpy as np


if os.getpid() == 0:
    # Initial connection by parent process
    client = MongoClient('localhost', 27017) # Where are we connecting
else: 
    # No need to reconnect if we are connected
    client = MongoClient('localhost', 27017, connect=False)

db = client.backend_db # The specific mongo database we are working with 
repos = db.repos # collection for storing all of a repo's main api json information 
pull_requests = db.pullRequests # collection for storing all pull requests for all repos


# Takes in the name of a repo to query, and returns a dict containing num_pulls, 
# num_closed_merged_pulls, num_closed_unmerged_pulls, num_open_pulls, created_at_list, 
# closed_at_list, merged_at_list, and num_newcomer_labels.
def extract_pull_request_model_data(pygit_repo):
    extracted_info = {
        "num_pulls": pull_requests.count_documents({"url": {"$regex": pygit_repo.full_name}}),

        "num_closed_merged_pulls":pull_requests.count_documents({"url": {"$regex": pygit_repo.full_name}, 
                                                                "state":"closed", "merged_at": {"$ne":None}}),

        "num_closed_unmerged_pulls":pull_requests.count_documents({"url": {"$regex": pygit_repo.full_name}, 
                                                                "state":"closed", "merged_at":None}),

        "num_open_pulls":pull_requests.count_documents({"url": {"$regex": pygit_repo.full_name}, 
                                                                "state":"open", "merged_at":None}),

        "people_list": [pull['user']['login'] for pull in pull_requests.find({"url": {"$regex": pygit_repo.full_name}})],
        
        "people_date_tuple":[(pull['user']['login'], datetime.datetime.strptime(str(pull["created_at"]), "%Y-%m-%dT%H:%M:%SZ")) for pull in pull_requests.find({"url": {"$regex": pygit_repo.full_name}})],

        "created_at_list":[datetime.datetime.strptime(str(pull["created_at"]), "%Y-%m-%dT%H:%M:%SZ") 
                            for pull in pull_requests.find({"url": {"$regex": pygit_repo.full_name}})],

        "closed_at_list":[datetime.datetime.strptime(str(pull["closed_at"]), "%Y-%m-%dT%H:%M:%SZ") 
                            for pull in pull_requests.find({"url": {"$regex": pygit_repo.full_name},
                                                                "closed_at": {"$ne":None}})],

        "merged_at_list":[datetime.datetime.strptime(str(pull["merged_at"]), "%Y-%m-%dT%H:%M:%SZ") 
                            for pull in pull_requests.find({"url": {"$regex": pygit_repo.full_name}, 
                                                                "merged_at": {"$ne":None}})],

        "num_newcomer_labels":pull_requests.count_documents({"url": {"$regex": pygit_repo.full_name}, 
                                                                "labels": {"name": {"$regex": "first"}}})
    }
    try:
        extracted_info.update(
            {
                "bar_chart": produce_pull_type_bar_chart(extracted_info),
                "line_chart": produce_pull_requests_per_month_line_chart(extracted_info),
                "contribution_line_chart_html":produce_contributors_per_month_line_chart(extracted_info)
            }
        )
    except Exception as e:
        print("ERROR ON CHARTS:", e)
    return extracted_info


def produce_pull_type_bar_chart(extracted_info):
    num_closed_merged_pulls = extracted_info['num_closed_merged_pulls']
    num_closed_unmerged_pulls = extracted_info['num_closed_unmerged_pulls']
    num_open_pulls = extracted_info['num_open_pulls']

    data = [
        go.Bar(
            x=["Closed-Merged", "Closed-Unmerged", "Open"],
            y=[num_closed_merged_pulls, num_closed_unmerged_pulls, num_open_pulls], 
            name='Pulls Bar Chart',
            marker=dict(
            color=['rgba(255,0,0,1)', 
                    'rgba(0,94,255,1)',
                    'rgba(8,154,105,1)'
                ]
            )
        )
    ]

    layout = go.Layout(
        title='Pull Request Bar Chart',
        xaxis=dict(
        title='Pull Request Type',
        titlefont=dict(
                family='Courier New, monospace',
                size=18,
                color='#7f7f7f'
            )
        ),
        yaxis=dict(
        title='Number of Pull Requests',
        titlefont=dict(
                family='Courier New, monospace',
                size=18,
                color='#7f7f7f'
            )
        )
    )


    figure=go.Figure(data=data,layout=layout)
    div = opy.plot(figure,  output_type='div')

    return div

def produce_pull_requests_per_month_line_chart(extracted_info):
    created_dates_str = extracted_info["created_at_list"]
    closed_dates_str = extracted_info["closed_at_list"]
    merged_dates_str = extracted_info["merged_at_list"]

    try:
        created_dates = pd.to_datetime(pd.Series(created_dates_str), format="%Y-%m-%d %H:%M:%S")
        created_dates.index = created_dates.dt.to_period('m')
        created_dates = created_dates.groupby(level=0).size()
        created_dates = created_dates.reindex(pd.period_range(created_dates.index.min(),
                                            created_dates.index.max(), freq='m'), fill_value=0)
        created_indices = np.array(created_dates.index.astype(str))
        created_date_freq = np.array(created_dates)
    except Exception:
        created_indices = []
        created_date_freq = []

    try:
        closed_dates = pd.to_datetime(pd.Series(closed_dates_str), format="%Y-%m-%d %H:%M:%S")
        closed_dates.index = closed_dates.dt.to_period('m')
        closed_dates = closed_dates.groupby(level=0).size()
        closed_dates = closed_dates.reindex(pd.period_range(closed_dates.index.min(),
                                            closed_dates.index.max(), freq='m'), fill_value=0)
        closed_indices = np.array(closed_dates.index.astype(str))
        closed_date_freq = np.array(closed_dates)
    except:
        closed_indices = []
        closed_date_freq = []

    try:
        merged_dates = pd.to_datetime(pd.Series(merged_dates_str), format="%Y-%m-%d %H:%M:%S")
        merged_dates.index = merged_dates.dt.to_period('m')
        merged_dates = merged_dates.groupby(level=0).size()
        merged_dates = merged_dates.reindex(pd.period_range(merged_dates.index.min(),
                                            merged_dates.index.max(), freq='m'), fill_value=0)
        merged_indices = np.array(merged_dates.index.astype(str))
        merged_date_freq = np.array(merged_dates)
    except Exception:
        merged_indices = []
        merged_date_freq = []
    
    data = [
        go.Scatter(
            x=created_indices, 
            y=created_date_freq,
            mode = 'lines+markers',
            name="Created"
        ),
        go.Scatter(
            x=closed_indices, 
            y=closed_date_freq,
            mode = 'lines+markers',
            name="Closed"
        ),
        go.Scatter(
            x=merged_indices, 
            y=merged_date_freq,
            mode = 'lines+markers',
            name="Merged"
        )
    ]

    layout = go.Layout(
        title='Pull Request Frequency by Month',
        xaxis=dict(
            title='Date',
            titlefont=dict(
                family='Courier New, monospace',
                size=18,
                color='#7f7f7f'
            )
        ),
        yaxis=dict(
            title='Number of Pull Requests',
            titlefont=dict(
                family='Courier New, monospace',
                size=18,
                color='#7f7f7f'
            )
        )
    )

    figure=go.Figure(data=data,layout=layout)

    div = opy.plot(figure,  output_type='div')
    return div

def produce_contributors_per_month_line_chart(extracted_info):
    people = extracted_info['people_list']
    created = extracted_info['created_at_list']

    # We need this to refer back to rows 
    raw_data = pd.DataFrame({
        'person':people,
        'month':pd.to_datetime(pd.Series(created), format="%Y-%m-%d %H:%M:%S")
    })

    # Create a dataframe with people and month of contribution as the columns
    filtered_df = pd.DataFrame({
        'person':people,
        'month':pd.to_datetime(pd.Series(created), format="%Y-%m-%d %H:%M:%S").dt.to_period('m')
    })

    # eliminate duplicate rows (people showing up more than once each month)
    filtered_df = filtered_df.drop_duplicates()

    # Get the rows with their indexes 
    dates = pd.Series(filtered_df['month'])

    # refer back to the raw data by index
    dates = raw_data.iloc[dates.index]['month']

    # Convert this data it only look at the month 
    dates.index = dates.dt.to_period('m')

    # Group by the month and count the occurrences 
    dates = dates.groupby(level=0).size()

    # Fill in missing months with the vlaue '0'
    dates = dates.reindex(pd.period_range(dates.index.min(),
                                        dates.index.max(), freq='m'), fill_value=0)

    # Get the months as a string for our x-axis
    dates_indices = np.array(dates.index.astype(str))

    # Get the frequency as a list for the y-axis 
    dates_freq = np.array(dates)

    # Now all we need to do is plot this bad boy! 
    data = [
        go.Scatter(
            x=dates_indices, 
            y=dates_freq,
            mode = 'lines+markers',
            name="Contribution"
        )
    ]

    layout = go.Layout(
        title='Contribution Frequency by Month',
        xaxis=dict(
            title='Date',
            titlefont=dict(
                family='Courier New, monospace',
                size=18,
                color='#7f7f7f'
            )
        ),
        yaxis=dict(
            title='Number of People Contributing',
            titlefont=dict(
                family='Courier New, monospace',
                size=18,
                color='#7f7f7f'
            )
        )
    )

    figure=go.Figure(data=data,layout=layout)

    div = opy.plot(figure,  output_type='div')
    return div