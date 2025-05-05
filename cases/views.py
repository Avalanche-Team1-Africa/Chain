from datetime import timezone
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponseForbidden
from django.core.paginator import Paginator
from django.core.mail import send_mail
from django.conf import settings
from django.urls import reverse
from django.db.models import Avg
from django.db.models import Q
from accounts import models
from .models import (
    Case,
    CaseDocument,
    CaseUpdate,
    CaseMilestone,
    LawyerApplication,
    CaseCategory,
    LawyerApplication, 
    CaseUpdate,
    SuccessStory, 
    LawyerRating
)
from .forms import (
    CaseForm,
    CaseDocumentForm,
    CaseUpdateForm,
    InviteLawyerForm,
    LawyerApplicationForm,
    CaseProgressForm,
    CaseCompletionForm,
    SuccessStoryForm
)
from accounts.models import LawyerProfile, NGOProfile,DonorProfile


@login_required
def ngo_dashboard(request):
    """NGO dashboard showing case overview"""
    if request.user.role != 'NGO' or not hasattr(request.user, 'ngo_profile'):
        return HttpResponseForbidden("You must be an NGO to access this page")
    cases = Case.objects.filter(ngo=request.user).order_by('-created_at')
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
    if request.user.role != 'NGO' or not hasattr(request.user, 'ngo_profile'):
        return HttpResponseForbidden("You must be an NGO to access this page")
    cases = Case.objects.filter(ngo=request.user).order_by('-created_at')
    status_filter = request.GET.get('status', '')
    if status_filter:
        cases = cases.filter(status=status_filter)
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
    """Create a new case with milestones"""
    if request.user.role != 'NGO' or not hasattr(request.user, 'ngo_profile'):
        return HttpResponseForbidden("You must be an NGO to access this page")
    
    if request.method == 'POST':
        form = CaseForm(request.POST)
        if form.is_valid():
            # Save the case first
            case = form.save(commit=False)
            case.ngo = request.user
            case.save()
            
            # Process milestone data
            milestone_count = int(request.POST.get('milestone_count', 0))
            for i in range(milestone_count):
                if f'milestone_title_{i}' not in request.POST:
                    continue
                title = request.POST.get(f'milestone_title_{i}')
                description = request.POST.get(f'milestone_description_{i}', '')
                target_date = request.POST.get(f'milestone_date_{i}')
                
                if title and target_date:  # Only create if there's at least a title and date
                    CaseMilestone.objects.create(
                        case=case,
                        title=title,
                        description=description,
                        target_date=target_date,
                        status='pending'
                    )
            
            messages.success(request, "Case created successfully with milestones!")
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
    is_case_ngo = (request.user == case.ngo)
    is_lawyer = (request.user.role == 'LAWYER' and hasattr(request.user, 'lawyer_profile'))
    if not (is_case_ngo or is_lawyer):
        return HttpResponseForbidden("You don't have permission to view this case")
    documents = case.documents.all()
    updates = case.updates.all()
    applications = None
    if is_case_ngo:
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
    if request.user != case.ngo or request.user.role != 'NGO':
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
def case_history(request, pk):
    """View the history of changes and updates for a case"""
    case = get_object_or_404(Case, pk=pk)
    
    # Check permissions - only NGO associated with the case should access it
    if request.user != case.ngo and request.user.role != 'NGO':
        return HttpResponseForbidden("You don't have permission to view this case history")
    
    # Get all case updates in chronological order
    case_updates = case.updates.all().order_by('-created_at')
    
    # Get all document uploads in chronological order
    documents = case.documents.all().order_by('-uploaded_at')
    
    # Combine all activities for the case timeline
    # You might need to adjust this based on your models
    activities = []
    
    # Add case creation as first activity
    activities.append({
        'type': 'creation',
        'date': case.created_at,
        'description': f"Case was created by {case.ngo.get_full_name()}",
        'icon': 'fa-folder-plus'
    })
    
    # Add updates
    for update in case_updates:
        activities.append({
            'type': 'update',
            'date': update.created_at,
            'description': update.content,
            'author': update.author.get_full_name() if update.author else "System",
            'icon': 'fa-pen'
        })
    
    # Add document uploads
    for doc in documents:
        activities.append({
            'type': 'document',
            'date': doc.uploaded_at,
            'description': f"Document '{doc.name}' was uploaded",
            'author': doc.uploaded_by.get_full_name() if doc.uploaded_by else "System",
            'icon': 'fa-file-alt'
        })
    
    # Add status changes if you track them
    # (You'd need a model that tracks status changes)
    
    # Sort all activities by date, newest first
    activities.sort(key=lambda x: x['date'], reverse=True)
    
    context = {
        'case': case,
        'activities': activities,
    }
    
    return render(request, 'cases/ngo/case_history.html', context)


