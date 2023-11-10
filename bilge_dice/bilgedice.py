import random
from bilge_dice.models import User, Game, Player, PlayerState

TOTAL_DICE_COUNT = 6
HAND_SIZE = 4
FIRST_QUALIFIER = 1
SECOND_QUALIFIER = 4

def get_user():
    return User.objects.first()


def get_current_game():
    user = get_user()
    current_game, created = Game.objects.get_or_create(user_id=user.id)
    return current_game


def new_game():
    game = get_current_game()
    game.delete()


def get_opponents():
    current_game = get_current_game()
    opponent_players = Player.objects.filter(is_user=False)
    
    opponents = []
    for opponent_player in opponent_players:
        player_state, created = PlayerState.objects.get_or_create(game_id=current_game.id, player_id=opponent_player.id)
        
        hand = generate_hand(player_state)
        qualifiers = generate_qualifiers(player_state)
        score = calculate_score(player_state)
        
        player_ui = PlayerUi(opponent_player, hand, qualifiers, score)
        opponents.append(player_ui)

    return opponents


def get_user_player():
    current_game = get_current_game()

    player = Player.objects.get(is_user=True)
    player_state, created = PlayerState.objects.get_or_create(game_id=current_game.id,player_id=player.id)
    
    hand = generate_hand(player_state)
    qualifiers = generate_qualifiers(player_state)
    score = calculate_score(player_state)

    player_ui = PlayerUi(player, hand, qualifiers, score)

    return player_ui


def generate_hand(player_state):
    print(f"generate hand: {player_state.hand}")
    hand = string_to_numbers_list(player_state.hand)
    dice_rolls = dice_rolls_from_numbers(hand)
    missing_rolls_count = HAND_SIZE - len(dice_rolls)

    for _ in range(missing_rolls_count):
        missing_roll = DiceRoll(None, get_empty_dice_roll_image())
        dice_rolls.append(missing_roll)

    return dice_rolls


def generate_qualifiers(player_state):
    qualifiers = string_to_numbers_list(player_state.qualifiers)
    dice_rolls=[]

    dice_roll = None
    if FIRST_QUALIFIER in qualifiers:
        dice_roll = DiceRoll(FIRST_QUALIFIER, get_dice_roll_image(FIRST_QUALIFIER))
    else:
        dice_roll = DiceRoll(None, get_empty_qualifier_image(FIRST_QUALIFIER))
    dice_rolls.append(dice_roll)

    if SECOND_QUALIFIER in qualifiers:
        dice_roll = DiceRoll(SECOND_QUALIFIER, get_dice_roll_image(SECOND_QUALIFIER))
    else:
        dice_roll = DiceRoll(None, get_empty_qualifier_image(SECOND_QUALIFIER))
    dice_rolls.append(dice_roll)

    return dice_rolls


def calculate_score(player_state): 
    hand = string_to_numbers_list(player_state.hand)
    return sum(hand)


def get_rolls():
    current_game = get_current_game()
    rolls = current_game.rolls

    if not rolls:
        return generate_rolls()
    
    return dice_rolls_from_numbers(map(int, rolls))


def generate_rolls():
    current_game = get_current_game()
    player = Player.objects.get(is_user=True)
    player_state, created = PlayerState.objects.get_or_create(game_id=current_game.id,player_id=player.id)
    
    rolls_left = TOTAL_DICE_COUNT - len(player_state.hand) - len(player_state.qualifiers)
    print(f"rolls_left = {rolls_left}")

    roll_results = []
    for _ in range(rolls_left):
        roll = random.randint(1, TOTAL_DICE_COUNT)
        roll_results.append(roll)

    game = get_current_game()
    game.rolls = numbers_list_to_string(roll_results)
    game.save()

    return dice_rolls_from_numbers(roll_results)


def keep_user_hand(string_numbers):
    if not string_numbers:
        return
    
    player = Player.objects.get(is_user=True)
    update_player_state(player, string_to_numbers_list(string_numbers))
    

def update_player_state(player, numbers):
    current_game = get_current_game()
    player_state = PlayerState.objects.get(game_id=current_game.id,player_id=player.id)
    
    print(f"numbers: {numbers}")
    print(f"hand before: {player_state.hand}")
    print(f"qualifiers before: {player_state.qualifiers}")

    qualifiers = string_to_numbers_list(player_state.qualifiers)

    if FIRST_QUALIFIER in numbers:
        numbers.remove(FIRST_QUALIFIER)
        player_state.qualifiers += str(FIRST_QUALIFIER)

    if SECOND_QUALIFIER in numbers and not SECOND_QUALIFIER in qualifiers:
        numbers.remove(SECOND_QUALIFIER)
        player_state.qualifiers += str(SECOND_QUALIFIER)

    player_state.hand += numbers_list_to_string(numbers)
    print(f"hand: {player_state.hand}")
    print(f"qualifiers: {player_state.qualifiers}")
    player_state.save()


def get_final_results():
    current_game = get_current_game()
    player = Player.objects.get(is_user=True)
    player_state, created = PlayerState.objects.get_or_create(game_id=current_game.id,player_id=player.id)
    
    score = calculate_score(player_state)

    qualifiers = string_to_numbers_list(player_state.qualifiers)
    is_victory = FIRST_QUALIFIER in qualifiers and SECOND_QUALIFIER in qualifiers

    print(f"final score: {score}")

    return FinalResults(score, is_victory)


def string_to_numbers_list(string):
    return [int(number) for number in string]


def numbers_list_to_string(numbers):
    return ''.join(map(str, numbers))


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


class FinalResults:
  def __init__(self, user_score, is_victory):
    self.user_score = user_score
    self.is_victory = is_victory