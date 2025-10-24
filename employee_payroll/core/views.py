from calendar import monthrange
from datetime import date
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Sum, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.core.paginator import Paginator
from django.utils import timezone

from .models import Employee, Attendance, PayrollPeriod, PayrollRecord
from .forms import EmployeeForm, AttendanceForm, BulkAttendanceForm
from .calculators import compute_payroll_for_employee
from .exports import export_attendance_excel, export_payroll_excel, render_pdf

def staff_required(view):
    return login_required(user_passes_test(lambda u: u.is_staff)(view))

@login_required
def dashboard(request):
    emp_count = Employee.objects.filter(active=True).count()
    today = timezone.localdate()
    this_month = today.month
    this_year = today.year
    present_today = Attendance.objects.filter(date=today, status__in=['PRESENT','LATE','HALF_DAY']).count()
    last_period = PayrollPeriod.objects.order_by('-year','-month').first()
    return render(request, 'dashboard.html', {
        'emp_count': emp_count,
        'present_today': present_today,
        'last_period': last_period,
    })

# Employees
@staff_required
def employee_list(request):
    q = request.GET.get('q','')
    qs = Employee.objects.all()
    if q:
        qs = qs.filter(Q(code__icontains=q)|Q(first_name__icontains=q)|Q(last_name__icontains=q)|Q(email__icontains=q))
    paginator = Paginator(qs.order_by('code'), 20)
    page = request.GET.get('page')
    employees = paginator.get_page(page)
    return render(request, 'employees/list.html', {'employees': employees, 'q': q})

@staff_required
def employee_create(request):
    if request.method == 'POST':
        form = EmployeeForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Employee created')
            return redirect('employee_list')
    else:
        form = EmployeeForm()
    return render(request, 'employees/form.html', {'form': form})

@staff_required
def employee_edit(request, pk):
    emp = get_object_or_404(Employee, pk=pk)
    if request.method == 'POST':
        form = EmployeeForm(request.POST, instance=emp)
        if form.is_valid():
            form.save()
            messages.success(request, 'Employee updated')
            return redirect('employee_list')
    else:
        form = EmployeeForm(instance=emp)
    return render(request, 'employees/form.html', {'form': form})

@staff_required
def employee_detail(request, pk):
    emp = get_object_or_404(Employee, pk=pk)
    return render(request, 'employees/detail.html', {'emp': emp})

@staff_required
def employee_delete(request, pk):
    emp = get_object_or_404(Employee, pk=pk)
    emp.delete()
    messages.success(request, 'Employee deleted')
    return redirect('employee_list')

# Attendance
@staff_required
def attendance_list(request):
    emp_id = request.GET.get('employee')
    month = int(request.GET.get('month', date.today().month))
    year = int(request.GET.get('year', date.today().year))
    qs = Attendance.objects.select_related('employee').filter(date__month=month, date__year=year)
    if emp_id:
        qs = qs.filter(employee_id=emp_id)
    paginator = Paginator(qs.order_by('-date'), 25)
    page = request.GET.get('page')
    attendances = paginator.get_page(page)
    employees = Employee.objects.all().order_by('code')
    return render(request, 'attendance/list.html', {
        'attendances': attendances, 'employees': employees, 'selected_employee': emp_id, 'month': month, 'year': year
    })

@staff_required
def attendance_create(request):
    if request.method == 'POST':
        form = AttendanceForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Attendance saved')
            return redirect('attendance_list')
    else:
        form = AttendanceForm()
    return render(request, 'attendance/form.html', {'form': form})

@staff_required
def attendance_edit(request, pk):
    att = get_object_or_404(Attendance, pk=pk)
    if request.method == 'POST':
        form = AttendanceForm(request.POST, instance=att)
        if form.is_valid():
            form.save()
            messages.success(request, 'Attendance updated')
            return redirect('attendance_list')
    else:
        form = AttendanceForm(instance=att)
    return render(request, 'attendance/form.html', {'form': form})

@staff_required
def attendance_bulk(request):
    employees = Employee.objects.filter(active=True).order_by('code')
    if request.method == 'POST':
        form = BulkAttendanceForm(request.POST)
        if form.is_valid():
            dt = form.cleaned_data['date']
            for emp in employees:
                status = request.POST.get(f'status_{emp.id}', 'ABSENT')
                check_in = request.POST.get(f'check_in_{emp.id}') or None
                check_out = request.POST.get(f'check_out_{emp.id}') or None
                Attendance.objects.update_or_create(
                    employee=emp, date=dt,
                    defaults={'status': status, 'check_in': check_in, 'check_out': check_out}
                )
            messages.success(request, 'Bulk attendance saved')
            return redirect('attendance_list')
    else:
        form = BulkAttendanceForm()
    return render(request, 'attendance/bulk.html', {'form': form, 'employees': employees})

