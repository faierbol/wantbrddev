from django.conf.urls import url
from django.urls import path, reverse_lazy
from . import views

app_name = 'b'
urlpatterns = [	
	path('<username>/<board_name>', views.view_board, name='view_board'),
	path('<username>/<board_name>/view/<itemconx_id>', views.view_item, name='view_item'),
	path('my_boards/add/', views.add_board, name='add_board'),
	path('my_boards/edit/<board_id>', views.edit_board, name='edit_board'),
	path('my_boards/edit/<board_id>/add_item', views.add_item, name='add_item'),
	path('my_boards/edit/<board_id>/<item_id>', views.edit_item, name='edit_item'),
	path('like_board/<board_id>/', views.like_board, name='like_board'),
	path('unlike_board/<board_id>', views.unlike_board, name='unlike_board'),
]