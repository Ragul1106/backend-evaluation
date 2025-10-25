from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import User

class EmployerSignUpForm(UserCreationForm):
    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = User.Roles.EMPLOYER
        if commit:
            user.save()
        return user

class ApplicantSignUpForm(UserCreationForm):
    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = User.Roles.APPLICANT
        if commit:
            user.save()
        return user

class LoginForm(AuthenticationForm):
    pass
