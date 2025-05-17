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
    path('case/<int:case_pk>/assign/<int:lawyer_id>/', views.assign_lawyer, name='assign_lawyer'),
    
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
    

    # Calendar related URLs
    path('calendar/', views.case_calendar, name='case_calendar'),
    path('events/add/', views.add_event, name='add_event'),
    path('cases/<int:case_pk>/events/add/', views.add_event, name='add_case_event'),
    path('events/<int:event_id>/', views.event_detail, name='event_detail'),


    # Message related URLs
    path('cases/<int:case_pk>/messages/', views.case_messages, name='case_messages'),
    path('cases/<int:case_pk>/messages/load/<int:last_message_id>/', 
         views.load_new_messages, name='load_new_messages'),
    path('cases/<int:case_pk>/messages/mark-read/', 
         views.mark_messages_read, name='mark_messages_read'),


          path('document-templates/', views.document_templates, name='document_templates'),
    path('cases/<int:case_pk>/generate-document/<int:template_pk>/', 
         views.generate_document, name='generate_document'),
    path('document-templates/<int:template_pk>/download/', 
         views.download_template, name='download_template'),


         # Document related URLs
    path('cases/<int:case_pk>/documents/upload/', views.upload_document, name='upload_document'),
    # path('documents/<int:document_id>/', views.document_detail, name='document_detail'),
    path('documents/<int:document_id>/download/', views.download_document, name='download_document'),
    

    path('wallet/', views.wallet_dashboard, name='wallet_dashboard'),
    path('token/redeem/', views.redeem_tokens, name='redeem_tokens'),

     path('token/award/', views.award_tokens, name='award_tokens'),
     # Notifications
    path('lawyer/notifications/', views.lawyer_notifications, name='lawyer_notifications'),
    path('notifications/mark-read/', views.mark_notification_read, name='mark_notification_read'),
    path('notifications/mark-all-read/', views.mark_all_notifications_read, name='mark_all_notifications_read'),
]
    