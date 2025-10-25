from django.urls import path
from .views import (
    JobListView, JobDetailView, JobCreateView, JobUpdateView, JobDeleteView,
    apply_to_job, withdraw_application, ApplicationListView
)

app_name = 'jobs'

urlpatterns = [
    path('', JobListView.as_view(), name='job_list'),
    path('jobs/<int:pk>/', JobDetailView.as_view(), name='job_detail'),
    path('employer/jobs/create/', JobCreateView.as_view(), name='job_create'),
    path('employer/jobs/<int:pk>/edit/', JobUpdateView.as_view(), name='job_update'),
    path('employer/jobs/<int:pk>/delete/', JobDeleteView.as_view(), name='job_delete'),

    path('applications/', ApplicationListView.as_view(), name='application_list'),
    path('jobs/<int:job_id>/apply/', apply_to_job, name='apply'),
    path('applications/<int:pk>/withdraw/', withdraw_application, name='withdraw'),
]
