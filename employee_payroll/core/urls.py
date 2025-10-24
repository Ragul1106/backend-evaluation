from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),

    path('employees/', views.employee_list, name='employee_list'),
    path('employees/new/', views.employee_create, name='employee_create'),
    path('employees/<int:pk>/edit/', views.employee_edit, name='employee_edit'),
    path('employees/<int:pk>/', views.employee_detail, name='employee_detail'),
    path('employees/<int:pk>/delete/', views.employee_delete, name='employee_delete'),

    path('attendance/', views.attendance_list, name='attendance_list'),
    path('attendance/new/', views.attendance_create, name='attendance_create'),
    path('attendance/<int:pk>/edit/', views.attendance_edit, name='attendance_edit'),
    path('attendance/bulk/', views.attendance_bulk, name='attendance_bulk'),
    path('attendance/export/xlsx/', views.attendance_export_excel, name='attendance_export_excel'),

    path('payroll/periods/', views.payroll_periods, name='payroll_periods'),
    path('payroll/generate/', views.payroll_generate, name='payroll_generate'),
    path('payroll/<int:period_id>/records/', views.payroll_records, name='payroll_records'),
    path('payroll/<int:period_id>/export/xlsx/', views.payroll_export_excel, name='payroll_export_excel'),
    path('payroll/payslip/<int:record_id>/pdf/', views.payroll_payslip_pdf, name='payroll_payslip_pdf'),
]
