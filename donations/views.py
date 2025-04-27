from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponseForbidden
from django.core.paginator import Paginator
from django.db.models import Sum
from functools import wraps

from cases.models import Case
from .models import Donation, Comment
from .forms import DonationForm, CommentForm


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


@login_required
@donor_required
def donate_to_case(request, case_pk):
    """
    Allows donors to donate to a specific case.
    Respects anonymous donation preferences.
    """
    case = get_object_or_404(Case, pk=case_pk)
    donor_profile = request.user.donor_profile

    if request.method == 'POST':
        form = DonationForm(request.POST)
        if form.is_valid():
            donation = form.save(commit=False)
            donation.case = case
            donation.donor = donor_profile
            donation.anonymous = form.cleaned_data.get('is_anonymous', False)
            donation.save()

            messages.success(request, "Thank you for your donation!")
            return redirect('donations:case_detail', pk=case.pk)
    else:
        form = DonationForm(initial={'is_anonymous': donor_profile.allow_anonymous})

    context = {
        'form': form,
        'case': case,
    }
    return render(request, 'donations/donate.html', context)


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