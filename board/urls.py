from django.conf.urls import url
from django.urls import path, reverse_lazy
from . import views

app_name = 'b'
urlpatterns = [	
	path('<username>/<board_name>', views.view_board, name='view_board'),
	path('<username>/<board_name>/<item_id>/<item_slug>', views.view_item, name='view_item'),
	path('my_boards/edit/<board_id>', views.edit_board, name='edit_board'),
	path('my_boards/edit/<board_id>/add_item', views.add_item, name='add_item'),
	path('my_boards/edit/<board_id>/<itemconx_id>', views.edit_item, name='edit_item'),
	path('like_board/', views.like_board, name='like_board'),
	path('unlike_board/', views.unlike_board, name='unlike_board'),		
	path('like_item/', views.like_item, name='like_item'),
	path('unlike_item/', views.unlike_item, name='unlike_item'),
	path('save_item/', views.save_item, name='save_item'),
	path('follow/', views.follow_user, name='follow_user'),
	path('unfollow/', views.unfollow_user, name='unfollow_user'),	
	path('my_boards/edit/<board_id>/add_item/<itemconx_id>', views.add_existing_item, name='add_existing_item'),
]