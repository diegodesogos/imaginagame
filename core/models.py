from django.db import models
from datetime import datetime
from djangotoolbox.fields import ListField
import random

import core.const
logger =  core.const.configureLogger('models')

class GameState():
    """game states"""
    WAITING_NEW_PLAYERS = 'WAITING_NEW_PLAYERS'
    WAITING_STORYTELLER_NEW_ROUND = 'WAITING_STORYTELLER_NEW_ROUND'
    WAITING_PLAYERS_CHOSEN_CARDS = 'WAITING_PLAYERS_CHOSEN_CARDS'
    VOTING = 'VOTING'
    FINISHED = 'FINISHED'
    CURRENT_GAME_STATE_CHOICES = (
        (WAITING_NEW_PLAYERS, 'WAITING_NEW_PLAYERS'),
        (WAITING_STORYTELLER_NEW_ROUND, 'WAITING_STORYTELLER_NEW_ROUND'),
        (WAITING_PLAYERS_CHOSEN_CARDS, 'WAITING_PLAYERS_CHOSEN_CARDS'),
        (VOTING, 'VOTING'),
        (FINISHED, 'FINISHED'),
    )

class Player(models.Model):
    name = models.CharField(max_length=200)
    def __unicode__(self):
        return 'Player ' + self.name
    
class Deck(models.Model):
    name = models.CharField(max_length=200, default='unnamed')
    description = models.CharField(max_length=200, default='none')
    author = models.CharField(max_length=200, default='unknown')
    def __unicode__(self):
        return 'Deck ' + self.name
    def create_card(self, url, name):
        card = Card.objects.create(url=url, name=name, deck=self)
        return card
    def cards_count(self):
        return len(self.get_cards())
    
    def get_cards(self):
        return self.cards.all()
    
    def get_card(self, card_id):
        return self.cards.get(id=card_id)

class Card(models.Model):
    url = models.CharField(max_length=400)
    name = models.CharField(max_length=200)
    deck = models.ForeignKey(Deck, related_name='cards')
    def __unicode__(self):
        return self.name

class PlayerGameState(models.Model):
    game = models.ForeignKey('Game', related_name='playergamestates')
    order = models.IntegerField(default=0)
    player = models.ForeignKey(Player)
    player_state_id = models.CharField(max_length=400)
    points = models.IntegerField(default=0)
    cards = ListField(models.ForeignKey(Card))
    def __unicode__(self):
        return 'player {0} player_state_id: {1} Points: {2} Cards: {3}'.format(self.player.name,
                                                                                                self.player_state_id,
                                                                                                self.points,
                                                                                                self.get_cards())
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
    def add_round_points(self, round_points):
        self.points = self.points + round_points
        logger.debug("ADDING POINTS TO player %s . Round points: %d . NEW TOTAL: %d", self.player_state_id, round_points, self.points)
        self.save()
 
