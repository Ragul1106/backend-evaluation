from django.contrib import admin
from .models import Parent, Teacher, Course, Subject, ClassRoom, Student, SessionTerm, Attendance, Exam, Mark

for m in [Parent,Teacher,Course,Subject,ClassRoom,Student,SessionTerm,Attendance,Exam,Mark]:
    admin.site.register(m)
