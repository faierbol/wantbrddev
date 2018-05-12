import requests, urllib
from django.shortcuts import render, redirect, get_object_or_404
from django.core.files.storage import FileSystemStorage
from django.db.models import Q
from django.http import HttpResponseRedirect
from django.contrib.auth.models import User
from .models import Board, Item, BoardLike, ItemLike, BoardView, ItemView
from user.views import Connection
from .forms import BoardForm, ItemForm, EditBoardForm, ChangeBackgroundForm, UpdateTags
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import os
from urllib.parse import urlparse
from PIL import ImageFile
from django.core import files
from io import BytesIO
import requests

# instantiate a chrome options object so you can set the size and headless preference
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--window-size=1920x1080")


##### List all users boards
def home(request):
	template = 'index.html'
	return render(request, template)


##### List all users boards
def my_boards(request):
	template = 'board/my_boards.html'

	user = request.user
	boards = Board.objects.filter(user=user.id)
	boards_dict = {
		'boards':boards
	}

	return render(request, template, boards_dict)


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

	# get the board id from the url
	board = get_object_or_404(Board, pk=board_id)
	board.thetags = board.tags.all()
	form = EditBoardForm(instance=board)
	bgform = ChangeBackgroundForm(instance=board)
	tagform = UpdateTags(instance=board)
	items = Item.objects.filter(board=board)


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
				item = get_object_or_404(Item, pk=request.POST.get("item_id",""))
				item.delete()
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
			'items':items
		}

		return render(request, template, context_dict)


##### Edit item
def edit_item(request, board_id, item_id):
	template = 'board/edit_item.html'
	board = get_object_or_404(Board, id=board_id)
	item = get_object_or_404(Item, id=item_id)
	form = ItemForm(instance=item)

	# the url submitted	
	url = item.purchase_url
	# get the domain from the url var
	parsed_uri = urlparse(url)
	domain = '{uri.scheme}://{uri.netloc}/'.format(uri=parsed_uri)
	# set up selenium to use headless chrome
	driver = webdriver.Chrome("/usr/bin/chromedriver", chrome_options=chrome_options)
	driver.get(url)
	driver.wait(1)
	driver.close
	driver.quit
	allimages = driver.find_elements_by_tag_name('img')
	page_title = driver.title

	data = []
	sizes = []

	# for image in allimages:
	# 	imgurl = image.get_attribute('src')
	# 	if (imgurl is not None) and ("data:" not in imgurl):
	# 		# check is src starts without full path and append with domain appropriately 
	# 		if not imgurl.startswith("http"):
	# 			if imgurl.startswith("//"):
	# 				imgurl = "https:" + imgurl
	# 			else:
	# 				imgurl = domain + imgurl
	# 	data.append(imgurl)

			# # get the sizes		
			# file = urllib.request.urlopen(imgurl)
			# size = file.headers.get("content-length")
			# if size: size = int(size)
			# p = ImageFile.Parser()
			# while 1:
			# 	imgdata = file.read(1024)
			# 	if not imgdata:
			# 		break
			# 	p.feed(imgdata)
			# 	if p.image:
			# 		if p.image.size[0] > 200:
			# 			sizes.append(p.image.size[0])
			# 			data.append(imgurl)
			# 		break
			# file.close()

	context_dict = {
		'board':board,
		'item':item,
		'form':form,
		'data':data,
		'allimages':allimages,
	}

	if request.method == 'POST':
		if 'updateitem' in request.POST:
			form = ItemForm(request.POST, request.FILES, instance=item)
			item_name = request.POST.get("item_name")
			purchase_url = request.POST.get("purchase_url")
			imgsrc = request.POST.get("imgsrc")		

			if imgsrc == 'web':
				url = request.POST.get("scrapedimg")
				if len(url) != 0:
					resp = requests.get(url)
					if resp.status_code != requests.codes.ok:
						return redirect('home')
					fp = BytesIO()
					fp.write(resp.content)
					file_name = url.split("/")[-1]					

			if form.is_valid():			
				item = form.save(commit=False)
				item.item_name = item_name
				item.purchase_url = purchase_url
				item.board = board
				if imgsrc == 'own':
					if len(request.FILES) != 0:
						new_image = request.FILES['ownimage']
						item.image = new_image						
						item.save()
				elif len(url) != 0:
					item.image.save(file_name, files.File(fp))
				else:
					item.save()

				return redirect('b:edit_board', board_id=board_id)



			if form.is_valid():			
				item = form.save(commit=False)
				item.item_name = item_name
				item.purchase_url = purchase_url
				item.board = board
				if len(request.FILES) != 0:
					new_image = request.FILES['ownimage']
					item.image = new_image
				item.save()
				return redirect('b:edit_board', board_id=board_id)

	return render(request, template, context_dict)


