"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""

from django.test import TestCase
from core.models import Game, Card, Player, GameState, Deck

import core.const
import logging
logger =  core.const.configureLogger('models')

class GameTest(TestCase):
    def setUp(self):
        '@type game: Game'
        deck = Deck.objects.create(name='deck1')
        for idx in range(0, 24):
            deck.create_card(url='url' +`idx`, name='card '+`idx`)
        game = Game.objects.create(board_id='board 1', deck=deck, min_players=3)

        for idx in range(0, 3):
            a_player= Player.objects.create(name='player' +`idx`)
            '@type a_playerstate: PlayerGameState'
            game.create_playerstate(a_player)
        self.assertEqual(game.current_state, GameState.WAITING_STORYTELLER_NEW_ROUND)    
        game.save()
    
    def tets_game_players_count(self):
        '@type game: Game'
        game = Game.objects.get(board_id='board 1')
        self.assertEqual(game.players_count(), 3)
        
    
    def test_creation(self):
        '@type game: Game'
        game = Game.objects.get(board_id='board 1')
        self.assertEqual(Card.objects.all().count(), 24)
        self.assertEqual(Player.objects.all().count(), 3)
        self.assertEqual(game.board_id, 'board 1')
        self.assertEqual(game.playergamestates.all().count(), 3)
        player = Player.objects.get(name="player1")
        playergamestate = game.playergamestates.get(player=player)
        self.assertEqual(6, len(playergamestate.cards))
        
    def test_game_next_storyteller_when_no_rounds(self):
        '@type game: Game'
        game = Game.objects.get(board_id='board 1')
        player = Player.objects.get(name="player0")
        playergamestate = game.playergamestates.get(player=player)
        next_storyteller =  game.next_storyteller_playergamestate()
        self.assertEqual(next_storyteller, playergamestate)    
        
    def test_create_first_game_round(self):
        '@type game: Game'
        game = Game.objects.get(board_id='board 1')
        '@type playergamestate: PlayerGameState'
        playergamestate = game.next_storyteller_playergamestate()
        #get second card from storyteller
        selected_card = playergamestate.get_card(2)
        new_game_round = game.new_round(playergamestate, selected_card, 'I have selected the card positioned at 2')
        self.assertEqual(new_game_round, game.current_round())
        self.assertEqual(game.current_state, GameState.WAITING_PLAYERS_CHOSEN_CARDS)
        
    def test_game_play_card_chosen(self):
        '@type game: Game'
        game = Game.objects.get(board_id='board 1')
        storyteller = game.next_storyteller_playergamestate()
        selected_card = storyteller.get_card(2)
        game.new_round(storyteller, selected_card, 'I have selected the card positioned at 2')
        self.assertEqual(game.current_state, GameState.WAITING_PLAYERS_CHOSEN_CARDS)
        self.assertIsNotNone(game.current_round())
        #storyteller should not be able to play
        self.assertRaises(ValueError, game.play_card_chosen, storyteller, selected_card)
        #verify other players can play
        playergamestate1 = game.get_playergamestate_for_player(Player.objects.get(name='player' + str(1)))
        selected_card2 = playergamestate1.get_card(2)
        game.play_card_chosen(playergamestate1, selected_card2)
        #verify a player cannot play another player's card
        self.assertRaises(ValueError, game.play_card_chosen, playergamestate1, selected_card)
        self.assertEqual(game.current_state, GameState.WAITING_PLAYERS_CHOSEN_CARDS)
        #verify that once all three players chosen a card, the game changes to voting stage
        playergamestate2 = game.get_playergamestate_for_player(Player.objects.get(name='player' + str(2)))
        selected_card3 = playergamestate2.get_card(3)
        game.play_card_chosen(playergamestate2, selected_card3)
        self.assertEqual(game.current_state, GameState.VOTING)
        
    def test_game_vote_card(self):
        '@type game: Game'
        game = Game.objects.get(board_id='board 1')
        storyteller = game.next_storyteller_playergamestate()
        selected_card = storyteller.get_card(2)
        playergamestate1 = game.get_playergamestate_for_player(Player.objects.get(name='player' + str(1)))
        playergamestate2 = game.get_playergamestate_for_player(Player.objects.get(name='player' + str(2)))
        game.new_round(storyteller, selected_card, 'I have selected the card positioned at 2')
        selected_card2 = playergamestate1.get_card(2)
        game.play_card_chosen(playergamestate1, selected_card2)
        selected_card3 = playergamestate2.get_card(2)
        game.play_card_chosen(playergamestate2, selected_card3)
        cards = game.get_current_round_chosen_cards()
        logger.debug('---- CARDS IN PLAY---\n %s \ END CARDS IN PLAY', cards)
        if core.const.LOG_LEVEL == logging.DEBUG:
            logger.debug('---- STORY TELLER CHOSEN CARD: %s ', game.get_current_round_storyteller_chosen_card())
        game.vote_card(playergamestate1, selected_card3)
        self.assertEqual(game.current_state, GameState.VOTING)
        game.vote_card(playergamestate2, selected_card2)
        self.assertEqual(game.current_state, GameState.WAITING_STORYTELLER_NEW_ROUND)
        
        
    def start_new_round(self, game, storyteller, playergamestate1, playergamestate2, storyteller_card, player1_card, player2_card):
        self.assertEqual(game.current_state, GameState.WAITING_STORYTELLER_NEW_ROUND)
        game.new_round(storyteller, storyteller_card, 'I have selected the card ' + storyteller_card.name)
        self.assertEqual(game.current_state, GameState.WAITING_PLAYERS_CHOSEN_CARDS)
        game.play_card_chosen(playergamestate1, player1_card)
        game.play_card_chosen(playergamestate2, player2_card)
        self.assertEqual(game.current_state, GameState.VOTING)           
        
    def test_full_game_cycle(self):
        '@type game: Game'
        game = Game.objects.get(board_id='board 1')
        #prepare to start round 1
        storyteller = game.next_storyteller_playergamestate()
        playergamestate0 = game.get_playergamestate_for_player(Player.objects.get(name='player' + str(0)))
        self.assertEquals(storyteller, playergamestate0)
        playergamestate1 = game.get_playergamestate_for_player(Player.objects.get(name='player' + str(1)))
        playergamestate2 = game.get_playergamestate_for_player(Player.objects.get(name='player' + str(2)))
        storyteller_card = storyteller.get_card(0)
        player1_card = playergamestate1.get_card(0)
        player2_card = playergamestate2.get_card(0)
        
        logger.debug('---------------GAME CYCLE, ROUND START')
        self.start_new_round(game, storyteller, playergamestate1, playergamestate2, storyteller_card, player1_card, player2_card)
        
        logger.debug('Round cards are: %s', game.get_current_round_chosen_cards())
        
        game.vote_card(playergamestate1, storyteller_card)
        #cannot choose owns card
        self.assertRaises(ValueError, game.vote_card, playergamestate2, player2_card)
        #cannot vote again
        self.assertRaises(ValueError, game.vote_card, playergamestate1, player2_card)
        
        self.assertEqual(game.current_state, GameState.VOTING)
        
        game.vote_card(playergamestate2, player1_card)
        
        self.assertEqual(game.current_state, GameState.WAITING_STORYTELLER_NEW_ROUND)
        
        #get updated versions of each player and game
        game = Game.objects.get(board_id='board 1')
        playergamestate0 =  game.get_playergamestate_for_player(Player.objects.get(name='player' + str(0)))
        playergamestate1 =  game.get_playergamestate_for_player(Player.objects.get(name='player' + str(1)))
        playergamestate2 =  game.get_playergamestate_for_player(Player.objects.get(name='player' + str(2)))        
        #storyteller card found by player 1, not found by player 2 who chosen player 1 card

        self.assertEqual(3, playergamestate0.points)
        self.assertEqual(4, playergamestate1.points)
        self.assertEqual(0, playergamestate2.points)
        logger.debug('---------------GAME CYCLE, ROUND 1 END')
        
        self.assertFalse(game.is_game_over())
        self.assertTrue(game.are_enough_cards_for_another_round())
        

        
        #######################
        
        #lets play next round
        storyteller = playergamestate1
        self.assertEqual(storyteller, game.next_storyteller_playergamestate())
        
        storyteller_card = storyteller.get_card(0)
        player0_card = playergamestate0.get_card(0)
        player2_card = playergamestate2.get_card(0)
        
        logger.debug('---------------GAME CYCLE, ROUND 2 START')
        self.start_new_round(game, storyteller, playergamestate0, playergamestate2, storyteller_card, player0_card, player2_card)
        
        logger.debug('Round cards are: %s', game.get_current_round_chosen_cards())
        
        game.vote_card(playergamestate0, player2_card)
        game.vote_card(playergamestate2, player0_card)
        
        #get updated versions of each player and game
        game = Game.objects.get(board_id='board 1')
        playergamestate0 =  game.get_playergamestate_for_player(Player.objects.get(name='player' + str(0)))
        playergamestate1 =  game.get_playergamestate_for_player(Player.objects.get(name='player' + str(1)))
        playergamestate2 =  game.get_playergamestate_for_player(Player.objects.get(name='player' + str(2)))        
        #storyteller card not found, everyone else score 2 points, each player whos card was chosen get one extra point

        self.assertEqual(3+2+1, playergamestate0.points)
        self.assertEqual(4, playergamestate1.points)
        self.assertEqual(0+2+1, playergamestate2.points)
        logger.debug('---------------GAME CYCLE, ROUND 2 END')
        
        logger.debug(' CARDS REMAINING AFTER ROUND: %s', game.remaining_cards)

        #this will be the last round (cards were already drawn)
        self.assertFalse(game.are_enough_cards_for_another_round())
        
        ##########
        ##########
        #######################
        
        #lets play the last round, this time, both choose storyteller card
        storyteller = playergamestate2
        self.assertEqual(storyteller, game.next_storyteller_playergamestate())
        
        storyteller_card = storyteller.get_card(0)
        player0_card = playergamestate0.get_card(0)
        player1_card = playergamestate1.get_card(0)
        
        logger.debug('---------------GAME CYCLE, ROUND 3 START')
        self.start_new_round(game, storyteller, playergamestate0, playergamestate1, storyteller_card, player0_card, player1_card)
        
        logger.debug('Round cards are: %s', game.get_current_round_chosen_cards())
        
        game.vote_card(playergamestate0, storyteller_card)
        game.vote_card(playergamestate1, storyteller_card)
        
        #get updated versions of each player and game
        game = Game.objects.get(board_id='board 1')
        playergamestate0 =  game.get_playergamestate_for_player(Player.objects.get(name='player' + str(0)))
        playergamestate1 =  game.get_playergamestate_for_player(Player.objects.get(name='player' + str(1)))
        playergamestate2 =  game.get_playergamestate_for_player(Player.objects.get(name='player' + str(2)))        
        #storyteller card not found, everyone else score 2 points, each player whos card was chosen get one extra point

        self.assertEqual(6+2, playergamestate0.points)
        self.assertEqual(4+2, playergamestate1.points)
        self.assertEqual(3+0, playergamestate2.points)
        logger.debug('---------------GAME CYCLE, ROUND 3 END')
        
        logger.debug(' CARDS REMAINING AFTER ROUND: %s', game.remaining_cards)       
       
        ##########
        ##########
        
        self.assertTrue(game.is_game_over())
