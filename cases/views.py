from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponseForbidden
from django.core.paginator import Paginator
from django.core.mail import send_mail
from django.conf import settings
from django.urls import reverse
from .models import Case, CaseDocument, CaseUpdate, LawyerApplication, CaseCategory
from .forms import CaseForm, CaseDocumentForm, CaseUpdateForm, InviteLawyerForm
from accounts.models import LawyerProfile, NGOProfile

@login_required
def ngo_dashboard(request):
    """NGO dashboard showing case overview"""
    if not hasattr(request.user, 'ngo'):
        return HttpResponseForbidden("You must be an NGO to access this page")
    
    cases = Case.objects.filter(ngo=request.user.ngo).order_by('-created_at')
    
    # Count cases by status
    open_cases = cases.filter(status='open').count()
    in_progress_cases = cases.filter(status='in_progress').count()
    completed_cases = cases.filter(status='completed').count()
    
    context = {
        'cases': cases[:5],  # Show only 5 recent cases
        'open_cases': open_cases,
        'in_progress_cases': in_progress_cases,
        'completed_cases': completed_cases,
        'total_cases': cases.count(),
    }
    
    return render(request, 'cases/ngo/dashboard.html', context)

@login_required
def list_cases(request):
    """List all cases for the NGO"""
    if not hasattr(request.user, 'ngo'):
        return HttpResponseForbidden("You must be an NGO to access this page")
    
    cases = Case.objects.filter(ngo=request.user.ngo).order_by('-created_at')
    
    # Filter cases by status if requested
    status_filter = request.GET.get('status', '')
    if status_filter:
        cases = cases.filter(status=status_filter)
    
    # Pagination
    paginator = Paginator(cases, 10)  # 10 cases per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'status_filter': status_filter,
    }
    
    return render(request, 'cases/ngo/list_cases.html', context)

@login_required
def create_case(request):
    """Create a new case"""
    if not hasattr(request.user, 'ngo'):
        return HttpResponseForbidden("You must be an NGO to access this page")
    
    if request.method == 'POST':
        form = CaseForm(request.POST)
        if form.is_valid():
            case = form.save(commit=False)
            case.ngo = request.user.ngo
            case.save()
            messages.success(request, "Case created successfully!")
            return redirect('cases:case_detail', pk=case.pk)
    else:
        form = CaseForm()
    
    context = {
        'form': form,
        'categories': CaseCategory.objects.all(),
    }
    
    return render(request, 'cases/ngo/create_case.html', context)

@login_required
def case_detail(request, pk):
    """View a specific case with all details"""
    case = get_object_or_404(Case, pk=pk)
    
    # Check if user is authorized to view this case
    if not (hasattr(request.user, 'ngo') and request.user.ngo == case.ngo) and not hasattr(request.user, 'lawyer'):
        return HttpResponseForbidden("You don't have permission to view this case")
    
    # Get all documents and updates for this case
    documents = case.documents.all()
    updates = case.updates.all()
    
    # Get lawyer applications if user is the NGO
    applications = None
    if hasattr(request.user, 'ngo') and request.user.ngo == case.ngo:
        applications = case.applications.all()
    
    context = {
        'case': case,
        'documents': documents,
        'updates': updates,
        'applications': applications,
        'total_donations': case.total_donations(),
    }
    
    return render(request, 'cases/ngo/case_detail.html', context)

@login_required
def edit_case(request, pk):
    """Edit an existing case"""
    case = get_object_or_404(Case, pk=pk)
    
    # Check if user is authorized to edit this case
    if not hasattr(request.user, 'ngo') or request.user.ngo != case.ngo:
        return HttpResponseForbidden("You don't have permission to edit this case")
    
    if request.method == 'POST':
        form = CaseForm(request.POST, instance=case)
        if form.is_valid():
            form.save()
            messages.success(request, "Case updated successfully!")
            return redirect('cases:case_detail', pk=case.pk)
    else:
        form = CaseForm(instance=case)
    
    context = {
        'form': form,
        'case': case,
        'categories': CaseCategory.objects.all(),
    }
    
    return render(request, 'cases/ngo/edit_case.html', context)

