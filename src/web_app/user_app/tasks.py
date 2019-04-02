from __future__ import absolute_import, unicode_literals

from web_app.celery import app
from celery.utils.log import get_task_logger
from celery.result import AsyncResult
from celery.task.control import revoke
from mining_scripts.mining import *
from mining_scripts.send_email import *
from github import GithubException
from django.db import transaction
from mining_scripts.batchify import *
import time 
from datetime import datetime
import json
from user_app.models import QueuedMiningRequest, MinedRepo
from django.contrib.auth.models import User
import sys
import numpy as np
from django.utils import timezone
import os

# Handle parallel processing not knowing about django apps
try:
    from django.apps import apps
    apps.check_apps_ready()
except AppRegistryNotReady:
    import django
    django.setup()

if os.getpid() == 0:
    # Initial connection by parent process
    client = MongoClient('localhost', 27017) # Where are we connecting
else: 
    # No need to reconnect if we are connected
    client = MongoClient('localhost', 27017, connect=False)

db = client.backend_db # The specific mongo database we are working with 

repos = db.repos # collection for storing all of a repo's main api json information 

pull_requests = db.pullRequests # collection for storing all pull requests for all repos 

pull_batches = db.pullBatches

g = Github(GITHUB_TOKEN, per_page=100) # authorization for the github API 
logger = get_task_logger(__name__)

class CeleryTaskFailedError(Exception):
    pass


def all_tasks_completed(repo_name):
    total_batches = db.pullBatches.find_one({"repo":repo_name})["total_batches"]
    collected_batches = db.pullBatches.find_one({"repo":repo_name})["collected_batches"]
    attempted_batches = db.pullBatches.find_one({"repo":repo_name})["attempted_batches"]
    
    if collected_batches == total_batches:
        return True
        
    else:
        return False 

def initialize_batch_json(batch_list, repo_name):
    total_batches = len(batch_list)
    batch_json_data  = {
        "repo": f"{repo_name}",
        "BATCH_SIZE": BATCH_SIZE,
        "total_batches": total_batches,
        "collected_batches": 0,
        "attempted_batches": 0,
        "updated": str(timezone.now())
    }
    db.pullBatches.update_one(batch_json_data, {"$set": batch_json_data}, upsert=True)



# When the admin approves, go call the mining script asynchronously 
@app.task(bind=True, name='tasks.mine_data_asynchronously', hard_time_limit=60*60*10)
def mine_data_asynchronously(self, repo_name, username, user_email, queued_request):    
    pygit_repo = g.get_repo(repo_name)

    # mine and store the main page josn
    mine_repo_page(pygit_repo)

    batch_data = batchify(repo_name)

    # TODO: If there are no pull requests, just make a table, no graphs 
    
    # Else, move on to mining the data 
    initialize_batch_json(batch_data, repo_name)

    for job in range(len(batch_data)):
        mine_pull_request_batch_asynchronously.delay(repo_name, job)

    return True 


@app.task(name='tasks.mine_pull_request_batch_asynchronously', hard_time_limit=60*60*3)
def mine_pull_request_batch_asynchronously(repo_name, job):
    pulls_batch = get_batch_number(repo_name, job)
    
    mine_pulls_batch(pulls_batch, repo_name)

    return True

@app.task(name='tasks.update_all_repos')
def update_all_repos():
    mined_repos = list(MinedRepo.objects.values_list('repo_name', flat=True)) # Obtain all the mining requests
    
    for repo in mined_repos:
        update_specific_repo.delay(repo)

    return True 


