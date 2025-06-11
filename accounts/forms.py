from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User, NGOProfile, LawyerProfile, DonorProfile
class UserRegistrationForm(UserCreationForm):
    phone_number = forms.CharField(
        label='Phone Number',
        help_text='Enter your phone number starting with +254. Example: +254712345678'
    )

    class Meta:
        model = User
        fields = ('email', 'role', 'phone_number', 'password1', 'password2')
class NGOProfileForm(forms.ModelForm):
    class Meta:
        model = NGOProfile
        exclude = ('user', 'is_verified')

class LawyerProfileForm(forms.ModelForm):
    class Meta:
        model = LawyerProfile
        exclude = ('user', 'is_verified', 'rating')

class DonorProfileForm(forms.ModelForm):
    class Meta:
        model = DonorProfile
        exclude = ('user',)