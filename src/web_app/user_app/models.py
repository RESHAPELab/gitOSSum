from django.db import models
from django_mysql.models import ListTextField
from django.core.validators import MinValueValidator

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

class FeedbackMessage(models.Model):
    subject                 = models.CharField(max_length=120, null=False, blank=False)
    message                 = models.TextField(null=False, blank=False)
    requested_by            = models.CharField(max_length=240, null=False, blank=False)
    sender_email            = models.EmailField(null=False, blank=False)
    timestamp               = models.DateTimeField(auto_now_add=True)



    def __str__(self):
        return f"{self.repo_name}, {self.email}, {self.timestamp}, {self.updated}"


class QueuedMiningRequest(models.Model):
    repo_name               = models.CharField(max_length=240, null=False, blank=False)
    requested_by            = models.CharField(max_length=240, null=False, blank=False)
    timestamp               = models.DateTimeField(auto_now_add=True)
    requested_timestamp     = models.DateTimeField(auto_now_add=False)

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
    num_pulls                    = models.IntegerField(validators=[MinValueValidator(0)])
    num_closed_merged_pulls      = models.IntegerField(validators=[MinValueValidator(0)])
    num_closed_unmerged_pulls    = models.IntegerField(validators=[MinValueValidator(0)])
    num_open_pulls               = models.IntegerField(validators=[MinValueValidator(0)])
    created_at_list              = ListTextField(base_field=models.CharField(max_length=240))
    closed_at_list               = ListTextField(base_field=models.CharField(max_length=240))
    merged_at_list               = ListTextField(base_field=models.CharField(max_length=240))
    num_newcomer_labels          = models.IntegerField(validators=[MinValueValidator(0)])
    bar_chart_html               = models.TextField()
    pull_line_chart_html         = models.TextField()
    completed_timestamp          = models.DateTimeField(auto_now_add=True)
    accepted_timestamp           = models.DateTimeField(auto_now_add=False)
    requested_timestamp          = models.DateTimeField(auto_now_add=False)
    updated                      = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.repo_name}, {self.completed_timestamp}, {self.updated}"