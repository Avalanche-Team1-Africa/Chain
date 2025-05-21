from django.db import models
from django.conf import settings
from accounts.models import LawyerProfile
from django.contrib.postgres.fields import ArrayField
from django.core.exceptions import ValidationError
from django.utils import timezone

from django.contrib.auth import get_user_model

User = get_user_model()


class CaseCategory(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    class Meta:
        verbose_name_plural = "Case Categories"

    def __str__(self):
        return self.name


class Case(models.Model):
    STATUS_CHOICES = (
        ('open', 'Open'),
        ('assigned', 'Assigned'),
        ('in_progress', 'In Progress'),
        ('review', 'Under Review'),
        ('completed', 'Completed'),
        ('closed', 'Closed'),
    )
    URGENCY_CHOICES = (
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    )
    COMPLEXITY_CHOICES = (
        ('simple', 'Simple'),
        ('moderate', 'Moderate'),
        ('complex', 'Complex'),
    )

    title = models.CharField(max_length=200)
    description = models.TextField()
    ngo = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='cases'
    )
    category = models.ForeignKey(
        CaseCategory,
        on_delete=models.SET_NULL,
        null=True,
        related_name='cases'
    )
    bounty_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )
    location = models.CharField(max_length=200)
    urgency = models.CharField(
        max_length=20,
        choices=URGENCY_CHOICES,
        default='medium'
    )
    complexity = models.CharField(
        max_length=20,
        choices=COMPLEXITY_CHOICES,
        default='moderate'
    )
    assigned_lawyer = models.ForeignKey(
        LawyerProfile,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_cases'
    )
    shortlisted_lawyers = models.ManyToManyField(
        LawyerProfile,
        related_name='shortlisted_cases',
        blank=True
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='open'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deadline = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.title

    def total_donations(self):
        from donations.models import Donation
        return Donation.objects.filter(case=self).aggregate(models.Sum('amount'))['amount__sum'] or 0

    def is_completed(self):
        return self.status == 'completed'


class CaseDocument(models.Model):
    DOCUMENT_TYPE_CHOICES = [
        ('evidence', 'Evidence'),
        ('legal_brief', 'Legal Brief'),
        ('court_filing', 'Court Filing'),
        ('generated', 'Generated Document'),
        ('other', 'Other'),
    ]

    case = models.ForeignKey(
        Case,
        on_delete=models.CASCADE,
        related_name='documents'
    )
    name = models.CharField(max_length=255)
    file = models.FileField(upload_to='case_documents/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.case.title}"


def document_upload_path(instance, filename):
    """Determine upload path for case documents."""
    return f"case_documents/{instance.case.reference_number}/{filename}"


class CaseUpdate(models.Model):
    case = models.ForeignKey(Case, on_delete=models.CASCADE, related_name='updates')
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Update on {self.case.title} at {self.created_at}"


class CaseMilestone(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
    )

    case = models.ForeignKey(
        Case,
        on_delete=models.CASCADE,
        related_name='milestones'
    )
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    target_date = models.DateField()
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['target_date']

    def __str__(self):
        return f"{self.case.title} - {self.title}"


class CaseEvent(models.Model):
    EVENT_TYPE_CHOICES = [
        ('meeting', 'Meeting'),
        ('hearing', 'Court Hearing'),
        ('deadline', 'Deadline'),
        ('appointment', 'Appointment'),
        ('other', 'Other'),
    ]

    case = models.ForeignKey(
        Case,
        on_delete=models.CASCADE,
        related_name='events'
    )
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    event_type = models.CharField(max_length=20, choices=EVENT_TYPE_CHOICES)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField(null=True, blank=True)
    location = models.CharField(max_length=255, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='created_events'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.case.reference_number} - {self.title}"

    def get_color_by_type(self):
        color_map = {
            'meeting': '#007bff',   # Blue
            'hearing': '#dc3545',   # Red
            'deadline': '#fd7e14',  # Orange
            'appointment': '#6f42c1',  # Purple
            'other': '#6c757d'      # Gray
        }
        return color_map.get(self.event_type, '#6c757d')


class CaseMessage(models.Model):
    case = models.ForeignKey(
        Case,
        on_delete=models.CASCADE,
        related_name='messages'
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='sent_messages'
    )
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    read_by = ArrayField(models.IntegerField(), default=list, blank=True)

    def __str__(self):
        return f"Message from {self.sender} on {self.timestamp.strftime('%Y-%m-%d %H:%M')}"


class CaseMessageAttachment(models.Model):
    message = models.ForeignKey(
        CaseMessage,
        on_delete=models.CASCADE,
        related_name='attachments'
    )
    file = models.FileField(upload_to='message_attachments/')
    name = models.CharField(max_length=255)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


def template_upload_path(instance, filename):
    return f"document_templates/{filename}"


class WalletTransaction(models.Model):
    TRANSACTION_TYPES = (
        ('DEPOSIT', 'Deposit'),
        ('WITHDRAW', 'Withdraw'),
        ('EARN', 'Earn'),
        ('SPEND', 'Spend'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    description = models.CharField(max_length=255)
    payment_method = models.CharField(max_length=20, choices=(('ETH', 'Ethereum'), ('MPESA', 'M-Pesa')))  # Track payment method
    external_tx_id = models.CharField(max_length=100, blank=True, null=True)  # For blockchain or Paystack tx ID
    case = models.ForeignKey('Case', on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.transaction_type} of {self.amount} via {self.payment_method} for {self.user.username}"

class ChatMessage(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='case_chat_messages')
    case = models.ForeignKey('Case', on_delete=models.SET_NULL, null=True, blank=True)
    message = models.TextField()
    response = models.TextField(null=True, blank=True)  # AI response
    timestamp = models.DateTimeField(default=timezone.now)
    is_user_message = models.BooleanField(default=True)  # True for user, False for AI

    class Meta:
        ordering = ['timestamp']

    def __str__(self):
        return f"{self.user.username}: {self.message} ({self.timestamp})"




class DocumentTemplate(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    template_file = models.FileField(upload_to=template_upload_path)
    available_to_ngo = models.BooleanField(default=True)
    available_to_lawyer = models.BooleanField(default=True)
    required_fields = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class LawyerApplication(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('shortlisted', 'Shortlisted'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
    )

    case = models.ForeignKey(
        'cases.Case',
        on_delete=models.CASCADE,
        related_name='applications'
    )
    lawyer = models.ForeignKey(
        'accounts.LawyerProfile',
        on_delete=models.CASCADE,
        related_name='applications'
    )
    cover_letter = models.TextField()
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    applied_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('case', 'lawyer')
        verbose_name = 'Lawyer Application'
        verbose_name_plural = 'Lawyer Applications'

    def __str__(self):
        return f"{self.lawyer.user.get_full_name()} applying for {self.case.title}"


class LawyerRating(models.Model):
    RATING_CHOICES = (
        (1, '1 Star'),
        (2, '2 Stars'),
        (3, '3 Stars'),
        (4, '4 Stars'),
        (5, '5 Stars'),
    )

    case = models.ForeignKey(
        Case,
        on_delete=models.CASCADE,
        related_name='lawyer_ratings'
    )
    lawyer = models.ForeignKey(
        LawyerProfile,
        on_delete=models.CASCADE,
        related_name='ratings'
    )
    rating = models.IntegerField(choices=RATING_CHOICES)
    review = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )

    class Meta:
        unique_together = ('case', 'lawyer')

    def __str__(self):
        return f"{self.lawyer.user.get_full_name()} - {self.case.title} - {self.rating} stars"


class SuccessStory(models.Model):
    lawyer = models.ForeignKey(
        LawyerProfile,
        on_delete=models.CASCADE,
        related_name='success_stories'
    )
    case = models.ForeignKey(
        Case,
        on_delete=models.CASCADE,
        related_name='success_stories',
        null=True,
        blank=True
    )
    title = models.CharField(max_length=200)
    content = models.TextField()
    image = models.ImageField(
        upload_to='success_stories/',
        null=True,
        blank=True
    )
    is_public = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Success Stories"

    def __str__(self):
        return self.title
    
class UserWallet(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='wallet',
    )
    balance = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
    )
    eth_address = models.CharField(
        max_length=42,
        blank=True,
        null=True,
        help_text="Ethereum address for crypto redemptions (e.g., 0x...)",
    )
    phone_number = models.CharField(
        max_length=15,
        blank=True,
        null=True,
        help_text="Phone number for M-Pesa redemptions (e.g., +2547xxxxxxxx)",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}'s Wallet: {self.balance} tokens"

    class Meta:
        verbose_name = "User Wallet"
        verbose_name_plural = "User Wallets"


class TokenTransaction(models.Model):
    TRANSACTION_TYPES = (
        ('earn', 'Earned'),
        ('spend', 'Spent'),
        ('adjust', 'Adjustment'),
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='token_transactions',
    )
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
    )
    transaction_type = models.CharField(
        max_length=10,
        choices=TRANSACTION_TYPES,
    )
    description = models.TextField()
    case = models.ForeignKey(
        'Case',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='token_transactions',
    )
    external_tx_id = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Blockchain or Paystack transaction ID",
    )
    created_at = models.DateTimeField(
        default=timezone.now,
    )

    def __str__(self):
        return f"{self.user.username} - {self.transaction_type} {self.amount} tokens: {self.description}"

    class Meta:
        verbose_name = "Token Transaction"
        verbose_name_plural = "Token Transactions"
        indexes = [
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['case']),
        ]

class CaseNotification(models.Model):
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='custom_notifications'
    )
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='sent_notifications'
    )
    case = models.ForeignKey(
        'Case',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='notifications'
    )
    NOTIFICATION_TYPES = (
        ('case_assignment', 'Case Assignment'),
        ('client_message', 'Client Message'),
        ('deadline', 'Deadline Reminder'),
        ('system', 'System Notification'),
        ('donation', 'Donation Alert'),
        ('comment', 'Case Comment'),
    )
    notification_type = models.CharField(max_length=50, choices=NOTIFICATION_TYPES)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='custom_notifications'  # ← Changed related_name
    )
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='sent_notifications'
    )
    case = models.ForeignKey(
        'Case',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='notifications'
    )
    notification_type = models.CharField(max_length=50, choices=NOTIFICATION_TYPES)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Notification for {self.recipient} - {self.notification_type}"