import datetime, base64
from django.contrib import messages
from django.core.mail import send_mail
from django.contrib.auth import login, update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.http import HttpResponseRedirect
from .forms import SignUpForm, UserForm, ProfileForm, ProfileImageForm, ChangeBackgroundForm, UpdateSocial, SettingsForm, PrivacyForm
from .models import Profile, Connection, BlockedUsers, AuthorisedUsers, Notification
from board.models import Board, Item, ItemConnection, BoardView, ItemLike, ItemView, BoardPrivacy
from django.core.exceptions import PermissionDenied
from django.forms.models import inlineformset_factory
from wantbrd.utils import *

# viewing your own profile
@login_required
def home(request):
	template = "user/index.html"	
	editable = True
	user = request.user
	boards = Board.objects.filter(user=user.id).exclude(slug='your-saved-items')
	
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
	connections = profile.get_connections()
	followers = profile.get_followers()
	no_connections = profile.get_connections().count()
	no_followers = profile.get_followers().count()

	if request.method == 'POST':

		# check we have submitted a want or rec create 
		if request.POST.get("createwantboard"):
			
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
				#create the board
				new_board = Board.objects.create (
					user = user,
					board_name = new_board_name,
				)
				#redirect to edit board page using new model
				return redirect('b:edit_board', board_id=new_board.id)

		#delete boards
		elif 'deleteboard' in request.POST:
			board = get_object_or_404(Board, pk=request.POST.get("board_id",""))
			board.delete()
			notifications = Notification.objects.filter(board_ref=request.POST.get("board_id",""))
			for n in notifications:
				n.delete()
			return redirect('u:home')

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
	}

	return render(request, template, context_dict)



# viewing your home
@login_required
def my_home(request):
	template = 'user/my_home.html'

	user = request.user
	boards = Board.objects.filter(user=user.id).exclude(slug='your-saved-items')
	no_items = 0
	
	for board in boards:
		board.items = []		
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
	suggested_boards = profile.get_suggested_boards(2, request)

	# recent activity
	now = datetime.datetime.now()
	ago = now - datetime.timedelta(days=1)

	recent_itemlikes = Notification.objects.filter(user=user, notification_type='likeitem', created__range=[ago, now]).count()
	recent_boardlikes = Notification.objects.filter(user=user, notification_type='likeboard', created__range=[ago, now]).count()
	recent_followers = Notification.objects.filter(user=user, notification_type='newfollow', created__range=[ago, now]).count()
	recent_likes = recent_itemlikes + recent_boardlikes

	# get all users that we're following
	following = request.user.profile.get_connections()

	# get boards of people we're following and build array
	board_obj = []
	for user in following:		
		boards = Board.objects.filter(user=user.following).exclude(slug='your-saved-items')
		for board in boards:
			board_obj.append(board)

	# for each item in board array we just made...
	itemconx_obj = []
	for board in board_obj: 
		# get item conx instances with this board
		itemconxs = ItemConnection.objects.filter(board=board, active=True)
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
			like_item(itemconx_id, request.user)
			# messages.info(request, 'Item liked')
			return HttpResponseRedirect(request.path_info)

		# unlike item
		if 'unlikeitem' in request.POST:
			itemconx_id = request.POST.get("itemconx_id")
			unlike_item(itemconx_id, request.user)
			# messages.info(request, 'Item unliked')
			return HttpResponseRedirect(request.path_info)

		# save item
		if 'savelater' in request.POST:
			itemconx = request.POST.get("itemconx_id")
			ItemConnection.save_item(itemconx, request)
			messages.info(request, 'This item has been added to your Saved Items')
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
		'suggested_boards':suggested_boards,
		'recent_likes':recent_likes,
		'recent_followers':recent_followers,
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


