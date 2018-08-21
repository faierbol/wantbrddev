from django.contrib import admin
from .models import Board, Item, BoardLike, ItemLike, BoardView, ItemView, ItemConnection, BoardPrivacy

class BoardAdmin(admin.ModelAdmin):
	prepopulated_fields = {
		'slug':(
			'board_name',
		)
	}
	readonly_fields=('id',)
	list_display = ('id', 'board_name', 'user')
admin.site.register(Board, BoardAdmin)

class ItemAdmin(admin.ModelAdmin):
	list_display = ('id','item_name')
admin.site.register(Item, ItemAdmin)

class ItemConxAdmin(admin.ModelAdmin):
	readonly_fields=('id',)
	list_display = ('id', 'board', 'item_id')
admin.site.register(ItemConnection, ItemConxAdmin)

admin.site.register(BoardLike)

admin.site.register(ItemLike)

admin.site.register(BoardView)

admin.site.register(ItemView)

admin.site.register(BoardPrivacy)