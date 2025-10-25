from django import forms

class CheckoutForm(forms.Form):
    name = forms.CharField(max_length=120)
    phone = forms.CharField(max_length=30)
    address = forms.CharField(widget=forms.Textarea, required=False)
    # payment_token = forms.CharField(widget=forms.HiddenInput)  # if using stripe token
