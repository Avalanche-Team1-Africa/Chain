from django import forms
from .models import VideoCallSchedule
from django.utils import timezone

class VideoCallScheduleForm(forms.ModelForm):
    class Meta:
        model = VideoCallSchedule
        fields = ['scheduled_time', 'duration_minutes']
        widgets = {
            'scheduled_time': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'duration_minutes': forms.NumberInput(attrs={'min': 15, 'max': 120}),
        }

    def clean_scheduled_time(self):
        scheduled_time = self.cleaned_data['scheduled_time']
        if scheduled_time < timezone.now():
            raise forms.ValidationError("Scheduled time cannot be in the past.")
        return scheduled_time