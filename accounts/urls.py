from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'accounts'

urlpatterns = [
    path('register/', views.RegisterView.as_view(), name='register'),
    path('login/', auth_views.LoginView.as_view(template_name='accounts/login.html'), name='login'),
    # path('logout/', auth_views.LogoutView.as_view(next_page='accounts:login'), name='logout'),
    path('logout/', views.logout_view, name='logout'),
    path('verify-email/', views.VerifyEmailView.as_view(), name='verify_email'),
    path('profile-setup/', views.ProfileSetupView.as_view(), name='profile_setup'),
    path('profile/', views.ProfileView.as_view(), name='profile'),
    path('ngo/profile/', views.NGOProfileView.as_view(), name='ngo_profile'),
    path('lawyer/profile/', views.LawyerProfileView.as_view(), name='lawyer_profile'),  
    path('donor/profile/', views.DonorProfileView.as_view(), name='donor_profile'),   
    path('settings/', views.settings_view, name='settings'),  # Add this line
    path('dashboard/', views.dashboard, name='dashboard'),
    path('ngo/dashboard/', views.ngo_dashboard, name='ngo_dashboard'),
    path('lawyer/dashboard/', views.lawyer_dashboard, name='lawyer_dashboard'),
    path('donor/dashboard/', views.donor_dashboard, name='donor_dashboard'),
]