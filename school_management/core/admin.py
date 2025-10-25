from django.contrib import admin
from .models import Teacher, Parent, Course, Student, Exam, Marks, Attendance

@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = ("user", "phone")

@admin.register(Parent)
class ParentAdmin(admin.ModelAdmin):
    list_display = ("user", "phone")

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "teacher")

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ("roll_no", "user", "parent")
    filter_horizontal = ("courses",)

@admin.register(Exam)
class ExamAdmin(admin.ModelAdmin):
    list_display = ("course", "name", "date")

@admin.register(Marks)
class MarksAdmin(admin.ModelAdmin):
    list_display = ("student", "exam", "marks_obtained")

@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ("student", "course", "date", "present")
