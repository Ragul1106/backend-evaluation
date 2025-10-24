from django.db import models
from django.contrib.auth.models import User

class Parent(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='parent_profile')
    phone = models.CharField(max_length=20, blank=True)

    def __str__(self): return f"Parent {self.user.get_full_name()}"

class Teacher(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='teacher_profile')
    employee_code = models.CharField(max_length=20, unique=True)
    department = models.CharField(max_length=100, blank=True)

    def __str__(self): return f"{self.employee_code} - {self.user.get_full_name()}"

class Course(models.Model):
    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=120)
    description = models.TextField(blank=True)
    def __str__(self): return f"{self.code} - {self.name}"

class Subject(models.Model):
    code = models.CharField(max_length=20)
    name = models.CharField(max_length=120)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='subjects')
    teacher = models.ForeignKey(Teacher, on_delete=models.SET_NULL, null=True, blank=True, related_name='subjects')
    class Meta:
        unique_together = ('code','course')
    def __str__(self): return f"{self.code} - {self.name}"

class ClassRoom(models.Model):
    name = models.CharField(max_length=50)  # e.g., "CSE-A 2025"
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='classes')
    year = models.IntegerField()
    class_teacher = models.ForeignKey(Teacher, on_delete=models.SET_NULL, null=True, blank=True, related_name='classrooms')
    def __str__(self): return f"{self.name}"

class Student(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='student_profile')
    roll_no = models.CharField(max_length=20, unique=True)
    classroom = models.ForeignKey(ClassRoom, on_delete=models.SET_NULL, null=True, related_name='students')
    parent = models.ForeignKey(Parent, on_delete=models.SET_NULL, null=True, related_name='children')
    phone = models.CharField(max_length=20, blank=True)
    address = models.CharField(max_length=200, blank=True)
    def __str__(self): return f"{self.roll_no} - {self.user.get_full_name()}"

class SessionTerm(models.Model):
    name = models.CharField(max_length=50)   # e.g., "2025-26 Term 1"
    start_date = models.DateField()
    end_date = models.DateField()
    def __str__(self): return self.name

ATTEND_STATUS = (('P','Present'),('A','Absent'))
class Attendance(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='attendance')
    classroom = models.ForeignKey('ClassRoom', on_delete=models.CASCADE, null=True, blank=True)
    date = models.DateField()
    present = models.BooleanField(default=True)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='attendance')
    class Meta:
        unique_together = ('date','subject','student')
        ordering = ['-date']

class Exam(models.Model):
    name = models.CharField(max_length=120)  # e.g., "Mid Term"
    session = models.ForeignKey(SessionTerm, on_delete=models.CASCADE, related_name='exams')
    date = models.DateField()
    def __str__(self): return f"{self.name} ({self.session})"

class Mark(models.Model):
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name='marks')
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='marks')
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='marks')
    score = models.DecimalField(max_digits=5, decimal_places=2)
    max_score = models.DecimalField(max_digits=5, decimal_places=2, default=100)
    class Meta:
        unique_together = ('exam','subject','student')