@login_required
def upload_document(request, case_pk):
    """Upload a document to a case"""
    case = get_object_or_404(Case, pk=case_pk)
    is_case_ngo = (request.user == case.ngo)
    is_assigned_lawyer = (
        request.user.role == 'LAWYER' and
        hasattr(request.user, 'lawyer_profile') and
        case.assigned_lawyer and
        request.user.lawyer_profile == case.assigned_lawyer
    )
    if not (is_case_ngo or is_assigned_lawyer):
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
    is_case_ngo = (request.user == case.ngo)
    is_assigned_lawyer = (
        request.user.role == 'LAWYER' and
        hasattr(request.user, 'lawyer_profile') and
        case.assigned_lawyer and
        request.user.lawyer_profile == case.assigned_lawyer
    )
    if not (is_case_ngo or is_assigned_lawyer):
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
    if request.user != case.ngo or request.user.role != 'NGO':
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
    if request.user != application.case.ngo or request.user.role != 'NGO':
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
def invite_lawyers(request, case_pk):
    """NGO invites a lawyer directly to a case."""
    case = get_object_or_404(Case, pk=case_pk)

    # Check if current user is the NGO owner
    if request.user != case.ngo or request.user.role != 'NGO':
        return HttpResponseForbidden("You don't have permission to invite lawyers to this case.")

    if request.method == 'POST':
        form = InviteLawyerForm(request.POST)
        if form.is_valid():
            # Get lawyer ID from form (form should be a ChoiceField or ModelChoiceField)
            lawyer = form.cleaned_data['lawyer']  # Now lawyer is already a LawyerProfile instance!

            # Check if application already exists (optional but good)
            application_exists = LawyerApplication.objects.filter(case=case, lawyer=lawyer).exists()
            if application_exists:
                messages.warning(request, f"Lawyer {lawyer.user.get_full_name()} has already been invited or applied.")
                return redirect('cases:case_detail', pk=case.pk)

            # Create the Lawyer Application
            LawyerApplication.objects.create(
                case=case,
                lawyer=lawyer,
                cover_letter="Invited directly by NGO",
                status='accepted'
            )

            # Update the Case
            case.assigned_lawyer = lawyer
            case.status = 'assigned'
            case.save()

            # Notify the Lawyer
            send_mail(
                subject=f"You've been invited to a case: {case.title}",
                message=f"Hello {lawyer.user.get_full_name()},\n\nYou have been invited to work on the case '{case.title}'. Please log in to view the case details.\n\nBest regards,\nThe Team",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[lawyer.user.email],
                fail_silently=False,
            )

            messages.success(request, f"Lawyer {lawyer.user.get_full_name()} has been invited successfully.")
            return redirect('cases:case_detail', pk=case.pk)
    else:
        form = InviteLawyerForm()

    context = {
        'case': case,
        'form': form,
    }
    return render(request, 'cases/ngo/invite_lawyer.html', context)
