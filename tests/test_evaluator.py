"""
Tests for position evaluators (evaluator package) and Position.get_piece_counts.

Builds custom positions and checks evaluation scores against hand-calculated
expectations.

Run with: python3 -m tests.test_evaluator
"""

from position.base import (
    BLACK,
    BISHOP,
    EMPTY,
    KING,
    KNIGHT,
    PAWN,
    Position,
    QUEEN,
    ROOK,
    WHITE,
)
from position.matrix import MatrixPosition
from evaluator.base import Evaluator, MATE_SCORE
from evaluator.simple import PieceCountEvaluator
from evaluator.weighted import MaterialEvaluator

EVALUATORS = [
    ("PieceCountEvaluator", PieceCountEvaluator()),
    ("MaterialEvaluator", MaterialEvaluator()),
]

INITIAL_BACK_RANK = [ROOK, KNIGHT, BISHOP, QUEEN, KING, BISHOP, KNIGHT, ROOK]


def initial_board_with(changes: dict[tuple[int, int], int]) -> list[list[int]]:
    """
    Builds a standard initial board with the given square modifications.

    Each change maps a (row, col) square to a piece value (EMPTY to remove).
    """
    board = [
        INITIAL_BACK_RANK.copy(),
        [PAWN] * 8,
        [EMPTY] * 8,
        [EMPTY] * 8,
        [EMPTY] * 8,
        [EMPTY] * 8,
        [-PAWN] * 8,
        [-piece for piece in INITIAL_BACK_RANK],
    ]
    for (row, col), piece in changes.items():
        board[row][col] = piece
    return board


def make_position(board: list[list[int]], active_color: str = WHITE) -> MatrixPosition:
    return MatrixPosition(
        board=board,
        active_color=active_color,
        castling_rights="KQkq",
        en_passant_square=None,
        halfmove_clock=0,
        fullmove_number=1,
        history=[]
    )


def make_board(pieces: dict[tuple[int, int], int]) -> list[list[int]]:
    board = [[EMPTY] * 8 for _ in range(8)]
    for (row, col), piece in pieces.items():
        board[row][col] = piece
    return board


def play_moves(
    position: MatrixPosition,
    moves: list[tuple[tuple[int, int], tuple[int, int]]]
) -> MatrixPosition:
    for from_sq, to_sq in moves:
        position, _ = position.make_move(from_sq, to_sq)
    return position


def run_case(
    description: str,
    positions: list[Position],
    expected_by_class: dict[type, float]
) -> bool:
    all_ok = True
    print(f"\n{description}")
    for name, evaluator in EVALUATORS:
        expected = expected_by_class[type(evaluator)]
        scores = [evaluator.evaluate(p) for p in positions]
        consistent = all(score == scores[0] for score in scores)
        correct = scores[0] == expected
        ok = consistent and correct
        all_ok = ok and all_ok
        mark = "PASS" if ok else "FAIL"
        scores_str = ", ".join(f"{score:+g}" for score in scores)
        print(f"  [{mark}] {name}: {scores_str} (expected {expected:+g})")
    return all_ok


def run_piece_counts_test() -> bool:
    counts = MatrixPosition.initial_position().get_piece_counts()
    expected = {
        PAWN: 8, -PAWN: 8,
        KNIGHT: 2, -KNIGHT: 2,
        BISHOP: 2, -BISHOP: 2,
        ROOK: 2, -ROOK: 2,
        QUEEN: 1, -QUEEN: 1,
        KING: 1, -KING: 1,
    }
    ok = counts == expected
    mark = "PASS" if ok else "FAIL"
    print(f"\n[{mark}] get_piece_counts on initial position ({len(counts)} entries)")
    if not ok:
        print(f"  expected: {expected}")
        print(f"  actual:   {counts}")
    return ok


def main() -> None:
    print("=== Evaluator tests ===")

    all_ok = True

    initial = MatrixPosition.initial_position()
    all_ok = run_case(
        "Initial position (perfect symmetry)",
        [initial],
        {PieceCountEvaluator: 0, MaterialEvaluator: 0},
    ) and all_ok

    white_up_queen_board = initial_board_with({(7, 3): EMPTY})
    all_ok = run_case(
        "White up a queen (both active colors, same score expected)",
        [
            make_position(white_up_queen_board, active_color=WHITE),
            make_position(white_up_queen_board, active_color=BLACK),
        ],
        {PieceCountEvaluator: 1, MaterialEvaluator: 9},
    ) and all_ok

    all_ok = run_case(
        "Black up a knight",
        [make_position(initial_board_with({(0, 1): EMPTY}))],
        {PieceCountEvaluator: -1, MaterialEvaluator: -3},
    ) and all_ok

    all_ok = run_case(
        "Composite: white lost a rook, black lost a bishop and a pawn",
        [make_position(initial_board_with({
            (0, 0): EMPTY,
            (7, 2): EMPTY,
            (6, 4): EMPTY,
        }))],
        {PieceCountEvaluator: 1, MaterialEvaluator: -1},
    ) and all_ok

    all_ok = run_case(
        "White promoted a pawn to a queen (same piece count, higher material)",
        [make_position(initial_board_with({(1, 0): QUEEN}))],
        {PieceCountEvaluator: 0, MaterialEvaluator: 8},
    ) and all_ok

    fools_mate = play_moves(MatrixPosition.initial_position(), [
        ((1, 5), (2, 5)),
        ((6, 4), (4, 4)),
        ((1, 6), (3, 6)),
        ((7, 3), (3, 7)),
    ])
    all_ok = run_case(
        "Fool's mate (1.f3 e5 2.g4 Qh4#) - white checkmated",
        [fools_mate],
        {PieceCountEvaluator: -MATE_SCORE, MaterialEvaluator: -MATE_SCORE},
    ) and all_ok

    scholars_mate = play_moves(MatrixPosition.initial_position(), [
        ((1, 4), (3, 4)),
        ((6, 4), (4, 4)),
        ((0, 5), (3, 2)),
        ((7, 1), (5, 2)),
        ((0, 3), (4, 7)),
        ((7, 6), (5, 5)),
        ((4, 7), (6, 5)),
    ])
    all_ok = run_case(
        "Scholar's mate (1.e4 e5 2.Bc4 Nc6 3.Qh5 Nf6 4.Qxf7#) - black checkmated",
        [scholars_mate],
        {PieceCountEvaluator: MATE_SCORE, MaterialEvaluator: MATE_SCORE},
    ) and all_ok

    all_ok = run_case(
        "Stalemate (black king h8, white queen f7, white king g6)",
        [make_position(make_board({
            (7, 7): -KING,
            (6, 5): QUEEN,
            (5, 6): KING,
        }), active_color=BLACK)],
        {PieceCountEvaluator: 0, MaterialEvaluator: 0},
    ) and all_ok

    all_ok = run_piece_counts_test() and all_ok

    print(f"\n=== Overall result: {'PASS' if all_ok else 'FAIL'} ===")


if __name__ == "__main__":
    main()
