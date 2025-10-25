from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.mail import send_mail
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView

from accounts.models import User
from .models import Job, Application
from .forms import JobForm, ApplicationForm, JobSearchForm
from .filters import filter_jobs

class EmployerRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.role == User.Roles.EMPLOYER

class JobListView(ListView):
    model = Job
    template_name = 'jobs/job_list.html'
    context_object_name = 'jobs'
    paginate_by = 10

    def get_queryset(self):
        qs = Job.objects.select_related('poster').all()
        form = JobSearchForm(self.request.GET)
        if form.is_valid():
            q = form.cleaned_data.get('q')
            location = form.cleaned_data.get('location')
            qs = filter_jobs(qs, q=q, location=location)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['form'] = JobSearchForm(self.request.GET or None)
        return ctx

class JobDetailView(DetailView):
    model = Job
    template_name = 'jobs/job_detail.html'
    context_object_name = 'job'

class JobCreateView(LoginRequiredMixin, EmployerRequiredMixin, CreateView):
    model = Job
    form_class = JobForm
    template_name = 'jobs/job_form.html'
    success_url = reverse_lazy('accounts:employer_dashboard')

    def form_valid(self, form):
        form.instance.poster = self.request.user
        messages.success(self.request, 'Job posted successfully!')
        return super().form_valid(form)

class JobOwnerRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        job = self.get_object()
        return self.request.user.is_authenticated and job.poster == self.request.user

class JobUpdateView(LoginRequiredMixin, EmployerRequiredMixin, JobOwnerRequiredMixin, UpdateView):
    model = Job
    form_class = JobForm
    template_name = 'jobs/job_form.html'
    success_url = reverse_lazy('accounts:employer_dashboard')

    def form_valid(self, form):
        messages.success(self.request, 'Job updated successfully!')
        return super().form_valid(form)

class JobDeleteView(LoginRequiredMixin, EmployerRequiredMixin, JobOwnerRequiredMixin, DeleteView):
    model = Job
    template_name = 'jobs/job_confirm_delete.html'
    success_url = reverse_lazy('accounts:employer_dashboard')

class ApplicationListView(LoginRequiredMixin, ListView):
    model = Application
    template_name = 'applications/application_list.html'
    context_object_name = 'applications'
    paginate_by = 10

    def get_queryset(self):
        user = self.request.user
        if user.role == User.Roles.EMPLOYER:
            return Application.objects.filter(job__poster=user).select_related('job', 'applicant')
        return Application.objects.filter(applicant=user).select_related('job')

def apply_to_job(request, job_id):
    job = get_object_or_404(Job, id=job_id)
    if not request.user.is_authenticated:
        return redirect('accounts:login')
    if request.user.role != User.Roles.APPLICANT:
        messages.error(request, 'Only applicants can apply to jobs.')
        return redirect('jobs:job_detail', pk=job.id)

    if request.method == 'POST':
        form = ApplicationForm(request.POST, request.FILES)
        if form.is_valid():
            app, created = Application.objects.get_or_create(
                job=job,
                applicant=request.user,
                defaults={
                    'cover_letter': form.cleaned_data['cover_letter'],
                    'resume': form.cleaned_data['resume'],
                }
            )
            if not created:
                messages.warning(request, 'You have already applied to this job.')
            else:
                messages.success(request, 'Application submitted! A confirmation email has been sent.')
                subject = f"Application Received: {job.title} at {job.company}"
                body = (
                    f"Hi {request.user.username},\n\n"
                    f"Your application for '{job.title}' at {job.company} has been received.\n"
                    f"We will keep you posted on the status.\n\n"
                    f"Thanks,\nJob Portal"
                )
                send_mail(subject, body, None, [request.user.email], fail_silently=True)

                if job.poster.email:
                    send_mail(
                        f"New Application: {job.title}",
                        f"You have a new application from {request.user.username}.",
                        None,
                        [job.poster.email],
                        fail_silently=True,
                    )
            return redirect('jobs:job_detail', pk=job.id)
    else:
        form = ApplicationForm()
    return render(request, 'applications/apply_form.html', {'form': form, 'job': job})

def withdraw_application(request, pk):
    if not request.user.is_authenticated:
        return redirect('accounts:login')
    application = get_object_or_404(Application, pk=pk)
    if application.applicant != request.user:
        messages.error(request, 'You can only withdraw your own applications.')
        return redirect('jobs:application_list')
    application.status = Application.Status.WITHDRAWN
    application.save(update_fields=['status'])
    messages.success(request, 'Application withdrawn.')
    return redirect('jobs:application_list')
