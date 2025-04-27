from django.db import models
from django.conf import settings
from cases.models import Case
from django.utils.translation import gettext_lazy as _

class ChatMessage(models.Model):
    case = models.ForeignKey(Case, on_delete=models.CASCADE, related_name='chat_messages')
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ['timestamp']

    def __str__(self):
        return f"{self.sender.email} - {self.case.title} - {self.timestamp}"

class VideoCallSchedule(models.Model):
    STATUS_CHOICES = (
        ('PENDING', 'Pending'),
        ('CONFIRMED', 'Confirmed'),
        ('CANCELED', 'Canceled'),
        ('COMPLETED', 'Completed'),
    )

    case = models.ForeignKey(Case, on_delete=models.CASCADE, related_name='video_call_schedules')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='scheduled_calls')
    scheduled_time = models.DateTimeField()
    duration_minutes = models.PositiveIntegerField(default=30)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Call for {self.case.title} at {self.scheduled_time}"