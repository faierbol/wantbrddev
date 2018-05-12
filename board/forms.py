from django import forms
from django.forms import Textarea
from .models import Board, Item
from django.core.exceptions import ValidationError


class BoardForm(forms.ModelForm):
	class Meta:
		model = Board
		exclude = ['created', 'slug']
		widgets = {'user':forms.HiddenInput()}

	def clean(self):
		cleaned_data = super(BoardForm, self).clean()
		user = cleaned_data.get("user")
		board_name = cleaned_data.get("board_name")
		user_boards = Board.objects.filter(user=user)
		if user_boards.filter(board_name=board_name).exists():		
			raise forms.ValidationError("You already have a board with this name")
		return cleaned_data


class ItemForm(forms.ModelForm):
	class Meta:
		model = Item
		exclude = ['board', 'purchase_url', 'image', 'item_name']
		widgets = {
	        'item_desc': Textarea(),
	    }


class EditBoardForm(forms.ModelForm):
	class Meta:
		model = Board
		exclude = ['created', 'slug']
		widgets = {'user':forms.HiddenInput()}


class ChangeBackgroundForm(forms.ModelForm):
	class Meta:
		model = Board
		file = forms.FileField()
		fields = ['hero', 'user']
		widgets = {'user':forms.HiddenInput()}


class UpdateTags(forms.ModelForm):
	class Meta:
		model = Board
		fields = ['tags', 'user']
		widgets = {'user':forms.HiddenInput()}