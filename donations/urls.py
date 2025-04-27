# donations/urls.py
from django.urls import path
from . import views

app_name = 'donations'

urlpatterns = [
    path('donor/browse/', views.browse_cases, name='browse_cases'),
    path('case/<int:pk>/', views.case_detail, name='case_detail'),
    path('donate/<int:case_pk>/', views.donate_to_case, name='donate_to_case'),  # Updated to use case_pk
    path('my-donations/', views.my_donations, name='my_donations'),
]