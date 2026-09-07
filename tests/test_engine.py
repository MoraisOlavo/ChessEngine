"""
Tests for the engine package (Engine ABC, MiniMaxEngine and AlphaBetaEngine).

Uses positions with known best moves to verify the search behavior of both
engines, plus a cross-engine equivalence check (alpha-beta must agree with
plain minimax).

Run with: python3 -m tests.test_engine
"""

from position.base import EMPTY, KING, PAWN, ROOK, WHITE
from position.matrix import MatrixPosition
from evaluator.base import MATE_SCORE
from evaluator.weighted import MaterialEvaluator
from engine.minimax import MiniMaxEngine
from engine.alphabeta import AlphaBetaEngine


def make_board(pieces: dict[tuple[int, int], int]) -> list[list[int]]:
    board = [[EMPTY] * 8 for _ in range(8)]
    for (row, col), piece in pieces.items():
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


def play_moves(
    position: MatrixPosition,
    moves: list[tuple[tuple[int, int], tuple[int, int]]]
) -> MatrixPosition:
    for from_sq, to_sq in moves:
        position, _ = position.make_move(from_sq, to_sq)
    return position


def run_case(
    description: str,
    engine: MiniMaxEngine | AlphaBetaEngine,
    position: MatrixPosition,
    expected_move: tuple[tuple[int, int], tuple[int, int]],
    expected_score: float
) -> bool:
    move, score = engine.find_best_move(position)
    actual_move = (move.from_sq, move.to_sq)
    ok = actual_move == expected_move and score == expected_score
    mark = "PASS" if ok else "FAIL"
    print(f"[{mark}] {description}")
    if not ok:
        print(f"  expected move {expected_move} with score {expected_score}")
        print(f"  actual move   {actual_move} with score {score}")
    return ok


def run_terminal_case(
    description: str,
    engine: MiniMaxEngine | AlphaBetaEngine,
    position: MatrixPosition
) -> bool:
    ok = False
    try:
        engine.find_best_move(position)
    except ValueError:
        ok = True
    mark = "PASS" if ok else "FAIL"
    print(f"[{mark}] {description}")
    if not ok:
        print("  expected ValueError for a position with no legal moves")
    return ok


def run_depth_validation_case(engine_class: type) -> bool:
    ok = False
    try:
        engine_class(MaterialEvaluator(), max_depth=0)
    except ValueError:
        ok = True
    mark = "PASS" if ok else "FAIL"
    print(f"[{mark}] {engine_class.__name__} rejects max_depth < 1")
    if not ok:
        print("  expected ValueError for max_depth < 1")
    return ok


def run_equivalence_case() -> bool:
    initial = MatrixPosition.initial_position()
    minimax_move, minimax_score = MiniMaxEngine(
        MaterialEvaluator(), max_depth=3
    ).find_best_move(initial)
    alphabeta_move, alphabeta_score = AlphaBetaEngine(
        MaterialEvaluator(), max_depth=3
    ).find_best_move(initial)

    minimax_sq = (minimax_move.from_sq, minimax_move.to_sq)
    alphabeta_sq = (alphabeta_move.from_sq, alphabeta_move.to_sq)
    ok = minimax_sq == alphabeta_sq and minimax_score == alphabeta_score

    mark = "PASS" if ok else "FAIL"
    print(f"[{mark}] AlphaBeta agrees with MiniMax (initial position, depth 3)")
    if not ok:
        print(f"  MiniMax:   {minimax_sq} score {minimax_score}")
        print(f"  AlphaBeta: {alphabeta_sq} score {alphabeta_score}")
    return ok


def main() -> None:
    print("=== Engine tests ===")

    all_ok = True

    back_rank_mate = make_position(make_board({
        (7, 0): -KING,
        (5, 1): KING,
        (0, 7): ROOK,
    }))

    material_position = make_position(make_board({
        (3, 3): PAWN,
        (1, 6): KING,
        (4, 2): -ROOK,
        (4, 4): -PAWN,
        (7, 7): -KING,
    }))

    fools_mate = play_moves(MatrixPosition.initial_position(), [
        ((1, 5), (2, 5)),
        ((6, 4), (4, 4)),
        ((1, 6), (3, 6)),
        ((7, 3), (3, 7)),
    ])

    for engine_class in (MiniMaxEngine, AlphaBetaEngine):
        print(f"\n--- {engine_class.__name__} ---")
        all_ok = run_case(
            "Back rank mate in 1 (Rh8#) with depth 1",
            engine_class(MaterialEvaluator(), max_depth=1),
            back_rank_mate,
            ((0, 7), (7, 7)),
            MATE_SCORE,
        ) and all_ok

        all_ok = run_case(
            "Back rank mate in 1 (Rh8#) with depth 2",
            engine_class(MaterialEvaluator(), max_depth=2),
            back_rank_mate,
            ((0, 7), (7, 7)),
            MATE_SCORE,
        ) and all_ok

        all_ok = run_case(
            "Prefers capturing a rook over a pawn (depth 1)",
            engine_class(MaterialEvaluator(), max_depth=1),
            material_position,
            ((3, 3), (4, 2)),
            0.0,
        ) and all_ok

        all_ok = run_terminal_case(
            "Terminal position (white checkmated) raises ValueError",
            engine_class(MaterialEvaluator(), max_depth=1),
            fools_mate,
        ) and all_ok

        all_ok = run_depth_validation_case(engine_class) and all_ok

    print("\n--- Cross-engine equivalence ---")
    all_ok = run_equivalence_case() and all_ok

    print(f"\n=== Overall result: {'PASS' if all_ok else 'FAIL'} ===")


if __name__ == "__main__":
    main()
