from django.db import models
from django.contrib.auth.models import User
from board.models import Board
from django.db.models.signals import post_save
from django.dispatch import receiver
from phonenumber_field.modelfields import PhoneNumberField

def user_directory_path(instance, filename):
    return 'user_files/{0}/picture/{1}'.format(instance.user.id, filename)

# Profile model
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    bio = models.TextField(default='', max_length=500, blank=True)
    country = models.CharField(default='', max_length=30, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    phone_number = PhoneNumberField(default='', null=True, blank=True)
    website = models.URLField(default='', blank=True)
    picture = models.ImageField(upload_to=user_directory_path, blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True)
    alert_new_subscribe = models.BooleanField(default=True)
    alert_new_item = models.BooleanField(default=True)
    alert_suggested_boards = models.BooleanField(default=True)

    def __str__(self):
        return self.user.username

    def get_connections(self):
        connections = Connection.objects.filter(creator=self.user)
        return connections

    def get_followers(self):
        followers = Connection.objects.filter(following = self.user)
        return followers


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