from django.contrib import admin
from django.contrib.admin.actions import delete_selected as delete_selected_
from django.core.exceptions import PermissionDenied


# Register your models here.
from .models import MiningRequest, BlacklistedMiningRequest, MinedRepo, OAuthToken
from mining_scripts.mining import *
from multiprocessing import Pool

# Admin functionality for approving mining requests
def approve_mining_requests(modeladmin, request, queryset):
    pool = Pool()

    # Iterate over all of the items the admin has checked
    for obj in queryset:
        # Mine that repo, and store it in mongoDB
        repo_name = obj.repo_name
        user_email = obj.email
        kw_args = {'email': user_email}

        pool.apply_async(mine_and_store_all_repo_data, args=(repo_name, user_email,))
       

        # Add this repo to the mined repos table
        MinedRepo.objects.create(
            repo_name=obj.repo_name)
            
        # Delete the request from the MiningRequest Database
        MiningRequest.objects.get(repo_name=obj.repo_name).delete()


# A short description for this function
approve_mining_requests.short_description = "Approve selected mining requests"


# Admin functionality for blacklisting a repository
def black_list_requests(modeladmin, request, queryset):
    # Iterate over all of the items the admin has checked
    for obj in queryset:
        # Blacklist the repo
        BlacklistedMiningRequest.objects.create(
            repo_name=obj.repo_name)
        # Delete the request from the MiningRequest database
        MiningRequest.objects.get(repo_name=obj.repo_name).delete()

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
            obj.delete()

    else:

        return delete_selected_(modeladmin, request, queryset)

delete_selected.short_description = "Delete selected repos from database"

class MiningRequestAdmin(admin.ModelAdmin):
    list_display = ['repo_name', "email", "timestamp"]
    ordering = ['timestamp']
    actions = [approve_mining_requests, black_list_requests]

class BlacklistedMiningRequestAdmin(admin.ModelAdmin):
    list_display = ['repo_name', "timestamp"]
    ordering = ['timestamp']

class MinedRepoAdmin(admin.ModelAdmin):
    list_display = ['repo_name', "timestamp"]
    ordering = ['timestamp']
    actions=[delete_selected]

class OAuthTokenAdmin(admin.ModelAdmin):
    list_display = ["oauth_token", "owner"]
    ordering = ["owner"]

admin.site.register(MiningRequest, MiningRequestAdmin)
admin.site.register(BlacklistedMiningRequest, BlacklistedMiningRequestAdmin)
admin.site.register(MinedRepo, MinedRepoAdmin)
admin.site.register(OAuthToken, OAuthTokenAdmin)