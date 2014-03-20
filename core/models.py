from django.db import models
from datetime import datetime
from djangotoolbox.fields import ListField

class GameState():
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
    name = models.CharField(max_length=200)
    def __unicode__(self):
        return 'Player ' + self.name

class Card(models.Model):
    url = models.CharField(max_length=400)
    description = models.CharField(max_length=200)
    def __unicode__(self):
        return 'Card url: ' + self.url + ' Description: ' +self.description

class PlayerGameState(models.Model):
    game = models.ForeignKey('Game', related_name='playergamestates')
    order = models.IntegerField(default=0)
    player = models.ForeignKey(Player)
    player_state_id = models.CharField(max_length=400)
    points = models.IntegerField(default=0)
    cards = ListField(models.ForeignKey(Card))
    def __unicode__(self):
        return 'PlayerGameState: player ' + self.player.name + ' Points: ' + str(self.points) + ' Cards: ' + ', '.join(str(x) for x in self.cards)
 
class Game(models.Model):
    board_id = models.CharField(max_length=400)
    creation_date = models.DateTimeField(default=datetime.now, blank=True)
    current_state = models.CharField(max_length=40,
                                      choices=GameState.CURRENT_GAME_STATE_CHOICES,
                                      default=GameState.WAITING_PLAYING_CARD_AND_CONCEPT)
    def current_storyteller_playergamestate(self):
        '@rtype PlayerGameState'
        rounds = self.rounds.order_by('order')
        if not rounds:
            #get first PlayerGameState from player game states
            return self.playergamestates.order_by('order')[0]
        else:
            #get the storyteller from the last round played
            last_round = rounds.reverse()[0]
            last_round_player = last_round.storyteller_player
            return self.playergamestates.get(player=last_round_player)
    def next_storyteller_playergamestate(self):
        '@rtype PlayerGameState'
        current_storyteller_order = self.current_storyteller_playergamestate().order
        next_storyteller_order = (current_storyteller_order + 1) % self.playergamestates.count()
        return self.playergamestates.get(order=next_storyteller_order)
            
    def __unicode__(self):
        return 'Game: unique id ' + self.board_id + \
                ' Game state: ' + self.current_state
    
class PlayerPlay(models.Model):
    game_round = models.ForeignKey('GameRound', related_name='plays')
    owner_player = models.ForeignKey(Player, related_name='plays')
    selected_card = models.ForeignKey(Card, related_name='+')
    unchosen_cards = ListField(models.ForeignKey(Card))
    voted_by_players = ListField(models.ForeignKey(PlayerGameState))
    storyteller = models.BooleanField(default=False)   
    def __unicode__(self):
        return 'PlayerPlay: owner ' + self.owner_player.name + \
                ' Storyteller: ' + self.storyteller.str() + \
                ' Selected card ' + self.selected_card.url + \
                ' Unchosen cards: ' + self.unchosen_cards.str()
    
class GameRound(models.Model):
    game = models.ForeignKey(Game, related_name='rounds')
    order = models.IntegerField(default=0)
    opened = models.BooleanField(default=True)   
    storyteller_player = models.ForeignKey(Player, related_name='+')
    storyteller_selected_card = models.ForeignKey(Card, related_name='+')
    storyteller_sentence_for_selected_card = models.CharField(max_length=1000)
    def __unicode__(self):
        return 'GameRound: game ' + self.game.board_id + \
                ' Storyteller ' + self.storyteller_player.name + \
                ' Storyteller selected card: ' + self.storyteller_selected_card.url + \
                ' Storyteller sentence: ' + self.storyteller_sentence_for_selected_card 
    
    