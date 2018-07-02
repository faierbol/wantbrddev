from django.db import models
from django.contrib.auth.models import User
from board.models import Board, BoardView, ItemConnection
from django.db.models.signals import post_save
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
    social_instagram = models.CharField(default='', max_length=500, blank=True)
    social_twitter = models.CharField(default='', max_length=500, blank=True)
    social_youtube = models.CharField(default='', max_length=500, blank=True)
    social_facebook = models.CharField(default='', max_length=500, blank=True)
    social_twitch = models.CharField(default='', max_length=500, blank=True)
    social_pinterest = models.CharField(default='', max_length=500, blank=True)
    social_vimeo = models.CharField(default='', max_length=500, blank=True)
    social_weibo = models.CharField(default='', max_length=500, blank=True)
    social_vk = models.CharField(default='', max_length=500, blank=True)


    def __str__(self):
        return self.user.username

    def get_connections(self):
        connections = Connection.objects.filter(creator=self.user)
        return connections

    def get_followers(self):
        followers = Connection.objects.filter(following = self.user)
        return followers

    def get_suggested_boards(self, qty, request):    
        user_tags = []
        user_obj = User.objects.get(pk=self.user.id)
        user_boards = Board.objects.filter(user=user_obj)

        ##### !!!!! NEED TO MAKE SURE BLOCKING BLOCKED USERS FROM BELOW !!!!! #####

        suggested_boards = []    
        c = 0    
        q = qty
        for board in user_boards:                        
            if c < q:
                similar_boards = board.tags.similar_objects()
                for board in similar_boards:                
                    if c < q:
                        if (board.slug != 'Your Saved Items' and board not in suggested_boards and
                            board.user != request.user and board.user_blocked(request.user) == False and
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
                break

        return suggested_boards

    def get_saved_board(self):
        saved_board = Board.objects.get(user=self.user, slug="your-saved-items")
        return saved_board.id


# update or create user profile model when user model is created or updated
@receiver(post_save, sender=User)
def update_user_profile(sender, instance, created, **kwargs):
    
    if created:
        Profile.objects.create(user=instance)
        Board.objects.create(user=instance, board_name='Your Saved Items', private=True, board_type='Wants', deleteable=False)  
    try:
        instance.profile.save()
    except AttributeError:
        profile = Profile.objects.create(user=instance)
        profile.save()



class Connection(models.Model):
    created = models.DateTimeField(auto_now_add=True, editable=False)
    creator = models.ForeignKey(User, related_name="friendship_creator_set", on_delete=models.CASCADE)
    following = models.ForeignKey(User, related_name="friend_set", on_delete=models.CASCADE)