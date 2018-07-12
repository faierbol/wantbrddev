import requests, urllib, datetime, random, json, re
from django.contrib import messages
from django.template import RequestContext
from django.shortcuts import render, redirect, get_object_or_404
from django.core.files.storage import FileSystemStorage
from django.db.models import Q
from django.http import HttpResponseRedirect
from django.contrib.auth.models import User
from .models import Board, Item, BoardLike, ItemLike, BoardView, ItemView, ItemConnection, BoardPrivacy
from user.models import Notification
from user.views import Connection
from .forms import BoardForm, ItemForm, EditBoardForm, ChangeBackgroundForm, UpdateTags
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import os, copy
from urllib.parse import urlparse
from PIL import ImageFile, Image
from django.core import files
from io import BytesIO
from wantbrd.utils import *
import urllib.request
from urllib.parse import quote_plus
from lxml import html
import opengraph_py3
import metadata_parser


##### HOME PAGE
def home(request):

	if request.method == "POST":

		# like item
		if 'likeitem' in request.POST:
			itemconx_id = request.POST.get("itemconx_id")						
			like_item(itemconx_id, request.user)
			return HttpResponseRedirect(request.path_info)

		# unlike item
		if 'unlikeitem' in request.POST:
			itemconx_id = request.POST.get("itemconx_id")
			unlike_item(itemconx_id, request.user)
			return HttpResponseRedirect(request.path_info)

	template = 'index.html'
	hot_items = []

	trending_items = get_trending_items(request,3)
	trending_users = get_trending_users(request,3)
	trending_boards = get_trending_boards(request,3)
	recommended_boards = get_recommended_boards(request)

	mixed = list(trending_boards) + list(trending_items) + list(trending_users) + list(recommended_boards)
	random.shuffle(mixed)	
	for item in mixed:
		if item not in hot_items:
			hot_items.append(item)

	context_dict = {
		'hot_items':hot_items,
	}

	return render(request, template, context_dict)


##### Home Trending Items
def trending_items(request):
	template = 'trending_items.html'

	items = get_trending_items(request,3)

	context_dict = {
		'items':items
	}

	return render(request, template, context_dict)


##### Home Trending Boards
def trending_boards(request):
	template = 'trending_boards.html'

	trending_boards = get_trending_boards(request,3)

	context_dict = {
		'trending_boards':trending_boards,
	}

	return render(request, template, context_dict)


##### Home Trending Users
def trending_users(request):
	template = 'trending_users.html'

	trending_users = get_trending_users(request,3)

	context_dict = {
		'trending_users':trending_users
	}

	return render(request, template, context_dict)


##### Add a new board
def add_board(request):
	template = 'board/add_board.html'

	board_form = BoardForm()
	board_form.fields['user'].initial = request.user

	if request.method == "POST":
		form = BoardForm(request.POST, request.FILES)
		if form.is_valid():			
			board_form = form.save(commit=False)			
			board_form.save()
			form.save_m2m()
			return redirect('b:my_boards')
		else:
			return render(request, template, {"form": form,})

	return render(request, template, {
		"form": board_form,
	})


