from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils.translation import gettext_lazy as _

class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('Users must have an email address')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', 'ADMIN')
        
        return self.create_user(email, password, **extra_fields)

class User(AbstractUser):
    ROLE_CHOICES = (
        ('NGO', 'NGO'),
        ('LAWYER', 'Lawyer'),
        ('DONOR', 'Donor'),
        ('ADMIN', 'Admin'),
    )
    
    username = None
    email = models.EmailField(_('email address'), unique=True)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    is_verified = models.BooleanField(default=False)
    verification_code = models.CharField(max_length=6, blank=True, null=True)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['role']
    
    objects = UserManager()
    
    def __str__(self):
        return self.email

class NGOProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='ngo_profile')
    organization_name = models.CharField(max_length=255)
    registration_number = models.CharField(max_length=100)
    description = models.TextField()
    website = models.URLField(blank=True, null=True)
    address = models.TextField()
    logo = models.ImageField(upload_to='ngo_logos/', blank=True, null=True)
    verification_documents = models.FileField(upload_to='ngo_verification/', blank=True, null=True)
    is_verified = models.BooleanField(default=False)
    
    def __str__(self):
        return self.organization_name

class LawyerProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='lawyer_profile')
    full_name = models.CharField(max_length=255)
    license_number = models.CharField(max_length=100)
    specialization = models.CharField(max_length=255)
    experience_years = models.PositiveIntegerField()
    education = models.TextField()
    bio = models.TextField()
    profile_picture = models.ImageField(upload_to='lawyer_profiles/', blank=True, null=True)
    verification_documents = models.FileField(upload_to='lawyer_verification/', blank=True, null=True)
    is_verified = models.BooleanField(default=False)
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.0)
    
    def __str__(self):
        return self.full_name

class DonorProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='donor_profile')
    display_name = models.CharField(max_length=255)
    allow_anonymous = models.BooleanField(default=False)
    preferred_causes = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return self.display_name