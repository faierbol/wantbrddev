import requests, urllib
from django.shortcuts import render, redirect, get_object_or_404
from django.core.files.storage import FileSystemStorage
from django.db.models import Q
from django.http import HttpResponseRedirect
from django.contrib.auth.models import User
from .models import Board, Item, BoardLike, ItemLike, BoardView, ItemView, ItemConnection, BoardPrivacy
from user.views import Connection
from .forms import BoardForm, ItemForm, EditBoardForm, ChangeBackgroundForm, UpdateTags
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import os, copy
from urllib.parse import urlparse
from PIL import ImageFile
from django.core import files
from io import BytesIO
import requests

# instantiate a chrome options object so you can set the size and headless preference
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--window-size=1920x1080")


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
		item = Item.objects.get(pk=item_conx.item.id)
		item.itemconx = item_conx
		items.append(item)	

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
					return HttpResponseRedirect(request.path_info)

			# manage video
			if request.POST.get("updatevideo"):
				video_status = request.POST.get("show_video")
				video_id = request.POST.get("videoid")
				Board.objects.filter(pk=board.id).update(video=video_id)
				if video_status:					
					Board.objects.filter(pk=board.id).update(show_video=True)
				else:
					Board.objects.filter(pk=board.id).update(show_video=False)
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

				return HttpResponseRedirect(request.path_info)

			# update desc
			if request.POST.get("updatedescription"):
				new_desc = request.POST.get("boardDesc")
				Board.objects.filter(pk=board.id).update(description=new_desc)
				return HttpResponseRedirect(request.path_info)

			# update tags
			if request.POST.get("updatetags"):
				form = UpdateTags(request.POST, instance=board)
				if form.is_valid():
					form.save()
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
def edit_item(request, board_id, item_id):
	template = 'board/edit_item.html'
	board = get_object_or_404(Board, id=board_id)
	item = get_object_or_404(Item, id=item_id)
	itemconx = get_object_or_404(ItemConnection, item=item, board=board_id)
	itemconxs = ItemConnection.objects.filter(item=item).count()

	form = ItemForm(instance=item)
	item.url = itemconx.purchase_url

	context_dict = {
		'board':board,
		'item':item,
		'itemconx':itemconx,
		'form':form,
		'itemconxs':itemconxs,
	}

	if request.method == 'POST':

		if 'updateitem' in request.POST:
			form = ItemForm(request.POST, request.FILES, instance=item)
			item_name = request.POST.get("item_name")
			purchase_url = request.POST.get("purchase_url")
			item_status = request.POST.get("item_status")
			item_desc = request.POST.get("item_desc")
			item_active = request.POST.get("item_active")
			if item_active == "active":
				item_active = True
			else:
				item_active = False		

			if form.is_valid():
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
				itemconx.purchase_url = purchase_url
				itemconx.item_status = item_status
				itemconx.item_desc = item_desc
				itemconx.active = item_active
				itemconx.save()					

				return redirect('b:edit_board', board_id=board_id)

	return render(request, template, context_dict)



##### View board
def view_board(request, username, board_name):
	template = 'board/view_board.html'	
	user = request.user
	message = None

	board = get_object_or_404(Board, slug=board_name)
	board.thetags = board.tags.all()
	board.likes = BoardLike.objects.filter(board=board).count()
	board.is_liked = BoardLike.objects.filter(board=board, user=request.user).exists()
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
	item_conxs = ItemConnection.objects.filter(board=board.id)		
	for item_conx in item_conxs:
		item = Item.objects.get(pk=item_conx.item.id)
		item.likes = ItemLike.objects.filter(item_conx=item_conx).count()
		item.is_liked = ItemLike.objects.filter(item_conx=item_conx, user=request.user).exists()
		item.views = ItemView.objects.filter(item_conx=item_conx).count()
		item.itemconx = item_conx
		items.append(item)	

	user_boards = Board.objects.filter(user=user).exclude(board_name="Your Saved Items")

	# create new board view instance if not exsists, count views
	board_view, created = BoardView.objects.get_or_create(board=board, ip=userip, user=request.user)
	board.views = BoardView.objects.filter(board=board).count()

	following = request.user.profile.get_connections()
	is_followed = False
	for user in following:
		if board.user == user.following:
			is_followed = True

	# handle submissions
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

		# if user followed
		if 'follow' in request.POST:
			new_connection = Connection.objects.create(
				creator = user,
				following = board.user,
			)

		# if user unfollowed
		if 'unfollow' in request.POST:
			connection = Connection.objects.filter(creator=user, following=board.user)
			connection.delete()

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

		if 'savelater' in request.POST:
			itemconx = request.POST.get("itemconx_id")
			ItemConnection.save_item(itemconx, request)
			message = "The item was added to your saved items"

	context_dict = {
		'message':message,
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
	page = ''

	if request.method == 'POST':

		if 'geturl' in request.POST:

			# the url submitted	
			url = request.POST.get("targeturl", "")
			# get the domain from the url var
			parsed_uri = urlparse(url)
			domain = '{uri.scheme}://{uri.netloc}/'.format(uri=parsed_uri)
			# set up selenium to use headless chrome
			driver = webdriver.Chrome("/usr/bin/chromedriver", chrome_options=chrome_options)
			driver.get(url)
			# assign the scraped page content to response
			response = driver.page_source
			allimages = driver.find_elements_by_tag_name('img')
			page_title = driver.title
			# soup = BeautifulSoup(response)
			# find all image tags in response
			# images = soup.find_all('img')
			data = []
			sizes = []

			for image in allimages:
				imgurl = image.get_attribute('src')
				if (imgurl is not None) and ("data:" not in imgurl):
					# check is src starts without full path and append with domain appropriately 
					if not imgurl.startswith("http"):
						if imgurl.startswith("//"):
							imgurl = "https:" + imgurl
						else:
							imgurl = domain + imgurl

					# get the sizes		
					file = urllib.request.urlopen(imgurl)
					size = file.headers.get("content-length")
					if size: size = int(size)
					p = ImageFile.Parser()
					while 1:
						imgdata = file.read(1024)
						if not imgdata:
							break
						p.feed(imgdata)
						if p.image:
							if p.image.size[0] > 200:
								sizes.append(p.image.size[0])
								data.append(imgurl)
							break
					file.close()					
					
			context_dict = {
				'board':board,
				'form':form,
				'data':data,
				'domain':domain,
				'sizes':sizes,
				'url':url,
				'allimages':allimages,
				'pagetitle':page_title,
			}

			return render(request, template, context_dict)

		if 'additem' in request.POST:
			form = ItemForm(request.POST, request.FILES)
			imgsrc = request.POST.get("imgsrc")
			item_name = request.POST.get("item_name")
			purchase_url = request.POST.get("purchase_url")
			item_status = request.POST.get("item_name")
			item_desc = request.POST.get("item_desc")
			item_active = request.POST.get("item_active")
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
				new_item = form.save(commit=False)
				new_item.item_name = item_name
				new_item.save()
				new_item_conx = ItemConnection()
				new_item_conx.board = board
				new_item_conx.item = new_item
				new_item_conx.purchase_url = purchase_url
				new_item_conx.status = item_status
				new_item_conx.item_desc = item_desc
				new_item_conx.active = item_active
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
		'page':page,
	}

	return render(request, template, context_dict)


