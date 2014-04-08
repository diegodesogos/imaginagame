from imagina.models import NUMBER_OF_PLAYERS_CHOICES, Deck, Card
from django import forms

class NewGameForm(forms.Form):
    player_name = forms.CharField(max_length=100)
    number_of_players = forms.ChoiceField(choices=NUMBER_OF_PLAYERS_CHOICES)
    deck =  forms.ModelChoiceField(queryset=Deck.objects.all(), empty_label=None)

class ChooseCardForm(forms.Form):
    card = forms.ChoiceField(choices=[])
    def __init__(self, *args, **kwargs):
        player_cards = kwargs.pop('player_cards', None)
        super(forms.Form, self).__init__(*args, **kwargs)
        if player_cards:
            self.fields['card'].choices =  [(card.id,card.name) for card in player_cards]

class NewRoundForm(ChooseCardForm):
    phrase = forms.CharField(max_length=100, required=True)
    card = forms.ChoiceField(choices=[])
    def __init__(self, *args, **kwargs):
        player_cards = kwargs.pop('player_cards', None)
        super(forms.Form, self).__init__(*args, **kwargs)
        if player_cards:
            self.fields['card'].choices =  [(card.id,card.name) for card in player_cards]

class JoinGameForm(forms.Form):
    board_id = forms.CharField(max_length=100)
    player_name = forms.CharField(max_length=100)
