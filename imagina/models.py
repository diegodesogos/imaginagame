from django.db import models
from datetime import datetime
from djangotoolbox.fields import ListField
import random
import uuid
import imagina.const
logger =  imagina.const.configureLogger('models')

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
    
NUMBER_OF_PLAYERS_CHOICES = [(i,i) for i in range(4,7)]

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
    storyteller = models.BooleanField(default=False)
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
        
    def get_current_position(self):
        return self.game.get_current_position(self)
 
class Game(models.Model):
    board_id = models.CharField(max_length=400)
    deck = models.ForeignKey(Deck)
    #the cards that will be draw during the game, each time a card is assigned to a player it is removed from this list
    remaining_cards = ListField(models.ForeignKey(Card))
    min_players = models.IntegerField(default=4)
    creation_date = models.DateTimeField(default=datetime.now, blank=True)
    #can be 0 to play till deck of cards is exhausted
    points_goal = models.IntegerField(default=0)
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
        count = self.players_count()
        if not new_player:
            new_player = Player.objects.create('anon' + `count`)
            new_player.save()
            
        player_state_id = uuid.uuid4()
        new_player_state = PlayerGameState.objects.create(game=self, order = count, player = new_player, player_state_id = player_state_id)
        logger.debug('Created playerstate %s', player_state_id)
        self.playergamestates.add(new_player_state)
        if self.players_count() >= self.min_players:
            self.start_with_current_players()
        self.save()
        return new_player_state
                
    def players_count(self):
        return self.playergamestates.all().count()   
    
    def get_current_position(self, playerstate):
        position = 1
        for player in self.get_playerstates_by_position():
            if (player == playerstate):
                return position
            position = position + 1
        return position
    
    def get_playerstates_by_position(self):
        return self.playergamestates.order_by('points')
    
    def current_round(self):
        '@rtype GameRound'
        rounds = self.rounds.order_by('order')
        if not rounds:
            return None
        return rounds.reverse()[0]
    
        

    def next_storyteller_playergamestate(self):
        last_round = self.current_round()
        if not last_round:
            #get first PlayerGameState from player game states
            return self.playergamestates.order_by('order')[0]
        '@type PlayerGameState'
        current_storyteller_order = last_round.storyteller_player.order
        next_storyteller_order = (current_storyteller_order + 1) % self.playergamestates.all().count()
        return self.playergamestates.get(order=next_storyteller_order)
    
    
    def start_with_current_players(self):
        if self.current_state != GameState.WAITING_NEW_PLAYERS:
            raise ValueError("Current game state does not allow to start the game!")
        if self.players_count() < self.min_players:
            raise ValueError('There are not enough players to start the game!')
        self.current_state = GameState.WAITING_STORYTELLER_NEW_ROUND
        self.draw_cards(None)
        self.save()
        
    '''
    private
    called to assign next storyteller to one of current playerstates
    '''    
    def assign_story_teller(self, previous_story_teller):
        if self.current_state != GameState.WAITING_STORYTELLER_NEW_ROUND:
            raise ValueError("Current game state does not allow assign next storyteller!")
        storyteller_state  = self.next_storyteller_playergamestate()
        storyteller_state.storyteller = True
        storyteller_state.save()
        if previous_story_teller:
            previous_story_teller.storyteller =  False
            previous_story_teller.save()
        
    
    def new_round(self, playerstate, selected_card, sentence):
        if self.current_state != GameState.WAITING_STORYTELLER_NEW_ROUND:
            raise ValueError("Current game state does not allow to create a new round!")
        '@type GameRound'
        current_round = self.current_round()
        #check opened round
        if current_round and current_round.opened:
            raise ValueError('There is a game round already in progress for game ' + self.board_id)
        #check player is the current story teller
        if playerstate != self.next_storyteller_playergamestate():
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
        new_game_round.save()
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
        return current_round.get_current_play_for_playerstate(playerstate)
    
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
            raise ValueError('Player cannot vote to his own selected card! ' + self.board_id)
        current_round.vote_card(playerstate, selected_card)
        if not current_round.opened:
            logger.debug('Round %s closed, preparing for next round', current_round.id)
            logger.debug('Remaining cards in deck: %s', self.remaining_cards)
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
                return
        if self.are_enough_cards_for_another_round():
            logger.debug('Drawing cards for next round')
            self.draw_cards(current_round.storyteller_player)
        else:
            logger.debug('Not enough cards for another round, game ended')
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

    
    '''
    private draw card_count cards to playerstate
    '''
    def draw_cards_to_players(self, card_count):
        for playerstate in self.get_playerstates():
            for _ in range(card_count):
                        card = self.draw_card()
                        playerstate.add_card(card)
        
    def draw_cards(self, previous_story_teller):
        if (self.current_state != GameState.FINISHED and len(self.remaining_cards) == 0):
            self.init_remaining_cards_pool()
            self.draw_cards_to_players(self.player_card_count())
        else:
            #we have to redraw one card to each player
            if not self.are_enough_cards_for_another_round():
                raise ValueError('There are not enough cards in the deck!')
            self.draw_cards_to_players(1)
        self.assign_story_teller(previous_story_teller)
        self.save()
        
    def is_game_over(self):
        return self.current_state == GameState.FINISHED
    def is_waiting_new_players(self):
        return self.current_state == GameState.WAITING_NEW_PLAYERS
    
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
        total_votes_for_this_player_card = len(self.voted_by_players)
        total_votes_to_storyteller_card = len(storyteller_play.voted_by_players)

        all_found_storyteller_or_none_dit_it = total_votes_to_storyteller_card == total_plays-1 or total_votes_to_storyteller_card == 0
        round_points_for_this_player = 0      
          
        #Rule 1: If all the players have found the storyteller's image, 
        #or if none have found it, then the storyteller doesn't 
        #score any points and everyone else scores 2 points
        if all_found_storyteller_or_none_dit_it:
            if not self.storyteller:
                logger.debug('Round %d, Player %s gets 2 points', self.game_round.id, self.owner_player)
                round_points_for_this_player = 2
        else:
            #Rule 2: In any other case, the storyteller scores 3 points
            #and so do the players who found his card.
            if self.storyteller or storyteller_play.voted_by_playerstate(self.owner_player):
                logger.debug('Round %d, Player %s gets 3 points for being the storyteller or voting to storyteller card', self.game_round.id, self.owner_player)
                round_points_for_this_player = 3
                    
        #Rule 3: Each player, except the storyteller scores one point 
        #for each vote that was placed on his or her card
        if not self.storyteller:
            logger.debug('Round %d, Player %s gets %d points for other players voting its card', self.game_round.id, self.owner_player, total_votes_for_this_player_card)
            round_points_for_this_player = round_points_for_this_player + total_votes_for_this_player_card
            
        self.points = round_points_for_this_player
        self.owner_player.add_round_points(round_points_for_this_player)
        logger.debug('Player round points: %d \nPlayer total points so far: %d', self.points, self.owner_player.points)
        self.save()
        logger.debug('---- END SCORES FOR %s -----', self.owner_player)
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
        random.shuffle(cards)    
        return cards
    
    def get_current_play_for_playerstate(self, playerstate):
        plays =  self.plays.filter(owner_player=playerstate)
        if plays.count() > 1:
            raise ValueError('found more than one play for the same player in the same round!')
        if plays.count() == 1:
            return plays[0]
        else:
            return None
    
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
        logger.debug('Game round %d finished and closed', self.id )
        self.opened = False
        all_plays = self.plays.all()
        total_plays = all_plays.count()
        storyteller_play = self.storyteller_play()
        logger.debug('STORY TELLER SELECTED CARD IS  %s',  storyteller_play.selected_card)
        for play in all_plays:
            '@type play: PlayerPlay'
            play.compute_round_scores(storyteller_play, total_plays)
        self.save()
            
        
            
    
    
