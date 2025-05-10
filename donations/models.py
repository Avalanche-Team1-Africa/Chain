from django.db import models
from django.utils.translation import gettext_lazy as _
from cases.models import Case
from accounts.models import DonorProfile


class PaymentStatus:
    """Constants for payment status values"""
    PENDING = 'PENDING'
    COMPLETED = 'COMPLETED'
    FAILED = 'FAILED'
    
    CHOICES = (
        (PENDING, _('Pending')),
        (COMPLETED, _('Completed')),
        (FAILED, _('Failed')),
    )


class PaymentMethod:
    """Constants for payment method values"""
    PAYSTACK = 'PAYSTACK'
    CRYPTO = 'CRYPTO'
    OTHER = 'OTHER'
    MPESA = 'MPESA'
    
    CHOICES = (
        (PAYSTACK, _('Paystack')),
        (CRYPTO, _('Cryptocurrency')),
        (MPESA, _('M-Pesa')),
        (OTHER, _('Other')),
    )
    """Constants for payment method values"""
    PAYSTACK = 'PAYSTACK'
    CRYPTO = 'CRYPTO'
    OTHER = 'OTHER'
    
    CHOICES = (
        (PAYSTACK, _('Paystack')),
        (CRYPTO, _('Cryptocurrency')),
        (OTHER, _('Other')),
    )


class Donation(models.Model):
    """
    Model representing donations made to specific cases.
    Tracks payment information, status, and donation details.
    """
    donor = models.ForeignKey(
        DonorProfile,
        on_delete=models.CASCADE,
        related_name='donations'
    )
    case = models.ForeignKey(
        Case,
        on_delete=models.CASCADE,
        related_name='donations'
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    amount_received = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text=_("Actual amount received, if different.")
    )
    transaction_id = models.CharField(max_length=100, blank=True)
    reference = models.CharField(
        max_length=100,
        blank=True,
        help_text=_("Paystack payment reference")
    )
    payment_status = models.CharField(
        max_length=20,
        choices=PaymentStatus.CHOICES,
        default=PaymentStatus.PENDING
    )
    payment_method = models.CharField(
        max_length=20,
        choices=PaymentMethod.CHOICES,
        default=PaymentMethod.PAYSTACK
    )
    anonymous = models.BooleanField(default=False)
    message = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    callback_response = models.JSONField(
        null=True,
        blank=True,
        help_text=_("Raw payment gateway callback response.")
    )
    email = models.EmailField(
        blank=True,
        help_text=_("Email for payment confirmation")
    )
    
    class Meta:
        ordering = ['-timestamp']
        verbose_name = _('Donation')
        verbose_name_plural = _('Donations')
        
    def __str__(self):
        if self.anonymous:
            return f"Anonymous donation of {self.amount} to {self.case.title}"
        return f"Donation of {self.amount} by {self.donor.user.username} to {self.case.title}"
    
    @property
    def is_completed(self):
        """Check if the donation payment is completed"""
        return self.payment_status == PaymentStatus.COMPLETED


class Comment(models.Model):
    """
    Model representing comments made on cases by donors.
    Comments can be anonymous or associated with a donor.
    """
    case = models.ForeignKey(
        Case, 
        related_name='comments', 
        on_delete=models.CASCADE
    )
    donor = models.ForeignKey(
        DonorProfile,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='case_comments'
    )
    text = models.TextField()
    is_anonymous = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = _('Comment')
        verbose_name_plural = _('Comments')
    
    def __str__(self):
        author = _('Anonymous') if self.is_anonymous else (self.donor.user.username if self.donor else _('Unknown'))
        return f"Comment by {author} on {self.case.title}"