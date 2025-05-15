import random
import string
import africastalking
from django.http import Http404, HttpResponseForbidden
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth import login,logout
from django.contrib import messages
from django.views.generic import CreateView, UpdateView, DetailView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.conf import settings

from cases.models import Case, CaseMilestone, CaseUpdate
from .models import User, NGOProfile, LawyerProfile, DonorProfile
from .forms import UserRegistrationForm, NGOProfileForm, LawyerProfileForm, DonorProfileForm

# Initialize Africa's Talking
africastalking.initialize(settings.AFRICASTALKING_USERNAME, settings.AFRICASTALKING_API_KEY)
sms = africastalking.SMS

def generate_verification_code():
    return ''.join(random.choices(string.digits, k=6))

def send_sms(phone_number, message):
    try:
        response = sms.send(message, [phone_number], sender_id="AFTKNG")
        print("SMS sent:", response)
    except Exception as e:
        print("SMS sending error:", str(e))

class RegisterView(CreateView):
    form_class = UserRegistrationForm
    template_name = 'accounts/register.html'
    success_url = reverse_lazy('accounts:verify_email')  # Note the namespace
    
    def form_valid(self, form):
        user = form.save(commit=False)
        user.verification_code = generate_verification_code()
        user.is_active = False  # Prevent login until OTP is verified
        user.save()
        
        # Create the appropriate profile
        if user.role == 'NGO':
            NGOProfile.objects.create(user=user)
        elif user.role == 'LAWYER':
            LawyerProfile.objects.create(user=user)
        elif user.role == 'DONOR':
            DonorProfile.objects.create(user=user)
        
        # Send OTP SMS
        otp_message = f"Your HakiChain OTP is: {user.verification_code}"
        send_sms(user.phone_number, otp_message)
        
        # Temporarily store user id in session for verification
        self.request.session['unverified_user_id'] = user.id
        messages.success(self.request, 'An OTP was sent to your phone. Please verify to continue.')
        return redirect('accounts:verify_email')

class VerifyEmailView(UpdateView):
    model = User
    fields = ['verification_code']
    template_name = 'accounts/verify_email.html'
    success_url = reverse_lazy('accounts:profile_setup')
    
    def get_object(self):
        user_id = self.request.session.get('unverified_user_id')
        return User.objects.get(id=user_id) if user_id else None
    
    def form_valid(self, form):
        user = form.save(commit=False)
        input_code = self.request.POST.get('verification_code')
        
        if user.verification_code == input_code:
            user.is_verified = True
            user.is_active = True  # Allow login
            user.verification_code = ''
            user.save()
            
            # Clear session
            if 'unverified_user_id' in self.request.session:
                del self.request.session['unverified_user_id']
            
            # Send welcome SMS
            welcome_msg = f"Hello {user.username}, thank you for creating an account with HakiChain. Justice is in your hands always."
            send_sms(user.phone_number, welcome_msg)
            
            login(self.request, user)
            messages.success(self.request, 'Verification successful! You are now logged in.')
            return redirect(self.success_url)
        else:
            messages.error(self.request, 'Invalid verification code.')
            return self.form_invalid(form)

class ProfileSetupView(LoginRequiredMixin, UpdateView):
    template_name = 'accounts/profile_setup.html'
    
    def get_object(self):
        user = self.request.user
        
        # Check if profile exists or needs to be created
        if user.role == 'NGO':
            profile, created = NGOProfile.objects.get_or_create(user=user)
            return profile
        elif user.role == 'LAWYER':
            profile, created = LawyerProfile.objects.get_or_create(user=user)
            return profile
        elif user.role == 'DONOR':
            profile, created = DonorProfile.objects.get_or_create(user=user)
            return profile
        else:
            # Handle unexpected role
            raise Http404("Profile type not found")
    
    def get_form_class(self):
        user = self.request.user
        if user.role == 'NGO':
            return NGOProfileForm
        elif user.role == 'LAWYER':
            return LawyerProfileForm
        elif user.role == 'DONOR':
            return DonorProfileForm
        else:
            # Handle unexpected role
            raise Http404("Form not found for this user role")
    
    def get_success_url(self):
        user = self.request.user
        if user.role == 'NGO':
            return reverse_lazy('accounts:ngo_dashboard')
        elif user.role == 'LAWYER':
            return reverse_lazy('accounts:lawyer_dashboard')
        elif user.role == 'DONOR':
            return reverse_lazy('accounts:donor_dashboard')
        return reverse_lazy('accounts:profile')  # Default fallback
    
    def form_valid(self, form):
        # Save the profile
        form.instance.user = self.request.user
        response = super().form_valid(form)
        messages.success(self.request, 'Profile updated successfully!')
        return response

