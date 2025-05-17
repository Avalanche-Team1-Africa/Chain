from django.utils import timezone
from datetime import datetime, timedelta
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import FileResponse, HttpResponseForbidden, JsonResponse
from django.core.paginator import Paginator
from django.core.mail import send_mail
from django.conf import settings
from django.urls import reverse
from django.db.models import F, Avg, Count, ExpressionWrapper, DurationField
from django.core.exceptions import ObjectDoesNotExist 
from django.db.models.functions import TruncMonth
from django.db.models import Q
import json
import logging
import io
from docxtpl import DocxTemplate
from django.core.files.base import ContentFile
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from cases.utils import award_tokens
from decimal import Decimal
from django.db import transaction
from .models import CaseNotification, TokenTransaction  
# from ratelimit.decorators import ratelimit       
import os
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
    LawyerRating,
    CaseEvent,
    CaseMessage, 
    CaseMessageAttachment,
    CaseDocument, 
    DocumentTemplate,
    UserWallet,

)
from .forms import (
    CaseForm,
    CaseDocumentForm,
    CaseUpdateForm,
    InviteLawyerForm,
    LawyerApplicationForm,
    CaseProgressForm,
    CaseCompletionForm,
    SuccessStoryForm,
    CaseEventForm,
    CaseMessageForm,
    DocumentGenerationForm
    
)

@login_required
def ngo_dashboard(request):
    """Enhanced dashboard with analytics for NGOs"""
    if request.user.role != 'NGO' or not hasattr(request.user, 'ngo_profile'):
        return HttpResponseForbidden("You must be an NGO to access this page")
    
    # Get cases for this NGO
    cases = Case.objects.filter(ngo=request.user)
    
    # Calculate totals safely to avoid divide-by-zero
    case_count = cases.count()
    completed_count = cases.filter(status='completed').count()
    
    # Calculate total donations - handle if total_donations() method exists
    try:
        total_donations = sum(c.total_donations() for c in cases)
    except AttributeError:
        # If total_donations() method doesn't exist, try to use related donations
        total_donations = sum(c.donations.all().aggregate(Sum('amount'))['amount__sum'] or 0 for c in cases)
    except:
        # Fallback if neither approach works
        total_donations = 0
    
    # Case metrics
    case_stats = {
        'total_cases': case_count,
        'open_cases': cases.filter(status='open').count(),
        'in_progress_cases': cases.filter(status='in_progress').count(),
        'completed_cases': completed_count,
        
        # Calculate time metrics differently, as completion_date doesn't exist
        # Using updated_at as a proxy for completion date for completed cases
        'avg_completion_time': cases.filter(status='completed').annotate(
            time_to_complete=ExpressionWrapper(
                F('updated_at') - F('created_at'),
                output_field=DurationField()
            )
        ).aggregate(avg_time=Avg('time_to_complete'))['avg_time'],
        
        # Success rate with safe division
        'success_rate': (completed_count / max(case_count, 1)) * 100,
        
        # Financial metrics with safe division
        'total_donations': total_donations,
        'avg_donations_per_case': total_donations / max(case_count, 1),
    }
    
    # Category distribution
    category_data = cases.values('category__name').annotate(
        count=Count('id')
    ).order_by('-count')
    
    # Monthly case trend
    monthly_trend = cases.annotate(
        month=TruncMonth('created_at')
    ).values('month').annotate(
        count=Count('id')
    ).order_by('month')
    
    context = {
        'case_stats': case_stats,
        'category_data': category_data,
        'monthly_trend': monthly_trend,
        'recent_cases': cases.order_by('-created_at')[:5],
    }
    
    return render(request, 'cases/ngo/dashboard.html', context)
    """Enhanced dashboard with analytics for NGOs"""
    if request.user.role != 'NGO' or not hasattr(request.user, 'ngo_profile'):
        return HttpResponseForbidden("You must be an NGO to access this page")
    
    # Get cases for this NGO
    cases = Case.objects.filter(ngo=request.user)
    
    # Calculate totals safely to avoid divide-by-zero
    case_count = cases.count()
    completed_count = cases.filter(status='completed').count()
    total_donations = sum(c.total_donations() for c in cases)
    
    # Case metrics
    case_stats = {
        'total_cases': case_count,
        'open_cases': cases.filter(status='open').count(),
        'in_progress_cases': cases.filter(status='in_progress').count(),
        'completed_cases': completed_count,
        
        # Time metrics - using proper F expression import
        'avg_completion_time': cases.filter(status='completed').annotate(
            time_to_complete=F('completion_date') - F('created_at')
        ).aggregate(avg_time=Avg('time_to_complete'))['avg_time'],
        
        # Success rate with safe division
        'success_rate': (completed_count / max(case_count, 1)) * 100,
        
        # Financial metrics with safe division
        'total_donations': total_donations,
        'avg_donations_per_case': total_donations / max(case_count, 1),
    }
    
    # Category distribution
    category_data = cases.values('category__name').annotate(
        count=Count('id')
    ).order_by('-count')
    
    # Monthly case trend
    monthly_trend = cases.annotate(
        month=TruncMonth('created_at')
    ).values('month').annotate(
        count=Count('id')
    ).order_by('month')
    
    context = {
        'case_stats': case_stats,
        'category_data': category_data,
        'monthly_trend': monthly_trend,
        'recent_cases': cases.order_by('-created_at')[:5],
    }
    
    return render(request, 'cases/ngo/ngo_dashboard.html', context)




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


