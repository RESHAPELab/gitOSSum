#!/usr/bin/env python
# -*- coding: utf-8 -*-
# mining.py
# Created by Stephen White
# Date: 1/22/2019
# Purpose: This script will provide the necessary functionality to store json data
#          from GitHub's API into the MongoDB database of our choosing 

from pymongo import MongoClient # Import pymongo for interacting with MongoDB
from github import Github # Import PyGithub for mining data
from email.message import EmailMessage # Import the email modules we'll need
import smtplib # Import smtplib for the actual sending function
import config 

client = MongoClient('localhost', 27017) # Where are we connecting

db = client.backend_db # The specific mongo database we are working with 

repos = db.repos # collection for storing all of a repo's main api json information 

pull_requests = db.pullRequests # collection for storing all pull requests for all repos 

g = Github(config.GITHUB_USERNAME, config.GITHUB_PASSWORD, per_page=100) # authorization for the github API 


def send_confirmation_email(repo_name, email_address):
    try:
        server = smtplib.SMTP('smtp.gmail.com:587')
        server.ehlo()
        server.starttls()
        server.login(config.EMAIL_ADDRESS, config.PASSWORD)
        subj = 'Git-OSS-um %s Mining Request Complete!' % repo_name
        msg = (
        '''Hello, this is an automated message letting you know that your ''' + \
        '''request to mine %s has been completed! Thank you for using our service!''' % repo_name + \
        '''\n\nUntil next time,\n\nGit-OSS-um Team <3''')
        message = "Subject: {}\n\n{}".format(subj, msg)
        server.sendmail(config.EMAIL_ADDRESS, email_address, message)
        return True 

    except Exception as e:
        return False 

    finally:
        server.quit() 



# Wrapper function that will perform all mining steps necessary when
# provided with the repository name
def mine_and_store_all_repo_data(repo_name, **kwargs):  
    # Use pygit to eliminate any problems with users not spelling the repo name
    # exactly as it is on the actual repo 
    pygit_repo = g.get_repo(repo_name)

    # mine and store the main page josn
    mine_repo_page(pygit_repo)

    # mine and store all pulls for this repo 
    mine_pulls_from_repo(pygit_repo)

    # send any emails as necessary
    if "email" in kwargs:
        # Iterate over a list of emails if thats what was provided 
        if type(kwargs["email"]) is list:
            for email_recipient in kwargs["email"]:
                send_confirmation_email(repo_name, email_recipient)
        
        # Otherwise its just one single email
        else:
            send_confirmation_email(repo_name, kwargs["email"])

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


# Method to download all pull requests of a given repo and 
# put them within the db.pullRequests collection 
def mine_pulls_from_repo(pygit_repo):
    # Retrieve all pull request numbers associated with this repo 
    pulls = pygit_repo.get_pulls('all')

    for pull in pulls:
        # Overwrite already existing instances of jsons 
        pull_requests.update_one(pull.raw_data, {"$set": pull.raw_data}, upsert=True)

    return 


# Helper method to find a specific repo's main api page json 
def find_repo_main_page(repo_name):
    # Use pygit to eliminate any problems with users not spelling the repo name
    # exactly as it is on the actual repo 
    pygit_repo = g.get_repo(repo_name)
    
    return repos.find_one({"full_name":pygit_repo.full_name})


# Helper method to find and return a list of all pull request json files 
# belonging to a specific repo 
def find_all_pull_requests_from_a_specific_repo(repo_name):
    # Use pygit to eliminate any problems with users not spelling the repo name
    # exactly as it is on the actual repo 
    pygit_repo = g.get_repo(repo_name)

    # Obtain a list of all the pull requests matching the repo's full name 
    pulls = pull_requests.find({"url": {"$regex": pygit_repo.full_name}})

    return pulls


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
    return 


# Method to delete all jsons belonging to a specific repo from every collection 
def delete_all_contents_of_specific_repo_from_every_collection(repo_name):
    delete_specific_repo_from_repo_collection(repo_name)
    delete_specifc_repos_pull_requests(repo_name)
    return

