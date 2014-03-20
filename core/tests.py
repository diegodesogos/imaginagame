"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""

from django.test import TestCase
from core.models import Game, Card, Player, PlayerGameState

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
                print card.url
                print a_playerstate.cards
                a_playerstate.cards.append(card.id)
                a_playerstate.save()
        game.save()
    
    def test_creation(self):
        '@type game: Game'
        game = Game.objects.get(board_id='board 1')
        self.assertEqual(Card.objects.all().count(), 20)
        self.assertEqual(Player.objects.all().count(), 3)
        self.assertEqual(game.board_id, 'board 1')
        self.assertEqual(game.playergamestates.count(), 3)
        playergamestate = game.playergamestates.get(player_state_id='playerstate_player_url0')
        #matches one single card
        print '-------'
        print playergamestate.cards
        print '-------'
        card_id = playergamestate.cards[0]
        '@type card: Card'
        card = Card.objects.get(url="url0")
        self.assertEqual(card_id, card.id)
        
       