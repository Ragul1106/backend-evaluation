from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Count, Avg, Q
from .models import Parent, Teacher, Course, Subject, ClassRoom, Student, SessionTerm, Attendance, Exam, Mark
from .forms import StudentForm, TeacherForm, CourseForm, SubjectForm, ClassRoomForm, AttendanceTakeForm, MarksEntryForm

def is_admin(u): return u.is_staff
def is_teacher(u): return hasattr(u, 'teacher_profile')
def is_student(u): return hasattr(u, 'student_profile')
def is_parent(u): return hasattr(u, 'parent_profile')

@login_required
def dashboard(request):
    if is_admin(request.user):
        stats = {
            'students': Student.objects.count(),
            'teachers': Teacher.objects.count(),
            'courses': Course.objects.count(),
            'subjects': Subject.objects.count(),
        }
        return render(request, 'dashboard_admin.html', {'stats': stats})
    if is_teacher(request.user):
        t = request.user.teacher_profile
        classes = ClassRoom.objects.filter(class_teacher=t).count()
        subs = t.subjects.count()
        return render(request, 'dashboard_teacher.html', {'classes': classes, 'subjects': subs})
    if is_student(request.user):
        s = request.user.student_profile
        att_pct = Attendance.objects.filter(student=s).aggregate(
            p=Count('id', filter=Q(status='P'))
        )
        total = Attendance.objects.filter(student=s).count()
        pct = round((att_pct['p'] or 0) * 100.0 / total, 2) if total else 0.0
        avg_score = Mark.objects.filter(student=s).aggregate(a=Avg('score'))['a'] or 0
        return render(request, 'dashboard_student.html', {'attendance_pct': pct, 'avg_score': avg_score})
    if is_parent(request.user):
        p = request.user.parent_profile
        kids = p.children.select_related('classroom').all()
        return render(request, 'dashboard_parent.html', {'children': kids})
    return redirect('login')

# Admin CRUD samples
@login_required 
@user_passes_test(is_admin)
def student_list(request):
    students = Student.objects.select_related('user','classroom').all()
    return render(request, 'students/list.html', {'students': students})

@login_required 
@user_passes_test(is_admin)
def student_create(request):
    if request.method == 'POST':
        form = StudentForm(request.POST)
        if form.is_valid():
            form.save(); messages.success(request,'Student created'); return redirect('student_list')
    else: form = StudentForm()
    return render(request, 'students/form.html', {'form': form})

@login_required
def student_detail(request, pk):
    s = get_object_or_404(Student, pk=pk)
    marks = Mark.objects.filter(student=s).select_related('exam','subject')
    att_p = Attendance.objects.filter(student=s, status='P').count()
    att_t = Attendance.objects.filter(student=s).count()
    pct = round(att_p*100.0/att_t, 2) if att_t else 0.0
    return render(request, 'students/detail.html', {'s': s, 'marks': marks, 'attendance_pct': pct})

@login_required 
@user_passes_test(is_admin)
def teacher_list(request):
    teachers = Teacher.objects.select_related('user').all()
    return render(request, 'teachers/list.html', {'teachers': teachers})

@login_required 
@user_passes_test(is_admin)
def teacher_create(request):
    if request.method == 'POST':
        form = TeacherForm(request.POST)
        if form.is_valid():
            form.save(); messages.success(request,'Teacher added'); return redirect('teacher_list')
    else: form = TeacherForm()
    return render(request, 'teachers/form.html', {'form': form})

@login_required 
@user_passes_test(is_admin)
def course_list(request):
    return render(request, 'courses/list.html', {'courses': Course.objects.all()})

@login_required 
@user_passes_test(is_admin)
def course_create(request):
    form = CourseForm(request.POST or None)
    if request.method=='POST' and form.is_valid():
        form.save(); messages.success(request,'Course added'); return redirect('course_list')
    return render(request, 'courses/form.html', {'form': form})

@login_required 
@user_passes_test(is_admin)
def subject_list(request):
    return render(request, 'subjects/list.html', {'subjects': Subject.objects.select_related('course','teacher').all()})

@login_required 
@user_passes_test(is_admin)
def subject_create(request):
    form = SubjectForm(request.POST or None)
    if request.method=='POST' and form.is_valid():
        form.save(); messages.success(request,'Subject added'); return redirect('subject_list')
    return render(request, 'subjects/form.html', {'form': form})

