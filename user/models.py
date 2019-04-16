import datetime
from django.db import models
from django.core.mail import send_mail
from django.contrib.auth.models import User
from board.models import Board, BoardView, ItemView, ItemConnection
from django.db.models.signals import post_save
from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver
from phonenumber_field.modelfields import PhoneNumberField
from django_countries.fields import CountryField


def user_directory_path(instance, filename):
    return 'user_files/{0}/picture/{1}'.format(instance.user.id, filename)

# Profile model
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    bio = models.TextField(default='', max_length=500, blank=True)
    country = CountryField(default='', max_length=30, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    phone_number = PhoneNumberField(default='', null=True, blank=True)
    website = models.URLField(default='', blank=True)
    picture = models.ImageField(upload_to=user_directory_path, blank=True, null=True)
    background = models.ImageField(upload_to=user_directory_path, blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True)
    alert_new_subscribe = models.BooleanField(default=True)
    alert_new_item = models.BooleanField(default=True)
    alert_suggested_boards = models.BooleanField(default=True)
    ALL = 'ALL'
    NONE = 'NONE'
    HIDE = 'HIDE'
    SHOW = 'SHOW'
    GLOBAL_PRIVACY_CHOICES = (
        (ALL, 'Make all my boards visible to all users by default'),
        (NONE, 'Make all my boards invisible to all users by default'),
        (HIDE, 'Make all my boards invisible to everyone except the following users...'),
        (SHOW, 'Make all my boards visible to everyone except the following users...'),
    )
    global_privacy = models.CharField(
        max_length=4,
        choices=GLOBAL_PRIVACY_CHOICES,
        default=ALL,
    )

    PERSONAL = 'PERSONAL'
    PRO = 'PRO'
    BUSINESS = 'BUSINESS'
    USER_TYPE_CHOICES = (
        (PERSONAL, 'Personal'),
        (PRO, 'Pro'),
        (BUSINESS, 'Business'),
    )
    user_type = models.CharField(
        max_length=8,
        choices=USER_TYPE_CHOICES,
        default=PERSONAL,
    )

    pro_type = models.CharField(default='', max_length=20, blank=True)    

    social_instagram = models.CharField(default='', max_length=500, blank=True)
    social_twitter = models.CharField(default='', max_length=500, blank=True)
    social_youtube = models.CharField(default='', max_length=500, blank=True)
    social_facebook = models.CharField(default='', max_length=500, blank=True)
    social_twitch = models.CharField(default='', max_length=500, blank=True)
    social_pinterest = models.CharField(default='', max_length=500, blank=True)
    social_vimeo = models.CharField(default='', max_length=500, blank=True)
    social_weibo = models.CharField(default='', max_length=500, blank=True)
    social_vk = models.CharField(default='', max_length=500, blank=True)
    login_count = models.IntegerField(default=0)
    saved_count = models.IntegerField(default=0)
    isaved_count = models.IntegerField(default=0)


    def __str__(self):
        return self.user.username

    # get all the people this user follows
    def get_connections(self):
        connections = Connection.objects.filter(creator=self.user)
        return connections

    # get all the peolpe that are following this user
    def get_followers(self):
        followers = Connection.objects.filter(following = self.user)
        return followers

    # check if any given user is following this user
    def check_is_following(self, tocheck):
        is_following = False
        followers = Connection.objects.filter(following = self.user)
        for follower in followers:
            if follower.creator == tocheck:
                is_following = True
                break
        return is_following

    # get number of items for given user
    def get_user_item_count(self):
        # setup, then get all users boards and loop
        item_count = 0
        boards = Board.objects.filter(user=self.user)
        for board in boards:
            # get all the items for this board
            boarditems = ItemConnection.objects.filter(board=board).count()
            item_count+=boarditems
        return item_count

    # get number of view of given user
    def get_user_views(self):
        # setup, then get all the users boards and loop
        item_views = 0
        board_views = 0
        views_count = 10
        boards = Board.objects.filter(user=self.user)
        for board in boards:
            # get the board views
            board_views += BoardView.objects.filter(board=board).count()
            # get the board items and loop
            boarditems = ItemConnection.objects.filter(board=board)         
            for item in boarditems:
                # get the views for each item and sum up
                item_views += ItemView.objects.filter(item_conx=item).count()
            # once finished looping items, add item views to board views
            views_count = board_views + item_views
        # send total board and item views        
        return views_count

    # get all tags for user
    def get_user_tags(self):
        the_tags = []
        all_boards = Board.objects.filter(user=self.user)
        for board in all_boards:
            board_tags = board.tags.all()
            for tag in board_tags:
                if tag not in the_tags:
                    the_tags.append(tag)
        return the_tags


    
    def get_suggested_boards(self, qty):    
        user_tags = []
        our_user = User.objects.get(pk=self.user.id)
        user_boards = Board.objects.filter(user=our_user)          
        suggested_boards = []    
        c = 0    
        q = qty
        # cycle all boards owned by the current user
        for board in user_boards:
            board.thetags = board.tags.all()
            # verify we have not reached max qty of results yet    
            if c < q:
                # find similar board
                similar_boards = board.tags.similar_objects()
                for board in similar_boards:
                    if isinstance(board, Board):
                        if c < q:
                            if (board.slug != 'Your Saved Items' and board not in suggested_boards and
                                board.user != our_user and board.user_blocked(our_user) == False and
                                board.get_item_count() > 0):
                                board.totalitems = board.get_item_count()
                                board.views = BoardView.objects.filter(board=board).count()
                                board.items = []

                                # get all items for this board
                                boarditems = ItemConnection.objects.filter(board=board)
                                board.itemcount = boarditems.count()
                                x=0
                                for item in boarditems:
                                    if x < 2:
                                        board.items.append(item)
                                        x+=1
                                    else:
                                        break

                                suggested_boards.append(board)
                                c+=1
                        else:
                            break
                    else:
                        pass    
            else:
                break

        return suggested_boards

    # get the users saved board
    def get_saved_board(self):
        saved_board = Board.objects.get(user=self.user, slug="your-saved-items")
        return saved_board.id

    def make_connection(self, request):        
        if Connection.objects.filter(creator=request.user, following=self.user).exists():
            return False
        else:
            send_mail('You did it!', 'My god, it worked', 'noreply@wantbrd.com', ['iamholdsworth@gmail.com'])
            Notification.create_follow_notify(request.user, self.user)
            new_connection = Connection.objects.create(
                creator = request.user,
                following = self.user,
            )            
            return True

    def break_connection(self, request):        
        if Connection.objects.filter(creator=request.user, following=self.user).exists():
            connection = Connection.objects.filter(creator=request.user, following=self.user)
            connection.delete()
        else:
            return False


def login_user(sender, request, user, **kwargs):
    user.profile.login_count = user.profile.login_count + 1
    user.profile.save()

user_logged_in.connect(login_user)


# update or create user profile model when user model is created or updated
@receiver(post_save, sender=User)
def update_user_profile(sender, instance, created, **kwargs):
    
    if created:
        Profile.objects.create(user=instance)
        Board.objects.create(user=instance, board_name='Your Saved Items', private=True, deleteable=False)  
    try:
        instance.profile.save()
    except AttributeError:
        profile = Profile.objects.create(user=instance)
        profile.save()


class Connection(models.Model):
    created = models.DateTimeField(auto_now_add=True, editable=False)
    creator = models.ForeignKey(User, related_name="friendship_creator_set", on_delete=models.CASCADE)
    following = models.ForeignKey(User, related_name="friend_set", on_delete=models.CASCADE)


class BlockedUsers(models.Model):
    user = models.ForeignKey(User, related_name="block_creator_set" ,on_delete=models.CASCADE)
    blocked_user = models.CharField(default='', blank=True, max_length=255)


class AuthorisedUsers(models.Model):
    user = models.ForeignKey(User, related_name="auth_creator_set" ,on_delete=models.CASCADE)
    authorised_user = models.CharField(default='', blank=True, max_length=255)


class Notification(models.Model):
    created = models.DateTimeField(auto_now_add=True, editable=False)
    user = models.ForeignKey(User, related_name="user_notify_set" ,on_delete=models.CASCADE)
    notification_type = models.CharField(default='', max_length=500, blank=False)
    board_ref = models.IntegerField(blank=True, null=True)
    item_ref = models.IntegerField(blank=True, null=True)
    user_trigger = models.ForeignKey(User, related_name="user_trigger_set" ,on_delete=models.CASCADE)
    seen = models.BooleanField(default=False)

    def create_itemlike_notify(user_trigger, user_to_notify, item_ref):
        # set up so we only noify if there is no matching notification from the last 24 hours
        now = datetime.datetime.now()
        ago = now - datetime.timedelta(days=1)  
        try:
            Notification.objects.get(user_trigger=user_trigger, item_ref=item_ref, created__range=[ago, now])
        except:
            new_notification = Notification.objects.create(
                user = user_to_notify,
                notification_type = 'likeitem',
                item_ref = item_ref,
                user_trigger = user_trigger,
                seen = False,       
            )

    def create_boardlike_notify(user_trigger, user_to_notify, board_ref):
        # set up so we only noify if there is no matching notification from the last 24 hours
        now = datetime.datetime.now()
        ago = now - datetime.timedelta(days=1)  
        try:
            Notification.objects.get(user_trigger=user_trigger, board_ref=board_ref, created__range=[ago, now])
        except:
            new_notification = Notification.objects.create(
                user = user_to_notify,
                notification_type = 'likeboard',
                board_ref = board_ref,
                user_trigger = user_trigger,
                seen = False,       
            )

    def create_follow_notify(user_trigger, user_to_notify):
        # set up so we only noify if there is no matching notification from the last 24 hours
        now = datetime.datetime.now()
        ago = now - datetime.timedelta(days=1)  
        try:
            Notification.objects.get(user_trigger=user_trigger, notification_type='newfollow', created__range=[ago, now])
        except:
            new_notification = Notification.objects.create(
                user = user_to_notify,
                notification_type = 'newfollow',
                user_trigger = user_trigger,
                seen = False,       
            )

class TagFollows(models.Model):
    user = models.ForeignKey(User,on_delete=models.CASCADE)
    tag = models.CharField(default='', max_length=500, blank=False, null=False)