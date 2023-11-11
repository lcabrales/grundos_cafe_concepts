import random
from bilge_dice.models import User, Game, Player, PlayerState

TOTAL_DICE_COUNT = 6
HAND_SIZE = 4
QUALIFIERS_SIZE = 2
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


def get_user_player_db():
    return Player.objects.get(is_user=True)


def get_opponents_db():
    return Player.objects.filter(is_user=False)


def get_player_state(player):
    current_game = get_current_game()
    player_state, created = PlayerState.objects.get_or_create(game_id=current_game.id,player_id=player.id)
    return player_state


def get_opponents():
    opponent_players = get_opponents_db()
    
    opponents = []
    for opponent_player in opponent_players:
        player_state = get_player_state(opponent_player)
        
        hand = generate_hand(player_state)
        qualifiers = generate_qualifiers(player_state)
        score = calculate_score(player_state)
        
        player_ui = PlayerUi(opponent_player, hand, qualifiers, score)
        opponents.append(player_ui)

    return opponents


def get_user_player():
    player = get_user_player_db()
    player_state = get_player_state(player)
    
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


def roll_dice(amount):
    roll_results = []
    for _ in range(amount):
        roll = random.randint(1, TOTAL_DICE_COUNT)
        roll_results.append(roll)
    return roll_results

def generate_rolls():
    player = get_user_player_db()
    player_state = get_player_state(player)
    
    rolls_left = player_state.rolls_left
    print(f"rolls_left = {rolls_left}")
    roll_results = roll_dice(rolls_left)

    game = get_current_game()
    game.rolls = numbers_list_to_string(roll_results)
    game.save()

    return dice_rolls_from_numbers(roll_results)


def keep_user_hand(string_numbers):
    player = get_user_player_db()
    keep_player_hand(player, string_numbers)
    keep_opponents_hand(len(string_numbers))
    

def keep_player_hand(player, string_numbers):
    if not string_numbers:
        return
    
    update_player_state(player, string_to_numbers_list(string_numbers))


def keep_opponents_hand(amount_to_keep):
    opponent_players = get_opponents_db()

    for opponent in opponent_players:
        player_amount_to_keep = amount_to_keep

        player_state = get_player_state(opponent)

        if player_state.is_game_over or player_state.rolls_left <= 0:
            continue

        qualifiers = string_to_numbers_list(player_state.qualifiers)
        need_first_qualifier = FIRST_QUALIFIER not in qualifiers
        need_second_qualifier = SECOND_QUALIFIER not in qualifiers

        roll_results = roll_dice(player_state.rolls_left)

        rolls_to_keep = []
        if need_first_qualifier and FIRST_QUALIFIER in roll_results and player_amount_to_keep > 0:
            rolls_to_keep.append(FIRST_QUALIFIER)
            roll_results.remove(FIRST_QUALIFIER)
            player_amount_to_keep -= 1

        if need_second_qualifier and SECOND_QUALIFIER in roll_results and player_amount_to_keep > 0:
            rolls_to_keep.append(SECOND_QUALIFIER)
            roll_results.remove(SECOND_QUALIFIER)
            player_amount_to_keep -= 1

        if player_amount_to_keep > 0:
            sorted_rolls = sorted(roll_results, reverse=True)
            highest_rolls = sorted_rolls[:player_amount_to_keep]
            for roll in highest_rolls:
                rolls_to_keep.append(roll)

        keep_player_hand(opponent, numbers_list_to_string(rolls_to_keep))


def update_player_state(player, numbers):
    player_state = get_player_state(player)

    player_state.rolls_left -= len(numbers)
    
    print(f"numbers: {numbers}")
    print(f"hand before: {player_state.hand}")
    print(f"qualifiers before: {player_state.qualifiers}")

    qualifiers = string_to_numbers_list(player_state.qualifiers)

    if FIRST_QUALIFIER in numbers and not FIRST_QUALIFIER in qualifiers:
        numbers.remove(FIRST_QUALIFIER)
        player_state.qualifiers += str(FIRST_QUALIFIER)

    if SECOND_QUALIFIER in numbers and not SECOND_QUALIFIER in qualifiers:
        numbers.remove(SECOND_QUALIFIER)
        player_state.qualifiers += str(SECOND_QUALIFIER)

    if player_state.rolls_left <= 0:
        player_state.is_game_over = True

    temp_hand = player_state.hand + numbers_list_to_string(numbers)
    player_state.hand = temp_hand[:HAND_SIZE]
        
    print(f"hand: {player_state.hand}")
    print(f"qualifiers: {player_state.qualifiers}")
    player_state.save()


def get_final_results():
    user_player = get_user_player_db()
    user_player_state = get_player_state(user_player)
    user_score = calculate_score(user_player_state)

    opponent_players = get_opponents_db()

    scores_to_beat = []
    for opponent in opponent_players:
        player_state = get_player_state(opponent)
        is_qualified = is_player_qualified(opponent)

        if not is_qualified:
            continue

        scores_to_beat.append(calculate_score(player_state))

    opponent_highest_score = 0
    if scores_to_beat:
        opponent_highest_score = max(scores_to_beat)
    
    game_result = 0
    if not is_player_qualified(user_player):
        game_result = -2
    elif user_score > opponent_highest_score:
        game_result = 1
    elif user_score == opponent_highest_score:
        game_result = 0
    else:
        game_result = -1

    print(f"final score: {user_score}")

    return FinalResults(user_score, game_result)


def is_player_qualified(player):
    player_state = get_player_state(player)
    qualifiers = string_to_numbers_list(player_state.qualifiers)

    return FIRST_QUALIFIER in qualifiers and SECOND_QUALIFIER in qualifiers


def validate_game_state(dice_rolls):
    player = get_user_player_db()
    player_state = get_player_state(player)
    
    return dice_rolls and not player_state.is_game_over
    

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
  def __init__(self, user_score, game_result):
    self.user_score = user_score
    self.game_result = game_result