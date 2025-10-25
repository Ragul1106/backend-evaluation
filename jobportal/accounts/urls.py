from django.urls import path
from django.contrib.auth import views as auth_views
from .views import signup_employer, signup_applicant, employer_dashboard, applicant_dashboard

app_name = 'accounts'

urlpatterns = [
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('signup/employer/', signup_employer, name='signup_employer'),
    path('signup/applicant/', signup_applicant, name='signup_applicant'),
    path('dashboard/employer/', employer_dashboard, name='employer_dashboard'),
    path('dashboard/applicant/', applicant_dashboard, name='applicant_dashboard'),
]
