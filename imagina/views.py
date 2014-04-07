# Create your views here.
from django.shortcuts import render_to_response, get_object_or_404, redirect,\
    render
from django.http import HttpResponse
from django.views.decorators.http import require_http_methods, require_GET, require_POST, require_safe
import uuid
from imagina.models import Game, GameState, Deck, Player, PlayerGameState, Card

import imagina.const
import logging
logger =  imagina.const.configureLogger('views')

from imagina.forms import NewGameForm, JoinGameForm, NewRoundForm,\
    ChooseCardForm
from django.template.context import RequestContext
from django.forms.widgets import HiddenInput
from django.core.context_processors import csrf
from django.views.decorators.csrf import ensure_csrf_cookie

'''
The view functions to be fired for a given playerstate, all functions expect a request and a playerstate parameter

All view functions are expected to return a HttpResponse
'''
def player_board_when_game_finished(request, playerstate):
    return render_to_response('imagina/gameover.html', {'playerstate': playerstate,
                                                        'cards' : playerstate.get_cards()})

def player_board_when_game_voting(request, playerstate):
    game = playerstate.game
    current_round = game.current_round()
    if playerstate.storyteller:
            #story teller has to wait to other players vote their card
            return render_to_response('imagina/storytellerwaitvotes.html', {'playerstate': playerstate, 
                                                                            'cards' : playerstate.get_cards(),
                                                                            'current_round' : current_round})    
    else:   
        play = game.get_current_play_for_playerstate(playerstate)
        playerplay_voted_by_playerstate = current_round.get_playerplay_voted_by_playerstate(playerstate)
        if playerplay_voted_by_playerstate:
            #player has already chosen a card and has already voted
            card_voted = playerplay_voted_by_playerstate.selected_card
            return render_to_response('imagina/alreadyvotedwait.html', {'playerstate': playerstate, 
                                                                        'cards' : playerstate.get_cards(),
                                                                        'play':play,
                                                                        'current_round' : current_round, 
                                                                        'card_voted': card_voted})
        else:
            #there is a round, waiting this player to vote
            candidate_cards = current_round.get_chosen_cards()
            vote_card_form = ChooseCardForm(player_cards=candidate_cards)
            return render_to_response('imagina/showcandidatecards.html', {'playerstate': playerstate, 
                                                                          'cards' : candidate_cards,
                                                                          'playerplay' : play, 
                                                                          'current_round' : current_round, 
                                                                          'vote_card_form': vote_card_form},
                                                                           context_instance=RequestContext(request))

def player_board_when_game_waiting_new_players(request, playerstate):
    return render_to_response('imagina/waitotherplayers.html', {'playerstate': playerstate,
                                                                'cards' : playerstate.get_cards(),})

def player_board_when_game_choosing_cards(request, playerstate):
    game = playerstate.game
    current_round = game.current_round
    if current_round:
        if playerstate.storyteller:
            #story teller has to wait to other players select their card
            return render_to_response('imagina/storytellerwaitselection.html', {'playerstate': playerstate, 
                                                                                'cards' : playerstate.get_cards(),
                                                                                'current_round' : current_round})    
        play = game.get_current_play_for_playerstate(playerstate)
        if play:
            #player has already chosen a card, wait for others to play
            return render_to_response('imagina/alreadyplayedwait.html', {'playerstate': playerstate, 
                                                                       'play':play,
                                                                       'cards' : playerstate.get_cards(),
                                                                       'current_round' : current_round,
                                                                       })
        else:
            #there is a round, waiting player to choose a card
            choose_card_form = ChooseCardForm(player_cards=playerstate.get_cards())
            return render_to_response('imagina/showplayercards.html', {'playerstate': playerstate, 
                                                                       'cards' : playerstate.get_cards(),
                                                                       'playerplay' : play, 
                                                                       'current_round' : current_round, 
                                                                       'choose_card_form': choose_card_form},
                                                                       context_instance=RequestContext(request))
    else:
        return render_to_response('imagina/waitingstorytellernewround.html', {'playerstate': playerstate,
                                                                    'cards' : playerstate.get_cards()})

