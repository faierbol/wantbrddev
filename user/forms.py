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
		fields = ('bio', 'website', 'country', 'date_of_birth', 'phone_number')
		widgets = {
			'bio':forms.Textarea(attrs={'placeholder': 'Tell people about yourself', 'rows':20, 'cols':100}),
			'website':forms.TextInput(attrs={'placeholder': 'Your website address'}),			
			'phone_number':forms.TextInput(attrs={'placeholder': 'Yourt telephone number'}),
			'alert_new_subscribe':forms.CheckboxInput(attrs={'name': 'alert_new_sub', 'hidden': 'hidden', 'id':'alert_new_sub'}), 
			'alert_new_item':forms.CheckboxInput(attrs={'name': 'alert_new_item', 'hidden': 'hidden', 'id':'alert_new_item'}),
			'alert_suggested_boards':forms.CheckboxInput(attrs={'name': 'alert_sug_board', 'hidden': 'hidden', 'id':'alert_sug_board'}),
			'date_of_birth':forms.TextInput(attrs={'data-toggle':'datepicker'}),
		}


class PrivacyForm(forms.ModelForm):	
	class Meta:
		model = Profile		
		fields = ('global_privacy', 'user')
		widgets = {'user':forms.HiddenInput()}


class SettingsForm(forms.ModelForm):	
	class Meta:
		model = Profile		
		fields = ('alert_new_subscribe', 'alert_new_item', 'alert_suggested_boards', 'user')
		widgets = {
			'alert_new_subscribe':forms.CheckboxInput(attrs={'hidden': 'hidden', 'id':'alert_new_sub'}), 
			'alert_new_item':forms.CheckboxInput(attrs={'hidden': 'hidden', 'id':'alert_new_item'}),
			'alert_suggested_boards':forms.CheckboxInput(attrs={'hidden': 'hidden', 'id':'alert_sug_board'}),
			'user':forms.HiddenInput(),
		}


class ChangeBackgroundForm(forms.ModelForm):
	background = forms.ImageField(label=(''),required=False, widget=forms.FileInput(attrs={'class': "jfilestyle"}))
	class Meta:
		model = Profile		
		fields = ['background', 'user']
		widgets = {'user':forms.HiddenInput()}


class UpdateSocial(forms.ModelForm):
	class Meta:
		model = Profile
		fields = ['social_instagram', 'social_facebook', 'social_twitter', 'social_youtube',
		'social_twitch', 'social_vimeo', 'social_pinterest', 'social_weibo', 'social_vk', 'user']
		widgets = {
			'user':forms.HiddenInput(),
			'social_instagram':forms.TextInput(attrs={'placeholder': 'Your Instagram username'}),
			'social_facebook':forms.TextInput(attrs={'placeholder': 'Your Facebook username'}),
			'social_twitter':forms.TextInput(attrs={'placeholder': 'Your Twitter username'}),
			'social_youtube':forms.TextInput(attrs={'placeholder': 'Your Youtube username'}),
			'social_twitch':forms.TextInput(attrs={'placeholder': 'Your Twitch username'}),
			'social_vimeo':forms.TextInput(attrs={'placeholder': 'Your Vimeo username'}),
			'social_pinterest':forms.TextInput(attrs={'placeholder': 'Your Pinterest username'}),
			'social_weibo':forms.TextInput(attrs={'placeholder': 'Your Weibo username'}),
			'social_vk':forms.TextInput(attrs={'placeholder': 'Your VK username'}),
		}