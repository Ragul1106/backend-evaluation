from django.test import TestCase

# Create your tests here.
from django.urls import path
from . import views

app_name = "core"

urlpatterns = [
    path("", views.index, name="index"),
    path("student/<int:pk>/", views.student_detail, name="student_detail"),
    path("parent/dashboard/", views.parent_dashboard, name="parent_dashboard"),
    path("attendance/entry/", views.attendance_entry, name="attendance_entry"),
    path("marks/entry/", views.marks_entry, name="marks_entry"),
    path("exam/create/", views.exam_create, name="exam_create"),
]
