from django import forms
from .models import Donation, Comment

class DonationForm(forms.ModelForm):
    class Meta:
        model = Donation
        fields = ['amount', 'anonymous']  

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['anonymous'].label = "Donate Anonymously"  

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['text', 'is_anonymous']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['is_anonymous'].label = "Post Comment Anonymously"