##### Edit a board
def edit_board(request, board_id):
	template = 'board/view_board.html'
	editable = True
	deniedusers = False

	# get the board id from the url
	board = get_object_or_404(Board, pk=board_id)
	board.thetags = board.tags.all()
	form = EditBoardForm(instance=board)
	bgform = ChangeBackgroundForm(instance=board)
	tagform = UpdateTags(instance=board)
	items = []
	item_conxs = ItemConnection.objects.filter(board=board_id)
	allusers = User.objects.all()
	for item_conx in item_conxs:
		items.append(item_conx)	

	blocked_obj = BoardPrivacy.objects.filter(board=board) 
	board.blocked = []
	for obj in blocked_obj:
		board.blocked.append(obj.user)


	# check the current user is the boards owner
	if board.user.id != request.user.id:
		return redirect('b:view_boards')
	else:
		# was a form submitted?
		if request.method == 'POST':

			# change background image
			if request.POST.get("changebackground"):
				form = ChangeBackgroundForm(request.POST, request.FILES, instance=board)
				if form.is_valid():
					form.save()
					messages.info(request, 'Your boards background was updated.')
					return HttpResponseRedirect(request.path_info)

			# manage video
			if request.POST.get("updatevideo"):
				video_status = request.POST.get("show_video")
				video_id = request.POST.get("videoid")
				Board.objects.filter(pk=board.id).update(video=video_id)
				if video_status:					
					messages.info(request, 'The video has been enabled.')
					Board.objects.filter(pk=board.id).update(show_video=True)
				else:
					Board.objects.filter(pk=board.id).update(show_video=False)
					messages.info(request, 'The video has been disabled.')
				return HttpResponseRedirect(request.path_info)

			# manage privacy
			if request.POST.get("updateprivacy"):
				# get form data
				board = get_object_or_404(Board, pk=request.POST.get("board"))
				deniedusers = request.POST.getlist("list-users")
				# remove all current privacy entries
				BoardPrivacy.objects.filter(board=board).delete()
				# loop through users and apply
				for user in deniedusers:
					# create a new block
					new_block = BoardPrivacy()
					# assign values to new block
					user = get_object_or_404(User, pk=user)
					new_block.board = board
					new_block.user = user
					# save it
					new_block.save()
				messages.info(request, 'Your board privacy settings have been updated.')
				return HttpResponseRedirect(request.path_info)

			# update desc
			if request.POST.get("updatedescription"):
				new_desc = request.POST.get("boardDesc")
				Board.objects.filter(pk=board.id).update(description=new_desc)
				messages.info(request, 'Your board description was updated.')
				return HttpResponseRedirect(request.path_info)

			# update tags
			if request.POST.get("updatetags"):
				form = UpdateTags(request.POST, instance=board)
				if form.is_valid():
					form.save()
					messages.info(request, 'Your board tags have been updated.')
					return HttpResponseRedirect(request.path_info)

			if 'deleteitem' in request.POST:
				# get the item connection object
				item_conx = get_object_or_404(ItemConnection, id=request.POST.get("item_id",""))
				# check the item is owned by the current user
				if item_conx.board.user == request.user:
					# get the item id (and then item) from the connection
					item = item_conx.item
					# now we can delete the connection
					item_conx.delete()
					# get all remaining connections with this item.id
					items = ItemConnection.objects.filter(item=item)
					# is there less than one? If so, delete the item as well as we dont need it.
					if items.count() < 1:
						item.delete()	
						messages.info(request, 'The item was deleted.')			
					return HttpResponseRedirect(request.path_info)
				# if the current user is not the owner
				else:
					return HttpResponseRedirect(request.path_info)

			# otherwise				
			else:
				form = EditBoardForm(request.POST, request.FILES, instance=board)
				if form.is_valid():
					form = form.save()					
					return redirect('b:my_boards')
		else:
			# create a form using the current board instance
			form = EditBoardForm(instance=board)

		context_dict = {
			'board':board,
			'form':form,
			'editable':editable,
			'bgform':bgform,
			'tagform':tagform,
			'items':items,
			'allusers':allusers,
			'deniedusers':deniedusers,
		}

		return render(request, template, context_dict)


##### Edit item
def edit_item(request, board_id, itemconx_id):
	template = 'board/edit_item.html'
	board = get_object_or_404(Board, id=board_id)
	itemconx = get_object_or_404(ItemConnection, pk=itemconx_id)	
	item = get_object_or_404(Item, pk=itemconx.item.id)
	form = ItemForm(instance=itemconx)	

	if request.method == 'POST':

		if 'updateitem' in request.POST:
			form = ItemForm(request.POST, instance=itemconx)
			item_name = request.POST.get("item_name")

			if form.is_valid():
				# save the new form instance to a var
				itemconx = form.save(commit=False)				
				# if the name has changed
				if item.item_name != item_name:
					# check is there is another item_connection connected to this item
					itemconxs = ItemConnection.objects.filter(item=item).count()
					# if there is more than one, then someone elses item is connected and so we must create a new one
					if itemconxs > 1:
						# create a new item 
						new_item = Item()
						# give the new item the new name
						new_item.item_name = item_name
						new_item.save()
						# assign the new item to the item connection
						itemconx.item = new_item
					# if there is only 1 then we can just rename this one.
					else:
						# we can update the original item
						item.item_name = item_name
						item.save()
				form.save()		

				return redirect('b:edit_board', board_id=board_id)

			else:
				return redirect('home')				

	context_dict = {
		'board':board,
		'itemconx':itemconx,
		'form':form,
		'item':item,
	}

	return render(request, template, context_dict)



