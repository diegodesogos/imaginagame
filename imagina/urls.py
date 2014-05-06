from django.conf.urls import patterns, url

urlpatterns = patterns('imagina.views',
    url('^$', 'index', name="index"),
    url('^game/(?P<game_board_id>[-\w\d]+)/detail$', 'game_detail',name='game_detail'),
    url('^play/(?P<player_state_id>[-\w\d]+)/board$', 'playerstate_detail',name='playerstate_detail'),
    url('^play/(?P<player_state_id>[-\w\d]+)/startnewround$', 'start_new_round',name='start_new_round'),
    url('^play/(?P<player_state_id>[-\w\d]+)/choosecard$', 'choose_card',name='choose_card'),
    url('^play/(?P<player_state_id>[-\w\d]+)/votecard$', 'vote_card',name='vote_card'),
    url('^play/(?P<player_state_id>[-\w\d]+)/roundfinished$', 'round_finished',name='round_finished'),
    url('^player/(?P<player_id>[-\w\d]+)/detail$', 'player_detail',name='player_detail'),
    ('startnewgame', 'start_new_game'),
    ('^game/(?P<game_board_id>[-\w\d]+)/join$', 'join_game'),
    ('debug_re_create_deck_default', 'debug_re_create_deck_default'),
    ('debug_reset_game_and_plays_datamodel', 'debug_reset_game_and_plays_datamodel'),
    ('re_create_deck_default', 'debug_re_create_deck_default'),
)

