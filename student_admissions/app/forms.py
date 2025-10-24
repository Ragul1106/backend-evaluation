from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField, SelectField, DateField
from wtforms.validators import DataRequired, Email, Length, Optional

class RegistrationForm(FlaskForm):
    full_name = StringField('Full name', validators=[DataRequired(), Length(max=200)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    phone = StringField('Phone', validators=[Optional(), Length(max=30)])
    dob = DateField('Date of Birth', format='%Y-%m-%d', validators=[Optional()])
    course = SelectField('Desired Course', choices=[
        ('bsc','B.Sc'), ('ba','B.A'), ('bcom','B.Com'), ('mca','MCA')
    ])
    address = TextAreaField('Address', validators=[Optional(), Length(max=2000)])
    submit = SubmitField('Apply')