@login_required
def review_completed_case(request, pk):
    """Review and approve a completed case"""
    case = get_object_or_404(Case, pk=pk)
    if request.user != case.ngo or request.user.role != 'NGO':
        return HttpResponseForbidden("You don't have permission to review this case")
    if case.status != 'review':
        messages.error(request, "This case is not ready for review yet.")
        return redirect('cases:case_detail', pk=case.pk)
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'approve':
            case.status = 'completed'
            case.save()
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
            CaseUpdate.objects.create(
                case=case,
                created_by=request.user,
                content=f"Changes requested: {feedback}"
            )
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
def set_milestones(request, case_pk):
    """Set or update milestones for a case"""
    case = get_object_or_404(Case, pk=case_pk)
    if request.user != case.ngo or request.user.role != 'NGO':
        return HttpResponseForbidden("You don't have permission to set milestones for this case")
    milestones = case.milestones.all().order_by('target_date')
    if request.method == 'POST':
        milestone_count = int(request.POST.get('milestone_count', 0))
        existing_milestone_ids = []
        for i in range(milestone_count):
            if f'milestone_title_{i}' not in request.POST:
                continue
            title = request.POST.get(f'milestone_title_{i}')
            description = request.POST.get(f'milestone_description_{i}', '')
            target_date = request.POST.get(f'milestone_date_{i}')
            status = request.POST.get(f'milestone_status_{i}', 'pending')
            milestone_id = request.POST.get(f'milestone_id_{i}', None)
            if milestone_id:
                try:
                    milestone = CaseMilestone.objects.get(pk=milestone_id, case=case)
                    milestone.title = title
                    milestone.description = description
                    milestone.target_date = target_date
                    milestone.status = status
                    milestone.save()
                    existing_milestone_ids.append(milestone.id)
                except CaseMilestone.DoesNotExist:
                    milestone = CaseMilestone.objects.create(
                        case=case,
                        title=title,
                        description=description,
                        target_date=target_date,
                        status=status
                    )
                    existing_milestone_ids.append(milestone.id)
            else:
                milestone = CaseMilestone.objects.create(
                    case=case,
                    title=title,
                    description=description,
                    target_date=target_date,
                    status=status
                )
                existing_milestone_ids.append(milestone.id)
        case.milestones.exclude(id__in=existing_milestone_ids).delete()
        messages.success(request, "Milestones updated successfully!")
        return redirect('cases:case_detail', pk=case.pk)
    context = {
        'case': case,
        'milestones': milestones,
    }
    return render(request, 'cases/ngo/set_milestones.html', context)


@login_required
def view_donations(request, case_pk):
    """View donations for a specific case"""
    case = get_object_or_404(Case, pk=case_pk)
    if request.user != case.ngo or request.user.role != 'NGO':
        return HttpResponseForbidden("You don't have permission to view donations for this case")
    from donation.models import Donation
    donations = Donation.objects.filter(case=case).order_by('-created_at')
    total_amount = sum(donation.amount for donation in donations)
    context = {
        'case': case,
        'donations': donations,
        'total_amount': total_amount,
    }
    return render(request, 'cases/ngo/view_donations.html', context)


@login_required
def redirect_browse_cases(request):
    """Redirect to the appropriate browse cases view based on user role"""
    if hasattr(request.user, 'donor_profile') and request.user.role == 'DONOR':
        return redirect('donations:browse_cases')
    elif hasattr(request.user, 'lawyer_profile') and request.user.role == 'LAWYER':
        return redirect('cases:lawyer_browse_cases')
    else:
        return HttpResponseForbidden("You must be a donor or lawyer to access this page")



