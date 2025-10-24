from io import BytesIO
from django.http import HttpResponse
from django.template.loader import get_template
# from weasyprint import HTML
import openpyxl

def export_attendance_excel(rows, filename='attendance.xlsx'):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = 'Attendance'
    headers = ['Emp Code','Name','Date','Status','Check In','Check Out','Hours','OT Hours']
    ws.append(headers)
    for r in rows:
        ws.append(r)
    stream = BytesIO()
    wb.save(stream)
    stream.seek(0)
    resp = HttpResponse(stream.read(), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    resp['Content-Disposition'] = f'attachment; filename="{filename}"'
    return resp

def export_payroll_excel(rows, filename='payroll.xlsx'):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = 'Payroll'
    headers = ['Emp Code','Name','Basic','HRA','Allowances','OT Pay','PF','ESI','Tax','LOP','Gross','Net']
    ws.append(headers)
    for r in rows:
        ws.append(r)
    stream = BytesIO()
    wb.save(stream)
    stream.seek(0)
    resp = HttpResponse(stream.read(), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    resp['Content-Disposition'] = f'attachment; filename="{filename}"'
    return resp

import pdfkit
from django.http import HttpResponse
from django.template.loader import get_template

def render_pdf(template_name, context, filename='payslip.pdf'):
    html = get_template(template_name).render(context)
    # options: tune as needed (margins, page size)
    options = {
        'page-size': 'A4',
        'encoding': "UTF-8",
        # 'margin-top': '10mm', 'margin-bottom': '10mm', ...
    }
    # returns bytes when output_path=False
    pdf_bytes = pdfkit.from_string(html, False, options=options)
    resp = HttpResponse(pdf_bytes, content_type='application/pdf')
    resp['Content-Disposition'] = f'attachment; filename="{filename}"'
    return resp
