from django import forms
from .models import SampleModel

class SampleForm(forms.ModelForm):
    class Meta:
        model = SampleModel
        fields = ['nombre', 'direccion']
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Nombre completo'
            }),
            'direccion': forms.EmailInput(attrs={
                'class': 'form-input',
                'placeholder': 'correo@ejemplo.com'
            })
        }
        labels = {
            'nombre': 'Nombre',
            'direccion': 'Correo Electrónico'
        }