class Game(models.Model):
    board_id = models.CharField(max_length=400)
    deck = models.ForeignKey(Deck)
    #the cards that will be draw during the game, each time a card is assigned to a player it is removed from this list
    remaining_cards = ListField(models.ForeignKey(Card))
    creation_date = models.DateTimeField(default=datetime.now, blank=True)
    #can be 0 to play till deck of cards is exhausted
    points_goal = models.IntegerField(default=30)
    current_state = models.CharField(max_length=40,
                                      choices=GameState.CURRENT_GAME_STATE_CHOICES,
                                      default=GameState.WAITING_NEW_PLAYERS)
                  
    def __unicode__(self):
        return 'Game: unique id ' + self.board_id + \
                ' Game state: ' + self.current_state    
    
    def create_playerstate(self, player=None):
        if self.current_state != GameState.WAITING_NEW_PLAYERS:
            raise ValueError("Current game state does not allow to add new players!")
        new_player = player  
        if not new_player:
            new_player = Player.objects.create('anon')
            new_player.save()
        count = self.players_count()    
        next_id = count+1
        player_url = 'playerstate_player_url'+`next_id`
        new_player_state = PlayerGameState.objects.create(game=self, order = count, player = new_player, player_state_id = player_url)
        logger.debug('Created player %s', new_player_state)
        self.playergamestates.add(new_player_state)
        self.save()
        return new_player_state
                
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
        last_round = self.current_round()
        if not last_round:
            return self.current_storyteller_playergamestate()
        '@type PlayerGameState'
        current_storyteller_order = self.current_storyteller_playergamestate().order
        next_storyteller_order = (current_storyteller_order + 1) % self.playergamestates.all().count()
        return self.playergamestates.get(order=next_storyteller_order)
    
    
    def start_with_current_players(self):
        if self.current_state != GameState.WAITING_NEW_PLAYERS:
            raise ValueError("Current game state does not allow to start the game!")
        if self.players_count() < self.min_players_count():
            raise ValueError('There are not enough players to start the game!')
        self.current_state = GameState.WAITING_STORYTELLER_NEW_ROUND
        self.draw_cards()
        self.save()
        
    
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
        new_game_round.play_card_chosen(playerstate, selected_card, True)
        return new_game_round
        
    def play_card_chosen(self, playerstate, selected_card):        
        if self.current_state != GameState.WAITING_PLAYERS_CHOSEN_CARDS:
            raise ValueError("Current game state does not allow to create a new round!")  
        '@rtype GameRound'
        current_round = self.current_round()
        playerplay = current_round.play_card_chosen(playerstate, selected_card)
        if (current_round.all_players_chosen_cards()):
            self.current_state = GameState.VOTING
        return playerplay

    def get_playergamestate_for_player(self, player):
        return self.playergamestates.get(player = player)
    
    def get_all_playergamestates(self):
        return self.playergamestates.all()
    
    def get_current_play_for_playerstate(self, playerstate):
        current_round = self.current_round()
        # check opened round
        if not current_round:
            raise ValueError('No current round for game ' + self.board_id)
        return self.current_round().get_current_play_for_playerstate(playerstate)
    
    def get_current_round_chosen_cards(self):
        current_round = self.current_round()
        #check opened round
        if not current_round:
            raise ValueError('No current round for game ' + self.board_id)
        return current_round.get_chosen_cards()
    def get_current_round_storyteller_chosen_card(self):
        current_round = self.current_round()
        #check opened round
        if not current_round:
            raise ValueError('No current round for game ' + self.board_id)
        return current_round.storyteller_chosen_card()
    
    def vote_card(self, playerstate, selected_card):
        if self.current_state != GameState.VOTING:
            raise ValueError("Current game state does not allow voting!")
        '@type GameRound'
        current_round = self.current_round()
        # check opened round
        if not current_round:
            raise ValueError('No current round for game ' + self.board_id)
        # check opened round
        if not current_round.opened:
            raise ValueError('This game round is already closed ' + self.board_id)
        play = self.get_current_play_for_playerstate(playerstate)
        if play.selected_card == selected_card:
            raise ValueError('Player cannot vote to its selected card! ' + self.board_id)
        current_round.vote_card(playerstate, selected_card)
        if not current_round.opened:
            self.prepare_for_next_round(current_round)
    
    '''
    Private
    All players played a card, all players voted, round is over
    compute scores and prepare for next round
    '''
    def prepare_for_next_round(self, current_round):
        #next state may be WAITING_STORYTELLER_NEW_ROUND or FINISHED according to scores
        self.current_state = GameState.WAITING_STORYTELLER_NEW_ROUND
        for playerstate in self.playergamestates.all():
            playerstate.points += current_round.get_current_play_for_playerstate(playerstate).points
            if self.points_goal > 0 and playerstate.points >= self.points_goal:
                self.current_state = GameState.FINISHED
        if self.are_enough_cards_for_another_round():
            self.draw_cards()
        else:
            self.current_state = GameState.FINISHED
        self.save()
    
    def init_remaining_cards_pool(self):
        for card in self.deck.get_cards():
            self.remaining_cards.append(card.id)
        random.shuffle(self.remaining_cards)
            
    def are_enough_cards_for_another_round(self):
        return  len(self.remaining_cards) >= self.players_count()
    
    def get_playerstates(self):
        return self.playergamestates.all()
   
    '''
    private draw a card from remaining_cards
    ''' 
    def draw_card(self):
        card_id = self.remaining_cards.pop(0)
        return self.deck.get_card(card_id)
    
                
    '''how many cards per player'''
    def player_card_count(self):
        return 6
    
    '''how many cards per player'''
    def min_players_count(self):
        return 3
    
    '''
    private draw card_count cards to playerstate
    '''
    def draw_cards_to_players(self, card_count):
        for playerstate in self.get_playerstates():
            for _ in range(card_count):
                        card = self.draw_card()
                        playerstate.add_card(card)
        
    def draw_cards(self):
        if (self.current_state != GameState.FINISHED and len(self.remaining_cards) == 0):
            self.init_remaining_cards_pool()
            self.draw_cards_to_players(self.player_card_count())
        else:
            #we have to redraw one card to each player
            if not self.are_enough_cards_for_another_round():
                raise ValueError('There are not enough cards in the deck!')
            self.draw_cards_to_players(1)
        self.save()
        
    def is_game_over(self):
        return self.current_state == GameState.FINISHED
    