@login_required
def browse_cases(request):
    """View available cases for donors to browse and support"""
    # Check if user is a donor first
    if hasattr(request.user, 'donor_profile') and request.user.role == 'DONOR':
        # Get all cases that can be donated to
        cases = Case.objects.filter(status__in=['open', 'in_progress']).order_by('-created_at')
        
        # Filter by category if requested
        category_filter = request.GET.get('category', '')
        if category_filter:
            cases = cases.filter(category__id=category_filter)
        
        # Filter by urgency if requested
        urgency_filter = request.GET.get('urgency', '')
        if urgency_filter:
            cases = cases.filter(urgency=urgency_filter)
        
        # Filter by location if requested
        location_filter = request.GET.get('location', '')
        if location_filter:
            cases = cases.filter(location__icontains=location_filter)
        
        # Get all case categories for filter
        categories = CaseCategory.objects.all()
        
        paginator = Paginator(cases, 10)  # 10 cases per page
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        
        context = {
            'page_obj': page_obj,
            'categories': categories,
            'category_filter': category_filter,
            'urgency_filter': urgency_filter,
            'location_filter': location_filter,
        }
        return render(request, 'cases/donor/browse_cases.html', context)
    
@login_required
def lawyer_browse_cases(request):
    if request.user.role != 'LAWYER' or not hasattr(request.user, 'lawyer_profile'):
        return HttpResponseForbidden("You must be a lawyer to access this page")

    lawyer_profile = request.user.lawyer_profile
    cases = Case.objects.filter(status='open').order_by('-created_at')

    # Filtering by category
    category_filter = request.GET.get('category')
    if category_filter:
        cases = cases.filter(category_id=category_filter)

    # Filtering by urgency
    urgency_filter = request.GET.get('urgency')
    if urgency_filter:
        cases = cases.filter(urgency=urgency_filter)

    # Filtering by location
    location_filter = request.GET.get('location')
    if location_filter:
        cases = cases.filter(location__icontains=location_filter)

    # Get applied case IDs
    applied_case_ids = LawyerApplication.objects.filter(
        lawyer=lawyer_profile
    ).values_list('case_id', flat=True)

    # Pagination
    paginator = Paginator(cases, 10)  # Show 10 cases per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'cases': cases,
        'page_obj': page_obj,
        'applied_case_ids': applied_case_ids,
        'categories': CaseCategory.objects.all(),
        'category_filter': category_filter,
        'urgency_filter': urgency_filter,
        'location_filter': location_filter,
    }

    return render(request, 'cases/lawyer/browse_cases.html', context)
@login_required
def redirect_browse_cases(request):
    if hasattr(request.user, 'donor_profile') and request.user.role == 'DONOR':
        return redirect('donations:browse_cases')
    elif request.user.role == 'LAWYER' and hasattr(request.user, 'lawyer_profile'):
        return redirect('cases:lawyer_browse_cases')
    else:
        return HttpResponseForbidden("You must be a donor or lawyer to access this page")




@login_required
def search_cases(request):
    query = request.GET.get('q', '')
    cases = Case.objects.none()
    
    if query:
        cases = Case.objects.filter(
            models.Q(title__icontains=query) |
            models.Q(description__icontains=query) |
            models.Q(tags__icontains=query)
        )
    
    return render(request, 'cases/search_results.html', {
        'cases': cases,
        'query': query
    })

def lawyer_dashboard(request):
    # Your logic here
    return render(request, 'cases/lawyer/dashboard.html', {
        # Your context variables
    })

# 2. Apply to represent a case
@login_required
def apply_for_case(request, pk):
    """Apply to represent a case"""
    if request.user.role != 'LAWYER' or not hasattr(request.user, 'lawyer_profile'):
        return HttpResponseForbidden("You must be a lawyer to apply for cases")
    
    case = get_object_or_404(Case, pk=pk)
    if case.status != 'open':
        messages.error(request, "This case is no longer accepting applications.")
        return redirect('cases:browse_cases')
    
    lawyer_profile = request.user.lawyer_profile
    
    # Check if already applied
    if LawyerApplication.objects.filter(case=case, lawyer=lawyer_profile).exists():
        messages.warning(request, "You have already applied for this case.")
        return redirect('cases:case_detail_lawyer', pk=case.pk)
    
    if request.method == 'POST':
        form = LawyerApplicationForm(request.POST)
        if form.is_valid():
            application = form.save(commit=False)
            application.case = case
            application.lawyer = lawyer_profile
            application.save()
            
            # Notify NGO about new application
            send_mail(
                f'New application for your case: {case.title}',
                f'A lawyer has applied to represent your case "{case.title}". Login to view the application.',
                settings.DEFAULT_FROM_EMAIL,
                [case.ngo.email],
                fail_silently=False,
            )
            
            messages.success(request, "Your application has been submitted successfully!")
            return redirect('cases:lawyer_dashboard')
    else:
        form = LawyerApplicationForm()
    
    context = {
        'form': form,
        'case': case,
    }
    return render(request, 'cases/lawyer/apply_for_case.html', context)

