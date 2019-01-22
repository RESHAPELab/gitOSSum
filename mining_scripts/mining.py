#!/usr/bin/env python
# -*- coding: utf-8 -*-
# mining.py
# Created by Stephen White
# Date: 1/22/2019
# Purpose: This script will provide the necessary functionality to store json data
#          from GitHub's API into the MongoDB database of our choosing 

from pymongo import MongoClient
from github import Github
import json


client = MongoClient('localhost', 27017)
db = client.backend_db
pull_requests = db.pullRequests
g = Github("Githubfake01", "5RNsya*z#&aA")
repo = g.get_repo("Swhite9478/Github-Mining-Tool")

# To find a specific repo: db.pullRequests.find({"url":{$regex: repo}})

# Method to download all pull requests of a given repo and 
# put them within the db.pullRequests collection 
def mine_pulls_from_repo(repo):

    # Retrieve all pull request numbers associated with this repo 
    pulls = repo.get_pulls(state='all', sort='created', base='master')

    raw_json = repo.get_pull(pulls[0].number).raw_data

    pull_requests.update(raw_json, raw_json, upsert=True)


# Helper method to find and return all pull request json files 
# belonging to a specific repo 
def find_all_repo_pulls(repo):
    print(repo)
    pulls = pull_requests.find({"url": {"$regex": repo}})
    for pull in pulls:
        print(pull)
    return pulls
    
# mine_pulls_from_repo(repo)

find_all_repo_pulls(repo.full_name)