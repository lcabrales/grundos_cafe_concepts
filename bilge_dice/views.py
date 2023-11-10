from django.shortcuts import render
from bilge_dice.models import User
from bilge_dice import bilgedice

def home(request):
    is_new_game = check_new_game(request)

    if is_new_game:
        bilgedice.new_game()

    if request.method == "POST" and not is_new_game:
        if check_selection(request):
            dice_rolls = bilgedice.generate_rolls()
        else:
            dice_rolls = bilgedice.get_rolls()
    else:
        dice_rolls = bilgedice.get_rolls()

    if not dice_rolls:
        results = bilgedice.get_final_results()
        return render_results(request, results)

    user = bilgedice.get_user()
    user_player = bilgedice.get_user_player()
    opponents = bilgedice.get_opponents()

    context = {
        "user": user,
        "player": user_player,
        "opponents": opponents,
        "dice_rolls": dice_rolls
    }

    return render(request, "bilge_dice/home.html", context)


def render_results(request, results):
    user = bilgedice.get_user()

    context = {
        "user": user,
        "results": results
    }

    return render(request, "bilge_dice/results.html", context)


def check_new_game(request):
    return request.POST.get("new_game")


def check_selection(request):
    numbers_to_keep = []

    for index in range(6):
        dice_number = request.POST.get(f"roll_{index}", 0)
        if dice_number != 0:
            numbers_to_keep.append(dice_number)

    if not numbers_to_keep:
        return False
    
    bilgedice.keep_user_hand(numbers_to_keep)
    return True