### Update profile
def update_profile(request):
	template = "user/update_profile.html"

	user = request.user
	profile = get_object_or_404(Profile, user=user)
	user_form = UserForm(instance=user, label_suffix='')
	profile_form = ProfileForm(instance=profile, label_suffix='')	
	social_form = UpdateSocial(instance=profile, label_suffix='')
	bgform = ChangeBackgroundForm(instance=profile)
	remaining = 500 - len(profile.bio)

	if request.method == "POST":

		if 'updatePpic' in request.POST:
			b64image = request.POST.get("b64image")
			form = ProfileImageForm(request.POST, instance=profile)
			if form.is_valid():
				up = form.save(commit=False)
				up.picture = decode_base64_file(b64image)
				up.save()	
				messages.info(request, 'Your profile picture was updated.')
				return HttpResponseRedirect(request.path_info)		

		elif 'changebackground' in request.POST:
			b64pic = request.POST.get("b64pic")
			form = ChangeBackgroundForm(request.POST, instance=profile)
			if form.is_valid():
				ub = form.save(commit=False)
				ub.background = decode_base64_file(b64pic)
				ub.save()		
				messages.info(request, 'Your profile background was updated.')
				return HttpResponseRedirect(request.path_info)

		elif request.POST.get("updateprofile"):
			user_form = UserForm(request.POST, request.FILES, instance=user)
			profile_form = ProfileForm(request.POST, request.FILES, instance=profile)

			if all([user_form.is_valid(), profile_form.is_valid()]):
				user = user_form.save()
				profile = profile_form.save()
				messages.info(request, 'Your profile has been updated.')
				return HttpResponseRedirect(request.path_info)

		elif request.POST.get("updatesocial"):
			form = UpdateSocial(request.POST, instance=profile) 
			if form.is_valid():
				form.save()
				messages.info(request, 'Your social profiles have been updated.')
				# send_mail('You did it!', 'My god, it worked', 'noreply@wantbrd.com', ['iamholdsworth@gmail.com'])
				return HttpResponseRedirect(request.path_info)

	return render(request, template, {
		"userid": user.id,
		"user_form": user_form,
		"profile_form": profile_form,
		"social_form":social_form,
		"bgform":bgform,
		'remaining':remaining,
	})


