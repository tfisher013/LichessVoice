import berserk
from requests_oauthlib import OAuth2Session
import threading

# reads Lichess account token from file account_token.txt
API_TOKEN = ''
with open("account_token.txt") as f:
    API_TOKEN = f.read()

# set up connection to DarcChess account
session = berserk.TokenSession(API_TOKEN)
client = berserk.Client(session=session)

# Lichess api endpoints
CHALLENGE_ENDPOINT = 'https://lichess.org/api/challenge/'

GAME_OVER_CODES = ['mate', 'resign', 'timeout', 'outoftime', 'cheat']


def integrated_game_manager(game_id: str):
    """
    Handles the communication of a game to the user via command line.
    """

    am_white = False
    play_move_thread = None

    for event in client.board.stream_game_state(game_id):

        # check for starting position
        if event['type'] == 'gameFull':
            if event['white']['id'] == client.account.get()['id']:
                play_move_thread = threading.Thread(target=play_move, args=(game_id,))
                play_move_thread.start()
                play_move_thread.join()
                am_white = True
            else:
                print('Waiting for opponent\'s move...')
        # receive opponent's move or end of game
        elif event['type'] == 'gameState':
            if event['status'] in GAME_OVER_CODES:
                print('Game over by '+event['status'] +
                      '. Winner is '+event['winner']+'.')
            else:

                # determine who made the last move
                if (am_white and len(event['moves'].split()) % 2 == 0) or (not am_white and len(event['moves'].split()) % 2 != 0):
                    print('Opponent plays '+event['moves'].split()[-1])
                    play_move(game_id)
                else:
                    print('Waiting for opponent\'s move...')
        # chat message
        elif event['type'] == 'chatLine':
            print(event['username'] + ' says \''+event['text']+'\'')


def play_move(game_id: str):

    move_successful = False
    while not move_successful:
        move = str(input('Enter move: '))
        move_successful = make_move(game_id, move)

        if not move_successful:
            print('Invalid move. Try again.')


def await_game_move(game_id: str, prev_move: str or None):
    """
    Awaits opponent's move in the provided game and returns the move
    when played.

    Parameters:
        game_id (str): The id of the game
        prev_move (str): The last move played (by logged in user)

    Returns:
        The moved played by the opponent
    """

    for game_info in client.board.stream_game_state(game_id):

        if game_info['type'] == 'gameState':
            # case where a move has been played
            if game_info['moves'] != '':
                last_sent_move = game_info['moves'].split()[-1]

                # first check for game being over
                if game_info['status'] in GAME_OVER_CODES:
                    return {'move': last_sent_move, 'win_method': game_info['status'], 'winner': game_info['winner']}

                # case where we are waiting on the opponent to make the first move
                if prev_move is None:
                    if last_sent_move != '':
                        return {'move': last_sent_move}
                # case where we are waiting on the opponent to make a move (not first game move)
                else:
                    if last_sent_move != prev_move:
                        return {'move': last_sent_move}


def challenge_user(player_id: str):
    """
    Issues a challenge to the provided player id.

    Parameters:
        player_id (str): the id of the player to challenge (non-empty)
    """
    print('Challenging '+player_id+'...')

    try:
        challenge_response = client.challenges.create(player_id, rated=False)
        return challenge_response['challenge']['id']
    except Exception:
        return None


def get_self_id():
    """
    Returns the id of the logged in player.
    """
    return client.account.get()['id']


def is_game_over(game_id: str):
    """
    Checks whether the game indicated by the id has completed or not.

    Parameters:
        game_id (str): the id of the game to query

    Returns:
        A dict of the following form
            {'game_over': True/False,
             'winner': 'white'/'black'/None,
             'win_method': str/None
            }
    """

    for event in client.board.stream_game_state(game_id):
        if event['type'] == 'gameState':
            if event['status'] in GAME_OVER_CODES:
                return {'game_over': True, 'winner': event['winner'], 'win_method': event['status']}
            else:
                return {'game_over': False, 'winner': None, 'win_method': None}


def make_move(game_id: str, move: str):
    """
    Makes the provided move in the game associated with the given id.

    Parameters:
        game_id (str): the id of the ongoing game in which to make the move
        move (str): the move to make

    Returns:
        True if the move was made successfully, False otherwise
    """
    try:
        client.board.make_move(game_id, move)
        return True
    # TODO how to identify what went wrong (invalid move, lost connection, etc.)?
    except berserk.exceptions.ResponseError:
        return False


def get_opponents_color(game_id: str):
    """
    Returns the color of the opponent in the provide game id.

    Parameters:
        game_id (str): The game id

    Returns
        'white' or 'black'
    """

    for game_info in client.board.stream_game_state(game_id):
        if game_info['white']['id'] == get_self_id():
            return 'black'
        return 'white'


def view_user_info():
    """
    Prints the Lichess info of the logged in user.
    """
    print(str(client.account.get()))


def wait_for_any_challenge_acceptance():
    """
    Wait for any current challenge made by the logged in player to be accpted
    and return the id of the started game.

    Returns:
        The id of an accepted challenge, or None if there are no current challenges.
    """

    for event in client.board.stream_incoming_events():
        if event['type'] == 'gameStart':
            return event['game']['gameId']


def wait_for_known_challenge_acceptance(challenge_id: str = ''):
    """
    Waits for the challenge associated with the provided challenge id to be accepted.
    Returns an indication of the success of the challenge acceptance.

    Parameters:
        challenge_id (str): the id of the challenge waiting to be accepted

    Returns:
        True if the challenge was accepted, False if the challenge was cancelled, declined,
        or if there is no current challenge with the provided id.
    """

    for event in client.board.stream_incoming_events():
        if event['type'] == 'gameStart' and event['game']['gameId'] == challenge_id:
            return True
        if event['type'] == 'challengeDeclined' and event['challenge']['id'] == challenge_id:
            return False


def wait_for_challenge_offered():
    """
    Wait for the first offered challenge and return the game id.
    """

    for event in client.board.stream_incoming_events():
        print(event)
        if event['type'] == 'challenge':
            client.challenges.accept(event['challenge']['id'])
            return event['challenge']['id']