def assign_lawyer(request, case_pk, lawyer_id):
    # Your logic here
    return redirect('cases/ngo/assign_lawyer.html')

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
def case_calendar(request):
    """Calendar view showing all case events and deadlines"""
    user = request.user
    events = []
    
    # Get events based on user role
    if user.role == 'NGO' and hasattr(user, 'ngo_profile'):
        # For NGOs, show events for all their cases
        cases = Case.objects.filter(ngo=user)
        case_events = CaseEvent.objects.filter(case__in=cases)
        
    elif user.role == 'LAWYER' and hasattr(user, 'lawyer_profile'):
        # For lawyers, show events for cases they're assigned to
        cases = Case.objects.filter(assigned_lawyer=user.lawyer_profile)
        case_events = CaseEvent.objects.filter(case__in=cases)
        
    else:
        return HttpResponseForbidden("You don't have permission to view the calendar")
    
    # Add events to the list
    for event in case_events:
        events.append({
            'id': event.id,
            'title': event.title,
            'start': event.start_time.isoformat(),
            'end': event.end_time.isoformat() if event.end_time else None,
            'url': reverse('cases:event_detail', args=[event.id]),
            'backgroundColor': event.get_color_by_type(),
        })
    
    # Add case milestones
    for case in cases:
        for milestone in case.milestones.all():
            if milestone.target_date:
                events.append({
                    'id': f'milestone_{milestone.id}',
                    'title': f"Milestone: {milestone.title}",
                    'start': milestone.target_date.isoformat(),
                    'url': reverse('cases:case_detail', args=[case.id]),
                    'backgroundColor': '#28a745' if milestone.status == 'completed' else '#ffc107',
                })
    
    context = {
        'events_json': json.dumps(events),
    }
    return render(request, 'cases/calendar.html', context)

@login_required
def add_event(request, case_pk=None):
    """Add a new event to the calendar"""
    # Determine if user has permission
    user = request.user
    if user.role not in ['NGO', 'LAWYER']:
        return HttpResponseForbidden("You don't have permission to add events")
    
    initial_data = {}
    if case_pk:
        case = get_object_or_404(Case, pk=case_pk)
        # Check if user has permission for this case
        if (user.role == 'NGO' and case.ngo != user) or \
           (user.role == 'LAWYER' and case.assigned_lawyer != user.lawyer_profile):
            return HttpResponseForbidden("You don't have permission to add events to this case")
        initial_data['case'] = case
    
    if request.method == 'POST':
        form = CaseEventForm(request.POST, user=user)
        if form.is_valid():
            event = form.save(commit=False)
            event.created_by = user
            event.save()
            
            # Optionally notify others involved with the case
            notify_event_creation(event)
            
            messages.success(request, "Event added successfully!")
            if 'next' in request.GET:
                return redirect(request.GET['next'])
            return redirect('cases:case_calendar')
    else:
        form = CaseEventForm(initial=initial_data, user=user)
    
    context = {
        'form': form,
        'case_pk': case_pk,
    }
    return render(request, 'cases/add_event.html', context)


@login_required
def event_detail(request, event_id):
    """View details of a calendar event"""
    event = get_object_or_404(CaseEvent, pk=event_id)
    user = request.user
    
    # Check permissions
    if user.role == 'NGO':
        if event.case.ngo != user:
            return HttpResponseForbidden("You don't have permission to view this event")
    elif user.role == 'LAWYER':
        if event.case.assigned_lawyer != user.lawyer_profile:
            return HttpResponseForbidden("You don't have permission to view this event")
    else:
        return HttpResponseForbidden("You don't have permission to view this event")
    
    context = {
        'event': event,
        'case': event.case,
    }
    return render(request, 'cases/event_detail.html', context)


def notify_event_creation(event):
    """Notify relevant users about event creation"""
    case = event.case
    
    # Notify the NGO if created by lawyer
    if event.created_by.role == 'LAWYER' and case.ngo:
        send_mail(
            f'New event for case: {case.title}',
            f'A new event "{event.title}" has been scheduled for {event.start_time.strftime("%B %d, %Y at %I:%M %p")}.',
            settings.DEFAULT_FROM_EMAIL,
            [case.ngo.email],
            fail_silently=False,
        )
    
    # Notify the lawyer if created by NGO
    if event.created_by.role == 'NGO' and case.assigned_lawyer:
        send_mail(
            f'New event for case: {case.title}',
            f'A new event "{event.title}" has been scheduled for {event.start_time.strftime("%B %d, %Y at %I:%M %p")}.',
            settings.DEFAULT_FROM_EMAIL,
            [case.assigned_lawyer.user.email],
            fail_silently=False,
        )

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

