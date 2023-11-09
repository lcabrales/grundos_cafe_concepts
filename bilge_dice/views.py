from django.shortcuts import render
from bilge_dice.models import User
from bilge_dice import bilgedice

def home(request):
    user = bilgedice.get_user()
    user_player = bilgedice.get_user_player()
    opponents = bilgedice.get_opponents()
    dice_rolls = bilgedice.generate_rolls()
    context = {
        "user": user,
        "player": user_player,
        "opponents": opponents,
        "rolls": dice_rolls
    }
    return render(request, "bilge_dice/home.html", context)