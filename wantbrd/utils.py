import requests, urllib, datetime
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User
from board.models import ItemLike, BoardLike, ItemConnection, ItemView, BoardView, Board
from user.models import Notification


### GET TRENDING ITEMS
def get_trending_items(request, period):
	# current datetime and datetime 3 days ago
	now = datetime.datetime.now()
	ago = now - datetime.timedelta(days=period)

	try:
		item_likes = ItemLike.objects.filter(created__range=[ago, now])	
	except:
		pass
	
	itemconxs = []
	trending_items = []

	if item_likes:
		for item in item_likes:
			if item.item_conx not in itemconxs:
				itemconxs.append(item.item_conx)
		
		for item in itemconxs:
			item.likes = ItemLike.objects.filter(item_conx=item).count()
			try:
				item.is_liked = ItemLike.objects.filter(item_conx=item, user=request.user).exists()
			except:
				item.is_liked = False
			item.views = ItemView.objects.filter(item_conx=item).count()
			trending_items.append(item)

	return trending_items


### GET TRENDING BOARDS
def get_trending_boards(request, period):
	now = datetime.datetime.now()
	ago = now - datetime.timedelta(days=period)

	board_likes = BoardLike.objects.filter(created__range=[ago, now])

	all_boards = []
	for board_like in board_likes:
		if board_like.board not in all_boards:
			all_boards.append(board_like.board)

	trending_boards = []
	for board in all_boards:
		board.totalitems = board.get_item_count()
		board.views = BoardView.objects.filter(board=board).count()
		board.itemconxs = ItemConnection.objects.filter(board=board, active=True)[:5]
		trending_boards.append(board)

	return trending_boards


### GET TRENDING USERS
def get_trending_users(request, period):
	now = datetime.datetime.now()
	ago = now - datetime.timedelta(days=period)

	item_likes = ItemLike.objects.filter(created__range=[ago, now])	

	users = []
	for item in item_likes:
		if item.item_conx.board.user not in users:
			users.append(item.item_conx.board.user)

	trending_users = []
	for user in users:
		user_boards = Board.objects.filter(user=user).exclude(slug='your-saved-items')
		user.totalboards = user_boards.count()
		user_items = []
		for board in user_boards:
			itemconxs = ItemConnection.objects.filter(board=board, active=True)
			for item in itemconxs:
				user_items.append(item)									
		user.items = user_items[:5]
		user.totalitems = len(user_items)
		trending_users.append(user)

	return trending_users


### GET RECOMMENDED BOARDS
def get_recommended_boards(request):

	rec_boards = Board.objects.filter(recommended=True)

	for board in rec_boards:
		board.totalitems = board.get_item_count()
		board.views = BoardView.objects.filter(board=board).count()
		board.itemconxs = ItemConnection.objects.filter(board=board, active=True)[:5]

	return rec_boards


# Like item & notify
def like_item(itemconx_id, user):			
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
def unlike_item(itemconx_id, user):
	itemconx = get_object_or_404(ItemConnection, pk=itemconx_id)
	like = ItemLike.objects.filter(
		user=user,
		item_conx=itemconx
	)
	like.delete()


# Like board and notify
def like_board(board_id, user):
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
def unlike_board(board_id, user):
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