from django.contrib import admin
from .models import Profile, Connection, BlockedUsers, AuthorisedUsers, Notification

admin.site.register(Profile)

class ConnectionAdmin(admin.ModelAdmin):
	list_display = ('creator','following')
admin.site.register(Connection, ConnectionAdmin)

admin.site.register(BlockedUsers)
admin.site.register(AuthorisedUsers)
class NotificationAdmin(admin.ModelAdmin):
	readonly_fields = ('created',)
admin.site.register(Notification, NotificationAdmin)