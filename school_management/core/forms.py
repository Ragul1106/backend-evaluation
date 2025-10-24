from django import forms
from .models import Marks, Attendance, Exam

class MarksForm(forms.ModelForm):
    class Meta:
        model = Marks
        fields = ["student", "exam", "marks_obtained"]

class AttendanceForm(forms.ModelForm):
    class Meta:
        model = Attendance
        fields = ["student", "course", "date", "present"]

class ExamForm(forms.ModelForm):
    class Meta:
        model = Exam
        fields = ["course", "name", "date"]
