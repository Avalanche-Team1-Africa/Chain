from django import forms
from .models import Case, CaseDocument, CaseUpdate, LawyerApplication, SuccessStory, CaseEvent, CaseMessage, DocumentTemplate
from accounts.models import LawyerProfile
from multiupload.fields import MultiFileField
from django.core.validators import MinValueValidator
import re



class CaseForm(forms.ModelForm):
    class Meta:
        model = Case
        fields = ['title', 'description', 'category', 'bounty_amount', 'location', 'urgency', 'deadline']
        widgets = {
            'deadline': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'description': forms.Textarea(attrs={'rows': 5}),
        }

class CaseDocumentForm(forms.ModelForm):
    """Form for uploading case documents."""

    class Meta:
        model = CaseDocument
        fields = ['name', 'file']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'file': forms.FileInput(attrs={'class': 'form-control'}),
        }
        help_texts = {
            'name': "Give a name or title to this document",
            'file': "Upload the file (PDF, Word, etc.)",
        }


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


class CaseEventForm(forms.ModelForm):
    """Form for creating and editing case events."""

    class Meta:
        model = CaseEvent
        fields = [
            'case', 'title', 'description', 'event_type',
            'start_time', 'end_time', 'location'
        ]
        widgets = {
            'start_time': forms.DateTimeInput(
                attrs={'type': 'datetime-local'},
                format='%Y-%m-%dT%H:%M'
            ),
            'end_time': forms.DateTimeInput(
                attrs={'type': 'datetime-local'},
                format='%Y-%m-%dT%H:%M'
            ),
            'description': forms.Textarea(attrs={'rows': 4}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        # Format initial datetime values
        if self.instance.start_time:
            self.initial['start_time'] = self.instance.start_time.strftime('%Y-%m-%dT%H:%M')
        if self.instance.end_time:
            self.initial['end_time'] = self.instance.end_time.strftime('%Y-%m-%dT%H:%M')

        # Limit case choices based on user role
        if user:
            if user.role == 'NGO':
                self.fields['case'].queryset = Case.objects.filter(ngo=user)
            elif user.role == 'LAWYER' and hasattr(user, 'lawyer_profile'):
                self.fields['case'].queryset = Case.objects.filter(
                    assigned_lawyer=user.lawyer_profile
                )


class CaseMessageForm(forms.ModelForm):
    attachments = MultiFileField(
        min_num=1,
        max_num=5,
        max_file_size=1024 * 1024 * 5,  # 5 MB
        required=False,
        label="Attachments",
        help_text="Upload up to 5 files (max 5MB each)."
    )

    class Meta:
        model = CaseMessage
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Type your message here...'}),
        }

class DocumentGenerationForm(forms.Form):
    """
    Dynamic form for generating documents from templates.
    Fields are created based on the required_fields of the template.
    """
    document_name = forms.CharField(
        max_length=255,
        help_text="Name for the generated document"
    )

    def __init__(self, *args, **kwargs):
        template = kwargs.pop('template', None)
        super().__init__(*args, **kwargs)

        if template:
            # Add fields based on template required_fields
            for field_info in template.required_fields:
                field_name = field_info.get('name')
                field_type = field_info.get('type', 'text')
                field_label = field_info.get('label', field_name.replace('_', ' ').title())
                field_required = field_info.get('required', True)

                if field_type == 'text':
                    self.fields[field_name] = forms.CharField(
                        label=field_label,
                        required=field_required,
                        max_length=255
                    )
                elif field_type == 'textarea':
                    self.fields[field_name] = forms.CharField(
                        label=field_label,
                        required=field_required,
                        widget=forms.Textarea(attrs={'rows': 4})
                    )
                elif field_type == 'date':
                    self.fields[field_name] = forms.DateField(
                        label=field_label,
                        required=field_required,
                        widget=forms.DateInput(attrs={'type': 'date'})
                    )
                elif field_type == 'number':
                    self.fields[field_name] = forms.IntegerField(
                        label=field_label,
                        required=field_required
                    )
                elif field_type == 'checkbox':
                    self.fields[field_name] = forms.BooleanField(
                        label=field_label,
                        required=False
                    )
                elif field_type == 'select':
                    choices = [(c, c) for c in field_info.get('choices', [])]
                    self.fields[field_name] = forms.ChoiceField(
                        label=field_label,
                        required=field_required,
                        choices=choices
                    )

class DocumentTemplateForm(forms.ModelForm):
    """Form for creating and editing document templates."""

    class Meta:
        model = DocumentTemplate
        fields = [
            'name', 'description', 'template_file',
            'available_to_ngo', 'available_to_lawyer'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }

class TokenRedemptionForm(forms.Form):
    tokens = forms.IntegerField(
        label="Number of Tokens",
        min_value=1,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Enter tokens to redeem'})
    )
    redemption_method = forms.ChoiceField(
        label="Redemption Method",
        choices=(('crypto', 'Cryptocurrency (HakiToken)'), ('mpesa', 'M-Pesa')),
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    eth_address = forms.CharField(
        label="Ethereum Address",
        max_length=42,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '0x...'})
    )
    phone_number = forms.CharField(
        label="Phone Number",
        max_length=15,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+2547xxxxxxxx'})
    )

    def clean(self):
        cleaned_data = super().clean()
        method = cleaned_data.get('redemption_method')
        eth_address = cleaned_data.get('eth_address')
        phone_number = cleaned_data.get('phone_number')

        if method == 'crypto':
            if not eth_address or not re.match(r'^0x[a-fA-F0-9]{40}$', eth_address):
                self.add_error('eth_address', 'Please enter a valid Ethereum address.')
        elif method == 'mpesa':
            if not phone_number or not re.match(r'^\+254[0-9]{9}$', phone_number):
                self.add_error('phone_number', 'Please enter a valid phone number (e.g., +2547xxxxxxxx).')

        return cleaned_data
    
class WalletDepositForm(forms.Form):
    amount = forms.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0.01)],
        label="Amount to Deposit"
    )
    payment_method = forms.ChoiceField(
        choices=(('ETH', 'Ethereum'), ('MPESA', 'M-Pesa')),
        label="Payment Method"
    )
    eth_address = forms.CharField(
        max_length=42,
        required=False,
        label="Ethereum Address (for ETH deposits)"
    )
    phone_number = forms.CharField(
        max_length=15,
        required=False,
        label="Phone Number (for M-Pesa deposits)"
    )

    def clean(self):
        cleaned_data = super().clean()
        payment_method = cleaned_data.get('payment_method')
        eth_address = cleaned_data.get('eth_address')
        phone_number = cleaned_data.get('phone_number')

        if payment_method == 'ETH' and not eth_address:
            raise forms.ValidationError("Ethereum address is required for ETH deposits.")
        if payment_method == 'MPESA' and not phone_number:
            raise forms.ValidationError("Phone number is required for M-Pesa deposits.")
        return cleaned_data