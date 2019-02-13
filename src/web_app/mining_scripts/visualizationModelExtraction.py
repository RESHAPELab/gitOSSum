from pymongo import MongoClient # Import pymongo for interacting with MongoDB
from github import Github # Import PyGithub for mining data
import datetime



client = MongoClient('localhost', 27017) # Where are we connecting
db = client.backend_db # The specific mongo database we are working with 
repos = db.repos # collection for storing all of a repo's main api json information 
pull_requests = db.pullRequests # collection for storing all pull requests for all repos


# Takes in the name of a repo to query, and returns a dict containing num_pulls, 
# num_closed_merged_pulls, num_closed_unmerged_pulls, num_open_pulls, created_at_list, 
# closed_at_list, merged_at_list, and num_newcomer_labels.
def extract_pull_request_model_data(pygit_repo):
    return {
        "num_pulls": pull_requests.count_documents({"url": {"$regex": pygit_repo.full_name}}),

        "num_closed_merged_pulls":pull_requests.count_documents({"url": {"$regex": pygit_repo.full_name}, 
                                                                "state":"closed", "merged_at": {"$ne":None}}),

        "num_closed_unmerged_pulls":pull_requests.count_documents({"url": {"$regex": pygit_repo.full_name}, 
                                                                "state":"closed", "merged_at":None}),

        "num_open_pulls":pull_requests.count_documents({"url": {"$regex": pygit_repo.full_name}, 
                                                                "state":"open", "merged_at":None}),

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