@app.task(name='tasks.update_specific_repo')
def update_specific_repo(repo_name):
    pygit_repo = g.get_repo(repo_name)
    mine_repo_page(pygit_repo) # update the landing page

    # get a list of all the current pull requests 
    num_current_pulls = count_all_pull_requests_from_a_specifc_repo(repo_name)

    # get a paginated list of all the pull requests
    pulls = pygit_repo.get_pulls('all')

    # get the number of pulls that we can see now
    total_pulls_as_of_now = 0
    for item in pulls:
        total_pulls_as_of_now += 1

    # DO NOT CONTINUE IF THERE AREN'T NEW PULLS
    if total_pulls_as_of_now == num_current_pulls:
        mined_repo_model_obj = MinedRepo.objects.get(repo_name=repo_name)
        mined_repo_model_obj.completed_timestamp = str(timezone.now())
        mined_repo_model_obj.save()
        return 

    # IF THERE ARE NEW PULLS, MINE THEM...
    new_pygit_pulls_list = [pulls[item] for item in range(num_current_pulls+2, total_pulls_as_of_now)]

    for pygit_pull_obj in new_pygit_pulls_list:
        mine_specific_pull(pygit_pull_obj)

    mined_repo_model_obj = MinedRepo.objects.get(repo_name=repo_name)

    visualization_data = extract_pull_request_model_data(pygit_repo)

    mined_repo_model_obj.num_pulls=visualization_data["num_pulls"]
    mined_repo_model_obj.num_closed_merged_pulls=visualization_data["num_closed_merged_pulls"]
    mined_repo_model_obj.num_closed_unmerged_pulls=visualization_data["num_closed_unmerged_pulls"]
    mined_repo_model_obj.num_open_pulls=visualization_data["num_open_pulls"]
    mined_repo_model_obj.created_at_list=visualization_data["created_at_list"]
    mined_repo_model_obj.closed_at_list=visualization_data["closed_at_list"]
    mined_repo_model_obj.merged_at_list=visualization_data["merged_at_list"]
    mined_repo_model_obj.num_newcomer_labels=visualization_data["num_newcomer_labels"]
    mined_repo_model_obj.bar_chart_html=visualization_data["bar_chart"]
    mined_repo_model_obj.pull_line_chart_html=visualization_data["line_chart"]
    mined_repo_model_obj.completed_timestamp = str(timezone.now())
    mined_repo_model_obj.save()

    return True 

@app.task(name='tasks.visualize_repo_data')
def visualize_repo_data():
    mined_repos = list(MinedRepo.objects.values_list('repo_name', flat=True)) # Obtain all the mining requests
    batched_repos = [batch['repo'] for batch in pull_batches.find({}, {"_id":0, "repo":1})]
    repos_needing_rendering = np.setdiff1d(batched_repos,mined_repos)
    if len(repos_needing_rendering) != 0:
        for repo_name in repos_needing_rendering:
            if all_tasks_completed(repo_name) == False:
                continue
            username = getattr(QueuedMiningRequest.objects.get(repo_name=repo_name), "requested_by")
            # It is finished, time to visualize it 
            logger.info('Extracting visualization data for {0}'.format(repo_name))
            visualization_data = extract_pull_request_model_data(g.get_repo(repo_name))
            logger.info('Successfully extracted visualization data for {0}'.format(repo_name))

            logger.info('Creating MinedRepo database object for {0}'.format(repo_name))
            # Add this repo to the mined repos table
            mined_repo = MinedRepo(
                repo_name=repo_name,
                requested_by=username,
                num_pulls=visualization_data["num_pulls"],
                num_closed_merged_pulls=visualization_data["num_closed_merged_pulls"],
                num_closed_unmerged_pulls=visualization_data["num_closed_unmerged_pulls"],
                num_open_pulls=visualization_data["num_open_pulls"],
                created_at_list=visualization_data["created_at_list"],
                closed_at_list=visualization_data["closed_at_list"],
                merged_at_list=visualization_data["merged_at_list"],
                num_newcomer_labels=visualization_data["num_newcomer_labels"],
                bar_chart_html=visualization_data["bar_chart"],
                pull_line_chart_html=visualization_data["line_chart"],
                accepted_timestamp=getattr(QueuedMiningRequest.objects.get(repo_name=repo_name), "timestamp"),
                requested_timestamp=getattr(QueuedMiningRequest.objects.get(repo_name=repo_name), "requested_timestamp")
            ) 

            mined_repo.save()
            logger.info('Successfully created MinedRepo database object for {0}'.format(repo_name))

            QueuedMiningRequest.objects.get(repo_name=repo_name).delete()

            send_confirmation_email(repo_name, username, getattr(User.objects.get(username=username), 'email'))
