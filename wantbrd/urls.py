from django.conf.urls import url, include
from django.conf import settings
from django.contrib import admin
from django.conf.urls.static import static
from django.urls import path
from django.contrib.auth import views as auth_views
from django.views.i18n import JavaScriptCatalog
from board import views as board_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('u/', include('user.urls')),
    path('b/', include('board.urls')),
    path('search/item/', board_views.search_item, name='search_item'),
    path('search/user/', board_views.search_user, name='search_user'),
    path('search/board/', board_views.search_board, name='search_board'),
    path('comments/', include('fluent_comments.urls')),
    url(r'^login/$', auth_views.login, name='login'),
    url(r'^logout/$', auth_views.logout, name='logout'),    
]
if settings.DEBUG:
	urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)