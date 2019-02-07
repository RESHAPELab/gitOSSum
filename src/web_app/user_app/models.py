from django.db import models
from pymongo import MongoClient

class OAuthToken(models.Model):
    oauth_token             = models.CharField(max_length=240, null=False, blank=False)
    owner                   = models.CharField(max_length=240, null=False, blank=False)

class MiningRequest(models.Model):
    repo_name               = models.CharField(max_length=240, null=False, blank=False)
    requested_by            = models.CharField(max_length=240, null=False, blank=False)
    email                   = models.EmailField(null=False, blank=False)
    send_email              = models.BooleanField()
    timestamp               = models.DateTimeField(auto_now_add=True)
    updated                 = models.DateTimeField(auto_now=True)


    def __str__(self):
        return f"{self.repo_name}, {self.email}, {self.timestamp}, {self.updated}"

class BlacklistedMiningRequest(models.Model):
    repo_name               = models.CharField(max_length=240, null=False, blank=False)
    requested_by            = models.CharField(max_length=240, null=False, blank=False)
    timestamp               = models.DateTimeField(auto_now_add=True)
    updated                 = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.repo_name}, {self.timestamp}, {self.updated}"

class MinedRepo(models.Model):
    repo_name                    = models.CharField(max_length=240, null=False, blank=False)
    requested_by                 = models.CharField(max_length=240, null=False, blank=False)
    #num_pulls                    = models.IntegerField(min_value=0)
    #num_closed_merged_pulls      = models.IntegerField(min_value=0)
    #num_closed_unmerged_pulls    = models.IntegerField(min_value=0)
    #num_open_pulls               = models.IntegerField(min_value=0)
    timestamp                    = models.DateTimeField(auto_now_add=True)
    updated                      = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.repo_name}, {self.timestamp}, {self.updated}"