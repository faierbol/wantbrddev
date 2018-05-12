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
    path('', board_views.home, name='home'),
    path('u/', include('user.urls')),
    path('b/', include('board.urls')),
    path('search/', board_views.search, name='search'),
    path(r'comments/', include('django_comments_xtd.urls')),
    # url(r'^login/$', auth_views.login, name='login'),
    # url(r'^logout/$', auth_views.logout, name='logout'),    
    path(r'jsi18n/', JavaScriptCatalog.as_view(), name='javascript-catalog'),
]
if settings.DEBUG:
	urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)