def player_board_when_game_waiting_for_storyteller_new_round(request, playerstate):
    if playerstate.storyteller:
        new_round_form = NewRoundForm(request.POST, player_cards=playerstate.get_cards())
        return render_to_response('imagina/startnewround.html', 
                                  {'playerstate': playerstate, 'new_round_form': new_round_form}, 
                                  context_instance=RequestContext(request))
    else:   
        return render_to_response('imagina/waitingstorytellernewround.html', {'playerstate': playerstate,
                                                                    'cards' : playerstate.get_cards(),
                                                                    })

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
    return render_to_response('imagina/index.html', {'latest_game_list': latest_game_list}, context_instance=RequestContext(request))

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
        return render_to_response('imagina/startnewgame.html', {'new_game_form': new_game_form, }, context_instance=RequestContext(request))

@ensure_csrf_cookie
@require_GET
def game_detail(request, game_board_id):
    p = get_object_or_404(Game, board_id=game_board_id)
    join_game_form = JoinGameForm(initial={ 'board_id': game_board_id})
    if p.is_waiting_new_players():
        join_game_form.board_id = game_board_id
        join_game_form.fields['board_id'].widget = HiddenInput()
    return render_to_response('imagina/gamedetail.html', {'game': p, 'join_game_form' : join_game_form}, context_instance=RequestContext(request))

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
@require_POST
def start_new_round(request, player_state_id):
    storyteller = get_object_or_404(PlayerGameState, player_state_id=player_state_id)
    player_cards=storyteller.get_cards()
    form = NewRoundForm(request.POST, player_cards = player_cards)
    #HACK can't make work validation on NewRoundForm when changing the queryset, skip it
    #if form.is_valid():
    phrase = form.data['phrase']
    card_data = int(form.data['card'])
    card = Card.objects.get(id=card_data)
    game = storyteller.game
    game.new_round(storyteller, card, phrase)
    game.save()
    return redirect('playerstate_detail', player_state_id=storyteller.player_state_id)


@ensure_csrf_cookie
@require_POST
def choose_card(request, player_state_id):
    player = get_object_or_404(PlayerGameState, player_state_id=player_state_id)
    player_cards = player.get_cards()
    if player.storyteller:
        raise ValueError("The player is the story teller, it can't choose a card!")
    form = ChooseCardForm(request.POST, player_cards = player_cards)
    #HACK can't make work validation on NewRoundForm when changing the queryset, skip it
    #if form.is_valid():
    card_data = int(form.data['card'])
    card = Card.objects.get(id=card_data)
    game = player.game
    game.play_card_chosen(player, card)
    game.save()
    return redirect('playerstate_detail', player_state_id=player.player_state_id)

@ensure_csrf_cookie
@require_POST
def vote_card(request, player_state_id):
    player = get_object_or_404(PlayerGameState, player_state_id=player_state_id)
    player_cards = player.get_cards()
    if player.storyteller:
        raise ValueError("The player is the story teller, it can't choose a card!")
    form = ChooseCardForm(request.POST, player_cards = player_cards)
    #HACK can't make work validation on NewRoundForm when changing the queryset, skip it
    #if form.is_valid():
    card_data = int(form.data['card'])
    card = Card.objects.get(id=card_data)
    game = player.game
    game.vote_card(player, card)
    game.save()
    return redirect('playerstate_detail', player_state_id=player.player_state_id)

@ensure_csrf_cookie
@require_GET
def player_detail(request, player_id):
    player = get_object_or_404(Player, id=player_id)
    return render_to_response('imagina/playerdetail.html', {'player': player}, context_instance=RequestContext(request))

@require_POST
def debug_re_create_deck_default(request):
    if imagina.const.LOG_LEVEL == logging.DEBUG:
        logger.debug('---- Re-creating default deck')
        decks = Deck.objects.filter(name='Default')
        existsDeckDefault = decks.count() > 0
        if existsDeckDefault:
            deck = decks[0]
            deck.delete()
        deck = Deck.objects.create(name='Default')    
        for idx in range(0, 48):
            url = './static/decks/default/default_' +`idx+1` + '.png'
            existsCard = deck.cards.filter(url=url).count() > 0
            if not existsCard:
                deck.create_card(url=url, name='deck_default_card '+`idx+1`)
    return redirect('index')
    
 

