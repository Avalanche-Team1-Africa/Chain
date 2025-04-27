from django.urls import path
from . import views

app_name = 'chat'

urlpatterns = [
    path('case/<int:case_pk>/', views.case_chat, name='case_chat'),
    path('case/<int:case_pk>/schedule/', views.schedule_video_call, name='schedule_video_call'),
    path('call/<int:call_pk>/confirm/', views.confirm_video_call, name='confirm_video_call'),
    path('call/<int:call_pk>/cancel/', views.cancel_video_call, name='cancel_video_call'),
]