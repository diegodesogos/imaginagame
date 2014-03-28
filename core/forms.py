from core.models import NUMBER_OF_PLAYERS_CHOICES, Deck
from django import forms

class NewGameForm(forms.Form):
    player_name = forms.CharField(max_length=100)
    number_of_players = forms.ChoiceField(choices=NUMBER_OF_PLAYERS_CHOICES)
    deck =  forms.ModelChoiceField(queryset=Deck.objects.all(), empty_label=None)
    
