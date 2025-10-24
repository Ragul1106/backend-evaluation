from django import forms
from .models import Employee, Attendance

class EmployeeForm(forms.ModelForm):
    class Meta:
        model = Employee
        fields = ['code','first_name','last_name','email','phone','department','designation',
                  'date_of_joining','base_salary','hourly_rate','bank_name','account_no','ifsc','pan','uan','active']

class AttendanceForm(forms.ModelForm):
    class Meta:
        model = Attendance
        fields = ['employee','date','check_in','check_out','status']
        widgets = {
            'date': forms.DateInput(attrs={'type':'date'}),
            'check_in': forms.TimeInput(attrs={'type':'time'}),
            'check_out': forms.TimeInput(attrs={'type':'time'}),
        }

class BulkAttendanceForm(forms.Form):
    date = forms.DateField(widget=forms.DateInput(attrs={'type':'date'}))
