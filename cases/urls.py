from django.urls import path
from . import views

app_name = 'cases'

urlpatterns = [
    # NGO Dashboard
    path('ngo/dashboard/', views.ngo_dashboard, name='ngo_dashboard'),
    
    # Case Management
    path('ngo/cases/', views.list_cases, name='list_cases'),
    path('ngo/cases/create/', views.create_case, name='case_create'),
    path('ngo/cases/<int:pk>/', views.case_detail, name='case_detail'),
    path('ngo/cases/<int:pk>/edit/', views.edit_case, name='edit_case'),
    path('ngo/cases/<int:pk>/history/', views.case_history, name='case_history'),
    path('ngo/cases/<int:pk>/funding-history/', views.funding_history, name='funding_history'),
    path('ngo/cases/<int:pk>/updates/', views.case_updates, name='case_updates'),
    path('ngo/cases/<int:pk>/approve-completion/', views.approve_completion, name='approve_completion'),
    path('cases/<int:case_pk>/milestones/', views.set_milestones, name='set_milestones'),
    
    # Document Management
    path('cases/<int:case_pk>/upload-document/', views.upload_document, name='upload_document'),
    path('documents/<int:pk>/delete/', views.delete_document, name='delete_document'),
    
    # Case Updates
    path('cases/<int:case_pk>/add-update/', views.add_update, name='add_update'),
    
    # Lawyer Applications
    path('ngo/cases/<int:case_pk>/applications/', views.view_applications, name='view_applications'),
    path('ngo/applications/<int:application_pk>/<str:status>/', views.update_application_status, name='update_application_status'),
    path('case/<int:case_pk>/invite-lawyer/', views.invite_lawyers, name='invite_lawyers'),
    path('case/<int:case_pk>/rate-lawyer/', views.rate_lawyer, name='rate_lawyer'),
    
    # Case Review
    path('ngo/cases/<int:pk>/review/', views.review_completed_case, name='review_case'),
    
    # Donations
    path('ngo/cases/<int:case_pk>/donations/', views.view_donations, name='view_donations'),

    # Lawyer features
    path('lawyer/cases/', views.lawyer_cases, name='lawyer_cases'),
    path('browse/', views.redirect_browse_cases, name='browse_cases'),  
    path('lawyer/browse/', views.lawyer_browse_cases, name='lawyer_browse_cases'), 
    path('apply/<int:pk>/', views.apply_for_case, name='apply_for_case'),
    path('lawyer/dashboard/', views.lawyer_dashboard, name='lawyer_dashboard'),
    path('lawyer/case/<int:pk>/', views.case_detail_lawyer, name='case_detail_lawyer'),
    path('lawyer/case/<int:case_pk>/progress/', views.submit_progress, name='submit_progress'),
    path('lawyer/case/<int:case_pk>/complete/', views.submit_case_completion, name='submit_case_completion'),
    path('lawyer/ratings/', views.lawyer_ratings, name='lawyer_ratings'),
    path('lawyer/success-stories/', views.lawyer_success_stories, name='lawyer_success_stories'),
    path('lawyer/success-stories/add/', views.add_success_story, name='add_success_story'),
    path('lawyer/success-stories/add/<int:case_pk>/', views.add_success_story, name='add_case_success_story'),
    path('lawyer/profile/<int:lawyer_id>/', views.lawyer_profile_public, name='lawyer_profile_public'),

    # NGO features related to lawyers
    path('case/<int:case_pk>/rate-lawyer/', views.rate_lawyer, name='rate_lawyer'),

    # Search Cases
    path('cases/search/', views.search_cases, name='search_cases'),# Search Cases
    
]