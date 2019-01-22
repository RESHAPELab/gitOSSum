#!/usr/bin/env python
# -*- coding: utf-8 -*-
# mining.py
# Created by Stephen White
# Date: 1/22/2019
# Purpose: This script will provide the necessary functionality to store json data
#          from GitHub's API into the MongoDB database of our choosing 

from pymongo import MongoClient
from github import Github


client = MongoClient('localhost', 27017)
db = client.backend_db
repos = db.repos
pull_requests = db.pullRequests
g = Github("Githubfake01", "5RNsya*z#&aA", per_page=100)
repo_name = "google/gumbo-parser"
pygit_repo = g.get_repo(repo_name)

# To find a specific repo: db.pullRequests.find({"url":{$regex: repo}})


# Method to download a repo's main json and place it in the 
# db.repos collection for future parsing 
def mine_repo_page(repo_name):
    # Use pygit to eliminate any problems with users not spelling the repo name
    # exactly as it is on the actual repo 
    pygit_repo = g.get_repo(repo_name)
    repos.update(pygit_repo.raw_data, pygit_repo.raw_data, upsert=True)
    return 


# Method to download all pull requests of a given repo and 
# put them within the db.pullRequests collection 
def mine_pulls_from_repo(repo_name):
    # Use pygit to retrieve the repo itself 
    pygit_repo = g.get_repo(repo_name)

    # Retrieve all pull request numbers associated with this repo 
    pulls = pygit_repo.get_pulls('all')

    for pull in pulls:
        # Overwrite already existing instances of jsons 
        pull_requests.update(pull.raw_data, pull.raw_data, upsert=True)


# Helper method to find a specific repo's main api page json 
def find_repo_main_page(repo_name):
    # Use pygit to eliminate any problems with users not spelling the repo name
    # exactly as it is on the actual repo 
    pygit_repo = g.get_repo(repo_name)
    print(repos.find_one({"full_name":pygit_repo.full_name}))
    return repos.find_one({"full_name":pygit_repo.full_name})


# Helper method to find and return all pull request json files 
# belonging to a specific repo 
def find_all_repo_pulls(repo_name):
    # Use pygit to eliminate any problems with users not spelling the repo name
    # exactly as it is on the actual repo 
    pygit_repo = g.get_repo(repo_name)

    # Obtain a list of all the pull requests matching the repo's full name 
    pulls = pull_requests.find({"url": {"$regex": pygit_repo.full_name}})
    for pull in pulls:
        print(pull)
    return pulls


# mine_repo_page(repo_name)
find_repo_main_page(repo_name)
# mine_pulls_from_repo(repo_name)
# find_all_repo_pulls(repo_name)