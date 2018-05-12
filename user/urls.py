from django.conf.urls import url
from django.urls import path, reverse_lazy
from django.contrib.auth import views as auth_views
from . import views

app_name = 'u'
urlpatterns = [	
	url(r'^$', views.home, name='home'),
	url(r'^signup/$', views.signup, name='signup'),
	url(r'^login/$',  auth_views.LoginView.as_view(template_name='user/login.html'), name='login'),
	path('<username>/', views.profile, name='profile'),
	path('my_account/', views.my_account, name='myaccount'),
	path('update_account/', views.update_account, name='update_account'),
	url(r'^logout/$', auth_views.LogoutView.as_view(), name='logout'),	
	url(r'^reset/$',
	    auth_views.PasswordResetView.as_view(
	        template_name='user/password_reset.html',
	        email_template_name='user/password_reset_email.html',
	        subject_template_name='user/password_reset_subject.txt',
	        success_url=reverse_lazy('u:password_reset_done'),
	    ),
	    name='password_reset'),
	path(
		'reset/done/',
	    auth_views.PasswordResetDoneView.as_view(template_name='user/password_reset_done.html'),
	    name='password_reset_done'),
	url(r'^reset/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$',
	    auth_views.PasswordResetConfirmView.as_view(
	    	template_name='user/password_reset_confirm.html',
	    	success_url=reverse_lazy('u:password_reset_complete'),
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
			success_url=reverse_lazy('u:password_change_done'),
		),
	    name='password_change'),
	url(r'^settings/password/done/$', auth_views.PasswordChangeDoneView.as_view(template_name='user/password_change_done.html'),
	    name='password_change_done'),	
]