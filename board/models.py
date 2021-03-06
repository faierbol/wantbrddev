import os, copy
from django.db import models
from sorl.thumbnail import ImageField
from django.urls import reverse
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from taggit.managers import TaggableManager
from django.template.defaultfilters import slugify
from django.contrib import messages
from django.http import HttpResponseRedirect, HttpResponse

# Board Model
def user_directory_path(instance, filename):
    return 'user_files/{0}/hero/{1}'.format(instance.user.id, filename)


##### Board Model
class Board(models.Model):
	user = models.ForeignKey(User, on_delete=models.CASCADE)
	board_name = models.CharField(null=False, max_length=100, blank=False)	
	created = models.DateTimeField(auto_now_add=True)
	private = models.BooleanField(default=False)
	description = models.TextField(default='', max_length=500, blank=True)
	video = models.CharField(max_length=11, blank=True)
	hero = models.ImageField(upload_to = user_directory_path, blank=True, null=True)
	show_video = models.BooleanField(default=False)
	tags = TaggableManager(blank=True)
	active = models.BooleanField(default=False)	
	slug = models.SlugField(default='', max_length=255)
	deleteable = models.BooleanField(default=True)
	recommended = models.BooleanField(default=False)

	def save(self, *args, **kwargs):
		self.slug = slugify(self.board_name)
		super(Board, self).save(*args, **kwargs)

	def get_item_count(self):
		item_count = ItemConnection.objects.filter(board=self,active=True).count()
		return item_count

	def user_blocked(self,user):
		if BoardPrivacy.objects.filter(board=self, user=user).exists():
			return True
		else:
			return False		

	def __str__(self):
		return self.board_name


##### Board Like Model
class BoardLike(models.Model):
	user = models.ForeignKey(User, on_delete=models.CASCADE)
	board = models.ForeignKey(Board, on_delete=models.CASCADE)
	created = models.DateTimeField(auto_now_add=True)

	# unlike board class method
	def unlike(board, user):
		like = BoardLike.objects.filter(user=user, board=board)
		like.delete()	    				

	# like board class method
	def like(board, user):
		new_like = BoardLike.objects.create(
			user=user,
			board=board,
		)


##### Track board views
class BoardView(models.Model):
	board = models.ForeignKey(Board, on_delete=models.CASCADE)
	ip = models.CharField(max_length=16)


##### Item Model
class Item(models.Model):		
	item_name = models.CharField(null=False, max_length=255, blank=False)		

	def __str__(self):
		return self.item_name


##### Item Connections
class ItemConnection(models.Model):
	board = models.ForeignKey(Board, on_delete=models.CASCADE)
	image = ImageField(upload_to = 'uploads/items/', default = 'defaults/no-item.png')
	img_own = models.BooleanField(default=False)
	itook = models.BooleanField(default=False)
	item = models.ForeignKey(Item, on_delete=models.CASCADE)
	slug = models.SlugField(default='', max_length=255)
	created = models.DateTimeField(auto_now_add=True)
	allow_comments = models.BooleanField('allow comments', default=True)
	purchase_url = models.URLField(max_length=2000, blank=True)
	original_purchase_url = models.URLField(max_length=2000, blank=True)
	item_desc = models.CharField(max_length=1000, blank=True)
	review = models.CharField(max_length=1000, blank=True, default='')
	front_page_review = models.BooleanField(default=False)
	rating = models.IntegerField(null=False, blank=False, default=1)
	image_owner = models.IntegerField(null=True, blank=True)
	tags = TaggableManager(blank=True)
	WANT = 'WNT'
	GOT = 'GOT'
	ITEM_STATUS_CHOICES = (
		(WANT, 'I want this'),
		(GOT, 'I\'ve got this'),
	)
	item_status = models.CharField(
		max_length=3,
		choices=ITEM_STATUS_CHOICES,
		default=WANT,
	)
	active = models.BooleanField(default=True)

	def __str__(self):
		return self.item.item_name

	def save(self, *args, **kwargs):
		self.slug = slugify(self.item.item_name)
		super(ItemConnection, self).save(*args, **kwargs)

	def save_item(itemconx, request):
		# current user
		user = request.user
		# board to copy to
		board = Board.objects.get(user=user, board_name="Your Saved Items")
		# get model of item connection we're copying
		itemconx = ItemConnection.objects.get(pk=itemconx)
		# create clone
		clone = copy.copy(itemconx)
		# remove pk and add destination board to clone
		clone.pk = None
		clone.board = board	
		clone.review = ''
		clone.item_status = 'WNT'
		clone.item_desc = ''		
		clone.rating = 1
		clone.purchase_url = itemconx.original_purchase_url		
		# remove prefetch cache, becuase...
		try:
		    delattr(clone, '_prefetched_objects_cache')
		except AttributeError:
		    pass
		clone.save()	

	def copy_to_board(boardid, new_board_name, itemconxid, request):
		# if we're adding a new board
		if boardid == 'newBoard':

			if new_board_name == '':
				return "no name"
				
			else:			
				#check the board name has not already been used
				new_board_name = request.POST.get("addNewBoard")
				user_boards = Board.objects.filter(user=request.user)

				if user_boards.filter(board_name=new_board_name).exists():
					return "name exists"

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
		clone.purchase_url = itemconx.original_purchase_url
		clone.review = ''
		clone.rating = 1
		clone.item_desc = ''
		# remove prefetch cache, becuase...
		try:
		    delattr(clone, '_prefetched_objects_cache')
		except AttributeError:
		    pass
		clone.save()
		return itemconx
		


##### Item Like Model
class ItemLike(models.Model):
	item_conx = models.ForeignKey(ItemConnection, on_delete=models.CASCADE)
	user = models.ForeignKey(User, on_delete=models.CASCADE)	
	created = models.DateTimeField(auto_now_add=True)

	# like item class method
	def like(itemconx, user):		
		new_like = ItemLike.objects.create(
			user=user,
			item_conx=itemconx,
		)

	# unlike item class method
	def unlike(itemconx, user):
		like = ItemLike.objects.filter(
			user=user,
			item_conx=itemconx
		)
		like.delete()	    				


# Collections
class Collection(models.Model):
	name = models.CharField(null=False, max_length=100, blank=False)
	description = models.TextField(default='', blank=True)
	item_conx = models.ManyToManyField(ItemConnection)
	board = models.ManyToManyField(Board)
	slug = models.SlugField(default='', max_length=255)

	def __str__(self):
		return self.name

	def save(self, *args, **kwargs):
		self.slug = slugify(self.name)
		super(Collection, self).save(*args, **kwargs)


# Communities
class Community(models.Model):
	name = models.CharField(null=False, max_length=100, blank=False)
	tag = models.CharField(max_length=100, blank=True)
	products_included = models.TextField(default='', blank=True)
	description = models.TextField(default='', blank=True)
	front_page = models.BooleanField(default=False)
	image = ImageField(upload_to = 'uploads/community/', default = 'defaults/no-item.png')
	slug = models.SlugField(default='', max_length=255)

	def __str__(self):
		return self.name

	def save(self, *args, **kwargs):
		self.slug = slugify(self.name)
		super(Community, self).save(*args, **kwargs)

# Track item views
class ItemView(models.Model):
	item_conx = models.ForeignKey(ItemConnection, on_delete=models.CASCADE)
	ip = models.CharField(max_length=16)


# Privacy
class BoardPrivacy(models.Model):
	board = models.ForeignKey(Board, on_delete=models.CASCADE)
	user = models.ForeignKey(User, on_delete=models.CASCADE)