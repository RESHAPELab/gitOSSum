from __future__ import absolute_import

from web_app.celery import app
from celery.utils.log import get_task_logger
from mining_scripts.mining import *
from mining_scripts.send_email import *
from github import GithubException
from django.db import transaction
from mining_scripts.batchify import *
import time 
from user_app.models import QueuedMiningRequest, MinedRepo, OAuthToken

# Handle parallel processing not knowing about django apps
try:
    from django.apps import apps
    apps.check_apps_ready()
except AppRegistryNotReady:
    import django
    django.setup()

g = Github(GITHUB_TOKEN, per_page=100) # authorization for the github API 


logger = get_task_logger(__name__)

# When the admin approves, go call the mining script asynchronously 
@app.task(name='tasks.mine_data_asynchronously', hard_time_limit=60*60*10)
def mine_data_asynchronously(repo_name, username, user_email, queued_request):
    # Update the log to show we started 
    logger.info('Starting Mining Job with repo_name="{0}", username="{1}", and user_email="{2}".'.format(repo_name, username, user_email))
    
    logger.info('Retrieving the pygit_repo from github for {0}'.format(repo_name))
    pygit_repo = g.get_repo(repo_name)
    logger.info('Successfully retrieved pygit_repo from github for {0}'.format(repo_name))


    # mine and store the main page josn
    logger.info('Mining the  the landing page JSON from github for {0}'.format(repo_name))
    mine_repo_page(pygit_repo)
    logger.info('Successfully mined the  the landing page JSON from github for {0}'.format(repo_name))

    # Go mine the data and log whats happening along the way
    # mine_and_store_all_repo_data(repo_name, username, user_email, queued_request)

    logger.info('Starting to BATCH JOBS for repo_name="{0}", username="{1}", and user_email="{2}".'.format(repo_name, username, user_email))
    batch_data = batchify(repo_name)
    logger.info('Successfully BATCHED JOBS for repo_name="{0}", username="{1}", and user_email="{2}".'.format(repo_name, username, user_email))

    logger.info(f'TOTAL OF {len(batch_data)} BATCH JOBS OF SIZE {len(batch_data[0])} for repo_name="{repo_name}"')
    
    logger.info(f'Kicking off jobs for repo_name="{repo_name}"')
    for job in range(len(batch_data)):
        mine_pull_request_batch_asynchronously.s(repo_name, job, username, user_email, queued_request).delay()

 
    # Log that this repo has been finished 
    # logger.info('Finished Mining Job with repo_name="{0}", username="{1}", and user_email="{2}".'.format(repo_name, username, user_email))
    logger.info(f'PARENT PROCESS FINISHED FOR {repo_name}. WAITING ON TASKS.')
    return


# @app.task(bind=True, default_retry_delay=10, name='tasks.mine_pull_request_asynchronously')
# def mine_pull_request_asynchronously(self, repo, pygit_pull):
#     try:
#         pull = g.get_repo(repo).get_pull(pygit_pull)
#         # logger.info('Placing "api.github.com/{0}/pulls/{1}" into MongoDB pullRequests collection.'.format(repo, pull.number))
#         pull_requests.update_one(pull.raw_data, {"$set": pull.raw_data}, upsert=True)
#         # logger.info('Successfully placed "api.github.com/repos/{0}/pulls/{1}" into MongoDB pullRequests collection.'.format(repo, pull.number))
#         return True
        
#     except GithubException as e:
#         logger.info('GITHUB EXCEPTION: {0} for "api.github.com/repos/{0}/pulls/{1}". RETRYING'.format(e, repo, pull.number))
#         self.retry(exc=e, countdown=exponential_backoff(self))
      

# def exponential_backoff(task_self):
#     minutes = task_self.default_retry_delay / 60
#     rand = random.uniform(minutes, minutes * 1.3)
#     return int(rand ** task_self.request.retries) * 60


@app.task(name='tasks.mine_pull_request_batch_asynchronously', hard_time_limit=60*60*3)
def mine_pull_request_batch_asynchronously(repo_name, job, username, user_email, queued_request):
    pulls_batch = get_batch_number(repo_name, job)
    
    if pulls_batch["is_last_batch"] == False: # If it is a normal batch, just go mine stuff
        mine_pulls_batch(pulls_batch["data"])
    
    else:
        mine_pulls_batch(pulls_batch["data"]) # If it is our last batch, we have more to do 

        # We want to make sure that everything gets finished 
        while count_all_pull_requests_from_a_specifc_repo(repo_name) != g.get_repo(repo_name).get_pulls('all').totalCount:
            time.sleep(10)


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
            accepted_timestamp=getattr(QueuedMiningRequest.objects.get(pk=queued_request), "timestamp"),
            requested_timestamp=getattr(QueuedMiningRequest.objects.get(pk=queued_request), "requested_timestamp")
        ) 

        mined_repo.save()

        logger.info('Successfully created MinedRepo database object for {0}'.format(repo_name))

        # Delete the request from the MiningRequest Database
        logger.info('Deleting QueuedMiningRequest database object for {0}'.format(repo_name))
        QueuedMiningRequest.objects.get(pk=queued_request).delete()
        logger.info('Successfully deleted QueuedMiningRequest database object for {0}'.format(repo_name))

        # send any emails as necessary
        logger.info('Sending email confirmation to "{0}" in regard to {1}'.format(user_email, repo_name))
        send_confirmation_email(repo_name, username, user_email)
        logger.info('Successfully sent email confirmation to "{0}" in regard to {1}'.format(user_email, repo_name))

    return True
