# Create your views here.
from django.shortcuts import render_to_response, get_object_or_404
from django.http import HttpResponse
from core.models import Game

def index(request):
    latest_game_list = Game.objects.all().order_by('-creation_date')[:5]
    return render_to_response('core/index.html', {'latest_game_list': latest_game_list})

def detail(request, game_id):
    p = get_object_or_404(Game, pk=game_id)
    return render_to_response('core/detail.html', {'game': p})

def results(request, game_id):
    return HttpResponse("You're looking at the results of game %s." % game_id)

def vote(request, game_id):
    return HttpResponse("You're playing on game %s." % game_id)