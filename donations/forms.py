from django import forms
from .models import Donation, Comment
from django.core.validators import MinValueValidator

# Use this if you want to keep ModelForm but override fields
class DonationForm(forms.Form):
    amount = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        min_value=0.01,
        validators=[MinValueValidator(0.01)],
        label='Donation Amount',
        widget=forms.NumberInput(attrs={
            'placeholder': 'Enter amount',
            'class': 'form-control',
            'step': '0.01'
        })
    )
    
    email = forms.EmailField(
        label='Email Address',
        widget=forms.EmailInput(attrs={
            'placeholder': 'Enter your email address',
            'class': 'form-control'
        })
    )
    
    message = forms.CharField(
        required=False,
        label='Your Message (Optional)',
        widget=forms.Textarea(attrs={
            'placeholder': 'Leave a message with your donation',
            'class': 'form-control',
            'rows': 3
        })
    )
    
    is_anonymous = forms.BooleanField(
        required=False,
        label='Make this donation anonymous',
        initial=False
    )
    amount = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        label="Donation Amount",
        widget=forms.NumberInput(attrs={'placeholder': 'e.g., 500.00'})
    )
    phone_number = forms.CharField(
        max_length=15,
        label="Phone Number (M-Pesa)",
        widget=forms.TextInput(attrs={'placeholder': 'e.g., 254722000000'})
    )
    message = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'rows': 3, 'placeholder': 'Optional message to the case owner'}),
        label="Message (Optional)"
    )
    anonymous = forms.BooleanField(
        required=False,
        label="Donate Anonymously"
    )

    def save(self, donor, case, commit=True):
        # You can still simulate a model save using the cleaned data
        cleaned_data = self.cleaned_data
        donation = Donation(
            donor=donor,
            case=case,
            amount=cleaned_data['amount'],
            anonymous=cleaned_data.get('anonymous', False),
            message=cleaned_data.get('message', ''),
            payment_status='PENDING',
            payment_method='MPESA_STK'
        )
        if commit:
            donation.save()
        return donation


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['text', 'is_anonymous']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['is_anonymous'].label = "Post Comment Anonymously"