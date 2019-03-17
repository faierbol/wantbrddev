import requests, urllib, datetime, base64
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User
from board.models import ItemLike, BoardLike, ItemConnection, ItemView, BoardView, Board, BoardPrivacy, Community
from user.models import Notification
from django.urls import reverse
from django.contrib.staticfiles.templatetags.staticfiles import static



### GET TRENDING ITEMS
def ajax_trending_items(request, period):
	# current datetime and datetime 3 days ago
	now = datetime.datetime.now()
	ago = now - datetime.timedelta(days=period)

	# get all item like objects between date range
	try:
		item_likes = ItemLike.objects.filter(created__range=[ago, now])	
	except:
		pass
	
	itemconxs = []

	# if there are item like objects
	if item_likes:
		for item in item_likes:
			# if the item connection related to the item like is not already in our list, add it
			if item.item_conx not in itemconxs:
				itemconxs.append(item.item_conx)

		trending_items = []

		# now we have a unique list of itemconx's, loop through them
		for item in itemconxs:
			if not item.board.private:
				
				ti_dict = {}
				item_name = item.item.item_name
				item_likes = ItemLike.objects.filter(item_conx=item).count()
				try:
					item_is_liked = ItemLike.objects.filter(item_conx=item, user=request.user).exists()
				except:
					item_is_liked = False
				item_views = ItemView.objects.filter(item_conx=item).count()						
				item_image = item.image.url
				item_id = item.id
				item_slug = item.slug
				user = item.board.user.get_full_name()
				username = item.board.user.username
				board_name = item.board.board_name
				board_slug = item.board.slug
				user_url = reverse('u:profile', kwargs={'username':username})
				item_url = reverse('b:view_item', kwargs={'username':username, 'board_name':board_name, 'item_id':item_id, 'item_slug':item_slug})			
				board_url = reverse('b:view_board', kwargs={'username':username,'board_name':board_slug})

				ti_dict = {
					'type':'trending_item',
					'item_name':item_name,
					'item_likes':item_likes,
					'item_is_liked':item_is_liked,
					'item_views':item_views,
					'item_image':item_image,
					'item_url':item_url,
					'user':user,
					'user_url':user_url,
					'board_name':board_name,
					'board_url':board_url,
				}
				trending_items.append(ti_dict)
			
	return trending_items


### GET TRENDING BOARDS
def ajax_trending_boards(request, period):

	now = datetime.datetime.now()
	ago = now - datetime.timedelta(days=period)

	board_likes = BoardLike.objects.filter(created__range=[ago, now])

	all_boards = []
	for board_like in board_likes:
		if board_like.board not in all_boards:
			all_boards.append(board_like.board)

	trending_boards = []
	tb_dict = {}

	for board in all_boards:
		if not board.private:

			board.itemconxs = ItemConnection.objects.filter(board=board, active=True)[:5]
			board.nohero = 'img/default-hero-1.jpg'

			username = board.user.username
			full_name = board.user.get_full_name()
			try:
				user_pic = board.user.profile.picture.url
			except:
				user_pic = static('img/default-hero-1.jpg')
			try:
				hero = board.hero.url
			except:
				hero = static('img/default-hero-3.jpg')

			board_name = board.board_name
			board_slug = board.slug
			total_items = board.totalitems = board.get_item_count()
			views = board.views = BoardView.objects.filter(board=board).count()		
			user_url = reverse('u:profile', kwargs={'username':username})
			board_url = reverse('b:view_board', kwargs={'username':username,'board_name':board_slug})

			getItems = ItemConnection.objects.filter(board=board, active=True)[:3]
			allitems = []
			for item in getItems:
				item_id = item.id
				item_slug = item.slug
				item_link = item_url = reverse('b:view_item', kwargs={'username':username, 'board_name':board_name, 'item_id':item_id, 'item_slug':item_slug})			
				item_dict = {
					'image':item.image.url,
					'link':item_link
				}
				allitems.append(item_dict)		

			tb_dict = {
				'type':'trending_board',
				'items':allitems,
				'username':username,
				'full_name':full_name,
				'user_pic':user_pic,
				'board_name':board_name,
				'total_items':total_items,
				'views':views,
				'user_url':user_url,
				'board_url':board_url,
				'hero':hero,
			}

			trending_boards.append(tb_dict)

	return trending_boards


