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

					notifications = Notification.objects.filter(item_ref=request.POST.get("item_id",""))
					for n in notifications:
						n.delete()

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
	user_boards = Board.objects.filter(user=request.user)
	itemconx = get_object_or_404(ItemConnection, pk=itemconx_id)	
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
				itemconx.rating = rating
				itemconx.board = board_assign
				form.save()		

				return redirect('b:edit_board', board_id=board_id)

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

			# if we're adding a new board
			if boardid == 'newBoard':

				#check the board name has not already been used
				new_board_name = request.POST.get("addNewBoard")
				user_boards = Board.objects.filter(user=request.user)

				if user_boards.filter(board_name=new_board_name).exists():
					messages.info(request, 'You already have a board with this name.')
					return HttpResponseRedirect(request.path_info)

				# if the name is not aready used by this user
				else:
					#create the board
					board = Board.objects.create (
						user = request.user,
						board_name = new_board_name,
					)
			# otherwise get the board that was selected
			else:
				board = Board.objects.get(pk=boardid)

			# get model of item connection we're copying
			itemconxid =  request.POST.get("itemconx_id")
			itemconx = ItemConnection.objects.get(pk=itemconxid)
			# create clone
			clone = copy.copy(itemconx)
			# remove pk and add destination board to clone
			clone.pk = None
			clone.board = board	
			clone.item_status = 'WNT'
			clone.item_desc = ''
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
	user_boards = Board.objects.filter(user=request.user)
	linkback = False
	if itemconx.image_owner:
		linkback = User.objects.get(pk=itemconx.image_owner)

	# handle submissions
	if request.method == 'POST':

		# # like item
		# if 'likeitem' in request.POST:
		# 	itemconx_id = request.POST.get("itemconx_id")						
		# 	like_item(itemconx_id, request.user)
		# 	return HttpResponseRedirect(request.path_info)

		# # unlike item
		# if 'unlikeitem' in request.POST:
		# 	itemconx_id = request.POST.get("itemconx_id")
		# 	unlike_item(itemconx_id, request.user)
		# 	return HttpResponseRedirect(request.path_info)

		# # if user followed
		# if 'follow' in request.POST:
		# 	board.user.profile.make_connection(request)
		# 	return HttpResponseRedirect(request.path_info)

		# # if user unfollowed
		# if 'unfollow' in request.POST:
		# 	board.user.profile.break_connection(request)
		# 	return HttpResponseRedirect(request.path_info)

		# if add to board
		if 'addtoboard' in request.POST:
			# board to copy to
			boardid = request.POST.get("board_id")

			# if we're adding a new board
			if boardid == 'newBoard':

				#check the board name has not already been used
				new_board_name = request.POST.get("addNewBoard")
				user_boards = Board.objects.filter(user=request.user)

				if user_boards.filter(board_name=new_board_name).exists():
					messages.info(request, 'You already have a board with this name.')
					return HttpResponseRedirect(request.path_info)

				# if the name is not aready used by this user
				else:
					#create the board
					board = Board.objects.create (
						user = request.user,
						board_name = new_board_name,
					)
			# otherwise get the board that was selected
			else:
				board = Board.objects.get(pk=boardid)

			# get model of item connection we're copying
			itemconxid =  request.POST.get("itemconx_id")
			itemconx = ItemConnection.objects.get(pk=itemconxid)
			# create clone
			clone = copy.copy(itemconx)
			# remove pk and add destination board to clone
			clone.pk = None
			clone.board = board	
			clone.item_status = 'WNT'
			clone.item_desc = ''
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
		'itemconx': itemconx,
		'user_boards':user_boards,
		'linkback':linkback,
	}

	return render(request, template, context_dict)


