from django import forms
from .models import Order
import re

class CheckoutForm(forms.Form):
    name = forms.CharField(
        max_length=120,
        required=True,
        widget=forms.TextInput(attrs={'placeholder': 'Enter your full name'})
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={'placeholder': 'example@gmail.com'})
    )
    phone = forms.CharField(
        max_length=10,
        required=True,
        widget=forms.TextInput(attrs={'placeholder': '10-digit mobile number'})
    )
    address = forms.CharField(
        max_length=255,
        required=True,
        widget=forms.TextInput(attrs={'placeholder': 'House no, Street, Area'})
    )
    city = forms.CharField(
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={'placeholder': 'City name'})
    )
    pincode = forms.CharField(
        max_length=12,
        required=True,
        widget=forms.TextInput(attrs={'placeholder': '6-digit pin code'})
    )

    payment_method = forms.ChoiceField(
        choices=Order.PAYMENT_METHOD_CHOICES,
        initial="stripe",
        widget=forms.RadioSelect,
        required=True
    )

    # --- VALIDATIONS ---

    # Name: letters and spaces only (no numbers/special chars)
    def clean_name(self):
        name = self.cleaned_data.get("name", "").strip()
        if not re.match(r'^[A-Za-z ]+$', name):
            raise forms.ValidationError("Name should contain letters and spaces only (no numbers or special characters).")
        return name

    # Email: valid AND must be a Gmail address (name@gmail.com)
    def clean_email(self):
        email = self.cleaned_data.get("email", "").strip()
        if not re.match(r'^[A-Za-z0-9._%+-]+@gmail\.com$', email, flags=re.IGNORECASE):
            raise forms.ValidationError("Enter a valid Gmail address like name@gmail.com.")
        return email

    # Phone: Indian 10-digit mobile (starts with 6/7/8/9)
    def clean_phone(self):
        phone = self.cleaned_data.get("phone", "").strip()
        if not re.match(r'^[6-9]\d{9}$', phone):
            raise forms.ValidationError("Enter a valid 10-digit Indian mobile number (must start with 6, 7, 8, or 9).")
        return phone

    # Pincode: strict 6 digits
    def clean_pincode(self):
        pincode = self.cleaned_data.get("pincode", "").strip()
        if not re.match(r'^\d{6}$', pincode):
            raise forms.ValidationError("Enter a valid 6-digit pincode.")
        return pincode
