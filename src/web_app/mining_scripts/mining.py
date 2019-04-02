#!/usr/bin/env python
# -*- coding: utf-8 -*-
# mining.py
# Created by Stephen White
# Date: 1/22/2019
# Purpose: This script will provide the necessary functionality to store json data
#          from GitHub's API into the MongoDB database of our choosing 

from pymongo import MongoClient # Import pymongo for interacting with MongoDB
from github import Github # Import PyGithub for mining data
from mining_scripts.send_email import * 
from mining_scripts.config import *
from mining_scripts.visualizationModelExtraction import *
from django.core.exceptions import AppRegistryNotReady
from celery.utils.log import get_task_logger # For the server's logger
from celery import group
from retrying import retry
import os
import time
from datetime import datetime
from mining_scripts.batchify import BatchedGeneratorTask
import gc

logger = get_task_logger(__name__) # Retrieve the actual logger 


# Handle parallel processing not knowing about django apps
try:
    from django.apps import apps
    apps.check_apps_ready()
except AppRegistryNotReady:
    import django
    django.setup()

# Only import the models after we know django has been setup 
from user_app.models import QueuedMiningRequest, MinedRepo

# precent issues with forking 
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

def mongo_mining_test_init():
    global db 
    global repos 
    global pull_requests
    global pull_batches 
    db = client.test_db
    repos = db.repos
    pull_requests = db.pullRequests
    pull_batches = db.pullBatches



g = Github(GITHUB_TOKEN, per_page=100) # authorization for the github API 


# Wrapper function that will perform all mining steps necessary when
# provided with the repository name
def mine_and_store_all_repo_data(repo_name, username, email, queued_request):

    # Use pygit to eliminate any problems with users not spelling the repo name
    # exactly as it is on the actual repo 
    logger.info('Retrieving the pygit_repo from github for {0}'.format(repo_name))
    pygit_repo = g.get_repo(repo_name)
    logger.info('Successfully retrieved pygit_repo from github for {0}'.format(repo_name))

    # mine and store the main page josn
    logger.info('Mining the  the landing page JSON from github for {0}'.format(repo_name))
    mine_repo_page(pygit_repo)
    logger.info('Successfully mined the landing page JSON from github for {0}'.format(repo_name))

    # mine and store all pulls for this repo 
    logger.info('Starting to mine pull requests from github for {0}'.format(repo_name))
    mine_pulls_from_repo(pygit_repo)
    logger.info('Successfully mined all pull requests from github for {0}'.format(repo_name))

    logger.info('Extracting visualization data for {0}'.format(repo_name))
    visualization_data = extract_pull_request_model_data(pygit_repo)
    logger.info('Successfully extracted visualization data for {0}'.format(repo_name))

    logger.info('Creating MinedRepo database object for {0}'.format(repo_name))
    # Add this repo to the mined repos table
    MinedRepo.objects.create(
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
        accepted_timestamp=getattr(QueuedMiningRequest.objects.get(pk=queued_request), "timestamp"),
        requested_timestamp=getattr(QueuedMiningRequest.objects.get(pk=queued_request), "requested_timestamp")
    ) 
    logger.info('Successfully created MinedRepo database object for {0}'.format(repo_name))

    # Delete the request from the MiningRequest Database
    logger.info('Deleting QueuedMiningRequest database object for {0}'.format(repo_name))
    QueuedMiningRequest.objects.get(repo_name=repo_name).delete()
    logger.info('Successfully deleted QueuedMiningRequest database object for {0}'.format(repo_name))

    # send any emails as necessary
    logger.info('Sending email confirmation to "{0}" in regard to {1}'.format(email, repo_name))
    send_confirmation_email(repo_name, username, email)
    logger.info('Successfully sent email confirmation to "{0}" in regard to {1}'.format(email, repo_name))

    return 


# Method to download a repo's main json and place it in the 
# db.repos collection for future parsing 
def mine_repo_page(pygit_repo):
    repos.update_one(pygit_repo.raw_data, {"$set": pygit_repo.raw_data}, upsert=True)
    return 


# Function that will delete all repos from the repos collection of the mongodb database
def delete_all_repos_from_repo_collection():
    repos.delete_many({})
    return


# Method to find a specific repo in the repos collection and delete it 
def delete_specific_repo_from_repo_collection(repo_name):
    pygit_repo = g.get_repo(repo_name)
    repos.delete_one({"full_name":pygit_repo.full_name})
    return

# Method to remove all pull requests from the pull request collection 
def delete_all_pulls_from_pull_request_collection():
    pull_requests.delete_many({})
    return


# Method to delete all pull requests belonging to a specific repo 
# from the pullRequests collection 
def delete_specifc_repos_pull_requests(repo_name):
    pygit_repo = g.get_repo(repo_name)
    pull_requests.delete_many({"url": {"$regex": pygit_repo.full_name}})
    return

def rate_limit_is_reached():
    num_requests_remaining = get_number_of_remaining_requests()
    if num_requests_remaining == 0:
        return True 
    else:
        logger.info('NUMBER OF GITHUB REQUESTS REMAINING: {0}'.format(num_requests_remaining))
        return False 

def get_number_of_remaining_requests():
    g = Github(GITHUB_TOKEN, per_page=100) # Update authorization to have up to date requests remaining 
    return  g.rate_limiting[0] # the current number of remaining requests