def privacy_settings(request):
	template = "user/privacy_settings.html"
	user = request.user
	profile = get_object_or_404(Profile, user=user)
	blocked_users_obj = BlockedUsers.objects.filter(user=user)
	blocked_users_list = []
	authorised_users_obj = AuthorisedUsers.objects.filter(user=user)
	authorised_users_list = []
	for user in blocked_users_obj:
		blocked_users_list.append(user.blocked_user)
	for user in authorised_users_obj:
		authorised_users_list.append(user.authorised_user)
	blocked_users = ','.join(map(str, blocked_users_list))
	authorised_users = ','.join(map(str, authorised_users_list))


	settings_form = SettingsForm(instance=profile)	
	password_form = PasswordChangeForm(user)
	privacy_form = PrivacyForm(instance = profile)

	context_dict = {
		'settings_form':settings_form,
		'password_form':password_form,
		'privacy_form':privacy_form,
		'blocked_users':blocked_users,
		'authorised_users':authorised_users,
	}

	if request.method == "POST":
		if 'updatepassword' in request.POST:
			password_form = PasswordChangeForm(request.user, request.POST)
			if password_form.is_valid():
				user = password_form.save()
				update_session_auth_hash(request, user)  # Important!
				messages.success(request, 'Your password was updated.')
				return redirect('privacy_settings')
			else:
				messages.error(request, 'There was a problem updating your password, please try again')
				context_dict = {
					'settings_form':settings_form,
					'password_form':password_form,
					'privacy_form':privacy_form,
					'blocked_users':blocked_users,
					'authorised_users':authorised_users,
				}
				return render(request, template, context_dict)

		if 'updateprivacy' in request.POST:
			privacy_form = PrivacyForm(request.POST, instance=profile)
			privacy_choice = request.POST.get("global_privacy")
			userlist = request.POST.get("user_list")			

			if privacy_form.is_valid():		

				# if we need to deal with the blocked/allowed users
				if privacy_choice == 'HIDE' or privacy_choice == 'SHOW':

					# split it
					user_list = userlist.split(",")

					# if privacy choice is invisible except...
					if privacy_choice == 'HIDE':
						for x in user_list:						
							new_authorised_user = AuthorisedUsers.objects.create(
								user = user,
								authorised_user = x
							)
					# if privacy choice is visible except...							
					else:
						for x in user_list:						
							new_blocked_user = BlockedUsers.objects.create(
								user = user,
								blocked_user = x
							)

				privacy_form.save()
				messages.info(request, 'Your global privacy settings were updated.')
				return redirect('privacy_settings')	

				privacy_form.save()
				messages.info(request, 'Your global privacy settings were updated.')
				return redirect('privacy_settings')	
			else:
				messages.error(request, 'There was a problem updating your privacy settings, please try again')
				context_dict = {
					'settings_form':settings_form,
					'password_form':password_form,
					'privacy_form':privacy_form,
					'blocked_users':blocked_users,
					'authorised_users':authorised_users,
				}
				return render(request, template, context_dict)

		if 'updatenotification' in request.POST:
			settings_form = SettingsForm(request.POST, instance=profile)
			if settings_form.is_valid():
				settings_form.save()
				messages.info(request, 'Your notification settings were updated.')
				return redirect('privacy_settings')	
			else:
				messages.error(request, 'There was a problem updating your notifications preferences, please try again')
				context_dict = {
					'settings_form':settings_form,
					'password_form':password_form,
					'privacy_form':privacy_form,
					'blocked_users':blocked_users,
					'authorised_users':authorised_users,
				}
				return render(request, template, context_dict)

	return render(request, template, context_dict)


# view someone elses profile
def profile(request, username):
	template = 'user/index.html'	

	try:
		user = get_object_or_404(User, username=username)
		boards = Board.objects.filter(user=user.id).exclude()
		the_boards = []
		# get the tags for each board
		for board in boards:
			board.items = []
			board.thetags = board.tags.all()
			item_conxs = ItemConnection.objects.filter(board=board, active=True)
			board.count = item_conxs.count()
			if board.count > 0:
				board.views = BoardView.objects.filter(board=board).count()
				board.items = ItemConnection.objects.filter(board=board, active=True)[:3]
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
			user.profile.make_connection(request)

		#if user unfollowed
		if 'unfollow' in request.POST:
			user.profile.break_connection(request)

		return HttpResponseRedirect(request.path_info)

	return render(request, template, context_dict)


# View someones followers
def profile_followers(request, username):
	template = 'user/view_followers.html'	
	user = get_object_or_404(User, username=username)

	try:
		boards = Board.objects.filter(user=user.id).exclude(slug='your-saved-items').count()
		profile = user.profile
		connections = profile.get_connections()
		followers = profile.get_followers()
		no_connections = profile.get_connections().count()
		no_followers = profile.get_followers().count()

		is_followed = False
		for x in followers:
			if x.creator == request.user:
				is_followed = True

		for auser in followers:
			auserfollowers = auser.creator.profile.get_followers()
			for x in auserfollowers:
				if x.creator == request.user:
					auser.followed = True
				else:
					auser.followed = False
	except:
		pass

	# handle submissions
	if request.method == 'POST':

		# if user followed
		if 'follow' in request.POST:
			user.profile.make_connection(request)

		#if user unfollowed
		if 'unfollow' in request.POST:
			user.profile.break_connection(request)

		# if user followed
		if 'followcard' in request.POST:
			userid = request.POST.get("auser")
			auser = User.objects.get(pk=userid)
			auser.profile.make_connection(request)

		#if user unfollowed
		if 'unfollowcard' in request.POST:
			userid = request.POST.get("auser")
			auser = User.objects.get(pk=userid)
			auser.profile.break_connection(request)

		return HttpResponseRedirect(request.path_info)

	context_dict = {
		'profile': profile,
		'no_followers': no_followers,
		'followers': followers,
		'no_connections': no_connections,
		'connections': connections,
		'followers': followers,
		'is_followed':is_followed,
		'boards':boards,
	}

	return render(request, template, context_dict)


