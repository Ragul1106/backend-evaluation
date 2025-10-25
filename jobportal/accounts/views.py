from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from .forms import EmployerSignUpForm, ApplicantSignUpForm
from .models import User
from jobs.models import Job, Application

def signup_employer(request):
    if request.method == 'POST':
        form = EmployerSignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('accounts:employer_dashboard')
    else:
        form = EmployerSignUpForm()
    return render(request, 'registration/signup_employer.html', {'form': form})

def signup_applicant(request):
    if request.method == 'POST':
        form = ApplicantSignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('accounts:applicant_dashboard')
    else:
        form = ApplicantSignUpForm()
    return render(request, 'registration/signup_applicant.html', {'form': form})

@login_required
def employer_dashboard(request):
    if request.user.role != User.Roles.EMPLOYER:
        return redirect('accounts:applicant_dashboard')
    jobs = Job.objects.filter(poster=request.user).order_by('-created_at')
    applications = Application.objects.filter(job__poster=request.user).select_related('job', 'applicant')
    return render(request, 'dashboards/employer_dashboard.html', {
        'jobs': jobs,
        'applications': applications,
    })

@login_required
def applicant_dashboard(request):
    if request.user.role != User.Roles.APPLICANT:
        return redirect('accounts:employer_dashboard')
    applications = Application.objects.filter(applicant=request.user).select_related('job')
    return render(request, 'dashboards/applicant_dashboard.html', {
        'applications': applications,
    })
