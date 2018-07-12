def include_login_form(request):
	from django.contrib.auth.forms import AuthenticationForm
	form = AuthenticationForm()
	return {'login_form': form}


def unread_notifications(request):
	from user.models import Notification
	import datetime
	user = request.user
	unread_followers = False
	unread_likes = False
	now = datetime.datetime.now()
	ago = now - datetime.timedelta(days=1)
	try:
		unread_itemlikes = Notification.objects.filter(user=user, notification_type='likeitem', seen=False).count()
		unread_boardlikes = Notification.objects.filter(user=user, notification_type='likeboard', seen=False).count()
		unread_followers = Notification.objects.filter(user=user, notification_type='newfollow', seen=False).count()
		unread_likes = unread_itemlikes + unread_boardlikes
	except:
		pass

	return {
		'unread_followers':unread_followers,
		'unread_likes':unread_likes,
	}