##### Like Board
def like_board(request, board_id):
	user = request.user
	board = get_object_or_404(Board, pk=board_id)
	BoardLike.like(board, user)
	board_user = board.user
	return redirect('b:view_board', username=board_user, board_name=board.slug)


##### Unlike Board
def unlike_board(request, board_id):
	user = request.user
	board = get_object_or_404(Board, pk=board_id)
	BoardLike.unlike(board, user)
	board_user = board.user
	return redirect('b:view_board', username=board_user, board_name=board.slug)


##### Search Items
def search_item(request):
	template = 'board/search_item.html'

	# set things up
	item_results = []
	search_term = ""
	search_term = request.GET.get('kw', '')

	#items 
	items = Item.objects.filter(item_name__contains=search_term)
	for item in items:
		item_conxs = ItemConnection.objects.filter(item=item)
		for item in item_conxs:
			item.likes = ItemLike.objects.filter(item_conx=item).count()
			item.is_liked = ItemLike.objects.filter(item_conx=item, user=request.user).exists()
			item.views = ItemView.objects.filter(item_conx=item).count()
			item_results.append(item)

	# boards
	board_results = False
	board_search_tags = Board.objects.filter(tags__name__in=[search_term])
	board_search_names = Board.objects.filter(board_name__contains=search_term)
	board_results = board_search_tags | board_search_names
	board_results = board_results.distinct()
	for board in board_results:
		board.totalitems = board.get_item_count()

	# users
	user_results = False
	user_results = User.objects.filter(username__contains=search_term)

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
	search_term = ""
	search_term = request.GET.get('kw', '')

	#items 
	items = Item.objects.filter(item_name__contains=search_term)
	for item in items:
		item_conxs = ItemConnection.objects.filter(item=item)
		for item in item_conxs:
			item.likes = ItemLike.objects.filter(item_conx=item).count()
			item.is_liked = ItemLike.objects.filter(item_conx=item, user=request.user).exists()
			item.views = ItemView.objects.filter(item_conx=item).count()
			item_results.append(item)

	# boards
	board_results = False
	board_search_tags = Board.objects.filter(tags__name__in=[search_term])
	board_search_names = Board.objects.filter(board_name__contains=search_term)
	board_results = board_search_tags | board_search_names
	board_results = board_results.distinct()
	for board in board_results:
		board.totalitems = board.get_item_count()
		board.views = BoardView.objects.filter(board=board).count()
		board.itemconxs = ItemConnection.objects.filter(board=board)[:5]	

	# users
	user_results = False
	user_results = User.objects.filter(username__contains=search_term)

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
	search_term = ""
	search_term = request.GET.get('kw', '')

	#items 
	items = Item.objects.filter(item_name__contains=search_term)
	for item in items:
		item_conxs = ItemConnection.objects.filter(item=item)
		for item in item_conxs:
			item.likes = ItemLike.objects.filter(item_conx=item).count()
			item.is_liked = ItemLike.objects.filter(item_conx=item, user=request.user).exists()
			item.views = ItemView.objects.filter(item_conx=item).count()
			item_results.append(item)

	# boards
	board_results = False
	board_search_tags = Board.objects.filter(tags__name__in=[search_term])
	board_search_names = Board.objects.filter(board_name__contains=search_term)
	board_results = board_search_tags | board_search_names
	board_results = board_results.distinct()
	for board in board_results:
		board.totalitems = board.get_item_count()

	# users
	user_results = False
	user_results = User.objects.filter(username__contains=search_term)
	for user in user_results:
		# set things up
		user.itemcount = 0
		user.viewscount = 0
		user.items = []

		# get all boards
		boards = Board.objects.filter(user=user)
		# set board count
		user.boardcount = boards.count()
		#cycle through boards
		for board in boards:
			# get the board views
			boardviews = BoardView.objects.filter(board=board).count()
			# get all items for this board and count 
			boarditems = ItemConnection.objects.filter(board=board)			
			user.itemcount+=boarditems.count()
			itemviews = 0
			x = 0
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