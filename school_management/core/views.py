from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import Student, Parent, Marks, Attendance, Exam, Course
from .forms import MarksForm, AttendanceForm, ExamForm
from django.contrib import messages
from django.db import IntegrityError

def index(request):
    courses = Course.objects.all()[:10]
    return render(request, "core/index.html", {"courses": courses})

@login_required
def student_detail(request, pk):
    student = get_object_or_404(Student, pk=pk)
    marks = student.marks.select_related("exam", "exam__course").all()
    attendance = student.attendance.select_related("course").all().order_by("-date")[:50]
    return render(request, "core/student_detail.html", {"student": student, "marks": marks, "attendance": attendance})

@login_required
def parent_dashboard(request):
    # Parents see their children
    try:
        parent = request.user.parent_profile
    except:
        messages.error(request, "You are not a parent account.")
        return redirect("core:index")
    children = parent.children.all()
    # For each child, gather marks & attendance summary
    children_data = []
    for child in children:
        marks = child.marks.select_related("exam", "exam__course").all()
        attendance = child.attendance.all()
        total_days = attendance.count()
        present_days = attendance.filter(present=True).count()
        attendance_pct = (present_days / total_days * 100) if total_days else None
        children_data.append({
            "student": child,
            "marks": marks,
            "attendance_pct": attendance_pct,
        })
    return render(request, "core/parent_dashboard.html", {"children_data": children_data})

@login_required
def attendance_entry(request):
    # Limited: staff or teacher should be allowed in real app
    if request.method == "POST":
        form = AttendanceForm(request.POST)
        if form.is_valid():
            try:
                form.save()
                messages.success(request, "Attendance saved.")
                return redirect("core:attendance_entry")
            except IntegrityError:
                messages.error(request, "Attendance for this student/course/date already exists.")
    else:
        form = AttendanceForm()
    recent = Attendance.objects.select_related("student", "course").order_by("-date")[:20]
    return render(request, "core/attendance_entry.html", {"form": form, "recent": recent})

@login_required
def marks_entry(request):
    if request.method == "POST":
        form = MarksForm(request.POST)
        if form.is_valid():
            try:
                form.save()
                messages.success(request, "Marks recorded.")
                return redirect("core:marks_entry")
            except IntegrityError:
                messages.error(request, "Marks for this student & exam already exist.")
    else:
        form = MarksForm()
    recent = Marks.objects.select_related("student", "exam").order_by("-exam__date")[:20]
    return render(request, "core/marks_entry.html", {"form": form, "recent": recent})

@login_required
def exam_create(request):
    if request.method == "POST":
        form = ExamForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Exam created.")
            return redirect("core:exam_create")
    else:
        form = ExamForm()
    exams = Exam.objects.select_related("course").order_by("-date")[:20]
    return render(request, "core/exam_create.html", {"form": form, "exams": exams})
