import random
from copy import deepcopy, copy
from tqdm import tqdm, trange
import time
from itertools import permutations, product

BOARD_SIZE = 16
GOOD_CAMELS = {'r', 'b', 'g', 'y', 'p'}
CRAZY_CAMELS = {'k' ,'w'}
CAMEL_DIR = {
    'r': 1,
    'b': 1,
    'g': 1,
    'y': 1,
    'p': 1,
    'k': -1,
    'w': -1
}

class Board():
    def __init__(self):
        self.board = [[] for _ in range(BOARD_SIZE)]
        self.cheering_tiles = [0 for _ in range(BOARD_SIZE)]

    def __deepcopy__(self, memo):
        inst_copy = copy(self)

        inst_copy.board = [pos[:] for pos in self.board]
        inst_copy.cheering_tiles = self.cheering_tiles[:]

        return inst_copy

    def print_board(self):
        for height in reversed(range(len(GOOD_CAMELS) + len(CRAZY_CAMELS))):
            line = ''
            for pos in range(BOARD_SIZE):
                if height < len(self.board[pos]):
                    line += self.board[pos][height].upper()
                else:
                    line += ' '
            print(line)

        print(''.join(['-' for _ in range(BOARD_SIZE)]))
        line = ''
        for i in range(BOARD_SIZE):
            line += str(i)[-1]
        print(line)

        line = ''
        for i in range(BOARD_SIZE):
            if self.cheering_tiles[i] == 1:
                line += '+'
            elif self.cheering_tiles[i] == -1:
                line += '-'
            else:
                line += ' '

        print(line)
        print('Current Leader:', self.leader())

    def leader(self):
        for i in reversed(range(BOARD_SIZE)):
            if self.board[i] and GOOD_CAMELS.intersection(self.board[i]):
                for camel in reversed(self.board[i]):
                    if camel in GOOD_CAMELS:
                        return camel
                
        raise Exception('No good camels found')

    def random_board(self):
        self.board = [[] for _ in range(BOARD_SIZE)]
        self.cheering_tiles = [0 for _ in range(BOARD_SIZE)]

        for camel in GOOD_CAMELS:
            self.place_camel(camel, random.randint(0,2))

        for camel in CRAZY_CAMELS:
            self.place_camel(camel, (0 - random.randint(1,3)) % BOARD_SIZE)

    def place_camel(self, camel, pos):
        self.board[pos] += [camel]

    def place_tile(self, pos, value):
        if value == '+':
            self.cheering_tiles[pos] = 1
        else:
            self.cheering_tiles[pos] = -1

    def move(self, camel, hops):
        # Select correct crazy camel
        if camel in CRAZY_CAMELS:
            white_camel_pos = None
            white_camel_idx = None
            black_camel_pos = None
            black_camel_idx = None
            for pos, camels in enumerate(self.board):
                if 'w' in camels:
                    white_camel_pos = pos
                    white_camel_idx = self.board[pos].index('w')
                if 'k' in camels:
                    black_camel_pos = pos
                    black_camel_idx = self.board[pos].index('k')

            white_carrying = ((white_camel_idx + 1) < len(self.board[white_camel_pos]))
            black_carrying = ((black_camel_idx + 1) < len(self.board[black_camel_pos]))

            # Move the top camel if they are stacked together
            if white_camel_pos == black_camel_pos:
                camel = [camel for camel in self.board[white_camel_pos] if camel in CRAZY_CAMELS][-1]
            elif white_carrying and not black_carrying:
                camel = 'w'
            elif black_carrying and not white_carrying:
                camel = 'k'


        new_pos = None
        for i in range(len(self.board)):
            if camel in self.board[i]:
                camel_idx = self.board[i].index(camel)
                stack = self.board[i][camel_idx:]
                self.board[i] = self.board[i][:camel_idx]
                new_pos = (i + (hops * CAMEL_DIR[camel])) % BOARD_SIZE
                self.board[new_pos] += stack
                break

        if new_pos is None:
            raise Exception(f"Couldn't find camel {camel}")

        # Check for +/- 1 tile
        if self.cheering_tiles[new_pos] != 0:
            step = self.cheering_tiles[new_pos] * CAMEL_DIR[camel]
            step_pos = (new_pos + step) % BOARD_SIZE

            # Do strange hop thing
            if self.cheering_tiles[new_pos] == -1:
                self.board[step_pos] = self.board[new_pos] + self.board[step_pos]
                self.board[new_pos] = []

            else: # normal hops
                self.board[step_pos] = self.board[step_pos] + self.board[new_pos]
                self.board[new_pos] = []


def expected_winner(board: Board):
    players = list(GOOD_CAMELS) + [None]
    winners = {camel: 0 for camel in GOOD_CAMELS}
    trials = 0
    # For dice permutation
    with tqdm(total=174960) as pbar:
        for ig_player in (players):
            small_players = players[:]
            small_players.remove(ig_player)
            
            # For roll permutation
            for camels in (permutations(small_players)):
                for rolls in product(range(1,4), repeat=len(camels)):
                    board_copy = deepcopy(board)
                    trials += 1
                    pbar.update(1)
                    for camel, hops in zip(camels, rolls):
                        if camel is not None:
                            board_copy.move(camel, hops)
                        else:
                            board_copy.move(random.choice(['w', 'k']), hops)
                    winners[board_copy.leader()] += 1

    print('True Camel Odds:')
    for camel, wins in winners.items():
        print(f'\tCamel: {camel}, chance: {(wins/trials)*100}')
                        
def mc_expected_winner(board, iterations=10000):
    """
    Monte Carlo Simulation of the current leg
    """
    random.seed(time.time_ns())
    players = list(GOOD_CAMELS) + [None]
    winners = {camel: 0 for camel in GOOD_CAMELS}

    # For dice permutation
    for _ in trange(iterations):
        board_copy = deepcopy(board)

        small_players = players[:]
        small_players.remove(random.choice(players))
        random.shuffle(small_players)
        for camel in small_players:
            hops = random.randint(1,3)
            if camel is not None:
                board_copy.move(camel, hops)
            else:
                board_copy.move(random.choice(['w', 'k']), hops)
        winners[board_copy.leader()] += 1

    print('Estimated Camel Odds:')
    for camel, wins in winners.items():
        print(f'\tCamel: {camel}, chance: {(wins/iterations)*100}')


if __name__ == "__main__":
    board = Board()
    board.random_board()

    while True:
        board.print_board()
        expected_winner(board)
        mc_expected_winner(board)
        print(f'Camels: {", ".join(GOOD_CAMELS.union(CRAZY_CAMELS))}')
        print('Move a camel eg: b2, g1, k3')
        print('Place a spectator tile. Eg: -3 +13')
        move = input(f'Enter your move: ')

        try:
            hops = int(move[1:])
            camel = move[:1]
        except:
            continue
        if camel in {'+', '-'}:
            board.place_tile(hops, camel)
        else:
            board.move(camel, hops)