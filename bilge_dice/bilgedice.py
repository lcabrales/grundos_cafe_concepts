import random
from bilge_dice.models import User, Game, Player, PlayerState

def get_user():
    return User.objects.first()

def get_current_game():
    user = get_user()
    current_game = Game.objects.get_or_create(user__id=user.id)
    return current_game[0]

def get_opponents():
    current_game = get_current_game()
    opponent_players = Player.objects.filter(is_user=False)
    
    opponents = []
    for opponent_player in opponent_players:
        player_state = PlayerState.objects.get_or_create(game__id=current_game.id, player__id=opponent_player.id)[0]
        opponents.append(player_state)

    return opponents

def get_user_player():
    current_game = get_current_game()

    user_player = Player.objects.get(is_user=True)
    print(user_player.id)
    user_player_state = PlayerState.objects.get_or_create(game__id=current_game.id,player__id=user_player.id)
    
    return user_player_state

def generate_rolls():
    roll_results = []
    for _ in range(6):
        roll = random.randint(1, 6)
        roll_results.append(roll)
    return roll_results
    