def lawyer_cases(request):
    # Your view logic here
    return render(request, 'cases/lawyer_cases.html', {})


# 3. Manage Active Case Portfolio
# @login_required
# def browse_cases(request):
#     """View available cases for lawyers to apply"""
#     if request.user.role != 'LAWYER' or not hasattr(request.user, 'lawyer_profile'):
#         return HttpResponseForbidden("You must be a lawyer to access this page")
    
#     # Get lawyer profile
#     lawyer_profile = request.user.lawyer_profile
    
#     # Get all open cases
#     cases = Case.objects.filter(status='open')
    
#     # Filter by category if requested
#     category_filter = request.GET.get('category', '')
#     if category_filter:
#         cases = cases.filter(category__id=category_filter)
    
#     # Filter by urgency if requested
#     urgency_filter = request.GET.get('urgency', '')
#     if urgency_filter:
#         cases = cases.filter(urgency=urgency_filter)
    
#     # Filter by location if requested
#     location_filter = request.GET.get('location', '')
#     if location_filter:
#         cases = cases.filter(location__icontains=location_filter)
        
#     # Filter by bounty amount (new)
#     min_bounty = request.GET.get('min_bounty', '')
#     if min_bounty and min_bounty.isdigit():
#         cases = cases.filter(bounty_amount__gte=int(min_bounty))
    
#     # Filter by case complexity (new)
#     complexity_filter = request.GET.get('complexity', '')
#     if complexity_filter:
#         cases = cases.filter(complexity=complexity_filter)
    
#     # Check which cases lawyer has already applied for
#     applied_case_ids = LawyerApplication.objects.filter(
#         lawyer=lawyer_profile
#     ).values_list('case_id', flat=True)
    
#     # Get all case categories for filter
#     categories = CaseCategory.objects.all()
    
#     paginator = Paginator(cases, 10)  # 10 cases per page
#     page_number = request.GET.get('page')
#     page_obj = paginator.get_page(page_number)
    
#     context = {
#         'page_obj': page_obj,
#         'applied_case_ids': applied_case_ids,
#         'categories': categories,
#         'category_filter': category_filter,
#         'urgency_filter': urgency_filter,
#         'location_filter': location_filter,
#         'min_bounty': min_bounty,
#         'complexity_filter': complexity_filter,
#     }
#     return render(request, 'cases/lawyer/browse_cases.html', context)

@login_required
def case_detail_lawyer(request, pk):
    """View case details for lawyers"""
    case = get_object_or_404(Case, pk=pk)
    lawyer_profile = request.user.lawyer_profile
    
    # Check if lawyer is assigned to this case or has applied for it
    is_assigned = (case.assigned_lawyer == lawyer_profile)
    has_applied = LawyerApplication.objects.filter(case=case, lawyer=lawyer_profile).exists()
    
    if not (is_assigned or has_applied or case.status == 'open'):
        return HttpResponseForbidden("You don't have permission to view this case")
    
    context = {
        'case': case,
        'documents': case.documents.all(),
        'updates': case.updates.all(),
        'milestones': case.milestones.all(),
        'is_assigned': is_assigned,
        'has_applied': has_applied,
        'application': LawyerApplication.objects.filter(case=case, lawyer=lawyer_profile).first() if has_applied else None,
    }
    return render(request, 'cases/lawyer/case_detail.html', context)

