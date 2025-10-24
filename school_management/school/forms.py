from django import forms
from .models import Student, Teacher, Course, Subject, ClassRoom, Attendance, Mark, Exam

class StudentForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = ['user','roll_no','classroom','parent','phone','address']

class TeacherForm(forms.ModelForm):
    class Meta:
        model = Teacher
        fields = ['user','employee_code','department']

class CourseForm(forms.ModelForm):
    class Meta: model = Course; fields = ['code','name','description']

class SubjectForm(forms.ModelForm):
    class Meta: model = Subject; fields = ['code','name','course','teacher']

class ClassRoomForm(forms.ModelForm):
    class Meta: model = ClassRoom; fields = ['name','course','year','class_teacher']

class AttendanceTakeForm(forms.Form):
    date = forms.DateField(widget=forms.DateInput(attrs={'type':'date'}))
    subject = forms.ModelChoiceField(queryset=Subject.objects.all())
    classroom = forms.ModelChoiceField(queryset=ClassRoom.objects.all())

class MarksEntryForm(forms.Form):
    exam = forms.ModelChoiceField(queryset=Exam.objects.all())
    subject = forms.ModelChoiceField(queryset=Subject.objects.all())
    classroom = forms.ModelChoiceField(queryset=ClassRoom.objects.all())
