from core.models import Player, Card, Game, PlayerGameState, PlayerPlay, GameRound, Deck
from django.contrib import admin

admin.site.register(Player)
admin.site.register(Card)
admin.site.register(PlayerPlay)
admin.site.register(GameRound)
admin.site.register(PlayerGameState)
admin.site.register(Game)   
admin.site.register(Deck)   
#class PlayerStateInline(admin.StackedInline):
'''
class PlayerGameStateInline(admin.TabularInline):
    model = PlayerGameState
    extra = 3


class GameAdmin(admin.ModelAdmin):
    fieldsets = [
        (None,               {'fields': ['board_id', 'current_state']}),
        ('Date information', {'fields': ['creation_date'], 'classes': ['collapse']}),
    ]
    inlines = [PlayerGameStateInline]
    list_display = ('board_id', 'creation_date', 'current_state')
    
admin.site.register(Game, GameAdmin)    
'''