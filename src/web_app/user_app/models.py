from django.db import models
from pymongo import MongoClient

class RestaurantLocation(models.Model):
    name         = models.CharField(max_length=120)
    location     = models.CharField(max_length=120, null=True, blank=True)
    category     = models.CharField(max_length=120, null=True, blank=False)
    timestamp    = models.DateTimeField(auto_now_add=True)
    updated      = models.DateTimeField(auto_now=True)

class MiningRequest(models.Model):
    repo_name               = models.CharField(max_length=120, null=False, blank=False)
    pull_request_number     = models.IntegerField(null=False, blank=False)
    timestamp               = models.DateTimeField(auto_now_add=True)
    updated                 = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('repo_name', 'pull_request_number',)

    def __str__(self):
        return f"{self.repo_name}, {self.pull_request_number}, {self.timestamp}, {self.updated}"

class AdminApproval(models.Model):
    approve_for_mining = models.BooleanField()