### GET TRENDING USERS
def ajax_trending_users(request, period):

	now = datetime.datetime.now()
	ago = now - datetime.timedelta(days=period)

	item_likes = ItemLike.objects.filter(created__range=[ago, now])	

	users = []
	for item in item_likes:
		if item.item_conx.board.user not in users:
			users.append(item.item_conx.board.user)

	trending_users = []
	tu_dict = {}

	for user in users:
		username = user.username
		name = user.get_full_name()
		user_url = reverse('u:profile', kwargs={'username':username})
		try:
			user_pic = user.profile.picture.url
		except:
			user_pic = static('img/default-hero-1.jpg')
		try:
			hero = user.profile.url
		except:
			hero = static('img/default-hero-3.jpg')
		user_boards = Board.objects.filter(user=user).exclude(slug='your-saved-items')
		total_boards = user_boards.count()
		user_items = []
		
		x = 0		
		for board in user_boards:
			if x < 3:
				itemconxs = ItemConnection.objects.filter(board=board, active=True)
				for item in itemconxs:
					if x < 3:
						user_items.append(item)									
						x+=1
					else:
						break
			else:
				break

		getItems = user_items
		total_items = len(user_items)
		allitems = []
		for item in getItems:
			item_id = item.id
			item_slug = item.slug
			item_link = item_url = reverse('b:view_item', kwargs={'username':username, 'board_name':item.board.board_name, 'item_id':item_id, 'item_slug':item_slug})			
			item_dict = {
				'image':item.image.url,
				'link':item_link
			}
			allitems.append(item_dict)


		tu_dict = {
			'type':'trending_user',
			'total_boards':total_boards,
			'total_items':total_items,
			'user_pic':user_pic,
			'hero':hero,
			'user_url':user_url,
			'username':username,
			'name':name,
			'items':allitems
		}

		trending_users.append(tu_dict)

	return trending_users


### GET COMMUNITIES
def ajax_communities(request):

	communities = []
	com_dict = {}
	all_communities = Community.objects.filter(front_page=True)
	for community in all_communities:
		name = community.name
		description = community.description
		products = community.products_included
		image = community.image.url
		slug = community.slug
	
		com_dict = {
			'type': 'community',
			'name': name,
			'slug': slug,
			'description': description,
			'products': products,
			'image': image,
		}
	
		communities.append(com_dict);

	return communities



### GET RECOMMENDED BOARDS
def ajax_recommended_boards(request):

	rec_boards = []
	rec_dict = {}
	
	all_boards = Board.objects.filter(recommended=True)
	
	for board in all_boards:

		username = board.user.username
		full_name = board.user.get_full_name()

		try:
			hero = board.hero.url
		except:
			hero = static('img/default-hero-3.jpg')

		board_name = board.board_name
		board_slug = board.slug
		total_items = board.totalitems = board.get_item_count()
		views = board.views = BoardView.objects.filter(board=board).count()		
		user_url = reverse('u:profile', kwargs={'username':username})
		board_url = reverse('b:view_board', kwargs={'username':username,'board_name':board_slug})

		rec_dict = {
			'type':'rec_board',
			'username':username,
			'full_name':full_name,
			'board_name':board_name,
			'total_items':total_items,
			'views':views,
			'user_url':user_url,
			'board_url':board_url,
			'hero':hero,
		}

		rec_boards.append(rec_dict)

	return rec_boards