@staff_required
def attendance_export_excel(request):
    emp_id = request.GET.get('employee')
    month = int(request.GET.get('month', date.today().month))
    year = int(request.GET.get('year', date.today().year))
    qs = Attendance.objects.select_related('employee').filter(date__month=month, date__year=year)
    if emp_id:
        qs = qs.filter(employee_id=emp_id)
    rows = []
    for a in qs.order_by('employee__code','date'):
        rows.append([
            a.employee.code,
            f"{a.employee.first_name} {a.employee.last_name}".strip(),
            a.date.isoformat(),
            a.status,
            a.check_in.isoformat() if a.check_in else '',
            a.check_out.isoformat() if a.check_out else '',
            float(a.work_hours),
            float(a.overtime_hours),
        ])
    return export_attendance_excel(rows, filename=f'attendance_{year}_{month:02d}.xlsx')

@staff_required
def payroll_periods(request):
    periods = PayrollPeriod.objects.all()
    return render(request, 'payroll/periods.html', {'periods': periods})

@staff_required
def payroll_generate(request):
    if request.method == 'POST':
        month = int(request.POST.get('month'))
        year = int(request.POST.get('year'))
        period, _ = PayrollPeriod.objects.get_or_create(month=month, year=year)
        if period.locked:
            messages.warning(request, 'Period locked')
            return redirect('payroll_periods')

        # compute for each employee
        employees = Employee.objects.filter(active=True)
        # Determine month range
        _, last_day = monthrange(year, month)
        start_dt = date(year, month, 1)
        end_dt = date(year, month, last_day)

        # wipe existing
        PayrollRecord.objects.filter(period=period).delete()

        for emp in employees:
            qs = Attendance.objects.filter(employee=emp, date__range=(start_dt, end_dt))
            present = qs.filter(status__in=['PRESENT','LATE','HALF_DAY']).count()
            absents = qs.filter(status='ABSENT').count()
            half_days = qs.filter(status='HALF_DAY').count()
            ot_hours = qs.aggregate(s=Sum('overtime_hours'))['s'] or 0
            # LOP assume absents are LOP
            summary = {
                'present_days': present,
                'absent_days': absents,
                'half_days': half_days,
                'ot_hours': ot_hours,
                'lop_days': absents + (half_days * 0.5),
            }
            comp = compute_payroll_for_employee(emp, summary)
            PayrollRecord.objects.create(
                period=period, employee=emp,
                basic=comp['basic'], hra=comp['hra'], allowances=comp['allowances'],
                overtime_pay=comp['overtime_pay'], pf=comp['pf'], esi=comp['esi'],
                tax=comp['tax'], lop=comp['lop'], gross=comp['gross'], net=comp['net']
            )
        messages.success(request, 'Payroll generated')
        return redirect('payroll_records', period_id=period.id)
    return redirect('payroll_periods')

@staff_required
def payroll_records(request, period_id):
    period = get_object_or_404(PayrollPeriod, pk=period_id)
    records = PayrollRecord.objects.select_related('employee').filter(period=period)
    return render(request, 'payroll/records.html', {'period': period, 'records': records})

@staff_required
def payroll_export_excel(request, period_id):
    period = get_object_or_404(PayrollPeriod, pk=period_id)
    records = PayrollRecord.objects.select_related('employee').filter(period=period).order_by('employee__code')
    rows = []
    for r in records:
        rows.append([
            r.employee.code,
            f"{r.employee.first_name} {r.employee.last_name}".strip(),
            float(r.basic), float(r.hra), float(r.allowances), float(r.overtime_pay),
            float(r.pf), float(r.esi), float(r.tax), float(r.lop),
            float(r.gross), float(r.net)
        ])
    return export_payroll_excel(rows, filename=f'payroll_{period.year}_{period.month:02d}.xlsx')

@staff_required
def payroll_payslip_pdf(request, record_id):
    r = get_object_or_404(PayrollRecord, pk=record_id)
    ctx = {'r': r}
    return render_pdf('payroll/payslip_pdf.html', ctx, filename=f'payslip_{r.employee.code}_{r.period.year}_{r.period.month:02d}.pdf')
