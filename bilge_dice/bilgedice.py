import random
from bilge_dice.models import User, Game, Player, PlayerState

HAND_SIZE = 4

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
        
        hand = generate_hand(player_state)
        qualifiers = generate_qualifiers(player_state)
        score = calculate_score(player_state)
        
        player_ui = PlayerUi(opponent_player, hand, qualifiers, score)
        opponents.append(player_ui)

    return opponents

def get_user_player():
    current_game = get_current_game()

    player = Player.objects.get(is_user=True)
    player_state = PlayerState.objects.get_or_create(game__id=current_game.id,player__id=player.id)[0]
    
    hand = generate_hand(player_state)
    qualifiers = generate_qualifiers(player_state)
    score = calculate_score(player_state)

    player_ui = PlayerUi(player, hand, qualifiers, score)

    return player_ui

def generate_hand(player_state):
    hand = list(player_state.hand)
    dice_rolls = dice_rolls_from_numbers(hand)
    missing_rolls_count = HAND_SIZE - len(dice_rolls)

    for _ in range(missing_rolls_count):
        missing_roll = DiceRoll(None, get_empty_dice_roll_image())
        dice_rolls.append(missing_roll)

    return dice_rolls

def generate_qualifiers(player_state):
    qualifiers = list(player_state.qualifiers)
    dice_rolls=[]

    dice_roll = None
    if 1 in qualifiers:
        dice_roll = DiceRoll(1, get_dice_roll_image(1))
    else:
        dice_roll = DiceRoll(None, get_empty_qualifier_image(1))
    dice_rolls.append(dice_roll)

    if 4 in qualifiers:
        dice_roll = DiceRoll(4, get_dice_roll_image(4))
    else:
        dice_roll = DiceRoll(None, get_empty_qualifier_image(4))
    dice_rolls.append(dice_roll)

    return dice_rolls

def calculate_score(player_state): 
    hand = list(player_state.hand)
    return sum(hand)

def generate_rolls():
    roll_results = []
    for _ in range(6):
        roll = random.randint(1, 6)
        roll_results.append(roll)

    return dice_rolls_from_numbers(roll_results)

def dice_rolls_from_numbers(numbers):
    dice_rolls = []
    for number in numbers:
        dice_roll = DiceRoll(number, get_dice_roll_image(number))
        dice_rolls.append(dice_roll)

    return dice_rolls

def get_dice_roll_image(number):
    if number == 1:
        return "/static/bilge_dice/images/dice_1.gif"
    elif number == 2:
        return "/static/bilge_dice/images/dice_2.gif"
    elif number == 3:
        return "/static/bilge_dice/images/dice_3.gif"
    elif number == 4:
        return "/static/bilge_dice/images/dice_4.gif"
    elif number == 5:
        return "/static/bilge_dice/images/dice_5.gif"
    elif number == 6:
        return "/static/bilge_dice/images/dice_6.gif"
    else:
        return ""

def get_empty_qualifier_image(number):
    if number == 1:
        return "/static/bilge_dice/images/d1.gif"
    elif number == 4:
        return "/static/bilge_dice/images/d4.gif"
    else:
        return "/static/bilge_dice/images/d0.gif"

def get_empty_dice_roll_image():
    return "/static/bilge_dice/images/d0.gif"

class DiceRoll:
  def __init__(self, number, image_url):
    self.number = number
    self.image_url = image_url

class PlayerUi:
  def __init__(self, player, hand, qualifiers, score):
    self.player = player
    self.hand = hand
    self.qualifiers = qualifiers
    self.score = score