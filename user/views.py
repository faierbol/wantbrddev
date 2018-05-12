from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.http import HttpResponseRedirect
from .forms import SignUpForm, UserForm
from .models import Profile, Connection
from board.models import Board, Item
from django.core.exceptions import PermissionDenied
from django.forms.models import inlineformset_factory


# viewing your own profile
@login_required
def home(request):
	template = "user/index.html"	
	editable = True
	user = request.user
	boards = Board.objects.filter(user=user.id)
	# get the tags for each board
	for board in boards:
		board.thetags = board.tags.all()
		items = Item.objects.filter(board=board)
		board.items = items.count()

	saved_board = Board.objects.get(user=user.id, slug="your-saved-items")
	saved_board_items = Item.objects.filter(board=saved_board)
	
	profile = request.user.profile
	connections = profile.get_connections()
	followers = profile.get_followers()
	no_connections = profile.get_connections().count()
	no_followers = profile.get_followers().count()
	context_dict = {
		'profile': profile,
		'no_connections': no_connections,
		'no_followers': no_followers,
		'connections': connections,
		'followers': followers,
		'boards': boards,
		'saved_board':saved_board,
		'saved_board_items':saved_board_items,
		'editable':editable
	}

	if request.method == 'POST':

		# check we have submitted a want or rec create 
		if request.POST.get("createwantboard") or request.POST.get("createrecboard"):
			
			#check the board name has not already been used
			new_board_name = request.POST.get("boardname","")
			user_boards = Board.objects.filter(user=user)

			if user_boards.filter(board_name=new_board_name).exists():
				errors = {
					'error':"You already have a board with this name",
				}
				context_dict.update(errors)
				
				return render(request, template, context_dict)

			# if the name is not aready used by this user
			else:
				# set the board type
				if 'createwantboard' in request.POST:
					board_type = "Want"
				else:
					board_type = "Recommended"	
				#create the board
				new_board = Board.objects.create (
					user = user,
					board_name = new_board_name,
					board_type = board_type,
				)
				#redirect to edit board page using new model
				return redirect('b:edit_board', board_id=new_board.id)

		elif 'deleteboard' in request.POST:
			board = get_object_or_404(Board, pk=request.POST.get("board_id",""))
			board.delete()
			return redirect('u:home')

	return render(request, template, context_dict)


def signup(request):
	template = 'user/signup.html'

	if request.method == 'POST':
		form = SignUpForm(request.POST)
		if form.is_valid():
			user = form.save();
			login(request, user)
			return redirect('u:home')
	else:
		form = SignUpForm()
	
	return render(request, template, {'form':form})


@login_required
def my_account(request):
	template = "user/my_account.html"
	return render(request, template)


@login_required
def update_account(request):
	template = "user/update_account.html"

	# querying the User object with pk from url
	user = User.objects.get(pk=request.user.id)

	# prepopulate UserProfileForm with retrieved user values from above.
	user_form = UserForm(instance=user)

	ProfileInlineFormset = inlineformset_factory(User, Profile, fields=(
		'website', 'bio', 'country', 'date_of_birth', 'phone_number',
		'picture', 'alert_new_subscribe', 'alert_new_item', 'alert_suggested_boards'
	))
	formset = ProfileInlineFormset(instance=user)

	if request.method == "POST":
		user_form = UserForm(request.POST, request.FILES, instance=user)
		formset = ProfileInlineFormset(request.POST, request.FILES, instance=user)

		if user_form.is_valid():
			created_user = user_form.save(commit=False)
			formset = ProfileInlineFormset(request.POST, request.FILES, instance=created_user)
			
			if formset.is_valid():
				created_user.save()
				formset.save()
				return redirect('u:update_account')

	return render(request, template, {
		"userid": user.id,
		"form": user_form,
		"formset": formset,
	})


# viewing someone elses profile
def profile(request, username):
	template = 'user/index.html'	

	try:
		user = get_object_or_404(User, username=username)
		boards = Board.objects.filter(user=user.id)
		# get the tags for each board
		for board in boards:
			board.thetags = board.tags.all()
			items = Item.objects.filter(board=board)
			board.items = items.count()
		profile = user.profile
		connections = profile.get_connections()
		followers = profile.get_followers()
		no_connections = profile.get_connections().count()
		no_followers = profile.get_followers().count()

		is_followed = False
		for auser in followers:
			if request.user == auser.creator:
				is_followed = True

		context_dict = {
			'profile': profile,
			'no_connections': no_connections,
			'no_followers': no_followers,
			'connections': connections,
			'followers': followers,
			'is_followed': is_followed,
			'boards': boards,
		}

	except:
		context_dict = {
			# 'editable': editable,
		}

	# handle submissions
	if request.method == 'POST':

		# get current user
		current_user = request.user

		# if user followed
		if 'follow' in request.POST:
			new_connection = Connection.objects.create(
				creator = current_user,
				following = user,
			)

		#if user unfollowed
		if 'unfollow' in request.POST:
			connection = Connection.objects.filter(creator=current_user, following=user)
			connection.delete()

		return HttpResponseRedirect(request.path_info)

	return render(request, template, context_dict)