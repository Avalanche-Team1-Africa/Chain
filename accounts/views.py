import random
import string
import africastalking
from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib import messages
from django.views.generic import CreateView, UpdateView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from django.conf import settings

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
    success_url = reverse_lazy('verify_email')  # Go to verify page

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
        return redirect('verify_email')


class VerifyEmailView(UpdateView):
    model = User
    fields = ['verification_code']
    template_name = 'accounts/verify_email.html'
    success_url = reverse_lazy('profile_setup')

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
    success_url = reverse_lazy('dashboard')

    def get_object(self):
        user = self.request.user
        if user.role == 'NGO':
            return user.ngo_profile
        elif user.role == 'LAWYER':
            return user.lawyer_profile
        elif user.role == 'DONOR':
            return user.donor_profile

    def get_form_class(self):
        user = self.request.user
        if user.role == 'NGO':
            return NGOProfileForm
        elif user.role == 'LAWYER':
            return LawyerProfileForm
        elif user.role == 'DONOR':
            return DonorProfileForm

    def form_valid(self, form):
        messages.success(self.request, 'Profile updated successfully!')
        return super().form_valid(form)
