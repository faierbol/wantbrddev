from django.db import models
from sorl.thumbnail import ImageField
from django.urls import reverse
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from taggit.managers import TaggableManager
from django_comments_xtd.moderation import moderator, SpamModerator
from board.badwords import badwords
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
	active = models.BooleanField(default=True)	
	slug = models.SlugField(default='')
	deleteable = models.BooleanField(default=True)

	def save(self, *args, **kwargs):
		self.slug = slugify(self.board_name)
		super(Board, self).save(*args, **kwargs)

	def __str__(self):
		return self.board_name


##### Board Like Model
class BoardLike(models.Model):
	user = models.ForeignKey(User, on_delete=models.CASCADE)
	board = models.ForeignKey(Board, on_delete=models.CASCADE)
	created = models.DateTimeField(auto_now_add=True)

	# unlike board class method
	def unlike(request, user):
		board_id = request.POST.get("board_id", "")
		board = get_object_or_404(Board, pk=board_id)
		like = BoardLike.objects.filter(user=user, board=board)
		like.delete()	    

	# like board class method
	def like(request, user):
		board_id = request.POST.get("board_id", "")
		board = get_object_or_404(Board, pk=board_id)
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
	board = models.ForeignKey(Board, on_delete=models.CASCADE)
	created = models.DateTimeField(auto_now_add=True)
	allow_comments = models.BooleanField('allow comments', default=True)
	item_name = models.CharField(null=False, max_length=255, blank=False)
	item_desc = models.CharField(null=True, max_length=500, blank=True)
	image = ImageField(upload_to = 'uploads/items/', default = 'defaults/no-item.png')	
	purchase_url = models.URLField(max_length=255, blank=True)
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
	active = models.BooleanField()

	def __str__(self):
		return self.item_name

	def get_absolute_url(self):
	    return reverse('board:view_item',
	                   kwargs={'board_id': self.board.id,
	                           'item_id': self.id})


##### Item Like Model
class ItemLike(models.Model):
	user = models.ForeignKey(User, on_delete=models.CASCADE)
	item = models.ForeignKey(Item, on_delete=models.CASCADE)
	created = models.DateTimeField(auto_now_add=True)

	# unlike item class method
	def unlike(request, user):
		item_id = request.POST.get("item_id", "")
		item = get_object_or_404(Item, pk=item_id)
		like = ItemLike.objects.filter(user=user, item=item)
		like.delete()	    

	# like item class method
	def like(request, user):
		item_id = request.POST.get("item_id", "")
		item = get_object_or_404(Item, pk=item_id)
		new_like = ItemLike.objects.create(
			user=user,
			item=item,
		)

# Track item views
class ItemView(models.Model):
	item = models.ForeignKey(Item, on_delete=models.PROTECT)
	ip = models.CharField(max_length=16)
	user = models.ForeignKey(User, on_delete=models.PROTECT)	


# Add this code at the end of the file.
class ItemCommentModerator(SpamModerator):
    email_notification = True
    removal_suggestion_notification = True
    def moderate(self, comment, content_object, request):
        # Make a dictionary where the keys are the words of the message and
        # the values are their relative position in the message.
        def clean(word):
            ret = word
            if word.startswith('.') or word.startswith(','):
                ret = word[1:]
            if word.endswith('.') or word.endswith(','):
                ret = word[:-1]
            return ret

        lowcase_comment = comment.comment.lower()
        msg = dict([(clean(w), i)
                    for i, w in enumerate(lowcase_comment.split())])
        for badword in badwords:
            if isinstance(badword, str):
                if lowcase_comment.find(badword) > -1:
                    return True
            else:
                lastindex = -1
                for subword in badword:
                    if subword in msg:
                        if lastindex > -1:
                            if msg[subword] == (lastindex + 1):
                                lastindex = msg[subword]
                        else:
                            lastindex = msg[subword]
                    else:
                        break
                if msg.get(badword[-1]) and msg[badword[-1]] == lastindex:
                    return True
        return super(ItemCommentModerator, self).moderate(comment,
                                                          content_object,
                                                          request)

moderator.register(Item, ItemCommentModerator)