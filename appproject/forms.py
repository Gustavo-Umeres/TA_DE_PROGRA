from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model

User = get_user_model()  # Obtiene el modelo de usuario personalizado

class UserRegisterForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        help_text='Requerido. Ingrese una dirección de correo electrónico válida.'
    )
    first_name = forms.CharField(
        max_length=30, required=True, help_text='Requerido. Ingrese su nombre.'
    )
    last_name = forms.CharField(
        max_length=30, required=True, help_text='Requerido. Ingrese su apellido.'
    )

    class Meta:
        model = User  # Ahora referenciamos al modelo correcto
        fields = ('username', 'first_name', 'last_name', 'email', 'password1', 'password2')

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Este correo electrónico ya está en uso.")
        return email

    def clean_password2(self):
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Las contraseñas no coinciden.")
        return password2
