from django.contrib import admin
from django.contrib.admin.actions import delete_selected as delete_selected_
from django.core.exceptions import PermissionDenied
from django.template.loader import get_template



# Register your models here.
from .models import MiningRequest, QueuedMiningRequest, BlacklistedMiningRequest, MinedRepo, OAuthToken
from mining_scripts.mining import *
from mining_scripts.send_email import *
from multiprocessing import Pool

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
    pool = Pool()

    # Iterate over all of the items the admin has checked
    for obj in queryset:
        # Mine that repo, store it in mongoDB, and create an SQL representation of it
        repo_name = obj.repo_name
        username = obj.requested_by
        user_email = ""
        if obj.send_email == True:
            user_email = obj.email

        # Move this repo into the Queue
        QueuedMiningRequest.objects.create(repo_name=repo_name,
                                           requested_by=username
                                          )

        # Delete this repo from the Requests
        MiningRequest.objects.get(repo_name=repo_name).delete()
            
        # Send the User an email as appropriate, letting them know 
        # we have started mining their data
        send_mining_initialized_email(obj.repo_name, username, user_email)

        # Fork a process and mine their data
        pool.apply_async(mine_and_store_all_repo_data, [repo_name, username, user_email]) 


# A short description for this function
approve_mining_requests.short_description = "Approve selected mining requests"


# Admin functionality for blacklisting a repository
def black_list_requests(modeladmin, request, queryset):
    # Iterate over all of the items the admin has checked
    for obj in queryset:
        # Blacklist the repo
        BlacklistedMiningRequest.objects.create(
            repo_name=obj.repo_name,
            requested_by=obj.requested_by
        )
        # Delete the request from the MiningRequest database
        MiningRequest.objects.get(repo_name=obj.repo_name).delete()

        # if obj.send_email == True:
        #     send_repository_blacklist_email(obj.repo_name, obj.email)


# A short description for this function
black_list_requests.short_description = "Blacklist selected requests"


# Function for deleting repositories from the MongoDB database
def delete_selected(modeladmin, request, queryset):
    pool = Pool()

    if not modeladmin.has_delete_permission(request):

        raise PermissionDenied

    if request.POST.get('post'):

        for obj in queryset:
            pool.apply_async(delete_all_contents_of_specific_repo_from_every_collection, args=(obj.repo_name,))
            # if obj.send_email == True:
            #     send_repository_denied_email(obj.repo_name, obj.email)
            obj.delete()
            

    else:

        return delete_selected_(modeladmin, request, queryset)

delete_selected.short_description = "Delete selected repos from database"


# Design the admin panel for each database model 
class MiningRequestAdmin(admin.ModelAdmin):
    list_display = ['repo_name', "requested_by", "email", "send_email", "timestamp"]
    ordering = ['timestamp']
    actions = [approve_mining_requests, black_list_requests]

class QueuedMiningRequestAdmin(admin.ModelAdmin):
    list_display = ['repo_name', "requested_by", "timestamp"]
    ordering = ['timestamp']

class BlacklistedMiningRequestAdmin(admin.ModelAdmin):
    list_display = ['repo_name', "requested_by", "timestamp"]
    ordering = ['timestamp']

class MinedRepoAdmin(admin.ModelAdmin):
    list_display = ['repo_name', "requested_by", "timestamp"]
    ordering = ['timestamp']
    
    actions=[delete_selected]

    def get_fieldsets(self, request, obj=None):
        fieldsets = super(MinedRepoAdmin, self).get_fieldsets(request, obj)
        remove_from_fieldsets(fieldsets, ('num_pulls', 'num_closed_merged_pulls', 
                                        'num_open_pulls', 'num_closed_unmerged_pulls', 
                                        'created_at_list', 'closed_at_list', 
                                        'merged_at_list', 'num_newcomer_labels',
                                        'bar_chart_html', 'pull_line_chart_html',))
        return fieldsets

class OAuthTokenAdmin(admin.ModelAdmin):
    list_display = ["oauth_token", "owner"]
    ordering = ["owner"]


# Register all of the admin panels to their respective models 
admin.site.register(MiningRequest, MiningRequestAdmin)
admin.site.register(QueuedMiningRequest, QueuedMiningRequestAdmin)
admin.site.register(BlacklistedMiningRequest, BlacklistedMiningRequestAdmin)
admin.site.register(MinedRepo, MinedRepoAdmin)
admin.site.register(OAuthToken, OAuthTokenAdmin)