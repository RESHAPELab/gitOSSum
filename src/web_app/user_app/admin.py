from django.contrib import admin


# Register your models here.
from .models import RestaurantLocation, MiningRequest
from mining_scripts.mining import *


def approve_mining_requests(modeladmin, request, queryset):
    for obj in queryset:
        print("\n\nREPO THAT WILL BE MINED: ", obj.repo_name)
        print("EMAIL: ", obj.email)
        mine_and_store_all_repo_data(obj.repo_name, email=obj.email)
        MiningRequest.objects.get(repo_name=obj.repo_name).delete()

    return

approve_mining_requests.short_description = "Approve selected mining requests"

class MiningRequestAdmin(admin.ModelAdmin):
    list_display = ['repo_name', "email", "timestamp"]
    ordering = ['timestamp']
    actions = [approve_mining_requests]


admin.site.register(RestaurantLocation)
admin.site.register(MiningRequest, MiningRequestAdmin)