from django.conf.urls import patterns

urlpatterns = patterns('core.views',
    ('^$', 'index'),
    ('^(?P<game_id>\d+)/$', 'detail'),
    ('^(?P<game_id>\d+)/results/$', 'results'),
    ('^(?P<game_id>\d+)/vote/$', 'vote'),
)

