from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.http import HttpResponseRedirect
from .forms import SignUpForm, UserForm, ChangeBackgroundForm
from .models import Profile, Connection
from board.models import Board, Item, ItemConnection, BoardView, ItemLike, ItemView, BoardPrivacy
from django.core.exceptions import PermissionDenied
from django.forms.models import inlineformset_factory


# viewing your own profile
@login_required
def home(request):
	template = "user/index.html"	
	editable = True
	user = request.user
	boards = Board.objects.filter(user=user.id)
	
	for board in boards:
		board.items = []
		# get the tags for each board
		board.thetags = board.tags.all()
		# get all connections matching this board
		item_conxs = ItemConnection.objects.filter(board=board)
		board.count = item_conxs.count()
		board.views = BoardView.objects.filter(board=board).count()
		board.items = ItemConnection.objects.filter(board=board)[:3]

	saved_board = Board.objects.get(user=user.id, slug="your-saved-items")
	saved_board.items = ItemConnection.objects.filter(board=saved_board)[:5]
	
	profile = request.user.profile
	bgform = ChangeBackgroundForm(instance=profile)
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
		'the_boards': boards,
		'saved_board':saved_board,
		'editable':editable,
		'boards':boards,
		'bgform':bgform,
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

		#update bio
		elif request.POST.get("updatebio"):
				new_bio = request.POST.get("userBio")
				Profile.objects.filter(pk=user.id).update(bio=new_bio)
				return HttpResponseRedirect(request.path_info)

		# set background
		elif 'changebackground' in request.POST:
			form = ChangeBackgroundForm(request.POST, request.FILES, instance=profile)
			if form.is_valid():
				form.save()
				return HttpResponseRedirect(request.path_info)

		#delete boards
		elif 'deleteboard' in request.POST:
			board = get_object_or_404(Board, pk=request.POST.get("board_id",""))
			board.delete()
			return redirect('u:home')

	return render(request, template, context_dict)



# viewing your home
@login_required
def my_home(request):
	template = 'user/my_home.html'

	user = request.user
	boards = Board.objects.filter(user=user.id).exclude(slug='your-saved-items')
	
	for board in boards:
		board.items = []
		no_items = 0
		# get the tags for each board
		board.thetags = board.tags.all()
		# get all connections matching this board
		item_conxs = ItemConnection.objects.filter(board=board)
		# get all items matching 'item' in connections
		for item_conx in item_conxs:
			# for each item, get the Item object and append to our items arr
			item = Item.objects.get(pk=item_conx.item.id)
			board.items.append(item)
		board.count = item_conxs.count()
		board.views = BoardView.objects.filter(board=board).count()
		item_count = ItemConnection.objects.filter(board=board).count()
		no_items += item_count

	profile = user.profile
	connections = profile.get_connections()
	followers = profile.get_followers()
	no_connections = profile.get_connections().count()
	no_followers = profile.get_followers().count()

	# get all users that we're following
	following = request.user.profile.get_connections()

	# get boards of people we're following and build array
	board_obj = []
	for user in following:		
		boards = Board.objects.filter(user=user.following)
		for board in boards:
			board_obj.append(board)

	# for each item in board array we just made...
	itemconx_obj = []
	for board in board_obj: 
		# get item conx instances with this board
		itemconxs = ItemConnection.objects.filter(board=board)
		# for each item conx instance...
		for item in itemconxs:
			# get the likes
			item.likes = ItemLike.objects.filter(item_conx=item).count()
			# is the item liked?
			item.is_liked = ItemLike.objects.filter(item_conx=item, user=request.user).exists()
			# get the views
			item.views = ItemView.objects.filter(item_conx=item).count()			
			# item_conxs = ItemConnection.objects.filter(board=board)	
			# for item_conx in item_conxs:
			# 	item.itemconx = item_conx

			# get the users saved board
			user_saved_board = Board.objects.get(user=request.user, board_name="Your Saved Items")			
			# is this item already in the users saved board?
			item.is_saved = ItemConnection.objects.filter(pk=item.id, board=user_saved_board.id).exists()
			itemconx_obj.append(item)

	if request.method == 'POST':

		# like item
		if 'likeitem' in request.POST:
			itemconx_id = request.POST.get("itemconx_id")
			itemconx = get_object_or_404(ItemConnection, pk=itemconx_id)
			ItemLike.like(itemconx, request.user)
			return HttpResponseRedirect(request.path_info)

		# unlike item
		if 'unlikeitem' in request.POST:
			itemconx_id = request.POST.get("itemconx_id")
			itemconx = get_object_or_404(ItemConnection, pk=itemconx_id)
			ItemLike.unlike(itemconx, request.user)
			return HttpResponseRedirect(request.path_info)

		# save item
		if 'savelater' in request.POST:
			itemconx = request.POST.get("itemconx_id")
			ItemConnection.save_item(itemconx, request)
			return HttpResponseRedirect(request.path_info)

	context_dict = {
		'profile': profile,
		'no_connections': no_connections,
		'no_followers': no_followers,
		'no_items': no_items,
		'connections': connections,
		'followers': followers,
		'boards': boards,
		'itemconxs':itemconx_obj,
	}

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
		the_boards = []
		# get the tags for each board
		for board in boards:
			board.items = []
			board.thetags = board.tags.all()
			item_conxs = ItemConnection.objects.filter(board=board)
			board.count = item_conxs.count()
			board.views = BoardView.objects.filter(board=board).count()
			board.items = ItemConnection.objects.filter(board=board)[:3]
			blocked_obj = BoardPrivacy.objects.filter(board=board) 
			board.blocked = []
			for obj in blocked_obj:
				board.blocked.append(obj.user)
			if board.items:
				if request.user not in board.blocked:
					the_boards.append(board)

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
			'boards':boards,
			'the_boards': the_boards,
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