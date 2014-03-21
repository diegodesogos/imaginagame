from django.db import models
from datetime import datetime
from djangotoolbox.fields import ListField

class GameState():
    """game states"""
    WAITING_STORYTELLER_NEW_ROUND = 'WAITING_STORYTELLER_NEW_ROUND'
    WAITING_PLAYERS_CHOSEN_CARDS = 'WAITING_PLAYERS_CHOSEN_CARDS'
    VOTING = 'VOTING'
    FINISHED = 'FINISHED'
    CURRENT_GAME_STATE_CHOICES = (
        (WAITING_STORYTELLER_NEW_ROUND, 'WAITING_STORYTELLER_NEW_ROUND'),
        (WAITING_PLAYERS_CHOSEN_CARDS, 'WAITING_PLAYERS_CHOSEN_CARDS'),
        (VOTING, 'VOTING'),
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
    def has_card(self, card):
        return card.id in self.cards
    def get_card(self, idx):
        return Card.objects.get(id=self.cards[idx])
    def get_cards(self):
        #theCards = []
        return Card.objects.filter(id__in=self.cards)
        #for cardid in self.cards:
        #    theCards.append(self.get_card(cardid))
        #return theCards
    def remaining_cards(self, selected_card):
        theCards = []
        for card in self.get_cards():
            if card != selected_card:
                theCards.append(card)
        return theCards
    def add_card(self, card):
        self.cards.append(card.id)
        self.save()
    def remove_card(self, card):
        self.cards.remove(card.id)
        self.save()
 
class Game(models.Model):
    board_id = models.CharField(max_length=400)
    creation_date = models.DateTimeField(default=datetime.now, blank=True)
    current_state = models.CharField(max_length=40,
                                      choices=GameState.CURRENT_GAME_STATE_CHOICES,
                                      default=GameState.WAITING_STORYTELLER_NEW_ROUND)
                  
    def __unicode__(self):
        return 'Game: unique id ' + self.board_id + \
                ' Game state: ' + self.current_state    
                
    def players_count(self):
        return self.playergamestates.all().count()            
    
    def current_round(self):
        '@rtype GameRound'
        rounds = self.rounds.order_by('order')
        if not rounds:
            return None
        return rounds.reverse()[0]
    def current_storyteller_playergamestate(self):
        '@rtype PlayerGameState'
        last_round = self.current_round()
        if not last_round:
            #get first PlayerGameState from player game states
            return self.playergamestates.order_by('order')[0]
        else:
            #get the storyteller from the last round played
            return last_round.storyteller_player
    def next_storyteller_playergamestate(self):
        '@type PlayerGameState'
        current_storyteller_order = self.current_storyteller_playergamestate().order
        next_storyteller_order = (current_storyteller_order + 1) % self.playergamestates.count()
        return self.playergamestates.get(order=next_storyteller_order)
    
    def new_round(self, playerstate, selected_card, sentence):
        if self.current_state != GameState.WAITING_STORYTELLER_NEW_ROUND:
            raise ValueError("Current game state does not allow to create a new round!")
        '@type GameRound'
        current_round = self.current_round()
        #check opened round
        if current_round and current_round.opened:
            raise ValueError('There is a game round already in progress for game ' + self.board_id)
        #check player is the current story teller
        if playerstate != self.current_storyteller_playergamestate():
            raise ValueError('Only current storyteller can create a new game round. ')
        #check selected card belongs to storyteller
        if not playerstate.has_card(selected_card):
            raise ValueError("The selected card must be one of current player's card.")
        self.current_state = GameState.WAITING_PLAYERS_CHOSEN_CARDS
        new_round_order = 0
        if current_round:
            new_round_order = current_round.order+1
        '@type GameRound'
        new_game_round = GameRound.objects.create(game = self, 
                                 order = new_round_order, 
                                 storyteller_player=playerstate, 
                                 storyteller_selected_card = selected_card,
                                 storyteller_sentence_for_selected_card = sentence
                                 )
        new_game_round.play_card_chosen(playerstate, selected_card)
        return new_game_round
        
    def play_card_chosen(self, playerstate, selected_card):        
        if self.current_state != GameState.WAITING_PLAYERS_CHOSEN_CARDS:
            raise ValueError("Current game state does not allow to create a new round!")  
        '@rtype GameRound'
        current_round = self.current_round()
        playerplay = current_round.play_card_chosen(playerstate, selected_card)
        if (current_round.all_players_card_chosen()):
            self.current_state = GameState.VOTING
        return playerplay

    def get_playergamestate_for_player(self, player):
        return self.playergamestates.get(player = player)

    
class PlayerPlay(models.Model):
    game_round = models.ForeignKey('GameRound', related_name='plays')
    owner_player = models.ForeignKey(PlayerGameState, related_name='plays+')
    selected_card = models.ForeignKey(Card, related_name='+')
    unchosen_cards = ListField(models.ForeignKey(Card))
    voted_by_players = ListField(models.ForeignKey(PlayerGameState))
    storyteller = models.BooleanField(default=False)   
    def __unicode__(self):
        return 'PlayerPlay \n  owner: ' + self.owner_player.player.name + \
                ' \n  Storyteller: ' + str(self.storyteller) + \
                ' \n  Selected card: ' + str(self.selected_card) + \
                ' \n  Unchosen cards: ' + str(self.unchosen_cards)
    def set_unchosen_cards(self, cards):
        for card in cards:
            self.unchosen_cards.append(card.id)
        self.save()
    
class GameRound(models.Model):
    game = models.ForeignKey(Game, related_name='rounds')
    order = models.IntegerField(default=0)
    opened = models.BooleanField(default=True)   
    storyteller_player = models.ForeignKey(PlayerGameState, related_name='+')
    storyteller_selected_card = models.ForeignKey(Card, related_name='+')
    storyteller_sentence_for_selected_card = models.CharField(max_length=1000)
    def __unicode__(self):
        return 'GameRound: game ' + self.game.board_id + \
                ' Storyteller ' + self.storyteller_player.player.name + \
                ' Storyteller selected card: ' + self.storyteller_selected_card.url + \
                ' Storyteller sentence: ' + self.storyteller_sentence_for_selected_card 
                
    def play_card_chosen(self, playerstate, selected_card):
        '@type playerstate: PlayerGameState'
        '@type selected_card: Card'
        if not self.opened:
            raise ValueError('This game round is already closed!')
        print '--------'
        print self.plays.all()
        print '--------'
        if self.plays.filter(owner_player=playerstate).exists():
            raise ValueError("The player has already chosen a card on this round!")
        unchosen_cards = playerstate.remaining_cards(selected_card)
        new_play = PlayerPlay.objects.create(game_round = self,
                                             owner_player = playerstate,
                                             selected_card = selected_card
                                             )
        new_play.set_unchosen_cards(unchosen_cards)
        self.plays.add(new_play)
        playerstate.remove_card(selected_card.id)
        self.save()
        return new_play
    
    def all_players_card_chosen(self):
        return self.game.players_count() == self.plays.all().count()
        
            
    
    