##### View all boards on the site
def view_boards(request):
	template = 'board/view_boards.html'

	context_dict = {}
	user = request.user
	boards = Board.objects.exclude(user=user).exclude(private=True).exclude(active=False)
	boardlikes = BoardLike.objects.all()	

	for board in boards:
		board.likes = BoardLike.objects.filter(board=board).count()
		board.is_liked = BoardLike.objects.filter(board=board, user=request.user).exists()
		board.views = BoardView.objects.filter(board=board).count()

	# handle submissions
	if request.method == 'POST':

		# if board unliked
		if 'unlikeboard' in request.POST:
			BoardLike.unlike(request, user)

		# if board liked
		if 'likeboard' in request.POST:
			BoardLike.like(request, user)

		return HttpResponseRedirect(request.path_info)

	context_dict = {
		'boards':boards
	}

	return render(request, template, context_dict)


##### View board
def view_board(request, username, board_name):
	template = 'board/view_board.html'	

	board = get_object_or_404(Board, slug=board_name)
	board.thetags = board.tags.all()
	board.likes = BoardLike.objects.filter(board=board).count()
	board.is_liked = BoardLike.objects.filter(board=board, user=request.user).exists()

	items = Item.objects.filter(board=board)
	userip = request.META['REMOTE_ADDR']

	for item in items:
		item.likes = ItemLike.objects.filter(item=item).count()		 
		item.is_liked = ItemLike.objects.filter(item=item, user=request.user).exists()
		item.views = ItemView.objects.filter(item=item).count()

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

		# get current user and item id
		user = request.user

		# if item unliked
		if 'unlikeitem' in request.POST:
			ItemLike.unlike(request, user)

		# if item liked
		if 'likeitem' in request.POST:
			ItemLike.like(request, user)

		# if user followed
		if 'follow' in request.POST:
			new_connection = Connection.objects.create(
				creator = user,
				following = board.user,
			)

		#if user unfollowed
		if 'unfollow' in request.POST:
			connection = Connection.objects.filter(creator=user, following=board.user)
			connection.delete()

		return HttpResponseRedirect(request.path_info)

	context_dict = {
		'is_followed': is_followed,
		'following': following,
		'items':items,
		'board':board,
	}

	return render(request, template, context_dict)


##### View item
def view_item(request, board_id, item_id):
	template = 'board/view_item.html'

	item = get_object_or_404(Item, pk=item_id)
	item.likes = ItemLike.objects.filter(item=item).count()		 
	item.is_liked = ItemLike.objects.filter(item=item, user=request.user).exists()

	# handle submissions
	if request.method == 'POST':

		# get current user and item id
		user = request.user

		# if item unliked
		if 'unlikeitem' in request.POST:
			ItemLike.unlike(request, user)

		# if item liked
		if 'likeitem' in request.POST:
			ItemLike.like(request, user)

		return HttpResponseRedirect(request.path_info)

	context_dict = {
		'item': item,
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
				new_item.purchase_url = purchase_url
				new_item.board = board
				if imgsrc == 'own':
					new_image = request.FILES['ownimage']
					new_item.image = new_image
					new_item.save()
				else:
					new_item.image.save(file_name, files.File(fp))					
				return redirect('b:edit_board', board_id=board_id)

	context_dict = {
		'board':board,
		'page':page,
	}

	return render(request, template, context_dict)


##### Populate discovery page
def discovery(request):
	template = 'user/discovery.html'

	following = request.user.profile.get_connections()

	# get boards of people the user follows and build array
	board_obj = []
	for user in following:		
		boards = Board.objects.filter(user=user.following)
		for board in boards:
			board_obj.append(board)

	# get items in board array we just made
	item_obj = []
	for board in board_obj:
		items = Item.objects.filter(board=board)
		for item in items:
			item.likes = ItemLike.objects.filter(item=item).count()
			item.is_liked = ItemLike.objects.filter(item=item, user=request.user).exists()			
			item_obj.append(item)

	# handle submissions
	if request.method == 'POST':

		# get current user and item id
		user = request.user

		# if item unliked
		if 'unlikeitem' in request.POST:
			ItemLike.unlike(request, user)

		# if item liked
		if 'likeitem' in request.POST:
			ItemLike.like(request, user)

		return HttpResponseRedirect(request.path_info)

	context_dict = {
		'boards': board_obj,
		'items': item_obj,
	}

	return render(request, template, context_dict)


##### Search
def search(request):
	template = 'board/search.html'

	item_results = False
	board_results = False
	user_results = False

	if request.method == 'POST':
		search_term = request.POST.get("search", "")	
		item_results = Item.objects.filter(item_name__contains=search_term)
		user_results = User.objects.filter(username__contains=search_term)

		# get boards matching tags
		board_search_tags = Board.objects.filter(tags__name__in=[search_term])
		# get boards matching name
		board_search_names = Board.objects.filter(board_name__contains=search_term)
		# combine querysets 
		board_results = board_search_tags | board_search_names
		# get rid of duplicates
		board_results = board_results.distinct()				

	context_dict = {
		'item_results':item_results,
		'board_results':board_results,
		'user_results':user_results,
	}

	return render(request, template, context_dict)