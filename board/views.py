import requests, urllib, datetime, random, json, re
from django.contrib import messages
from django.core.mail import send_mail
from django.template import RequestContext
from django.shortcuts import render, redirect, get_object_or_404
from django.core.files.storage import FileSystemStorage
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q
from django.http import HttpResponseRedirect, HttpResponse
from django.contrib.auth.models import User
from .models import Board, Item, BoardLike, ItemLike, BoardView, ItemView, ItemConnection, BoardPrivacy, Collection, Community
from user.models import Notification, TagFollows
from user.views import Connection
from .forms import BoardForm, ItemForm, EditBoardForm, ChangeBackgroundForm, UpdateTags, BoardPrivacyForm
from bs4 import BeautifulSoup
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
from amazon.api import AmazonAPI
import bottlenose.api
from django.template.defaultfilters import slugify
from dal import autocomplete


def error_404(request, exception):
    data = {"name": "ThePythonDjango.com"}
    return render(request,'error_404.html', data)


def error_500(request, exception):
    data = {"name": "ThePythonDjango.com"}
    return render(request,'error_500.html', data)


##### GET HOME ITEMS
def get_home_items(request):
	
	trending_items = ajax_trending_items(request,120)
	trending_boards = ajax_trending_boards(request,240)
	trending_users = ajax_trending_users(request,240)
	communities = ajax_communities(request)
	recommended_boards = ajax_recommended_boards(request)
	highlighted_reviews = ajax_highlighted_reviews(request)

	mixed = trending_boards + trending_users + communities + recommended_boards + highlighted_reviews
	random.shuffle(mixed)

	return HttpResponse(
		json.dumps(mixed),
		content_type="application/json"
	)

##### GET TRENDING ITEMS
def get_trending_items(request):
	
	trending_items = ajax_trending_items(request,240)

	return HttpResponse(
		json.dumps(trending_items),
		content_type="application/json"
	)

##### GET TRENDING USERS
def get_trending_users(request):
	
	trending_users = ajax_trending_users(request,240)	

	return HttpResponse(
		json.dumps(trending_users),
		content_type="application/json"
	)

##### GET TRENDING BOARDDS
def get_trending_boards(request):
	
	trending_boards = ajax_trending_boards(request,240)

	return HttpResponse(
		json.dumps(trending_boards),
		content_type="application/json"
	)

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

	context_dict = {}

	return render(request, template, context_dict)


##### Home Trending Items
def trending_items(request):
	template = 'trending_items.html'

	context_dict = {}

	return render(request, template, context_dict)


##### Home Trending Boards
def trending_boards(request):
	template = 'trending_boards.html'

	context_dict = {}

	return render(request, template, context_dict)


##### Home Trending Users
def trending_users(request):
	template = 'trending_users.html'

	trending_users = ajax_trending_users(request,365)

	context_dict = {}

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
def edit_board(request, board_id, itemadded=''):
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
	privacy_form = BoardPrivacyForm()
	for item in item_conxs:
		item.likes = ItemLike.objects.filter(item_conx=item).count()
		try:
			item.is_liked = ItemLike.objects.filter(item_conx=item, user=request.user).exists()
		except:
			item.is_liked = False
		item.views = ItemView.objects.filter(item_conx=item).count()
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
				b64pic = request.POST.get("b64pic")
				bgform = ChangeBackgroundForm(request.POST, instance=board)
				if bgform.is_valid():
					ub = bgform.save(commit=False)
					ub.hero = decode_base64_file(b64pic)
					ub.save()		
					messages.info(request, 'Your boards background was updated.')
					return HttpResponseRedirect(request.path_info)
				else:
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
					

			# manage video
			if request.POST.get("updatevideo"):
				video_status = request.POST.get("show_video")
				video_id = request.POST.get("videoid")
				Board.objects.filter(pk=board.id).update(video=video_id)
				if video_status:					
					Board.objects.filter(pk=board.id).update(show_video=True)
				else:
					Board.objects.filter(pk=board.id).update(show_video=False)
				messages.info(request, 'your video settings were updated.')
				return HttpResponseRedirect(request.path_info)


			# manage board visibility
			if request.POST.get("updatevisibility"):
				board_status = request.POST.get("show_board")
				if board_status:
					Board.objects.filter(pk=board.id).update(private=False)
					messages.info(request, 'Your board is now visible to users.')
				else:
					Board.objects.filter(pk=board.id).update(private=True)		
					messages.info(request, 'Your board is now hidden from users.')		
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

			# update name
			if request.POST.get("updateboardname"):
				new_name = request.POST.get("boardName")
				newslug = slugify(new_name)
				Board.objects.filter(pk=board.id).update(board_name=new_name, slug=newslug)
				messages.info(request, 'Your board name was updated.')
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

					notifications = Notification.objects.filter(item_ref=request.POST.get("item_id",""))
					for n in notifications:
						n.delete()

					return HttpResponseRedirect(request.path_info)
				# if the current user is not the owner
				else:
					return HttpResponseRedirect(request.path_info)

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

			# otherwise				
			else:
				form = EditBoardForm(request.POST, request.FILES, instance=board)
				if form.is_valid():
					form = form.save()					
					return redirect('b:my_boards')
		else:
			# create a form using the current board instance
			form = EditBoardForm(instance=board)	

		try:
			item_to_tweet = ItemConnection.objects.get(pk=itemadded)
		except:
			item_to_tweet = ''

		context_dict = {
			'board':board,
			'form':form,
			'editable':editable,
			'bgform':bgform,
			'privacy_form':privacy_form,
			'tagform':tagform,
			'items':items,
			'allusers':allusers,
			'deniedusers':deniedusers,
			'item_to_tweet':item_to_tweet,
		}

		return render(request, template, context_dict)