### GET HIGHLIGHTED REVIEWS
def ajax_highlighted_reviews(request):

	reviews = []
	review_dict = {}
	
	items_with_reviews = ItemConnection.objects.filter(front_page_review=True)
	
	for item in items_with_reviews:

		ti_dict = {}
		item_name = item.item.item_name
		item_image = item.image.url
		item_id = item.id
		item_slug = item.slug
		user = item.board.user.get_full_name()
		username = item.board.user.username
		board_name = item.board.board_name
		board_slug = item.board.slug
		user_url = reverse('u:profile', kwargs={'username':username})
		item_url = reverse('b:view_item', kwargs={'username':username, 'board_name':board_name, 'item_id':item_id, 'item_slug':item_slug})			
		board_url = reverse('b:view_board', kwargs={'username':username,'board_name':board_slug})
		item_review = item.review

		review_dict = {
			'type':'review',
			'item_name':item_name,
			'item_image':item_image,
			'item_url':item_url,
			'item_review':item_review,
			'user':user,
			'user_url':user_url,
			'board_name':board_name,
			'board_url':board_url,
		}
		reviews.append(review_dict)

	return reviews


# Like item & notify
def like_an_item(itemconx_id, user):			
	itemconx = get_object_or_404(ItemConnection, pk=itemconx_id)		
	try:
		ItemLike.objects.get(user=user, item_conx=itemconx)
	except:
		user_to_notify = itemconx.board.user
		new_like = ItemLike.objects.create(
			user=user,
			item_conx=itemconx,
		)		
		Notification.create_itemlike_notify(user, user_to_notify, itemconx_id)	

# Unlike item
def unlike_an_item(itemconx_id, user):
	itemconx = get_object_or_404(ItemConnection, pk=itemconx_id)
	like = ItemLike.objects.filter(
		user=user,
		item_conx=itemconx
	)
	like.delete()


# Like board and notify
def like_a_board(board_id, user):
	board = get_object_or_404(Board, pk=board_id)	
	try:
		BoardLike.objects.get(user=user, board=board)
	except:
		user_to_notify = board.user
		new_like = BoardLike.objects.create(
			user=user,
			board=board,
		)
		Notification.create_boardlike_notify(user, user_to_notify, board_id)

# Unlike board
def unlike_a_board(board_id, user):
	board = get_object_or_404(Board, pk=board_id)
	
	like = BoardLike.objects.filter(
		user=user,
		board=board,
	)
	like.delete()

# Get notifications
def get_notifications(request):
	all_notifications = Notification.objects.filter(user=request.user)
	new_notifications = []
	old_notifications = []
	for n in all_notifications:

		if n.notification_type == 'likeitem':
			n.item = ItemConnection.objects.get(pk=n.item_ref)

		if n.notification_type == 'likeboard':
			n.board = Board.objects.get(pk=n.board_ref)

		if n.seen == False:
			new_notifications.append(n)
			
		else:
			old_notifications.append(n)

	return new_notifications, old_notifications

# Decode B64
def decode_base64_file(data):

    def get_file_extension(file_name, decoded_file):
        import imghdr

        extension = imghdr.what(file_name, decoded_file)
        extension = "jpg" if extension == "jpeg" else extension

        return extension

    from django.core.files.base import ContentFile
    import base64
    import six
    import uuid

    # Check if this is a base64 string
    if isinstance(data, six.string_types):
        # Check if the base64 string is in the "data:" format
        if 'data:' in data and ';base64,' in data:
            # Break out the header from the base64 content
            header, data = data.split(';base64,')

        # Try to decode the file. Return validation error if it fails.
        try:
            decoded_file = base64.b64decode(data)
        except TypeError:
            TypeError('invalid_image')

        # Generate file name:
        file_name = str(uuid.uuid4())[:12] # 12 characters are more than enough.
        # Get the file name extension:
        file_extension = get_file_extension(file_name, decoded_file)

        complete_file_name = "%s.%s" % (file_name, file_extension, )

        return ContentFile(decoded_file, name=complete_file_name)

### IS BLOCKED
def is_blocked(board, user):
	try:
		BoardPrivacy.objects.get(board=board, user=user)
		return True
	except:
		return False