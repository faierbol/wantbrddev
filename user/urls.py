from django.conf.urls import url
from django.urls import path, reverse_lazy
from django.contrib.auth import views as auth_views
from . import views

app_name = 'u'
urlpatterns = [	
	url(r'^$', views.home, name='home'),
	path('<username>/', views.profile, name='profile'),
	path('<username>/following/', views.profile_following, name='profile_following'),
	path('<username>/followers/', views.profile_followers, name='profile_followers'),
]

handler404 = 'board.views.error_404'
handler500 = 'board.views.error_500'