##### Edit item
def edit_item(request, board_slug, itemconx_id, item_slug):
	template = 'board/edit_item.html'
	itemconx = get_object_or_404(ItemConnection, pk=itemconx_id)
	fpreview = itemconx.front_page_review	
	board = get_object_or_404(Board, id=itemconx.board.id)
	user_boards = Board.objects.filter(user=request.user)
	item = get_object_or_404(Item, pk=itemconx.item.id)
	form = ItemForm(instance=itemconx)
	rev_remain =  1000 - len(itemconx.review)
	desc_remain =  1000 - len(itemconx.item_desc)

	if request.method == 'POST':

		if 'updateitem' in request.POST:
			form = ItemForm(request.POST, instance=itemconx)
			item_name = request.POST.get("item_name")
			current_board = request.POST.get("currentBoard")
			rating = request.POST.get("your_rating")
			board_assign = Board.objects.get(id=current_board)

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
				itemconx.front_page_review = fpreview
				itemconx.rating = rating
				itemconx.board = board_assign
				form.save()		

				return redirect('b:edit_board', board_id=board.id)

			else:
				return redirect('home')

	context_dict = {
		'board':board,
		'itemconx':itemconx,
		'form':form,
		'item':item,
		'user_boards':user_boards,
		'rev_remain':rev_remain,
		'desc_remain':desc_remain,
	}

	return render(request, template, context_dict)



##### View board
def view_board(request, username, board_name):
	template = 'board/view_board.html'	
	board_owner = get_object_or_404(User, username=username)
	user = request.user
	board = get_object_or_404(Board, slug=board_name, user=board_owner)

	if is_blocked(board, request.user):
		return redirect('home')
	else:
		pass
		
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
	userip = request.META['REMOTE_ADDR']
	refer = request.META.get('HTTP_REFERER')
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

		# if add to board
		if 'addtoboard' in request.POST:
			boardid = request.POST.get("board_id")
			new_board_name = ''
			itemconxid =  request.POST.get("itemconx_id")
			itemconx = ItemConnection.copy_to_board(boardid, new_board_name, itemconxid, request)
			messages.info(request, '"{0}" was added to the board, "{1}".'.format(itemconx.item.item_name, board.board_name))
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
def view_item(request, username, board_name, item_id, item_slug):
	template = 'board/view_item.html'
	itemconx = ItemConnection.objects.get(pk=item_id)
	itemconx.thetags = itemconx.tags.all()

	# is the user blocked from this board?
	if is_blocked(itemconx.board, request.user):
		return redirect('home')	

	# if item is in saved items board and is not current user
	if itemconx.board.slug == 'your-saved-items':
		if itemconx.board.user != request.user:
			return redirect('home')			

	# start the fun
	userip = request.META['REMOTE_ADDR']
	item_view, created = ItemView.objects.get_or_create(item_conx=itemconx, ip=userip)

	try:
		user_boards = Board.objects.filter(user=request.user)
	except:
		user_boards = False

	linkback = False
	if itemconx.image_owner:
		linkback = User.objects.get(pk=itemconx.image_owner)

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
			boardid = request.POST.get("board_id")
			new_board_name = ''
			itemconxid =  request.POST.get("itemconx_id")
			ItemConnection.copy_to_board(boardid, new_board_name, itemconxid, request)
			messages.info(request, '"{0}" was added to your board.'.format(itemconx.item.item_name))
			return HttpResponseRedirect(request.path_info)

		# if save later
		if 'savelater' in request.POST:
			itemconx = request.POST.get("itemconx_id")
			ItemConnection.save_item(itemconx, request)							
			copied_item = ItemConnection.objects.get(pk=itemconx)
			messages.info(request, '"%s" was added to your saved items board.' % copied_item.item.item_name)
			return HttpResponseRedirect(request.path_info)


	context_dict = {
		'itemconx': itemconx,
		'user_boards':user_boards,
		'linkback':linkback,
	}

	return render(request, template, context_dict)