@login_required
def lawyer_dashboard(request):
    user = request.user
    
    try:
        lawyer_profile = models.LawyerProfile.objects.get(user=user)
    except models.LawyerProfile.DoesNotExist:
        return render(request, 'cases/error.html', {
            'error_message': 'You do not have a lawyer profile. Please contact an administrator.'
        })
    
    assigned_cases = Case.objects.filter(
        assigned_lawyer=lawyer_profile
    ).exclude(
        status='completed'
    ).order_by('deadline')
    
    cases_in_progress = Case.objects.filter(
        assigned_lawyer=lawyer_profile, 
        status__in=['assigned', 'in_progress']
    ).count()
    
    cases_under_review = Case.objects.filter(
        assigned_lawyer=lawyer_profile, 
        status='review'
    ).count()
    
    cases_completed = Case.objects.filter(
        assigned_lawyer=lawyer_profile, 
        status='completed'
    ).count()
    
    notifications = CaseNotification.objects.filter(
        recipient=user
    ).order_by('-created_at')[:10]
    
    case_notifications = CaseNotification.objects.filter(
        recipient=user,
        case__isnull=False
    ).order_by('-created_at')[:5]
    
    unread_notifications_count = CaseNotification.objects.filter(
        recipient=user,
        is_read=False
    ).count()
    
    context = {
        'assigned_cases': assigned_cases,
        'cases_in_progress': cases_in_progress,
        'cases_under_review': cases_under_review,
        'cases_completed': cases_completed,
        'notifications': notifications,
        'case_notifications': case_notifications,
        'unread_notifications_count': unread_notifications_count,
    }
    
    return render(request, 'cases/lawyer/dashboard.html', context)
@login_required
def lawyer_notifications(request):
    """
    View for displaying all notifications for a lawyer
    """
    lawyer = request.user
    
    # Get all notifications for this lawyer
    notifications = CaseNotification.objects.filter(
        recipient=lawyer
    ).order_by('-created_at')
    
    # Count unread notifications
    unread_notifications_count = notifications.filter(is_read=False).count()
    
    # Filter by type if requested
    notification_type = request.GET.get('type')
    if notification_type:
        if notification_type == 'case_assignments':
            notifications = notifications.filter(notification_type='case_assignment')
        elif notification_type == 'client_messages':
            notifications = notifications.filter(notification_type='client_message')
        elif notification_type == 'deadlines':
            notifications = notifications.filter(notification_type='deadline')
        elif notification_type == 'system':
            notifications = notifications.filter(notification_type='system')
    
    context = {
        'notifications': notifications,
        'unread_notifications_count': unread_notifications_count,
    }
    
    return render(request, 'cases/lawyer/lawyer_notifications.html', context)



