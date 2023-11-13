from django.shortcuts import render
from bilge_dice import bilgedice


def home(request):
    login_username = request.POST.get("username")
    if login_username:
        bilgedice.create_user_session(login_username)
        return render_home(request)
    
    if not bilgedice.get_user_session():
        return render_login(request)

    bet = request.POST.get("bet")
    is_start_over = check_start_over(request)
    is_show_results = check_show_results(request)

    if is_start_over:
        # start over after results view
        bilgedice.delete_current_game()
        return render_home(request)

    if bet:
        # selected a bet from welcome view
        bilgedice.new_game(bet)
        return render_game(request)

    if not bilgedice.get_current_game():
        # error?
        return render_home(request)
    
    if is_show_results:
        return render_results(request)

    return render_game(request)


def render_login(request):
    return render(request, "bilge_dice/login.html", {})


def render_home(request):
    user = bilgedice.get_user()
    context = {
        "user": user,
    }
    return render(request, "bilge_dice/home.html", context)

def render_game(request):
    if request.method == "POST":
        if check_selection(request):
            dice_rolls = bilgedice.generate_rolls()
        else:
            dice_rolls = bilgedice.get_rolls()
    else:
        dice_rolls = bilgedice.get_rolls()

    game_state = bilgedice.validate_game_state()
    if game_state == bilgedice.GameState.RESULTS:
        return render_final_user_score(request)

    user = bilgedice.get_user()
    user_player = bilgedice.get_user_player()
    opponents = bilgedice.get_opponents()

    context = {
        "user": user,
        "player": user_player,
        "opponents": opponents,
        "dice_rolls": dice_rolls
    }

    return render(request, "bilge_dice/game.html", context)


def render_final_user_score(request):
    user = bilgedice.get_user()
    user_player = bilgedice.get_user_player()
    results = bilgedice.get_final_results(False)

    context = {
        "user": user,
        "player": user_player,
        "results": results
    }

    return render(request, "bilge_dice/your_score.html", context)


def render_results(request):
    user = bilgedice.get_user()
    user_player = bilgedice.get_user_player()
    results = bilgedice.get_final_results(True)

    bilgedice.delete_current_game()

    context = {
        "user": user,
        "player": user_player,
        "results": results
    }

    return render(request, "bilge_dice/results.html", context)


def check_start_over(request):
    return request.POST.get("new_game")


def check_show_results(request):
    return request.POST.get("show_results")


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