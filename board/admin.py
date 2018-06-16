from django.contrib import admin
from .models import Board, Item, BoardLike, ItemLike, BoardView, ItemView, ItemConnection, BoardPrivacy

class BoardAdmin(admin.ModelAdmin):
	prepopulated_fields = {
		'slug':(
			'board_name',
		)
	}
	readonly_fields=('id',)
admin.site.register(Board, BoardAdmin)

# class ItemAdmin(admin.ModelAdmin):
# 	readonly_fields = ('created',)
admin.site.register(Item)

class ItemConxAdmin(admin.ModelAdmin):
	readonly_fields=('id',)
admin.site.register(ItemConnection, ItemConxAdmin)

admin.site.register(BoardLike)

admin.site.register(ItemLike)

admin.site.register(BoardView)

admin.site.register(ItemView)

admin.site.register(BoardPrivacy)