@login_required 
@user_passes_test(is_admin)
def classroom_list(request):
    return render(request, 'classes/list.html', {'classes': ClassRoom.objects.select_related('course','class_teacher').all()})

@login_required 
@user_passes_test(is_admin)
def classroom_create(request):
    form = ClassRoomForm(request.POST or None)
    if request.method=='POST' and form.is_valid():
        form.save(); messages.success(request,'Class created'); return redirect('classroom_list')
    return render(request, 'classes/form.html', {'form': form})

# Attendance
@login_required 
@user_passes_test(lambda u: is_teacher(u) or u.is_staff)
def attendance_take(request):
    from datetime import date as dt
    subjects = Subject.objects.all()
    classrooms = ClassRoom.objects.all()
    if request.method == 'POST':
        date = request.POST.get('date')
        subject_id = request.POST.get('subject')
        classroom_id = request.POST.get('classroom')
        cls = get_object_or_404(ClassRoom, pk=classroom_id)
        sub = get_object_or_404(Subject, pk=subject_id)
        for s in cls.students.select_related('user'):
            status = request.POST.get(f'status_{s.id}', 'A')
            Attendance.objects.update_or_create(
                date=date, subject=sub, student=s, defaults={'classroom': cls, 'status': status}
            )
        messages.success(request, 'Attendance saved')
        return redirect('attendance_report')
    return render(request, 'attendance/take.html', {'subjects': subjects, 'classrooms': classrooms})

@login_required
def attendance_report(request):
    classroom_id = request.GET.get('classroom')
    subject_id = request.GET.get('subject')
    qs = Attendance.objects.select_related('student','subject','classroom')
    if classroom_id: qs = qs.filter(classroom_id=classroom_id)
    if subject_id: qs = qs.filter(subject_id=subject_id)
    return render(request, 'attendance/report.html', {
        'records': qs.order_by('-date')[:200],
        'classes': ClassRoom.objects.all(),
        'subjects': Subject.objects.all(),
    })

# Exams & Marks
@login_required 
@user_passes_test(is_admin)
def exam_periods(request):
    exams = Exam.objects.select_related('session').all().order_by('-date')
    sessions = SessionTerm.objects.all()
    if request.method == 'POST':
        name = request.POST.get('name'); session_id = request.POST.get('session'); date = request.POST.get('date')
        Exam.objects.create(name=name, session_id=session_id, date=date)
        messages.success(request, 'Exam created'); return redirect('exam_periods')
    return render(request, 'exams/periods.html', {'exams': exams, 'sessions': sessions})

@login_required 
@user_passes_test(lambda u: is_teacher(u) or u.is_staff)
def marks_entry(request):
    exams = Exam.objects.all()
    subjects = Subject.objects.all()
    classes = ClassRoom.objects.all()
    if request.method == 'POST':
        exam_id = request.POST.get('exam'); subject_id = request.POST.get('subject'); class_id = request.POST.get('classroom')
        cls = get_object_or_404(ClassRoom, pk=class_id); sub = get_object_or_404(Subject, pk=subject_id)
        for s in cls.students.all():
            score = request.POST.get(f'score_{s.id}')
            if score is not None and score != '':
                Mark.objects.update_or_create(exam_id=exam_id, subject=sub, student=s, defaults={'score': score, 'max_score': 100})
        messages.success(request, 'Marks saved'); return redirect('exam_results')
    return render(request, 'exams/marks_entry.html', {'exams': exams, 'subjects': subjects, 'classes': classes})

@login_required
def exam_results(request):
    classroom_id = request.GET.get('classroom')
    qs = Mark.objects.select_related('student','exam','subject')
    if classroom_id:
        qs = qs.filter(student__classroom_id=classroom_id)
    return render(request, 'exams/results.html', {
        'marks': qs.order_by('student__roll_no', 'subject__name'),
        'classes': ClassRoom.objects.all(),
    })

# Parent portal
@login_required 
@user_passes_test(is_parent)
def parent_portal(request):
    p = request.user.parent_profile
    children = p.children.select_related('classroom').all()
    return render(request, 'dashboard_parent.html', {'children': children})