##### Add item
def add_item(request, board_id):
	template = 'board/add_item.html'

	board = get_object_or_404(Board, pk=board_id)
	user_boards = Board.objects.filter(user=request.user)
	form = ItemForm()
	url = ''
	api = 'aaF7juZfhdnyptXo4Kjm6A'
	jsapi = 'vBlWMcz5CXvV4A-YnXhhag'
	proxy = 'no'

	if request.method == 'GET' and 'find' in request.GET:

		find_item = request.GET.get('find', '')
		find_item = find_item.lower()
		item_results = []
		results = 'no'

		# get all matching items
		found_items = Item.objects.filter(item_name__icontains=find_item)

		# loop through all matching items
		for item in found_items:

			# get the item connection for the item, must be active, must not belong to the person searching
			item_conx = ItemConnection.objects.filter(item=item, active=True).exclude(board__user=request.user)[0]

			# check if we have any results:
			if item_results:
				# loop through the current list of items
				for citem in item_results:
					# assume we cannot use it
					useit = False
					# if this list item has the same name as our item
					if citem.item.item_name == item_conx.item.item_name:
						# if it has less views
						if citem.views > item_conx.views:
							useit = False
						else:
							useit = True
					# else if it does not have the same name, we're good
					else:
						useit = True
				
				# if at the end of it all, this item is the highest viewed with this name, add it to the list
				if useit == True:
					item_results.append(item_conx)
			# its the first item in the list, so append it
			else:
				item_results.append(item_conx)



			#### THIS IS FROM WHEN WE WERE PREFERRING ITEMS WHICH HAD NON UPLOADED IMAGES
			# try:
			# 	item_conx = ItemConnection.objects.filter(item=item, active=True, img_own=False).exclude(board__user=request.user)[0]				
			# 	item_results.append(item_conx)
			# except IndexError:
			# 	try:
			# 		item_conx = ItemConnection.objects.filter(item=item, active=True, img_own=True).exclude(board__user=request.user)[0]
			# 		item_results.append(item_conx)
			# 	except:
			# 		pass

		if item_results:
			results = 'yes'

		context_dict = {
			'find_item':find_item,
			'item_results':item_results,
			'board':board,
			'user_boards':user_boards,
			'results':results,
		}

		return render(request, template, context_dict)
	
	if request.method == 'POST':			

		if 'geturl' in request.POST:

			ogimg = False
			og_img_meta = False
			sizes = []
			allimages = []
			output = []
			page_title = ''
			image = False
			meta_image = False
			html = ''
			page = ''
			method = 'scraped'
			url = request.POST.get("targeturl", "")
			parsed_uri = urlparse(url)
			domain = '{uri.scheme}://{uri.netloc}/'.format(uri=parsed_uri)

			####### CASE: AMAZON
			if domain == 'https://www.amazon.co.uk/':				
				match = re.findall(r'(?:[/dp/]|$)([A-Z0-9]{10})', url)
				asin = match[0]
				amazon = AmazonAPI('AKIAIB7XBGHKU3J4L7PA', 'KHC/thUX/c8q93NbM0xuqlUlq2pS8XJ++BwrxZvG', 'wantbrd-21', region="UK")
				product = amazon.lookup(ItemId=asin)
				ogimg = product.large_image_url
				page_title = product.title
				method = 'amazon'

			####### CASE: META_PARSER
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

						# try bs4 to find OG first
						ogmeta = soup.find("meta",  property="og:image")
						if ogmeta:
							ogimg = ogmeta["content"]
							method = 'bs4og'

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
				'allimages':allimages,
				'page_title':page_title,
				'html':html,
				'user_boards':user_boards,
				'method':method,
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
				new_item_conx.board = board
				new_item_conx.item = new_item
				if itook == True:
					new_item_conx.image_owner = request.user.id
				if imgsrc == 'own':
					b64pic = request.POST.get("b64pic")
					new_item_conx.image = decode_base64_file(b64pic)
					new_item_conx.img_own = True
					new_item_conx.save()
				else:
					new_item_conx.image.save(file_name, files.File(fp))
				new_item_conx.board = board_assign
				new_item_conx.original_purchase_url = original_url
				new_item_conx.save()	

				return redirect('b:edit_board', board_id=board_id)
				

	context_dict = {
		'board':board,
		'user_boards':user_boards
	}

	return render(request, template, context_dict)


### add existing item
def add_existing_item(request, board_id, item_id):
	template = 'board/add_item.html'

	itemconx = ItemConnection.objects.get(id=item_id)
	copied_item = Item.objects.get(pk=itemconx.item.id)
	board = Board.objects.get(id=board_id)
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
				if item_name != copied_item.item_name:
					# we must create a new one.
					new_item = Item()
					# give the new item the new name
					new_item.item_name = item_name
					new_item.save()
					# assign the new item to the cloned itemconnection
					clone.item = new_item

				
				# save all the other item details				
				clone.board = board_assign
				clone.itook = itook
				clone.review = review
				clone.item_desc = item_desc
				clone.purchase_url = purchase_url
				clone.active = item_active
				clone.item_status = item_status
				if item_status == 'GOT':
					clone.rating = rating
				else:
					clone.rating = 1

				# replace  the image if it was changed (can only be own)
				if imgsrc == 'own':
					b64pic = request.POST.get("b64pic")					
					clone.image = decode_base64_file(b64pic)
					clone.img_own = True	
					if itook == True:
						clone.image_owner = request.user.id
					else:
						clone.image_owner = False				
					clone.save()

				# wrap it all up
				clone.save()					
				return redirect('b:edit_board', board_id=board_id)

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
	items = Item.objects.filter(item_name__icontains=search_term)
	for item in items:
		item_conxs = ItemConnection.objects.filter(item=item, active=True)
		for item in item_conxs:
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
		board.itemconxs = ItemConnection.objects.filter(board=board, active=True)[:5]
	

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

	mixed = list(user_results) + list(board_results) + list(item_results)
	random.shuffle(mixed)	
	for item in mixed:
		if item not in all_results:
			all_results.append(item)

	board_count = len(board_results)
	item_count = len(item_results)
	user_count = len(user_results)

	context_dict = {
		'search_term':search_term,
		'all_results':all_results,
		'user_count':user_count,
		'item_count':item_count,
		'board_count':board_count,
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
	user_count = User.objects.filter(username__icontains=search_term).count()

	all_results = board_count + user_count + len(item_results)

	context_dict = {
		'search_term':search_term,
		'item_results':item_results,
		'user_count':user_count,
		'board_count':board_count,
		'all_results':all_results,
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
		item_conxs = ItemConnection.objects.filter(item=item, active=True)
		for item in item_conxs:
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
		board.itemconxs = ItemConnection.objects.filter(board=board, active=True)[:5]

	# users
	user_count = User.objects.filter(username__icontains=search_term).count()

	all_results = item_count + user_count + len(board_results)

	context_dict = {
		'search_term':search_term,
		'item_count':item_count,
		'user_count':user_count,
		'board_results':board_results,
		'all_results':all_results,
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
		item_conxs = ItemConnection.objects.filter(item=item, active=True)
		for item in item_conxs:
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

	all_results = item_count + board_count + len(user_results)

	context_dict = {
		'search_term':search_term,
		'item_count':item_count,
		'user_results':user_results,
		'board_count':board_count,
		'all_results':all_results,
	}

	return render(request, template, context_dict)