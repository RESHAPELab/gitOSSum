from django import forms 
from .models import MiningRequest, BlacklistedMiningRequest, MinedRepo
from django.forms import ValidationError
from mining_scripts.mining import *
import re

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

