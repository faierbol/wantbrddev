from django.conf.urls import url
from django.urls import path, reverse_lazy
from . import views

app_name = 'b'
urlpatterns = [	
	path('', views.view_boards, name='view_boards'),
	path('<username>/<board_name>', views.view_board, name='view_board'),
	path('<board_id>/<item_id>', views.view_item, name='view_item'),
	path('my_boards/', views.my_boards, name='my_boards'),
	path('my_boards/add/', views.add_board, name='add_board'),
	path('my_boards/edit/<board_id>', views.edit_board, name='edit_board'),
	path('my_boards/edit/<board_id>/add_item', views.add_item, name='add_item'),
	path('my_boards/edit/<board_id>/<item_id>', views.edit_item, name='edit_item'),
	path('discovery/', views.discovery, name='discovery'),	
]