# View who someone is following
def profile_following(request, username):
	template = 'user/view_following.html'	
	user = get_object_or_404(User, username=username)

	try:
		boards = Board.objects.filter(user=user.id).exclude(slug='your-saved-items').count()
		profile = user.profile
		followers = profile.get_followers()		
		connections = profile.get_connections()
		no_connections = profile.get_connections().count()
		no_followers = profile.get_followers().count()

		is_followed = False
		for x in followers:
			if x.creator == request.user:
				is_followed = True

		for auser in connections:
			auser_profile = auser.following.profile
			auser_connections = auser_profile.get_followers()
			for x in auser_connections:
				if x.creator == request.user:
					auser.followed = True
					break
				else:
					auser.followed = False

	except:
		pass

	# handle submissions
	if request.method == 'POST':

		# if user followed
		if 'follow' in request.POST:
			user.profile.make_connection(request)

		#if user unfollowed
		if 'unfollow' in request.POST:
			user.profile.break_connection(request)

		# if user followed
		if 'followcard' in request.POST:
			userid = request.POST.get("auser")
			auser = User.objects.get(pk=userid)
			auser.profile.make_connection(request)

		#if user unfollowed
		if 'unfollowcard' in request.POST:
			userid = request.POST.get("auser")
			auser = User.objects.get(pk=userid)
			auser.profile.break_connection(request)

		return HttpResponseRedirect(request.path_info)

	context_dict = {
		'profile': profile,
		'no_followers': no_followers,
		'followers': followers,
		'no_connections': no_connections,
		'connections': connections,
		'followers': followers,
		'is_followed':is_followed,
		'boards':boards,
		'auser_connections':auser_connections,
	}

	return render(request, template, context_dict)


def check_status(request):
	user = request.user
	
	if user.profile.login_count > 1:
		return redirect('my_home')
	else:
		return redirect('initial')


def initial(request):
	template = 'user/initial.html'

	# handle submissions
	if request.method == 'POST':

		# after selecting the topics interested in
		if request.POST.get("nextstep"):
			tags = request.POST.get("usertags")
			tags_list = tags.split(',')
			tags_list = tags_list[:-1]
			users = []
			boards = Board.objects.filter(tags__name__in = tags_list).distinct()
			for board in boards:
				user = board.user
				user.boardcount = Board.objects.filter(user=user).exclude(slug='your-saved-items').count()
				user.itemcount = user.profile.get_user_item_count()
				user.viewscount = user.profile.get_user_views()
				user.the_tags = user.profile.get_user_tags()
				users.append(user)			

		# after selecting users to follow
		if request.POST.get("followall"):
			users_to_follow = request.POST.get("userstofollow")
			follow_list = users_to_follow.split(",")			
			follow_list = list(map(int, follow_list))
			for user in follow_list:
				to_follow = User.objects.get(id=user)
				to_follow.profile.make_connection(request)
			return redirect('my_home')


		context_dict = {
			'users':users
		}

		return render(request, template, context_dict)

	context_dict = {}

	return render(request, template, context_dict)


def my_notifications(request):

	template = 'user/my_notifications.html'	

	new, old = get_notifications(request)

	# clear all notifications
	notifications = Notification.objects.filter(user=request.user)
	notifications.update(seen=True)

	context_dict = {
		'new':new,
		'old':old,
	}

	return render(request, template, context_dict)


def terms(request):
	template = 'terms.html'
	return render(request, template)


def influencers(request):
	template = 'influencers.html'
	return render(request, template)
