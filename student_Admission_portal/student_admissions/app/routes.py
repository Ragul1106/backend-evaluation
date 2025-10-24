from flask import Blueprint, render_template, redirect, flash, url_for, request
from .forms import RegistrationForm
from . import db
from .models import Applicant
from .email_utils import send_email
from .sms_utils import send_sms

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    return render_template('register.html', form=RegistrationForm())

@main_bp.route('/apply', methods=['GET', 'POST'])
def apply():
    form = RegistrationForm()
    if form.validate_on_submit():
        app_obj = Applicant(
            full_name=form.full_name.data,
            email=form.email.data,
            phone=form.phone.data,
            dob=form.dob.data,
            course=form.course.data,
            address=form.address.data
        )
        db.session.add(app_obj)
        db.session.commit()

        # send email confirmation
        try:
            send_email(
                "Application Received",
                [app_obj.email],
                "application_received",
                applicant=app_obj
            )
        except Exception as e:
            # log error; do not crash
            print("Email send failed:", e)

        # optional SMS
        if app_obj.phone:
            try:
                send_sms(app_obj.phone, f"Hi {app_obj.full_name}, we received your application. ID: {app_obj.id}")
            except Exception as e:
                print("SMS failed:", e)

        return render_template('thanks.html', applicant=app_obj)
    return render_template('register.html', form=form)
