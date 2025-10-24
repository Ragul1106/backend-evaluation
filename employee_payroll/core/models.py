from django.db import models
from django.utils import timezone
from datetime import datetime, timedelta

class Employee(models.Model):
    code = models.CharField(max_length=20, unique=True)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50, blank=True)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, blank=True)
    department = models.CharField(max_length=100, blank=True)
    designation = models.CharField(max_length=100, blank=True)
    date_of_joining = models.DateField(default=timezone.now)
    base_salary = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    hourly_rate = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    bank_name = models.CharField(max_length=100, blank=True)
    account_no = models.CharField(max_length=50, blank=True)
    ifsc = models.CharField(max_length=20, blank=True)
    pan = models.CharField(max_length=20, blank=True)
    uan = models.CharField(max_length=20, blank=True)
    active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.code} - {self.first_name} {self.last_name}".strip()

ATT_STATUS = (
    ('PRESENT','PRESENT'),
    ('ABSENT','ABSENT'),
    ('LATE','LATE'),
    ('HALF_DAY','HALF_DAY'),
)

class Attendance(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='attendances')
    date = models.DateField()
    check_in = models.TimeField(null=True, blank=True)
    check_out = models.TimeField(null=True, blank=True)
    status = models.CharField(max_length=10, choices=ATT_STATUS, default='PRESENT')
    work_hours = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    overtime_hours = models.DecimalField(max_digits=5, decimal_places=2, default=0)

    class Meta:
        unique_together = ('employee','date')
        ordering = ['-date']

    def save(self, *args, **kwargs):
        if self.check_in and self.check_out:
            dt_in = datetime.combine(self.date, self.check_in)
            dt_out = datetime.combine(self.date, self.check_out)
            if dt_out < dt_in:
                dt_out = dt_out + timedelta(days=1)
            hours = (dt_out - dt_in).total_seconds() / 3600.0
            self.work_hours = round(hours, 2)
            self.overtime_hours = round(max(0.0, hours - 8.0), 2)
            # Simple rules
            if self.work_hours < 4:
                self.status = 'HALF_DAY'
            # Late if after 9:30
            if self.check_in > datetime.strptime('09:30','%H:%M').time():
                if self.status == 'PRESENT':
                    self.status = 'LATE'
        else:
            # No times implies absent unless explicitly set
            if self.status not in ['HALF_DAY','LATE','PRESENT']:
                self.status = 'ABSENT'
        super().save(*args, **kwargs)

LEAVE_TYPES = (
    ('CL','Casual'),
    ('SL','Sick'),
    ('PL','Privilege'),
    ('LOP','Loss of Pay'),
)

class Leave(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='leaves')
    type = models.CharField(max_length=3, choices=LEAVE_TYPES, default='CL')
    start_date = models.DateField()
    end_date = models.DateField()
    approved = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.employee.code} {self.type} {self.start_date} - {self.end_date}"

class PayrollPeriod(models.Model):
    month = models.IntegerField()  # 1-12
    year = models.IntegerField()
    locked = models.BooleanField(default=False)

    class Meta:
        unique_together = ('month','year')
        ordering = ['-year','-month']

    def __str__(self):
        return f"{self.month:02d}/{self.year}"

class PayrollRecord(models.Model):
    period = models.ForeignKey(PayrollPeriod, on_delete=models.CASCADE, related_name='records')
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='payrolls')

    basic = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    hra = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    allowances = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    overtime_pay = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    pf = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    esi = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tax = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    lop = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    gross = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    net = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.employee.code} - {self.period}"