##### View board
def view_board(request, username, board_name):
	template = 'board/view_board.html'	
	board_owner = get_object_or_404(User, username=username)
	user = request.user

	board = get_object_or_404(Board, slug=board_name, user=board_owner)
	board.thetags = board.tags.all()
	board.likes = BoardLike.objects.filter(board=board).count()
	try:
		board.is_liked = BoardLike.objects.filter(board=board, user=request.user).exists()
	except:
		board.is_liked = False
	blocked_obj = BoardPrivacy.objects.filter(board=board) 
	board.blocked = []
	for obj in blocked_obj:
		board.blocked.append(obj.user)
	if request.user in board.blocked:
		board.blocked = True
	else:
		board.blocked = False

	userip = request.META['REMOTE_ADDR']
	refer = request.META.get('HTTP_REFERER')

	items = []
	item_conxs = ItemConnection.objects.filter(board=board.id, active=True)		
	for item in item_conxs:
		if item.active:
			item.likes = ItemLike.objects.filter(item_conx=item).count()
			try:
				item.is_liked = ItemLike.objects.filter(item_conx=item, user=request.user).exists()
			except:
				item.is_liked = False
			item.views = ItemView.objects.filter(item_conx=item).count()
			items.append(item)	

	try:
		user_boards = Board.objects.filter(user=user).exclude(board_name="Your Saved Items")
	except:
		user_boards = []

	# create new board view instance if not exsists, count views
	board_view, created = BoardView.objects.get_or_create(board=board, ip=userip)
	board.views = BoardView.objects.filter(board=board).count()

	try:
		following = request.user.profile.get_connections()
		is_followed = False
		for user in following:
			if board.user == user.following:
				is_followed = True
	except:
		following = False
		is_followed = False

	# handle submissions
	if request.method == 'POST':

		# like item
		if 'likeitem' in request.POST:
			itemconx_id = request.POST.get("itemconx_id")						
			like_item(itemconx_id, request.user)
			return HttpResponseRedirect(request.path_info)

		# unlike item
		if 'unlikeitem' in request.POST:
			itemconx_id = request.POST.get("itemconx_id")
			unlike_item(itemconx_id, request.user)
			return HttpResponseRedirect(request.path_info)

		# like board
		if 'likeboard' in request.POST:
			board_id = request.POST.get("board_id")
			like_board(board_id, request.user)
			return HttpResponseRedirect(request.path_info)

		# unlike board
		if 'unlikeboard' in request.POST:
			board_id = request.POST.get("board_id")
			unlike_board(board_id, request.user)
			return HttpResponseRedirect(request.path_info)

		# if user followed
		if 'follow' in request.POST:
			board.user.profile.make_connection(request)
			return HttpResponseRedirect(request.path_info)

		# if user unfollowed
		if 'unfollow' in request.POST:
			board.user.profile.break_connection(request)
			return HttpResponseRedirect(request.path_info)

		# if add to board
		if 'addtoboard' in request.POST:
			# board to copy to
			boardid = request.POST.get("board_id")
			board = Board.objects.get(pk=boardid)
			# get model of item connection we're copying
			itemconxid =  request.POST.get("itemconx_id")
			itemconx = ItemConnection.objects.get(pk=itemconxid)
			# create clone
			clone = copy.copy(itemconx)
			# remove pk and add destination board to clone
			clone.pk = None
			clone.board = board			
			# remove prefetch cache, becuase...
			try:
			    delattr(clone, '_prefetched_objects_cache')
			except AttributeError:
			    pass
			clone.save()
			messages.info(request, '"{0}" was added to the board, "{1}".'.format(itemconx.item.item_name, board.board_name))
			return HttpResponseRedirect(request.path_info)

		if 'savelater' in request.POST:
			itemconx = request.POST.get("itemconx_id")
			ItemConnection.save_item(itemconx, request)							
			copied_item = ItemConnection.objects.get(pk=itemconx)
			messages.info(request, '"%s" was added to your saved items board.' % copied_item.item.item_name)
			return HttpResponseRedirect(request.path_info)

	context_dict = {
		'is_followed': is_followed,
		'following': following,
		'items':items,
		'board':board,
		'user_boards':user_boards,
		'refer':refer,
	}

	return render(request, template, context_dict)


##### View item
def view_item(request, username, board_name, itemconx_id):
	template = 'board/view_item.html'

	itemconx = ItemConnection.objects.get(pk=itemconx_id)

	context_dict = {
		'itemconx': itemconx,
	}

	return render(request, template, context_dict)