# 2. Apply to represent a case
@login_required
# @ratelimit(key='user', rate='5/d', method='POST')
@login_required
def apply_for_case(request, pk):
    # Check if user is a lawyer with a lawyer profile
    if request.user.role != 'LAWYER' or not hasattr(request.user, 'lawyer_profile'):
        return HttpResponseForbidden("You must be a lawyer to apply for cases")
    
    # Get the case
    case = get_object_or_404(Case, pk=pk)
    
    # Check if case is open
    if case.status != 'open':
        messages.error(request, "This case is no longer accepting applications.")
        return redirect('cases:browse_cases')
    
    # Get lawyer profile
    lawyer_profile = request.user.lawyer_profile
    
    # Check if lawyer has already applied
    if LawyerApplication.objects.filter(case=case, lawyer=lawyer_profile).exists():
        messages.warning(request, "You have already applied for this case.")
        return redirect('cases:case_detail_lawyer', pk=case.pk)
    
    if request.method == 'POST':
        form = LawyerApplicationForm(request.POST)
        if form.is_valid():
            # Save application
            application = form.save(commit=False)
            application.case = case
            application.lawyer = lawyer_profile
            application.save()
            
            # Award tokens for applying
            award_tokens(
                user=request.user,
                amount=10,
                description=f"Applied for case: {case.title}",
                case=case
            )
            
            # Send email notification to NGO
            # send_mail(
            #     subject=f'New application for your case: {case.title}',
            #     message=f'A lawyer has applied to represent your case "{case.title}". Login to view the application.',
            #     from_email=settings.DEFAULT_FROM_EMAIL,
            #     recipient_list=[case.ngo.email],
            #     fail_silently=False,
            # )
            
            # Send SMS notification to lawyer using Africa's Talking API
            # Get phone number from user or user profile as appropriate
            phone_number = getattr(request.user, 'phone_number', None)
            
            # If not found in user model, try other possible locations
            if not phone_number and hasattr(request.user, 'profile'):
                phone_number = getattr(request.user.profile, 'phone_number', None)
            
            if phone_number:
                send_sms_notification(
                    phone_number=phone_number,
                    message=f"Congratulations {request.user.first_name}! You have successfully applied to case: {case.title}, "
                            f"with bounty amount of {case.bounty_amount} and {case.milestones.count()} milestones. "
                            f"If successful, the NGO will contact you."
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


logger = logging.getLogger(__name__)


# Add this function to handle SMS sending
def send_sms_notification(phone_number, message):
    """
    Send SMS notification using Africa's Talking API
    
    Args:
        phone_number (str): The recipient's phone number
        message (str): The message to send
    """
    try:
        # Import the Africa's Talking module
        import africastalking
        
        # Set your app credentials
        username = settings.AFRICASTALKING_USERNAME
        api_key = settings.AFRICASTALKING_API_KEY
        
        # Initialize the SDK
        africastalking.initialize(username, api_key)
        
        # Get the SMS service
        sms = africastalking.SMS
        
        # Make sure the phone number is in the correct format (e.g., +254XXXXXXXXX)
        if not phone_number.startswith('+'):
            phone_number = '+' + phone_number
            
        # Send the message
        response = sms.send(message, [phone_number])
        
        # Log the response
        logger.info(f"SMS sent successfully: {response}")
        
        return response
    except Exception as e:
        # Log any errors
        logger.error(f"Failed to send SMS: {str(e)}")
        
        # Don't raise the exception as this shouldn't block the main functionality
        return None
    
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

    # Check if user is a lawyer and has a lawyer profile
    if request.user.role != 'LAWYER':
        return HttpResponseForbidden("You must be a lawyer to access this page")
    
    try:
        lawyer_profile = request.user.lawyer_profile
    except User.lawyer_profile.RelatedObjectDoesNotExist:
        return HttpResponseForbidden("You do not have a lawyer profile. Please contact an administrator or complete your profile setup.")

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
    case = get_object_or_404(Case, pk=case_pk)
    lawyer_profile = request.user.lawyer_profile
    
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
            
            # Award tokens for progress update
            award_tokens(
                user=request.user,
                amount=15,
                description=f"Submitted progress update for case: {case.title}",
                case=case
            )
            
            # Handle milestone updates
            for milestone in case.milestones.all():
                status = request.POST.get(f'milestone_{milestone.id}_status', None)
                if status and status != milestone.status:
                    milestone.status = status
                    milestone.save()
                    if status == 'completed':
                        # Award tokens for milestone completion
                        award_tokens(
                            user=request.user,
                            amount=30,
                            description=f"Completed milestone: {milestone.title} for case: {case.title}",
                            case=case
                        )
            
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
    case = get_object_or_404(Case, pk=case_pk)
    lawyer_profile = request.user.lawyer_profile
    
    if case.assigned_lawyer != lawyer_profile:
        return HttpResponseForbidden("You are not assigned to this case")
    
    if case.status not in ['assigned', 'in_progress']:
        messages.error(request, "This case cannot be submitted for completion at this time.")
        return redirect('cases:case_detail_lawyer', pk=case.pk)
    
    if request.method == 'POST':
        form = CaseCompletionForm(request.POST, request.FILES)
        if form.is_valid():
            update = CaseUpdate(
                case=case,
                created_by=request.user,
                content=form.cleaned_data['outcome_description']
            )
            update.save()
            
            if 'documents' in form.cleaned_data:
                for doc in form.cleaned_data['documents']:
                    CaseDocument.objects.create(
                        case=case,
                        title=f"Final document: {doc.name}",
                        file=doc,
                    )
            
            case.status = 'review'
            case.save()
            
            # Award tokens for submitting case for review
            award_tokens(
                user=request.user,
                amount=50,
                description=f"Submitted case for review: {case.title}",
                case=case
            )
            
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
    case = get_object_or_404(Case, pk=case_pk)
    if request.user != case.ngo or request.user.role != 'NGO':
        return HttpResponseForbidden("You don't have permission to rate this lawyer")
    if case.status != 'completed':
        messages.error(request, "You can only rate the lawyer after the case is completed")
        return redirect('cases:case_detail', pk=case_pk)
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
        
        LawyerRating.objects.create(
            lawyer=case.assigned_lawyer,
            case=case,
            created_by=request.user,
            rating=rating,
            review=review
        )
        
        # Award tokens for rating
        award_tokens(
            user=request.user,
            amount=10,
            description=f"Rated lawyer for case: {case.title}",
            case=case
        )
        
        messages.success(request, "Thank you for rating the lawyer!")
        return redirect('cases:case_detail', pk=case_pk)
    
    context = {
        'case': case,
        'lawyer': case.assigned_lawyer
    }
    return render(request, 'cases/ngo/rate_lawyer.html', context)
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


@login_required
def case_messages(request, case_pk):
    """View and create messages for a specific case"""
    case = get_object_or_404(Case, pk=case_pk)
    
    # Check permissions
    is_case_ngo = (request.user == case.ngo)
    is_assigned_lawyer = (
        request.user.role == 'LAWYER' and
        hasattr(request.user, 'lawyer_profile') and
        case.assigned_lawyer and
        request.user.lawyer_profile == case.assigned_lawyer
    )
    
    if not (is_case_ngo or is_assigned_lawyer):
        return HttpResponseForbidden("You don't have permission to access messages for this case")
    
    # Get all messages for this case
    messages = CaseMessage.objects.filter(case=case).order_by('timestamp')
    
    # Handle new message submission
    if request.method == 'POST':
        form = CaseMessageForm(request.POST, request.FILES)
        if form.is_valid():
            message = form.save(commit=False)
            message.case = case
            message.sender = request.user
            message.save()
            
            # Handle file attachments
            files = request.FILES.getlist('attachments')
            for file in files:
                CaseMessageAttachment.objects.create(
                    message=message,
                    file=file,
                    name=file.name
                )
            
            # Redirect to avoid form resubmission
            return redirect('cases:case_messages', case_pk=case_pk)
    else:
        form = CaseMessageForm()
    
    context = {
        'case': case,
        'messages': messages,
        'form': form,
        'is_case_ngo': is_case_ngo,
        'is_assigned_lawyer': is_assigned_lawyer,
    }
    return render(request, 'cases/messages.html', context)

@login_required
def load_new_messages(request, case_pk, last_message_id):
    """API endpoint to load new messages (for AJAX polling)"""
    case = get_object_or_404(Case, pk=case_pk)
    
    # Check permissions
    is_case_ngo = (request.user == case.ngo)
    is_assigned_lawyer = (
        request.user.role == 'LAWYER' and
        hasattr(request.user, 'lawyer_profile') and
        case.assigned_lawyer and
        request.user.lawyer_profile == case.assigned_lawyer
    )
    
    if not (is_case_ngo or is_assigned_lawyer):
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    # Get new messages
    new_messages = CaseMessage.objects.filter(
        case=case,
        id__gt=last_message_id
    ).order_by('timestamp')
    
    # Format messages for JSON response
    messages_data = []
    for msg in new_messages:
        attachments = []
        for attachment in msg.attachments.all():
            attachments.append({
                'id': attachment.id,
                'name': attachment.name,
                'url': attachment.file.url,
            })
        
        messages_data.append({
            'id': msg.id,
            'sender_name': msg.sender.get_full_name(),
            'sender_role': msg.sender.role,
            'content': msg.content,
            'timestamp': msg.timestamp.strftime('%b %d, %Y, %I:%M %p'),
            'attachments': attachments,
        })
    
    return JsonResponse({'messages': messages_data})


@login_required
def mark_messages_read(request, case_pk):
    """Mark all messages in a case as read"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    case = get_object_or_404(Case, pk=case_pk)
    
    # Check permissions
    is_case_ngo = (request.user == case.ngo)
    is_assigned_lawyer = (
        request.user.role == 'LAWYER' and
        hasattr(request.user, 'lawyer_profile') and
        case.assigned_lawyer and
        request.user.lawyer_profile == case.assigned_lawyer
    )
    
    if not (is_case_ngo or is_assigned_lawyer):
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    # Mark unread messages as read
    unread_count = CaseMessage.objects.filter(
        case=case,
        read_by__contains=request.user.id
    ).update(read_by=models.F('read_by').add(request.user.id))
    
    return JsonResponse({'success': True, 'marked_read': unread_count})


# 7. Add success story
@login_required
def add_success_story(request, case_pk=None):
    if request.user.role != 'LAWYER' or not hasattr(request.user, 'lawyer_profile'):
        return HttpResponseForbidden("You must be a lawyer to access this page")
    
    lawyer_profile = request.user.lawyer_profile
    case = None
    if case_pk:
        case = get_object_or_404(Case, pk=case_pk)
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
            
            # Award tokens for success story
            award_tokens(
                user=request.user,
                amount=25,
                description=f"Added success story for case: {success_story.title}",
                case=case
            )
            
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

@login_required
def document_templates(request):
    """View available document templates"""
    # Check user role
    if request.user.role not in ['NGO', 'LAWYER']:
        return HttpResponseForbidden("You don't have permission to access document templates")
    
    templates = DocumentTemplate.objects.all()
    
    if request.user.role == 'NGO':
        templates = templates.filter(available_to_ngo=True)
    elif request.user.role == 'LAWYER':
        templates = templates.filter(available_to_lawyer=True)
    
    context = {
        'templates': templates,
    }
    return render(request, 'cases/document_templates.html', context)


@login_required
def generate_document(request, case_pk, template_pk):
    """Generate a document from a template for a specific case"""
    case = get_object_or_404(Case, pk=case_pk)
    template = get_object_or_404(DocumentTemplate, pk=template_pk)
    
    # Check permissions
    is_case_ngo = (request.user == case.ngo)
    is_assigned_lawyer = (
        request.user.role == 'LAWYER' and
        hasattr(request.user, 'lawyer_profile') and
        case.assigned_lawyer and
        request.user.lawyer_profile == case.assigned_lawyer
    )
    
    if not (is_case_ngo or is_assigned_lawyer):
        return HttpResponseForbidden("You don't have permission to generate documents for this case")
    
    # Check template access
    if request.user.role == 'NGO' and not template.available_to_ngo:
        return HttpResponseForbidden("This template is not available for NGO use")
    if request.user.role == 'LAWYER' and not template.available_to_lawyer:
        return HttpResponseForbidden("This template is not available for lawyer use")
    
    if request.method == 'POST':
        form = DocumentGenerationForm(request.POST, template=template)
        if form.is_valid():
            # Get form data
            context_data = form.cleaned_data
            
            # Add case-specific data
            context_data.update({
                'case_title': case.title,
                'case_reference': case.reference_number,
                'case_description': case.description,
                'ngo_name': case.ngo.get_full_name(),
                'ngo_email': case.ngo.email,
                'today_date': timezone.now().strftime('%B %d, %Y'),
            })
            
            # Add lawyer data if available
            if case.assigned_lawyer:
                context_data.update({
                    'lawyer_name': case.assigned_lawyer.user.get_full_name(),
                    'lawyer_email': case.assigned_lawyer.user.email,
                    'lawyer_phone': case.assigned_lawyer.phone_number,
                })
            
            # Generate document from template
            doc = DocxTemplate(template.template_file.path)
            doc.render(context_data)
            
            # Create a buffer to store the document
            buffer = io.BytesIO()
            doc.save(buffer)
            buffer.seek(0)
            
            # Save the document to the case
            document_name = form.cleaned_data.get('document_name', f"{template.name} - {case.title}")
            document = CaseDocument(
                case=case,
                name=document_name,
                uploaded_by=request.user,
                document_type='generated'
            )
            
            # Save the file content
            document.file.save(
                f"{document_name}.docx",
                ContentFile(buffer.read())
            )
            document.save()
            
            messages.success(request, f"Document '{document_name}' generated successfully!")
            return redirect('cases:case_detail', pk=case.pk)
    else:
        form = DocumentGenerationForm(template=template)
    
    context = {
        'form': form,
        'case': case,
        'template': template,
    }
    return render(request, 'cases/generate_document.html', context)



@login_required
def download_template(request, template_pk):
    """Download a blank template document"""
    template = get_object_or_404(DocumentTemplate, pk=template_pk)
    
    # Check access permissions
    if request.user.role == 'NGO' and not template.available_to_ngo:
        return HttpResponseForbidden("This template is not available for NGO use")
    if request.user.role == 'LAWYER' and not template.available_to_lawyer:
        return HttpResponseForbidden("This template is not available for lawyer use")
    
    # Open the file
    file_path = template.template_file.path
    with open(file_path, 'rb') as file:
        response = HttpResponse(
            file.read(),
            content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        )
        
        # Set filename
        filename = os.path.basename(file_path)
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        return response


@login_required
def advanced_search(request):
    """Advanced search with multiple filters and sorting options"""
    # Base queryset - different for each user role
    user = request.user
    
    if user.role == 'NGO' and hasattr(user, 'ngo_profile'):
        cases = Case.objects.filter(ngo=user)
    elif user.role == 'LAWYER' and hasattr(user, 'lawyer_profile'):
        lawyer_profile = user.lawyer_profile
        # Lawyers can see cases they're assigned to or open cases
        cases = Case.objects.filter(
            Q(assigned_lawyer=lawyer_profile) | 
            Q(status='open')
        ).distinct()
    elif user.role == 'DONOR' and hasattr(user, 'donor_profile'):
        # Donors can see open or in-progress cases
        cases = Case.objects.filter(status__in=['open', 'in_progress'])
    else:
        # Default to no access
        cases = Case.objects.none()
    
    # Apply search filters if provided
    # Text search
    search_query = request.GET.get('q', '').strip()
    if search_query:
        cases = cases.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(reference_number__icontains=search_query) |
            Q(tags__icontains=search_query)
        )
    
    # Category filter
    category = request.GET.get('category', '')
    if category:
        cases = cases.filter(category__id=category)
    
    # Status filter
    status = request.GET.get('status', '')
    if status:
        cases = cases.filter(status=status)
    
    # Urgency filter
    urgency = request.GET.get('urgency', '')
    if urgency:
        cases = cases.filter(urgency=urgency)
    
    # Location filter
    location = request.GET.get('location', '')
    if location:
        cases = cases.filter(location__icontains=location)
    
    # Date range filter
    date_from = request.GET.get('date_from', '')
    if date_from:
        cases = cases.filter(created_at__gte=date_from)
    
    date_to = request.GET.get('date_to', '')
    if date_to:
        cases = cases.filter(created_at__lte=date_to)
    
    # Bounty amount range
    min_bounty = request.GET.get('min_bounty', '')
    if min_bounty and min_bounty.isdigit():
        cases = cases.filter(bounty_amount__gte=int(min_bounty))
    
    max_bounty = request.GET.get('max_bounty', '')
    if max_bounty and max_bounty.isdigit():
        cases = cases.filter(bounty_amount__lte=int(max_bounty))
    
    # Has lawyer assigned filter
    has_lawyer = request.GET.get('has_lawyer', '')
    if has_lawyer == 'yes':
        cases = cases.exclude(assigned_lawyer=None)
    elif has_lawyer == 'no':
        cases = cases.filter(assigned_lawyer=None)
    
    # Sort results
    sort_by = request.GET.get('sort_by', '-created_at')
    valid_sort_fields = ['created_at', '-created_at', 'title', '-title', 
                         'urgency', '-urgency', 'bounty_amount', '-bounty_amount']
    
    if sort_by in valid_sort_fields:
        cases = cases.order_by(sort_by)
    else:
        # Default sort
        cases = cases.order_by('-created_at')
    
    # Add annotations for advanced sorting/filtering if needed
    cases = cases.annotate(
        update_count=Count('updates'),
        donation_sum=Sum('donations__amount'),
    )
    
    # Pagination
    paginator = Paginator(cases, 10)  # 10 cases per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Context for templates
    context = {
        'page_obj': page_obj,
        'categories': CaseCategory.objects.all(),
        'search_query': search_query,
        'category': category,
        'status': status,
        'urgency': urgency,
        'location': location,
        'date_from': date_from,
        'date_to': date_to,
        'min_bounty': min_bounty,
        'max_bounty': max_bounty,
        'has_lawyer': has_lawyer,
        'sort_by': sort_by,
        'result_count': cases.count(),
    }
    
    return render(request, 'cases/advanced_search.html', context)


@login_required
def export_search_results(request):
    """Export search results to CSV or PDF"""
    # This should reuse the filtering logic from advanced_search
    # But instead of rendering a template, generate a CSV or PDF file
    
    # First get the filtered queryset using the same logic as advanced_search
    user = request.user
    
    if user.role == 'NGO' and hasattr(user, 'ngo_profile'):
        cases = Case.objects.filter(ngo=user)
    elif user.role == 'LAWYER' and hasattr(user, 'lawyer_profile'):
        lawyer_profile = user.lawyer_profile
        cases = Case.objects.filter(
            Q(assigned_lawyer=lawyer_profile) | 
            Q(status='open')
        ).distinct()
    elif user.role == 'DONOR' and hasattr(user, 'donor_profile'):
        cases = Case.objects.filter(status__in=['open', 'in_progress'])
    else:
        cases = Case.objects.none()
    
    # Apply all the same filters as in advanced_search
    # (This is identical to the filtering logic above)
    # ...
    
    # Now determine export format
    export_format = request.GET.get('format', 'csv')
    
    if export_format == 'csv':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="case_search_results.csv"'
        
        # Create CSV writer
        import csv
        writer = csv.writer(response)
        
        # Write header row
        writer.writerow(['Title', 'Reference', 'Status', 'Created', 'Category', 
                         'Urgency', 'Location', 'Bounty Amount', 'Assigned Lawyer'])
        
        # Write data rows
        for case in cases:
            writer.writerow([
                case.title,
                case.reference_number,
                case.get_status_display(),
                case.created_at.strftime('%Y-%m-%d'),
                case.category.name if case.category else '',
                case.get_urgency_display(),
                case.location,
                case.bounty_amount,
                case.assigned_lawyer.user.get_full_name() if case.assigned_lawyer else 'Unassigned'
            ])
        
        return response
    
    elif export_format == 'pdf':
        # Generate PDF using a library like ReportLab or WeasyPrint
        
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="case_search_results.pdf"'
        
        # Create document
        doc = SimpleDocTemplate(response, pagesize=landscape(letter))
        elements = []
        
        # Define styles
        styles = getSampleStyleSheet()
        title_style = styles['Heading1']
        
        # Add title
        elements.append(Paragraph("Case Search Results", title_style))
        
        # Create table data
        data = [['Title', 'Reference', 'Status', 'Created', 'Category', 
                'Urgency', 'Location', 'Bounty Amount', 'Assigned Lawyer']]
        
        for case in cases:
            data.append([
                case.title,
                case.reference_number,
                case.get_status_display(),
                case.created_at.strftime('%Y-%m-%d'),
                case.category.name if case.category else '',
                case.get_urgency_display(),
                case.location,
                str(case.bounty_amount),
                case.assigned_lawyer.user.get_full_name() if case.assigned_lawyer else 'Unassigned'
            ])
        
        # Create table
        table = Table(data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        
        elements.append(table)
        doc.build(elements)
        
        return response
    
    else:
        # Handle unsupported format
        return HttpResponseBadRequest("Unsupported export format")
    
@login_required
def upload_document(request, case_pk):
    """Upload a document to a case."""
    case = get_object_or_404(Case, pk=case_pk)
    
    # Check permissions
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
            
            messages.success(request, f"Document '{document.name}' uploaded successfully!")
            return redirect('cases:case_detail', pk=case.id)
    else:
        form = CaseDocumentForm()
    
    context = {
        'form': form,
        'case': case,
    }
    return render(request, 'cases/upload_document.html', context)

@login_required
def download_document(request, document_id):
    """Download a case document."""
    document = get_object_or_404(CaseDocument, pk=document_id)
    case = document.case
    
    # Check permissions
    is_case_ngo = (request.user == case.ngo)
    is_assigned_lawyer = (
        request.user.role == 'LAWYER' and
        hasattr(request.user, 'lawyer_profile') and
        case.assigned_lawyer and
        request.user.lawyer_profile == case.assigned_lawyer
    )
    
    if not (is_case_ngo or is_assigned_lawyer):
        return HttpResponseForbidden("You don't have permission to download this document")
    
    # Open the file
    file_path = document.file.path
    return FileResponse(open(file_path, 'rb'), as_attachment=True, filename=document.filename())


@login_required
def wallet_dashboard(request):
    """Display user's token balance and transaction history"""
    wallet, created = UserWallet.objects.get_or_create(user=request.user)
    transactions = TokenTransaction.objects.filter(user=request.user).order_by('-created_at')
    
    paginator = Paginator(transactions, 20)  # 20 transactions per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'wallet': wallet,
        'page_obj': page_obj,
    }
    return render(request, 'cases/wallet_dashboard.html', context)


