from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from .models import Admin, Applicant
from . import db
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash
from flask import session
from .email_utils import send_email
from .sms_utils import send_sms

admin_bp = Blueprint('admin', __name__, template_folder='templates')

# simple admin auth for demo; for production use proper user creation & hashed password in DB
@admin_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        admin = Admin.query.filter_by(username=username).first()
        if admin and admin.check_password(password):
            login_user(admin)
            return redirect(url_for('admin.dashboard'))
        else:
            flash('Invalid credentials', 'danger')
    return render_template('admin_login.html')

@admin_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('admin.login'))

@admin_bp.route('/')
@login_required
def dashboard():
    # filter by status
    status = request.args.get('status', 'pending')
    applicants = Applicant.query.filter_by(status=status).order_by(Applicant.applied_on.desc()).all()
    return render_template('admin_dashboard.html', applicants=applicants, status=status)

@admin_bp.route('/application/<int:app_id>')
@login_required
def application_detail(app_id):
    a = Applicant.query.get_or_404(app_id)
    return render_template('application_detail.html', applicant=a)

@admin_bp.route('/application/<int:app_id>/update', methods=['POST'])
@login_required
def application_update(app_id):
    a = Applicant.query.get_or_404(app_id)
    action = request.form.get('action')  # 'approve' or 'reject'
    comment = request.form.get('comment', '')
    if action == 'approve':
        a.status = 'approved'
        a.admin_comment = comment
        db.session.commit()
        # send status email/sms
        try:
            send_email('Application Approved', [a.email], 'application_status', applicant=a, status='approved')
        except Exception as e:
            print("Email fail:", e)
        if a.phone:
            try:
                send_sms(a.phone, f"Congrats {a.full_name}, your application (ID: {a.id}) is APPROVED.")
            except Exception as e:
                print("SMS fail:", e)
        flash('Application approved', 'success')
    elif action == 'reject':
        a.status = 'rejected'
        a.admin_comment = comment
        db.session.commit()
        try:
            send_email('Application Rejected', [a.email], 'application_status', applicant=a, status='rejected')
        except Exception as e:
            print("Email fail:", e)
        if a.phone:
            try:
                send_sms(a.phone, f"Hi {a.full_name} — your application (ID: {a.id}) was rejected.")
            except Exception as e:
                print("SMS fail:", e)
        flash('Application rejected', 'warning')
    else:
        flash('Unknown action', 'danger')
    return redirect(url_for('admin.dashboard'))
