import random
from bilge_dice.models import User, Session, Game, Player, PlayerState, UserBilgeDice
from enum import Enum

TOTAL_DICE_COUNT = 6

HAND_SIZE = 4
QUALIFIERS_SIZE = 2

FIRST_QUALIFIER = 1
SECOND_QUALIFIER = 4

NPS_WIN_MULTIPLIER = 4

RNG_AVATAR_SCORE = 24
WIN_STREAK_AVATAR_COUNT = 10


def get_user_session():
    return Session.objects.first()


def create_user_session(username):
    Session.objects.all().delete()

    user, created = User.objects.get_or_create(username=username)
    session = Session(user_id=user.id)
    session.save()


def get_user():
    session = get_user_session()

    user = User.objects.first()
    if session:
        user = session.user

    return user


def get_current_game():
    user = get_user()
    current_game = Game.objects.filter(user_id=user.id).first()
    return current_game


def delete_current_game():
    game = get_current_game()
    if game:
        game.delete()


def new_game(bet_string):
    delete_current_game()

    bet = get_bet_value(bet_string)

    user = get_user()
    new_game = Game(user_id=user.id, bet=bet)
    new_game.save()

    update_user_nps(-bet)


def get_bet_value(bet_string):
    return int(bet_string.split()[0])


def get_user_player_db():
    return Player.objects.get(is_user=True)


def get_user_bilge_dice():
    user = get_user_player_db()
    user_bilge_dice, created = UserBilgeDice.objects.get_or_create(user_id=user.id)
    return user_bilge_dice


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

        if is_player_game_over(opponent):
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


def get_final_results(is_final_result):
    game = get_current_game()
    user_player = get_user_player_db()
    user_player_state = get_player_state(user_player)
    user_score = calculate_score(user_player_state)

    opponent_players = get_opponents_db()

    scores_to_beat = []
    opponents_results = []
    for opponent in opponent_players:
        player_state = get_player_state(opponent)
        is_qualified = is_player_qualified(opponent)

        opponent_score = calculate_score(player_state)

        if is_qualified:
            scores_to_beat.append(opponent_score)

        opponent_image = opponent.image
        if opponent_score <= user_score or not is_qualified:
            opponent_image = opponent.image_sad

        opponent_result = OpponentResult(opponent.name, opponent_score, is_qualified, opponent_image)
        opponents_results.append(opponent_result)

    opponent_highest_score = 0
    if scores_to_beat:
        opponent_highest_score = max(scores_to_beat)
    
    game_result = 0
    nps_won = 0
    if not is_player_qualified(user_player):
        game_result = GameResult.DID_N0T_QUALIFY
        updateWinStreak(False)
    elif user_score > opponent_highest_score:
        game_result = GameResult.WON
        nps_won = game.bet * NPS_WIN_MULTIPLIER
    elif user_score == opponent_highest_score:
        game_result = GameResult.TIED
        nps_won = game.bet
    else:
        game_result = GameResult.LOST

    print(f"final score: {user_score}")
    print(f"opponents_results: {opponents_results}")

    results = FinalResults(user_score, game_result, nps_won, opponents_results)

    if is_final_result:
        updateWinStreak(game_result == GameResult.WON)
        if nps_won > 0:
            update_user_nps(nps_won)
        checkAvatarsConditions(results)

    return results


def checkAvatarsConditions(results):
    user = get_user_player_db()

    # RNG score avatar
    if results.user_score == RNG_AVATAR_SCORE:
        check_rng_avatar()

    user_bilge_dice = get_user_bilge_dice()
    if user_bilge_dice.win_streak >= WIN_STREAK_AVATAR_COUNT:
        grant_lucky_streak_avatar()


def updateWinStreak(is_win):
    user_bilge_dice = get_user_bilge_dice()

    if is_win:
        user_bilge_dice.win_streak += 1
    else:
        user_bilge_dice.win_streak = 0

    print(f"user_bilge_dice.win_streak: {user_bilge_dice.win_streak}")

    user_bilge_dice.save()


def is_player_game_over(player):
    player_state = get_player_state(player)
    return player_state.is_game_over or player_state.rolls_left <= 0

def is_player_qualified(player):
    player_state = get_player_state(player)
    qualifiers = string_to_numbers_list(player_state.qualifiers)

    return FIRST_QUALIFIER in qualifiers and SECOND_QUALIFIER in qualifiers


def validate_game_state():
    game = get_current_game()

    if not game:
        return GameState.WELCOME
    
    player = get_user_player_db()

    if is_player_game_over(player):
        return GameState.RESULTS

    return GameState.GAME
    

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


def update_user_nps(nps):
    user = get_user()
    user.nps += nps
    user.save()
    pass


def check_rng_avatar():
    if random.randint(0, 1) >= 1:
        grant_rng_avatar()


def grant_rng_avatar():
    print("grant_rng_avatar")
    pass


def grant_lucky_streak_avatar():
    print("grant_lucky_streak_avatar")
    pass


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


class OpponentResult:
    def __init__(self, name, score, is_qualified, image):
        self.name = name
        self.score = score
        self.is_qualified = is_qualified
        self.image = image


class FinalResults:
  def __init__(self, user_score, game_result, nps_won, opponents_results):
    self.user_score = user_score
    self.game_result = game_result
    self.nps_won = nps_won
    self.opponents_results = opponents_results


class GameState(Enum):
    WELCOME = 0
    GAME = 1
    RESULTS = 2


class GameResult(Enum):
    DID_N0T_QUALIFY = -2
    LOST = -1
    TIED = 0
    WON = 1