@login_required
def search_cases(request):
    query = request.GET.get('q', '')
    cases = Case.objects.none()
    
    if query:
        cases = Case.objects.filter(
            models.Q(title__icontains=query) |
            models.Q(description__icontains=query) |
            models.Q(tags__icontains=query)
        )
    
    return render(request, 'cases/search_results.html', {
        'cases': cases,
        'query': query
    })


# 4. Submit progress and report to NGOs
@login_required
def submit_progress(request, case_pk):
    """Submit progress update for a case"""
    case = get_object_or_404(Case, pk=case_pk)
    lawyer_profile = request.user.lawyer_profile
    
    # Verify lawyer is assigned to this case
    if case.assigned_lawyer != lawyer_profile:
        return HttpResponseForbidden("You are not assigned to this case")
    
    if request.method == 'POST':
        form = CaseProgressForm(request.POST)
        if form.is_valid():
            update = CaseUpdate(
                case=case,
                created_by=request.user,
                content=form.cleaned_data['content']
            )
            update.save()
            
            # Handle milestone updates if present
            for milestone in case.milestones.all():
                status = request.POST.get(f'milestone_{milestone.id}_status', None)
                if status and status != milestone.status:
                    milestone.status = status
                    milestone.save()
            
            # Notify NGO
            send_mail(
                f'New update on case: {case.title}',
                f'The assigned lawyer has submitted a new progress update for your case "{case.title}". Login to view it.',
                settings.DEFAULT_FROM_EMAIL,
                [case.ngo.email],
                fail_silently=False,
            )
            
            messages.success(request, "Progress update submitted successfully!")
            return redirect('cases:case_detail_lawyer', pk=case.pk)
    else:
        form = CaseProgressForm()
    
    context = {
        'form': form,
        'case': case,
        'milestones': case.milestones.all(),
    }
    return render(request, 'cases/lawyer/submit_progress.html', context)


# 5. Submit case outcome and claim bounty
@login_required
def submit_case_completion(request, case_pk):
    """Submit case completion and claim bounty"""
    case = get_object_or_404(Case, pk=case_pk)
    lawyer_profile = request.user.lawyer_profile
    
    # Verify lawyer is assigned to this case
    if case.assigned_lawyer != lawyer_profile:
        return HttpResponseForbidden("You are not assigned to this case")
    
    # Check if case is in appropriate status
    if case.status not in ['assigned', 'in_progress']:
        messages.error(request, "This case cannot be submitted for completion at this time.")
        return redirect('cases:case_detail_lawyer', pk=case.pk)
    
    if request.method == 'POST':
        form = CaseCompletionForm(request.POST, request.FILES)
        if form.is_valid():
            # Create final update
            update = CaseUpdate(
                case=case,
                created_by=request.user,
                content=form.cleaned_data['outcome_description']
            )
            update.save()
            
            # For Option 1: Handle individual file fields
            # for i in range(1, 4):
            #     field_name = f'document{i}'
            #     if field_name in form.cleaned_data and form.cleaned_data[field_name]:
            #         doc = form.cleaned_data[field_name]
            #         CaseDocument.objects.create(
            #             case=case,
            #             title=f"Final document {i}: {doc.name}",
            #             file=doc,
            #         )
            
            # For Option 2: Handle MultiFileField
            if 'documents' in form.cleaned_data:
                for doc in form.cleaned_data['documents']:
                    CaseDocument.objects.create(
                        case=case,
                        title=f"Final document: {doc.name}",
                        file=doc,
                    )
            
            # Update case status
            case.status = 'review'
            case.save()
            
            # Notify NGO
            send_mail(
                f'Case ready for review: {case.title}',
                f'The lawyer has submitted the case "{case.title}" for review and completion. Login to review the outcome.',
                settings.DEFAULT_FROM_EMAIL,
                [case.ngo.email],
                fail_silently=False,
            )
            
            messages.success(request, "Case submitted for review. The NGO will review your work.")
            return redirect('cases:lawyer_dashboard')
    else:
        form = CaseCompletionForm()
    
    context = {
        'form': form,
        'case': case,
    }
    return render(request, 'cases/lawyer/submit_completion.html', context)


