from django import forms
from .models import Complaint, ComplaintAttachment


class ComplaintForm(forms.ModelForm):
    class Meta:
        model = Complaint
        fields = ['title', 'description', 'priority']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Brief title of the complaint',
                'required': True
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Detailed description of the complaint',
                'rows': 5,
                'required': True
            }),
            'priority': forms.Select(attrs={
                'class': 'form-control'
            }),
        }


class ComplaintAttachmentForm(forms.ModelForm):
    class Meta:
        model = ComplaintAttachment
        fields = ['file']
        widgets = {
            'file': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.doc,.docx,.jpg,.jpeg,.png,.txt'
            }),
        }


class LandlordResponseForm(forms.ModelForm):
    class Meta:
        model = Complaint
        fields = ['landlord_response', 'status']
        widgets = {
            'landlord_response': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Your response to the complaint',
                'rows': 5,
                'required': True
            }),
            'status': forms.Select(attrs={
                'class': 'form-control'
            }),
        }
