from django.conf.urls import patterns, url

urlpatterns = patterns('core.views',
    ('^$', 'index'),
    url('^game/(?P<game_board_id>[-\w\d]+)/detail$', 'game_detail',name='game_detail'),
    ('startnewgame', 'start_new_game'),
    ('^game/(?P<game_board_id>[-\w\d]+)/join$', 'join_game'),
)

