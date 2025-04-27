from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from cases.models import Case
from .models import ChatMessage, VideoCallSchedule
from .forms import VideoCallScheduleForm
from rest_framework_simplejwt.tokens import RefreshToken
import json
from django.core.serializers import serialize

@login_required
def case_chat(request, case_pk):
    case = get_object_or_404(Case, pk=case_pk)
    is_ngo = (request.user == case.ngo)
    is_lawyer = (
        request.user.role == 'LAWYER' and
        hasattr(request.user, 'lawyer_profile') and
        case.assigned_lawyer and
        request.user.lawyer_profile == case.assigned_lawyer
    )

    if not (is_ngo or is_lawyer):
        return HttpResponseForbidden("You don't have permission to access this chat")

    refresh = RefreshToken.for_user(request.user)
    access_token = str(refresh.access_token)

    messages_list = ChatMessage.objects.filter(case=case).order_by('timestamp')
    scheduled_calls = VideoCallSchedule.objects.filter(case=case, status__in=['PENDING', 'CONFIRMED']).order_by('scheduled_time')

    # Serialize scheduled_calls to JSON
    scheduled_calls_json = json.dumps([
        {
            'id': call.id,
            'scheduled_time': call.scheduled_time.isoformat(),
            'duration_minutes': call.duration_minutes,
            'status': call.status,
        }
        for call in scheduled_calls
    ])

    context = {
        'case': case,
        'messages': messages_list,
        'access_token': access_token,
        'user_email': request.user.email,
        'scheduled_calls': scheduled_calls_json,
        'is_ngo': is_ngo,
    }
    return render(request, 'chat/case_chat.html', context)

@login_required
def schedule_video_call(request, case_pk):
    case = get_object_or_404(Case, pk=case_pk)
    if request.user != case.ngo or request.user.role != 'NGO':
        return HttpResponseForbidden("Only NGOs can schedule video calls")

    if request.method == 'POST':
        form = VideoCallScheduleForm(request.POST)
        if form.is_valid():
            video_call = form.save(commit=False)
            video_call.case = case
            video_call.created_by = request.user
            video_call.save()

            if case.assigned_lawyer:
                send_mail(
                    f'Video Call Scheduled for Case: {case.title}',
                    f'A video call has been scheduled for {case.title} at {video_call.scheduled_time}. Please log in to confirm or view details.',
                    settings.DEFAULT_FROM_EMAIL,
                    [case.assigned_lawyer.user.email],
                    fail_silently=False,
                )
            messages.success(request, "Video call scheduled successfully!")
            return redirect('chat:case_chat', case_pk=case.pk)
    else:
        form = VideoCallScheduleForm()

    context = {
        'form': form,
        'case': case,
    }
    return render(request, 'chat/schedule_video_call.html', context)

@login_required
def confirm_video_call(request, call_pk):
    video_call = get_object_or_404(VideoCallSchedule, pk=call_pk)
    case = video_call.case
    if (
        request.user.role != 'LAWYER' or
        not hasattr(request.user, 'lawyer_profile') or
        case.assigned_lawyer != request.user.lawyer_profile
    ):
        return HttpResponseForbidden("Only the assigned lawyer can confirm this call")

    video_call.status = 'CONFIRMED'
    video_call.save()

    send_mail(
        f'Video Call Confirmed for Case: {case.title}',
        f'The lawyer has confirmed the video call for {case.title} at {video_call.scheduled_time}.',
        settings.DEFAULT_FROM_EMAIL,
        [case.ngo.email],
        fail_silently=False,
    )
    messages.success(request, "Video call confirmed!")
    return redirect('chat:case_chat', case_pk=case.pk)

@login_required
def cancel_video_call(request, call_pk):
    video_call = get_object_or_404(VideoCallSchedule, pk=call_pk)
    case = video_call.case
    is_ngo = (request.user == case.ngo)
    is_lawyer = (
        request.user.role == 'LAWYER' and
        hasattr(request.user, 'lawyer_profile') and
        case.assigned_lawyer and
        request.user.lawyer_profile == case.assigned_lawyer
    )

    if not (is_ngo or is_lawyer):
        return HttpResponseForbidden("You don't have permission to cancel this call")

    video_call.status = 'CANCELED'
    video_call.save()

    recipient = case.assigned_lawyer.user.email if is_ngo else case.ngo.email
    send_mail(
        f'Video Call Canceled for Case: {case.title}',
        f'The video call for {case.title} scheduled at {video_call.scheduled_time} has been canceled.',
        settings.DEFAULT_FROM_EMAIL,
        [recipient],
        fail_silently=False,
    )
    messages.success(request, "Video call canceled!")
    return redirect('chat:case_chat', case_pk=case.pk)