@login_required
def admin_token_management(request):
    if not request.user.is_staff:
        return HttpResponseForbidden("Admin access required")
    transactions = TokenTransaction.objects.all().order_by('-created_at')
    context = {'transactions': transactions}
    return render(request, 'cases/admin/token_management.html', context)

def award_tokens(user, amount, description, case=None):
    with transaction.atomic():
        # Get or create the user's wallet with all required fields
        current_time = timezone.now()
        wallet, created = UserWallet.objects.get_or_create(
            user=user,
            defaults={
                'balance': 0,
                'created_at': current_time,
                'updated_at': current_time
            }
        )
        
        # Convert amount to Decimal for compatibility with DecimalField
        amount_decimal = Decimal(str(amount))
        
        # Update wallet balance
        wallet.balance += amount_decimal
        wallet.save()
        
        # Create token transaction
        token_transaction = TokenTransaction.objects.create(
            user=user,
            amount=amount_decimal,
            transaction_type='EARN',
            description=description,
            case=case
        )
        
        # Send email notification
        send_mail(
            subject='New Tokens Earned!',
            message=f'You earned {amount} tokens for: {description}',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=True
        )
        
        return token_transaction
    
@login_required
def redeem_tokens(request):
    user = request.user
    
    # Check if user has a wallet, create one if not
    try:
        wallet = user.wallet
    except ObjectDoesNotExist:  # Use ObjectDoesNotExist instead
        # Create a wallet for this user
        wallet = UserWallet.objects.create(user=user)
        # Set initial values
        wallet.balance = 0  # or whatever default makes sense
        wallet.save()

    if request.method == 'POST':
        tokens = int(request.POST.get('tokens', 0))
        reason = request.POST.get('reason')

        # Basic validation
        if tokens <= 0:
            messages.error(request, "Please enter a valid number of tokens.")
            return redirect('cases:lawyer_dashboard')

        wallet = request.user.wallet
        if tokens > wallet.balance:
            messages.error(request, "You don't have enough tokens for this redemption.")
            return redirect('cases:lawyer_dashboard')

        # Deduct tokens
        with transaction.atomic():
            wallet.balance -= tokens
            wallet.save()
            # Record transaction
            TokenTransaction.objects.create(
                user=request.user,
                amount=tokens,
                transaction_type='SPEND',
                description=f"Redeemed {tokens} tokens for {reason}"
            )

        messages.success(request, f"You've successfully redeemed {tokens} tokens!")
        return redirect('cases:lawyer_dashboard')

    return redirect('cases:lawyer_dashboard')

    user = request.user
    
    # Check if user has a wallet, create one if not
    try:
        wallet = user.wallet
    except RelatedObjectDoesNotExist:
        # Create a wallet for this user
        wallet = UserWallet.objects.create(user=user)
        # You might need to set initial values
        wallet.balance = 0  
        wallet.save()
    if request.method == 'POST':
        tokens = int(request.POST.get('tokens', 0))
        reason = request.POST.get('reason')

        # Basic validation
        if tokens <= 0:
            messages.error(request, "Please enter a valid number of tokens.")
            return redirect('cases:lawyer_dashboard')

        wallet = request.user.wallet

        if tokens > wallet.balance:
            messages.error(request, "You don't have enough tokens for this redemption.")
            return redirect('cases:lawyer_dashboard')

        # Deduct tokens
        with transaction.atomic():
            wallet.balance -= tokens
            wallet.save()

            # Record transaction
            TokenTransaction.objects.create(
                user=request.user,
                amount=tokens,
                transaction_type='SPEND',
                description=f"Redeemed {tokens} tokens for {reason}"
            )

        messages.success(request, f"You've successfully redeemed {tokens} tokens!")
        return redirect('cases:lawyer_dashboard')

    return redirect('cases:lawyer_dashboard')

