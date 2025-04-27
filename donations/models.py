from django.db import models
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic.edit import CreateView
from django.urls import reverse_lazy
from django.shortcuts import redirect
from django.contrib import messages

from accounts.models import DonorProfile, User
from cases.models import Case
from django.conf import settings



class Donation(models.Model):
    donor = models.ForeignKey(DonorProfile, on_delete=models.CASCADE, related_name='donations')
    case = models.ForeignKey(Case, on_delete=models.CASCADE, related_name='donations')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    transaction_id = models.CharField(max_length=100, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    anonymous = models.BooleanField(default=False)  # Correct field name
    message = models.TextField(blank=True)
   
    def __str__(self):
        if self.anonymous:
            return f"Anonymous donation of {self.amount} to {self.case.title}"
        return f"Donation of {self.amount} by {self.donor.user.username} to {self.case.title}"

class DonateView(LoginRequiredMixin, CreateView):
    model = Donation
    fields = ['amount', 'anonymous', 'message']
    template_name = 'cases/donate.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['case'] = Case.objects.get(pk=self.kwargs['case_id'])
        return context
    
    def form_valid(self, form):
        form.instance.donor = self.request.user.donor_profile
        form.instance.case = Case.objects.get(pk=self.kwargs['case_id'])
        
        # Update the case's funding_received
        case = form.instance.case
        case.funding_received += form.instance.amount
        case.save()
        
        # Send SMS notification
        case_owner = case.ngo.user
        donation_msg = f"Good news! Your case '{case.title}' has received a donation of {form.instance.amount}."
        send_sms(case_owner.phone_number, donation_msg)
        
        messages.success(self.request, 'Thank you for your donation!')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('cases:case_detail', kwargs={'pk': self.kwargs['case_id']})
        
    def dispatch(self, request, *args, **kwargs):
        if request.user.role != 'DONOR':
            messages.error(request, 'Only donors can make donations')
            return redirect('accounts:dashboard')
        return super().dispatch(request, *args, **kwargs)
    
class Comment(models.Model):
    case = models.ForeignKey(Case, related_name='comments', on_delete=models.CASCADE)
    donor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    text = models.TextField()
    is_anonymous = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Comment by {self.donor.username if self.donor else 'Anonymous'} on {self.case.title}"