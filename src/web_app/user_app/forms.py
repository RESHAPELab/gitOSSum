from django import forms 
from .models import MiningRequest, QueuedMiningRequest, BlacklistedMiningRequest, MinedRepo
from django.forms import ValidationError, MultipleChoiceField, CheckboxSelectMultiple
from mining_scripts.mining import *
from mining_scripts.batchify import *
import re
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from github import Github # Import PyGithub for mining data
from .filters import *


class FeedbackForm(forms.Form):
    subject                 = forms.CharField(max_length=120, required=True, label="Subject",
                              widget = forms.TextInput(attrs={'placeholder':'Subject of message...'}))
    body                    = forms.CharField(max_length=1000, required=True, label='Message',
                              widget = forms.Textarea(attrs={'placeholder':'Message content...', 
                                                             'style': 'resize:none;'}))

class MiningRequestForm(forms.Form):
    repo_name               = forms.CharField(max_length=120, required=True, label="Repository", 
                              widget= forms.TextInput(attrs={'placeholder':'owner/repository'}))
    email                   = forms.BooleanField(required=False,
                                                 label="Send Me Email Notifications About This Request")

    # Function used for validating the mining request form 
    def clean_repo_name(self):
        repo_name = self.cleaned_data['repo_name'].lower()  # This is the repo name we will be looking at 
        valid_repo = re.compile('^(((\w+)[-]*)\w+)+/+((\w+)([-]|[.])*)+\w+$') # Regex that defines a proper repo name 
        mining_requests = list(MiningRequest.objects.values_list('repo_name', flat=True)) # Obtain all the mining requests
        mined_repos = list(MinedRepo.objects.values_list('repo_name', flat=True)) # Obtain all the mining requests
        queued_repos = list(QueuedMiningRequest.objects.values_list("repo_name", flat=True))
        black_listed_requests = list(BlacklistedMiningRequest.objects.values_list('repo_name', flat=True)) # Obtain all the mining requests
        mongo_repo = find_repo_main_page(repo_name)
        errors = [] # A list for holding validation errors 

        # Repo must match regex
        if not valid_repo.fullmatch(repo_name):
            errors.append('Repository must of the form "repo/name".')

        # If it matches the regex, it must exist on github 
        if isinstance(find_repo_main_page(repo_name), Exception) and valid_repo.fullmatch(repo_name):
            errors.append("That repository does not exist on GitHub.")

        # The repo cannot have already been mined 
        if  repo_name in mined_repos:
            errors.append("That repository has already been mined.")

        # The repo cannot have already been requested and hasn't already been mined 
        elif repo_name in mining_requests:
            errors.append("This repository has already been requested.")

        # The repo cannot currently be mining
        elif repo_name in queued_repos:
            errors.append("This repository is currently being mined.")

        # The repo cannot be blacklisted
        elif repo_name in black_listed_requests:
            errors.append("This repository has been blacklisted by the Administrator.")

        # (if it exists, and matches valid repo regex) the repo cannot have 0 pull requests 
        if not isinstance(find_repo_main_page(repo_name), Exception) and valid_repo.fullmatch(repo_name):
            batches = batchify(repo_name)
            
            # If there are no batches, thats a problem!
            if len(batches) == 0:
                errors.append("This repository has no pull requests!")


        # Raise any errors found 
        if errors != []:
            raise ValidationError(errors)
        
        return repo_name

class SignupForm(UserCreationForm):
    email = forms.EmailField(max_length=200, help_text='Required')
    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')
  
class LoginForm(forms.Form):
    username = forms.CharField(max_length=30, required=True)
    raw_password = forms.CharField(widget=forms.PasswordInput())

    def clean_username(self):
        username = self.cleaned_data['username']
        users = list(User.objects.values_list('username', flat=True))
        if not username in users:
            raise ValidationError("Incorrect username.")
        
        return username


class Filter(forms.Form):
    search = forms.CharField(max_length=120, required=False, 
        label="Search", widget = forms.TextInput(attrs={'placeholder':'Search For Repositories', 'class': 'filter-input'}))

    languages = forms.MultipleChoiceField(
        required= False,
        widget  = forms.CheckboxSelectMultiple,
        choices = [tuple((item, item)) for item in get_language_list_from_mongo()]
    )

    min_pull_requests = forms.IntegerField(required=False,
        widget = forms.NumberInput(attrs={'min':1, 'placeholder':'min number of pulls', 'class': 'filter-input'}))

    max_pull_requests = forms.IntegerField(required=False,
        widget = forms.NumberInput(attrs={'min':2, 'placeholder':'max number of pulls', 'class': 'filter-input'}))

    has_wiki = forms.MultipleChoiceField(
        required= False,
        widget = forms.CheckboxSelectMultiple,
        choices =[tuple(('True', 'True'))]
    )

    # The form must be initialized by passing in the languages every time.
    # This ensures the language checkboxes are up to date all the time 
    def __init__(self, languages, *args, **kwargs):
        super(Filter, self).__init__(*args, **kwargs)
        self.fields['languages'] = forms.MultipleChoiceField(
                                        required= False,
                                        widget  = forms.CheckboxSelectMultiple,
                                        choices = [tuple((language[0], f'{language[0]} ({language[1]})')) for language in languages]
                                    )

    def selected_languages_labels(self):
        return [label for value, label in self.fields['languages'].choices if value in self['languages'].value()]