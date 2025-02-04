import chess
import random
import logging
import math

logger = logging.getLogger(__name__)

PAWN_TO_ELO = 100
STD = 50
BASE_ELO = 3000
MAX_VARIATION = 200
AVERAGE_MOVES = 40
TIME_DOUBLING_ELO = 200

# Define removable pieces with positional values
piece_values = {
    chess.QUEEN: 9,
    chess.ROOK: 5,
    chess.BISHOP: 3,
    chess.KNIGHT: 3,
    chess.PAWN: 1
}


def get_positional_multiplier(square, piece_type):
    """Returns positional weight multiplier for a piece on a given square."""
    file = chess.square_file(square)
    rank = chess.square_rank(square)
    if rank >= 4:
        file = 7 - file

    if piece_type == chess.PAWN and file in [3, 4, 5]:
        return 1.2
    elif piece_type == chess.KNIGHT and file == 6:
        return 1.1
    elif piece_type == chess.ROOK and file == 7:
        return 1.2
    return 1.0


def generate_odds_fen(opponent_elo, num_games, bot_score, initial_time, increment, pawn_to_elo=PAWN_TO_ELO, variation_std=STD,
                      max_variation=MAX_VARIATION, base_elo=BASE_ELO, average_moves=AVERAGE_MOVES, time_doubling_elo=TIME_DOUBLING_ELO):
    """
    Generates a FEN with random color and controlled variation.
    variation_std: standard deviation for Elo adjustment (controls position difficulty spread)
    """
    delta = (2 * bot_score - num_games) * (400.0 / (num_games + 10))
    adjusted_elo = opponent_elo - delta

    # Apply time control adjustment
    base_initial = 180  # Base initial time (3 minutes)
    base_increment = 2  # Base increment (2 seconds)
    base_time = base_initial + base_increment * average_moves
    current_time = initial_time + increment * average_moves
    current_time = max(1, current_time)  # Avoid log of zero or negative

    time_ratio = current_time / base_time
    time_adjustment = time_doubling_elo * math.log(time_ratio, 2)  # Logarithmic scaling with base 2
    time_adjusted_elo = adjusted_elo + time_adjustment

    # Apply variation with normal distribution
    elo_adjustment = random.gauss(0, variation_std)
    elo_adjustment = max(-max_variation, min(max_variation, elo_adjustment))
    effective_elo = time_adjusted_elo + elo_adjustment
    logger.info(f"Opponent Elo: {opponent_elo}, Adjusted Elo: {adjusted_elo}, Time Adjusted Elo: {time_adjusted_elo} "
                f"Effective Elo: {effective_elo}")
    S = max(0, (base_elo - effective_elo) / pawn_to_elo)

    # Random color selection
    bot_color = random.choice([chess.WHITE, chess.BLACK])
    back_rank = 0 if bot_color == chess.WHITE else 7
    pawn_rank = 1 if bot_color == chess.WHITE else 6

    # Generate all possible removable pieces with weighted values
    removable_pieces = []
    # Back rank pieces
    for file, piece_type in [(0, chess.ROOK), (1, chess.KNIGHT), (2, chess.BISHOP),
                             (3, chess.QUEEN), (5, chess.BISHOP), (6, chess.KNIGHT),
                             (7, chess.ROOK)]:
        square = chess.square(file, back_rank)
        multiplier = get_positional_multiplier(square, piece_type)
        removable_pieces.append((square, piece_values[piece_type] * multiplier))

    # Pawns
    for file in range(8):
        square = chess.square(file, pawn_rank)
        multiplier = get_positional_multiplier(square, chess.PAWN)
        removable_pieces.append((square, piece_values[chess.PAWN] * multiplier))

    # Greedy removal with shuffled priority
    random.shuffle(removable_pieces)

    removed_squares = []
    current_sum = -0.35

    for square, value in removable_pieces:
        if current_sum + value < S:
            removed_squares.append(square)
            current_sum += value
        if current_sum >= S:  # Allow slight over-removal
            break

    # Create board and apply removals
    board = chess.Board()
    for square in removed_squares:
        board.remove_piece_at(square)

    # Set turn to opponent and preserve castling rights
    return board.fen(), bot_color


def get_expected_elo(fen, bot_color, pawn_to_elo=PAWN_TO_ELO, base_elo=BASE_ELO):
    """Calculates expected Elo considering piece positions and values"""
    board = chess.Board(fen)
    total_penalty = 0

    for square in board.piece_map():
        piece = board.piece_at(square)
        if piece is None or piece.piece_type == chess.KING:
            continue
        piece_type = piece.piece_type
        multiplier = get_positional_multiplier(square, piece_type)
        total_penalty += piece_values[piece_type] * multiplier * (1 if piece.color != bot_color else -1)

    return base_elo - pawn_to_elo * total_penalty


if __name__ == "__main__":
    # Example usage
    elo = 2000
    # un = set()
    # for _ in range(100):
    #     fen, color = generate_odds_fen(elo)
    #     un.add((fen, color))
    # print(f"Unique FENs: {len(un)}")
    fen, color = generate_odds_fen(elo, 10, 8, 60, 1)
    print(f"Generated FEN for {elo} Elo: {fen}")
    expected_elo = get_expected_elo(fen, color)
    print(f"Expected Elo: {expected_elo}")
    print(f"Color: {'White' if color == chess.WHITE else 'Black'}")
    print("Done.")
