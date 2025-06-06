from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponseForbidden
from django.core.paginator import Paginator
from django.db.models import Sum
from functools import wraps
import json
from django.views.decorators.csrf import csrf_exempt
import requests
from .mpesa_utils import get_mpesa_access_token, generate_password
from django.conf import settings
from django.urls import reverse
import uuid  
from django.http import JsonResponse

from cases.models import Case
from .models import Donation, Comment
from .forms import DonationForm, CommentForm
from django.utils import timezone
from cases.utils import award_tokens
# Utility function to generate a unique reference
def generate_reference():
    """
    Generates a unique reference string using UUID.
    """
    return str(uuid.uuid4())

# Decorator to enforce donor access
# Decorator to enforce donor access
def donor_required(view_func):
    """
    Ensures that only authenticated users with a donor profile can access the view.
    Redirects unauthenticated users to the login page.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        user = request.user
        if not user.is_authenticated:
            return redirect('login')  # Redirect to login if not authenticated
        if not hasattr(user, 'donor_profile') or user.role != 'DONOR':
            return HttpResponseForbidden("You must be a donor to access this page.")
        return view_func(request, *args, **kwargs)
    return _wrapped_view


@login_required
@donor_required
def browse_cases(request):
    """
    View for donors to browse available cases.
    Supports filtering by category and urgency with pagination.
    """
    cases = Case.objects.filter(status__in=['open', 'in_progress']).order_by('-created_at')

    # Apply filters
    category_filter = request.GET.get('category', '')
    urgency_filter = request.GET.get('urgency', '')
    
    if category_filter:
        cases = cases.filter(category__id=category_filter)
    if urgency_filter:
        cases = cases.filter(urgency=urgency_filter)

    paginator = Paginator(cases, 10)  # 10 cases per page
    page_obj = paginator.get_page(request.GET.get('page'))

    context = {
        'page_obj': page_obj,
        'category_filter': category_filter,
        'urgency_filter': urgency_filter,
    }
    return render(request, 'donations/browse_cases.html', context)


def donate_to_case(request, case_pk):
    case = get_object_or_404(Case, pk=case_pk)
    donor_profile = request.user.donor_profile
    
    if request.method == 'POST':
        form = DonationForm(request.POST)
        if form.is_valid():
            reference = generate_reference()  # Generate a unique reference
            email = form.cleaned_data['email']
            anonymous = form.cleaned_data.get('is_anonymous', False)
            message = form.cleaned_data.get('message', '')
            payment_method = form.cleaned_data.get('payment_method', 'PAYSTACK')
            phone_number = form.cleaned_data.get('phone_number', '')
            
            # Generate a unique reference
            reference = generate_reference()
            
            # Save donation with status as PENDING
            donation = Donation.objects.create(
                case=case,
                donor=donor_profile,
                amount=form.cleaned_data['amount'],
                anonymous=anonymous,
                payment_status='PENDING',
                payment_method=payment_method,
                reference=reference,
                message=message,
                email=email,
            )
            
            # Initiate payment via Paystack
            headers = {
                "Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}",
                "Content-Type": "application/json"
            }
            
            # Convert amount to the smallest currency unit (e.g., cents, kobo)
            amount_in_smallest_unit = int(float(form.cleaned_data['amount']) * 1)
            
            # Base payload for all payment methods
            payload = {
                "email": email,
                "amount": amount_in_smallest_unit,
                "reference": reference,
                "callback_url": request.build_absolute_uri(reverse('donations:paystack_callback')),
                "metadata": {
                    "donation_id": donation.id,
                    "case_id": case.id,
                    "payment_method": payment_method,
                    "custom_fields": [
                        {
                            "display_name": "Donation For",
                            "variable_name": "donation_for",
                            "value": case.title
                        }
                    ]
                }
            }
            
            # Add M-Pesa specific details if that's the chosen payment method
            if payment_method == 'MPESA':
                # Format the phone number correctly for M-Pesa
                formatted_phone = phone_number
                if not phone_number.startswith('+'):
                    formatted_phone = '+' + phone_number
                    
                # Add M-Pesa mobile money details
                payload["mobile_money"] = {
                    "phone": formatted_phone,
                    "provider": "mpesa"
                }
                
                # You may need to add a country-specific currency code
                payload["currency"] = "KES"  # Kenya Shillings for M-Pesa
            
            try:
                response = requests.post(
                    "https://api.paystack.co/transaction/initialize",
                    json=payload,
                    headers=headers
                )
                
                response_data = response.json()
                
                if response_data.get('status'):
                    # Redirect to Paystack payment page
                    payment_url = response_data['data']['authorization_url']
                    return redirect(payment_url)
                else:
                    messages.error(request, f"Failed to initiate payment: {response_data.get('message')}")
                    return redirect('donations:donate_to_case', case_pk=case.pk)
            except Exception as e:
                messages.error(request, f"An error occurred: {str(e)}")
                return redirect('donations:donate_to_case', case_pk=case.pk)
    else:
        form = DonationForm(initial={'is_anonymous': donor_profile.allow_anonymous})
    
    context = {
        'form': form,
        'case': case,
    }
    return render(request, 'donations/donate.html', context)


# Update the paystack_callback function to handle M-Pesa specific responses

@csrf_exempt
def paystack_callback(request):
    """Handle Paystack callback (including M-Pesa transactions)"""
    if request.method == 'GET':
        # Handle redirect from Paystack after payment
        reference = request.GET.get('reference')
        if reference:
            # Verify the transaction
            headers = {
                "Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}"
            }
            
            response = requests.get(
                f"https://api.paystack.co/transaction/verify/{reference}",
                headers=headers
            )
            
            response_data = response.json()
            
            if response_data.get('status'):
                transaction_status = response_data['data']['status']
                payment_method = response_data['data'].get('channel', '').upper()
                
                # Check if this is an M-Pesa transaction (could be labeled as 'mobile_money' in response)
                if 'mobile_money' in response_data['data'].get('authorization', {}).get('channel', '').lower() or \
                   'mpesa' in response_data['data'].get('authorization', {}).get('channel', '').lower():
                    payment_method = 'MPESA'
                
                try:
                    donation = Donation.objects.get(reference=reference)
                    
                    # For M-Pesa, the transaction might be 'pending' even after callback
                    # This is because M-Pesa might take some time to confirm
                    if transaction_status == 'success':
                        donation.payment_status = 'COMPLETED'
                        messages.success(request, "Thank you! Your donation was successful.")
                    elif transaction_status == 'pending' and payment_method == 'MPESA':
                        donation.payment_status = 'PENDING'
                        messages.info(request, "Your M-Pesa payment is being processed. You will receive a confirmation once completed.")
                    else:
                        donation.payment_status = 'FAILED'
                        messages.error(request, "Payment was not successful. Please try again.")
                    
                    donation.amount_received = float(response_data['data']['amount']) / 100  # Convert from smallest currency unit
                    donation.callback_response = response_data
                    donation.transaction_id = response_data['data'].get('id', '')
                    donation.payment_method = payment_method  # Update to the actual payment method used
                    donation.save()
                    
                    return redirect('donations:case_detail', pk=donation.case.pk)
                except Donation.DoesNotExist:
                    messages.error(request, "We could not find your donation. Please contact support.")
            else:
                messages.error(request, "Payment verification failed. Please try again or contact support.")
        
        # Fallback to home page if no reference or failed verification
        return redirect('home')
    
    # Handle webhook (POST requests)
    elif request.method == 'POST':
        payload = json.loads(request.body)
        event = payload.get('event')
        
        if event in ['charge.success', 'transfer.success', 'mobilecharge.success']:
            data = payload.get('data', {})
            reference = data.get('reference')
            
            try:
                donation = Donation.objects.get(reference=reference)
                
                # Determine the payment method from the response
                payment_method = data.get('channel', '').upper()
                if 'mobile_money' in data.get('authorization', {}).get('channel', '').lower() or \
                   'mpesa' in data.get('authorization', {}).get('channel', '').lower():
                    payment_method = 'MPESA'
                
                # Update donation information
                donation.payment_status = 'COMPLETED'
                donation.amount_received = float(data.get('amount', 0)) / 100  # Convert from smallest currency unit
                donation.callback_response = data
                donation.transaction_id = data.get('id', '')
                donation.payment_method = payment_method
                donation.save()
                
                # You might want to send a confirmation email here
                
            except Donation.DoesNotExist:
                # Log the error but return success to Paystack
                pass
        
        return JsonResponse({'status': 'success'})
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})


@csrf_exempt
def paystack_webhook(request):
    """Handle Paystack webhook events including M-Pesa transactions"""
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Invalid request method'})
    
    # Verify webhook signature if Paystack provides this feature
    # Read request body
    payload = json.loads(request.body)
    
    # Process different event types
    event = payload.get('event')
    
    if event in ['charge.success', 'transfer.success', 'mobilecharge.success']:
        # Process successful payment
        data = payload.get('data', {})
        reference = data.get('reference')
        
        try:
            donation = Donation.objects.get(reference=reference)
            if donation.payment_status != 'COMPLETED':
                # Determine the payment method from the response
                payment_method = data.get('channel', '').upper()
                if 'mobile_money' in data.get('authorization', {}).get('channel', '').lower() or \
                   'mpesa' in data.get('authorization', {}).get('channel', '').lower():
                    payment_method = 'MPESA'
                
                donation.payment_status = 'COMPLETED'
                donation.amount_received = float(data.get('amount', 0)) / 100  # Convert from smallest currency unit
                donation.callback_response = data
                donation.transaction_id = data.get('id', '')
                donation.payment_method = payment_method
                donation.save()
                
                # Send confirmation email/SMS for successful payment
                try:
                    # You can implement email/SMS sending logic here
                    pass
                except Exception as e:
                    # Log the error but continue processing
                    pass
        except Donation.DoesNotExist:
            # Log this unusual situation but return success to Paystack
            pass
    
    return JsonResponse({'status': 'success'})

@login_required
@donor_required
def case_detail(request, pk):
    """
    Displays detailed information about a case, including donations and comments.
    Allows donors to add comments.
    """
    case = get_object_or_404(Case, pk=pk)
    total_donations = case.donations.aggregate(Sum('amount'))['amount__sum'] or 0
    comments = case.comments.all()

    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.case = case
            if not form.cleaned_data['is_anonymous']:
                comment.donor = request.user
            comment.save()

            messages.success(request, "Your comment has been added.")
            return redirect('donations:case_detail', pk=case.pk)
    else:
        form = CommentForm(initial={
            'is_anonymous': request.user.donor_profile.allow_anonymous
        })

    context = {
        'case': case,
        'total_donations': total_donations,
        'comments': comments,
        'form': form,
    }
    return render(request, 'donations/case_detail.html', context)


@login_required
@donor_required
def my_donations(request):
    """
    Displays all donations made by the current donor.
    """
    donor_profile = request.user.donor_profile
    donations = Donation.objects.filter(donor=donor_profile).order_by('-timestamp')

    context = {
        'donations': donations,
    }
    return render(request, 'donations/my_donations.html', context)




@login_required
def process_donation(request, case_pk):
    case = get_object_or_404(Case, pk=case_pk)
    if request.user.role != 'DONOR' or not hasattr(request.user, 'donor_profile'):
        return HttpResponseForbidden("You must be a donor to make donations")
    
    if request.method == 'POST':
        amount = float(request.POST.get('amount', 0))
        if amount <= 0:
            messages.error(request, "Invalid donation amount")
            return redirect('donations:browse_cases')
        
        # Process payment (e.g., via Stripe or PayPal)
        # Assuming payment is successful...
        
        # Create donation record
        donation = Donation.objects.create(
            case=case,
            donor=request.user,
            amount=amount,
            created_at=timezone.now()
        )
        
        # Award tokens based on donation amount (1 token per $10)
        token_amount = amount // 10
        if token_amount > 0:
            award_tokens(
                user=request.user,
                amount=token_amount,
                description=f"Donated ${amount} to case: {case.title}",
                case=case
            )
        
        messages.success(request, "Thank you for your donation!")
        return redirect('donations:browse_cases')
    
    context = {
        'case': case,
    }
    return render(request, 'donations/process_donation.html', context)