class PlayerPlay(models.Model):
    game_round = models.ForeignKey('GameRound', related_name='plays')
    owner_player = models.ForeignKey(PlayerGameState, related_name='plays+')
    selected_card = models.ForeignKey(Card, related_name='+')
    unchosen_cards = ListField(models.ForeignKey(Card))
    voted_by_players = ListField(models.ForeignKey(PlayerGameState))
    storyteller = models.BooleanField(default=False)   
    #cache calculated value to avoid recomputing sums each time
    #this is calculated once the round where this play was performed is closed
    points = models.IntegerField(default=0)    
    def __unicode__(self):
        return 'PlayerPlay \n  owner: ' + self.owner_player.player.name + \
                ' \n  Storyteller: ' + str(self.storyteller) + \
                ' \n  Selected card: ' + str(self.selected_card) + \
                ' \n  Unchosen cards: ' + str(self.unchosen_cards)
    def set_unchosen_cards(self, cards):
        for card in cards:
            self.unchosen_cards.append(card.id)
        self.save()
    def vote_playerstate(self, playerstate):
        logger.debug('Player %s with selected card %s have received a vote from player %s', self.owner_player.player_state_id, self.selected_card.name, playerstate.player_state_id)
        self.voted_by_players.append(playerstate.id)
        self.save()
    def voted_by_playerstate(self, playerstate):
        for vote in self.voted_by_players:
            if playerstate.id == vote:
                return True
        return False
    '''
    Called by GameRound when the round is closed. 
    Computes the round total points obtained by this player.
    It caches the value in player's point field. Once the round is called, 
    it is safe to directly ask for the points by accessing points field
    '''
    def compute_round_scores(self, storyteller_play, total_plays):
        logger.debug( '---- SCORES FOR  %s ----------',  self.owner_player)
        total_votes = len(self.voted_by_players)
        if (self.storyteller):
            logger.debug( 'This player is the storyteller\n.  total votes:  %d \n  total players voting: %d', total_votes, total_plays)
            if ((total_votes != total_plays) and (total_votes > 0)):
                self.points = 3
        else:
            points_for_discover_storyteller_card = 0
            logger.debug( 'this player select card %s', self.selected_card)
            if (storyteller_play.voted_by_playerstate(self.owner_player)):              
                logger.debug('This player  discovered storyteller card!')
                points_for_discover_storyteller_card = 3
            self.points =  total_votes +  points_for_discover_storyteller_card
        self.owner_player.add_round_points(self.points)
        logger.debug('player round points: %d \n player total points so far: %d', self.points, self.owner_player.points)
        self.save()
        logger.debug('---- END SCORES -----')
        return self.points
    
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
                
    def play_card_chosen(self, playerstate, selected_card, storyteller=False):
        '@type playerstate: PlayerGameState'
        '@type selected_card: Card'
        if not self.opened:
            raise ValueError('This game round is already closed!')
        if self.plays.filter(owner_player=playerstate).exists():
            raise ValueError("The player has already chosen a card on this round!")
        unchosen_cards = playerstate.remaining_cards(selected_card)
        logger.debug('Play for player %s. \n           selected card: %s.\n           Unchosen cards are: %s', 
                     playerstate.player_state_id, selected_card.name, unchosen_cards)
        new_play = PlayerPlay.objects.create(game_round = self,
                                             owner_player = playerstate,
                                             selected_card = selected_card,
                                             storyteller=storyteller
                                             )
        new_play.set_unchosen_cards(unchosen_cards)
        self.plays.add(new_play)
        playerstate.remove_card(selected_card)
        self.save()
        return new_play
    
    def all_players_chosen_cards(self):
        return self.game.players_count() == self.plays.all().count()
    
    def get_vote_count(self):
        votes = 0
        for play in self.plays.all():
            votes =  votes +  len(play.voted_by_players)
        return votes
    
    def all_players_voted(self):
        votes = self.get_vote_count()
        #the storyteller does not vote
        return self.game.players_count() == (votes+1)
    
    def storyteller_chosen_card(self):
        return self.storyteller_play().selected_card
    
    def storyteller_play(self):
        return self.plays.get(storyteller=True)
    
    def get_chosen_cards(self):
        cards = []
        for play in self.plays.all():
            cards.append(play.selected_card)
        return cards
    
    def get_current_play_for_playerstate(self, playerstate):
        return self.plays.get(owner_player=playerstate)
    
    def get_playerplay_voted_by_playerstate(self, playerstate):
        for play in self.plays.all():
            if play.voted_by_playerstate(playerstate):
                return play
        return None

    def get_playerplay_for_card(self, card):
        for play in self.plays.all():
            if play.selected_card == card:
                    return play
        return None
    
    def vote_card(self, playerstate, selected_card):
        if not self.opened:
            raise ValueError('This game round is already closed!')
        if self.get_playerplay_voted_by_playerstate(playerstate):
            raise ValueError(str.format('The player %s  already voted on this round!', playerstate.player.name ))
        play =  self.get_playerplay_for_card(selected_card)
        play.vote_playerstate(playerstate)
        if (self.all_players_voted()):
            self.compute_round_scores()
        self.save()
        
    '''
    Private
    called once everybody played
    '''
    def compute_round_scores(self):
        if not self.opened:
            raise ValueError('This game round is already closed!')
        self.opened = False
        all_plays = self.plays.all()
        total_plays = all_plays.count()
        storyteller_play = self.storyteller_play()
        logger.debug('STORY TELLER SELECTED CARD IS  %s',  storyteller_play.selected_card)
        for play in all_plays:
            '@type play: PlayerPlay'
            play.compute_round_scores(storyteller_play, total_plays)
            
        
            
    
    
