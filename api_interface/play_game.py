from api_util_functions import *

def make_challenge_game():
    """
    Prompts the user for a Lichess username, and then challenges
    the user to a game.
    """

    opponent_username = ''
    while opponent_username == '':
        opponent_username = str(input('Enter opponent\'s username: '))

    challenge_id = challenge_user(opponent_username)
    if challenge_id is None:
        print('Error challenging '+opponent_username+'. Aborting.')
        return

    # await challenge to be accepted
    wait_for_known_challenge_acceptance(challenge_id)

    # start game manager
    integrated_game_manager(challenge_id)

def accept_challenge_game():
    game_id = wait_for_challenge_offered()

    # start game manager
    integrated_game_manager(game_id)


if __name__ == "__main__":

    make_challenge_game()

