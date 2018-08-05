from django import forms
from django.forms import Textarea
from .models import Board, Item, ItemConnection
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
		model = ItemConnection
		fields = ['purchase_url', 'item_desc', 'item_status', 'rating', 'review', 'active']
		widgets = {
	        'item_desc': Textarea(),
	        'rating':forms.HiddenInput(),
	        'active' : forms.CheckboxInput(attrs={'id': 'itemactive', 'hidden':'hidden'})
	    }


class EditBoardForm(forms.ModelForm):
	class Meta:
		model = Board
		exclude = ['created', 'slug']
		widgets = {'user':forms.HiddenInput()}


class ChangeBackgroundForm(forms.ModelForm):
	hero = forms.ImageField(label=(''),required=False, widget=forms.FileInput(attrs={'class': "jfilestyle"}))
	class Meta:
		model = Board		
		fields = ['hero', 'user']
		widgets = {'user':forms.HiddenInput()}


class UpdateTags(forms.ModelForm):
	class Meta:
		model = Board
		fields = ['tags', 'user']
		widgets = {'user':forms.HiddenInput()}

	def clean_tags(self):
	    """
	    Force all tags to lowercase.
	    """
	    tags = self.cleaned_data.get('tags', None)
	    if tags:
	        tags = [t.lower() for t in tags]

	    return tags