@login_required
def upload_document(request, case_pk):
    """Upload a document to a case"""
    case = get_object_or_404(Case, pk=case_pk)
    
    # Check if user is authorized to upload document
    if not (hasattr(request.user, 'ngo') and request.user.ngo == case.ngo) and not (
            hasattr(request.user, 'lawyer') and 
            hasattr(case, 'assigned_lawyer') and 
            request.user.lawyer == case.assigned_lawyer
        ):
        return HttpResponseForbidden("You don't have permission to upload documents to this case")
    
    if request.method == 'POST':
        form = CaseDocumentForm(request.POST, request.FILES)
        if form.is_valid():
            document = form.save(commit=False)
            document.case = case
            document.uploaded_by = request.user
            document.save()
            messages.success(request, "Document uploaded successfully!")
            return redirect('cases:case_detail', pk=case.pk)
    else:
        form = CaseDocumentForm()
    
    context = {
        'form': form,
        'case': case,
    }
    
    return render(request, 'cases/upload_document.html', context)

@login_required
def add_update(request, case_pk):
    """Add an update to a case"""
    case = get_object_or_404(Case, pk=case_pk)
    
    # Check if user is authorized to add updates
    if not (hasattr(request.user, 'ngo') and request.user.ngo == case.ngo) and not (
            hasattr(request.user, 'lawyer') and 
            hasattr(case, 'assigned_lawyer') and 
            request.user.lawyer == case.assigned_lawyer
        ):
        return HttpResponseForbidden("You don't have permission to add updates to this case")
    
    if request.method == 'POST':
        form = CaseUpdateForm(request.POST)
        if form.is_valid():
            update = form.save(commit=False)
            update.case = case
            update.created_by = request.user
            update.save()
            messages.success(request, "Update added successfully!")
            return redirect('cases:case_detail', pk=case.pk)
    else:
        form = CaseUpdateForm()
    
    context = {
        'form': form,
        'case': case,
    }
    
    return render(request, 'cases/add_update.html', context)

@login_required
def view_applications(request, case_pk):
    """View all lawyer applications for a case"""
    case = get_object_or_404(Case, pk=case_pk)
    
    # Check if user is authorized to view applications
    if not hasattr(request.user, 'ngo') or request.user.ngo != case.ngo:
        return HttpResponseForbidden("You don't have permission to view applications for this case")
    
    applications = case.applications.all().select_related('lawyer', 'lawyer__user')
    
    context = {
        'case': case,
        'applications': applications,
    }
    
    return render(request, 'cases/ngo/view_applications.html', context)

@login_required
def update_application_status(request, application_pk, status):
    """Update status of a lawyer application (shortlist, accept, reject)"""
    application = get_object_or_404(LawyerApplication, pk=application_pk)
    
    # Check if user is authorized to update application status
    if not hasattr(request.user, 'ngo') or request.user.ngo != application.case.ngo:
        return HttpResponseForbidden("You don't have permission to update this application")
    
    if status == 'shortlist':
        application.status = 'shortlisted'
        application.case.shortlisted_lawyers.add(application.lawyer)
        message = "Lawyer has been shortlisted!"
    elif status == 'accept':
        application.status = 'accepted'
        application.case.assigned_lawyer = application.lawyer
        application.case.status = 'assigned'
        application.case.save()
        message = f"Case has been assigned to {application.lawyer.user.get_full_name()}!"
        
        # Send email notification to the lawyer
        send_mail(
            f'You have been assigned to case: {application.case.title}',
            f'Your application has been accepted for the case "{application.case.title}". Please log in to the platform to view the details.',
            settings.DEFAULT_FROM_EMAIL,
            [application.lawyer.user.email],
            fail_silently=False,
        )
    elif status == 'reject':
        application.status = 'rejected'
        message = "Application has been rejected."
    else:
        messages.error(request, "Invalid action!")
        return redirect('cases:view_applications', case_pk=application.case.pk)
    
    application.save()
    messages.success(request, message)
    return redirect('cases:view_applications', case_pk=application.case.pk)