@login_required
def funding_history(request, pk):
    """View the funding/donation history for a case"""
    case = get_object_or_404(Case, pk=pk)
    # Check permissions
    if request.user != case.ngo and request.user.role != 'NGO':
        return HttpResponseForbidden("You don't have permission to view this case's funding history")
    
    # Get all donations for this case
    donations = case.donations.all().order_by('-timestamp')  # Changed from '-date' to '-timestamp'
    
    context = {
        'case': case,
        'donations': donations,
    }
    return render(request, 'cases/ngo/funding_history.html', context)

@login_required
def case_updates(request, pk):
    """View updates/progress updates for a case"""
    case = get_object_or_404(Case, pk=pk)
    # Check permissions
    if request.user != case.ngo and request.user.role != 'NGO':
        return HttpResponseForbidden("You don't have permission to view this case's updates")
    
    # Get all updates for this case
    updates = case.updates.all().order_by('-created_at')
    
    context = {
        'case': case,
        'updates': updates,
    }
    return render(request, 'cases/ngo/case_updates.html', context)

@login_required
def approve_completion(request, pk):
    """Approve case completion and release bounty"""
    case = get_object_or_404(Case, pk=pk)
    # Check permissions
    if request.user != case.ngo and request.user.role != 'NGO':
        return HttpResponseForbidden("You don't have permission to approve completion for this case")
    
    if request.method == 'POST':
        # Process approval
        case.is_completed = True
        case.completion_approved_at = timezone.now()
        case.save()
        
        # Process bounty release if applicable
        if case.assigned_lawyer.exists() and case.bounty_amount > 0:
            # Logic to release bounty to assigned lawyer(s)
            pass
        
        messages.success(request, "Case completion approved and bounty released!")
        return redirect('cases:case_detail', pk=case.pk)
    
    context = {
        'case': case,
    }
    return render(request, 'cases/ngo/approve_completion.html', context)

@login_required
def delete_document(request, pk):
    """Delete a document"""
    document = get_object_or_404(Document, pk=pk)
    case = document.case
    
    # Check permissions
    if request.user != case.ngo and request.user.role != 'NGO':
        return HttpResponseForbidden("You don't have permission to delete documents for this case")
    
    if request.method == 'POST':
        # Delete the document
        document.delete()
        messages.success(request, "Document deleted successfully!")
        return redirect('cases:edit_case', pk=case.pk)
    
    context = {
        'document': document,
        'case': case,
    }
    return render(request, 'cases/ngo/confirm_delete_document.html', context)


# Add this with the other view functions

@login_required
def rate_lawyer(request, case_pk):
    """Allow NGO to rate and review lawyer after case completion"""
    case = get_object_or_404(Case, pk=case_pk)
    
    # Verify permissions
    if request.user != case.ngo or request.user.role != 'NGO':
        return HttpResponseForbidden("You don't have permission to rate this lawyer")
    
    # Verify case is completed
    if case.status != 'completed':
        messages.error(request, "You can only rate the lawyer after the case is completed")
        return redirect('cases:case_detail', pk=case_pk)
    
    # Check if already rated
    if LawyerRating.objects.filter(case=case).exists():
        messages.warning(request, "You have already rated the lawyer for this case")
        return redirect('cases:case_detail', pk=case_pk)
    
    if request.method == 'POST':
        rating = request.POST.get('rating')
        review = request.POST.get('review', '')
        
        try:
            rating = int(rating)
            if rating < 1 or rating > 5:
                raise ValueError
        except (TypeError, ValueError):
            messages.error(request, "Please provide a valid rating between 1 and 5")
            return redirect('cases:rate_lawyer', case_pk=case_pk)
        
        # Create the rating
        LawyerRating.objects.create(
            lawyer=case.assigned_lawyer,
            case=case,
            created_by=request.user,
            rating=rating,
            review=review
        )
        
        messages.success(request, "Thank you for rating the lawyer!")
        return redirect('cases:case_detail', pk=case_pk)
    
    context = {
        'case': case,
        'lawyer': case.assigned_lawyer
    }
    return render(request, 'cases/ngo/rate_lawyer.html', context)

