from django import forms
from .models import Case, CaseDocument, CaseUpdate
from accounts.models import LawyerProfile

class CaseForm(forms.ModelForm):
    class Meta:
        model = Case
        fields = ['title', 'description', 'category', 'bounty_amount', 'location', 'urgency', 'deadline']
        widgets = {
            'deadline': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'description': forms.Textarea(attrs={'rows': 5}),
        }

class CaseDocumentForm(forms.ModelForm):
    class Meta:
        model = CaseDocument
        fields = ['title', 'file']

class CaseUpdateForm(forms.ModelForm):
    class Meta:
        model = CaseUpdate
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Provide an update on the case...'}),
        }

class InviteLawyerForm(forms.Form):
    lawyer = forms.ModelChoiceField(
        queryset=LawyerProfile.objects.filter(is_verified=True),
        label="Select Lawyer",
        widget=forms.Select(attrs={'class': 'form-control'})
    )