from django import forms 
from .models import AdminApproval

class MiningRequestCreateForm(forms.Form):
    repo_name               = forms.CharField(max_length=120, required=True)
    email                   = forms.EmailField(required=False)

class AdminApprovalForm(forms.Form):
    approve_for_mining = forms.BooleanField(required=False)

    class Meta: 
        model = AdminApproval