@login_required
def invite_lawyer(request, case_pk):
    """Directly invite a lawyer to a case"""
    case = get_object_or_404(Case, pk=case_pk)
    
    # Check if user is authorized to invite lawyers
    if not hasattr(request.user, 'ngo') or request.user.ngo != case.ngo:
        return HttpResponseForbidden("You don't have permission to invite lawyers to this case")
    
    if request.method == 'POST':
        form = InviteLawyerForm(request.POST)
        if form.is_valid():
            lawyer_id = form.cleaned_data['lawyer']
            lawyer = get_object_or_404(LawyerProfile, pk=lawyer_id)
            
            # Create an application for the lawyer
            LawyerApplication.objects.create(
                case=case,
                lawyer=lawyer,
                cover_letter="Invited directly by NGO",
                status='accepted'
            )
            
            # Update case status
            case.assigned_lawyer = lawyer
            case.status = 'assigned'
            case.save()
            
            # Send email notification to the lawyer
            send_mail(
                f'You have been invited to a case: {case.title}',
                f'You have been directly invited to work on the case "{case.title}". Please log in to the platform to view the details.',
                settings.DEFAULT_FROM_EMAIL,
                [lawyer.user.email],
                fail_silently=False,
            )
            
            messages.success(request, f"Lawyer {lawyer.user.get_full_name()} has been invited to this case!")
            return redirect('cases:case_detail', pk=case.pk)
    else:
        form = InviteLawyerForm()
    
    context = {
        'form': form,
        'case': case,
    }
    
    return render(request, 'cases/ngo/invite_lawyer.html', context)

@login_required
def review_completed_case(request, pk):
    """Review and approve a completed case"""
    case = get_object_or_404(Case, pk=pk)
    
    # Check if user is authorized to review this case
    if not hasattr(request.user, 'ngo') or request.user.ngo != case.ngo:
        return HttpResponseForbidden("You don't have permission to review this case")
    
    # Check if case is ready for review
    if case.status != 'review':
        messages.error(request, "This case is not ready for review yet.")
        return redirect('cases:case_detail', pk=case.pk)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'approve':
            case.status = 'completed'
            case.save()
            
            # Send notification to lawyer about bounty release
            send_mail(
                f'Case Approved: {case.title}',
                f'Your work on the case "{case.title}" has been approved. The bounty will be released shortly.',
                settings.DEFAULT_FROM_EMAIL,
                [case.assigned_lawyer.user.email],
                fail_silently=False,
            )
            
            messages.success(request, "Case has been approved and marked as completed!")
        elif action == 'request_changes':
            feedback = request.POST.get('feedback')
            case.status = 'in_progress'
            case.save()
            
            # Create an update with the feedback
            CaseUpdate.objects.create(
                case=case,
                created_by=request.user,
                content=f"Changes requested: {feedback}"
            )
            
            # Notify lawyer about requested changes
            send_mail(
                f'Changes Requested: {case.title}',
                f'The NGO has requested changes for the case "{case.title}". Please log in to view the feedback.',
                settings.DEFAULT_FROM_EMAIL,
                [case.assigned_lawyer.user.email],
                fail_silently=False,
            )
            
            messages.success(request, "Changes have been requested. The case has been returned to in-progress status.")
        
        return redirect('cases:case_detail', pk=case.pk)
    
    context = {
        'case': case,
    }
    
    return render(request, 'cases/ngo/review_case.html', context)

@login_required
def view_donations(request, case_pk):
    """View donations for a specific case"""
    case = get_object_or_404(Case, pk=case_pk)
    
    # Check if user is authorized to view donations
    if not hasattr(request.user, 'ngo') or request.user.ngo != case.ngo:
        return HttpResponseForbidden("You don't have permission to view donations for this case")
    
    # Import here to avoid circular imports
    from donation.models import Donation
    
    donations = Donation.objects.filter(case=case).order_by('-created_at')
    total_amount = sum(donation.amount for donation in donations)
    
    context = {
        'case': case,
        'donations': donations,
        'total_amount': total_amount,
    }
    
    return render(request, 'cases/ngo/view_donations.html', context)