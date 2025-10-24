from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

# Extend User for Teacher or Parent profiles via OneToOne if needed.
class Teacher(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="teacher_profile")
    phone = models.CharField(max_length=20, blank=True)

    def __str__(self):
        return self.user.get_full_name() or self.user.username

class Parent(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="parent_profile")
    phone = models.CharField(max_length=20, blank=True)

    def __str__(self):
        return self.user.get_full_name() or self.user.username

class Course(models.Model):
    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=200)
    teacher = models.ForeignKey(Teacher, on_delete=models.SET_NULL, null=True, blank=True, related_name="courses")

    def __str__(self):
        return f"{self.code} - {self.name}"

class Student(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="student_profile")
    roll_no = models.CharField(max_length=30, unique=True)
    courses = models.ManyToManyField(Course, related_name="students", blank=True)
    parent = models.ForeignKey(Parent, on_delete=models.SET_NULL, null=True, blank=True, related_name="children")

    def __str__(self):
        return f"{self.roll_no} - {self.user.get_full_name() or self.user.username}"

class Exam(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="exams")
    name = models.CharField(max_length=200)
    date = models.DateField(default=timezone.now)

    def __str__(self):
        return f"{self.course.code} - {self.name}"

class Marks(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="marks")
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name="marks")
    marks_obtained = models.DecimalField(max_digits=6, decimal_places=2)

    class Meta:
        unique_together = ("student", "exam")

    def __str__(self):
        return f"{self.student.roll_no} - {self.exam.name}: {self.marks_obtained}"

class Attendance(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="attendance")
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="attendance")
    date = models.DateField(default=timezone.now)
    present = models.BooleanField(default=True)

    class Meta:
        unique_together = ("student", "course", "date")

    def __str__(self):
        return f"{self.student.roll_no} - {self.course.code} - {self.date} - {'P' if self.present else 'A'}"
