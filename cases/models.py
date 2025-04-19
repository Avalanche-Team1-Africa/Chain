from django.db import models
from django.conf import settings
from django.utils import timezone
from accounts.models import LawyerProfile

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
    
    title = models.CharField(max_length=200)
    description = models.TextField()
    ngo = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='cases')
    category = models.ForeignKey(CaseCategory, on_delete=models.SET_NULL, null=True, related_name='cases')
    bounty_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    location = models.CharField(max_length=200)
    urgency = models.CharField(max_length=20, choices=URGENCY_CHOICES, default='medium')
    assigned_lawyer = models.ForeignKey(LawyerProfile, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_cases')
    shortlisted_lawyers = models.ManyToManyField(LawyerProfile, related_name='shortlisted_cases', blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deadline = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return self.title
    
    def total_donations(self):
        """Calculate total donations for this case"""
        from donation.models import Donation
        donations = Donation.objects.filter(case=self)
        return sum(donation.amount for donation in donations)

class CaseDocument(models.Model):
    case = models.ForeignKey(Case, on_delete=models.CASCADE, related_name='documents')
    title = models.CharField(max_length=200)
    file = models.FileField(upload_to='case_documents/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.title} - {self.case.title}"

class CaseUpdate(models.Model):
    case = models.ForeignKey(Case, on_delete=models.CASCADE, related_name='updates')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Update on {self.case.title} at {self.created_at}"

class LawyerApplication(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('shortlisted', 'Shortlisted'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
    )
    
    case = models.ForeignKey(Case, on_delete=models.CASCADE, related_name='applications')
    lawyer = models.ForeignKey(LawyerProfile, on_delete=models.CASCADE, related_name='applications')
    cover_letter = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    applied_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('case', 'lawyer')
    
    def __str__(self):
        return f"{self.lawyer.user.get_full_name()} applying for {self.case.title}"