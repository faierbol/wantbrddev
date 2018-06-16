from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Profile

class SignUpForm(UserCreationForm):
	email = forms.CharField(max_length=254, required=True, widget=forms.EmailInput())
	class Meta:
		model = User
		fields = ('username', 'email', 'first_name', 'last_name', 'password1', 'password2')


class UserForm(forms.ModelForm):
	class Meta:
		model = User
		fields = ('email', 'first_name', 'last_name')


class ProfileForm(forms.ModelForm):
	class Meta:
		model = Profile
		fields = ('bio', 'website')

class ChangeBackgroundForm(forms.ModelForm):
	class Meta:
		model = Profile
		file = forms.FileField()
		fields = ['background', 'user']
		widgets = {'user':forms.HiddenInput()}