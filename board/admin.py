from django.contrib import admin
from .models import Board, Item, BoardLike, ItemLike, BoardView

class BoardAdmin(admin.ModelAdmin):
	prepopulated_fields = {
		'slug':(
			'board_name',
		)
	}
admin.site.register(Board, BoardAdmin)

class ItemAdmin(admin.ModelAdmin):
	readonly_fields = ('created',)
admin.site.register(Item, ItemAdmin)

admin.site.register(BoardLike)

admin.site.register(ItemLike)

admin.site.register(BoardView)