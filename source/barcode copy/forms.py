from django import forms
from .models import Website

class WebsiteForm(forms.ModelForm):
    class Meta:
        model = Website
        fields = ['name', 'amount', 'receipt_image', 'picture']