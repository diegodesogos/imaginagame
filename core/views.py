# Create your views here.
from django.shortcuts import render_to_response, get_object_or_404, redirect,\
    render
from django.http import HttpResponse
from django.views.decorators.http import require_http_methods, require_GET, require_POST, require_safe
import uuid
from core.models import Game, GameState, Deck, Player

from core.forms import NewGameForm, JoinGameForm
from django.template.context import RequestContext
from django.forms.widgets import HiddenInput
from django.core.context_processors import csrf
from django.views.decorators.csrf import ensure_csrf_cookie


def games_waiting_players():
    return Game.objects.filter(current_state = GameState.WAITING_NEW_PLAYERS).order_by('-creation_date')[:5]

def index(request):
    latest_game_list = games_waiting_players()
    return render_to_response('core/index.html', {'latest_game_list': latest_game_list})

def get_or_create_player(player_name):
    players_with_name = Player.objects.filter(name=player_name)
    existsPlayer = players_with_name.count() > 0
    player = None
    if existsPlayer:
        player = players_with_name[0]
    else:
        player =  Player.objects.create(name=player_name)
    return player

'''
A player wants to start a new game, 
show new game options.
It must select a Deck and a Player
'''
@ensure_csrf_cookie
@require_http_methods(["GET", "POST"])
def start_new_game(request):
    if request.method == 'POST': # If the form has been submitted...
        form = NewGameForm(request.POST) # A form bound to the POST data
        if form.is_valid():
            deck = form.cleaned_data['deck']
            player_name = form.cleaned_data['player_name']
            min_players = form.cleaned_data['number_of_players']
            player = get_or_create_player(player_name)
            #deck = Deck.objects.get(id=deck_id)
            game = Game.objects.create(board_id=uuid.uuid4(), deck=deck, min_players=min_players)
            game.create_playerstate(player)
            game.save()
            return redirect('game_detail', game_board_id=game.board_id)
    else:
        new_game_form = NewGameForm()
        return render_to_response('core/startnewgame.html', {'new_game_form': new_game_form, }, context_instance=RequestContext(request))

@ensure_csrf_cookie
@require_GET
def game_detail(request, game_board_id):
    p = get_object_or_404(Game, board_id=game_board_id)
    join_game_form = JoinGameForm(initial={ 'board_id': game_board_id})
    if p.is_waiting_new_players():
        join_game_form.board_id = game_board_id
        join_game_form.fields['board_id'].widget = HiddenInput()
    return render_to_response('core/gamedetail.html', {'game': p, 'join_game_form' : join_game_form}, context_instance=RequestContext(request))

@ensure_csrf_cookie
@require_http_methods(["GET", "POST"])
def join_game(request, game_board_id):
    if request.method == 'POST':
        form = JoinGameForm(request.POST)
        if form.is_valid():
            board_id = form.cleaned_data['board_id']
            player_name = form.cleaned_data['player_name']
            game = get_object_or_404(Game, board_id=board_id)
            player = get_or_create_player(player_name)
            game.create_playerstate(player)
    return redirect('game_detail', game_board_id=game_board_id)

