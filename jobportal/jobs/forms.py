from django import forms
from .models import Job, Application

class JobSearchForm(forms.Form):
    q = forms.CharField(label='Keyword', required=False)
    location = forms.CharField(label='Location', required=False)

class JobForm(forms.ModelForm):
    class Meta:
        model = Job
        fields = ['title', 'company', 'location', 'description']

class ApplicationForm(forms.ModelForm):
    class Meta:
        model = Application
        fields = ['cover_letter', 'resume']
        widgets = {
            'cover_letter': forms.Textarea(attrs={'rows': 5}),
        }
