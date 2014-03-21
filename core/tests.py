"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""

from django.test import TestCase
from core.models import Game, Card, Player, GameState

class GameTest(TestCase):
    def setUp(self):
        '@type game: Game'
        game = Game.objects.create(board_id='board 1')
        for idx in range(0, 20):
            Card.objects.create(url='url' +`idx`, description='card '+`idx`)
        for idx in range(0, 3):
            a_player= Player.objects.create(name='player' +`idx`)
            player_order = idx
            '@type a_playerstate: PlayerGameState'
            a_playerstate = game.playergamestates.create(order=player_order,player=a_player, player_state_id='playerstate_player_url'+`idx`)
            for cardidx in range(idx, idx+5):
                card_id = idx*5 + cardidx
                card = Card.objects.get(url='url'+`card_id`)
                a_playerstate.add_card(card)
        game.save()
    
    def tets_game_players_count(self):
        '@type game: Game'
        game = Game.objects.get(board_id='board 1')
        self.assertEqual(game.players_count(), 3)
        
    
    def test_creation(self):
        '@type game: Game'
        game = Game.objects.get(board_id='board 1')
        self.assertEqual(Card.objects.all().count(), 20)
        self.assertEqual(Player.objects.all().count(), 3)
        self.assertEqual(game.board_id, 'board 1')
        self.assertEqual(game.playergamestates.count(), 3)
        playergamestate = game.playergamestates.get(player_state_id='playerstate_player_url0')
        #matches one single card
        card_id = playergamestate.cards[0]
        '@type card: Card'
        card = Card.objects.get(url="url0")
        self.assertEqual(card_id, card.id)
        
    def test_game_current_storyteller_when_no_rounds(self):
        '@type game: Game'
        game = Game.objects.get(board_id='board 1')
        playergamestate = game.playergamestates.get(player_state_id='playerstate_player_url0')
        current_storyteller =  game.current_storyteller_playergamestate()
        self.assertEqual(current_storyteller, playergamestate)
        
    def test_game_next_storyteller_when_no_rounds(self):
        '@type game: Game'
        game = Game.objects.get(board_id='board 1')
        playergamestate = game.playergamestates.get(player_state_id='playerstate_player_url1')
        next_storyteller =  game.next_storyteller_playergamestate()
        self.assertEqual(next_storyteller, playergamestate)    
        
    def test_create_first_game_round(self):
        '@type game: Game'
        game = Game.objects.get(board_id='board 1')
        '@type playergamestate: PlayerGameState'
        playergamestate = game.current_storyteller_playergamestate()
        #get second card from storyteller
        selected_card = playergamestate.get_card(2)
        new_game_round = game.new_round(playergamestate, selected_card, 'I have selected the card positioned at 2')
        self.assertEqual(new_game_round, game.current_round())
        self.assertEqual(playergamestate, game.current_storyteller_playergamestate())
        self.assertEqual(game.current_state, GameState.WAITING_PLAYERS_CHOSEN_CARDS)
        
    def test_game_play_card_chosen(self):
        '@type game: Game'
        game = Game.objects.get(board_id='board 1')
        storyteller = game.current_storyteller_playergamestate()
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
        storyteller = game.current_storyteller_playergamestate()
        selected_card = storyteller.get_card(2)
        playergamestate1 = game.get_playergamestate_for_player(Player.objects.get(name='player' + str(1)))
        playergamestate2 = game.get_playergamestate_for_player(Player.objects.get(name='player' + str(2)))
        game.new_round(storyteller, selected_card, 'I have selected the card positioned at 2')
        selected_card2 = playergamestate1.get_card(2)
        game.play_card_chosen(playergamestate1, selected_card2)
        selected_card3 = playergamestate2.get_card(2)
        game.play_card_chosen(playergamestate2, selected_card3)
        cards = game.get_current_round_chosen_cards()
        print '---- CARDS IN PLAY---'
        print cards
        print '---- END CARDS IN PLAY---'
        print '---- STORY TELLER CHOSEN CARD'
        print game.get_current_round_storyteller_chosen_card()
        print '---- END STORY TELLER CHOSEN CARD---'
        selectedcard1 = cards[0]
        selectedcard2 = cards[0]
        game.vote_card(playergamestate1, selectedcard1)
        self.assertEqual(game.current_state, GameState.VOTING)
        game.vote_card(playergamestate2, selectedcard2)
        self.assertEqual(game.current_state, GameState.WAITING_STORYTELLER_NEW_ROUND)
        #TODO make asserts of game score for each player
        