
from operator import and_
from functools import reduce
from mining_scripts.mining import *
from .models import *
import re
import os



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


# Function to be used in tests.py to ensure that we are not accessing the production database
def mongo_filter_test_init():
    global db 
    global repos 
    global pull_requests
    global pull_batches 
    db = client.test_db
    repos = db.repos
    pull_requests = db.pullRequests
    pull_batches = db.pullBatches

# Method to return a list of dictionaries containing each language
# we have stored in mongo, and the corresponding count for each language
def get_language_list_from_mongo():
    # Get a sorted list of all the languages in the form of a tuple (lanugage, count)
    return sorted([
        (item['_id'], item['count']) for item in repos.aggregate([{"$match":{"language":{"$ne":None}}},
        {"$group":{"_id":"$language", "count":{"$sum":1}}}])
    ])


# Helper method to return a flat list of all repos whose language
# is within languages_list 
def get_repos_list_by_language_filter(languages_list):
    repos_list = []
    for language in languages_list:
        repos_list.append([item['full_name'] for item in repos.find({"language":language}, 
                          {'_id':0,"full_name":1})])
    default_set = set([item.lower() for sublist in repos_list for item in sublist])
    set_to_be_returned = set()
    mined_repos = list(MinedRepo.objects.values_list('repo_name', flat=True)) # Obtain all the mining requests
    for repo in default_set:
        if repo in mined_repos:
            set_to_be_returned.add(repo)
    return set_to_be_returned


# Helper method to obtain a list of repos whose number of pull 
# requests is less than the upper_bound specified
def get_repos_list_by_pulls_less_than_filter(upper_bound):
    return set([
        item['_id'].lower() for item in pull_requests.aggregate([{'$group':{'_id':'$base.repo.full_name', 
        'count':{'$sum':1}}}, {'$match':{'count':{'$lt':upper_bound}}}])
    ])


# Helper method to obtain a list of repos whose number of pull 
# requests is greater than the lower_bound specified
def get_repos_list_by_pulls_greater_than_filter(lower_bound):
    return set([
        item['_id'].lower() for item in pull_requests.aggregate([{'$group':{'_id':'$base.repo.full_name', 
        'count':{'$sum':1}}}, {'$match':{'count':{'$gt':lower_bound}}}])
    ])


# Helper method to obtain a list of repos whose number of pull 
# requests is is greater than the lower_bound specified and
# less than the upper_bound specified
def get_repos_list_by_pulls_bounded_filter(lower_bound, upper_bound):
    return set([
        item['_id'].lower() for item in pull_requests.aggregate([{'$group':{'_id':'$base.repo.full_name', 
        'count':{'$sum':1}}}, {'$match':{'count':{'$gt':lower_bound, '$lt':upper_bound}}}])
    ])


def get_repos_list_has_wiki_filter(boolean):
    return set([
        item['_id'].lower() for item in repos.aggregate([{'$match':{"has_wiki":boolean}}, 
        {'$group':{'_id':"$full_name"}}])
    ])


def get_repos_search_query_filter(search_query):
    return set([
        item['full_name'].lower() for item in repos.find({'full_name': re.compile(search_query, re.IGNORECASE)},
        {"_id":0, "full_name":1})
    ])


def get_filtered_repos_list(filtered_sets):
    return list(reduce((lambda x,y: x&y), filtered_sets))
     
