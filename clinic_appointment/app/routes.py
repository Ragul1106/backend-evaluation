from flask import Blueprint, render_template, redirect, url_for, flash, request
from .models import Doctor, Appointment
from .forms import BookingForm
from . import db
from .email_utils import send_email
from .sms_utils import send_sms

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    doctors = Doctor.query.all()
    return render_template('index.html', doctors=doctors)

@main_bp.route('/book', methods=['GET','POST'])
def book():
    form = BookingForm()
    # populate doctors choices
    form.doctor_id.choices = [(d.id, d.name) for d in Doctor.query.all()]
    if form.validate_on_submit():
        # check slot availability
        existing = Appointment.query.filter_by(doctor_id=form.doctor_id.data,
                                               date=form.date.data,
                                               time=form.time.data).first()
        if existing:
            flash('Selected slot is already taken. Pick another.', 'danger')
            return render_template('book.html', form=form)

        appt = Appointment(
            patient_name=form.patient_name.data,
            patient_email=form.patient_email.data,
            patient_phone=form.patient_phone.data,
            doctor_id=form.doctor_id.data,
            date=form.date.data,
            time=form.time.data
        )
        db.session.add(appt)
        db.session.commit()

        # Send email confirmation (best to background this)
        try:
            send_email('Appointment Received', [appt.patient_email], 'emails/appointment_received', appointment=appt)
        except Exception as e:
            print('Email error:', e)

        if appt.patient_phone:
            try:
                send_sms(appt.patient_phone, f"Appointment received for {appt.date} {appt.time}")
            except Exception as e:
                print('SMS error:', e)

        return render_template('thanks.html', appointment=appt)
    return render_template('book.html', form=form)
