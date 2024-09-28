from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.models import User

from .models import Advertisement, Newsletter


class RegistrationForm(forms.ModelForm):
    code = forms.CharField(max_length=6, required=False)
    username = forms.CharField(max_length=150)
    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = get_user_model()
        fields = ['username', 'email', 'password', 'code']


class AuthForm(forms.ModelForm):
    username = forms.CharField(max_length=150)
    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ['email', 'password', 'username']


class ConfirmationForm(forms.ModelForm):
    code = forms.CharField(max_length=10)

    class Meta:
        model = User
        fields = ['code']


class AdvertisementForm(forms.ModelForm):
    class Meta:
        model = Advertisement
        fields = ['title', 'text', 'category', 'image']


class NewsletterForm(forms.ModelForm):
    class Meta:
        model = Newsletter
        fields = ['title', 'content', 'recipients']


class ResponseForm(forms.Form):
    content = forms.CharField(label='Текст отклика', widget=forms.Textarea)


class NewsForm(forms.Form):
    title = forms.CharField(label='Title', max_length=100)
    content = forms.CharField(label='Content', widget=forms.Textarea)
