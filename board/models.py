import os, copy
from django.db import models
from sorl.thumbnail import ImageField
from django.urls import reverse
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from taggit.managers import TaggableManager
from django.template.defaultfilters import slugify

# Board Model
def user_directory_path(instance, filename):
    return 'user_files/{0}/hero/{1}'.format(instance.user.id, filename)


##### Board Model
class Board(models.Model):
	user = models.ForeignKey(User, on_delete=models.CASCADE)
	board_name = models.CharField(null=False, max_length=255, blank=False)	
	created = models.DateTimeField(auto_now_add=True)
	private = models.BooleanField(default=False)
	description = models.TextField(default='', max_length=500, blank=True)
	WANTS = 'Want'
	RECOMMENDS = 'Recommended'
	BOARD_TYPE_CHOICES = (
		(WANTS, 'Wants'),
		(RECOMMENDS, 'Recommended'),
	)
	board_type = models.CharField(
		max_length=11,
		choices=BOARD_TYPE_CHOICES,
		default=WANTS,
	)
	video = models.CharField(max_length=50, blank=True)
	hero = models.ImageField(upload_to = user_directory_path, blank=True, null=True)
	show_video = models.BooleanField(default=False)
	tags = TaggableManager(blank=True)
	active = models.BooleanField(default=False)	
	slug = models.SlugField(default='')
	deleteable = models.BooleanField(default=True)
	recommended = models.BooleanField(default=False)

	def save(self, *args, **kwargs):
		self.slug = slugify(self.board_name)
		super(Board, self).save(*args, **kwargs)

	def get_item_count(self):
		item_count = ItemConnection.objects.filter(board=self).count()
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
	user = models.ForeignKey(User, on_delete=models.PROTECT)


##### Item Model
class Item(models.Model):		
	item_name = models.CharField(null=False, max_length=255, blank=False)		

	def __str__(self):
		return self.item_name

	# def get_absolute_url(self):
	#     return reverse('board:view_item',
	#                    kwargs={'board_id': self.board.id,
	#                            'item_id': self.id})


##### Item Connections
class ItemConnection(models.Model):
	board = models.ForeignKey(Board, on_delete=models.CASCADE)
	image = ImageField(upload_to = 'uploads/items/', default = 'defaults/no-item.png')
	item = models.ForeignKey(Item, on_delete=models.CASCADE)
	created = models.DateTimeField(auto_now_add=True)
	allow_comments = models.BooleanField('allow comments', default=True)
	purchase_url = models.URLField(max_length=255, blank=True)
	item_desc = models.CharField(null=True, max_length=500, blank=True)
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
		# remove prefetch cache, becuase...
		try:
		    delattr(clone, '_prefetched_objects_cache')
		except AttributeError:
		    pass
		clone.save()		
		

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


# Track item views
class ItemView(models.Model):
	item_conx = models.ForeignKey(ItemConnection, on_delete=models.PROTECT)
	ip = models.CharField(max_length=16)
	user = models.ForeignKey(User, on_delete=models.PROTECT)	


# Privacy
class BoardPrivacy(models.Model):
	board = models.ForeignKey(Board, on_delete=models.CASCADE)
	user = models.ForeignKey(User, on_delete=models.CASCADE)