def get_num_seconds_until_rate_limit_reset():
    current_time_unix = time.mktime(datetime.now().timetuple())
    rate_limit_reset_time_unix = g.rate_limiting_resettime
    num_seconds=rate_limit_reset_time_unix-current_time_unix
    num_minutes=num_seconds / 60
    logger.info('RATE LIMIT REACHED! WAITING FOR {0} minutes.'.format(num_minutes))
    return num_seconds

def wait_for_request_rate_reset():
    time.sleep(get_num_seconds_until_rate_limit_reset())
    time.sleep(1)  
    logger.info('Getting a new Github Token...') 
    g = Github(GITHUB_TOKEN, per_page=100) # Update authorization to have up to date requests remaining 

    logger.info('RATE LIMIT HAS BEEN RESET! STARTING TO MINE AGAIN.')
    return

# Method to download all pull requests of a given repo and 
# put them within the db.pullRequests collection 
def mine_pulls_from_repo(pygit_repo):
    logger.info('Retrieving a list of all pull requests for "{0}".'.format(pygit_repo.full_name))

    # Retrieve all pull request numbers associated with this repo 
    pulls = pygit_repo.get_pulls('all')
    logger.info('Successfully retrieved a list of all pull requests for "{0}".'.format(pygit_repo.full_name))

    logger.info('Beginning to mine individual pull requests for "{0}".'.format(pygit_repo.full_name))
    
    for pull in pulls:
        
        # Only mine data when we have remaining requests
        if rate_limit_is_reached():
            wait_for_request_rate_reset() # Dynamically wait for a given number of seconds
        else:
            mine_specific_pull(pygit_repo.full_name, pull) # Go mine stuff!

    return 

def increase_collected_batches_count(repo_name):
    document = pull_batches.find_one({"repo":repo_name})
    current_count = pull_batches.find_one({"repo":repo_name})["collected_batches"] 
    pull_batches.update_one(document, {"$set": {"collected_batches": current_count + 1}}, upsert=False)
    return 

def increase_attempted_batches_count(repo_name):
    document = pull_batches.find_one({"repo":repo_name})
    current_count = pull_batches.find_one({"repo":repo_name})["attempted_batches"] 
    pull_batches.update_one(document, {"$set": {"attempted_batches": current_count + 1}}, upsert=False)
    return 

def mine_pulls_batch(pulls_batch, repo_name):
    increase_attempted_batches_count(repo_name)
    try:
        for pull in range(len(pulls_batch)):
            if rate_limit_is_reached():
                wait_for_request_rate_reset() # Dynamically wait for a given number of seconds
            else:
                mine_specific_pull(next(pulls_batch)) # Move the iterator to the next pull request & mine
        increase_collected_batches_count(repo_name)
        # gc.collect()
        return True
    except Exception: 
        return False

# Mine and store specific repo. If there are any errors (other than 503),
# retry with exponential backoff 10 times. Fail after 10th attempt 
# @retry(wait_exponential_multiplier=1000, wait_exponential_max=10000, stop_max_attempt_number=10)
def mine_specific_pull(pull):
    try:
        pull_requests.update_one(pull.raw_data, {"$set": pull.raw_data}, upsert=True)
        
    except Exception as e:
        # if this repo doesn't exist, don't mine it 
        if e == 500 or e == 404:
            logger.info('GITHUB EXCEPTION: {0} for PULL {1}. PULL INACCESSIBLE, PASSING.'.format(e, pull.number))
            pass
        # TODO: Else, send the administrator an email to alert them of an error
    
# Helper method to find a specific repo's main api page json 
def find_repo_main_page(repo_name):
    # Use pygit to eliminate any problems with users not spelling the repo name
    # exactly as it is on the actual repo 
    try:
        pygit_repo = g.get_repo(repo_name)
        return repos.find_one({"full_name":pygit_repo.full_name})
    except Exception as e:
        return e


# Helper method to find and return a list of all pull request json files 
# belonging to a specific repo 
def find_all_pull_requests_from_a_specific_repo(repo_name):
    # Use pygit to eliminate any problems with users not spelling the repo name
    # exactly as it is on the actual repo 
    pygit_repo = g.get_repo(repo_name)

    # Obtain a list of all the pull requests matching the repo's full name 
    pulls = pull_requests.find({"url": {"$regex": pygit_repo.full_name}})

    return pulls

def count_all_pull_requests_from_a_specifc_repo(repo_name):
    pygit_repo = g.get_repo(repo_name)

    num_pulls = pull_requests.count_documents({"url": {"$regex": pygit_repo.full_name}})

    return num_pulls


# Method to retrieve all repos in the repo collection
def get_all_repos():
    return repos.find({})


# Method to retrieve every pull request in the pullRequest collection
def get_all_pull_requests():
    return pull_requests.find({})
     

# Method to delete all json files from every collection 
def delete_all_contents_from_every_collection():
    delete_all_repos_from_repo_collection()
    delete_all_pulls_from_pull_request_collection()
    delete_all_pull_requests_batches_from_batch_collection()
    return 

def delete_all_pull_requests_batches_from_batch_collection():
    pull_batches.delete_many({})

def delete_specific_repos_pull_request_batches(repo_name):
    pygit_repo = g.get_repo(repo_name)
    pull_batches.delete_many({"repo": {"$regex": pygit_repo.full_name.lower()}})

# Method to delete all jsons belonging to a specific repo from every collection 
def delete_all_contents_of_specific_repo_from_every_collection(repo_name):
    delete_specific_repo_from_repo_collection(repo_name)
    delete_specifc_repos_pull_requests(repo_name)
    delete_specific_repos_pull_request_batches(repo_name)
    return
    