class ProfileView(LoginRequiredMixin, DetailView):
    template_name = 'accounts/profile.html'
    
    def get_object(self):
        return self.request.user
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        if user.role == 'NGO':
            context['profile'] = getattr(user, 'ngo_profile', None)
        elif user.role == 'LAWYER':
            context['profile'] = getattr(user, 'lawyer_profile', None)
        elif user.role == 'DONOR':
            context['profile'] = getattr(user, 'donor_profile', None)
        
        # If profile doesn't exist yet, redirect to profile setup
        if not context['profile']:
            return redirect('accounts:profile_setup')
            
        return context

class NGOProfileView(LoginRequiredMixin, DetailView):
    model = NGOProfile
    template_name = 'accounts/ngo_profile.html'
    
    def get_object(self):
        return getattr(self.request.user, 'ngo_profile', None)
        
    def dispatch(self, request, *args, **kwargs):
        # Check if profile exists
        if not self.get_object():
            return redirect('accounts:profile_setup')
        return super().dispatch(request, *args, **kwargs)

class LawyerProfileView(LoginRequiredMixin, DetailView):
    model = LawyerProfile
    template_name = 'accounts/lawyer_profile.html'

    def get_object(self):
        # Get the LawyerProfile based on the passed user_id
        user_id = self.kwargs.get('user_id')
        if user_id:
            return get_object_or_404(LawyerProfile, user__id=user_id)
        return getattr(self.request.user, 'lawyer_profile', None)

    def dispatch(self, request, *args, **kwargs):
        # Check if profile exists
        if not self.get_object():
            return redirect('accounts:profile_setup')
        return super().dispatch(request, *args, **kwargs)

class DonorProfileView(LoginRequiredMixin, DetailView):
    model = DonorProfile
    template_name = 'accounts/donor_profile.html'
    
    def get_object(self):
        return getattr(self.request.user, 'donor_profile', None)
        
    def dispatch(self, request, *args, **kwargs):
        # Check if profile exists
        if not self.get_object():
            return redirect('accounts:profile_setup')
        return super().dispatch(request, *args, **kwargs)
@login_required
def ngo_dashboard(request):
    """NGO dashboard showing case overview"""
    if request.user.role != 'NGO' or not hasattr(request.user, 'ngo_profile'):
        return HttpResponseForbidden("You must be an NGO to access this page")
    
    # Get all cases for this NGO
    all_cases = Case.objects.filter(ngo=request.user).order_by('-created_at')
    
    # Get case counts by status
    open_cases = all_cases.filter(status='open')
    assigned_cases = all_cases.filter(status='assigned')
    in_progress_cases = all_cases.filter(status='in_progress')
    review_cases = all_cases.filter(status='review')
    completed_cases = all_cases.filter(status='completed')
    
    # Get recent activity (updates across all cases)
    recent_updates = CaseUpdate.objects.filter(
        case__ngo=request.user
    ).select_related('case', 'created_by').order_by('-created_at')[:5]
    
    # Get upcoming milestones
    from datetime import date, timedelta
    upcoming_milestones = CaseMilestone.objects.filter(
        case__ngo=request.user,
        status='pending',
        target_date__gte=date.today(),
        target_date__lte=date.today() + timedelta(days=14)  # Next 2 weeks
    ).select_related('case').order_by('target_date')[:5]
    
    context = {
        'all_cases': all_cases,
        'open_cases': open_cases,
        'assigned_cases': assigned_cases,
        'in_progress_cases': in_progress_cases,
        'review_cases': review_cases,
        'completed_cases': completed_cases,
        'recent_updates': recent_updates,
        'upcoming_milestones': upcoming_milestones,
        'total_cases': all_cases.count(),
    }
    return render(request, 'cases/ngo/dashboard.html', context)
@login_required
def lawyer_dashboard(request):
    # Your lawyer dashboard logic here
    return render(request, 'accounts/lawyer_dashboard.html')

@login_required
def donor_dashboard(request):
    # Your donor dashboard logic here
    return render(request, 'accounts/donor_dashboard.html')

# Simple redirect function based on user role
@login_required
def dashboard(request):
    user = request.user
    if user.role == 'NGO':
        return redirect('accounts:ngo_dashboard')
    elif user.role == 'LAWYER':
        return redirect('accounts:lawyer_dashboard')
    elif user.role == 'DONOR':
        return redirect('accounts:donor_dashboard')
    return redirect('accounts:profile')  # Fallback

@login_required
def settings_view(request):
    # Your settings page logic here
    return render(request, 'accounts/settings.html')

@login_required
def logout_view(request):
    """Custom logout view with additional functionality"""
    logout(request)
    messages.success(request, 'You have been successfully logged out.')
    return redirect('accounts:login')