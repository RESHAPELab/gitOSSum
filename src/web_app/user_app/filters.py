
from operator import and_
from functools import reduce
from mining_scripts.mining import *
import re

# Method to return a list of dictionaries containing each language
# we have stored in mongo, and the corresponding count for each language
def get_language_list_from_mongo():
    return [
        item['_id'] for item in repos.aggregate([{"$match":{"language":{"$ne":None}}},
        {"$group":{"_id":"$language", "count":{"$sum":1}}}])
    ]


# Helper method to return a flat list of all repos whose language
# is within languages_list 
def get_repos_list_by_language_filter(languages_list):
    repos_list = []
    for language in languages_list:
        repos_list.append([item['full_name'] for item in repos.find({"language":language}, 
                          {'_id':0,"full_name":1})])
    return set([item.lower() for sublist in repos_list for item in sublist])


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
     
