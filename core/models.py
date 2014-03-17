from django.db import models

"""game states"""
WAITING_PLAYING_CARD_AND_CONCEPT = 'WAITING_PLAYING_CARD_AND_CONCEPT'
WAITING_PLAYERS_CHOSEN_CARDS = 'WAITING_PLAYERS_CHOSEN_CARDS'
VOTING = 'VOTING'
COMPUTING_ROUND_SCORES = 'COMPUTING_ROUND_SCORES'
FINISHED = 'FINISHED'
CURRENT_GAME_STATE_CHOICES = (
    (WAITING_PLAYING_CARD_AND_CONCEPT, 'WAITING_PLAYING_CARD_AND_CONCEPT'),
    (WAITING_PLAYERS_CHOSEN_CARDS, 'WAITING_PLAYERS_CHOSEN_CARDS'),
    (VOTING, 'VOTING'),
    (COMPUTING_ROUND_SCORES, 'COMPUTING_ROUND_SCORES'),
    (FINISHED, 'FINISHED'),
)

class Player(models.Model):
    id = models.IntegerField()
    name = models.CharField(max_length=200)

class Card(models.Model):
    id = models.IntegerField()
    url = models.CharField(max_length=400)
    description = models.CharField(max_length=200)

class PlayerGameState(models.Model):
    player = models.ForeignKey(Player)
    player_state_url = models.CharField(max_length=400)
    points = models.IntegerField()
    cards = models.ManyToManyField(Card)
 
class Game(models.Model):
    id = models.IntegerField()
    board_url = models.CharField(max_length=400)
    player_states = models.ManyToManyField(PlayerGameState)
    turn = models.IntegerField()
    rounds = models.ManyToManyField('GameRound')
    current_state = models.CharField(max_length=40,
                                      choices=CURRENT_GAME_STATE_CHOICES,
                                      default=WAITING_PLAYING_CARD_AND_CONCEPT)
    
class PlayerPlay(models.Model):
    player = models.ForeignKey(Player)
    selected_card = models.ForeignKey(Card)
    unchosen_cards = models.ManyToManyField(Card) 
    voted_by_players = models.ManyToManyField(Player)    
    
class GameRound(models.Model):
    game = models.ForeignKey(Game)
    presenter_player = models.ForeignKey(Player)
    presenter_selected_card = models.ForeignKey(Card)
    presenter_concept_for_selected_card = models.CharField()
    plays = models.ManyToManyField(PlayerPlay)
    
    
    