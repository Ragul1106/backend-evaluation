from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, SelectField, DateField, TimeField
from wtforms.validators import DataRequired, Email, Optional

class BookingForm(FlaskForm):
    patient_name = StringField('Your name', validators=[DataRequired()])
    patient_email = StringField('Email', validators=[DataRequired(), Email()])
    patient_phone = StringField('Phone', validators=[Optional()])
    doctor_id = SelectField('Doctor', coerce=int, validators=[DataRequired()])
    date = DateField('Date', format='%Y-%m-%d', validators=[DataRequired()])
    time = TimeField('Time (HH:MM)', format='%H:%M', validators=[DataRequired()])
    submit = SubmitField('Book')

class DoctorLoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = StringField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')
