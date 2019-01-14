from django.conf.urls import url
from django.urls import path, reverse_lazy
from . import views
from .views import UserAutocomplete

app_name = 'b'
urlpatterns = [	
	path('my_boards/edit/<board_id>', views.edit_board, name='edit_board'),
	path('my_boards/edit/<board_id>/add_item', views.add_item, name='add_item'),
	path('my_boards/edit/<board_id>/r/<itemadded>', views.edit_board, name='edit_board_added'),	
	path('my_boards/edit/<board_id>/add_item/<itemconx_id>', views.add_existing_item, name='add_existing_item'),
	path('my_boards/edit/<board_slug>/<itemconx_id>/<item_slug>', views.edit_item, name='edit_item'),		
	path('get_home_items/', views.get_home_items, name='get_home_items'),
	path('get_trending_boards/', views.get_trending_boards, name='get_trending_boards'),
	path('get_trending_items/', views.get_trending_items, name='get_trending_items'),
	path('get_trending_users/', views.get_trending_users, name='get_trending_users'),
	path('like_board/', views.like_board, name='like_board'),
	path('unlike_board/', views.unlike_board, name='unlike_board'),		
	path('like_item/', views.like_item, name='like_item'),
	path('unlike_item/', views.unlike_item, name='unlike_item'),
	path('save_item/', views.save_item, name='save_item'),
	path('follow/', views.follow_user, name='follow_user'),
	path('unfollow/', views.unfollow_user, name='unfollow_user'),	
	url(r'^user_autocomplete/$', UserAutocomplete.as_view(), name='user_autocomplete',),
	path('<username>/<board_name>', views.view_board, name='view_board'),
	path('<username>/<board_name>/<item_id>/<item_slug>', views.view_item, name='view_item'),
]