@login_required
def convert_token(request):
     
    #  convert Token to Mpesa
    #   convert Mpesa to Token
        # list the current available currencies for exchange
        # supports Mobile money
        # 1 haKi_Token = 10 USD
        # Give  Token monetary value
      
 
     return redirect('cases:ngo_dashboard')


@login_required
def notifications_list(request):
    notifications = request.user.notifications.all().order_by('-timestamp')
    request.user.notifications.update(unread=False)  # Mark all as read
    return render(request, 'cases/notifications/list.html', {'notifications': notifications})




@login_required
@login_required
@require_POST
def mark_notification_read(request):
    try:
        data = json.loads(request.body)
        notification_id = data.get('id')

        if not notification_id:
            return JsonResponse({'success': False, 'error': 'No notification ID provided'})

        notification = Notification.objects.get(id=notification_id, recipient=request.user)
        notification.is_read = True
        notification.save()

        return JsonResponse({'success': True})
    except Notification.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Notification not found'})
    except Exception:
        return JsonResponse({'success': False, 'error': 'An unexpected error occurred'})
    """
    Mark a single notification as read
    """
    notification_id = request.GET.get('id')
    if notification_id:
        try:
            notification = Notification.objects.get(
                id=notification_id,
                recipient=request.user
            )
            notification.is_read = True
            notification.save()
            return JsonResponse({'success': True})
        except Notification.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Notification not found'})
    
    return JsonResponse({'success': False, 'error': 'No notification ID provided'})


@login_required
@require_POST
def mark_all_notifications_read(request):
    """
    Mark all notifications for the current user as read
    """
    Notification.objects.filter(
        recipient=request.user,
        is_read=False
    ).update(is_read=True)
    
    return JsonResponse({'success': True})