##### Add item
def add_item(request, board_id):
	template = 'board/add_item.html'

	try:
		board = get_object_or_404(Board, pk=board_id)
	except:
		board = None

	user_boards = Board.objects.filter(user=request.user)
	form = ItemForm()
	url = ''
	timage = 'extracted image'
	b64_apic = 'base64 text'
	api = 'aaF7juZfhdnyptXo4Kjm6A'
	jsapi = 'vBlWMcz5CXvV4A-YnXhhag'
	proxy = 'no'
	cuser = request.user

	if request.method == 'GET' and 'find' in request.GET:

		find_item = request.GET.get('find', '')
		find_item = find_item.lower()
		item_results = []
		final_results = []
		results = 'no'

		found_items = Item.objects.filter(item_name__icontains=find_item)

		# loop through all Items that match this keyword
		for found_item in found_items:
			# get all ItemConnections that link to this Item
			found_itemconxs = ItemConnection.objects.filter(item=found_item, active=True).exclude(board__user=request.user)
			# loop through all ItemConnections we retrieved
			for found_itemconx in found_itemconxs:
				# is the current user blocked?
				if is_blocked(found_itemconx.board, request.user):
					pass				
				else:					
					item_results.append(found_itemconx)
					break

		if item_results:
			results = 'yes'

		context_dict = {
			'find_item':find_item,
			'board':board,
			'user_boards':user_boards,
			'results':results,
			'item_results':item_results,
			'final_results':item_results
		}

		return render(request, template, context_dict)
	
	if request.method == 'POST':			

		if 'geturl' in request.POST:

			ogimg = None
			og_img_meta = False
			sizes = []
			allimages = []
			output = []
			page_title = ''
			image = False
			meta_image = False
			html = ''
			page = ''
			method = ''
			url = request.POST.get("targeturl", "")
			parsed_uri = urlparse(url)
			domain = '{uri.scheme}://{uri.netloc}/'.format(uri=parsed_uri)

			###### CASE: AMAZON
			if domain == 'https://www.amazon.co.uk/' or domain == 'https://www.amazon.com/':
				modded_url = quote_plus(url)
				user_agent = quote_plus('Mozilla/5.0 (compatible; GroupShareX/1.0; +http://www.google.com/bot.html)')
				method = 'amazon'

				# new method
				with requests.Session() as s:
					s.headers['User-Agent'] = user_agent
					response = s.get(url)
					soup = BeautifulSoup(response.text,"lxml")
					page_title = soup.title.string
					
					image = [x['data-old-hires'] for x in soup.findAll('img', {'id': 'landingImage'})]
					ogimg = image[0]
					if ogimg:
						method = 'amazon_hires'
					else:
						image = [x['src'] for x in soup.findAll('img', {'id': 'landingImage'})]
						ogimg = image[0]
						method = 'amazon_src'


			###### CASE: META_PARSER
			else:				
				try:
					page = metadata_parser.MetadataParser(url=url)
				except:
					pass

				# if we got some meta
				if page:
					try:
						page_title = page.get_metadatas('title')[0]
					except:
						pass
					try:
						meta_image = page.get_metadata('image')
					except:
						pass
			
				# if we got image from meta
				if meta_image:
					ogimg = meta_image
					method = 'metaparser'
				
				####### CASE: PROXYCRAWL
				else:
					modded_url = quote_plus(url)
					try:
						response = requests.get('https://api.proxycrawl.com/?token=' + jsapi + '&format=json&page_wait=3000&url=' + modded_url, timeout=30)	
						parsed_json = response.json()
						html = parsed_json['body']
						soup = BeautifulSoup(html)				

						# if we didnt already get the meta page title
						if not page_title:
							try:
								page_title = soup.title.string
							except:
								pass

						# try bs to find OG first
						ogmeta = soup.find("meta",  property="og:image")
						if ogmeta:
							ogimg = ogmeta["content"]
							method = 'scraped ogimage'

						# otherwise just scrape whatever images we can find
						else:
							# image_tags = soup.findAll('img', {'src' : re.compile(r'(jpe?g)|(png)$')})
							image_tags = soup.findAll('img')
							# loop through all img's found
							for img in image_tags:

								# get src from img
								imgurl = img.get('src')

								# check a value is there and its not a data: src
								if (imgurl is not None) and ("data:" not in imgurl):

									if imgurl.lower().endswith(('.bmp', '.gif', '.tif')):
										pass

									else:
										# check if src starts without full path and append with domain appropriately 
										if not imgurl.startswith("http"):
											if imgurl.startswith("//"):
												imgurl = "https:" + imgurl
											else:
												imgurl = domain + imgurl	

										allimages.append(imgurl)

										try:
											image_raw = requests.get(imgurl)
											the_image = Image.open(BytesIO(image_raw.content))
											img_width, img_height = the_image.size
											if img_width > 250:
												output.append(imgurl)
											method = 'scraped'
										except:
											pass
					except:
						pass

			context_dict = {
				'board':board,
				'form':form,
				'domain':domain,
				'url':url,				
				'ogimg':ogimg,				
				'output':output,
				'page_title':page_title,
				'user_boards':user_boards,
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
			current_board = request.POST.get("currentBoard")
			original_url = request.POST.get("original_url")
			board_assign = Board.objects.get(id=current_board)
			itook = request.POST.get("itook")
			board_assign = Board.objects.get(id=current_board)			

			if itook == "itook":
				itook = True
			else:
				itook = False

			if item_active == "active":
				item_active = True
			else:
				item_active = False

			if imgsrc == 'web':				
				url = request.POST.get("scrapedimg")
				if url.startswith('//'):
					url = 'https:' + url					

				resp = requests.get(url)
				if resp.status_code != 200:
					resp = requests.get('https://api.proxycrawl.com/?token=' + api + '&format=html&url=' + url, timeout=30)					
					proxy = 'yes'
				fp = BytesIO()
				fp.write(resp.content)
				full_file_name = url.split("/")[-1]
				file_name = full_file_name[0:25]

			if form.is_valid():
				# create a new item with this item name and save it
				new_item = Item()
				new_item.item_name = item_name
				new_item.save()
				
				# save the model form				
				new_item_conx = form.save(commit=False)
				if item_status == 'GOT':
					new_item_conx.rating = rating
				new_item_conx.board = board_assign
				new_item_conx.item = new_item
				if itook == True:
					new_item_conx.image_owner = request.user.id
				
				if imgsrc == 'own':
					b64pic = request.POST.get("b64pic")
					new_item_conx.image = decode_base64_file(b64pic)
					new_item_conx.img_own = True
					new_item_conx.save()

				if imgsrc == 'amazon':
					b64pic = request.POST.get("amazonb64")

					if b64pic.startswith('http'):
						url = b64pic
						if url.startswith('//'):
							url = 'https:' + url					

						resp = requests.get(url)
						if resp.status_code != 200:
							resp = requests.get('https://api.proxycrawl.com/?token=' + api + '&format=html&url=' + url, timeout=30)					
							proxy = 'yes'
						fp = BytesIO()
						fp.write(resp.content)
						full_file_name = url.split("/")[-1]
						file_name = full_file_name[0:25]
					else:
						imgsrc = b64pic.replace(" ", "")
						new_item_conx.image = decode_base64_file(imgsrc)
						new_item_conx.save()					

				else:
					new_item_conx.image.save(file_name, files.File(fp))				

				new_item_conx.original_purchase_url = original_url
				new_item_conx.save()
				form.save_m2m()					

				return redirect('b:edit_board_added', board_id=new_item_conx.board.id, itemadded=new_item_conx.id)					
				

	context_dict = {
		'timage': timage,
		'board':board,
		'user_boards':user_boards
	}

	return render(request, template, context_dict)


### add existing item
def add_existing_item(request, board_id, itemconx_id):
	try:
		board = get_object_or_404(Board, pk=board_id)
	except:
		board = None

	template = 'board/add_item.html'
	itemconx = ItemConnection.objects.get(id=itemconx_id)
	item_to_copy = Item.objects.get(pk=itemconx.item.id)
	ogimg = itemconx.image.url
	page_title = itemconx.item.item_name
	user_boards = Board.objects.filter(user=request.user)
	url = itemconx.original_purchase_url
	existing_item = True
	form = ItemForm()

	context_dict = {
		'itemconx':itemconx,
		'ogimg':ogimg,
		'board':board,
		'page_title':page_title,	
		'url':url,
		'user_boards':user_boards,
		'existing_item':existing_item,
		'form':form,
	}

	if request.method == 'POST':
		if 'additem' in request.POST:

			# Just grabbing and setting up all the values
			form = ItemForm(request.POST, request.FILES)
			imgsrc = request.POST.get("imgsrc")
			item_name = request.POST.get("item_name")
			purchase_url = request.POST.get("purchase_url")
			item_status = request.POST.get("item_status")
			item_desc = request.POST.get("item_desc")
			item_active = request.POST.get("active")
			rating = request.POST.get("rating")
			review = request.POST.get("review")
			current_board = request.POST.get("currentBoard")
			itook = request.POST.get("itook")
			board_assign = Board.objects.get(id=current_board)

			if itook == "itook":
				itook = True
			else:
				itook = False

			if item_active == "active":
				item_active = True
			else:
				item_active = False
						
			# create clone itemconnection of the item we're copying
			clone = copy.copy(itemconx)
			# remove pk and add destination board to clone
			clone.pk = None
			# remove prefetch cache, becuase...
			try:
			    delattr(clone, '_prefetched_objects_cache')
			except AttributeError:
			    pass

			if form.is_valid():
				# save the new form instance to a var
				new_itemconx = form.save(commit=False)				
				# if the name has changed from the one copied...
				if item_name != item_to_copy.item_name:
					# we must create a new one.
					new_item = Item()
					# give the new item the new name
					new_item.item_name = item_name
					new_item.save()
					# assign the new item to the cloned itemconnection
					new_itemconx.item = new_item
				else:
					new_itemconx.item = clone.item

				
				# save all the other item details
				if item_status == 'GOT':
					new_itemconx.rating = rating
				else:
					new_itemconx.rating = 1
				new_itemconx.board = board_assign

				# replace  the image if it was changed (can only be own)
				if imgsrc == 'own':
					b64pic = request.POST.get("b64pic")					
					new_itemconx.image = decode_base64_file(b64pic)
					clone.img_own = True	
					if itook == True:
						new_itemconx.image_owner = request.user.id
					else:
						new_itemconx.image_owner = False									
				else:
					new_itemconx.image = clone.image

				new_itemconx.save()
				form.save_m2m()

				return redirect('b:edit_board_added', board_id=board_id, itemadded=new_itemconx.id)

			else:
				context_dict = {
					'itemconx':itemconx,
					'ogimg':ogimg,
					'board':board,
					'page_title':page_title,	
					'url':url,
					'user_boards':user_boards,
					'existing_item':existing_item,
					'form':form,
				}
				return render(request, template, context_dict)

	return render(request, template, context_dict)



##### COLLECTIONS
def collection(request, collection_slug):
	template = 'board/collection.html'
	collection = Collection.objects.get(slug=collection_slug)
	
	### items
	items = collection.item_conx.all()
	item_results = []
	for item in items:
		if is_blocked(item.board, request.user):
			pass
		else:
			item.likes = ItemLike.objects.filter(item_conx=item).count()
			try:
				item.is_liked = ItemLike.objects.filter(item_conx=item, user=request.user).exists()
			except:
				item.is_liked = False
			item.views = ItemView.objects.filter(item_conx=item).count()
			item_results.append(item)


	### boards
	boards = collection.board.all()
	board_results = []
	for board in boards:
		try:
			if board.get_item_count() > 0 and not board.user_blocked(request.user):
				board_results.append(board)
		except:
			if board.get_item_count() > 0:
				board_results.append(board)
	for board in board_results:
		board.totalitems = board.get_item_count()
		board.views = BoardView.objects.filter(board=board).count()
		board.likes = BoardLike.objects.filter(board=board).count()
		board.itemconxs = ItemConnection.objects.filter(board=board, active=True)[:3]

	mixed = list(item_results) + list(board_results)
	random.shuffle(mixed)	

	context_dict = {
		'collection':collection,
		'mixed':mixed,
	}

	return render(request, template, context_dict)


##### COMMUNITIES
def community(request, community_slug):
	template = 'board/community.html'
	community = Community.objects.get(slug=community_slug)
	terms = community.tag.split(",")
	results = []
	board_results = []
	board_results_tmp = []
	item_results = []

	for term in terms:
		items = ItemConnection.objects.filter(tags__name__in=[term]).exclude(board__private=True)
		if items:
			for item in items:
				item_results.append(item)
		boards = Board.objects.filter(tags__name__in=[term]).exclude(private=True)				
		if boards:
			for board in boards:
				try:
					if board.get_item_count() > 0 and not board.user_blocked(request.user):
						board_results_tmp.append(board)
				except:
					pass
			for board in board_results_tmp:
				board.totalitems = board.get_item_count()
				board.views = BoardView.objects.filter(board=board).count()
				board.itemconxs = ItemConnection.objects.filter(board=board, active=True)[:3]
				board_results.append(board)

	mixed = board_results + item_results
	random.shuffle(mixed)	
	for item in mixed:
		if item not in results:
			results.append(item)

	context_dict = {
		'items': item_results,
		'mixed': mixed,
		'terms': terms,
		'results': results,
		'community': community,
	}

	return render(request, template, context_dict)


##### Search ALL
def search(request):
	template = 'board/search.html'

	# set things up
	all_results = []
	item_results = []
	search_term = request.GET.get('kw', '')
	search_term = search_term.lower()
	board_count = 0
	item_count = 0
	user_count = 0

	#items 
	all_items = []
	item_search_names = []
	item_obj = Item.objects.filter(item_name__icontains=search_term)
	for item in item_obj:
		item_conxs = ItemConnection.objects.filter(item=item, active=True).exclude(board__slug='your-saved-items').exclude(board__private=True)
		for item in item_conxs:
			item_search_names.append(item)

	item_search_tags = ItemConnection.objects.filter(tags__name__in=[search_term]).exclude(board__private=True)
	item_search_tags = list(item_search_tags)
	items_list = item_search_tags + item_search_names
	for item in items_list:
		if item.item.item_name not in all_items:
			all_items.append(item)
		else:
			pass

	for item in all_items:
		if is_blocked(item.board, request.user):
			pass
		else:
			item.likes = ItemLike.objects.filter(item_conx=item).count()
			try:
				item.is_liked = ItemLike.objects.filter(item_conx=item, user=request.user).exists()
			except:
				item.is_liked = False
			item.views = ItemView.objects.filter(item_conx=item).count()
			item_results.append(item)			

	# boards
	all_boards = False
	board_results = []
	board_search_tags = Board.objects.filter(tags__name__in=[search_term]).exclude(slug='your-saved-items').exclude(private=True)
	board_search_names = Board.objects.filter(board_name__icontains=search_term).exclude(slug='your-saved-items').exclude(private=True)
	all_boards = board_search_tags | board_search_names
	all_boards = all_boards.distinct()	
	for board in all_boards:
		if not board.private:
			try:
				if board.get_item_count() > 0 and not board.user_blocked(request.user):
					board_results.append(board)
			except:
				if board.get_item_count() > 0:
					board_results.append(board)
	for board in board_results:
		board.totalitems = board.get_item_count()
		board.views = BoardView.objects.filter(board=board).count()
		board.itemconxs = ItemConnection.objects.filter(board=board, active=True)[:3]
	

	# users
	user_results = False
	user_results = User.objects.filter(Q(username__icontains=search_term) | Q(first_name__icontains=search_term) | Q(last_name__icontains=search_term))
	for user in user_results:
		# set things up
		user.itemcount = 0
		user.viewscount = 0
		user.items = []

		# get all boards
		boards = Board.objects.filter(user=user).exclude(slug='your-saved-items').exclude(private=True)
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
				if x < 3:
					user.items.append(item)
				x+=1				
			user.viewscount = boardviews + itemviews

	mixed = list(user_results) + list(board_results) + list(item_results)
	random.shuffle(mixed)	
	for item in mixed:
		if item not in all_results:
			all_results.append(item)

	board_count = len(board_results)
	item_count = len(item_results)
	user_count = len(user_results)

	# is user following this term?	
	tag_term = search_term.replace(' ', '').replace("'"," ").replace('"', "")
	try:
		TagFollows.objects.get(user=request.user, tag=tag_term)
		tagfollowed = True
	except:
		tagfollowed = False

	if not all_results:
		trending_items = ajax_trending_items(request,140)
		trending_boards = ajax_trending_boards(request,140)
		trending_users = ajax_trending_users(request,140)
		suggested = trending_boards + trending_users + trending_items
		random.shuffle(suggested)
	else:
		suggested = []


	context_dict = {
		'search_term':search_term,
		'tag_term':tag_term,
		'tag_followed':tagfollowed,
		'all_results':all_results,
		'user_count':user_count,
		'item_count':item_count,
		'board_count':board_count,	
		'suggested': suggested,	
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
	all_items = []
	item_search_names = []
	item_obj = Item.objects.filter(item_name__icontains=search_term)
	for item in item_obj:
		item_conxs = ItemConnection.objects.filter(item=item, active=True).exclude(board__slug='your-saved-items').exclude(board__private=True)
		for item in item_conxs:
			item_search_names.append(item)

	item_search_tags = ItemConnection.objects.filter(tags__name__in=[search_term]).exclude(board__private=True)
	item_search_tags = list(item_search_tags)
	items_list = item_search_tags + item_search_names
	for item in items_list:
		if item.item.item_name not in all_items:
			all_items.append(item)
		else:
			pass

	for item in all_items:
		if is_blocked(item.board, request.user):
			pass
		else:
			item.likes = ItemLike.objects.filter(item_conx=item).count()
			try:
				item.is_liked = ItemLike.objects.filter(item_conx=item, user=request.user).exists()
			except:
				item.is_liked = False
			item.views = ItemView.objects.filter(item_conx=item).count()
			item_results.append(item)

	# boards
	all_boards = False
	board_results = []
	board_count = 0
	board_search_tags = Board.objects.filter(tags__name__in=[search_term])
	board_search_names = Board.objects.filter(board_name__icontains=search_term)
	
	all_boards = board_search_tags | board_search_names
	all_boards = all_boards.distinct()	
	for board in all_boards:
		try:
			if board.get_item_count() > 0 and not board.user_blocked(request.user):
				board_results.append(board)
		except:
			if board.get_item_count() > 0:
				board_results.append(board)
	board_count = len(board_results)


	# users
	user_count = user_results = User.objects.filter(Q(username__icontains=search_term) | Q(first_name__icontains=search_term) | Q(last_name__icontains=search_term)).count()

	all_results = board_count + user_count + len(item_results)

	# is user following this term?	
	tag_term = search_term.replace(' ', '').replace("'"," ").replace('"', "")
	try:
		TagFollows.objects.get(user=request.user, tag=tag_term)
		tagfollowed = True
	except:
		tagfollowed = False


	if not all_results:
		suggested = ajax_trending_items(request,140)
	else:
		suggested = []


	context_dict = {
		'search_term':search_term,
		'tag_term':tag_term,
		'tag_followed':tagfollowed,
		'item_results':item_results,
		'user_count':user_count,
		'board_count':board_count,
		'all_results':all_results,
		'suggested': suggested
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
	all_items = []
	items = Item.objects.filter(item_name__icontains=search_term)
	for item in items:
		item_conxs = ItemConnection.objects.filter(item=item, active=True).exclude(board__slug='your-saved-items')
		for item in item_conxs:
			if is_blocked(item.board, request.user):
				pass
			else:
				all_items.append(item)
	item_count = len(all_items)


	# boards
	all_boards = False
	board_results = []
	board_search_tags = Board.objects.filter(tags__name__in=[search_term])
	board_search_names = Board.objects.filter(board_name__icontains=search_term)
	all_boards = board_search_tags | board_search_names
	all_boards = all_boards.distinct()	
	for board in all_boards:
		try:
			if board.get_item_count() > 0 and not board.user_blocked(request.user):
				board_results.append(board)
		except:
			if board.get_item_count() > 0:
				board_results.append(board)
	for board in board_results:
		board.totalitems = board.get_item_count()
		board.views = BoardView.objects.filter(board=board).count()
		board.itemconxs = ItemConnection.objects.filter(board=board, active=True)[:3]

	# users
	user_count = user_results = User.objects.filter(Q(username__icontains=search_term) | Q(first_name__icontains=search_term) | Q(last_name__icontains=search_term)).count()

	all_results = item_count + user_count + len(board_results)

	# is user following this term?	
	tag_term = search_term.replace(' ', '').replace("'"," ").replace('"', "")
	try:
		TagFollows.objects.get(user=request.user, tag=tag_term)
		tagfollowed = True
	except:
		tagfollowed = False

	if not all_results:
		suggested = ajax_trending_boards(request,140)
	else:
		suggested = []


	context_dict = {
		'search_term':search_term,
		'tag_term':tag_term,
		'tag_followed':tagfollowed,
		'item_count':item_count,
		'user_count':user_count,
		'board_results':board_results,
		'all_results':all_results,
		'suggested': suggested
	}

	return render(request, template, context_dict)


##### Search Users
def search_user(request):
	template = 'board/search_user.html'

	# set things up
	item_count = 0
	search_term = request.GET.get('kw', '')
	search_term = search_term.lower()

	#items 
	all_items = []
	items = Item.objects.filter(item_name__icontains=search_term)
	for item in items:
		item_conxs = ItemConnection.objects.filter(item=item, active=True).exclude(board__slug='your-saved-items')
		for item in item_conxs:
			if is_blocked(item.board, request.user):
				pass
			else:
				all_items.append(item)
	item_count = len(all_items)


	# boards
	all_boards = False
	board_results = []
	board_count = 0
	board_search_tags = Board.objects.filter(tags__name__in=[search_term])
	board_search_names = Board.objects.filter(board_name__icontains=search_term)
	
	all_boards = board_search_tags | board_search_names
	all_boards = all_boards.distinct()	
	for board in all_boards:
		try:
			if board.get_item_count() > 0 and not board.user_blocked(request.user):
				board_results.append(board)
		except:
			if board.get_item_count() > 0:
				board_results.append(board)
	board_count = len(board_results)


	# users
	user_results = False
	user_results = User.objects.filter(Q(username__icontains=search_term) | Q(first_name__icontains=search_term) | Q(last_name__icontains=search_term))
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
				if x < 3:
					user.items.append(item)
				x+=1				
			user.viewscount = boardviews + itemviews

	all_results = item_count + board_count + len(user_results)

	# is user following this term?	
	tag_term = search_term.replace(' ', '').replace("'"," ").replace('"', "")
	try:
		TagFollows.objects.get(user=request.user, tag=tag_term)
		tagfollowed = True
	except:
		tagfollowed = False


	if not all_results:
		suggested = ajax_trending_users(request,140)
	else:
		suggested = []


	context_dict = {
		'search_term':search_term,
		'tag_term':tag_term,
		'tag_followed':tagfollowed,
		'item_count':item_count,
		'user_results':user_results,
		'board_count':board_count,
		'all_results':all_results,
		'suggested': suggested
	}

	return render(request, template, context_dict)


#### LIKE AN ITEM
def like_item(request):
	if request.method == 'POST':

		itemconx_id = request.POST.get("itemconx_id")
		itemconx = ItemConnection.objects.get(id=itemconx_id)
		item_name = itemconx.item.item_name

		merge_data = {
    		'item_name': item_name,
    		'username': itemconx.board.user.username
		}
		send_an_email(
			request,
			"emails/actions/item_liked.txt",
			"emails/actions/item_liked_body.html",
			"emails/actions/item_liked_body.txt",
			itemconx.board.user.email,
			merge_data
		)

		response_data = {}
		like_an_item(itemconx_id, request.user)		
		response_data['result'] = 'Item was liked.'
		return HttpResponse(
			json.dumps(response_data),
			content_type="application/json"
		)
	else:
		return HttpResponse(
			json.dumps({"nothing to see": "this isn't happening"}),
			content_type="application/json"
		)


#### UNLIKE AN ITEM
def unlike_item(request):
	if request.method == 'POST':
		itemconx_id = request.POST.get("itemconx_id")						
		response_data = {}
		unlike_an_item(itemconx_id, request.user)		
		response_data['result'] = 'Item was unliked.'
		return HttpResponse(
			json.dumps(response_data),
			content_type="application/json"
		)
	else:
		return HttpResponse(
			json.dumps({"nothing to see": "this isn't happening"}),
			content_type="application/json"
		)


#### LIKE A BOARD
def like_board(request):
	if request.method == 'POST':

		board_id = request.POST.get('board_id')
		board = Board.objects.get(id=board_id)
		board_name = board.board_name

		merge_data = {
    		'board_name': board_name,
    		'username': board.user.username
		}
		send_an_email(
			request,
			"emails/actions/board_liked.txt",
			"emails/actions/board_liked_body.html",
			"emails/actions/board_liked_body.txt",
			board.user.email,
			merge_data
		)
	
		response_data = {}
		like_a_board(board_id, request.user)
		response_data['result'] = 'Board was liked.'
		return HttpResponse(
			json.dumps(response_data),
			content_type="application/json"
		)
	else:
		return HttpResponse(
			json.dumps({"nothing to see": "this isn't happening"}),
			content_type="application/json"
		)


#### UNLIKE A BOARD
def unlike_board(request):
	if request.method == 'POST':
		board_id = request.POST.get('board_id')
		response_data = {}
		unlike_a_board(board_id, request.user)
		response_data['result'] = 'Board was unliked.'
		return HttpResponse(
			json.dumps(response_data),
			content_type="application/json"
		)
	else:
		return HttpResponse(
			json.dumps({"nothing to see": "this isn't happening"}),
			content_type="application/json"
		)	


#### FOLLOW USER
def follow_user(request):
	if request.method == 'POST':

		userid = request.POST.get("userid")
		user = User.objects.get(pk=userid)

		merge_data = {
    		'follower': request.user,
    		'username': user.username
		}
		send_an_email(
			request,
			"emails/actions/new_follower.txt",
			"emails/actions/new_follower_body.html",
			"emails/actions/new_follower_body.txt",
			user.email,
			merge_data
		)

		response_data = {}
		user.profile.make_connection(request)
		response_data['result'] = 'User followed.'		
		return HttpResponse(
			json.dumps(response_data),
			content_type="application/json"
		)
	else:
		return HttpResponse(
			json.dumps({"nothing to see": "this isn't happening"}),
			content_type="application/json"
		)	

#### UNFOLLOW USER
def unfollow_user(request):
	if request.method == 'POST':		
		response_data = {}
		userid = request.POST.get("userid")
		user = User.objects.get(pk=userid)
		user.profile.break_connection(request)
		response_data['result'] = 'User unfollowed.'
		return HttpResponse(
			json.dumps(response_data),
			content_type="application/json"
		)
	else:
		return HttpResponse(
			json.dumps({"nothing to see": "this isn't happening"}),
			content_type="application/json"
		)	      

#### SAVE ITEM
def save_item(request):
	if request.method == 'POST':
		response_data = {}
		itemconx = request.POST.get("itemid")
		ItemConnection.save_item(itemconx, request)							
		copied_item = ItemConnection.objects.get(pk=itemconx)
		response_data['result'] = 'Item saved.'
		return HttpResponse(
			json.dumps(response_data),
			content_type="application/json"
		)
	else:
		return HttpResponse(
			json.dumps({"nothing to see": "this isn't happening"}),
			content_type="application/json"
		)

class UserAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        if not self.request.user.is_authenticated():
            return User.objects.none()
        qs = User.objects.all()
        if self.q:
            qs = qs.filter(name__istartswith=self.q)
        return qs