##### Add item
def add_item(request, board_id):
	template = 'board/add_item.html'

	board = get_object_or_404(Board, pk=board_id)
	form = ItemForm()
	url = ''

	if request.method == 'POST':

		if 'geturl' in request.POST:

			ogimg = False
			og_img_meta = False
			sizes = []
			allimages = []
			output = []
			page_title = ''
			image = False
			html = ''
			page = ''
			url = request.POST.get("targeturl", "")
			parsed_uri = urlparse(url)
			domain = '{uri.scheme}://{uri.netloc}/'.format(uri=parsed_uri)

			try:
				page = metadata_parser.MetadataParser(url=url)
			except:
				pass
			if page:
				try:
					page_title = page.get_metadatas('title')[0]
				except:
					pass
				try:
					meta_image = page.get_metadata_link('image')
				except:
					pass

			if meta_image:
				output.append(meta_image)
			else:
				# ########## PROXYCRAWL BELOW #########
				api = 'aaF7juZfhdnyptXo4Kjm6A'
				jsapi = 'vBlWMcz5CXvV4A-YnXhhag'

				modded_url = quote_plus(url)
				response = requests.get('https://api.proxycrawl.com/?token=' + jsapi + '&format=json&page_wait=3000&url=' + modded_url)	
				parsed_json = response.json()
				html = parsed_json['body']

				soup = BeautifulSoup(html)

				if not page_title:
					page_title = soup.title.string

				# image_tags = soup.findAll('img', {'src' : re.compile(r'(jpe?g)|(png)$')})
				image_tags = soup.findAll('img')
				# loop through all img's found
				for img in image_tags:

					# get src from img
					imgurl = img.get('src')

					# check a value is there and its not a data: src
					if (imgurl is not None) and ("data:" not in imgurl):

						if imgurl.lower().endswith(('.bmp', '.png', '.gif', '.tif')):
							pass

						else:
							# check if src starts without full path and append with domain appropriately 
							if not imgurl.startswith("http"):
								if imgurl.startswith("//"):
									imgurl = "https:" + imgurl
								else:
									imgurl = domain + imgurl		

							try:
								image_raw = requests.get(imgurl)
								the_image = Image.open(BytesIO(image_raw.content))
								img_width, img_height = the_image.size
								if img_width > 250:
									output.append(imgurl)
							except:
								pass
			context_dict = {
				'board':board,
				'form':form,
				'domain':domain,
				'url':url,				
				'ogimg':ogimg,				
				'output':output,
				'allimages':allimages,
				'page_title':page_title,
				'html':html,
			}

			return render(request, template, context_dict)

		if 'additem' in request.POST:
			form = ItemForm(request.POST, request.FILES)
			imgsrc = request.POST.get("imgsrc")
			item_name = request.POST.get("item_name")
			purchase_url = request.POST.get("purchase_url")
			item_status = request.POST.get("item_status")
			item_desc = request.POST.get("item_desc")
			item_active = request.POST.get("item_active")
			rating = request.POST.get("rating")
			review = request.POST.get("review")

			if item_active == "active":
				item_active = True
			else:
				item_active = False

			if imgsrc == 'web':
				url = request.POST.get("scrapedimg")
				resp = requests.get(url)
				if resp.status_code != requests.codes.ok:
					return redirect('home')
				fp = BytesIO()
				fp.write(resp.content)
				file_name = url.split("/")[-1]

			if form.is_valid():		
				# create a new item with this item name and save it
				new_item = Item()
				new_item.item_name = item_name
				new_item.save()
				
				# save the model form
				new_item_conx = form.save(commit=False)
				new_item_conx.board = board
				new_item_conx.item = new_item
				if imgsrc == 'own':
					new_image = request.FILES['ownimage']
					new_item_conx.image = new_image
					new_item_conx.save()
				else:
					new_item_conx.image.save(file_name, files.File(fp))
				new_item_conx.save()					

				return redirect('b:edit_board', board_id=board_id)


	context_dict = {
		'board':board,
	}

	return render(request, template, context_dict)


##### Search Items
def search_item(request):
	template = 'board/search_item.html'

	# set things up
	item_results = []
	search_term = request.GET.get('kw', '')
	search_term = search_term.lower()

	#items 
	items = Item.objects.filter(item_name__icontains=search_term)
	for item in items:
		item_conxs = ItemConnection.objects.filter(item=item, active=True)
		for item in item_conxs:
			item.likes = ItemLike.objects.filter(item_conx=item).count()
			item.is_liked = ItemLike.objects.filter(item_conx=item, user=request.user).exists()
			item.views = ItemView.objects.filter(item_conx=item).count()
			item_results.append(item)

	# boards
	all_boards = False
	board_results = []
	board_search_tags = Board.objects.filter(tags__name__in=[search_term])
	board_search_names = Board.objects.filter(board_name__icontains=search_term)
	
	all_boards = board_search_tags | board_search_names
	all_boards = all_boards.distinct()	
	for board in all_boards:
		if board.get_item_count() > 0 and not board.user_blocked(request.user) and not board.user == request.user:
			board_results.append(board)
	for board in board_results:
		board.totalitems = board.get_item_count()


	# users
	user_results = False
	user_results = User.objects.filter(username__icontains=search_term)

	context_dict = {
		'search_term':search_term,
		'item_results':item_results,
		'user_results':user_results,
		'board_results':board_results,
	}

	return render(request, template, context_dict)


