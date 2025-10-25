from django.contrib.auth.models import User
from core.models import Teacher, Parent, Student, Course, Exam, Marks, Attendance
from datetime import date
import random

# Clear old data (optional)
Marks.objects.all().delete()
Attendance.objects.all().delete()
Exam.objects.all().delete()
Student.objects.all().delete()
Teacher.objects.all().delete()
Parent.objects.all().delete()
Course.objects.all().delete()
User.objects.exclude(is_superuser=True).delete()

print("🧹 Cleared old sample data.")

# --- Create Users ---
t1_user = User.objects.create_user(username="teacher1", password="pass123", first_name="John", last_name="Smith")
t2_user = User.objects.create_user(username="teacher2", password="pass123", first_name="Maria", last_name="Lopez")
p1_user = User.objects.create_user(username="parent1", password="pass123", first_name="Raj", last_name="Kumar")
p2_user = User.objects.create_user(username="parent2", password="pass123", first_name="Anita", last_name="Devi")
s1_user = User.objects.create_user(username="student1", password="pass123", first_name="Ravi", last_name="Singh")
s2_user = User.objects.create_user(username="student2", password="pass123", first_name="Meena", last_name="Kaur")
s3_user = User.objects.create_user(username="student3", password="pass123", first_name="Vijay", last_name="Das")

# --- Create Profiles ---
t1 = Teacher.objects.create(user=t1_user, phone="9991112222")
t2 = Teacher.objects.create(user=t2_user, phone="8881112222")
p1 = Parent.objects.create(user=p1_user, phone="7771112222")
p2 = Parent.objects.create(user=p2_user, phone="6661112222")

# --- Create Courses ---
c1 = Course.objects.create(code="MATH101", name="Mathematics", teacher=t1)
c2 = Course.objects.create(code="SCI101", name="Science", teacher=t2)
c3 = Course.objects.create(code="ENG101", name="English", teacher=t2)

# --- Create Students ---
s1 = Student.objects.create(user=s1_user, roll_no="S001", parent=p1)
s2 = Student.objects.create(user=s2_user, roll_no="S002", parent=p1)
s3 = Student.objects.create(user=s3_user, roll_no="S003", parent=p2)

s1.courses.add(c1, c2, c3)
s2.courses.add(c1, c2)
s3.courses.add(c1, c3)

# --- Create Exams ---
e1 = Exam.objects.create(course=c1, name="Mid Term", date=date(2025, 3, 15))
e2 = Exam.objects.create(course=c2, name="Mid Term", date=date(2025, 3, 17))
e3 = Exam.objects.create(course=c3, name="Final", date=date(2025, 5, 10))

# --- Create Marks ---
Marks.objects.create(student=s1, exam=e1, marks_obtained=85)
Marks.objects.create(student=s1, exam=e2, marks_obtained=90)
Marks.objects.create(student=s1, exam=e3, marks_obtained=88)
Marks.objects.create(student=s2, exam=e1, marks_obtained=70)
Marks.objects.create(student=s2, exam=e2, marks_obtained=75)
Marks.objects.create(student=s3, exam=e1, marks_obtained=92)
Marks.objects.create(student=s3, exam=e3, marks_obtained=89)

# --- Create Attendance ---
for s in [s1, s2, s3]:
    for course in s.courses.all():
        for day in range(1, 8):  # 7 days of attendance
            Attendance.objects.create(
                student=s,
                course=course,
                date=date(2025, 3, day),
                present=random.choice([True, True, True, False])
            )

print("✅ Sample data created successfully!")
print("Login credentials:")
print("  Superuser -> (create manually via createsuperuser)")
print("  Teacher1 -> username: teacher1, password: pass123")
print("  Parent1  -> username: parent1,  password: pass123")
print("  Student1 -> username: student1, password: pass123")
