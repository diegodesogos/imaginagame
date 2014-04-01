# Create your views here.
from django.shortcuts import render_to_response, get_object_or_404, redirect,\
    render
from django.http import HttpResponse
from django.views.decorators.http import require_http_methods, require_GET, require_POST, require_safe
import uuid
from core.models import Game, GameState, Deck, Player, PlayerGameState

import core.const
import logging
logger =  core.const.configureLogger('views')

from core.forms import NewGameForm, JoinGameForm
from django.template.context import RequestContext
from django.forms.widgets import HiddenInput
from django.core.context_processors import csrf
from django.views.decorators.csrf import ensure_csrf_cookie

'''
The view functions to be fired for a given playerstate, all functions expect a request and a playerstate parameter

All view functions are expected to return a HttpResponse
'''
def player_board_when_game_finished(request, playerstate):
    return render_to_response('core/waitotherplayers.html', {'playerstate': playerstate})

def player_board_when_game_voting(request, playerstate):
    return render_to_response('core/waitotherplayers.html', {'playerstate': playerstate})

def player_board_when_game_waiting_new_players(request, playerstate):
    return render_to_response('core/waitotherplayers.html', {'playerstate': playerstate})

def player_board_when_game_choosing_cards(request, playerstate):
    return render_to_response('core/waitotherplayers.html', {'playerstate': playerstate})

def player_board_when_game_waiting_for_storyteller_new_round(request, playerstate):
    return render_to_response('core/waitotherplayers.html', {'playerstate': playerstate})

player_board_views = {GameState.FINISHED : player_board_when_game_finished,
                GameState.VOTING : player_board_when_game_voting,
                GameState.WAITING_NEW_PLAYERS : player_board_when_game_waiting_new_players,
                GameState.WAITING_PLAYERS_CHOSEN_CARDS : player_board_when_game_choosing_cards,
                GameState.WAITING_STORYTELLER_NEW_ROUND : player_board_when_game_waiting_for_storyteller_new_round
                }



def games_waiting_players():
    return Game.objects.filter(current_state = GameState.WAITING_NEW_PLAYERS).order_by('-creation_date')[:5]

@ensure_csrf_cookie
def index(request):
    latest_game_list = games_waiting_players()
    return render_to_response('core/index.html', {'latest_game_list': latest_game_list, 'debugging' : core.const.LOG_LEVEL == logging.DEBUG}, context_instance=RequestContext(request))

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
            playerstate = game.create_playerstate(player)
            return redirect('playerstate_detail', player_state_id=playerstate.player_state_id)
    return redirect('game_detail', game_board_id=game_board_id)


@ensure_csrf_cookie
@require_GET
def playerstate_detail(request, player_state_id):
    playerstate = get_object_or_404(PlayerGameState, player_state_id=player_state_id)
    return player_board_views[playerstate.game.current_state](request, playerstate)

@ensure_csrf_cookie
@require_GET
def player_detail(request, player_id):
    player = get_object_or_404(Player, id=player_id)
    return render_to_response('core/playerdetail.html', {'player': player}, context_instance=RequestContext(request))

@require_POST
def debug_re_create_deck_default(request):
    if core.const.LOG_LEVEL == logging.DEBUG:
        logger.debug('---- Re-creating default deck')
        decks = Deck.objects.filter(name='Default')
        existsDeckDefault = decks.count() > 0
        if not existsDeckDefault:
            deck = Deck.objects.create(name='Default')
        else:
            deck = decks[0]
            
        for idx in range(0, 48):
            url = '//static/decks/default/card24' +`idx` + '.png'
            existsCard = deck.cards.filter(url=url).count() > 0
            if not existsCard:
                deck.create_card(url=url, name='deck_default_card '+`idx`)
    return redirect('index')
    
 

