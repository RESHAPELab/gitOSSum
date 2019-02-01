from django.db import models
from pymongo import MongoClient

class RestaurantLocation(models.Model):
    name         = models.CharField(max_length=120)
    location     = models.CharField(max_length=120, null=True, blank=True)
    category     = models.CharField(max_length=120, null=True, blank=False)
    timestamp    = models.DateTimeField(auto_now_add=True)
    updated      = models.DateTimeField(auto_now=True)

class MiningRequest(models.Model):
    repo_name               = models.CharField(max_length=240, null=False, blank=False)
    email                   = models.EmailField(null=False, blank=True)
    timestamp               = models.DateTimeField(auto_now_add=True)
    updated                 = models.DateTimeField(auto_now=True)


    def __str__(self):
        return f"{self.repo_name}, {self.email}, {self.timestamp}, {self.updated}"
