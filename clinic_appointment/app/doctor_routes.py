from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from .models import Doctor, Appointment
from .forms import DoctorLoginForm
from . import db

doctor_bp = Blueprint('doctor', __name__)

@doctor_bp.route('/login', methods=['GET','POST'])
def login():
    form = DoctorLoginForm()
    if form.validate_on_submit():
        doc = Doctor.query.filter_by(email=form.email.data).first()
        if doc and doc.check_password(form.password.data):
            login_user(doc)
            return redirect(url_for('doctor.dashboard'))
        flash('Invalid credentials', 'danger')
    return render_template('doctor_login.html', form=form)

@doctor_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.index'))

@doctor_bp.route('/dashboard')
@login_required
def dashboard():
    # show upcoming appointments
    appts = Appointment.query.filter_by(doctor_id=current_user.id).order_by(Appointment.date, Appointment.time).all()
    return render_template('doctor_dashboard.html', appointments=appts)

@doctor_bp.route('/appointment/<int:id>/update', methods=['POST'])
@login_required
def update_appointment(id):
    appt = Appointment.query.get_or_404(id)
    action = request.form.get('action')
    if action == 'confirm':
        appt.status = 'confirmed'
    elif action == 'cancel':
        appt.status = 'canceled'
    db.session.commit()
    flash('Appointment updated', 'success')
    return redirect(url_for('doctor.dashboard'))
