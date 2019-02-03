from django import forms 
from .models import MiningRequest, BlacklistedMiningRequest, MinedRepo
from django.forms import ValidationError
from mining_scripts.mining import *
import re
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from github import Github # Import PyGithub for mining data



class MiningRequestForm(forms.Form):
    repo_name               = forms.CharField(max_length=120, required=True, label="Repository", 
                              widget= forms.TextInput(attrs={'placeholder':'owner/repository'}))
    email                   = forms.EmailField(required=False, label="Email (optional)", 
                              widget= forms.TextInput(attrs={'placeholder':'me@example.com'}))

    # Function used for validating the mining request form 
    def clean_repo_name(self):
        repo_name = self.cleaned_data['repo_name'].lower()  # This is the repo name we will be looking at 
        valid_repo = re.compile('^((\w+)[-]*)+/+((\w+)[-]*)+\w+$') # Regex that defines a proper repo name 
        mining_requests = list(MiningRequest.objects.values_list('repo_name', flat=True)) # Obtain all the mining requests
        mined_repos = list(MinedRepo.objects.values_list('repo_name', flat=True)) # Obtain all the mining requests
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

        elif repo_name in black_listed_requests:
            errors.append("This repository has been blacklisted by the Administrator.")

        # Raise any errors found 
        if errors != []:
            raise ValidationError(errors)
        
        return repo_name

class SignUpForm(UserCreationForm):
    first_name = forms.CharField(max_length=30, required=True, help_text='*Required.')
    last_name = forms.CharField(max_length=30, required=True, help_text='*Required.')
    github_oauth = forms.CharField(max_length=254, required=False, help_text="*Optional.")
    email = forms.EmailField(max_length=254, required=False, help_text='*Optional.')

    def clean_github_oauth(self):
        github_oauth = self.cleaned_data['github_oauth']

        # Only try to authenticate of a token was passed in 
        if github_oauth != "":
            try:
                g = Github(github_oauth)
                authenticated_repo_test = [repo for repo in g.get_user().get_repos()]
            except Exception: #github.GithubException.BadCredentialsException
                raise ValidationError("Invalid Github OAuth Token.")

        return github_oauth
       
    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'github_oauth', 'password1', 'password2', )
 

class LoginForm(forms.Form):
    username = forms.CharField(max_length=30, required=True)
    raw_password = forms.CharField(widget=forms.PasswordInput())

    def clean_username(self):
        username = self.cleaned_data['username']
        users = list(User.objects.values_list('username', flat=True))
        if not username in users:
            raise ValidationError("Incorrect username.")
        
        return username
    