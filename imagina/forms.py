from imagina.models import NUMBER_OF_PLAYERS_CHOICES, Deck, Card
from django import forms

class NewGameForm(forms.Form):
    player_name = forms.CharField(max_length=100)
    number_of_players = forms.ChoiceField(choices=NUMBER_OF_PLAYERS_CHOICES)
    deck =  forms.ModelChoiceField(queryset=Deck.objects.all(), empty_label=None)

class ChooseCardForm(forms.Form):
    card = forms.ModelChoiceField(None, empty_label=None)
    def __init__(self, *args, **kwargs):
        player_cards = kwargs.pop('player_cards', None)
        super(forms.Form, self).__init__(*args, **kwargs)
        if player_cards:
            self.fields['card'].queryset = player_cards   

class NewRoundForm(forms.Form):
    phrase = forms.CharField(max_length=100, required=True)
    card = forms.ModelChoiceField(queryset=Card.objects.none(), empty_label=None, required=True)
    def __init__(self, *args, **kwargs):
        player_cards = kwargs.pop('player_cards', None)
        super(NewRoundForm, self).__init__(*args, **kwargs)
        if player_cards:
            self.fields['card'].queryset = player_cards 

class JoinGameForm(forms.Form):
    board_id = forms.CharField(max_length=100)
    player_name = forms.CharField(max_length=100)