# 6. View ratings and reviews from NGOs
@login_required
def lawyer_ratings(request):
    """View all ratings and reviews received"""
    if request.user.role != 'LAWYER' or not hasattr(request.user, 'lawyer_profile'):
        return HttpResponseForbidden("You must be a lawyer to access this page")
    
    lawyer_profile = request.user.lawyer_profile
    ratings = LawyerRating.objects.filter(lawyer=lawyer_profile).order_by('-created_at')
    average_rating = ratings.aggregate(Avg('rating'))['rating__avg'] or 0
    
    context = {
        'ratings': ratings,
        'average_rating': average_rating,
    }
    return render(request, 'cases/lawyer/ratings.html', context)


# 7. Add success story
@login_required
def add_success_story(request, case_pk=None):
    """Add a success story based on a completed case"""
    if request.user.role != 'LAWYER' or not hasattr(request.user, 'lawyer_profile'):
        return HttpResponseForbidden("You must be a lawyer to access this page")
    
    lawyer_profile = request.user.lawyer_profile
    case = None
    
    if case_pk:
        case = get_object_or_404(Case, pk=case_pk)
        # Check if lawyer was assigned to this case and it's completed
        if case.assigned_lawyer != lawyer_profile or case.status != 'completed':
            return HttpResponseForbidden("You can only add success stories for completed cases you worked on")
    
    if request.method == 'POST':
        form = SuccessStoryForm(request.POST, request.FILES)
        if form.is_valid():
            success_story = form.save(commit=False)
            success_story.lawyer = lawyer_profile
            if case:
                success_story.case = case
            success_story.save()
            messages.success(request, "Success story added successfully!")
            return redirect('cases:lawyer_success_stories')
    else:
        initial_data = {}
        if case:
            initial_data = {'title': f"Success story: {case.title}"}
        form = SuccessStoryForm(initial=initial_data)
    
    context = {
        'form': form,
        'case': case,
    }
    return render(request, 'cases/lawyer/add_success_story.html', context)


@login_required
def lawyer_success_stories(request):
    """View all success stories added by lawyer"""
    if request.user.role != 'LAWYER' or not hasattr(request.user, 'lawyer_profile'):
        return HttpResponseForbidden("You must be a lawyer to access this page")
    
    lawyer_profile = request.user.lawyer_profile
    success_stories = SuccessStory.objects.filter(lawyer=lawyer_profile).order_by('-created_at')
    
    context = {
        'success_stories': success_stories,
    }
    return render(request, 'cases/lawyer/success_stories.html', context)


# Public view to see lawyer achievements and success stories
def lawyer_profile_public(request, lawyer_id):
    """Public view of lawyer profile with achievements and success stories"""
    lawyer_profile = get_object_or_404(LawyerProfile, pk=lawyer_id) 
    
    # Get completed cases
    completed_cases_count = Case.objects.filter(
        assigned_lawyer=lawyer_profile, 
        status='completed'
    ).count()
    
    # Get average rating
    average_rating = LawyerRating.objects.filter(
        lawyer=lawyer_profile
    ).aggregate(Avg('rating'))['rating__avg'] or 0
    
    # Get public success stories
    success_stories = SuccessStory.objects.filter(
        lawyer=lawyer_profile,
        is_public=True
    ).order_by('-created_at')
    
    context = {
        'lawyer': lawyer_profile,
        'completed_cases_count': completed_cases_count,
        'average_rating': average_rating,
        'success_stories': success_stories,
    }
    return render(request, 'cases/public/lawyer_profile.html', context)