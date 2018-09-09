from django.conf.urls import url, include
from django.conf import settings
from django.contrib import admin
from django.conf.urls.static import static
from django.urls import path
from django.contrib.auth import views as auth_views
from django.views.i18n import JavaScriptCatalog
from board import views as board_views
from user import views as user_views
from django.urls import path, reverse_lazy

urlpatterns = [
    path('u/', include('user.urls')),
    path('b/', include('board.urls')),
    path('admin/', admin.site.urls),
    path('', board_views.home, name='home'),
    path('terms/', user_views.terms, name="terms"),
    path('influencers/', user_views.influencers, name="influencers"),
    path('checkstatus/', user_views.check_status, name='check_status'),
    path('initial/', user_views.initial, name='initial'),
    path('trending/items', board_views.trending_items, name='trending_items'),
    path('trending/users', board_views.trending_users, name='trending_users'),
    path('trending/boards', board_views.trending_boards, name='trending_boards'),
    path('collection/<collection_slug>', board_views.collection, name='collection'),
    path('search/', board_views.search, name='search'),
    path('search/item/', board_views.search_item, name='search_item'),
    path('search/user/', board_views.search_user, name='search_user'),
    path('search/board/', board_views.search_board, name='search_board'),
    path('comments/', include('fluent_comments.urls')),
    path('home/', user_views.my_home, name='my_home'),    
    path('my/profile/', user_views.update_profile, name='update_profile'),
    path('my/settings/', user_views.privacy_settings, name='privacy_settings'),
    path('my/notifications', user_views.my_notifications, name='my_notifications'),
    path('follow_tag/', user_views.follow_tag, name='follow_tag'),
    path('unfollow_tag/', user_views.unfollow_tag, name='unfollow_tag'),
    path('tags_followed/', user_views.tags_followed, name='tags_followed'),
    path('unfollowtag/', user_views.unfollowtag, name='unfollowtag'),
    # SIGN UP / SIGN IN
    path('signup/', user_views.signup, name='signup'),   
    url(r'^login/$',  auth_views.LoginView.as_view(template_name='user/login.html'), name='login'),
    url(r'^logout/$', auth_views.LogoutView.as_view(), name='logout'),  
    url(r'^reset/$',
        auth_views.PasswordResetView.as_view(
            template_name='user/password_reset.html',
            email_template_name='user/password_reset_email.html',
            subject_template_name='user/password_reset_subject.txt',
            success_url=reverse_lazy('password_reset_done'),
        ),
        name='password_reset'),
    path(
        'reset/done/',
        auth_views.PasswordResetDoneView.as_view(template_name='user/password_reset_done.html'),
        name='password_reset_done'),
    url(r'^reset/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$',
        auth_views.PasswordResetConfirmView.as_view(
            template_name='user/password_reset_confirm.html',
            success_url=reverse_lazy('password_reset_complete'),
        ),
        name='password_reset_confirm'),
    url(r'^reset/complete/$',
        auth_views.PasswordResetCompleteView.as_view(
            template_name='user/password_reset_complete.html'),
            name='password_reset_complete'),
    path(
        'settings/password/',
        auth_views.PasswordChangeView.as_view(
            template_name='user/password_change.html',
            success_url=reverse_lazy('password_change_done'),
        ),
        name='password_change'),
    url(r'^settings/password/done/$', auth_views.PasswordChangeDoneView.as_view(template_name='user/password_change_done.html'),
        name='password_change_done'),
]

handler404 = 'board.views.error_404'
handler500 = 'board.views.error_500'

if settings.DEBUG:
	urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)