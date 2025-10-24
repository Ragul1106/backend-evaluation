from decimal import Decimal

def compute_payroll_for_employee(emp, month_summary):
    # month_summary: dict with keys 'present_days','absent_days','half_days','ot_hours','lop_days'
    base = Decimal(emp.base_salary or 0)
    hourly = Decimal(emp.hourly_rate or 0)
    basic = (base * Decimal('0.50')).quantize(Decimal('0.01'))
    hra = (basic * Decimal('0.40')).quantize(Decimal('0.01'))
    allowances = (base - basic - hra).quantize(Decimal('0.01')) if base > 0 else Decimal('0.00')
    ot_pay = (Decimal(month_summary.get('ot_hours',0)) * hourly * Decimal('1.5')).quantize(Decimal('0.01'))

    # Deductions
    pf = (basic * Decimal('0.12')).quantize(Decimal('0.01'))  # cap can be applied as needed
    esi = Decimal('0.00')  # left simple
    # simple flat tax 5% of (base + ot)
    tax = ((base + ot_pay) * Decimal('0.05')).quantize(Decimal('0.01')) if base > 0 else Decimal('0.00')

    # LOP proportional per working day (assume 26 working days)
    lop_days = Decimal(month_summary.get('lop_days', 0))
    lop = ((base / Decimal('26')) * lop_days).quantize(Decimal('0.01')) if base > 0 else Decimal('0.00')

    gross = (basic + hra + allowances + ot_pay).quantize(Decimal('0.01'))
    total_deductions = (pf + esi + tax + lop).quantize(Decimal('0.01'))
    net = (gross - total_deductions).quantize(Decimal('0.01'))

    return {
        'basic': basic, 'hra': hra, 'allowances': allowances, 'overtime_pay': ot_pay,
        'pf': pf, 'esi': esi, 'tax': tax, 'lop': lop,
        'gross': gross, 'net': net,
    }
