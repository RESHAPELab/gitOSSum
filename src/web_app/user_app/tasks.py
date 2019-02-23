from __future__ import absolute_import

from web_app.celery import app
from celery.utils.log import get_task_logger
from mining_scripts.mining import *
from github import GithubException
from django.db import transaction


logger = get_task_logger(__name__)

# When the admin approves, go call the mining script asynchronously 
@app.task(name='tasks.mine_data_asynchronously')
def mine_data_asynchronously(repo_name, username, user_email, queued_request):
    # Update the log to show we started 
    logger.info('Starting Mining Job with repo_name="{0}", username="{1}", and user_email="{2}".'.format(repo_name, username, user_email))
    
    # Go mine the data and log whats happening along the way
    mine_and_store_all_repo_data(repo_name, username, user_email, queued_request)

    # Log that this repo has been finished 
    logger.info('Finished Mining Job with repo_name="{0}", username="{1}", and user_email="{2}".'.format(repo_name, username, user_email))
    return


@app.task(bind=True, default_retry_delay=10, name='tasks.mine_pull_request_asynchronously')
def mine_pull_request_asynchronously(self, repo, pygit_pull):
    try:
        pull = g.get_repo(repo).get_pull(pygit_pull)
        logger.info('Placing "api.github.com/{0}/pulls/{1}" into MongoDB pullRequests collection.'.format(repo, pull.number))
        pull_requests.update_one(pull.raw_data, {"$set": pull.raw_data}, upsert=True)
        logger.info('Successfully placed "api.github.com/repos/{0}/pulls/{1}" into MongoDB pullRequests collection.'.format(repo, pull.number))
        return True
        
    except GithubException as e:
        logger.info('GITHUB EXCEPTION: {0} for "api.github.com/repos/{0}/pulls/{1}". RETRYING'.format(e, repo, pull.number))
        self.retry(exc=e, countdown=exponential_backoff(self))
      

def exponential_backoff(task_self):
    minutes = task_self.default_retry_delay / 60
    rand = random.uniform(minutes, minutes * 1.3)
    return int(rand ** task_self.request.retries) * 60