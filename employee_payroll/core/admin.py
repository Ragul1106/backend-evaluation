from django.contrib import admin
from .models import Employee, Attendance, Leave, PayrollPeriod, PayrollRecord

@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ('code','first_name','last_name','department','designation','base_salary','active')
    search_fields = ('code','first_name','last_name','email','phone','department','designation')
    list_filter = ('department','designation','active')

@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ('employee','date','check_in','check_out','status','work_hours','overtime_hours')
    list_filter = ('status','date')
    search_fields = ('employee__code','employee__first_name','employee__last_name')

@admin.register(Leave)
class LeaveAdmin(admin.ModelAdmin):
    list_display = ('employee','type','start_date','end_date','approved')
    list_filter = ('type','approved')

@admin.register(PayrollPeriod)
class PayrollPeriodAdmin(admin.ModelAdmin):
    list_display = ('month','year','locked')
    list_filter = ('year','locked')

@admin.register(PayrollRecord)
class PayrollRecordAdmin(admin.ModelAdmin):
    list_display = ('employee','period','gross','net')
    list_filter = ('period__year','period__month')
    search_fields = ('employee__code','employee__first_name','employee__last_name')
