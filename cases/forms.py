from django import forms
from .models import Case, CaseDocument, CaseUpdate, LawyerApplication, SuccessStory
from accounts.models import LawyerProfile
from multiupload.fields import MultiFileField

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


class LawyerApplicationForm(forms.ModelForm):
    cover_letter = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 8}),
        help_text="Explain why you are a good fit for this case and your relevant experience."
    )

    class Meta:
        model = LawyerApplication
        fields = ['cover_letter']


class CaseProgressForm(forms.Form):
    content = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 8}),
        label="Progress Update",
        help_text="Provide details about the current status of the case and any developments."
    )


class CaseCompletionForm(forms.Form):
    outcome_description = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 8}),
        label="Case Outcome",
        help_text="Describe the outcome of the case and the results achieved."
    )
    documents = MultiFileField(
        min_num=1,
        max_num=5,
        max_file_size=1024*1024*5,  # 5 MB
        required=False,
        help_text="Upload up to 5 final documents (5MB max each)."
    )
class SuccessStoryForm(forms.ModelForm):
    class Meta:
        model = SuccessStory
        fields = ['title', 'content', 'image', 'is_public']
        widgets = {
            'content': forms.Textarea(attrs={'rows': 8}),
        }
        help_texts = {
            'is_public': "If checked, this success story will be visible on your public profile."
        }
