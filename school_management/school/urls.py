from django.urls import path
from . import views

urlpatterns = [
  path('', views.dashboard, name='dashboard'),

  path('students/', views.student_list, name='student_list'),
  path('students/new/', views.student_create, name='student_create'),
  path('students/<int:pk>/', views.student_detail, name='student_detail'),

  path('teachers/', views.teacher_list, name='teacher_list'),
  path('teachers/new/', views.teacher_create, name='teacher_create'),

  path('courses/', views.course_list, name='course_list'),
  path('courses/new/', views.course_create, name='course_create'),
  path('subjects/', views.subject_list, name='subject_list'),
  path('subjects/new/', views.subject_create, name='subject_create'),
  path('classes/', views.classroom_list, name='classroom_list'),
  path('classes/new/', views.classroom_create, name='classroom_create'),

  path('attendance/take/', views.attendance_take, name='attendance_take'),
  path('attendance/report/', views.attendance_report, name='attendance_report'),

  path('exams/', views.exam_periods, name='exam_periods'),
  path('exams/marks/', views.marks_entry, name='marks_entry'),
  path('exams/results/', views.exam_results, name='exam_results'),

  path('parent/', views.parent_portal, name='parent_portal'),
]
