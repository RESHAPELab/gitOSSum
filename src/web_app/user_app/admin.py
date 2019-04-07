from django.contrib import admin
from django.contrib.admin.actions import delete_selected as delete_selected_
from django.core.exceptions import PermissionDenied
from django.template.loader import get_template
from django.shortcuts import redirect


# Register your models here.
from .models import MiningRequest, QueuedMiningRequest, BlacklistedMiningRequest, MinedRepo
from mining_scripts.send_email import *
from mining_scripts.mining import *
from mining_scripts.batchify import *
from multiprocessing import Pool
from threading import Thread
from user_app.tasks import mine_pull_request_batch_asynchronously, initialize_batch_json #, mine_data_asynchronously
from django.db import transaction

from celery.result import AsyncResult
from celery.task.control import revoke

g = Github(GITHUB_TOKEN, per_page=100) # authorization for the github API 

logger = get_task_logger(__name__)


class CeleryTaskFailedError(Exception):
    pass


def all_tasks_completed(task_list):
    total_tasks = len(task_list)
    complete_tasks = 0
    for task in task_list:
        if AsyncResult(task.task_id).successful():
            complete_tasks += 1
        elif AsyncResult(task.task_id).failed():
            raise CeleryTaskFailedError("Celery Task Failed!!!")
    if complete_tasks == total_tasks:
        return True
    else:
        return False 

def start_new_thread(function):
    def decorator(*args, **kwargs):
        t = Thread(target = function, args=args, kwargs=kwargs)
        t.daemon = True
        t.start()
    return decorator


def remove_from_fieldsets(fieldsets, fields):
    for fieldset in fieldsets:
        for field in fields:
            if field in fieldset[1]['fields']:
                new_fields = []
                for new_field in fieldset[1]['fields']:
                    if not new_field in fields:
                        new_fields.append(new_field)
                        
                fieldset[1]['fields'] = tuple(new_fields)
                break



# Admin functionality for approving mining requests
def approve_mining_requests(modeladmin, request, queryset):

    # Iterate over all of the items the admin has checked
    for obj in queryset:
        # Mine that repo, store it in mongoDB, and create an SQL representation of it
        repo_name = obj.repo_name
        username = obj.requested_by
        user_email = ""
        if obj.send_email == True:
            user_email = obj.email

        # Move this repo into the Queue
        queued_request = QueuedMiningRequest(repo_name=repo_name, requested_by=username,
                requested_timestamp=getattr(MiningRequest.objects.get(repo_name=repo_name), "timestamp"),
                send_email=getattr(MiningRequest.objects.get(repo_name=repo_name), "send_email")
            )
        
        queued_request.save()

        # # Delete this repo from the Requests
        MiningRequest.objects.get(repo_name=repo_name).delete()

        # # Send the User an email as appropriate, letting them know 
        # # we have started mining their data
        send_mining_initialized_email(obj.repo_name, username, user_email) 
        
        batch_data = batchify(repo_name)
    
        # Else, move on to mining the data 
        initialize_batch_json(batch_data, repo_name)

        for job in range(len(batch_data)):
            mine_pull_request_batch_asynchronously.delay(repo_name, job)
            

        # mine_data_asynchronously.delay(repo_name, username, user_email, queued_request.id)    

# A short description for this function
approve_mining_requests.short_description = "Approve selected mining requests"


def delete_mining_requests(modeladmin, request, queryset):
    for obj in queryset:                
        if obj.send_email == True:
            repo_name = obj.repo_name
            username = obj.requested_by
            user_email = obj.email
            send_repository_denied_email(repo_name, username, user_email)

        obj.delete()

delete_mining_requests.short_description = "Deny selected mining requests"

# Admin functionality for blacklisting a repository
def black_list_requests(modeladmin, request, queryset):
    # Iterate over all of the items the admin has checked
    for obj in queryset:
        # Blacklist the repo
        BlacklistedMiningRequest.objects.create(
            repo_name=obj.repo_name,
            requested_by=obj.requested_by
        )

        if obj.send_email == True:
            repo_name = obj.repo_name
            username = obj.requested_by
            user_email = obj.email
            send_repository_blacklist_email(repo_name, username, user_email)

        # Delete the request from the MiningRequest database
        MiningRequest.objects.get(repo_name=obj.repo_name).delete()

        


# A short description for this function
black_list_requests.short_description = "Blacklist selected mining requests"


# Function for deleting repositories from the MongoDB database
def delete_selected(modeladmin, request, queryset):
    # pool = Pool()

    if not modeladmin.has_delete_permission(request):

        raise PermissionDenied

    if request.POST.get('post'):

        for obj in queryset:
            delete_all_contents_of_specific_repo_from_every_collection(obj.repo_name)
            
            #pool.apply_async(delete_all_contents_of_specific_repo_from_every_collection, args=(obj.repo_name,))
            

            obj.delete()
            

    else:

        return delete_selected_(modeladmin, request, queryset)

delete_selected.short_description = "Delete selected repos from database"


# Design the admin panel for each database model 
class MiningRequestAdmin(admin.ModelAdmin):
    list_display = ['repo_name', "requested_by", "email", "send_email", "timestamp"]
    ordering = ['timestamp']
    actions = [approve_mining_requests, delete_mining_requests, black_list_requests]
    
    def get_actions(self, request):
        actions = super(MiningRequestAdmin, self).get_actions(request)
        del actions['delete_selected']
        return actions


class QueuedMiningRequestAdmin(admin.ModelAdmin):
    list_display = ['repo_name', "requested_by", "timestamp", "requested_timestamp", "send_email"]
    ordering = ['timestamp']

    actions=[delete_selected]

class BlacklistedMiningRequestAdmin(admin.ModelAdmin):
    list_display = ['repo_name', "requested_by", "timestamp"]
    ordering = ['timestamp']

class MinedRepoAdmin(admin.ModelAdmin):
    list_display = ['repo_name', "requested_by", "completed_timestamp", "accepted_timestamp", "requested_timestamp", "send_email"]
    ordering = ['completed_timestamp']
    
    actions=[delete_selected]

    def get_fieldsets(self, request, obj=None):
        fieldsets = super(MinedRepoAdmin, self).get_fieldsets(request, obj)
        remove_from_fieldsets(fieldsets, ('num_pulls', 'num_closed_merged_pulls', 
                                        'num_open_pulls', 'num_closed_unmerged_pulls', 
                                        'created_at_list', 'closed_at_list', 
                                        'merged_at_list', 'num_newcomer_labels',
                                        'bar_chart_html', 'pull_line_chart_html',
                                        'contribution_line_chart_html',))
        return fieldsets


# Register all of the admin panels to their respective models 
admin.site.register(MiningRequest, MiningRequestAdmin)
admin.site.register(QueuedMiningRequest, QueuedMiningRequestAdmin)
admin.site.register(BlacklistedMiningRequest, BlacklistedMiningRequestAdmin)
admin.site.register(MinedRepo, MinedRepoAdmin)
