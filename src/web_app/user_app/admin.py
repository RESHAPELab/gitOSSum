from django.contrib import admin


# Register your models here.
from .models import MiningRequest, BlacklistedMiningRequest, MinedRepo
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

class MiningRequestAdmin(admin.ModelAdmin):
    list_display = ['repo_name', "email", "timestamp"]
    ordering = ['timestamp']
    actions = [approve_mining_requests, black_list_requests]



admin.site.register(MiningRequest, MiningRequestAdmin)
admin.site.register(BlacklistedMiningRequest)
admin.site.register(MinedRepo)