##### Search Boards
def search_board(request):
	template = 'board/search_board.html'

	# set things up
	item_results = []
	search_term = request.GET.get('kw', '')
	search_term = search_term.lower()

	#items 
	items = Item.objects.filter(item_name__icontains=search_term)
	for item in items:
		item_conxs = ItemConnection.objects.filter(item=item, active=True)
		for item in item_conxs:
			item.likes = ItemLike.objects.filter(item_conx=item).count()
			item.is_liked = ItemLike.objects.filter(item_conx=item, user=request.user).exists()
			item.views = ItemView.objects.filter(item_conx=item).count()
			item_results.append(item)

	# boards
	all_boards = False
	board_results = []
	board_search_tags = Board.objects.filter(tags__name__in=[search_term])
	board_search_names = Board.objects.filter(board_name__icontains=search_term)
	all_boards = board_search_tags | board_search_names
	all_boards = all_boards.distinct()	
	for board in all_boards:
		if board.get_item_count() > 0 and not board.user_blocked(request.user) and not board.user == request.user:
			board_results.append(board)
	for board in board_results:
		board.totalitems = board.get_item_count()
		board.views = BoardView.objects.filter(board=board).count()
		board.itemconxs = ItemConnection.objects.filter(board=board, active=True)[:5]

	# users
	user_results = False
	user_results = User.objects.filter(username__icontains=search_term)

	context_dict = {
		'search_term':search_term,
		'item_results':item_results,
		'user_results':user_results,
		'board_results':board_results,
	}

	return render(request, template, context_dict)


##### Search Users
def search_user(request):
	template = 'board/search_user.html'

	# set things up
	item_results = []
	search_term = request.GET.get('kw', '')
	search_term = search_term.lower()

	#items 
	items = Item.objects.filter(item_name__icontains=search_term)
	for item in items:
		item_conxs = ItemConnection.objects.filter(item=item, active=True)
		for item in item_conxs:
			item.likes = ItemLike.objects.filter(item_conx=item).count()
			item.is_liked = ItemLike.objects.filter(item_conx=item, user=request.user).exists()
			item.views = ItemView.objects.filter(item_conx=item).count()
			item_results.append(item)

	# boards
	all_boards = False
	board_results = []
	board_search_tags = Board.objects.filter(tags__name__in=[search_term])
	board_search_names = Board.objects.filter(board_name__icontains=search_term)
	
	all_boards = board_search_tags | board_search_names
	all_boards = all_boards.distinct()	
	for board in all_boards:
		if board.get_item_count() > 0 and not board.user_blocked(request.user) and not board.user == request.user:
			board_results.append(board)
	for board in board_results:
		board.totalitems = board.get_item_count()

	# users
	user_results = False
	user_results = User.objects.filter(username__icontains=search_term)
	for user in user_results:
		# set things up
		user.itemcount = 0
		user.viewscount = 0
		user.items = []

		# get all boards
		boards = Board.objects.filter(user=user)
		# set board count
		user.boardcount = boards.count()
		# start the item count so we only get the initial display ones
		x = 0
		#cycle through boards
		for board in boards:
			# get the board views
			boardviews = BoardView.objects.filter(board=board).count()
			# get all items for this board and count 
			boarditems = ItemConnection.objects.filter(board=board, active=True)			
			user.itemcount+=boarditems.count()
			itemviews = 0			
			for item in boarditems:
				itemviews += ItemView.objects.filter(item_conx=item).count()
				if x < 2:
					user.items.append(item)
				x+=1				
			user.viewscount = boardviews + itemviews

	context_dict = {
		'search_term':search_term,
		'item_results':item_results,
		'user_results':user_results,
		'board_results':board_results,
	}

	return render(request, template, context_dict)


def item_details(request):
	context_dict = {
	}
	return render(request, 'board/item_details.html', context_dict)