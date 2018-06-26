import requests, urllib, datetime
from django.contrib.auth.models import User
from board.models import ItemLike, BoardLike, ItemConnection, ItemView, BoardView, Board

### GET TRENDING ITEMS
def get_trending_items(request, period):
	# current datetime and datetime 3 days ago
	now = datetime.datetime.now()
	ago = now - datetime.timedelta(days=period)

	# get all itemLike objects between those dates
	item_likes = ItemLike.objects.filter(created__range=[ago, now])	

	# get all itemConnections from the item_lkes queryset
	itemconxs = []
	for item in item_likes:
		if item.item_conx not in itemconxs:
			itemconxs.append(item.item_conx)

	trending_items = []
	for item in itemconxs:
		item.likes = ItemLike.objects.filter(item_conx=item).count()
		item.is_liked = ItemLike.objects.filter(item_conx=item, user=request.user).exists()
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
		board.itemconxs = ItemConnection.objects.filter(board=board)[:5]
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
		user_boards = Board.objects.filter(user=user)
		user.totalboards = user_boards.count()
		user_items = []
		for board in user_boards:
			itemconxs = ItemConnection.objects.filter(board=board)
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
		board.itemconxs = ItemConnection.objects.filter(board=board)[:5]

	return rec_boards