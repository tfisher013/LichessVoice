from typing import List

def run_move_checker(all_moves_list: List[str]) -> None:
    """
    Allows for checking whether entered moves are present in the provided list.
    
    Parametrs:
    - all_moves_list [str]: A list of strings with all possible chess moves.
    """

    while True:
        print('Enter a move in algebraic notation to see if it\'s included, or enter exit to quit.')
        move = input('  Enter move: ')
        if move.lower == 'exit' or move.lower == 'quit':
            break
        elif move in all_moves_list is True:
            print(move + ' is included in the list of moves.')
        else:
            print('Nice catch! ' + move + ' is not included in the list of moves.')


def get_all_moves() -> List[str]:
    """
    Creates a list of strings representing all possible chess moves
    in standard algebraic notation.
    
    Returns:
    [str]: A list of strings with all possible chess moves.
    """
        
    pieces = ['K', 'Q', 'R', 'B', 'N']
    ranks = ['1', '2', '3', '4', '5', '6', '7', '8']
    files = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']

    all_moves_list = []

    # movement moves
    for rank in ranks:
        for file in files:

            # piece moves
            for piece in pieces:
                move = piece + file + rank
                all_moves_list.append(move)

            # pawn moves
            if rank != '1' and rank != '8':
                all_moves_list.append(file + rank)

    # captures
    for rank in ranks:
        for file in files:

            # piece captures
            for piece in pieces:
                all_moves_list.append(piece + 'x' + file + rank)

            # pawn captures
            if rank != '1' and rank != '8':
                if file == 'a':
                    white_move = file + 'xb' + str(int(rank) + 1)
                    black_move = file + 'xb' + str(int(rank) - 1)
                    all_moves_list.extend([white_move, black_move])
                elif file == 'h':
                    white_move = file + 'xg' + str(int(rank) + 1)
                    black_move = file + 'xg' + str(int(rank) - 1)
                    all_moves_list.extend([white_move, black_move])
                else:
                    file_index = files.index(file)
                    white_move_1 = file + 'x' + files[file_index + 1] + str(int(rank) + 1)
                    white_move_2 = file + 'x' + files[file_index - 1] + str(int(rank) + 1)
                    black_move_1 = file + 'x' + files[file_index + 1] + str(int(rank) - 1)
                    black_move_2 = file + 'x' + files[file_index - 1] + str(int(rank) - 1)
                    all_moves_list.extend([white_move_1, white_move_2, black_move_1, black_move_2])

    # promotions
    for piece in pieces:
        for file in files:
            if piece != 'K':

                # peaceful promotions
                white_promotion = file + '8=' + piece
                black_promotion = file + '1=' + piece

                all_moves_list.extend([white_promotion, black_promotion])

                # # capture promotions
                # if file == 'a':
                #     white_move = file + 'xb' + str(int(rank) + 1)
                #     black_move = file + 'xb' + str(int(rank) - 1)
                #     all_moves.extend([white_move, black_move])
                # elif file == 'h':
                #     white_move = file + 'xg' + str(int(rank) + 1)
                #     black_move = file + 'xg' + str(int(rank) - 1)
                #     all_moves.extend([white_move, black_move])
                # else:
                #     file_index = files.index(file)
                #     white_move_1 = file + 'x' + files[file_index + 1] + str(int(rank) + 1)
                #     white_move_2 = file + 'x' + files[file_index - 1] + str(int(rank) + 1)
                #     black_move_1 = file + 'x' + files[file_index + 1] + str(int(rank) - 1)
                #     black_move_2 = file + 'x' + files[file_index - 1] + str(int(rank) - 1)
                #     all_moves.extend([white_move_1, white_move_2, black_move_1, black_move_2])

    # castling
    all_moves_list.append('O-O')
    all_moves_list.append('O-O-O')

    # as any move can be a check, create a duplicate of every move
    # with the addition of a check
    all_moves_list.extend([move + '+' for move in all_moves_list])

    # print stats
    print("All moves:")
    for move in all_moves_list:
        print(move)
    print('Number of moves: '+str(len(all_moves_list)))

    return all_moves_list