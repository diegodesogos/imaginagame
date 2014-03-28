from django.conf.urls import patterns

urlpatterns = patterns('core.views',
    ('^$', 'index'),
    ('^game/(?P<game_board_id>[-\w\d]+)/detail$', 'game_detail'),
    ('startnewgame', 'start_new_game'),
)

