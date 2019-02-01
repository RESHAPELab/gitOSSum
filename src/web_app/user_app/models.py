from django.db import models
from pymongo import MongoClient

class MiningRequest(models.Model):
    repo_name               = models.CharField(max_length=240, null=False, blank=False)
    email                   = models.EmailField(null=False, blank=True)
    timestamp               = models.DateTimeField(auto_now_add=True)
    updated                 = models.DateTimeField(auto_now=True)


    def __str__(self):
        return f"{self.repo_name}, {self.email}, {self.timestamp}, {self.updated}"

class BlacklistedMiningRequest(models.Model):
    repo_name               = models.CharField(max_length=240, null=False, blank=False)
    timestamp               = models.DateTimeField(auto_now_add=True)
    updated                 = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.repo_name}, {self.timestamp}, {self.updated}"

class MinedRepo(models.Model):
    repo_name               = models.CharField(max_length=240, null=False, blank=False)
    timestamp               = models.DateTimeField(auto_now_add=True)
    updated                 = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.repo_name}, {self.timestamp}, {self.updated}"